use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};
use once_cell::sync::Lazy;

use winapi::shared::minwindef::{DWORD, HINSTANCE, LPARAM, LRESULT, WPARAM};
use winapi::shared::windef::HHOOK;
use winapi::um::processthreadsapi::OpenProcess;
use winapi::um::psapi::K32GetModuleBaseNameA;
use winapi::um::timeapi::{timeBeginPeriod, timeEndPeriod};
use winapi::um::winbase::PROCESS_QUERY_LIMITED_INFORMATION;
use winapi::um::winuser::{
    CallNextHookEx, GetAsyncKeyState, GetForegroundWindow, GetMessageW,
    GetWindowThreadProcessId, SetWindowsHookExW, UnhookWindowsHookEx,
    INPUT, INPUT_MOUSE, MOUSEEVENTF_HWHEEL, MOUSEEVENTF_WHEEL, MOUSEINPUT,
    MSLLHOOKSTRUCT, SendInput, VK_CONTROL, VK_MENU, WH_MOUSE_LL,
    WM_MOUSEHWHEEL, WM_MOUSEWHEEL,
};

use crate::config::AppSettings;
use crate::physics::ScrollPhysicsEngine;

pub const SMOOTH_EXTRA_INFO: usize = 0x534D5343; // 'SMSC'

static ENGINE: Lazy<Arc<Mutex<ScrollPhysicsEngine>>> =
    Lazy::new(|| Arc::new(Mutex::new(ScrollPhysicsEngine::new())));
static SETTINGS: Lazy<Arc<Mutex<AppSettings>>> =
    Lazy::new(|| Arc::new(Mutex::new(AppSettings::default())));
static IS_RUNNING: AtomicBool = AtomicBool::new(false);
static HOOK_HANDLE: Lazy<Mutex<Option<usize>>> = Lazy::new(|| Mutex::new(None));

pub fn update_runtime_settings(new_settings: AppSettings) {
    if let Ok(mut settings) = SETTINGS.lock() {
        *settings = new_settings;
    }
}

pub fn get_engine_metrics() -> (u64, u64) {
    if let Ok(engine) = ENGINE.lock() {
        (engine.total_intercepted_events, engine.total_dispatched_frames)
    } else {
        (0, 0)
    }
}

pub fn get_foreground_process_name() -> Option<String> {
    unsafe {
        let hwnd = GetForegroundWindow();
        if hwnd.is_null() {
            return None;
        }

        let mut process_id: DWORD = 0;
        GetWindowThreadProcessId(hwnd, &mut process_id);
        if process_id == 0 {
            return None;
        }

        let h_process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, process_id);
        if h_process.is_null() {
            return None;
        }

        let mut buffer = [0u8; 260];
        let len = K32GetModuleBaseNameA(h_process, std::ptr::null_mut(), buffer.as_mut_ptr() as *mut i8, buffer.len() as DWORD);
        winapi::um::handleapi::CloseHandle(h_process);

        if len > 0 {
            let name = String::from_utf8_lossy(&buffer[..len as usize]).to_string();
            return Some(name);
        }
    }
    None
}

/// Start the background low-level hook and dispatch worker thread.
pub fn start_hook(initial_settings: AppSettings) {
    if IS_RUNNING.swap(true, Ordering::SeqCst) {
        return; // Already running
    }

    update_runtime_settings(initial_settings);

    // Spawn the high-frequency physics dispatch worker
    thread::spawn(move || {
        physics_worker_loop();
    });

    // Spawn the Windows Hook message pump thread
    thread::spawn(move || {
        hook_message_loop();
    });
}

pub fn stop_hook() {
    IS_RUNNING.store(false, Ordering::SeqCst);
    if let Ok(mut handle) = HOOK_HANDLE.lock() {
        if let Some(h) = handle.take() {
            unsafe {
                UnhookWindowsHookEx(h as HHOOK);
            }
        }
    }
}

fn physics_worker_loop() {
    let timer_res_active = true;
    unsafe {
        timeBeginPeriod(1); // 1ms high resolution multimedia timer
    }

    let mut last_tick = Instant::now();

    while IS_RUNNING.load(Ordering::Relaxed) {
        let now = Instant::now();
        let dt = now.duration_since(last_tick).as_secs_f64();
        last_tick = now;

        let settings = {
            if let Ok(s) = SETTINGS.lock() {
                s.clone()
            } else {
                AppSettings::default()
            }
        };

        let mut v_step = 0;
        let mut h_step = 0;
        let mut has_motion = false;

        if let Ok(mut engine) = ENGINE.lock() {
            if engine.has_active_motion() {
                let steps = engine.update(dt, &settings);
                v_step = steps.0;
                h_step = steps.1;
                has_motion = engine.has_active_motion();
            }
        }

        if v_step != 0 {
            send_wheel_input(v_step, false);
        }
        if h_step != 0 {
            send_wheel_input(h_step, true);
        }

        if has_motion {
            // Target ~144Hz to 240Hz frame dispatch during smooth movement (~4-7ms)
            thread::sleep(Duration::from_millis(5));
        } else {
            // Low-power sleep when idle
            thread::sleep(Duration::from_millis(15));
        }
    }

    if timer_res_active {
        unsafe {
            timeEndPeriod(1);
        }
    }
}

fn send_wheel_input(delta: i32, is_horizontal: bool) {
    unsafe {
        let flags = if is_horizontal {
            MOUSEEVENTF_HWHEEL
        } else {
            MOUSEEVENTF_WHEEL
        };

        let mut input = INPUT {
            type_: INPUT_MOUSE,
            u: std::mem::zeroed(),
        };

        *input.u.mi_mut() = MOUSEINPUT {
            dx: 0,
            dy: 0,
            mouseData: delta as DWORD,
            dwFlags: flags,
            time: 0,
            dwExtraInfo: SMOOTH_EXTRA_INFO,
        };

        SendInput(1, &mut input, std::mem::size_of::<INPUT>() as i32);
    }
}

fn hook_message_loop() {
    unsafe {
        let hook = SetWindowsHookExW(
            WH_MOUSE_LL,
            Some(low_level_mouse_proc),
            std::ptr::null_mut() as HINSTANCE,
            0,
        );

        if hook.is_null() {
            eprintln!("[SmoothScroll] Failed to install WH_MOUSE_LL hook");
            return;
        }

        if let Ok(mut handle) = HOOK_HANDLE.lock() {
            *handle = Some(hook as usize);
        }

        let mut msg = std::mem::zeroed();
        while IS_RUNNING.load(Ordering::Relaxed) && GetMessageW(&mut msg, std::ptr::null_mut(), 0, 0) > 0 {
            winapi::um::winuser::TranslateMessage(&msg);
            winapi::um::winuser::DispatchMessageW(&msg);
        }

        UnhookWindowsHookEx(hook);
    }
}

unsafe extern "system" fn low_level_mouse_proc(
    n_code: i32,
    w_param: WPARAM,
    l_param: LPARAM,
) -> LRESULT {
    if n_code >= 0 {
        let hook_struct = *(l_param as *const MSLLHOOKSTRUCT);

        // Passthrough if the input event was generated by our own SendInput
        if hook_struct.dwExtraInfo == SMOOTH_EXTRA_INFO {
            return CallNextHookEx(std::ptr::null_mut(), n_code, w_param, l_param);
        }

        let is_wheel = w_param == WM_MOUSEWHEEL as usize;
        let is_hwheel = w_param == WM_MOUSEHWHEEL as usize;

        if is_wheel || is_hwheel {
            let settings = if let Ok(s) = SETTINGS.lock() {
                s.clone()
            } else {
                AppSettings::default()
            };

            if !settings.enabled {
                return CallNextHookEx(std::ptr::null_mut(), n_code, w_param, l_param);
            }

            // Check modifier keys: Ctrl for native zoom passthrough
            if settings.ctrl_passthrough_zoom {
                let ctrl_pressed = (GetAsyncKeyState(VK_CONTROL) as u16 & 0x8000) != 0;
                if ctrl_pressed {
                    return CallNextHookEx(std::ptr::null_mut(), n_code, w_param, l_param);
                }
            }

            // Check foreground application blacklist
            if !settings.blacklisted_apps.is_empty() {
                if let Some(process_name) = get_foreground_process_name() {
                    for blacklisted in &settings.blacklisted_apps {
                        if process_name.eq_ignore_ascii_case(blacklisted) {
                            return CallNextHookEx(std::ptr::null_mut(), n_code, w_param, l_param);
                        }
                    }
                }
            }

            // Extract signed high-word wheel delta
            let raw_delta = ((hook_struct.mouseData >> 16) & 0xFFFF) as i16;
            
            // Precision trackpad packets typically have |delta| < 120 or high frequency
            let is_trackpad = (raw_delta.abs() % 120 != 0) || (raw_delta.abs() < 120);

            let consumed = if let Ok(mut engine) = ENGINE.lock() {
                engine.on_input(raw_delta, is_hwheel, is_trackpad, &settings)
            } else {
                false
            };

            if consumed {
                // Return 1 to prevent the raw jerky tick from reaching the window
                return 1;
            }
        }
    }

    CallNextHookEx(std::ptr::null_mut(), n_code, w_param, l_param)
}
