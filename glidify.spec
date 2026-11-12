# -*- mode: python ; coding: utf-8 -*-
# HaiGlide Windows 11 — Native GUI PyInstaller Spec
# By Haistellar

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('src-tauri/icons', 'src-tauri/icons')
]
binaries = []
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    '_tkinter',
    'ctypes',
    'ctypes.wintypes',
    'threading',
    'math',
    'time',
    'json',
]

# Collect Pystray & Pillow
wdatas, wbins, wimports = collect_all('pystray')
datas += wdatas
binaries += wbins
hiddenimports += wimports
hiddenimports += collect_submodules('PIL')

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'cv2', 'test', 'unittest', 'email'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Glidify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pure native GUI desktop window & system tray
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src-tauri/icons/icon.ico',
)
