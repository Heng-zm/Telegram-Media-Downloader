#!/usr/bin/env pwsh
# Build script: creates PyInstaller one-folder app and compiles Inno Setup installer
# Requirements:
# - Python + PyInstaller (pip install pyinstaller)
# - Inno Setup 6 installed (ISCC.exe on PATH or at default location)

$ErrorActionPreference = 'Stop'

# Paths
$Root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Split-Path -Parent $Root
Set-Location $Project

$DistDir = Join-Path $Project 'dist/ImageToPDF'
$BuildDir = Join-Path $Project 'build'
$Icon = Join-Path $Project 'icon.ico'

# Ensure an icon exists; if not, create a simple placeholder
if (-not (Test-Path $Icon)) {
  Write-Host '==> No icon.ico found, creating a placeholder icon...'
  $py = @"
from PIL import Image
sizes=[16,24,32,48,64,128,256]
im=Image.new('RGBA',(256,256),(45,127,247,255))
for x in range(256):
    im.putpixel((x,0),(255,255,255,255))
    im.putpixel((x,255),(255,255,255,255))
for y in range(256):
    im.putpixel((0,y),(255,255,255,255))
    im.putpixel((255,y),(255,255,255,255))
im.save('icon.ico', format='ICO', sizes=[(s,s) for s in sizes])
print('placeholder icon.ico created')
"@
  $tmpPy = Join-Path $Project 'scripts\_gen_icon.py'
  $null = New-Item -ItemType File -Path $tmpPy -Force
  Set-Content -Path $tmpPy -Value $py -Encoding UTF8
  python "$tmpPy"
  Remove-Item "$tmpPy" -ErrorAction SilentlyContinue
}

# 1) PyInstaller build (one-folder recommended for PyQt6)
Write-Host '==> Building app with PyInstaller...'
& python -m PyInstaller --noconsole --name TelegramDownloader --icon "$Icon" app_pyqt6.py

# 2) Locate ISCC.exe
Write-Host '==> Locating Inno Setup compiler (ISCC.exe)...'
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
  $defaultIscc = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
  if (Test-Path $defaultIscc) { $iscc = $defaultIscc } else { throw 'ISCC.exe not found. Add Inno Setup 6 to PATH or install it.' }
} else {
  $iscc = $iscc.Path
}

# 3) Compile installer
$Iss = Join-Path $Project 'installer/ImageToPDF.iss'
Write-Host "==> Compiling installer: $Iss"
& "$iscc" "$Iss"

Write-Host "==> Done. Output in: $(Join-Path $Project 'installer/output')"
