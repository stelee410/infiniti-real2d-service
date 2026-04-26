from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


FrameFormat = Literal["jpeg", "webp", "png", "raw"]
AudioFormat = Literal["mp3", "wav", "pcm_s16le"]


class Real2dHealth(BaseModel):
    ok: bool = True
    ready: bool = True
    backend: str = "mock-real2d"
    fps: float | None = None
    latencyMs: float | None = None
    message: str | None = None


class SessionStartRequest(BaseModel):
    sessionId: str
    sourceImage: str | None = None
    fps: int = Field(default=25, ge=1, le=60)
    frameFormat: FrameFormat = "jpeg"


class SessionStartResponse(BaseModel):
    sessionId: str
    ready: bool = True
    backend: str = "mock-real2d"
    streamUrl: str | None = None


class ParamUpdate(BaseModel):
    type: Literal["PARAM_UPDATE"] = "PARAM_UPDATE"
    sessionId: str
    timestampMs: int
    emotion: str | None = None
    params: dict[str, float] = Field(default_factory=dict)
    transitionMs: int | None = None


class AudioChunk(BaseModel):
    type: Literal["AUDIO_CHUNK"] = "AUDIO_CHUNK"
    sessionId: str
    format: AudioFormat
    sampleRate: int
    channels: int = 1
    sequence: int
    audioBase64: str


class SessionStopRequest(BaseModel):
    sessionId: str


class Real2dFrame(BaseModel):
    type: Literal["REAL2D_FRAME"] = "REAL2D_FRAME"
    sessionId: str
    timestampMs: int
    format: FrameFormat
    frameBase64: str
