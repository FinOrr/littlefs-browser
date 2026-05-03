#!/usr/bin/env bash
# build-binary.sh - build a self-contained littlefs-browser executable
#
# Produces: dist/littlefs-browser  (single binary, no runtime deps)
#
# Requirements (Ubuntu/Debian):
#   sudo apt install -y build-essential libfuse-dev pkg-config python3 python3-pip
#   pip install pyinstaller
#   node / npm (for the frontend)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

ARCH="$(uname -m)"
OUTPUT="dist/littlefs-browser-linux-${ARCH}"

echo "[1/4] Building React frontend..."
pushd frontend >/dev/null
npm ci 2>/dev/null || npm install
npm run build
popd >/dev/null

echo "[2/4] Compiling littlefs-fuse..."
LFS_SRC="$(mktemp -d)"
git clone --depth 1 https://github.com/littlefs-project/littlefs-fuse "$LFS_SRC"
make -C "$LFS_SRC" -j"$(nproc)"

mkdir -p lfs_bundled
cp "$LFS_SRC/lfs" lfs_bundled/lfs
chmod +x lfs_bundled/lfs
rm -rf "$LFS_SRC"

echo "[3/4] Installing Python build deps..."
pip install --quiet pyinstaller flask flask-cors

echo "[4/4] Running PyInstaller..."
pyinstaller --clean --noconfirm littlefs_browser.spec

mv dist/littlefs-browser "$OUTPUT"

echo ""
echo "Done: $OUTPUT"
echo ""
echo "Run with:  sudo ./$OUTPUT"
echo "Then open: http://localhost:5000"
