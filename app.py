#!/usr/bin/env python3
"""
LittleFS Browser - Flask Web Interface
A professional tool for browsing LittleFS filesystems from embedded devices
"""

import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from flask import Flask, render_template_string, jsonify, send_file, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration"""
    MOUNT_BASE: str = "/tmp/littlefs_mounts"
    DEFAULT_EXPORT_PATH: str = "~/Downloads/littlefs_export"
    MOUNT_TIMEOUT: float = 0.5
    CLEANUP_ATTEMPTS: int = 3
    DETECTION_TIMEOUT: float = 0.5

    # Common LittleFS configurations for auto-detection
    COMMON_CONFIGS: List[Dict[str, int]] = None

    def __post_init__(self):
        if self.COMMON_CONFIGS is None:
            self.COMMON_CONFIGS = [
                # Zephyr RTOS / embedded system defaults
                {'block_size': 512, 'read_size': 16, 'prog_size': 16, 'cache_size': 64, 'lookahead_size': 32},
                {'block_size': 512, 'read_size': 32, 'prog_size': 32, 'cache_size': 64, 'lookahead_size': 32},
                {'block_size': 512, 'read_size': 64, 'prog_size': 64, 'cache_size': 64, 'lookahead_size': 32},
                {'block_size': 512, 'read_size': 128, 'prog_size': 128, 'cache_size': 128, 'lookahead_size': 32},
                {'block_size': 512, 'read_size': 256, 'prog_size': 256, 'cache_size': 256, 'lookahead_size': 32},
                {'block_size': 4096, 'read_size': 128, 'prog_size': 128, 'cache_size': 128, 'lookahead_size': 32},
                {'block_size': 4096, 'read_size': 256, 'prog_size': 256, 'cache_size': 256, 'lookahead_size': 32},
            ]


# Error messages
ERROR_DEVICE_NOT_MOUNTED = "Device not mounted"
ERROR_INVALID_DEVICE_PATH = "Invalid device path"
ERROR_DEVICE_ALREADY_MOUNTED = "Device already mounted"
ERROR_PATH_NOT_FOUND = "Path not found"
ERROR_FILE_NOT_FOUND = "File not found"
ERROR_FAILED_TO_UNMOUNT = "Failed to unmount"

# Application state
config = Config()
active_mounts: Dict[str, Dict[str, Any]] = {}

# Flask app
app = Flask(__name__)


def ensure_mount_dir() -> None:
    """Ensure mount directory exists"""
    os.makedirs(config.MOUNT_BASE, exist_ok=True)


def unmount_fuse(mount_point: str) -> bool:
    """Unmount a FUSE filesystem

    Args:
        mount_point: Path to the mounted filesystem

    Returns:
        True if unmount succeeded, False otherwise
    """
    try:
        subprocess.run(['fusermount', '-u', mount_point], check=True, capture_output=True)
        logger.info("Unmounted %s using fusermount", mount_point)
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.run(['umount', '-l', mount_point], check=True, capture_output=True)
            logger.info("Unmounted %s using umount -l", mount_point)
            return True
        except subprocess.CalledProcessError:
            logger.warning("Failed to unmount %s", mount_point)
            return False


def force_cleanup_mount_point(mount_point: str) -> bool:
    """Forcefully clean up a mount point

    Args:
        mount_point: Path to the mount point to clean up

    Returns:
        True if cleanup succeeded, False otherwise
    """
    if not os.path.exists(mount_point):
        return True

    logger.info("Attempting to clean up mount point: %s", mount_point)

    # Try unmounting multiple times with different methods
    unmount_commands = [
        ['fusermount', '-uz', mount_point],
        ['umount', '-l', mount_point],
    ]

    for cmd in unmount_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=2)
            if result.returncode == 0:
                logger.debug("Unmounted using: %s", ' '.join(cmd))
            time.sleep(0.1)
        except Exception:
            continue

    # Try to remove directory
    for attempt in range(config.CLEANUP_ATTEMPTS):
        try:
            if not os.path.exists(mount_point):
                return True

            if os.path.isdir(mount_point):
                # First try normal removal
                try:
                    if not os.listdir(mount_point):  # If empty
                        os.rmdir(mount_point)
                        logger.debug("Removed empty directory")
                        return True
                except OSError:
                    pass

                # Try force removal
                try:
                    shutil.rmtree(mount_point, ignore_errors=False)
                    if not os.path.exists(mount_point):
                        logger.debug("Force removed directory")
                        return True
                except Exception as e:
                    logger.debug("Attempt %d/%d failed: %s", attempt + 1, config.CLEANUP_ATTEMPTS, e)

            elif os.path.isfile(mount_point):
                os.remove(mount_point)
                return True

            time.sleep(0.2)
        except Exception as e:
            if attempt == config.CLEANUP_ATTEMPTS - 1:
                logger.warning("Failed to remove after %d attempts: %s", attempt + 1, e)

    # Last resort: check if it's actually gone
    exists = os.path.exists(mount_point)
    if exists:
        logger.warning("Mount point still exists: %s", mount_point)
    return not exists


def cleanup_stale_mounts() -> None:
    """Clean up any stale mount points from previous runs"""
    if not os.path.exists(config.MOUNT_BASE):
        return

    logger.info("Checking for stale mounts...")
    items = os.listdir(config.MOUNT_BASE)

    if not items:
        logger.info("No stale mounts found")
        return

    cleaned = 0
    failed = []

    for item in items:
        mount_point = os.path.join(config.MOUNT_BASE, item)
        if os.path.isdir(mount_point):
            if force_cleanup_mount_point(mount_point):
                cleaned += 1
                logger.info("✓ Cleaned: %s", item)
            else:
                failed.append(mount_point)
                logger.error("✗ Failed: %s", item)

    logger.info("Cleaned %d mount point(s)", cleaned)

    if failed:
        logger.warning("%d mount point(s) could not be cleaned:", len(failed))
        for mp in failed:
            logger.warning("  - %s", mp)
        logger.warning("You may need to manually run:")
        logger.warning("  sudo fusermount -uz %s && sudo rm -rf %s", failed[0], failed[0])
        logger.warning("Or use the cleanup script: sudo ./cleanup_mounts.sh")


def get_block_devices() -> List[Dict[str, Any]]:
    """Scan for block devices that might contain littlefs

    Returns:
        List of device information dictionaries
    """
    devices = []
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,LABEL'],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        data = json.loads(result.stdout)

        for device in data.get('blockdevices', []):
            dev_path = f"/dev/{device['name']}"

            if device['type'] in ['disk', 'part']:
                mount = device.get('mountpoint', '')
                if not mount or config.MOUNT_BASE in mount:
                    devices.append({
                        'path': dev_path,
                        'name': device['name'],
                        'size': device['size'],
                        'label': device.get('label', 'Unlabeled'),
                        'mounted': dev_path in active_mounts
                    })
    except subprocess.CalledProcessError as e:
        logger.error("Error scanning devices: %s", e)
    except Exception as e:
        logger.error("Unexpected error scanning devices: %s", e)

    return devices


def detect_littlefs_params(device_path: str) -> Dict[str, Any]:
    """Auto-detect LittleFS parameters by trying to mount with common configs

    Args:
        device_path: Path to the block device

    Returns:
        Dictionary with 'success' boolean and either 'params' or 'error'
    """
    test_mount_base = "/tmp/littlefs_test_mount"

    for i, params in enumerate(config.COMMON_CONFIGS, 1):
        test_mount = f"{test_mount_base}_{i}"
        try:
            # Clean up any existing test mount
            if os.path.exists(test_mount):
                subprocess.run(['fusermount', '-uz', test_mount], timeout=1, capture_output=True)
                try:
                    os.rmdir(test_mount)
                except OSError:
                    pass

            os.makedirs(test_mount, exist_ok=True)

            cmd = [
                'lfs',
                f'--block_size={params["block_size"]}',
                f'--read_size={params["read_size"]}',
                f'--prog_size={params["prog_size"]}',
                f'--cache_size={params.get("cache_size", 64)}',
                f'--lookahead_size={params.get("lookahead_size", 32)}',
                '-o', 'allow_other',
                device_path,
                test_mount
            ]

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(config.DETECTION_TIMEOUT)

            # Check if mount succeeded by testing accessibility
            try:
                os.listdir(test_mount)

                # Success! Clean up and return
                if proc.poll() is None:
                    proc.terminate()
                    time.sleep(0.2)
                subprocess.run(['fusermount', '-uz', test_mount], timeout=1, capture_output=True)
                os.rmdir(test_mount)

                logger.info("Detected LittleFS parameters for %s: %s", device_path, params)
                return {
                    'success': True,
                    'params': params
                }
            except OSError:
                # Mount failed, cleanup and try next config
                if proc.poll() is None:
                    proc.terminate()
                subprocess.run(['fusermount', '-uz', test_mount], timeout=1, capture_output=True)

            # Cleanup
            try:
                os.rmdir(test_mount)
            except OSError:
                pass

        except Exception as e:
            logger.debug("Detection attempt %d failed: %s", i, e)
            # Cleanup on exception
            try:
                subprocess.run(['fusermount', '-uz', test_mount], timeout=1, capture_output=True)
                os.rmdir(test_mount)
            except OSError:
                pass
            continue

    logger.warning("Could not detect LittleFS parameters for %s", device_path)
    return {
        'success': False,
        'error': 'Could not detect LittleFS parameters'
    }


def try_mount_littlefs(device_path: str, mount_point: str) -> Dict[str, Any]:
    """Try to mount a littlefs filesystem with auto-detected parameters

    Args:
        device_path: Path to the block device
        mount_point: Path where the filesystem should be mounted

    Returns:
        Dictionary with 'success' boolean and either 'params'/'process' or 'error'
    """
    ensure_mount_dir()

    # Clean up any stale mount point
    if os.path.exists(mount_point):
        if not force_cleanup_mount_point(mount_point):
            error_msg = f'Could not clean up stale mount point at {mount_point}'
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    # Create mount point
    try:
        os.makedirs(mount_point, exist_ok=False)
    except FileExistsError:
        error_msg = f'Mount point still exists after cleanup: {mount_point}'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f'Could not create mount point: {str(e)}'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

    # Auto-detect parameters
    detection = detect_littlefs_params(device_path)

    if not detection['success']:
        return {'success': False, 'error': 'Could not detect LittleFS parameters'}

    params = detection['params']

    # Mount with detected parameters
    try:
        cmd = [
            'lfs',
            f'--block_size={params["block_size"]}',
            f'--read_size={params["read_size"]}',
            f'--prog_size={params["prog_size"]}',
            f'--cache_size={params.get("cache_size", 64)}',
            f'--lookahead_size={params.get("lookahead_size", 32)}',
            '-o', 'allow_other',
            device_path,
            mount_point
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(config.MOUNT_TIMEOUT)

        # Verify mount succeeded by checking accessibility
        # FUSE can daemonize (exit with code 0) or stay running
        mount_success = False
        for attempt in range(5):
            try:
                os.listdir(mount_point)
                mount_success = True
                break
            except OSError:
                if attempt < 4:
                    time.sleep(0.2)

        if mount_success:
            logger.info("Successfully mounted %s at %s", device_path, mount_point)
            return {
                'success': True,
                'params': params,
                'process': proc
            }

        # Mount failed
        if proc.poll() is None:
            proc.terminate()

        stderr = proc.stderr.read().decode() if proc.stderr else ''
        error_msg = 'Mount failed'
        if stderr:
            error_msg += f': {stderr.strip()}'

        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

    except Exception as e:
        error_msg = f'Mount error: {str(e)}'
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


def get_directory_listing(path: str) -> List[Dict[str, Any]]:
    """Get files and directories at path

    Args:
        path: Directory path to list

    Returns:
        List of file/directory information dictionaries
    """
    items = []
    try:
        for entry in os.scandir(path):
            stat = entry.stat()
            items.append({
                'name': entry.name,
                'type': 'dir' if entry.is_dir() else 'file',
                'size': format_size(stat.st_size) if entry.is_file() else '-',
                'modified': time.strftime(
                    '%Y-%m-%d %H:%M',
                    time.localtime(stat.st_mtime)
                ),
                'path': entry.path
            })
    except Exception as e:
        logger.error("Error listing directory %s: %s", path, e)

    return sorted(items, key=lambda x: (x['type'] != 'dir', x['name'].lower()))


def format_size(size: float) -> str:
    """Format byte size to human readable

    Args:
        size: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# HTML Template - loaded lazily to handle missing file gracefully
_html_template: Optional[str] = None


def load_template() -> str:
    """Load HTML template with error handling"""
    global _html_template
    if _html_template is None:
        try:
            with open('templates/index.html', 'r') as f:
                _html_template = f.read()
        except FileNotFoundError:
            logger.error("Template file not found: templates/index.html")
            raise
    return _html_template


# Routes

@app.route('/')
def index():
    """Render the main page"""
    return render_template_string(load_template())


@app.route('/api/devices')
def api_devices():
    """Get list of available block devices"""
    devices = get_block_devices()
    return jsonify(devices)


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Detect LittleFS parameters without mounting"""
    data = request.json
    device_path = data.get('device')

    if not device_path or not os.path.exists(device_path):
        return jsonify({'success': False, 'error': ERROR_INVALID_DEVICE_PATH}), 400

    result = detect_littlefs_params(device_path)
    return jsonify(result)


@app.route('/api/mount', methods=['POST'])
def api_mount():
    """Mount a LittleFS device"""
    data = request.json
    device_path = data.get('device')

    if not device_path or not os.path.exists(device_path):
        return jsonify({'success': False, 'error': ERROR_INVALID_DEVICE_PATH}), 400

    if device_path in active_mounts:
        return jsonify({'success': False, 'error': ERROR_DEVICE_ALREADY_MOUNTED}), 400

    mount_name = os.path.basename(device_path)
    mount_point = os.path.join(config.MOUNT_BASE, mount_name)

    result = try_mount_littlefs(device_path, mount_point)

    if result['success']:
        active_mounts[device_path] = {
            'mount_point': mount_point,
            'params': result['params'],
            'process': result['process']
        }
        return jsonify({
            'success': True,
            'mount_point': mount_point,
            'params': result['params']
        })
    else:
        try:
            os.rmdir(mount_point)
        except Exception:
            pass
        return jsonify(result), 400


@app.route('/api/unmount', methods=['POST'])
def api_unmount():
    """Unmount a LittleFS device"""
    data = request.json
    device_path = data.get('device')

    if device_path not in active_mounts:
        return jsonify({'success': False, 'error': ERROR_DEVICE_NOT_MOUNTED}), 400

    mount_info = active_mounts[device_path]
    mount_point = mount_info['mount_point']

    if 'process' in mount_info:
        try:
            mount_info['process'].terminate()
        except Exception:
            pass

    if unmount_fuse(mount_point):
        try:
            os.rmdir(mount_point)
        except Exception:
            pass
        del active_mounts[device_path]
        logger.info("Unmounted device: %s", device_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': ERROR_FAILED_TO_UNMOUNT}), 500


@app.route('/api/list')
def api_list():
    """List files in a directory on mounted device"""
    device_path = request.args.get('device')
    subpath = request.args.get('path', '')

    if device_path not in active_mounts:
        return jsonify({'success': False, 'error': ERROR_DEVICE_NOT_MOUNTED}), 400

    mount_point = active_mounts[device_path]['mount_point']
    full_path = os.path.join(mount_point, subpath.lstrip('/'))

    if not os.path.exists(full_path):
        return jsonify({'success': False, 'error': ERROR_PATH_NOT_FOUND}), 404

    items = get_directory_listing(full_path)
    return jsonify({
        'success': True,
        'items': items,
        'path': subpath or '/'
    })


@app.route('/api/download')
def api_download():
    """Download a file from mounted device"""
    device_path = request.args.get('device')
    file_path = request.args.get('path')

    if device_path not in active_mounts:
        return jsonify({'success': False, 'error': ERROR_DEVICE_NOT_MOUNTED}), 400

    mount_point = active_mounts[device_path]['mount_point']
    full_path = os.path.join(mount_point, file_path.lstrip('/'))

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({'success': False, 'error': ERROR_FILE_NOT_FOUND}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=os.path.basename(full_path)
    )


@app.route('/api/extract-all', methods=['POST'])
def api_extract_all():
    """Extract all files from mounted device to local filesystem"""
    data = request.json
    device_path = data.get('device')
    dest_path = data.get(
        'destination',
        os.path.expanduser(config.DEFAULT_EXPORT_PATH)
    )

    if device_path not in active_mounts:
        return jsonify({'success': False, 'error': ERROR_DEVICE_NOT_MOUNTED}), 400

    mount_point = active_mounts[device_path]['mount_point']

    try:
        os.makedirs(dest_path, exist_ok=True)

        for item in os.listdir(mount_point):
            src = os.path.join(mount_point, item)
            dst = os.path.join(dest_path, item)

            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        logger.info("Extracted all files from %s to %s", device_path, dest_path)
        return jsonify({
            'success': True,
            'destination': dest_path
        })
    except Exception as e:
        logger.error("Error extracting files: %s", e)
        return jsonify({'success': False, 'error': str(e)}), 500


def check_permissions() -> None:
    """Check if we have necessary permissions to run the application"""
    if os.geteuid() != 0:
        logger.warning("=" * 60)
        logger.warning("WARNING: Not running as root")
        logger.warning("=" * 60)
        logger.warning("This app needs root privileges to:")
        logger.warning("  - Access block devices (e.g., /dev/mmcblk0)")
        logger.warning("  - Mount FUSE filesystems")
        logger.warning("  - Clean up stale mounts")
        logger.warning("")
        logger.warning("Please run with sudo:")
        logger.warning("  sudo python3 app.py")
        logger.warning("=" * 60)
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
        print()


if __name__ == '__main__':
    check_permissions()
    ensure_mount_dir()
    cleanup_stale_mounts()
    logger.info("LittleFS Browser starting...")
    app.run(debug=True, host='0.0.0.0', port=5000)
