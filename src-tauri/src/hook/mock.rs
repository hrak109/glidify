use crate::config::AppSettings;

pub fn update_runtime_settings(_new_settings: AppSettings) {}

pub fn get_engine_metrics() -> (u64, u64) {
    (0, 0)
}

pub fn get_foreground_process_name() -> Option<String> {
    Some("explorer.exe".to_string())
}

pub fn start_hook(_initial_settings: AppSettings) {
    println!("[SmoothScroll Mock] Hook started (non-Windows platform)");
}

pub fn stop_hook() {
    println!("[SmoothScroll Mock] Hook stopped");
}
