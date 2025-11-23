# Quick Start Guide

## Getting Started

### First Time Setup

1. Install Dependencies
   ```bash
   # Python dependencies
   pip install -r requirements.txt

   # Frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

2. Build the Application
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

3. Run the Application
   ```bash
   sudo python3 app.py
   ```

4. Open in Browser
   ```
   http://localhost:5000
   ```

## Development

### Using the Helper Script
```bash
./start-dev.sh
```

Options:
- Frontend only (React dev with HMR)
- Backend only (Flask API)
- Full stack (both servers)
- Production build

### Manual Setup

Terminal 1 - Backend:
```bash
sudo python3 app.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` for development with hot reload.

## Interface Overview

The shadcn/ui interface includes:

- Header: Title, status indicator, theme toggle, and scan button
- Device List: Available storage devices
- File Browser: Mounted device contents with breadcrumb navigation
- Info Card: Device and connection statistics
- Toast Notifications: User feedback for actions

## Features

- Modern UI with shadcn/ui components
- Full TypeScript support
- Responsive design
- Real-time status updates
- Toast notifications
- Dark/light mode toggle
- Download individual files or entire filesystem
- Breadcrumb navigation

## Common Tasks

### Mount a Device
1. Click "Scan Devices"
2. Click on a device from the list
3. Wait for automatic mount and detection

### Browse Files
- Click folders to navigate
- Use breadcrumbs to go back
- Hover over files to see download button

### Download Files
- Single file: Hover and click download icon
- All files: Click "Download All" button

### Unmount Device
Click "Eject" button in the file browser header

## Troubleshooting

### Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Permission Issues
Run Flask with sudo:
```bash
sudo python3 app.py
```

### Old Template
The original HTML template is available at:
```
http://localhost:5000/old
```

## Additional Documentation

- Full migration details: `MIGRATION.md`
- Component documentation: `frontend/src/components/`
- API endpoints: `app.py` routes
