#!/bin/bash

# LittleFS Browser - Installation Script
# Downloads and installs everything needed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/littlefs-browser"
REPO_URL="https://raw.githubusercontent.com/finorr/littlefs-browser/main"

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════╗
║   LittleFS Browser - Easy Installer  ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}[X] Don't run this as root/sudo${NC}"
    echo "Run as your normal user. It will ask for sudo when needed."
    exit 1
fi

# Check OS
echo -e "${YELLOW}[1/5]${NC} Checking system..."

if [ ! -f /etc/os-release ]; then
    echo -e "${RED}[X] Cannot detect OS. This script is for Ubuntu/Debian.${NC}"
    exit 1
fi

source /etc/os-release
if [[ ! "$ID" =~ ^(ubuntu|debian|linuxmint)$ ]]; then
    echo -e "${YELLOW}[!] Warning: Not Ubuntu/Debian. Installation may fail.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[OK]${NC} OS: $PRETTY_NAME"

# Install system dependencies
echo -e "\n${YELLOW}[2/5]${NC} Installing system dependencies..."
echo "This requires sudo and will ask for your password:"

sudo apt update

if ! command -v python3 &> /dev/null; then
    echo "  Installing Python 3..."
    sudo apt install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}[OK]${NC} Python 3 already installed"
fi

if ! command -v git &> /dev/null; then
    echo "  Installing Git..."
    sudo apt install -y git
else
    echo -e "${GREEN}[OK]${NC} Git already installed"
fi

echo "  Installing build tools and FUSE..."
sudo apt install -y build-essential libfuse-dev pkg-config util-linux wget curl

echo -e "${GREEN}[OK]${NC} System dependencies installed"

# Install littlefs-fuse
echo -e "\n${YELLOW}[3/5]${NC} Installing littlefs-fuse..."

if command -v lfs &> /dev/null; then
    echo -e "${GREEN}[OK]${NC} littlefs-fuse already installed"
else
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    echo "  Cloning repository..."
    git clone --depth 1 https://github.com/littlefs-project/littlefs-fuse
    cd littlefs-fuse
    echo "  Building (this may take a minute)..."
    make -j$(nproc)
    echo "  Installing..."
    # Manual install since makefile doesn't have install target
    sudo cp lfs /usr/local/bin/lfs
    sudo chmod +x /usr/local/bin/lfs
    cd
    rm -rf "$TEMP_DIR"
    echo -e "${GREEN}[OK]${NC} littlefs-fuse installed to /usr/local/bin/lfs"
fi

# Create installation directory
echo -e "\n${YELLOW}[4/5]${NC} Setting up application..."

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download application files
echo "  Downloading application files..."

# For local testing, check if files exist locally first
if [ -f "../app.py" ] && [ -f "../templates/index.html" ]; then
    echo "  Found local files, copying..."
    cp ../app.py .
    mkdir -p templates
    cp ../templates/index.html templates/
else
    echo "  Downloading from repository..."
    # Try to download from repo (will fail until you set up the repo)
    if ! wget -q "$REPO_URL/app.py" -O app.py 2>/dev/null; then
        echo -e "${RED}[X] Could not download app.py${NC}"
        echo "Please manually copy app.py to $INSTALL_DIR"
        exit 1
    fi
    
    mkdir -p templates
    if ! wget -q "$REPO_URL/templates/index.html" -O templates/index.html 2>/dev/null; then
        echo -e "${RED}[X] Could not download index.html${NC}"
        echo "Please manually copy templates/index.html to $INSTALL_DIR/templates/"
        exit 1
    fi
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet flask

echo -e "${GREEN}[OK]${NC} Application files ready"

# Create launcher script
echo -e "\n${YELLOW}[5/5]${NC} Creating launcher..."

cat > run.sh << 'ENDOFRUNNER'
#!/bin/bash

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting LittleFS Browser..."
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

sudo -E venv/bin/python3 app.py
ENDOFRUNNER

chmod +x run.sh

# Create desktop launcher
DESKTOP_FILE="$HOME/.local/share/applications/littlefs-browser.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << ENDOFDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=LittleFS Browser
Comment=Browse LittleFS volumes easily
Exec=x-terminal-emulator -e "$INSTALL_DIR/run.sh"
Icon=drive-harddisk
Terminal=true
Categories=System;Utility;
ENDOFDESKTOP

chmod +x "$DESKTOP_FILE"

echo -e "${GREEN}[OK]${NC} Launcher created"

# Success message
echo -e "\n${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════╗
║       Installation Complete!          ║
╚═══════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}To start LittleFS Browser:${NC}"
echo -e "  ${YELLOW}Option 1:${NC} Run in terminal:"
echo -e "    cd $INSTALL_DIR"
echo -e "    ./run.sh"
echo ""
echo -e "  ${YELLOW}Option 2:${NC} Search for 'LittleFS Browser' in your applications menu"
echo ""
echo -e "${BLUE}Then open your browser to:${NC} ${GREEN}http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo "  1. Insert your SD card with LittleFS"
echo "  2. Click 'Scan Devices'"
echo "  3. Click on your device to mount"
echo "  4. Browse and download files!"
echo ""
echo -e "${BLUE}Installation location:${NC} $INSTALL_DIR"
echo ""
echo -e "${YELLOW}Note:${NC} For automatic downloads from GitHub, set REPO_URL in the script"