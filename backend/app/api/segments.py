import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.db import get_db

router = APIRouter(prefix="/sessions", tags=["segments"])


@router.get("/{session_id}/segments", response_model=list[schemas.VideoSegmentOut])
def list_segments(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return crud.get_segments(db, session_id)


@router.get("/{session_id}/segments/{segment_index}/video")
def get_segment_video(session_id: uuid.UUID, segment_index: int, db: DBSession = Depends(get_db)):
    segment = crud.get_segment(db, session_id, segment_index)
    if segment is None:
        raise HTTPException(status_code=404, detail="segment not found")

    path = Path(segment.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="segment file missing on disk")

    return FileResponse(
        path,
        media_type="video/webm",
        filename=f"segment_{segment_index:04d}.webm",
    )
