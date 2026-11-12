"""
SmoothScroll Windows Input Hook (High performance Win64 ctypes)
"""

import sys
import time
import threading
from typing import Optional, Tuple
from core.config import AppSettings
from core.physics import ScrollPhysicsEngine

SMOOTH_EXTRA_INFO = 0x534D5343  # 'SMSC'

# Win32 Constants
WH_MOUSE_LL = 14
WM_MOUSEWHEEL = 0x020A
WM_MOUSEHWHEEL = 0x020E
INPUT_MOUSE = 0
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
VK_CONTROL = 0x11
VK_MENU = 0x12
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

class HookManager:
    def __init__(self):
        self.engine = ScrollPhysicsEngine()
        self.settings = AppSettings.load()
        self.is_enabled = self.settings.enabled
        self.is_foreground_blacklisted = False
        self.is_running = False
        self.hook_handle = None
        self.hook_proc_ref = None
        self._lock = threading.Lock()

    def update_settings(self, new_settings: AppSettings):
        with self._lock:
            self.settings = new_settings
            self.is_enabled = new_settings.enabled
            self.settings.save()

    def get_metrics(self) -> Tuple[int, int]:
        return self.engine.total_intercepted, self.engine.total_dispatched

    def get_foreground_process(self) -> Optional[str]:
        if sys.platform != "win32":
            return "explorer.exe"

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_process:
            return None

        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
                full_path = buf.value
                return full_path.split("\\")[-1]
        finally:
            kernel32.CloseHandle(h_process)
        return None

    def start(self):
        if self.is_running:
            return
        self.is_running = True

        # 1. Physics dispatch loop
        threading.Thread(target=self._physics_loop, daemon=True).start()

        # 2. Background process monitor (keeps hook ultra-fast without blocking on process queries)
        threading.Thread(target=self._process_monitor_loop, daemon=True).start()

        # 3. Windows input hook
        if sys.platform == "win32":
            threading.Thread(target=self._hook_message_loop, daemon=True).start()
        else:
            print("[SmoothScroll Hook] Non-windows platform - running in mock mode")

    def stop(self):
        self.is_running = False
        if sys.platform == "win32" and self.hook_handle:
            import ctypes
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None

    def _process_monitor_loop(self):
        """Polls foreground process once every 350ms to keep hook callback zero-latency."""
        while self.is_running:
            try:
                proc = self.get_foreground_process()
                if proc and self.settings.blacklisted_apps:
                    is_bl = any(proc.lower() == b.lower() for b in self.settings.blacklisted_apps)
                else:
                    is_bl = False
                self.is_foreground_blacklisted = is_bl
            except Exception:
                self.is_foreground_blacklisted = False
            time.sleep(0.35)

    def _physics_loop(self):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception:
                pass

        last_time = time.perf_counter()

        while self.is_running:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            with self._lock:
                settings = self.settings
                has_motion = self.engine.has_active_motion()
                v_step = 0
                h_step = 0
                if has_motion:
                    v_step, h_step = self.engine.update(dt, settings)
                    has_motion = self.engine.has_active_motion()

            if v_step != 0:
                self._send_wheel_input(v_step, is_horizontal=False)
            if h_step != 0:
                self._send_wheel_input(h_step, is_horizontal=True)

            if has_motion:
                time.sleep(0.005)  # ~200Hz refresh rate
            else:
                time.sleep(0.015)

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass

    def _send_wheel_input(self, delta: int, is_horizontal: bool):
        if sys.platform != "win32":
            return

        import ctypes
        from ctypes import wintypes

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT)]
            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        user32 = ctypes.windll.user32
        user32.SendInput.restype = wintypes.UINT
        user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]

        flags = MOUSEEVENTF_HWHEEL if is_horizontal else MOUSEEVENTF_WHEEL
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.mi.dx = 0
        inp.mi.dy = 0
        inp.mi.mouseData = delta & 0xFFFFFFFF
        inp.mi.dwFlags = flags
        inp.mi.time = 0
        inp.mi.dwExtraInfo = SMOOTH_EXTRA_INFO

        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _hook_message_loop(self):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # 64-bit correct Win32 types
        LRESULT = ctypes.c_int64
        user32.CallNextHookEx.restype = LRESULT
        user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.SetWindowsHookExW.restype = ctypes.c_void_p
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wintypes.HINSTANCE, wintypes.DWORD]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]

        class MSLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("pt_x", wintypes.LONG),
                ("pt_y", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t),
            ]

        HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        def low_level_mouse_proc(n_code, w_param, l_param):
            try:
                # ── CRITICAL: Zero overhead immediate bypass for mouse movement and clicks ──
                # 0x020A = WM_MOUSEWHEEL, 0x020E = WM_MOUSEHWHEEL
                if n_code < 0 or (w_param != WM_MOUSEWHEEL and w_param != WM_MOUSEHWHEEL):
                    return user32.CallNextHookEx(None, n_code, w_param, l_param)

                hook_data = MSLLHOOKSTRUCT.from_address(l_param)

                # Skip our own synthesized smooth events to prevent infinite loop
                if hook_data.dwExtraInfo == SMOOTH_EXTRA_INFO:
                    return user32.CallNextHookEx(None, n_code, w_param, l_param)

                # Fast check: disabled or blacklisted foreground app
                if not self.is_enabled or self.is_foreground_blacklisted:
                    return user32.CallNextHookEx(None, n_code, w_param, l_param)

                # Fast check: Ctrl key pressed (allow instant native zoom in Chrome/Edge)
                if self.settings.ctrl_passthrough_zoom and (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000):
                    return user32.CallNextHookEx(None, n_code, w_param, l_param)

                # Extract signed 16-bit delta
                raw_delta = ctypes.c_short((hook_data.mouseData >> 16) & 0xFFFF).value
                is_hwheel = (w_param == WM_MOUSEHWHEEL)
                is_trackpad = (abs(raw_delta) % 120 != 0) or (abs(raw_delta) < 120)

                with self._lock:
                    consumed = self.engine.on_input(raw_delta, is_hwheel, is_trackpad, self.settings)

                if consumed:
                    return 1  # Swallow the raw jerky wheel notch

            except Exception:
                pass

            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        self.hook_proc_ref = HOOKPROC(low_level_mouse_proc)
        self.hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, self.hook_proc_ref, None, 0)

        if not self.hook_handle:
            print("[SmoothScroll] Failed to install WH_MOUSE_LL hook")
            return

        msg = wintypes.MSG()
        while self.is_running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook_handle:
            user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None

hook_manager = HookManager()
