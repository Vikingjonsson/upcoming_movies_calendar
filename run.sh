#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment not found. Setting it up..."
    python3 -m venv "$VENV_DIR" && \
        "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

    if [ $? -ne 0 ]; then
        echo "Failed to set up virtual environment."
        exit 1
    fi

    echo "Setup complete."
fi

"$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
