# LittleFS Browser

A web-based file browser for LittleFS filesystems on Ubuntu. Access files from embedded devices (ESP32, STM32, nRF52, etc.) through a React interface built with shadcn/ui.

## Installation

### One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/finorr/littlefs-browser/main/install.sh | bash
```

### Manual Install

```bash
git clone https://github.com/finorr/littlefs-browser.git
cd littlefs-browser
chmod +x install.sh
./install.sh
```

## Usage

Start the application:

```bash
cd ~/littlefs-browser
./run.sh
```

Open http://localhost:5000 in your browser.

1. Insert your SD card or USB drive with LittleFS
2. Click "Scan Devices"
3. Click on your device to mount it
4. Browse and download files as needed
5. Click "Disconnect" when finished

## Features

- React UI with shadcn/ui components
- Automatic device detection
- Automatic mounting with common parameter detection
- File browser with breadcrumb navigation
- Individual file downloads or bulk extraction
- Toast notifications for user feedback
- Responsive design
- Dark/light mode toggle
- Proper unmounting and cleanup

## System Requirements

- Ubuntu 20.04 or newer (Debian-based distros should work)
- Python 3.8+
- Node.js 18+ (for development)

## Quick Start

### For Users (Production)
```bash
# Install dependencies
pip install -r requirements.txt

# Build frontend (one time)
cd frontend && npm install && npm run build && cd ..

# Run the application
sudo python3 app.py
```

Visit `http://localhost:5000`

### For Developers
```bash
# Easy way
./start-dev.sh

# Manual way - Terminal 1
sudo python3 app.py

# Manual way - Terminal 2
cd frontend && npm run dev
```

Visit `http://localhost:5173` for development with hot reload.

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.
See [MIGRATION.md](MIGRATION.md) for migration details.

## Technology Stack

- Frontend: React + TypeScript + Vite
- UI Components: shadcn/ui
- Styling: Tailwind CSS v4
- Backend: Flask (Python)
- API: RESTful JSON endpoints

## What Gets Installed

The installer will:
- Install Python 3 and Flask
- Install build tools (gcc, make, pkg-config)
- Install FUSE development libraries
- Build and install littlefs-fuse from source
- Create a Python virtual environment
- Set up the application in ~/littlefs-browser
- Create a desktop launcher

## Manual Installation Steps

If the automatic installer fails:

```bash
# Install dependencies
sudo apt update
sudo apt install -y build-essential libfuse-dev pkg-config git python3 python3-pip python3-venv

# Install littlefs-fuse
git clone https://github.com/littlefs-project/littlefs-fuse
cd littlefs-fuse
make -j$(nproc)
sudo cp lfs /usr/local/bin/
sudo chmod +x /usr/local/bin/lfs
cd ..

# Set up application
mkdir -p ~/littlefs-browser/templates
cd ~/littlefs-browser

# Copy app.py and templates/index.html to appropriate locations

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install flask

# Run
sudo -E venv/bin/python3 app.py
```

## How It Works

1. Uses `lsblk` to detect block devices
2. Attempts to mount LittleFS with common parameters (block sizes: 512, 4096; read/prog sizes: 16, 512)
3. Uses `littlefs-fuse` to mount the filesystem via FUSE
4. Flask serves a web interface on localhost:5000
5. Files are accessed directly from the FUSE mount point

## Troubleshooting

**Device not detected**
- Verify it's connected: `lsblk`
- Click "Scan Devices" again
- Check kernel messages: `dmesg | tail`

**Mount fails**
- Verify the device contains a LittleFS filesystem
- Some devices may require custom parameters
- Check device readability: `sudo file -s /dev/sdX`

**Port 5000 already in use**

Edit `app.py` and change the port number:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Permission errors**

The application requires sudo for device access. Use the provided `run.sh` script which handles this automatically.

**littlefs-fuse build fails**

Ensure all dependencies are installed:
```bash
sudo apt install build-essential libfuse-dev pkg-config
```

## Security

- Requires sudo for device mounting
- Listens on localhost only by default
- Uses FUSE for sandboxed filesystem access
- No network exposure unless you modify the host setting

## File Locations

- Application: `~/littlefs-browser/`
- Desktop launcher: `~/.local/share/applications/littlefs-browser.desktop`
- Binary: `/usr/local/bin/lfs`
- Temporary mount points: `/tmp/littlefs_mounts/`
- Downloaded files: `~/Downloads/littlefs_export/`

## Uninstallation

```bash
rm -rf ~/littlefs-browser
rm ~/.local/share/applications/littlefs-browser.desktop
sudo rm /usr/local/bin/lfs  # optional
```

## Use Cases

- Extract logs from microcontroller SD cards
- Browse filesystems from IoT devices
- Recover data from LittleFS volumes
- Verify files written by embedded systems
- Backup device data before reflashing

## Project Structure

```
littlefs-browser/
├── app.py              # Flask backend
├── templates/
│   └── index.html     # Web interface
├── install.sh         # Installation script
└── README.md          # Documentation
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [littlefs-fuse](https://github.com/littlefs-project/littlefs-fuse) - FUSE driver for LittleFS
- [LittleFS](https://github.com/littlefs-project/littlefs) - The filesystem implementation
- [Flask](https://flask.palletsprojects.com/) - Web framework
