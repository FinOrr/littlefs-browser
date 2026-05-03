#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
OUT_DIR="$ROOT_DIR/releases"
VERSION=${1:-"$(date +%Y%m%d)"}

echo "[1/3] Building frontend..."
pushd "$ROOT_DIR/frontend" >/dev/null
if command -v npm >/dev/null 2>&1; then
  npm ci || npm install
  npm run build
else
  echo "npm not found; cannot build frontend." >&2
  exit 1
fi
popd >/dev/null

echo "[2/3] Preparing package..."
WORKDIR=$(mktemp -d)
mkdir -p "$WORKDIR/frontend/dist"
cp "$ROOT_DIR/app.py" "$WORKDIR/"
cp "$ROOT_DIR/requirements.txt" "$WORKDIR/"
cp -r "$ROOT_DIR/frontend/dist" "$WORKDIR/frontend/"
cp "$ROOT_DIR/run.sh" "$WORKDIR/" 2>/dev/null || true
cp -r "$ROOT_DIR/templates" "$WORKDIR/" 2>/dev/null || true

cat >"$WORKDIR/README-RUN.txt" <<'EOF'
LittleFS Browser - Portable Bundle
==================================

Prerequisites (Ubuntu/Debian):
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip build-essential libfuse-dev pkg-config git util-linux

Install littlefs-fuse (if not installed):
  git clone https://github.com/littlefs-project/littlefs-fuse
  cd littlefs-fuse && make -j$(nproc)
  sudo cp lfs /usr/local/bin/lfs && sudo chmod +x /usr/local/bin/lfs

Create venv and run:
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  sudo -E .venv/bin/python app.py

Open http://localhost:5000
EOF

mkdir -p "$OUT_DIR"
ARCHIVE="$OUT_DIR/littlefs-browser-${VERSION}.tar.gz"

echo "[3/3] Creating archive $ARCHIVE"
tar -C "$WORKDIR" -czf "$ARCHIVE" .
rm -rf "$WORKDIR"
echo "Done: $ARCHIVE"
