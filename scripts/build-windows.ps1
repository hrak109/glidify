# =========================================================================
# SmoothScroll — Windows 11 Build & Packaging Script
# =========================================================================

Write-Host ">>> [1/4] Checking Windows prerequisites..." -ForegroundColor Cyan

$missingTools = @()

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    $missingTools += "Node.js (LTS)"
}

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    $missingTools += "Rust & Cargo"
}

if ($missingTools.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing required tools on Windows host: $($missingTools -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To install them automatically using Windows Package Manager (winget), run:" -ForegroundColor White
    
    if ($missingTools -contains "Node.js (LTS)") {
        Write-Host "  winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements" -ForegroundColor Green
    }
    if ($missingTools -contains "Rust & Cargo") {
        Write-Host "  winget install Rustlang.Rustup --accept-package-agreements --accept-source-agreements" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "After running the winget command(s), restart PowerShell and rerun this script." -ForegroundColor Cyan
    exit 1
}

Write-Host ">>> [2/4] Installing web dependencies..." -ForegroundColor Cyan
npm install

Write-Host ">>> [3/4] Building web frontend..." -ForegroundColor Cyan
npm run build

Write-Host ">>> [4/4] Compiling Rust backend & generating Windows installers (NSIS/MSI)..." -ForegroundColor Cyan
npm run tauri:build

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Build Complete!" -ForegroundColor Green
Write-Host " Installers generated in: src-tauri\target\release\bundle\" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
