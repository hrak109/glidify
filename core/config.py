"""
SmoothScroll Configuration Manager
Saves and loads settings to %APPDATA%/SmoothScroll/settings.json
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class AppSettings:
    enabled: bool = True
    step_size: float = 130.0
    animation_duration_ms: float = 650.0
    acceleration_factor: float = 1.85
    friction: float = 0.96
    easing_curve: str = "appleGlide"
    invert_vertical: bool = False
    invert_horizontal: bool = False
    trackpad_mode: bool = True
    trackpad_deadzone: float = 1.5
    trackpad_momentum: float = 2.0
    trackpad_invert: bool = False
    alt_accelerate: bool = True
    ctrl_passthrough_zoom: bool = True
    start_with_windows: bool = False
    start_minimized: bool = False
    low_latency_timer: bool = True
    blacklisted_apps: List[str] = field(default_factory=lambda: [
        "cs2.exe",
        "valorant.exe",
        "Overwatch.exe",
        "ApexLegends.exe",
    ])

    @classmethod
    def get_config_path(cls) -> Path:
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = Path(appdata) / "Glidify"
        else:
            base_dir = Path.home() / ".config" / "Glidify"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / "settings.json"

    @classmethod
    def load(cls) -> "AppSettings":
        path = cls.get_config_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Convert camelCase keys if present from frontend
                    cleaned = {}
                    for k, v in data.items():
                        snake_k = "".join(["_" + c.lower() if c.isupper() else c for c in k]).lstrip("_")
                        cleaned[snake_k] = v
                    return cls(**{k: v for k, v in cleaned.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f"[SmoothScroll] Error loading config: {e}")
        instance = cls()
        instance.save()
        return instance

    def save(self) -> None:
        path = self.get_config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            print(f"[SmoothScroll] Error saving config: {e}")

    def to_camel_dict(self) -> dict:
        data = asdict(self)
        res = {}
        for k, v in data.items():
            parts = k.split("_")
            camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
            res[camel] = v
        return res
