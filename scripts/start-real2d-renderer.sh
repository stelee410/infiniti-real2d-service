#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="8921"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)
      PORT="${2:-8921}"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  . .venv/bin/activate
fi

exec python -m uvicorn real2d_service.app:app --host 127.0.0.1 --port "$PORT"
