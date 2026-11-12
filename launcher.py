"""
SmoothScroll Windows 11 — Native Desktop Launcher
Starts the low-level mouse hook, system tray, and native Tkinter GUI.
"""

import sys
import os
import time
import threading
from PIL import Image

# Dynamic path resolution for PyInstaller
if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS
    current_dir = os.path.dirname(sys.executable)
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = bundle_dir

sys.path.insert(0, bundle_dir)

from core.hook import hook_manager
from gui import launch_gui

def get_tray_icon_image():
    icon_path = os.path.join(bundle_dir, "src-tauri", "icons", "32x32.png")
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass
    return Image.new("RGBA", (32, 32), (56, 189, 248, 255))

def setup_system_tray(gui_app, root):
    try:
        import pystray
        from pystray import MenuItem as item

        def on_open_settings(icon, item):
            root.after(0, gui_app.show_from_tray)

        def on_toggle(icon, item):
            root.after(0, gui_app._toggle_power)
            status = "ON" if hook_manager.is_enabled else "PAUSED"
            icon.title = f"Glidify ({status})"

        def on_exit(icon, item):
            hook_manager.stop()
            icon.stop()
            root.after(0, root.destroy)
            os._exit(0)

        menu = (
            item("Settings & Tuning", on_open_settings, default=True),
            item("Toggle Active", on_toggle),
            item("Exit Glidify", on_exit)
        )

        tray_icon = pystray.Icon("Glidify", get_tray_icon_image(), "Glidify (Active)", menu)
        tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
        tray_thread.start()
    except Exception as e:
        print(f"[Glidify Tray] System tray fallback: {e}")

def main():
    print("[Glidify] Starting background input hook...")
    hook_manager.start()

    print("[Glidify] Launching native Windows 11 GUI...")
    root, gui_app = launch_gui()

    # System Tray Integration
    setup_system_tray(gui_app, root)

    # Check start minimized argument or setting
    start_minimized = hook_manager.settings.start_minimized or ("--minimized" in sys.argv)
    if start_minimized:
        root.withdraw()
    else:
        root.deiconify()

    # Run native desktop GUI main loop
    root.mainloop()

if __name__ == "__main__":
    main()
