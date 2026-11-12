@echo off
title Glidify EXE Builder
setlocal enabledelayedexpansion
color 0B

echo.
echo  ======================================================
echo   GLIDIFY WINDOWS 11 — Standalone EXE Builder
echo   By Haistellar
echo  ======================================================
echo.

pushd "%~dp0"

:: ── Step 1: Verify Python ─────────────────────────────────
echo [STEP 1] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found! Install Python 3.10+ and ensure "Add to PATH" is checked.
    popd
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo         Found: %%v

:: ── Step 2: Upgrade pip ──────────────────────────────────
echo.
echo [STEP 2] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: ── Step 3: Install app dependencies ─────────────────────
echo.
echo [STEP 3] Installing app dependencies from requirements.txt...
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install requirements. Check your internet connection.
    popd
    pause
    exit /b 1
)

:: ── Step 4: Install PyInstaller ──────────────────────────
echo.
echo [STEP 4] Installing PyInstaller...
python -m pip install pyinstaller --quiet
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    popd
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python -m PyInstaller --version') do echo         PyInstaller version: %%v

:: ── Step 5: Clean previous build ─────────────────────────
echo.
echo [STEP 5] Cleaning previous build temporary files...
if exist "build\Glidify" rmdir /s /q "build\Glidify"

:: ── Step 6: Run PyInstaller with full visible output ──────
echo.
echo [STEP 6] Building Glidify.exe — live build log:
echo ========================================================
python -m PyInstaller glidify.spec --noconfirm --clean
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] PyInstaller build encountered an error (Code: %errorLevel%).
    popd
    pause
    exit /b 1
)

:: ── Step 7: Digitally Sign Executable (Trusted Authenticode) ──
echo.
echo [STEP 7] Digitally signing Glidify.exe to prevent SmartScreen untrusted errors...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\sign_app.ps1" -TargetExe "%~dp0dist\Glidify.exe"

:: ── Step 8: Verify output executable ──────────────────────
echo ========================================================
echo.
if exist "dist\Glidify.exe" (
    echo  ======================================================
    echo   [SUCCESS] Glidify.exe CREATED & SIGNED SUCCESSFULLY!
    echo.
    echo   File details:
    dir "dist\Glidify.exe" | findstr "Glidify.exe"
    echo.
    echo   Exact Path: %~dp0dist\Glidify.exe
    echo  ======================================================
    echo.
    echo Opening output folder in File Explorer...
    explorer "%~dp0dist"
) else (
    echo  ======================================================
    echo   [ERROR] File dist\Glidify.exe was not found!
    echo  ======================================================
)

popd
echo.
echo Press any key to close this window...
pause >nul
