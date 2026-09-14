import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.db import get_db
from app.webrtc.manager import manager

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionCreateOut)
def create_session(payload: schemas.SessionCreate, db: DBSession = Depends(get_db)):
    session = crud.create_session(db, payload.username, payload.email)
    return schemas.SessionCreateOut(session_id=session.id)


@router.get("/{session_id}", response_model=schemas.SessionOut)
def get_session(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@router.post("/{session_id}/end", response_model=schemas.SessionOut)
async def end_session(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    state = manager.get(str(session_id))
    if state is not None:
        await state.writer.stop()
        manager.unregister(str(session_id))
        await state.pc.close()

    crud.end_session(db, session_id, status="completed")
    db.refresh(session)
    return session
