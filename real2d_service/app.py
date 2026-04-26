from __future__ import annotations

import time

from fastapi import FastAPI

from .protocol import (
    AudioChunk,
    ParamUpdate,
    Real2dHealth,
    SessionStartRequest,
    SessionStartResponse,
    SessionStopRequest,
)
from .renderer import MockReal2dRenderer


app = FastAPI(title="Infiniti Real2D Service", version="0.1.0")
renderer = MockReal2dRenderer()
audio_chunks_received = 0
started_at = time.perf_counter()


@app.get("/health", response_model=Real2dHealth)
def health() -> Real2dHealth:
    return Real2dHealth(
        ok=True,
        ready=True,
        backend=renderer.backend,
        latencyMs=round(renderer.last_latency_ms, 2),
    )


@app.post("/session/start", response_model=SessionStartResponse)
def start_session(req: SessionStartRequest) -> SessionStartResponse:
    renderer.start(req)
    return SessionStartResponse(sessionId=req.sessionId, ready=True, backend=renderer.backend)


@app.post("/session/params")
def update_params(update: ParamUpdate):
    return renderer.render(update)


@app.post("/session/audio")
def receive_audio(chunk: AudioChunk) -> dict[str, bool | int]:
    global audio_chunks_received
    audio_chunks_received += 1
    return {"ok": True, "audioChunksReceived": audio_chunks_received, "sequence": chunk.sequence}


@app.post("/session/stop")
def stop_session(req: SessionStopRequest) -> dict[str, bool]:
    renderer.stop(req.sessionId)
    return {"ok": True}


@app.get("/metrics")
def metrics() -> dict[str, object]:
    return {
        **renderer.metrics(),
        "audioChunksReceived": audio_chunks_received,
        "uptimeSec": round(time.perf_counter() - started_at, 2),
    }
