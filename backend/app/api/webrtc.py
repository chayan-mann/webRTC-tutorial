import uuid

from aiortc import RTCSessionDescription
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app import crud, schemas
from app.config import settings
from app.db import get_db
from app.webrtc.ice import wait_for_ice_gathering_complete
from app.webrtc.peer import create_peer_connection

router = APIRouter(prefix="/sessions", tags=["webrtc"])


@router.post("/{session_id}/webrtc/offer", response_model=schemas.SDPOut)
async def webrtc_offer(session_id: uuid.UUID, payload: schemas.SDPIn, db: DBSession = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    pc = await create_peer_connection(str(session_id))

    offer = RTCSessionDescription(sdp=payload.sdp, type=payload.type)
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await wait_for_ice_gathering_complete(pc, settings.ICE_GATHERING_TIMEOUT)

    crud.set_session_status(db, session_id, "active")

    local_desc = pc.localDescription
    return schemas.SDPOut(sdp=local_desc.sdp, type=local_desc.type)
