# Infiniti Real2D Service

FastAPI service skeleton for the Infiniti Agent `real2d` renderer path.

This first version is intentionally a lightweight mock renderer. It validates the service boundary, session lifecycle, parameter protocol, and frame delivery before replacing the renderer internals with LivePortrait/FasterLivePortrait.

## Quick Start

```bash
./scripts/setup-real2d-venv.sh
./scripts/start-real2d-renderer.sh --port 8921
```

Smoke test:

```bash
. .venv/bin/activate
python tools/real2d-smoke-test.py --base-url http://127.0.0.1:8921
```

## API

- `GET /health`
- `POST /session/start`
- `POST /session/params`
- `POST /session/audio`
- `POST /session/stop`
- `GET /metrics`

`POST /session/params` returns a `REAL2D_FRAME` JSON payload in this mock implementation so the Node bridge can immediately draw frames in LiveUI.

## Next Renderer Step

Replace `real2d_service/renderer.py` with a FasterLivePortrait-backed renderer that:

- loads and caches the source image
- extracts base keypoints/features once per session
- blends emotion, mouth, idle, and action params
- returns JPEG/WebP frames at the requested FPS
