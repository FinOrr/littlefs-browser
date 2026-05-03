# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for littlefs-browser
#
# Before running pyinstaller, the build script must:
#   1. Build the React frontend:  cd frontend && npm run build
#   2. Compile littlefs-fuse and copy the 'lfs' binary to lfs_bundled/lfs
#
# Then run:
#   pyinstaller littlefs_browser.spec

import os

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    # Bundle the pre-compiled lfs binary at the root of _MEIPASS so
    # get_lfs_binary() in app.py can find it as os.path.join(_MEIPASS, 'lfs')
    binaries=[('lfs_bundled/lfs', '.')],
    # Bundle the built React frontend so Flask can serve it
    datas=[('frontend/dist', 'frontend/dist')],
    hiddenimports=[
        'flask',
        'flask_cors',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.exceptions',
        'jinja2',
        'click',
        'itsdangerous',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='littlefs-browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
