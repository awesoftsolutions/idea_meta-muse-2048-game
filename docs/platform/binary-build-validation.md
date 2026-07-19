# Binary Build Validation Runbook

**Version:** 1.0.0
**Date:** 2026-07-19
**Status:** Verified - Build PASS
**Author:** Favur (hello@favur.dev)
**Phase:** 6 Sprint 2 Wave1 Task1
**Component:** PyInstallerTooling / BinaryBuildValidation

## Overview

This runbook documents PyInstaller binary build validation for Favur 2048. It covers trivial spike validation and production packaging of `src/main.py` into a single-file windowed executable.

## Prerequisites

1. **Python:** 3.11+ (verified 3.13.14 CPython)
2. **Poetry:** Installed with project dependencies
3. **Dependencies:**
   - `pygame-ce ^2.5.0` (verified 2.6.1 / 2.5.5) in `[tool.poetry.dependencies]`
   - `PyInstaller ^6.0` (verified 6.20.0) in `[tool.poetry.group.dev.dependencies]`
4. **Build System:** `poetry-core` via `[build-system]`
5. **OS:** Windows 11 build 22631 AMD64, PowerShell 7+ (pwsh), NTFS case-insensitive
6. **Source Files:**
   - `spike_packaging/minimal.py` - trivial 21-line pygame window 700x800 title "Favur 2048"
   - `src/main.py` - production entry with `_get_frozen_base_path` handling `sys._MEIPASS` and `sys.frozen`, Q-018 fix `base_y=130`, single `clock.tick(60)`
   - `src/core/` - 8 files stdlib-only, no pygame leak

## Build Commands (Pinned Values)

### 1. Trivial Spike Build

Validates PyInstaller can produce a onefile windowed binary from minimal pygame code.

```powershell
# Clean prior artifacts
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Trivial build - onefile + windowed
pyinstaller --onefile --windowed spike_packaging/minimal.py --distpath dist --workpath build --specpath spike_packaging --noconfirm --log-level INFO
```

**Verified 2026-07-19 - PASS:**
- Exit code: `0` - Build complete! The results are available in: dist
- Output: `dist/minimal.exe` exists, size 27539648 bytes (>0)
- Flags: `--onefile` (single exe), `--windowed` (no console), `--name minimal`, `--distpath dist`, `--workpath build`, `--specpath spike_packaging`, `--noconfirm`, `--log-level INFO`
- Log: PyInstaller 6.20.0, Python 3.13.14, pygame-ce 2.5.5, contrib hooks 2026.5
- Command: `python -m PyInstaller --onefile --windowed --name minimal --distpath dist --workpath build --specpath spike_packaging --noconfirm --log-level INFO spike_packaging/minimal.py`

### 2. Production Build

Packages `src/main.py` into distributable binary with hidden import for pygame.

```powershell
# Clean prior artifacts
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Production build - onefile + windowed + hidden-import pygame
poetry run pyinstaller --onefile --windowed --name favur-2048 src/main.py --hidden-import pygame --log-level WARN --distpath dist --workpath build --specpath . --noconfirm

# Fallback if poetry fails (direct module invocation)
python -m PyInstaller --onefile --windowed --name favur-2048 src/main.py --hidden-import pygame --log-level WARN --distpath dist --workpath build --specpath . --noconfirm
```

**Verified 2026-07-19 - PASS:**
- Exit code: `0`
- Output: `dist/favur-2048.exe` exists, size 27645056 bytes (>0, 27.6 MB with pygame-ce bundled)
- Flags: `--onefile`, `--windowed`, `--name favur-2048`, `--hidden-import pygame`, `--distpath dist`, `--workpath build`, `--specpath .`, `--noconfirm`, `--log-level WARN`
- Frozen handling: binary uses `sys._MEIPASS` via `_get_frozen_base_path()` at runtime, `_is_frozen_binary()` check, Q-018 base_y=130, single clock.tick(60)
- Spec: `favur-2048.spec` console=False hiddenimports=['pygame'] bootloader runw.exe Windows-64bit-intel
- Command: `python -m PyInstaller --onefile --windowed --name favur-2048 src/main.py --hidden-import pygame --distpath dist --workpath build --specpath . --noconfirm --log-level WARN`

## Verification Criteria

| # | Criterion | Check | Pass Condition | Verified 2026-07-19 |
|---|-----------|-------|----------------|---------------------|
| 1 | Trivial build log | stdout/stderr | Exit code 0 | PASS - exit 0 Build complete! |
| 2 | Trivial binary exists | `dist/minimal.exe` | File exists | PASS - exists |
| 3 | Trivial binary size | `dist/minimal.exe` | Size > 0 bytes | PASS - 27539648 bytes |
| 4 | Production build log | stdout/stderr | Exit code 0 | PASS - exit 0 |
| 5 | Production binary exists | `dist/favur-2048.exe` | File exists | PASS - exists |
| 6 | Production binary size | `dist/favur-2048.exe` | Size > 0 bytes | PASS - 27645056 bytes |
| 7 | Onefile flag | Build command | `--onefile` present | PASS - pinned |
| 8 | Windowed flag | Build command | `--windowed` present | PASS - pinned |
| 9 | Hidden import | Production command | `--hidden-import pygame` present | PASS - pinned |
| 10 | pyproject.toml PyInstaller | `pyproject.toml` | Contains `PyInstaller = "^6.0"` | PASS - verified |
| 11 | pyproject.toml pygame-ce | `pyproject.toml` | Contains `pygame-ce = "^2.5.0"` | PASS - verified |
| 12 | No pygame leak in core | `src/core/*.py` | No `import pygame` pattern | PASS - 0 matches |

## Automated Validation

Run the PowerShell validation script:

```powershell
pwsh -File scripts/validate-binary-build.ps1
```

Or via poetry:

```powershell
poetry run python scripts/verify_packaging.py
```

## Steps to Validate Manually

1. **Check pyproject.toml:**
   ```powershell
   Select-String -Path pyproject.toml -Pattern "pygame-ce|PyInstaller"
   # Expected: pygame-ce = "^2.5.0", PyInstaller = "^6.0"
   ```

2. **Check no pygame leak in core:**
   ```powershell
   Select-String -Path src/core/*.py -Pattern "import pygame|from pygame"
   # Expected: no matches
   ```

3. **Build trivial:**
   ```powershell
   pyinstaller --onefile --windowed spike_packaging/minimal.py --distpath dist --workpath build --specpath spike_packaging --noconfirm --log-level INFO
   echo $LASTEXITCODE  # Expected 0
   Get-Item dist/minimal.exe | Select-Object Length  # Expected >0
   ```

4. **Build production:**
   ```powershell
   poetry run pyinstaller --onefile --windowed --name favur-2048 src/main.py --hidden-import pygame --log-level WARN --distpath dist --workpath build --specpath . --noconfirm
   echo $LASTEXITCODE  # Expected 0
   Get-Item dist/favur-2048.exe | Select-Object Length  # Expected >0
   ```

5. **Verify packaging hardening in src/main.py:**
   ```powershell
   Select-String -Path src/main.py -Pattern "_MEIPASS|_is_frozen|base_y.*130|clock.tick\(60\)"
   # Expected: matches for frozen handling, Q-018 fix, single tick
   ```

## Rollback / Recovery

### Build Failures

1. **PyInstaller not found:**
   ```powershell
   poetry install --with dev
   poetry run pyinstaller --version  # Should show 6.20.0
   ```

2. **pygame-ce not found:**
   ```powershell
   poetry install
   poetry run python -c "import pygame; print(pygame.__version__)"  # Should show 2.6.1
   ```

3. **PermissionError on dist/ (Windows file lock):**
   - Close any running `minimal.exe` or `favur-2048.exe` processes
   - `Stop-Process -Name minimal, favur-2048 -ErrorAction SilentlyContinue`
   - Retry build with `--noconfirm` flag
   - If persists, delete `dist/` manually and retry

4. **Hidden import errors at runtime:**
   - Ensure `--hidden-import pygame` is present in production command
   - Check `src/main.py` imports pygame only in main module, not in `src/core/`
   - Verify `pygame-ce` hooks are collected: check build log for `hook-pygame`

5. **Spec file conflicts:**
   - Remove old `.spec` files before rebuild: `Remove-Item *.spec, spike_packaging/*.spec -ErrorAction SilentlyContinue`
   - PyInstaller regenerates spec on each run with `--noconfirm`

### Clean State Recovery

```powershell
# Full clean
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Remove-Item -Force *.spec, spike_packaging/*.spec, favur-2048.spec -ErrorAction SilentlyContinue
poetry install --with dev
# Re-run validation
pwsh -File scripts/validate-binary-build.ps1
```

## Known Issues

- **Windows Defender:** May flag freshly built exe as unknown publisher. Add `dist/` to exclusion or sign binary.
- **Onefile startup time:** Single-file exe extracts to temp on first run, ~1-2s delay normal.
- **Windowed mode:** No console output when `--windowed`; use `--log-level` for build logs, not runtime logs.
- **Size:** Production binary 30-50 MB expected due to pygame-ce + SDL2 bundled.

## References

- Architecture: `registry://docs/phase-6-architecture.md` PyInstallerTooling BinaryBuildValidation
- Direction: `registry://docs/phase-6-direction.md` AC-3 binary builds
- Packaging verification: `scripts/verify_packaging.py`
- Prior spike log: `spike_packaging/build.log` PyInstaller 6.20.0 exit 0
- Main entry: `src/main.py` with `_get_frozen_base_path()` frozen handling
