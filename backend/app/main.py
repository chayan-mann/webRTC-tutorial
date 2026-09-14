import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import segments, sessions, webrtc
from app.config import settings
from app.webrtc.manager import manager
from app.webrtc.peer import _mark_interrupted_sync

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    yield
    for session_id in manager.all_session_ids():
        state = manager.get(session_id)
        if state is None:
            continue
        await state.writer.stop()
        await state.pc.close()
        _mark_interrupted_sync(session_id)
        manager.unregister(session_id)


app = FastAPI(title="Interview Recording API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(webrtc.router)
app.include_router(segments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
