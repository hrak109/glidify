// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod autostart;
mod config;
mod hook;
mod physics;
mod tray;

use config::AppSettings;
use tauri::Manager;

#[tauri::command]
fn get_settings() -> AppSettings {
    AppSettings::load()
}

#[tauri::command]
fn update_settings(settings: AppSettings) -> Result<(), String> {
    // If autostart setting changed, update Windows registry
    let prev = AppSettings::load();
    if prev.start_with_windows != settings.start_with_windows {
        let _ = autostart::set_autostart(settings.start_with_windows);
    }

    settings.save()?;
    hook::update_runtime_settings(settings);
    Ok(())
}

#[tauri::command]
fn toggle_enabled() -> Result<bool, String> {
    let mut settings = AppSettings::load();
    settings.enabled = !settings.enabled;
    settings.save()?;
    let new_state = settings.enabled;
    hook::update_runtime_settings(settings);
    Ok(new_state)
}

#[tauri::command]
fn get_metrics() -> (u64, u64) {
    hook::get_engine_metrics()
}

#[tauri::command]
fn get_foreground_app() -> Option<String> {
    hook::get_foreground_process_name()
}

#[tauri::command]
fn reset_defaults() -> Result<AppSettings, String> {
    let defaults = AppSettings::default();
    defaults.save()?;
    hook::update_runtime_settings(defaults.clone());
    Ok(defaults)
}

fn main() {
    let settings = AppSettings::load();
    let start_minimized = settings.start_minimized || std::env::args().any(|arg| arg == "--minimized");

    // Start low-level hook with current settings
    hook::start_hook(settings);

    tauri::Builder::default()
        .setup(move |app| {
            // Setup system tray
            if let Err(e) = tray::setup_tray(app.handle()) {
                eprintln!("[SmoothScroll] Tray setup warning: {}", e);
            }

            // Window close interception: hide to tray instead of exiting
            if let Some(window) = app.get_webview_window("main") {
                if start_minimized {
                    let _ = window.hide();
                }

                let win_clone = window.clone();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = win_clone.hide();
                    }
                });
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_settings,
            update_settings,
            toggle_enabled,
            get_metrics,
            get_foreground_app,
            reset_defaults
        ])
        .run(tauri::generate_context!())
        .expect("error while running SmoothScroll application");
}
