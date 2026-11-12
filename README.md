# Glidify for Windows 11

**Glidify** brings authentic **Apple Magic Trackpad kinetic glide scrolling** to Windows 11. It transforms standard, choppy mouse wheel notches and rigid trackpad movements into silky-smooth, fluid inertia glides with viscous exponential decay physics.

Engineered with high-speed kernel-level input hooks, automatic Authenticode code signing, and a native Windows 11 Fluent Dark desktop interface.

---

## ✨ Features

- **Apple Magic Trackpad Kinetic Glide (`appleGlide`)**:
  - Implements authentic macOS momentum physics where every scroll flick carries forward into a smooth coasting glide.
  - Viscous exponential decay ensures smooth deceleration without abrupt stops.
  - Multi-page flick inertia lets you coast through long documents and codebases effortlessly.

- **Precision Touchpad Enhancement**:
  - Jitter deadzone filter removes micro-trembling while resting fingers on the glass.
  - Post-release momentum multiplier accelerates fluid coasting when fingers leave the trackpad.
  - Independent trackpad direction inversion (natural scrolling for touchpad while preserving traditional direction for physical mouse wheels).

- **Ultra-Low Latency Win32 Input Hook (`WH_MOUSE_LL`)**:
  - Sub-microsecond immediate bypass for mouse movement and button clicks (`WM_MOUSEMOVE` has zero delay).
  - High-frequency micro-step dispatch (200Hz–250Hz) with 1ms multimedia timer accuracy (`timeBeginPeriod(1)`).
  - Sub-delta precision accumulator delivers hardware-accelerated sub-pixel smooth scrolling in Chrome, Edge, VS Code, and Windows Explorer.

- **Native Windows 11 Fluent Desktop GUI**:
  - Built with a native dark desktop interface — zero web server dependencies, no port collisions, and instant loading.
  - **Live Interactive Playground**: In-app test area to test scroll physics in real-time.
  - **1-Click Presets**: *Apple Magic Glide*, *Deep Coasting Glide*, *Snappy Mac*, *Direct Minimal*.
  - Live telemetry dashboard tracking intercepted events and smooth frame dispatches.

- **Automatic Digital Code Signing**:
  - Automatically generates and installs a trusted local developer certificate (`CN=Glidify (Haistellar)`).
  - Digitally signs `Glidify.exe` with Authenticode to prevent Windows SmartScreen "Untrusted / Unknown Publisher" prompts.

- **System & Tray Integration**:
  - Silent background operation with system tray icon.
  - Application blacklist (auto-detects foreground game/CAD windows to bypass smoothing).
  - Modifier key passthrough: holding `Ctrl` enables instant native browser zoom; holding `Alt` doubles acceleration.

---

## 🚀 Quick Start (Running on Windows 11)

### Option 1: Run Pre-Built Executable
Double-click `dist\Glidify.exe` to launch immediately.

### Option 2: Run from Python Source
Double-click `run_glidify.bat` (automatically installs `requirements.txt` and starts Glidify).

### Option 3: Build & Sign Standalone Executable
Double-click `build_exe_windows.bat` to recompile and digitally sign `dist\Glidify.exe`.

---

## 🛠️ Project Structure

```
glidify/
├── core/
│   ├── config.py             # Settings persistence in %APPDATA%\Glidify\settings.json
│   ├── hook.py               # 64-bit WH_MOUSE_LL hook & SendInput dispatcher
│   └── physics.py            # Apple Magic Trackpad kinetic glide physics engine
├── gui.py                    # Native Windows 11 Fluent Dark desktop interface
├── launcher.py               # Main entry point & system tray manager
├── glidify.spec              # Standalone PyInstaller specification
├── build_exe_windows.bat     # One-click Windows .exe builder & code signer
├── run_glidify.bat           # Direct launcher
├── requirements.txt          # Python dependencies (pystray, Pillow, pyinstaller)
├── scripts/
│   └── sign_app.ps1          # Automatic Authenticode code signing script
└── dist/
    ├── Glidify.exe           # Standalone signed executable
    └── Glidify.cer           # Public signing certificate
```

---

## 📄 License

MIT License — Haistellar.
