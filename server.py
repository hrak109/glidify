"""
SmoothScroll Local Web Server & API
Serves the Windows 11 Fluent UI and communicates with the input hook.
"""

import sys
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from core.hook import hook_manager
from core.config import AppSettings

# Resolve bundle path for PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DIST_DIR = BASE_DIR / "dist"
if not DIST_DIR.exists():
    DIST_DIR = BASE_DIR / "src"

app = FastAPI(title="SmoothScroll Windows 11 API")

@app.get("/api/settings")
def get_settings():
    return hook_manager.settings.to_camel_dict()

@app.post("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    settings = AppSettings.load()
    for k, v in data.items():
        snake_k = "".join(["_" + c.lower() if c.isupper() else c for c in k]).lstrip("_")
        if hasattr(settings, snake_k):
            setattr(settings, snake_k, v)
    hook_manager.update_settings(settings)
    return {"status": "ok"}

@app.post("/api/toggle")
def toggle_enabled():
    settings = hook_manager.settings
    settings.enabled = not settings.enabled
    hook_manager.update_settings(settings)
    return {"enabled": settings.enabled}

@app.get("/api/metrics")
def get_metrics():
    intercepted, dispatched = hook_manager.get_metrics()
    return [intercepted, dispatched]

@app.get("/api/detect_app")
def detect_app():
    proc = hook_manager.get_foreground_process()
    return {"process": proc or "explorer.exe"}

@app.post("/api/defaults")
def reset_defaults():
    defaults = AppSettings()
    hook_manager.update_settings(defaults)
    return defaults.to_camel_dict()

# Mount frontend assets
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

@app.get("/{full_path:path}")
def serve_frontend(full_path: str = ""):
    target = DIST_DIR / full_path
    if target.is_file():
        return FileResponse(target)
    return FileResponse(DIST_DIR / "index.html")
