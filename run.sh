#!/bin/bash

cd "$(dirname "$0")"

# Check if frontend is built
if [ ! -d "frontend/dist" ] || [ ! -f "frontend/dist/index.html" ]; then
    echo "Frontend not built. Building now..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    npm run build
    cd ..
    echo "Build complete!"
    echo ""
fi

echo "Starting LittleFS Browser..."
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Activate venv if it exists, otherwise use system Python
if [ -d "venv" ] || [ -d ".venv" ]; then
    VENV_DIR="venv"
    [ -d ".venv" ] && VENV_DIR=".venv"

    source "$VENV_DIR/bin/activate"
    sudo -E "$VENV_DIR/bin/python3" app.py
else
    sudo -E python3 app.py
fi
