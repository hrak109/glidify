# =========================================================================
# Glidify — Windows 11 Authenticode Code Signing Script
# Creates/uses a trusted local developer certificate and signs Glidify.exe
# =========================================================================

param (
    [string]$TargetExe = "$PSScriptRoot\..\dist\Glidify.exe"
)

Write-Host ">>> [Signing] Checking Authenticode Code Signing Certificate..." -ForegroundColor Cyan

$certSubject = "CN=Glidify (Haistellar)"
$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -eq $certSubject } | Select-Object -First 1

if (-not $cert) {
    Write-Host ">>> Creating new Authenticode Code Signing Certificate for Glidify..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $certSubject `
        -KeySpec Signature `
        -KeyLength 2048 `
        -KeyExportPolicy Exportable `
        -NotAfter (Get-Date).AddYears(10) `
        -CertStoreLocation "Cert:\CurrentUser\My"

    # Export public certificate
    $cerPath = "$PSScriptRoot\..\dist\Glidify.cer"
    $distDir = Split-Path $cerPath
    if (-not (Test-Path $distDir)) { New-Item -ItemType Directory -Path $distDir -Force | Out-Null }
    
    Export-Certificate -Cert $cert -FilePath $cerPath -Force | Out-Null

    # Trust certificate in CurrentUser Root store (prevents SmartScreen Untrusted error)
    Write-Host ">>> Installing certificate into CurrentUser Trusted Root store..." -ForegroundColor Yellow
    Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
}

if (-not (Test-Path $TargetExe)) {
    Write-Warning "Target executable not found at: $TargetExe"
    exit 0
}

Write-Host ">>> Signing $TargetExe with Authenticode Certificate ($certSubject)..." -ForegroundColor Cyan

try {
    # Try signing with RFC3161 Digicert timestamp server
    $sig = Set-AuthenticodeSignature -FilePath $TargetExe -Certificate $cert -TimestampServer "http://timestamp.digicert.com" -ErrorAction Stop
} catch {
    # Offline fallback without timestamp
    $sig = Set-AuthenticodeSignature -FilePath $TargetExe -Certificate $cert
}

$status = Get-AuthenticodeSignature -FilePath $TargetExe
if ($status.Status -eq "Valid") {
    Write-Host ">>> [SUCCESS] Glidify.exe is DIGITALLY SIGNED and TRUSTED!" -ForegroundColor Green
    Write-Host "    Status: $($status.Status)" -ForegroundColor Green
    Write-Host "    Signer: $($status.SignerCertificate.Subject)" -ForegroundColor Green
} else {
    Write-Host ">>> Signature applied. Status: $($status.Status)" -ForegroundColor Yellow
}

# Remove Mark-of-the-Web (Zone.Identifier) stream to prevent SmartScreen prompt
try {
    Unblock-File -Path $TargetExe -ErrorAction SilentlyContinue
    Write-Host ">>> [SUCCESS] Removed Windows Mark-of-the-Web (Unblocked)." -ForegroundColor Green
} catch {}
