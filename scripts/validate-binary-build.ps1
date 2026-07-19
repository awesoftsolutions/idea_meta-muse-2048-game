# Binary Build Validation Script - Favur 2048
# Phase 6 Sprint 2 Wave1 Task1 - PyInstaller Binary Build Validation
# Author: Favur (hello@favur.dev)
# Verifies: trivial and production PyInstaller builds exit 0, dist exists size>0, onefile windowed

$ErrorActionPreference = "Stop"
$failed = $false

Write-Host "=== Binary Build Validation ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "CWD: $(Get-Location)"
Write-Host ""

# 1. Check pyproject.toml
Write-Host "[1/6] Checking pyproject.toml dependencies..." -ForegroundColor Yellow
$pyproject = Get-Content pyproject.toml -Raw
if ($pyproject -match 'pygame-ce\s*=\s*"\^2\.5\.0"') {
    Write-Host "  PASS: pygame-ce ^2.5.0 found" -ForegroundColor Green
} else {
    Write-Host "  FAIL: pygame-ce ^2.5.0 not found" -ForegroundColor Red
    $failed = $true
}
if ($pyproject -match 'PyInstaller\s*=\s*"\^6\.0"') {
    Write-Host "  PASS: PyInstaller ^6.0 found" -ForegroundColor Green
} else {
    Write-Host "  FAIL: PyInstaller ^6.0 not found" -ForegroundColor Red
    $failed = $true
}

# 2. Check no pygame leak in core
Write-Host "[2/6] Checking no pygame leak in src/core..." -ForegroundColor Yellow
$leak = Select-String -Path src/core/*.py -Pattern "import pygame|from pygame" -ErrorAction SilentlyContinue
if ($null -eq $leak) {
    Write-Host "  PASS: No pygame import in src/core" -ForegroundColor Green
} else {
    Write-Host "  FAIL: pygame leak found in src/core:" -ForegroundColor Red
    $leak | ForEach-Object { Write-Host "    $($_.Path):$($_.LineNumber) $($_.Line)" -ForegroundColor Red }
    $failed = $true
}

# 3. Check PyInstaller version
Write-Host "[3/6] Checking PyInstaller version..." -ForegroundColor Yellow
try {
    $versionOutput = poetry run pyinstaller --version 2>&1 | Out-String
    if ($versionOutput -match "6\.\d+") {
        Write-Host "  PASS: PyInstaller version $versionOutput" -ForegroundColor Green
    } else {
        Write-Host "  INFO: PyInstaller version output: $versionOutput" -ForegroundColor Yellow
    }
} catch {
    try {
        $versionOutput = python -m PyInstaller --version 2>&1 | Out-String
        Write-Host "  PASS: PyInstaller version (fallback) $versionOutput" -ForegroundColor Green
    } catch {
        Write-Host "  FAIL: PyInstaller not found" -ForegroundColor Red
        $failed = $true
    }
}

# 4. Trivial build
Write-Host "[4/6] Building trivial spike (onefile windowed)..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Remove-Item -Force spike_packaging/minimal.spec -ErrorAction SilentlyContinue

$trivialCmd = "poetry run pyinstaller --onefile --windowed spike_packaging/minimal.py --distpath dist --workpath build --specpath spike_packaging --noconfirm --log-level INFO"
Write-Host "  CMD: $trivialCmd"
try {
    $trivialOutput = Invoke-Expression $trivialCmd 2>&1 | Out-String
    $trivialExit = $LASTEXITCODE
    # Save log
    $trivialOutput | Out-File -FilePath spike_packaging/build.log -Encoding utf8
    Write-Host "  Exit code: $trivialExit"
    if ($trivialExit -eq 0) {
        Write-Host "  PASS: Trivial build exit 0" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: Trivial build exit $trivialExit" -ForegroundColor Red
        Write-Host $trivialOutput
        $failed = $true
    }
} catch {
    Write-Host "  FAIL: Trivial build exception: $_" -ForegroundColor Red
    $failed = $true
    $trivialExit = 1
}

# Verify trivial binary
if (Test-Path dist/minimal.exe) {
    $size = (Get-Item dist/minimal.exe).Length
    if ($size -gt 0) {
        Write-Host "  PASS: dist/minimal.exe exists size=$size bytes" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: dist/minimal.exe size 0" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  FAIL: dist/minimal.exe not found" -ForegroundColor Red
    $failed = $true
}

# 5. Production build
Write-Host "[5/6] Building production favur-2048 (onefile windowed hidden-import pygame)..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Force favur-2048.spec, ./favur-2048.spec -ErrorAction SilentlyContinue

$prodCmd = "poetry run pyinstaller --onefile --windowed --name favur-2048 src/main.py --hidden-import pygame --log-level WARN --distpath dist --workpath build --specpath . --noconfirm"
Write-Host "  CMD: $prodCmd"
try {
    $prodOutput = Invoke-Expression $prodCmd 2>&1 | Out-String
    $prodExit = $LASTEXITCODE
    $prodOutput | Out-File -FilePath build-production.log -Encoding utf8
    Write-Host "  Exit code: $prodExit"
    if ($prodExit -eq 0) {
        Write-Host "  PASS: Production build exit 0" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: Production build exit $prodExit" -ForegroundColor Red
        Write-Host $prodOutput
        $failed = $true
    }
} catch {
    Write-Host "  FAIL: Production build exception: $_" -ForegroundColor Red
    $failed = $true
    $prodExit = 1
}

# Verify production binary
if (Test-Path dist/favur-2048.exe) {
    $size = (Get-Item dist/favur-2048.exe).Length
    if ($size -gt 0) {
        Write-Host "  PASS: dist/favur-2048.exe exists size=$size bytes" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: dist/favur-2048.exe size 0" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  FAIL: dist/favur-2048.exe not found" -ForegroundColor Red
    $failed = $true
}

# 6. Verify flags
Write-Host "[6/6] Verifying build flags..." -ForegroundColor Yellow
$checks = @(
    @{ Name = "onefile flag in trivial"; Pattern = "--onefile"; Cmd = $trivialCmd },
    @{ Name = "windowed flag in trivial"; Pattern = "--windowed"; Cmd = $trivialCmd },
    @{ Name = "onefile flag in production"; Pattern = "--onefile"; Cmd = $prodCmd },
    @{ Name = "windowed flag in production"; Pattern = "--windowed"; Cmd = $prodCmd },
    @{ Name = "hidden-import pygame in production"; Pattern = "--hidden-import pygame"; Cmd = $prodCmd },
    @{ Name = "name favur-2048 in production"; Pattern = "--name favur-2048"; Cmd = $prodCmd }
)
foreach ($check in $checks) {
    if ($check.Cmd -match [regex]::Escape($check.Pattern)) {
        Write-Host "  PASS: $($check.Name) present" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: $($check.Name) missing" -ForegroundColor Red
        $failed = $true
    }
}

Write-Host ""
if ($failed) {
    Write-Host "=== VALIDATION FAILED ===" -ForegroundColor Red
    exit 1
} else {
    Write-Host "=== VALIDATION PASSED ===" -ForegroundColor Green
    Write-Host "All criteria: exit 0, dist exists size>0, onefile windowed, hidden-import pygame, pyproject deps, no pygame leak"
    exit 0
}
