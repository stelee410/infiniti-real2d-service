#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import time
from pathlib import Path

import requests


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8921")
    ap.add_argument("--out", default="frames/smoke-happy.jpg")
    args = ap.parse_args()

    base = args.base_url.rstrip("/")
    r = requests.get(f"{base}/health", timeout=5)
    r.raise_for_status()
    print("health:", r.json())

    session_id = "smoke-test"
    r = requests.post(
        f"{base}/session/start",
        json={"sessionId": session_id, "fps": 25, "frameFormat": "jpeg"},
        timeout=5,
    )
    r.raise_for_status()
    print("start:", r.json())

    payload = {
        "type": "PARAM_UPDATE",
        "sessionId": session_id,
        "timestampMs": int(time.time() * 1000),
        "emotion": "happy",
        "params": {"smile": 0.8, "eyeOpen": 0.92, "mouthOpen": 0.45, "pitch": 5, "yaw": 0},
        "transitionMs": 200,
    }
    r = requests.post(f"{base}/session/params", json=payload, timeout=10)
    r.raise_for_status()
    frame = r.json()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(frame["frameBase64"]))
    print("frame:", out)


if __name__ == "__main__":
    main()
