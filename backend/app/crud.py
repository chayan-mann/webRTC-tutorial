import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from app import models


def create_session(db: DBSession, username: str, email: str) -> models.Session:
    session = models.Session(
        id=uuid.uuid4(),
        username=username,
        email=email,
        started_at=datetime.now(timezone.utc),
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: DBSession, session_id: uuid.UUID) -> models.Session | None:
    return db.get(models.Session, session_id)


def set_session_status(db: DBSession, session_id: uuid.UUID, status: str) -> None:
    session = db.get(models.Session, session_id)
    if session is None:
        return
    session.status = status
    db.commit()


def end_session(db: DBSession, session_id: uuid.UUID, status: str = "completed") -> None:
    session = db.get(models.Session, session_id)
    if session is None or session.ended_at is not None:
        return
    session.ended_at = datetime.now(timezone.utc)
    session.status = status
    db.commit()


def add_video_segment(
    db: DBSession,
    session_id: uuid.UUID,
    segment_index: int,
    file_path: str,
    started_at: float,
    ended_at: float,
) -> None:
    duration = ended_at - started_at
    segment = models.VideoSegment(
        session_id=session_id,
        segment_index=segment_index,
        file_path=file_path,
        started_at=datetime.fromtimestamp(started_at, tz=timezone.utc),
        ended_at=datetime.fromtimestamp(ended_at, tz=timezone.utc),
        duration_seconds=duration,
    )
    db.add(segment)
    db.commit()


def get_segments(db: DBSession, session_id: uuid.UUID) -> list[models.VideoSegment]:
    return (
        db.query(models.VideoSegment)
        .filter(models.VideoSegment.session_id == session_id)
        .order_by(models.VideoSegment.segment_index)
        .all()
    )


def get_segment(db: DBSession, session_id: uuid.UUID, segment_index: int) -> models.VideoSegment | None:
    return (
        db.query(models.VideoSegment)
        .filter(
            models.VideoSegment.session_id == session_id,
            models.VideoSegment.segment_index == segment_index,
        )
        .first()
    )
