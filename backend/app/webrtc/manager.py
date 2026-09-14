from dataclasses import dataclass

from aiortc import RTCPeerConnection

from app.webrtc.segment_writer import SegmentWriter


@dataclass
class PeerState:
    pc: RTCPeerConnection
    writer: SegmentWriter


class SessionManager:
    """In-process registry of live sessions. Single uvicorn worker only —
    doesn't scale past one process without a shared coordination layer."""

    def __init__(self) -> None:
        self._sessions: dict[str, PeerState] = {}

    def register(self, session_id: str, pc: RTCPeerConnection, writer: SegmentWriter) -> None:
        self._sessions[session_id] = PeerState(pc=pc, writer=writer)

    def get(self, session_id: str) -> PeerState | None:
        return self._sessions.get(session_id)

    def unregister(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def all_session_ids(self) -> list[str]:
        return list(self._sessions.keys())


manager = SessionManager()
