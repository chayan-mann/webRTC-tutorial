import asyncio
import logging
import time
from pathlib import Path
from typing import Awaitable, Callable

import av

from app.storage.paths import segment_path

logger = logging.getLogger(__name__)

OnSegmentClosed = Callable[[int, str, float, float], Awaitable[None]]


class SegmentWriter:
    """Consumes decoded audio+video frames from two aiortc tracks and muxes
    them into rotating ~60s .webm files, since aiortc's MediaRecorder can't rotate."""

    def __init__(
        self,
        session_id: str,
        segment_seconds: int,
        on_segment_closed: OnSegmentClosed,
    ):
        self.session_id = session_id
        self.segment_seconds = segment_seconds
        self.on_segment_closed = on_segment_closed

        self._lock = asyncio.Lock()
        self._index = 0
        self._container: av.container.OutputContainer | None = None
        self._video_stream = None
        self._audio_stream = None
        self._video_pts0 = None
        self._audio_pts0 = None
        self._segment_started: float | None = None
        self._current_path: Path | None = None
        self._closed = False
        self._tasks: list[asyncio.Task] = []

    async def start(self, video_track, audio_track) -> None:
        await self._open_segment()
        self._tasks = [
            asyncio.create_task(self._consume(video_track, "video")),
            asyncio.create_task(self._consume(audio_track, "audio")),
            asyncio.create_task(self._rotation_timer()),
        ]

    async def _rotation_timer(self) -> None:
        try:
            while not self._closed:
                await asyncio.sleep(self.segment_seconds)
                if not self._closed:
                    await self._open_segment()
        except asyncio.CancelledError:
            pass

    async def _open_segment(self) -> None:
        async with self._lock:
            if self._container is not None:
                await self._close_locked()
            path = segment_path(self.session_id, self._index)
            container = av.open(str(path), mode="w", format="webm")
            video_stream = container.add_stream("libvpx", rate=30)
            video_stream.pix_fmt = "yuv420p"
            video_stream.codec_context.bit_rate = 2_500_000
            video_stream.codec_context.options = {
                "deadline": "realtime",
                "cpu-used": "4",
            }
            audio_stream = container.add_stream("libopus", rate=48000)
            audio_stream.codec_context.bit_rate = 128_000

            self._container = container
            self._video_stream = video_stream
            self._audio_stream = audio_stream
            self._video_pts0 = None
            self._audio_pts0 = None
            self._segment_started = time.time()
            self._current_path = path

    async def _close_locked(self) -> None:
        if self._container is None:
            return
        for stream in (self._video_stream, self._audio_stream):
            try:
                for packet in stream.encode(None):
                    self._container.mux(packet)
            except Exception:
                logger.exception("error flushing stream for session %s", self.session_id)
        self._container.close()
        ended = time.time()
        index = self._index
        path = self._current_path
        started = self._segment_started
        self._container = None
        try:
            await self.on_segment_closed(index, str(path), started, ended)
        except Exception:
            logger.exception("error persisting segment %s for session %s", index, self.session_id)
        self._index += 1

    async def _consume(self, track, kind: str) -> None:
        while not self._closed:
            try:
                frame = await track.recv()
            except Exception:
                break
            async with self._lock:
                if self._container is None:
                    continue
                stream = self._video_stream if kind == "video" else self._audio_stream
                if kind == "video":
                    if self._video_pts0 is None:
                        self._video_pts0 = frame.pts
                    frame.pts = frame.pts - self._video_pts0
                else:
                    if self._audio_pts0 is None:
                        self._audio_pts0 = frame.pts
                    frame.pts = frame.pts - self._audio_pts0
                try:
                    for packet in stream.encode(frame):
                        self._container.mux(packet)
                except Exception:
                    logger.exception(
                        "error encoding %s frame for session %s", kind, self.session_id
                    )

    async def stop(self) -> None:
        if self._closed:
            return
        self._closed = True
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        async with self._lock:
            await self._close_locked()
