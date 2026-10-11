#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/venv"
PYTHON="${VENV_DIR}/bin/python"

cd "${PROJECT_ROOT}"

if [[ ! -x "${PYTHON}" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"
fi

echo "Installing dependencies..."
"${PYTHON}" -m pip install --upgrade pip
"${PYTHON}" -m pip install -r requirements.txt

echo "Initializing JSON data..."
"${PYTHON}" -m backend.seed

echo "Starting Smart Kiosk..."
exec "${PYTHON}" main.py "$@"