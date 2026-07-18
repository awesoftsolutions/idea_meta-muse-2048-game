"""
tests/test_hud.py — TDD tests for HUD with score, high_score, achievement toasts, reactor chrome.

Red phase: these tests MUST fail initially because src/render/hud.py does not exist yet.
Covers AC-1 to AC-7: HUD draws without crash 700x800, score/high_score display,
toast queue timing 2-3 sec stacking, toast animation scaling 1.0->1.2->1.0 particles
per heat cool 2-3 warm 4-5 hot 6-8 unstable 10+, heat identity colors
#3B82F6 #F59E0B #EF4444 #FFFFFF, no external assets programmatic only SysFont,
no board mutation, error handling None surface, overlay 700x800, queue overflow bounded max 5.

System: Phase 4 Sprint 1 Task 3 Wave2 Step 2 TDD red phase.
"""

from __future__ import annotations

import copy
import os
import pathlib
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface with fill, blit, get_rect, get_width/height for headless draw tests."""
    surface = MagicMock()
    surface.fill = MagicMock()
    surface.blit = MagicMock()
    surface.get_rect = MagicMock(return_value=MagicMock(center=(0, 0), width=700, height=800))
    surface.get_width = MagicMock(return_value=700)
    surface.get_height = MagicMock(return_value=800)
    return surface


@pytest.fixture
def sample_achievements() -> List[Dict[str, Any]]:
    """Sample achievements list with cold_fusion and heat_burst."""
    return [
        {"id": "cold_fusion", "title": "Cold Fusion", "description": "First merge cold"},
        {"id": "heat_burst", "title": "Heat Burst", "description": "Warm streak"},
    ]


@pytest.fixture
def all_heat_achievements() -> List[Dict[str, Any]]:
    """Achievements covering all heat treatments."""
    return [
        {"id": "cold_fusion", "title": "Cold Fusion", "description": "cool"},
        {"id": "warm_flare", "title": "Warm Flare", "description": "warm"},
        {"id": "hot_vent", "title": "Hot Vent", "description": "hot"},
        {"id": "unstable_core", "title": "Unstable Core", "description": "unstable"},
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_display_available() -> bool:
    """Check if DISPLAY is available for pygame real surface tests."""
    # On Windows, DISPLAY env not used, but we still check for headless CI
    # If pygame not installed, treat as no display
    try:
        import pygame  # noqa: F401

        # On Linux, check DISPLAY
        if os.name != "nt" and os.environ.get("DISPLAY") is None and os.environ.get("WAYLAND_DISPLAY") is None:
            # Try to see if we can still create surface without display
            # pygame.Surface does not need display, but font might
            # For safety, return False on Linux without DISPLAY to skip real surface tests
            return False
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# AC-1, AC-4: HUD draws without crash
# ---------------------------------------------------------------------------


def test_hud_draws_without_crash(mock_surface: MagicMock) -> None:
    """AC-1, AC-4: draw_hud does not crash with mock surface 700x800."""
    # Import inside test for red phase - module does not exist yet
    from src.render.hud import draw_hud

    surface = mock_surface
    score = 0
    high_score = 0
    achievements: List[Any] = []
    toasts: List[Any] = []

    try:
        draw_hud(surface, score, high_score, achievements, toasts)
    except Exception as e:
        pytest.fail(f"draw_hud crashed with mock surface: {e}")

    assert surface is not None
    # Verify mock was used (fill or blit or draw calls would be via pygame.draw, not surface directly)
    # At minimum, surface should still be valid
    assert mock_surface.get_width() == 700
    assert mock_surface.get_height() == 800


def test_score_high_score_display(mock_surface: MagicMock) -> None:
    """AC-1: score and high_score rendered without mutation, inputs unchanged."""
    from src.render.hud import draw_hud

    surface = mock_surface
    score = 1234
    high_score = 5678
    achievements: List[Any] = []

    try:
        draw_hud(surface, score, high_score, achievements, None)
    except Exception as e:
        pytest.fail(f"draw_hud crashed with score/high_score: {e}")

    # Inputs unchanged (ints immutable but check)
    assert score == 1234, "score mutated"
    assert high_score == 5678, "high_score mutated"


def test_overlay_700x800(mock_surface: MagicMock) -> None:
    """AC-1, AC-4: HUD overlay dimensions 700x800 reactor chrome, surface size unchanged."""
    from src.render.hud import WINDOW_H, WINDOW_W, draw_hud

    surface = mock_surface

    # Verify constants
    assert WINDOW_W == 700, f"WINDOW_W {WINDOW_W} != 700"
    assert WINDOW_H == 800, f"WINDOW_H {WINDOW_H} != 800"

    try:
        draw_hud(surface, 0, 0, [], None)
    except Exception as e:
        pytest.fail(f"draw_hud crashed on 700x800 overlay: {e}")

    # Surface size unchanged
    assert surface.get_width() == 700
    assert surface.get_height() == 800

    # HUD rect (0,0,700,120) within window - check constants
    from src.render.hud import HUD_H

    assert HUD_H == 120, f"HUD_H {HUD_H} != 120"
    assert HUD_H < WINDOW_H, "HUD_H should be less than WINDOW_H"
    assert WINDOW_W == 700


# ---------------------------------------------------------------------------
# AC-2, AC-7: Toast queue timing
# ---------------------------------------------------------------------------


def test_toast_queue_timing(sample_achievements: List[Dict[str, Any]]) -> None:
    """AC-2, AC-7: ToastManager push/update/has_visible timing 2-3 sec."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    assert manager.has_visible() is False, "Empty manager should not have visible"

    # Push 2 achievements
    manager.push(sample_achievements)
    assert len(manager.toasts) == 2, f"Expected 2 toasts after push, got {len(manager.toasts)}"
    assert manager.has_visible() is True, "Should have visible after push"

    # Update 1.0 sec still visible
    manager.update(1.0)
    assert manager.has_visible() is True, "Should still be visible after 1.0 sec"
    # Check elapsed ~1.0
    for toast in manager.toasts:
        assert 0.9 <= toast.elapsed <= 1.1, f"Toast elapsed {toast.elapsed} not ~1.0"

    # Update 2.0 more total 3.0 > duration 2.5 should be expired
    manager.update(2.0)
    assert manager.has_visible() is False, "Should not have visible after total 3.0 sec > 2.5 duration"
    assert len(manager.toasts) == 0, "Expired toasts should be removed"


def test_toast_queue_overflow_bounded() -> None:
    """AC-2: Toast queue overflow bounded max 5 prevents memory leak."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)

    # Push 10 achievements sequentially
    for i in range(10):
        manager.push([{"id": f"ach_{i}", "title": f"Ach {i}", "description": f"Desc {i}"}])

    # Bounded to max 5
    assert len(manager.toasts) <= 5, f"Queue len {len(manager.toasts)} >5 not bounded"
    assert len(manager.toasts) == 5, f"Expected 5 after overflow, got {len(manager.toasts)}"

    # Oldest removed - should contain ach_5..ach_9
    ids = [t.achievement_id for t in manager.toasts]
    assert "ach_0" not in ids, "Oldest ach_0 should be removed"
    assert "ach_9" in ids, "Newest ach_9 should be present"


# ---------------------------------------------------------------------------
# AC-2, AC-7: Toast animation scaling particles
# ---------------------------------------------------------------------------


def test_toast_animation_scaling(all_heat_achievements: List[Dict[str, Any]]) -> None:
    """AC-2, AC-7: toast animation scaling 1.0->1.2->1.0 and particles per heat identity."""
    from src.render.hud import Toast, ToastManager

    # Cool: cold_fusion -> 2-3 particles
    toast_cool = Toast(
        achievement_id="cold_fusion",
        title="Cold Fusion",
        description="cool test",
    )
    assert toast_cool.heat_treatment == "cool", f"Expected cool, got {toast_cool.heat_treatment}"
    assert 1.0 <= toast_cool.scale <= 1.2, f"Scale {toast_cool.scale} not in [1.0,1.2]"
    assert toast_cool.particles is not None
    assert 2 <= len(toast_cool.particles) <= 5, f"Cool particles {len(toast_cool.particles)} not in 2-3 (+bonus)"

    # Warm via manager
    manager_warm = ToastManager(max_toasts=5)
    manager_warm.push([{"id": "warm_flare", "title": "Warm Flare", "description": "warm"}])
    assert len(manager_warm.toasts) == 1
    warm_toast = manager_warm.toasts[0]
    assert warm_toast.heat_treatment == "warm"
    assert 4 <= len(warm_toast.particles) <= 8, f"Warm particles {len(warm_toast.particles)} not in 4-5 (+bonus)"

    # Hot
    manager_hot = ToastManager(max_toasts=5)
    manager_hot.push([{"id": "hot_vent", "title": "Hot Vent", "description": "hot"}])
    hot_toast = manager_hot.toasts[0]
    assert hot_toast.heat_treatment == "hot"
    assert 6 <= len(hot_toast.particles) <= 12, f"Hot particles {len(hot_toast.particles)} not in 6-8 (+bonus)"

    # Unstable
    manager_unstable = ToastManager(max_toasts=5)
    manager_unstable.push([{"id": "unstable_core", "title": "Unstable Core", "description": "unstable"}])
    unstable_toast = manager_unstable.toasts[0]
    assert unstable_toast.heat_treatment == "unstable"
    assert len(unstable_toast.particles) >= 10, f"Unstable particles {len(unstable_toast.particles)} not >=10"

    # Update dt 0.1 lerp 1.2->1.0
    manager_warm.update(0.1)
    # After 0.1 sec, scale should still be in pulse range or decreasing
    if manager_warm.toasts:
        assert 1.0 <= manager_warm.toasts[0].scale <= 1.2, f"Scale after 0.1 {manager_warm.toasts[0].scale} not in [1.0,1.2]"


# ---------------------------------------------------------------------------
# AC-3: Heat identity colors
# ---------------------------------------------------------------------------


def test_heat_identity_colors() -> None:
    """AC-3: heat identity colors #3B82F6 #F59E0B #EF4444 #FFFFFF mapping."""
    from src.render.hud import (
        HEAT_COOL,
        HEAT_HOT,
        HEAT_UNSTABLE,
        HEAT_WARM,
        _heat_color_for_treatment,
    )

    # Constants defined correctly
    assert HEAT_COOL == (59, 130, 246), f"HEAT_COOL {HEAT_COOL} != (59,130,246) #3B82F6"
    assert HEAT_WARM == (245, 158, 11), f"HEAT_WARM {HEAT_WARM} != (245,158,11) #F59E0B"
    assert HEAT_HOT == (239, 68, 68), f"HEAT_HOT {HEAT_HOT} != (239,68,68) #EF4444"
    assert HEAT_UNSTABLE == (255, 255, 255), f"HEAT_UNSTABLE {HEAT_UNSTABLE} != (255,255,255) #FFFFFF"

    # Function mapping
    assert _heat_color_for_treatment("cool") == (59, 130, 246)
    assert _heat_color_for_treatment("warm") == (245, 158, 11)
    assert _heat_color_for_treatment("hot") == (239, 68, 68)
    assert _heat_color_for_treatment("unstable") == (255, 255, 255)

    # Default fallback
    assert _heat_color_for_treatment("unknown") == (59, 130, 246), "Unknown should default to cool"


# ---------------------------------------------------------------------------
# AC-4: No external assets, no board mutation
# ---------------------------------------------------------------------------


def test_no_external_assets() -> None:
    """AC-4: no image.load no font file path only SysFont programmatic only."""
    hud_path = pathlib.Path("src/render/hud.py")
    assert hud_path.exists(), "src/render/hud.py does not exist yet (red phase)"

    content = hud_path.read_text(encoding="utf-8")

    assert "image.load" not in content, "Found pygame.image.load in hud.py - programmatic only violation"

    # Check font.Font file path - only SysFont allowed
    lines_with_font_font = [
        line
        for line in content.splitlines()
        if "font.Font" in line and "SysFont" not in line and not line.strip().startswith("#")
    ]
    assert len(lines_with_font_font) == 0, f"Found font.Font file path usage: {lines_with_font_font}"

    assert "SysFont" in content, "SysFont not found in hud.py - should use SysFont only"

    # Reactor chrome colors present
    assert "#0F172A" in content or "15, 23, 42" in content or "(15, 23, 42)" in content, "Reactor chrome #0F172A not found"
    assert "HEAT_COOL" in content or "#3B82F6" in content, "Heat identity #3B82F6 not found"


def test_no_board_mutation(mock_surface: MagicMock) -> None:
    """AC-4: draw_hud does not mutate inputs achievements list."""
    from src.render.hud import draw_hud

    achievements = [{"id": "cold_fusion", "title": "Cold Fusion", "description": "test"}]
    before = copy.deepcopy(achievements)
    score = 100
    high_score = 200

    try:
        draw_hud(mock_surface, score, high_score, achievements, None)
    except Exception as e:
        pytest.fail(f"draw_hud crashed in no mutation test: {e}")

    assert achievements == before, f"Achievements mutated: before {before} after {achievements}"
    assert score == 100, "score mutated"
    assert high_score == 200, "high_score mutated"


# ---------------------------------------------------------------------------
# AC-5: Error handling None surface
# ---------------------------------------------------------------------------


def test_error_handling_none_surface() -> None:
    """AC-5: ValueError raised when surface None per spec."""
    from src.render.hud import ToastManager, draw_hud

    # draw_hud None surface
    with pytest.raises(ValueError, match="surface None"):
        draw_hud(None, 0, 0, [], None)

    # ToastManager draw None
    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "test", "title": "Test", "description": "test"}])
    with pytest.raises(ValueError, match="surface None"):
        manager.draw(None)

    # ToastManager push None
    with pytest.raises(ValueError, match="achievements None"):
        manager.push(None)  # type: ignore[arg-type]

    # draw_hud_with_gamestate None surface
    from src.render.hud import draw_hud_with_gamestate

    with pytest.raises(ValueError, match="surface None"):
        draw_hud_with_gamestate(None, 0, 0, game_state=None, layout=None)

    # ToastManager update dt None and negative
    with pytest.raises(ValueError):
        manager.update(None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="negative"):
        manager.update(-0.1)


# ---------------------------------------------------------------------------
# Additional: Constants and reactor chrome
# ---------------------------------------------------------------------------


def test_reactor_chrome_constants() -> None:
    """Verify reactor chrome constants #0F172A #1E293B #334155 #475569 defined."""
    from src.render.hud import BOARD_BG, BORDER, EMPTY_CELL, REACTOR_BG

    assert REACTOR_BG == (15, 23, 42), f"REACTOR_BG {REACTOR_BG} != (15,23,42) #0F172A"
    assert BOARD_BG == (30, 41, 59), f"BOARD_BG {BOARD_BG} != (30,41,59) #1E293B"
    assert EMPTY_CELL == (51, 65, 85), f"EMPTY_CELL {EMPTY_CELL} != (51,65,85) #334155"
    assert BORDER == (71, 85, 105), f"BORDER {BORDER} != (71,85,105) #475569"


def test_toast_dataclass_fields() -> None:
    """Verify Toast dataclass has required fields per pseudocode."""
    from src.render.hud import Toast

    toast = Toast(achievement_id="test_id", title="Test", description="Desc")

    assert hasattr(toast, "achievement_id")
    assert hasattr(toast, "title")
    assert hasattr(toast, "description")
    assert hasattr(toast, "elapsed")
    assert hasattr(toast, "duration")
    assert hasattr(toast, "y_offset")
    assert hasattr(toast, "alpha")
    assert hasattr(toast, "scale")
    assert hasattr(toast, "heat_treatment")
    assert hasattr(toast, "particles")

    assert toast.elapsed == 0.0
    assert toast.duration == 2.5
    assert toast.alpha == 255
    assert toast.scale == 1.0
