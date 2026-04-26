from __future__ import annotations

import base64
import io
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from .protocol import FrameFormat, ParamUpdate, Real2dFrame, SessionStartRequest


@dataclass
class Real2dSession:
    session_id: str
    source_image: str | None
    fps: int
    frame_format: FrameFormat
    started_at: float = field(default_factory=time.perf_counter)
    last_params: dict[str, float] = field(default_factory=dict)


class MockReal2dRenderer:
    backend = "mock-real2d"

    def __init__(self) -> None:
        self.sessions: dict[str, Real2dSession] = {}
        self.frames_rendered = 0
        self.last_latency_ms = 0.0

    def start(self, req: SessionStartRequest) -> Real2dSession:
        sess = Real2dSession(
            session_id=req.sessionId,
            source_image=req.sourceImage,
            fps=req.fps,
            frame_format=req.frameFormat,
        )
        self.sessions[req.sessionId] = sess
        return sess

    def stop(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def render(self, update: ParamUpdate) -> Real2dFrame:
        t0 = time.perf_counter()
        sess = self.sessions.get(update.sessionId)
        if sess is None:
            sess = self.start(
                SessionStartRequest(sessionId=update.sessionId, fps=25, frameFormat="jpeg")
            )
        sess.last_params.update(update.params)
        image = self._base_image(sess)
        draw = ImageDraw.Draw(image, "RGBA")
        self._draw_param_overlay(draw, image.size, update.emotion or "neutral", sess.last_params)
        fmt = "PNG" if sess.frame_format == "png" else "WEBP" if sess.frame_format == "webp" else "JPEG"
        buf = io.BytesIO()
        if fmt == "JPEG":
            image = image.convert("RGB")
            image.save(buf, format=fmt, quality=86)
        else:
            image.save(buf, format=fmt)
        self.frames_rendered += 1
        self.last_latency_ms = (time.perf_counter() - t0) * 1000
        return Real2dFrame(
            sessionId=update.sessionId,
            timestampMs=int(time.time() * 1000),
            format=sess.frame_format,
            frameBase64=base64.b64encode(buf.getvalue()).decode("ascii"),
        )

    def metrics(self) -> dict[str, float | int | str]:
        return {
            "backend": self.backend,
            "sessions": len(self.sessions),
            "framesRendered": self.frames_rendered,
            "lastLatencyMs": round(self.last_latency_ms, 2),
        }

    def _base_image(self, sess: Real2dSession) -> Image.Image:
        if sess.source_image:
            p = Path(sess.source_image).expanduser()
            if p.exists() and p.is_file():
                try:
                    return Image.open(p).convert("RGBA").resize((768, 768))
                except Exception:
                    pass
        return Image.new("RGBA", (768, 768), (34, 38, 54, 255))

    def _draw_param_overlay(
        self,
        draw: ImageDraw.ImageDraw,
        size: tuple[int, int],
        emotion: str,
        params: dict[str, float],
    ) -> None:
        w, h = size
        cx = w // 2 + int(params.get("yaw", 0.0) * 3)
        cy = h // 2 - 18 - int(params.get("pitch", 0.0) * 2)
        smile = max(-1.0, min(1.0, params.get("smile", 0.0)))
        eye_open = max(0.05, min(1.4, params.get("eyeOpen", 1.0)))
        mouth_open = max(0.0, min(1.0, params.get("mouthOpen", 0.0)))
        brow = max(-1.0, min(1.0, params.get("brow", 0.0)))
        pulse = 0.5 + 0.5 * math.sin(time.perf_counter() * 2.0)

        draw.ellipse((cx - 176, cy - 206, cx + 176, cy + 206), fill=(236, 202, 180, 235))
        eye_h = int(18 * eye_open)
        draw.ellipse((cx - 92, cy - 60 - eye_h, cx - 44, cy - 60 + eye_h), fill=(24, 26, 32, 255))
        draw.ellipse((cx + 44, cy - 60 - eye_h, cx + 92, cy - 60 + eye_h), fill=(24, 26, 32, 255))
        draw.line((cx - 112, cy - 103 - brow * 28, cx - 38, cy - 112 + brow * 8), fill=(70, 42, 34, 255), width=8)
        draw.line((cx + 38, cy - 112 + brow * 8, cx + 112, cy - 103 - brow * 28), fill=(70, 42, 34, 255), width=8)

        mouth_w = 84 + int(abs(smile) * 46)
        mouth_h = 18 + int(mouth_open * 72)
        if smile >= 0:
            box = (cx - mouth_w, cy + 78 - mouth_h, cx + mouth_w, cy + 78 + mouth_h)
            draw.arc(box, 10, 170, fill=(80, 34, 44, 255), width=10)
        else:
            box = (cx - mouth_w, cy + 88 - mouth_h, cx + mouth_w, cy + 88 + mouth_h)
            draw.arc(box, 190, 350, fill=(80, 34, 44, 255), width=10)
        if mouth_open > 0.05:
            draw.ellipse((cx - 42, cy + 72, cx + 42, cy + 72 + mouth_h), fill=(82, 28, 38, 245))

        draw.rounded_rectangle((22, 22, 332, 86), radius=18, fill=(0, 0, 0, 100))
        draw.text((44, 42), f"{emotion}  mouth={mouth_open:.2f}  idle={pulse:.2f}", fill=(255, 255, 255, 255))
