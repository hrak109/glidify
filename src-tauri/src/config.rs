use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AppSettings {
    pub enabled: bool,
    
    // Physics & Wheel settings
    pub step_size: f64,              // Pixels / delta per wheel tick (default: 120.0)
    pub animation_duration_ms: f64,  // Duration of momentum animation (default: 380.0)
    pub acceleration_factor: f64,    // Acceleration multiplier on fast flick (default: 1.75)
    pub friction: f64,               // Viscous decay coefficient 0.80 - 0.98 (default: 0.92)
    pub easing_curve: String,        // "easeOutCubic", "exponential", "spring", "linear"
    pub invert_vertical: bool,       // Reverse vertical scroll direction
    pub invert_horizontal: bool,     // Reverse horizontal scroll direction
    
    // Trackpad / Touchpad specific tuning
    pub trackpad_mode: bool,         // Specialized filtering for precision touchpads
    pub trackpad_deadzone: f64,      // Deadzone threshold to filter finger resting jitter (default: 2.0)
    pub trackpad_momentum: f64,      // Glide multiplier when lifting fingers (default: 1.4)
    pub trackpad_invert: bool,       // Invert trackpad independent of mouse wheel
    
    // Key modifiers & behavior
    pub alt_accelerate: bool,        // Holding Alt doubles scroll speed
    pub ctrl_passthrough_zoom: bool, // Holding Ctrl bypasses smoothing for native browser zoom
    
    // System & Startup
    pub start_with_windows: bool,    // Run on Windows startup
    pub start_minimized: bool,       // Start minimized in system tray
    pub low_latency_timer: bool,     // Request 1ms multimedia timer resolution
    
    // Blacklisted application executable names (e.g., ["cs2.exe", "valorant.exe"])
    pub blacklisted_apps: Vec<String>,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            enabled: true,
            step_size: 120.0,
            animation_duration_ms: 380.0,
            acceleration_factor: 1.75,
            friction: 0.92,
            easing_curve: "easeOutCubic".to_string(),
            invert_vertical: false,
            invert_horizontal: false,
            trackpad_mode: true,
            trackpad_deadzone: 2.5,
            trackpad_momentum: 1.45,
            trackpad_invert: false,
            alt_accelerate: true,
            ctrl_passthrough_zoom: true,
            start_with_windows: false,
            start_minimized: false,
            low_latency_timer: true,
            blacklisted_apps: vec![
                "cs2.exe".to_string(),
                "valorant.exe".to_string(),
                "Overwatch.exe".to_string(),
                "ApexLegends.exe".to_string(),
            ],
        }
    }
}

impl AppSettings {
    pub fn config_path() -> PathBuf {
        #[cfg(target_os = "windows")]
        {
            if let Ok(app_data) = std::env::var("APPDATA") {
                let mut dir = PathBuf::from(app_data);
                dir.push("SmoothScroll");
                let _ = fs::create_dir_all(&dir);
                return dir.join("settings.json");
            }
        }

        // Fallback for non-windows / portable
        let mut dir = dirs_fallback();
        dir.push("SmoothScroll");
        let _ = fs::create_dir_all(&dir);
        dir.join("settings.json")
    }

    pub fn load() -> Self {
        let path = Self::config_path();
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(settings) = serde_json::from_str::<AppSettings>(&content) {
                    return settings;
                }
            }
        }
        let default_settings = Self::default();
        let _ = default_settings.save();
        default_settings
    }

    pub fn save(&self) -> Result<(), String> {
        let path = Self::config_path();
        let json = serde_json::to_string_pretty(self)
            .map_err(|e| format!("Failed to serialize settings: {}", e))?;
        
        if let Some(parent) = path.parent() {
            let _ = fs::create_dir_all(parent);
        }
        
        fs::write(&path, json)
            .map_err(|e| format!("Failed to write settings file: {}", e))?;
        Ok(())
    }
}

fn dirs_fallback() -> PathBuf {
    if let Ok(home) = std::env::var("HOME").or_else(|_| std::env::var("USERPROFILE")) {
        let mut p = PathBuf::from(home);
        p.push(".config");
        return p;
    }
    PathBuf::from(".")
}
