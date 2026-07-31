# Build a portable MarkItDown.exe (no installer).
# Run from repo root:
#   .\.venv\Scripts\Activate.ps1
#   powershell -ExecutionPolicy Bypass -File webapp\build_exe.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $PSScriptRoot

Write-Host "Installing PyInstaller..."
python -m pip install -q pyinstaller

Write-Host "Building portable MarkItDown.exe (this can take several minutes)..."
python -m PyInstaller --noconfirm --clean MarkItDown.spec

$Exe = Join-Path $PSScriptRoot "dist\MarkItDown.exe"
if (-not (Test-Path $Exe)) {
    throw "Build failed: $Exe not found"
}

$PortableDir = Join-Path $Root "portable"
New-Item -ItemType Directory -Force -Path $PortableDir | Out-Null
Copy-Item -Force $Exe (Join-Path $PortableDir "MarkItDown.exe")

$sizeMb = [math]::Round((Get-Item $Exe).Length / 1MB, 1)
Write-Host ""
Write-Host "Done."
Write-Host "Portable exe: $PortableDir\MarkItDown.exe ($sizeMb MB)"
Write-Host "Double-click it to open the app in your browser. Close the console window to quit."
