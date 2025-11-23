#!/bin/bash

# LittleFS Browser Development Starter
# This script helps start both backend and frontend in development mode

echo "Starting LittleFS Browser Development Environment"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "Error: app.py not found. Please run this script from the project root."
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "Error: frontend directory not found."
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "Checking dependencies..."

if ! command_exists python3; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "Error: npm is not installed"
    exit 1
fi

echo "All dependencies found"
echo ""

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "Frontend dependencies installed"
    echo ""
fi

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo "Flask not found. Installing Python dependencies..."
    pip3 install -r requirements.txt
}

python3 -c "import flask_cors" 2>/dev/null || {
    echo "flask-cors not found. Installing..."
    pip3 install flask-cors
}

echo "Python dependencies ready"
echo ""

# Ask user what mode they want
echo "Choose development mode:"
echo "  1) Frontend only (React dev server on :5173)"
echo "  2) Backend only (Flask API on :5000)"
echo "  3) Full stack (both servers)"
echo "  4) Production build (build React + run Flask)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo "Starting frontend dev server..."
        cd frontend
        npm run dev
        ;;
    2)
        echo "Starting Flask backend..."
        if [ "$EUID" -ne 0 ]; then
            echo "Warning: Backend requires sudo for device access"
            sudo python3 app.py
        else
            python3 app.py
        fi
        ;;
    3)
        echo "Starting Flask backend..."
        echo "   Visit http://localhost:5000 for production build"
        echo "   Visit http://localhost:5173 for dev mode with HMR"
        echo ""
        echo "Opening two terminals..."

        # Start backend in background
        if [ "$EUID" -ne 0 ]; then
            echo "Starting backend with sudo..."
            sudo python3 app.py &
        else
            python3 app.py &
        fi
        BACKEND_PID=$!

        # Wait a bit for backend to start
        sleep 2

        # Start frontend
        echo ""
        echo "Starting frontend dev server..."
        cd frontend
        npm run dev

        # Cleanup on exit
        trap "kill $BACKEND_PID" EXIT
        ;;
    4)
        echo "Building React application..."
        cd frontend
        npm run build
        cd ..

        echo "Build complete"
        echo ""
        echo "Starting Flask in production mode..."
        if [ "$EUID" -ne 0 ]; then
            sudo python3 app.py
        else
            python3 app.py
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
