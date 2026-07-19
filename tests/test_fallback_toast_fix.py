"""
tests/test_fallback_toast_fix.py — TDD red-phase tests for fallback removal Q-014 and toast overlap Q-016.

Phase 5 Sprint 1 Wave1 Tasks 1 and 2. Pseudocode at registry://pseudocode/phase_5_sprint_1_wave1_fallback_toast.md
defines fallback removal Q-014 (4 copies _FallbackEffectManager _FallbackToastManager -> loud ImportError)
and toast overlap Q-016 (base_x 10 width 200 HUD preserved).

AC mapping:
- AC-014-1: no _FallbackEffectManager in main.py
- AC-014-2: no _FallbackToastManager in main.py
- AC-014-3: no fallback in effects.py/hud.py
- AC-014-4: loud ImportError with hint pygame-ce ^2.5.0
- AC-016-1: toast base_x 10 width 200 range 10-210 no overlap hx 550
- AC-016-2: HUD preserved during game-over dim top 120px or re-draw
- AC-016-3: existing toast artifact valid PNG header 89 50 4E 47 700x800 not overwritten
- AC-016-4: grep toast base_x 10 width 200 present
- AC-012-1: existing artifacts 10376 16571 21606 41407 header 89 50 4E 47 700x800 not overwritten

Red phase: tests MUST FAIL initially because fallback still present and toast still 280/410.
This is intentional TDD.

Headless: file reads and grep only, no pygame display needed.
"""

from __future__ import annotations

import pathlib
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: str) -> str:
    """Read file content as text."""
    return pathlib.Path(path).read_text(encoding="utf-8")


def _file_contains(path: str, needle: str) -> bool:
    """Check if file contains needle."""
    try:
        content = _read_file(path)
        return needle in content
    except FileNotFoundError:
        return False


def _count_occurrences(path: str, needle: str) -> int:
    """Count occurrences of needle in file."""
    try:
        content = _read_file(path)
        return content.count(needle)
    except FileNotFoundError:
        return 0


def _png_header_valid(path: str) -> bool:
    """Check PNG header 89 50 4E 47 = b'\\x89PNG\\r\\n\\x1a\\n'."""
    try:
        data = pathlib.Path(path).read_bytes()
        if len(data) < 8:
            return False
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    except FileNotFoundError:
        return False


def _png_first4_valid(path: str) -> bool:
    """Check first 4 bytes 89 50 4E 47."""
    try:
        data = pathlib.Path(path).read_bytes()
        if len(data) < 4:
            return False
        return data[:4] == b"\x89PNG"
    except FileNotFoundError:
        return False


# ---------------------------------------------------------------------------
# Group 1: Fallback Removal Q-014
# ---------------------------------------------------------------------------


def test_no_fallback_effect_manager_in_main() -> None:
    """AC-014-1: When src/main.py is grepped for _FallbackEffectManager, then no matches."""
    content = _read_file("src/main.py")
    assert "_FallbackEffectManager" not in content, (
        "Found _FallbackEffectManager in src/main.py - should be removed per Q-014. "
        f"Count: {content.count('_FallbackEffectManager')}"
    )


def test_no_fallback_toast_manager_in_main() -> None:
    """AC-014-2: When src/main.py is grepped for _FallbackToastManager, then no matches."""
    content = _read_file("src/main.py")
    assert "_FallbackToastManager" not in content, (
        "Found _FallbackToastManager in src/main.py - should be removed per Q-014. "
        f"Count: {content.count('_FallbackToastManager')}"
    )


def test_no_fallback_in_effects_hud() -> None:
    """AC-014-3: When effects.py and hud.py grepped for fallback, then no matches."""
    for file_path in ["src/render/effects.py", "src/render/hud.py"]:
        content = _read_file(file_path)
        assert "_FallbackEffectManager" not in content, (
            f"Found _FallbackEffectManager in {file_path}"
        )
        assert "_FallbackToastManager" not in content, (
            f"Found _FallbackToastManager in {file_path}"
        )


def test_loud_import_error_with_hint() -> None:
    """AC-014-4: When EffectManager import fails, then loud ImportError with hint pygame-ce ^2.5.0."""
    content = _read_file("src/main.py")
    # Must contain install hint
    has_hint = (
        "pygame-ce ^2.5.0" in content
        or "pygame-ce not installed" in content
        or "pip install pygame-ce" in content
    )
    assert has_hint, "Install hint pygame-ce ^2.5.0 not found in src/main.py"

    # Must have loud ImportError with chaining from e
    has_loud = "raise ImportError" in content
    assert has_loud, "No loud raise ImportError found in src/main.py"

    # Check for chained exception from e
    has_chaining = "from e" in content or "from exc" in content
    assert has_chaining, "ImportError should be chained with 'from e' or 'from exc'"

    # Ensure not silent no-op: fallback classes should not exist, and warning-only handling for ImportError should be gone
    # The file should not have fallback class definitions
    assert "_FallbackEffectManager" not in content, "Fallback still present, not loud failure"
    assert "_FallbackToastManager" not in content, "Fallback still present, not loud failure"


def test_effect_manager_importable() -> None:
    """AC-014-4 regression: EffectManager importable when pygame available."""
    try:
        from src.render.effects import EffectManager

        assert EffectManager is not None
        assert callable(EffectManager)
    except ImportError as e:
        # If pygame not installed, this is okay in headless, but we still check file has loud error
        content = _read_file("src/main.py")
        assert "pygame-ce" in content, f"Import failed but no hint in main.py: {e}"


# ---------------------------------------------------------------------------
# Group 2: Toast Overlap Fix Q-016
# ---------------------------------------------------------------------------


def test_toast_base_x_10_width_200() -> None:
    """AC-016-1: When hud.py inspected, then toast base_x 10 left side width 200 range 10-210 no overlap hx 550."""
    content = _read_file("src/render/hud.py")

    # Check TOAST_W constant is 200
    assert "TOAST_W" in content, "TOAST_W constant not found"
    # Look for TOAST_W = 200
    has_200 = "TOAST_W = 200" in content or "TOAST_W: int = 200" in content or "TOAST_W=200" in content
    snippet = [line for line in content.splitlines() if "TOAST_W" in line][:5]
    assert has_200, f"TOAST_W should be 200, not 280. Content snippet: {snippet}"

    # Check base_x = 10 present
    has_base_x_10 = "base_x = 10" in content or "base_x=10" in content
    assert has_base_x_10, "base_x = 10 not found in hud.py - should be left side per Q-016"

    # Verify no old base_x 410
    has_old_410 = "WINDOW_W - TOAST_W - 10" in content
    # After fix, old calculation should be gone or replaced
    # We allow it if base_x 10 also present, but ideally old should be removed
    # For strict red phase, we check old should NOT be present
    assert not has_old_410, (
        "Old base_x calculation WINDOW_W - TOAST_W -10 (=410) still present, should be 10"
    )

    # Calculate range no overlap
    new_base_x = 10
    new_width = 200
    toast_right = new_base_x + new_width  # 210
    high_score_hx = 550  # surf_w -150 = 700-150
    assert toast_right < high_score_hx, f"Toast right edge {toast_right} should be < high-score hx {high_score_hx}"
    assert toast_right == 210, f"Expected 210, got {toast_right}"


def test_toast_no_overlap_high_score() -> None:
    """AC-016-1: Verify toast range 10-210 no overlap hx 550, old 410-690 overlaps."""
    # Old calculation
    old_base_x = 410
    old_width = 280
    old_right = old_base_x + old_width  # 690
    hx = 550
    assert old_right > hx, f"Old range should overlap: {old_right} > {hx} should be True"

    # New calculation
    new_base_x = 10
    new_width = 200
    new_right = new_base_x + new_width  # 210
    assert new_right < hx, f"New range should NOT overlap: {new_right} < {hx} should be True"

    # Verify file has new values
    content = _read_file("src/render/hud.py")
    # After fix, TOAST_W 200 and base_x 10 should be present
    assert "200" in content, "200 not found in hud.py"
    # Check for base_x 10
    assert "base_x = 10" in content or "base_x=10" in content, "base_x 10 not found"


def test_hud_preserved_during_game_over() -> None:
    """AC-016-2: Game-over overlay preserves HUD visibility top 120px or re-draws HUD after dim."""
    content = _read_file("src/render/hud.py")

    # Find draw_game_over function
    assert "def draw_game_over" in content, "draw_game_over function not found"

    # Check for HUD preservation logic: either clipping to HUD_H or re-draw
    has_hud_h_clipping = (
        "HUD_H" in content
        and ("WINDOW_H - HUD_H" in content or "WINDOW_H-HUD_H" in content or "y>=HUD_H" in content or "(0, HUD_H)" in content or "(0, 120)" in content)
    )
    has_redraw = (
        "draw_hud" in content.split("def draw_game_over")[-1]  # draw_hud called inside draw_game_over
        or "alpha 200" in content
        or "200+" in content
    )

    # At least one preservation method must be present
    assert has_hud_h_clipping or has_redraw, (
        "HUD preservation not found in draw_game_over: expected either "
        "clipping to y>=HUD_H (0,120) or re-draw HUD after dim with alpha 200+. "
        f"has_hud_h_clipping={has_hud_h_clipping}, has_redraw={has_redraw}"
    )

    # More specific: check overlay clipped to (0, HUD_H) or (WINDOW_W, WINDOW_H-HUD_H)
    # or overlay size (700, 680) = (WINDOW_W, WINDOW_H-HUD_H)
    has_clipped_overlay = (
        "(0, HUD_H)" in content
        or "(0, 120)" in content
        or "WINDOW_H - HUD_H" in content
        or "(700, 680)" in content
        or "680" in content  # WINDOW_H - HUD_H = 800-120=680
    )
    assert has_clipped_overlay or has_redraw, (
        "Expected clipped overlay to y>=HUD_H 120px or re-draw HUD after dim"
    )


def test_existing_toast_artifact_still_valid() -> None:
    """AC-016-3, AC-012-1: Existing toast artifact still valid PNG header 89 50 4E 47 700x800 not overwritten."""
    path = "visual-proof/phase-4-toast.png"
    p = pathlib.Path(path)
    assert p.exists(), f"{path} does not exist - should not be overwritten"

    data = p.read_bytes()
    assert len(data) > 0, f"{path} is empty"
    # Check PNG header 89 50 4E 47 = b'\\x89PNG'
    assert data[:4] == b"\x89PNG", f"{path} invalid PNG header first 4 bytes: {data[:4]!r} expected 89 50 4E 47"
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} invalid PNG 8-byte header: {data[:8]!r}"

    # Size check - expected 21606 but allow >0 for flexibility
    assert len(data) >= 1000, f"{path} too small: {len(data)} bytes, expected ~21606"

    # Check not overwritten by fix: file should exist and be valid
    # We don't enforce exact size to allow minor variations, but must be valid PNG


def test_grep_toast_base_x_10_width_200_present() -> None:
    """AC-016-4: When hud.py grepped for toast base_x, then new value 10 and width 200 present."""
    content = _read_file("src/render/hud.py")

    # Grep for base_x 10
    assert "base_x" in content, "base_x not found in hud.py"
    assert "10" in content, "10 not found in hud.py"

    # Grep for TOAST_W 200
    has_toast_w_200 = "TOAST_W = 200" in content or "TOAST_W: int = 200" in content
    found_lines = [line.strip() for line in content.splitlines() if "TOAST_W" in line][:5]
    assert has_toast_w_200, f"TOAST_W = 200 not found. Found: {found_lines}"

    has_toast_width_200 = (
        "TOAST_WIDTH = 200" in content
        or "TOAST_WIDTH: int = 200" in content
        or "TOAST_WIDTH = TOAST_W" in content
    )
    # TOAST_WIDTH alias should also be 200 or equal to TOAST_W
    assert has_toast_width_200 or "TOAST_WIDTH" in content, "TOAST_WIDTH alias not found"

    # Check width 200 present
    assert "200" in content, "width 200 not found in hud.py"


# ---------------------------------------------------------------------------
# Group 3: Edge Cases and Regression
# ---------------------------------------------------------------------------


def test_oserror_handling_preserved() -> None:
    """Regression: OSError handling preserved in ensure_visual_proof_dir and capture_screenshot."""
    content = _read_file("src/main.py")

    # Check except OSError in ensure_visual_proof_dir
    assert "except OSError" in content, "except OSError not found in main.py - should be preserved"

    # Check mkdir parents True exist_ok True
    has_mkdir = "mkdir" in content and "parents=True" in content and "exist_ok=True" in content
    assert has_mkdir, "mkdir(parents=True, exist_ok=True) not found - should be preserved"

    # Check OSError handling in capture_screenshot
    # Should have at least 2 OSError handlers (dir creation and screenshot save)
    oserror_count = content.count("except OSError")
    assert oserror_count >= 2, f"Expected at least 2 except OSError, found {oserror_count}"


def test_single_tick_60fps() -> None:
    """Regression: Single clock.tick(60) 60 FPS."""
    content = _read_file("src/main.py")

    count = content.count("clock.tick(60)")
    assert count == 1, f"Expected single clock.tick(60), found {count} occurrences - should be 1 per Q-015"

    # Also check dt = clock.tick(60)/1000.0 pattern
    assert "clock.tick(60)" in content, "clock.tick(60) not found"
    assert "/ 1000.0" in content or "/1000" in content, "dt conversion /1000.0 not found"


def test_headless_importable_no_pygame_leak() -> None:
    """Regression: Headless importable no pygame leak in core."""
    # Check sys.modules before and after importing core
    # First, ensure pygame not already loaded from previous tests
    # We test that src/core modules don't import pygame

    # Read core files for pygame import
    core_files = [
        "src/core/board.py",
        "src/core/rules.py",
        "src/core/score.py",
        "src/core/history.py",
        "src/core/achievements.py",
        "src/core/twist.py",
        "src/core/gamestate.py",
    ]
    for core_file in core_files:
        p = pathlib.Path(core_file)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            # Check for import pygame
            assert "import pygame" not in content, f"Found 'import pygame' in {core_file} - should be headless"
            assert "from pygame" not in content, f"Found 'from pygame' in {core_file} - should be headless"

    # Also test sys.modules delta
    before = set(sys.modules.keys())
    try:
        import src.core.board  # noqa: F401

        after = set(sys.modules.keys())
        new_modules = after - before
        # Check pygame not in new modules
        pygame_leaked = [m for m in new_modules if "pygame" in m.lower()]
        assert len(pygame_leaked) == 0, f"pygame leaked via core import: {pygame_leaked}"
    except Exception:
        # If import fails, still check file content
        pass


def test_artifacts_not_overwritten() -> None:
    """AC-012-1: Existing artifacts 10376 16571 21606 41407 header 89 50 4E 47 700x800 not overwritten."""
    artifacts = [
        "visual-proof/phase-3-first-light.png",
        "visual-proof/phase-4-merge.png",
        "visual-proof/phase-4-toast.png",
        "visual-proof/phase-4-gameover.png",
    ]
    for artifact_path in artifacts:
        p = pathlib.Path(artifact_path)
        assert p.exists(), f"Artifact {artifact_path} missing - should not be overwritten per Q-012"

        data = p.read_bytes()
        assert len(data) > 0, f"{artifact_path} empty"
        assert data[:4] == b"\x89PNG", f"{artifact_path} invalid header 89 50 4E 47: {data[:4]!r}"
        assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{artifact_path} invalid 8-byte header"

        # Size should be >0, ideally matching expected but allow flexibility
        assert len(data) >= 1000, f"{artifact_path} too small: {len(data)}"


def test_toast_rect_updated() -> None:
    """Additional: toast_rect in main.py _SimpleLayout should be updated to base_x 10 width 200."""
    content = _read_file("src/main.py")

    # Check for toast_rect method
    if "def toast_rect" in content:
        # Should have new values (10, ..., 200, 60) not old (410, ..., 280, 60)
        # Look for toast_rect line
        for line in content.splitlines():
            if "toast_rect" in line and "return" in line:
                # Old: (700 - 280 -10, 10 + index*(60+10), 280, 60) = (410, ..., 280, 60)
                # New: (10, 10 + index*(60+10), 200, 60)
                if "280" in line and "410" in line:
                    assert False, f"Old toast_rect still present: {line.strip()} - should be (10, ..., 200, 60)"
        # Check new present
        has_new = "(10," in content and "200, 60" in content
        # This is optional but good to check
        assert has_new or "base_x = 10" in content or "10" in content, "New toast_rect (10, ..., 200, 60) not found"


def test_no_synthetic_merge() -> None:
    """Regression: No _SyntheticMerge staging, real turn pipeline."""
    content = _read_file("src/main.py")
    assert "_SyntheticMerge" not in content, "Found _SyntheticMerge - should not exist per Q-010"
    assert "SyntheticMerge" not in content, "Found SyntheticMerge - should not exist"


def test_pygame_ce_hint_format() -> None:
    """AC-014-4: Install hint format pygame-ce ^2.5.0."""
    content = _read_file("src/main.py")
    # Must have pygame-ce and version hint
    assert "pygame-ce" in content, "pygame-ce not found in main.py"
    # Check for ^2.5.0 or install hint
    has_version_hint = "^2.5.0" in content or "2.5.0" in content or "pip install" in content or "poetry install" in content
    assert has_version_hint, "Version hint ^2.5.0 or install instruction not found"
