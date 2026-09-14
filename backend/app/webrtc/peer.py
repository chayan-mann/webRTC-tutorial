import asyncio
import logging
import uuid

from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection
from starlette.concurrency import run_in_threadpool

from app import crud
from app.config import settings
from app.db import SessionLocal
from app.webrtc.manager import manager
from app.webrtc.segment_writer import SegmentWriter

logger = logging.getLogger(__name__)


def _persist_segment_sync(session_id: str, index: int, path: str, started: float, ended: float) -> None:
    db = SessionLocal()
    try:
        crud.add_video_segment(db, uuid.UUID(session_id), index, path, started, ended)
    finally:
        db.close()


def _mark_interrupted_sync(session_id: str) -> None:
    db = SessionLocal()
    try:
        crud.end_session(db, uuid.UUID(session_id), status="interrupted")
    finally:
        db.close()


def _persist_segment_cb(session_id: str):
    async def cb(index: int, path: str, started: float, ended: float) -> None:
        await run_in_threadpool(_persist_segment_sync, session_id, index, path, started, ended)

    return cb


async def create_peer_connection(session_id: str) -> RTCPeerConnection:
    pc = RTCPeerConnection(
        configuration=RTCConfiguration(iceServers=[RTCIceServer(urls=[settings.STUN_URL])])
    )
    writer = SegmentWriter(
        session_id=session_id,
        segment_seconds=settings.SEGMENT_SECONDS,
        on_segment_closed=_persist_segment_cb(session_id),
    )
    tracks: dict[str, object] = {}
    cleanup_done = False

    async def cleanup() -> None:
        nonlocal cleanup_done
        if cleanup_done:
            return
        cleanup_done = True
        await writer.stop()
        manager.unregister(session_id)
        await run_in_threadpool(_mark_interrupted_sync, session_id)

    @pc.on("track")
    def on_track(track):
        tracks[track.kind] = track
        if "video" in tracks and "audio" in tracks:
            asyncio.ensure_future(writer.start(tracks["video"], tracks["audio"]))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("session %s connection state: %s", session_id, pc.connectionState)
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await cleanup()

    manager.register(session_id, pc, writer)
    return pc
