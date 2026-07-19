"""
tests/test_readme_finalization.py — README finalization gating tests.

TDD Red Phase for Phase 6 Sprint 2 Task 3.

Purpose:
    Verify README.md contains all required sections per SOW AC-6 and
    Phase 6 Direction AC-6: title, overview, Thermal Entropy Core identity
    with explicit heat colors and reactor chrome palette, installation via
    Poetry, running instructions, full controls (arrow keys, U/Z undo,
    Escape quit, R restart), how to run tests (poetry run pytest),
    how to build standalone binary (pyinstaller --onefile --windowed
    --name favur-2048 src/main.py), platform notes Windows/macOS/Linux,
    visual-proof manifest reference, and CI badge placeholder.

    These tests are file content checks (string containment) per the
    acceptance criteria verification method. They are expected to FAIL
    initially before README.md is finalized (red phase), except for the
    title which already exists in the partial README.

Design:
    - Headless, stdlib only (pathlib), no pygame import.
    - Helper _read_readme() resolves README.md robustly from tests/ dir.
    - 8 pytest tests, one per required section grouping.
    - Non-interactive: `poetry run pytest tests/test_readme_finalization.py -v`

AC Coverage:
    - AC-1: title/overview/twist identity + heat colors + reactor chrome
    - AC-2: controls arrow keys undo Escape R restart
    - AC-3: how to run tests poetry run pytest
    - AC-4: build binary pyinstaller command + platform notes
    - AC-5: visual-proof reference + CI badge placeholder
"""

from __future__ import annotations

import pathlib


def _read_readme() -> str:
    """Read README.md content robustly.

    Resolves README.md by searching upward from this file's directory
    and falling back to CWD. Returns file content as string.

    Raises:
        FileNotFoundError: If README.md cannot be located.
    """
    # Primary: project root is parent of tests/
    candidate = pathlib.Path(__file__).resolve().parent.parent / "README.md"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")

    # Fallback: search upward up to 4 levels
    current = pathlib.Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / "README.md"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        if current.parent == current:
            break
        current = current.parent

    # Final fallback: CWD
    cwd_candidate = pathlib.Path.cwd() / "README.md"
    if cwd_candidate.exists():
        return cwd_candidate.read_text(encoding="utf-8")

    raise FileNotFoundError("README.md not found from tests/test_readme_finalization.py")


def test_readme_contains_title_overview_twist_identity() -> None:
    """AC-1: README contains title Favur 2048, overview, twist identity, install."""
    content = _read_readme()
    assert "# Favur 2048" in content, "Missing title '# Favur 2048'"
    assert "Thermal Entropy Core" in content, "Missing twist 'Thermal Entropy Core'"
    assert "poetry install" in content, "Missing 'poetry install'"
    # Overview check: 5x5 or Overview heading
    assert ("5x5" in content or "Overview" in content), "Missing overview (5x5 or Overview)"


def test_readme_contains_heat_colors_and_reactor_chrome() -> None:
    """AC-1 extended: README contains heat colors and reactor chrome hex codes."""
    content = _read_readme()
    # Heat colors per twist identity
    assert "#3B82F6" in content, "Missing heat color #3B82F6 (cool blue 0)"
    assert "#F59E0B" in content, "Missing heat color #F59E0B (warm 1)"
    assert "#EF4444" in content, "Missing heat color #EF4444 (hot 2)"
    assert "#FFFFFF" in content, "Missing heat color #FFFFFF (unstable 3 glow)"
    # Reactor chrome palette
    assert "#0F172A" in content, "Missing reactor chrome #0F172A (dark reactor)"
    assert "#1E293B" in content, "Missing reactor chrome #1E293B (slate board)"
    assert "#334155" in content, "Missing reactor chrome #334155 (empty cell)"
    assert "#475569" in content, "Missing reactor chrome #475569 (border chrome)"


def test_readme_contains_controls_arrow_keys_undo_escape_restart() -> None:
    """AC-2: README contains controls arrow keys, undo U/Z, Escape quit, R restart."""
    content = _read_readme()
    # Arrow keys (case-insensitive check via both variants)
    assert ("Arrow" in content or "arrow" in content), "Missing 'Arrow' keys reference"
    # Undo key U or Z
    assert ("U" in content or "Z" in content), "Missing undo key U or Z"
    assert "undo" in content.lower(), "Missing 'undo' keyword for controls"
    assert "Escape" in content, "Missing 'Escape' quit key"
    # R restart
    assert "R" in content, "Missing 'R' restart key"
    assert "Restart" in content or "restart" in content, "Missing restart keyword"


def test_readme_contains_how_to_run_tests() -> None:
    """AC-3: README contains how to run tests poetry run pytest."""
    content = _read_readme()
    assert "poetry run pytest" in content, "Missing 'poetry run pytest' test instruction"


def test_readme_contains_build_binary_command() -> None:
    """AC-4 build part: README contains pyinstaller build command tokens."""
    content = _read_readme()
    assert "pyinstaller" in content, "Missing 'pyinstaller' build tool"
    assert "--onefile" in content, "Missing '--onefile' flag"
    assert "--windowed" in content, "Missing '--windowed' flag"
    assert "--name favur-2048" in content, "Missing '--name favur-2048'"
    assert "src/main.py" in content, "Missing 'src/main.py' entry point"


def test_readme_contains_platform_notes() -> None:
    """AC-4 platform part: README contains platform notes Windows macOS Linux."""
    content = _read_readme()
    assert "Windows" in content, "Missing platform note 'Windows'"
    assert "macOS" in content, "Missing platform note 'macOS'"
    assert "Linux" in content, "Missing platform note 'Linux'"


def test_readme_contains_visual_proof_reference() -> None:
    """AC-5 visual-proof part: README contains visual-proof manifest reference."""
    content = _read_readme()
    assert "visual-proof/README.md" in content, "Missing 'visual-proof/README.md' reference"
    assert "obs_000001" in content, "Missing observation id 'obs_000001' or range obs_000001-012"


def test_readme_contains_ci_badge_placeholder() -> None:
    """AC-5 CI badge part: README contains CI badge placeholder."""
    content = _read_readme()
    assert "CI" in content, "Missing 'CI' badge reference"
    # Accept any of: badge keyword, ![CI], [![CI]
    has_badge = ("badge" in content.lower()) or ("![CI]" in content) or ("[![CI]" in content)
    assert has_badge, "Missing CI badge placeholder pattern (badge or ![CI] or [![CI])"
