#!/usr/bin/env python3
"""
LittleFS Browser - Flask Web Interface
A professional tool for browsing LittleFS filesystems from embedded devices
"""

from flask import Flask, render_template_string, jsonify, send_file, request
import os
import subprocess
import json
import shutil
from pathlib import Path
import time

app = Flask(__name__)

# Configuration
MOUNT_BASE = "/tmp/littlefs_mounts"

# Active mounts tracking
active_mounts = {}


def ensure_mount_dir():
    """Ensure mount directory exists"""
    os.makedirs(MOUNT_BASE, exist_ok=True)


def cleanup_stale_mounts():
    """Clean up any stale mount points from previous runs"""
    if not os.path.exists(MOUNT_BASE):
        return

    print("Checking for stale mounts...")
    for item in os.listdir(MOUNT_BASE):
        mount_point = os.path.join(MOUNT_BASE, item)
        if os.path.isdir(mount_point):
            try:
                # Try to unmount
                unmount_fuse(mount_point)
                time.sleep(0.1)
            except:
                pass

            # Try to remove directory
            try:
                if not os.listdir(mount_point):
                    os.rmdir(mount_point)
                    print(f"Cleaned up stale mount: {mount_point}")
            except Exception as e:
                print(f"Could not remove {mount_point}: {e}")


def get_block_devices():
    """Scan for block devices that might contain littlefs"""
    devices = []
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,LABEL'],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)

        for device in data.get('blockdevices', []):
            dev_path = f"/dev/{device['name']}"

            if device['type'] in ['disk', 'part']:
                mount = device.get('mountpoint', '')
                if not mount or MOUNT_BASE in mount:
                    devices.append({
                        'path': dev_path,
                        'name': device['name'],
                        'size': device['size'],
                        'label': device.get('label', 'Unlabeled'),
                        'mounted': dev_path in active_mounts
                    })
    except Exception as e:
        print(f"Error scanning devices: {e}")

    return devices


def detect_littlefs_params(device_path):
    """Auto-detect LittleFS parameters using --stat"""
    # Extended parameter ranges for detection
    block_sizes = [512, 4096, 8192, 16384]
    read_sizes = [4, 8, 16, 32, 64, 128, 256, 512, 1024]
    prog_sizes = [4, 8, 16, 32, 64, 128, 256, 512, 1024]

    for block_size in block_sizes:
        for read_size in read_sizes:
            for prog_size in prog_sizes:
                try:
                    cmd = [
                        'lfs',
                        '--stat',
                        f'--block_size={block_size}',
                        f'--read_size={read_size}',
                        f'--prog_size={prog_size}',
                        device_path
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    # Check if stat succeeded by looking for filesystem info
                    if 'disk_version' in result.stdout or 'block_count' in result.stdout:
                        return {
                            'success': True,
                            'params': {
                                'block_size': block_size,
                                'read_size': read_size,
                                'prog_size': prog_size
                            },
                            'info': result.stdout
                        }

                except Exception:
                    continue

    return {
        'success': False,
        'error': 'Could not detect LittleFS parameters'
    }


def try_mount_littlefs(device_path, mount_point):
    """Try to mount a littlefs filesystem with auto-detected parameters"""
    ensure_mount_dir()

    # Clean up any stale mount point
    if os.path.exists(mount_point):
        # Try to unmount if it's already mounted
        try:
            unmount_fuse(mount_point)
        except:
            pass

        # Remove the directory if it exists
        try:
            if os.path.isdir(mount_point):
                # Check if it's empty
                if not os.listdir(mount_point):
                    os.rmdir(mount_point)
                else:
                    # Try to unmount again in case it's a stale FUSE mount
                    unmount_fuse(mount_point)
                    time.sleep(0.2)
                    if os.path.exists(mount_point) and not os.listdir(mount_point):
                        os.rmdir(mount_point)
            elif os.path.isfile(mount_point):
                os.remove(mount_point)
        except Exception as e:
            print(f"Warning: Could not clean up mount point: {e}")

    # Create fresh mount point
    os.makedirs(mount_point, exist_ok=True)

    # First, try to auto-detect parameters
    print(f"Auto-detecting parameters for {device_path}...")
    detection = detect_littlefs_params(device_path)

    if not detection['success']:
        return {
            'success': False,
            'error': 'Could not detect LittleFS parameters. Device may not contain a valid LittleFS filesystem.'
        }

    params = detection['params']
    print(f"Detected parameters: {params}")

    # Now mount with the detected parameters
    try:
        cmd = [
            'lfs',
            f'--block_size={params["block_size"]}',
            f'--read_size={params["read_size"]}',
            f'--prog_size={params["prog_size"]}',
            device_path,
            mount_point
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for FUSE mount to be ready (increased timeout)
        time.sleep(0.5)

        # Verify mount is working
        if proc.poll() is None:
            # Process is still running, check if mount point is accessible
            for attempt in range(5):
                try:
                    os.listdir(mount_point)
                    print(f"Successfully mounted {device_path} at {mount_point}")
                    return {
                        'success': True,
                        'params': params,
                        'process': proc
                    }
                except OSError:
                    if attempt < 4:
                        time.sleep(0.2)
                    continue

            # If we get here, mount didn't work
            proc.terminate()
            return {
                'success': False,
                'error': 'Mount process started but filesystem not accessible'
            }
        else:
            stderr = proc.stderr.read().decode() if proc.stderr else ''
            return {
                'success': False,
                'error': f'Mount process failed: {stderr}'
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'Mount error: {str(e)}'
        }


def unmount_fuse(mount_point):
    """Unmount a FUSE filesystem"""
    try:
        subprocess.run(['fusermount', '-u', mount_point], check=True)
        return True
    except:
        try:
            subprocess.run(['umount', '-l', mount_point], check=True)
            return True
        except:
            return False


def get_directory_listing(path):
    """Get files and directories at path"""
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
        print(f"Error listing directory: {e}")

    return sorted(items, key=lambda x: (x['type'] != 'dir', x['name'].lower()))


def format_size(size):
    """Format byte size to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# HTML Template
HTML_TEMPLATE = open('templates/index.html').read()

# Routes


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/devices')
def api_devices():
    devices = get_block_devices()
    return jsonify(devices)


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Detect LittleFS parameters without mounting"""
    data = request.json
    device_path = data.get('device')

    if not device_path or not os.path.exists(device_path):
        return jsonify({
            'success': False,
            'error': 'Invalid device path'
        }), 400

    result = detect_littlefs_params(device_path)
    return jsonify(result)


@app.route('/api/mount', methods=['POST'])
def api_mount():
    data = request.json
    device_path = data.get('device')

    if not device_path or not os.path.exists(device_path):
        return jsonify({
            'success': False,
            'error': 'Invalid device path'
        }), 400

    if device_path in active_mounts:
        return jsonify({
            'success': False,
            'error': 'Device already mounted'
        }), 400

    mount_name = os.path.basename(device_path)
    mount_point = os.path.join(MOUNT_BASE, mount_name)

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
        except:
            pass
        return jsonify(result), 400


@app.route('/api/unmount', methods=['POST'])
def api_unmount():
    data = request.json
    device_path = data.get('device')

    if device_path not in active_mounts:
        return jsonify({
            'success': False,
            'error': 'Device not mounted'
        }), 400

    mount_info = active_mounts[device_path]
    mount_point = mount_info['mount_point']

    if 'process' in mount_info:
        try:
            mount_info['process'].terminate()
        except:
            pass

    if unmount_fuse(mount_point):
        try:
            os.rmdir(mount_point)
        except:
            pass
        del active_mounts[device_path]
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to unmount'
        }), 500


@app.route('/api/list')
def api_list():
    device_path = request.args.get('device')
    subpath = request.args.get('path', '')

    if device_path not in active_mounts:
        return jsonify({
            'success': False,
            'error': 'Device not mounted'
        }), 400

    mount_point = active_mounts[device_path]['mount_point']
    full_path = os.path.join(mount_point, subpath.lstrip('/'))

    if not os.path.exists(full_path):
        return jsonify({
            'success': False,
            'error': 'Path not found'
        }), 404

    items = get_directory_listing(full_path)
    return jsonify({
        'success': True,
        'items': items,
        'path': subpath or '/'
    })


@app.route('/api/download')
def api_download():
    device_path = request.args.get('device')
    file_path = request.args.get('path')

    if device_path not in active_mounts:
        return jsonify({
            'success': False,
            'error': 'Device not mounted'
        }), 400

    mount_point = active_mounts[device_path]['mount_point']
    full_path = os.path.join(mount_point, file_path.lstrip('/'))

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({
            'success': False,
            'error': 'File not found'
        }), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=os.path.basename(full_path)
    )


@app.route('/api/extract-all', methods=['POST'])
def api_extract_all():
    data = request.json
    device_path = data.get('device')
    dest_path = data.get(
        'destination',
        os.path.expanduser('~/Downloads/littlefs_export')
    )

    if device_path not in active_mounts:
        return jsonify({
            'success': False,
            'error': 'Device not mounted'
        }), 400

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

        return jsonify({
            'success': True,
            'destination': dest_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    ensure_mount_dir()
    cleanup_stale_mounts()
    print("=" * 60)
    print("  LittleFS Browser")
    print("=" * 60)
    print(f"  Starting server on http://localhost:5000")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
