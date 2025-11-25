#!/usr/bin/env bash
set -euo pipefail

# Simple helper to create a venv, install minimal requirements and run the app
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/venv"
PY="$VENV_DIR/bin/python3"

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv..."
  python3 -m venv "$VENV_DIR"
fi

echo "Upgrading pip and installing requirements..."
"$PY" -m pip install --upgrade pip setuptools wheel
"$PY" -m pip install -r "$ROOT_DIR/requirements-no-xcode.txt"

echo "Starting application (use Ctrl+C to stop)..."
"$PY" main.py
