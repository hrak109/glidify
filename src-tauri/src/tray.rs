use tauri::menu::{Menu, MenuItem};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager};

pub fn setup_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let toggle_i = MenuItem::with_id(app, "toggle_active", "Enabled: ON", true, None::<&str>)?;
    let settings_i = MenuItem::with_id(app, "open_settings", "Settings & Tuning", true, None::<&str>)?;
    let quit_i = MenuItem::with_id(app, "quit", "Quit SmoothScroll", true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&toggle_i, &settings_i, &quit_i])?;

    let _tray = TrayIconBuilder::new()
        .menu(&menu)
        .tooltip("SmoothScroll - Windows 11")
        .icon(app.default_window_icon().unwrap().clone())
        .on_menu_event(|app, event| match event.id.as_ref() {
            "toggle_active" => {
                let mut settings = crate::config::AppSettings::load();
                settings.enabled = !settings.enabled;
                let _ = settings.save();
                crate::hook::update_runtime_settings(settings);
            }
            "open_settings" => {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            "quit" => {
                crate::hook::stop_hook();
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(window) = app.get_webview_window("main") {
                    if window.is_visible().unwrap_or(false) {
                        let _ = window.hide();
                    } else {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
            }
        })
        .build(app)?;

    Ok(())
}
