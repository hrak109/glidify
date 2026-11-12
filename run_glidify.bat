@echo off
title Glidify Windows 11
setlocal enabledelayedexpansion
color 0B

echo.
echo  ======================================================
echo   GLIDIFY WINDOWS 11 — Direct Launcher
echo   By Haistellar
echo  ======================================================
echo.

pushd "%~dp0"

:: Verify Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    popd
    pause
    exit /b 1
)

:: Sync dependencies
echo [SYSTEM] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet

echo [CORE] Launching Glidify background input hook & UI...
python launcher.py
popd
pause
