#[cfg(target_os = "windows")]
use winapi::um::winreg::{RegCloseKey, RegDeleteValueW, RegOpenKeyExW, RegSetValueExW, HKEY_CURRENT_USER};
#[cfg(target_os = "windows")]
use winapi::shared::minwindef::DWORD;
#[cfg(target_os = "windows")]
use winapi::um::winnt::{KEY_READ, KEY_WRITE, REG_SZ};
#[cfg(target_os = "windows")]
use std::os::windows::ffi::OsStrExt;
#[cfg(target_os = "windows")]
use std::ffi::OsStr;

pub fn set_autostart(enabled: bool) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        unsafe {
            let subkey: Vec<u16> = OsStr::new("Software\\Microsoft\\Windows\\CurrentVersion\\Run\0")
                .encode_wide()
                .collect();
            let app_name: Vec<u16> = OsStr::new("SmoothScroll\0")
                .encode_wide()
                .collect();

            let mut hkey = std::ptr::null_mut();
            let status = RegOpenKeyExW(
                HKEY_CURRENT_USER,
                subkey.as_ptr(),
                0,
                KEY_READ | KEY_WRITE,
                &mut hkey,
            );

            if status != 0 {
                return Err(format!("Failed to open Windows Run registry key. Error: {}", status));
            }

            if enabled {
                if let Ok(current_exe) = std::env::current_exe() {
                    let exe_str = format!("\"{}\" --minimized\0", current_exe.display());
                    let exe_wide: Vec<u16> = OsStr::new(&exe_str).encode_wide().collect();

                    let res = RegSetValueExW(
                        hkey,
                        app_name.as_ptr(),
                        0,
                        REG_SZ,
                        exe_wide.as_ptr() as *const u8,
                        (exe_wide.len() * 2) as DWORD,
                    );
                    RegCloseKey(hkey);
                    if res != 0 {
                        return Err(format!("Failed to set autostart registry value: {}", res));
                    }
                }
            } else {
                let _ = RegDeleteValueW(hkey, app_name.as_ptr());
                RegCloseKey(hkey);
            }
            Ok(())
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        let _ = enabled;
        Ok(())
    }
}
