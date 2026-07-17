"""
Framework spike window tests for Task 2 - TDD red phase.

Tests file inspection per pseudocode TDD Test Structure.
Covers AC-1 through AC-6: API verification, window title/size,
non-resizable flag, primitive drawing, clean quit, Clock 60 FPS,
no external assets, no core import, pygame-ce version pinned.

All tests non-interactive, headless, use pathlib file inspection.
Expected to FAIL initially because src/main.py does not exist yet
(TDD red phase) - implementation in next step will make them pass.
"""

from __future__ import annotations

import pathlib


def _read_main() -> str:
    """Read src/main.py content or raise if missing."""
    path = pathlib.Path("src/main.py")
    assert path.exists(), "src/main.py does not exist - framework spike not created yet"
    return path.read_text(encoding="utf-8")


def _read_pyproject() -> str:
    """Read pyproject.toml content or raise if missing."""
    path = pathlib.Path("pyproject.toml")
    assert path.exists(), "pyproject.toml does not exist"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test: import without side effect - AC1, AC2
# ---------------------------------------------------------------------------


def test_import_without_side_effect() -> None:
    """Verify src/main.py has __main__ guard for clean import without window."""
    content = _read_main()
    assert '__name__' in content, "Missing __name__ guard - import would have side effects"
    assert '__main__' in content, "Missing __main__ guard - required for import check"
    # Ensure main() is defined
    assert "def main" in content, "main() function not defined in src/main.py"


# ---------------------------------------------------------------------------
# Test: API verification exists - AC1
# ---------------------------------------------------------------------------


def test_api_verification_exists() -> None:
    """Verify all 11 required pygame-ce APIs present in source per AC1."""
    content = _read_main()
    required_apis = [
        "pygame.init",
        "set_mode",
        "set_caption",
        "event.get",
        "QUIT",
        "KEYDOWN",
        "K_ESCAPE",
        "draw.rect",
        "Clock",
        "pygame.quit",
        "sys.exit",
    ]
    missing = [api for api in required_apis if api not in content]
    assert not missing, f"Missing required APIs in src/main.py: {missing}"
    # At least one primitive must be present, rect or circle
    assert ("draw.rect" in content) or ("draw.circle" in content), (
        "No primitive drawing API found - need draw.rect or draw.circle"
    )


# ---------------------------------------------------------------------------
# Test: window title exact - AC2
# ---------------------------------------------------------------------------


def test_window_title_exact() -> None:
    """Verify window title exactly Favur 2048 case-sensitive per SOW."""
    content = _read_main()
    assert "Favur 2048" in content, (
        "Exact title 'Favur 2048' not found - case-sensitive per SOW, "
        "check for typo like Favur-2048 or favur 2048"
    )


# ---------------------------------------------------------------------------
# Test: window size 700x800 - AC2
# ---------------------------------------------------------------------------


def test_window_size_700x800() -> None:
    """Verify window size 700x800 per SOW fixed requirements."""
    content = _read_main()
    # Check for tuple (700, 800) in various spacing forms
    has_size = ("700" in content) and ("800" in content)
    assert has_size, "Window size 700 and 800 not both found in src/main.py"
    # More precise check for set_mode with 700,800
    assert "700" in content and "800" in content, "Missing 700x800 size literal"
    # Ensure set_mode is present
    assert "set_mode" in content, "set_mode not found - required for window creation"
    # Check that (700, 800) tuple appears, not reversed (800, 700) as primary
    # Allow both but prefer (700, 800)
    assert "(700, 800)" in content or "(700,800)" in content or "700, 800" in content, (
        "Expected (700, 800) tuple not found - SOW requires width 700 height 800"
    )


# ---------------------------------------------------------------------------
# Test: non-resizable flag - AC4
# ---------------------------------------------------------------------------


def test_non_resizable_flag() -> None:
    """Verify non-resizable flag explicit, no RESIZABLE per AC4."""
    content = _read_main()
    assert "RESIZABLE" not in content, (
        "RESIZABLE flag found - violates SOW non-resizable requirement, "
        "use flags=0 or no flags argument"
    )
    assert "set_mode" in content, "set_mode not found - cannot verify non-resizable"


# ---------------------------------------------------------------------------
# Test: primitive drawing present - AC2, AC5
# ---------------------------------------------------------------------------


def test_primitive_drawing_present() -> None:
    """Verify primitive rect/circle drawn programmatically per AC2 AC5."""
    content = _read_main()
    has_rect = "draw.rect" in content
    has_circle = "draw.circle" in content
    assert has_rect or has_circle, (
        "No primitive drawing found - need draw.rect or draw.circle per AC2 AC5"
    )


# ---------------------------------------------------------------------------
# Test: clean quit present - AC3
# ---------------------------------------------------------------------------


def test_clean_quit_present() -> None:
    """Verify clean quit with pygame.quit() and sys.exit(0) per AC3."""
    content = _read_main()
    assert "pygame.quit" in content, "pygame.quit() not found - required for clean quit AC3"
    assert "sys.exit" in content, "sys.exit not found - required for clean quit AC3"
    # Check for exit code 0
    assert "sys.exit(0)" in content or "sys.exit( 0" in content, (
        "sys.exit(0) not found - must exit with code 0 per AC3"
    )


# ---------------------------------------------------------------------------
# Test: Clock 60 FPS present - AC6
# ---------------------------------------------------------------------------


def test_clock_60fps_present() -> None:
    """Verify 60 FPS Clock tick present per AC6."""
    content = _read_main()
    assert "Clock" in content, "Clock not found - required for 60 FPS per AC6"
    assert "tick" in content, "tick not found - required for FPS capping per AC6"
    # Check for 60 FPS literal
    assert "tick(60)" in content or "tick( 60" in content or "60" in content, (
        "tick(60) not found - must cap at 60 FPS per AC6"
    )
    # More precise
    assert "60" in content, "60 FPS literal not found"


# ---------------------------------------------------------------------------
# Test: no external assets - AC5
# ---------------------------------------------------------------------------


def test_no_external_assets() -> None:
    """Verify no external assets loaded, programmatic only per AC5."""
    content = _read_main()
    assert "image.load" not in content, (
        "image.load found - violates SOW programmatic graphics only per AC5"
    )
    # Also check for common asset loading patterns that would violate
    # Allow font loading via SysFont but not file loads
    assert "pygame.image.load" not in content, "pygame.image.load violates AC5"


# ---------------------------------------------------------------------------
# Test: no core import - AC1 isolation
# ---------------------------------------------------------------------------


def test_no_core_import() -> None:
    """Verify spike isolation, no src/core dependency per architecture."""
    content = _read_main()
    assert "from src.core" not in content, "from src.core import violates spike isolation"
    assert "import src.core" not in content, "import src.core violates spike isolation"
    assert "src.core" not in content, "src.core import found - spike must be independent"
    assert "src/core" not in content, "src/core path reference suggests core dependency"


# ---------------------------------------------------------------------------
# Test: pygame version pinned - AC1
# ---------------------------------------------------------------------------


def test_pygame_version_pinned() -> None:
    """Verify pygame-ce ^2.5.0 declared in pyproject.toml per AC1."""
    content = _read_pyproject()
    assert "pygame-ce" in content, "pygame-ce not declared in pyproject.toml per ADR-001"
    assert "^2.5.0" in content, "pygame-ce ^2.5.0 not declared per architecture config"
