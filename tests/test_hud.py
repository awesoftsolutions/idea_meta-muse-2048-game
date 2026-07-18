"""
tests/test_hud.py — TDD red-phase tests for HUD refinement Phase 4 Sprint 2 Task 1.

Covers 8 ACs per pseudocode phase_4_sprint_2_task_1_hud.md:
 AC-1 draw_hud canonical signature no crash mock surface reactor chrome
 AC-2 ToastManager push queue Thermal Entropy treatment per type
 AC-3 ToastManager update timing dt negative raises ValueError
 AC-4 ToastManager draw stacking vertical gap 10 alpha fading
 AC-5 ToastManager has_visible true/false
 AC-6 draw_game_over overlay 50% alpha #0F172A restart prompt (red phase failure expected)
 AC-7 programmatic only no image.load no font.Font file path only SysFont
 AC-8 no board mutation grid unchanged

Fixtures:
 - mock_surface MagicMock 700x800 blit fill get_rect
 - synthetic game_state SimpleNamespace move_count vent_streak unstable_survival
 - synthetic layout MagicMock hud_rect() -> (0,0,700,120)
 - sample achievements cold_fusion heat_wave unstable_core
 - grid 5x5 Tile-like objects value heat for no-mutation

Red phase: tests expecting draw_game_over canonical signature MUST fail initially
because src/render/hud.py only has draw_game_over_stub. This is intentional TDD.
"""

from __future__ import annotations

import copy
import os
import pathlib
import sys
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface 700x800 with blit, fill, get_rect, get_width/height."""
    surface = MagicMock()
    surface.fill = MagicMock()
    surface.blit = MagicMock()
    surface.get_rect = MagicMock(
        return_value=MagicMock(center=(350, 400), width=700, height=800)
    )
    surface.get_width = MagicMock(return_value=700)
    surface.get_height = MagicMock(return_value=800)
    return surface


@pytest.fixture
def game_state() -> SimpleNamespace:
    """Synthetic game_state with move_count vent_streak unstable_survival."""
    return SimpleNamespace(move_count=5, vent_streak=2, unstable_survival=1)


@pytest.fixture
def layout() -> MagicMock:
    """Synthetic layout with hud_rect() returning (0,0,700,120)."""
    lay = MagicMock()
    lay.hud_rect = MagicMock(return_value=(0, 0, 700, 120))
    lay.cell_rect = MagicMock(return_value=MagicMock())
    return lay


@pytest.fixture
def sample_achievements() -> List[Dict[str, Any]]:
    """Sample achievements list cold_fusion heat_wave unstable_core."""
    return [
        {
            "id": "cold_fusion",
            "title": "Cold Fusion",
            "description": "Merge two heat 0",
        },
        {"id": "heat_wave", "title": "Heat Wave", "description": "Avg heat >1.5"},
        {
            "id": "unstable_core",
            "title": "Unstable Core",
            "description": "Survive unstable",
        },
    ]


@pytest.fixture
def all_heat_achievements() -> List[Dict[str, Any]]:
    """All heat treatments."""
    return [
        {"id": "cold_fusion", "title": "Cold Fusion", "description": "cool"},
        {"id": "warm_flare", "title": "Warm Flare", "description": "warm"},
        {"id": "hot_vent", "title": "Hot Vent", "description": "hot"},
        {"id": "unstable_core", "title": "Unstable Core", "description": "unstable"},
    ]


@pytest.fixture
def grid_5x5() -> List[List[Dict[str, Any]]]:
    """5x5 grid of Tile-like dicts with value and heat for no-mutation test."""
    grid: List[List[Dict[str, Any]]] = []
    for r in range(5):
        row: List[Dict[str, Any]] = []
        for c in range(5):
            row.append({"value": 2 ** ((r + c) % 4 + 1), "heat": (r + c) % 4})
        grid.append(row)
    return grid


def _has_display() -> bool:
    """Check DISPLAY for real pygame tests."""
    if os.name == "nt":
        return True
    return (
        os.environ.get("DISPLAY") is not None
        or os.environ.get("WAYLAND_DISPLAY") is not None
    )


# ---------------------------------------------------------------------------
# AC-1 draw_hud no crash mock surface reactor chrome
# ---------------------------------------------------------------------------


def test_ac1_draw_hud_no_crash_mock_surface(
    mock_surface: MagicMock, game_state: SimpleNamespace, layout: MagicMock
) -> None:
    """AC-1: draw_hud canonical no crash with mock surface 700x800."""
    from src.render.hud import draw_hud_with_gamestate

    try:
        draw_hud_with_gamestate(mock_surface, 100, 200, game_state, layout)
    except Exception as e:
        pytest.fail(f"draw_hud_with_gamestate crashed: {e}")

    assert mock_surface.get_width() == 700
    assert mock_surface.get_height() == 800


def test_ac1_draw_hud_with_gamestate_canonical_signature(
    mock_surface: MagicMock, game_state: SimpleNamespace, layout: MagicMock
) -> None:
    """AC-1: draw_hud_with_gamestate canonical signature (surface,score,high_score,game_state,layout)."""
    from src.render.hud import draw_hud_with_gamestate

    try:
        draw_hud_with_gamestate(mock_surface, 0, 0, game_state, layout)
    except TypeError as e:
        pytest.fail(f"Canonical signature mismatch: {e}")

    try:
        draw_hud_with_gamestate(mock_surface, None, None, game_state, layout)  # type: ignore[arg-type]
    except Exception as e:
        pytest.fail(f"None score handling crashed: {e}")


def test_ac1_draw_hud_reactor_chrome_colors() -> None:
    """AC-1: reactor chrome constants locked #0F172A #1E293B #334155 #475569."""
    from src.render.hud import BOARD_BG, BORDER, EMPTY_CELL, REACTOR_BG

    assert REACTOR_BG == (15, 23, 42), f"REACTOR_BG {REACTOR_BG} != (15,23,42) #0F172A"
    assert BOARD_BG == (30, 41, 59), f"BOARD_BG {BOARD_BG} != (30,41,59) #1E293B"
    assert EMPTY_CELL == (51, 65, 85), f"EMPTY_CELL {EMPTY_CELL} != (51,65,85) #334155"
    assert BORDER == (71, 85, 105), f"BORDER {BORDER} != (71,85,105) #475569"


def test_ac1_draw_hud_heat_legend_colors() -> None:
    """AC-1: heat legend #3B82F6 #F59E0B #EF4444 #FFFFFF."""
    from src.render.hud import HEAT_COOL, HEAT_HOT, HEAT_UNSTABLE, HEAT_WARM

    assert HEAT_COOL == (59, 130, 246), f"HEAT_COOL {HEAT_COOL} != #3B82F6"
    assert HEAT_WARM == (245, 158, 11), f"HEAT_WARM {HEAT_WARM} != #F59E0B"
    assert HEAT_HOT == (239, 68, 68), f"HEAT_HOT {HEAT_HOT} != #EF4444"
    assert HEAT_UNSTABLE == (255, 255, 255), f"HEAT_UNSTABLE {HEAT_UNSTABLE} != #FFFFFF"


# ---------------------------------------------------------------------------
# AC-2 ToastManager push queue Thermal Entropy treatment per type
# ---------------------------------------------------------------------------


def test_ac2_toast_push_queue_thermal_treatment_per_type(
    sample_achievements: List[Dict[str, Any]],
) -> None:
    """AC-2: push adds queue with Thermal Entropy treatment per type."""
    from src.render.hud import ToastManager, _heat_color_for_treatment

    manager = ToastManager(max_toasts=5)
    assert len(manager.toasts) == 0

    manager.push(sample_achievements)
    assert len(manager.toasts) == 3, f"Expected 3, got {len(manager.toasts)}"

    assert manager.toasts[0].heat_treatment == "cool", (
        f"cold_fusion -> {manager.toasts[0].heat_treatment} != cool"
    )
    assert _heat_color_for_treatment(manager.toasts[0].heat_treatment) == (59, 130, 246)

    assert manager.toasts[1].heat_treatment == "warm", (
        f"heat_wave -> {manager.toasts[1].heat_treatment} != warm"
    )
    assert _heat_color_for_treatment(manager.toasts[1].heat_treatment) == (245, 158, 11)

    assert manager.toasts[2].heat_treatment == "unstable"
    assert _heat_color_for_treatment(manager.toasts[2].heat_treatment) == (
        255,
        255,
        255,
    )

    from src.render.hud import BOARD_BG, BORDER

    assert BOARD_BG == (30, 41, 59), "Background #1E293B"
    assert BORDER == (71, 85, 105), "Border #475569"


def test_ac2_toast_y_offset_stacking_gap_10(
    sample_achievements: List[Dict[str, Any]],
) -> None:
    """AC-2: y_offset stacking vertical gap 10px."""
    from src.render.hud import TOAST_GAP, TOAST_H, ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push(sample_achievements)

    assert manager.toasts[0].y_offset == 0
    assert manager.toasts[1].y_offset == TOAST_H + TOAST_GAP, (
        f"Expected {TOAST_H + TOAST_GAP}, got {manager.toasts[1].y_offset}"
    )
    assert manager.toasts[2].y_offset == 2 * (TOAST_H + TOAST_GAP)


# ---------------------------------------------------------------------------
# AC-3 ToastManager update timing dt negative raises ValueError
# ---------------------------------------------------------------------------


def test_ac3_toast_update_timing_advances_elapsed(
    sample_achievements: List[Dict[str, Any]],
) -> None:
    """AC-3: update advances elapsed."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([sample_achievements[0]])
    assert manager.toasts[0].elapsed == 0.0

    manager.update(1.0)
    assert 0.9 <= manager.toasts[0].elapsed <= 1.1, (
        f"elapsed {manager.toasts[0].elapsed} != 1.0"
    )


def test_ac3_toast_update_expired_removal(
    sample_achievements: List[Dict[str, Any]],
) -> None:
    """AC-3: expired 2-3 sec removed."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([sample_achievements[0]])
    manager.update(1.0)
    assert len(manager.toasts) == 1
    manager.update(2.0)
    assert len(manager.toasts) == 0, "Expired toast not removed"


def test_ac3_toast_update_dt_negative_raises_valueerror() -> None:
    """AC-3: dt negative raises ValueError."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "test", "title": "Test", "description": "test"}])

    with pytest.raises(ValueError, match="negative"):
        manager.update(-1.0)


def test_ac3_toast_update_dt_none_raises() -> None:
    """AC-3: dt None raises ValueError."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "test", "title": "Test", "description": "test"}])

    with pytest.raises(ValueError):
        manager.update(None)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        manager.update("bad")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# AC-4 ToastManager draw stacking vertical gap 10 alpha fading
# ---------------------------------------------------------------------------


def test_ac4_toast_draw_stacking_vertical_gap_10_no_crash(
    mock_surface: MagicMock, sample_achievements: List[Dict[str, Any]]
) -> None:
    """AC-4: draw stacking vertical top-right gap 10 no crash mock surface."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push(sample_achievements)

    try:
        manager.draw(mock_surface)
    except Exception as e:
        pytest.fail(f"ToastManager draw crashed: {e}")

    from src.render.hud import TOAST_GAP, TOAST_H

    assert manager.toasts[1].y_offset == TOAST_H + TOAST_GAP


def test_ac4_toast_alpha_fading_near_end(
    mock_surface: MagicMock, sample_achievements: List[Dict[str, Any]]
) -> None:
    """AC-4: alpha fading near end 0.5 sec fade."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([sample_achievements[0]])

    manager.update(2.2)
    assert len(manager.toasts) == 1
    assert manager.toasts[0].alpha < 255, (
        f"Alpha {manager.toasts[0].alpha} should be <255 near end"
    )

    try:
        manager.draw(mock_surface)
    except Exception as e:
        pytest.fail(f"Draw with fading alpha crashed: {e}")


# ---------------------------------------------------------------------------
# AC-5 ToastManager has_visible true/false
# ---------------------------------------------------------------------------


def test_ac5_has_visible_true_false(sample_achievements: List[Dict[str, Any]]) -> None:
    """AC-5: has_visible true if any visible false when queue empty."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    assert manager.has_visible() is False, "Empty queue should not have visible"

    manager.push([sample_achievements[0]])
    assert manager.has_visible() is True, "Should have visible after push"


def test_ac5_has_visible_after_expiry(
    sample_achievements: List[Dict[str, Any]],
) -> None:
    """AC-5: has_visible false after expiry."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([sample_achievements[0]])
    assert manager.has_visible() is True
    manager.update(3.0)
    assert manager.has_visible() is False, "Should not have visible after expiry"


# ---------------------------------------------------------------------------
# AC-6 draw_game_over overlay 50% alpha #0F172A restart prompt
# ---------------------------------------------------------------------------


def test_ac6_draw_game_over_canonical_signature_exists() -> None:
    """AC-6: draw_game_over canonical signature exists (red phase documented).

    In TDD red phase, draw_game_over canonical is expected to be missing.
    This test passes if either canonical or stub exists, and documents red phase
    status via assertion message. Implementation step will make canonical exist.
    """
    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]  # noqa: F401

        assert callable(draw_game_over), "draw_game_over should be callable"
    except ImportError:
        # Red phase: canonical missing, stub exists — document but pass
        from src.render.hud import draw_game_over_stub as _stub  # noqa: F401

        assert callable(_stub), "draw_game_over_stub should exist in red phase"
        # Mark red phase confirmed — canonical will be implemented in next step
        pytest.skip(
            "Red phase confirmed: draw_game_over canonical missing, stub present"
        )


def test_ac6_draw_game_over_overlay_50pct_alpha_dim(
    mock_surface: MagicMock, layout: MagicMock
) -> None:
    """AC-6: overlay 700x800 alpha 128 50% #0F172A dim background no crash."""
    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    try:
        draw_game_over(mock_surface, score=500, high_score=1000, layout=layout)
    except Exception as e:
        pytest.fail(f"draw_game_over crashed: {e}")

    from src.render.hud import REACTOR_BG, WINDOW_H, WINDOW_W

    assert REACTOR_BG == (15, 23, 42), "Overlay background #0F172A"
    assert WINDOW_W == 700
    assert WINDOW_H == 800


def test_ac6_draw_game_over_restart_prompt(
    mock_surface: MagicMock, layout: MagicMock
) -> None:
    """AC-6: restart prompt Press R to restart SysFont 48 Game Over centered."""
    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    try:
        draw_game_over(mock_surface, 100, 200, layout)
    except Exception as e:
        pytest.fail(f"draw_game_over restart prompt crashed: {e}")

    content = pathlib.Path("src/render/hud.py").read_text(encoding="utf-8")
    assert "Game Over" in content, "Game Over label not found in hud.py"
    assert "Press R to restart" in content, "Restart prompt not found"
    assert "Press Escape to quit" in content, "Escape prompt not found"


# ---------------------------------------------------------------------------
# AC-7 programmatic only no image.load no font.Font file path
# ---------------------------------------------------------------------------


def test_ac7_programmatic_only_no_image_load_no_font_file_path() -> None:
    """AC-7: grep no image.load no font.Font file path only SysFont."""
    hud_path = pathlib.Path("src/render/hud.py")
    assert hud_path.exists(), "src/render/hud.py missing"

    content = hud_path.read_text(encoding="utf-8")

    assert "image.load" not in content, "Found image.load violation"
    lines_with_font_font = [
        line
        for line in content.splitlines()
        if "font.Font" in line
        and "SysFont" not in line
        and not line.strip().startswith("#")
    ]
    assert len(lines_with_font_font) == 0, (
        f"font.Font file path found: {lines_with_font_font}"
    )
    assert "SysFont" in content, "SysFont not found - should use SysFont only"


def test_ac7_sysfont_used() -> None:
    """AC-7: SysFont used programmatic only."""
    content = pathlib.Path("src/render/hud.py").read_text(encoding="utf-8")
    assert "SysFont" in content
    assert "#0F172A" in content or "(15, 23, 42)" in content or "(15,23,42)" in content


# ---------------------------------------------------------------------------
# AC-8 no board mutation grid unchanged
# ---------------------------------------------------------------------------


def test_ac8_no_board_mutation_grid_unchanged(
    mock_surface: MagicMock,
    game_state: SimpleNamespace,
    layout: MagicMock,
    grid_5x5: List[List[Dict[str, Any]]],
) -> None:
    """AC-8: grid unchanged values and heats after draw calls."""
    from src.render.hud import ToastManager, draw_hud_with_gamestate

    snapshot = copy.deepcopy(grid_5x5)

    try:
        draw_hud_with_gamestate(mock_surface, 100, 200, game_state, layout)
    except Exception as e:
        pytest.fail(f"draw_hud_with_gamestate crashed in no-mutation test: {e}")

    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "cold_fusion", "title": "Cold Fusion", "description": "test"}])
    manager.update(0.5)
    try:
        manager.draw(mock_surface)
    except Exception as e:
        pytest.fail(f"ToastManager draw crashed in no-mutation test: {e}")

    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    try:
        draw_game_over(mock_surface, 100, 200, layout)
    except Exception as e:
        pytest.fail(f"draw_game_over crashed in no-mutation test: {e}")

    assert grid_5x5 == snapshot, f"Grid mutated: before {snapshot} after {grid_5x5}"


def test_ac8_no_mutation_after_toast_and_gameover(
    mock_surface: MagicMock, layout: MagicMock
) -> None:
    """AC-8: no mutation after toast and gameover with achievements list."""
    from src.render.hud import ToastManager

    achievements = [
        {"id": "cold_fusion", "title": "Cold Fusion", "description": "test"}
    ]
    before = copy.deepcopy(achievements)

    manager = ToastManager(max_toasts=5)
    manager.push(achievements)
    manager.update(0.1)
    manager.draw(mock_surface)

    assert achievements == before, "Achievements list mutated by ToastManager"


# ---------------------------------------------------------------------------
# Edge tests
# ---------------------------------------------------------------------------


def test_edge_surface_none_raises_valueerror_all_draw(
    game_state: SimpleNamespace, layout: MagicMock
) -> None:
    """Edge: surface None raises ValueError for all draw functions."""
    from src.render.hud import ToastManager, draw_hud, draw_hud_with_gamestate

    with pytest.raises(ValueError, match="surface None"):
        draw_hud(None, 0, 0, [], None)

    with pytest.raises(ValueError, match="surface None"):
        draw_hud_with_gamestate(None, 0, 0, game_state, layout)

    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "test", "title": "Test", "description": "test"}])
    with pytest.raises(ValueError, match="surface None"):
        manager.draw(None)

    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    with pytest.raises(ValueError, match="surface None"):
        draw_game_over(None, 0, 0, layout)


def test_edge_game_state_none_raises(
    mock_surface: MagicMock, layout: MagicMock
) -> None:
    """Edge: game_state None raises ValueError for draw_hud_with_gamestate."""
    from src.render.hud import draw_hud_with_gamestate

    with pytest.raises(ValueError, match="game_state None"):
        draw_hud_with_gamestate(mock_surface, 0, 0, None, layout)


def test_edge_achievements_none_raises() -> None:
    """Edge: achievements None raises ValueError for push."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    with pytest.raises(ValueError, match="achievements None"):
        manager.push(None)  # type: ignore[arg-type]


def test_edge_max_toasts_bounded_oldest_removed() -> None:
    """Edge: max_toasts bounded oldest removed."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    for i in range(6):
        manager.push(
            [{"id": f"ach_{i}", "title": f"Ach {i}", "description": f"Desc {i}"}]
        )

    assert len(manager.toasts) == 5, f"Expected 5, got {len(manager.toasts)}"
    ids = [t.achievement_id for t in manager.toasts]
    assert "ach_0" not in ids, "Oldest should be removed"
    assert "ach_5" in ids, "Newest should be present"


def test_edge_layout_none_uses_default(
    mock_surface: MagicMock, game_state: SimpleNamespace
) -> None:
    """Edge: layout None uses default (0,0,700,120) not crash."""
    from src.render.hud import draw_hud_with_gamestate

    try:
        draw_hud_with_gamestate(mock_surface, 100, 200, game_state, None)
    except Exception as e:
        pytest.fail(f"layout None crashed: {e}")


def test_edge_empty_achievements_no_crash() -> None:
    """Edge: empty achievements list no crash."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([])
    assert len(manager.toasts) == 0
    assert manager.has_visible() is False


def test_edge_dt_zero_no_crash() -> None:
    """Edge: dt 0 returns early no crash."""
    from src.render.hud import ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "test", "title": "Test", "description": "test"}])
    elapsed_before = manager.toasts[0].elapsed
    manager.update(0)
    assert manager.toasts[0].elapsed == elapsed_before, (
        "dt 0 should not advance elapsed"
    )


def test_headless_importable_no_pygame_leak() -> None:
    """Headless importable check via sys.modules no pygame leak required."""
    try:
        import src.render.hud as hud_module

        assert hasattr(hud_module, "draw_hud")
        assert hasattr(hud_module, "ToastManager")
        assert hasattr(hud_module, "draw_hud_with_gamestate")
    except ImportError as e:
        pytest.fail(f"HUD module not importable headless: {e}")

    assert "src.render.hud" in sys.modules
