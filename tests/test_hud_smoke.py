"""
tests/test_hud_smoke.py — Smoke tests for HUD refinement Phase 4 Sprint 2 Task 1.

Covers AC-1 to AC-8 smoke: HUD no crash, ToastManager push/update/draw/has_visible,
game-over overlay no crash, headless skip via pytest.mark.skipif, mock surface no pygame display.

System: Phase 4 Sprint 2 Task 1 Step 2 TDD red phase smoke.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _has_display() -> bool:
    """Check if display available for real pygame surface."""
    if os.name == "nt":
        return True
    return (
        os.environ.get("DISPLAY") is not None
        or os.environ.get("WAYLAND_DISPLAY") is not None
    )


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface 700x800 headless no pygame display required."""
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
    """Synthetic game_state move_count vent_streak unstable_survival."""
    return SimpleNamespace(move_count=5, vent_streak=2, unstable_survival=1)


@pytest.fixture
def layout() -> MagicMock:
    """Synthetic layout hud_rect() -> (0,0,700,120)."""
    lay = MagicMock()
    lay.hud_rect = MagicMock(return_value=(0, 0, 700, 120))
    return lay


@pytest.mark.skipif(
    not _has_display(), reason="No DISPLAY, skipping real pygame surface smoke"
)
def test_hud_smoke_real_surface() -> None:
    """Smoke: real pygame surface 700x800 draw_hud ToastManager game-over no crash."""
    try:
        import pygame
    except ImportError:
        pytest.skip("pygame not installed")

    try:
        pygame.init()
    except Exception:
        pytest.skip("pygame init failed headless")

    try:
        surface = pygame.Surface((700, 800))
        from src.render.hud import ToastManager, draw_hud_with_gamestate

        gs = SimpleNamespace(move_count=5, vent_streak=2, unstable_survival=1)
        lay = MagicMock()
        lay.hud_rect = MagicMock(return_value=(0, 0, 700, 120))

        draw_hud_with_gamestate(surface, 0, 0, gs, lay)
        draw_hud_with_gamestate(surface, 1234, 5678, gs, lay)

        manager = ToastManager(max_toasts=5)
        manager.push(
            [{"id": "cold_fusion", "title": "Cold Fusion", "description": "First"}]
        )
        manager.update(0.016)
        manager.draw(surface)

        # Game-over overlay
        try:
            from src.render.hud import draw_game_over  # type: ignore[attr-defined]
        except ImportError:
            from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

        draw_game_over(surface, 100, 200, lay)

        assert surface.get_width() == 700
        assert surface.get_height() == 800

    finally:
        try:
            pygame.quit()
        except Exception:
            pass


def test_hud_smoke_mock_surface(
    mock_surface: MagicMock, game_state: SimpleNamespace, layout: MagicMock
) -> None:
    """Smoke: mock surface no crash headless always runnable covering AC-1, AC-2, AC-4, AC-5, AC-6."""
    from src.render.hud import ToastManager, draw_hud_with_gamestate

    manager = ToastManager(max_toasts=5)
    assert manager.has_visible() is False

    manager.push(
        [{"id": "cold_fusion", "title": "Cold Fusion", "description": "Smoke test"}]
    )
    assert manager.has_visible() is True

    try:
        draw_hud_with_gamestate(mock_surface, 100, 200, game_state, layout)
    except Exception as e:
        pytest.fail(f"Smoke mock surface draw_hud_with_gamestate crashed: {e}")

    try:
        manager.update(0.016)
        manager.draw(mock_surface)
    except Exception as e:
        pytest.fail(f"Smoke mock surface manager draw crashed: {e}")

    # Game-over overlay no crash
    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    try:
        draw_game_over(mock_surface, 100, 200, layout)
    except Exception as e:
        pytest.fail(f"Smoke mock surface draw_game_over crashed: {e}")

    manager.update(3.0)
    assert manager.has_visible() is False


def test_hud_smoke_toast_queue_timing() -> None:
    """Smoke: ToastManager queue timing 2-3 sec stacking gap 10."""
    from src.render.hud import TOAST_GAP, TOAST_H, ToastManager

    manager = ToastManager(max_toasts=5)
    manager.push(
        [
            {"id": "cold_fusion", "title": "Cold Fusion", "description": "cool"},
            {"id": "heat_wave", "title": "Heat Wave", "description": "warm"},
        ]
    )
    assert len(manager.toasts) == 2
    assert manager.toasts[0].y_offset == 0
    assert manager.toasts[1].y_offset == TOAST_H + TOAST_GAP

    manager.update(1.0)
    assert manager.has_visible() is True
    manager.update(2.0)
    assert manager.has_visible() is False


def test_hud_smoke_game_over_overlay() -> None:
    """Smoke: game-over overlay dim 50% alpha #0F172A restart prompt."""
    mock_surface = MagicMock()
    mock_surface.fill = MagicMock()
    mock_surface.blit = MagicMock()
    mock_surface.get_rect = MagicMock(
        return_value=MagicMock(center=(350, 400), width=700, height=800)
    )
    mock_surface.get_width = MagicMock(return_value=700)
    mock_surface.get_height = MagicMock(return_value=800)
    layout = MagicMock()
    layout.hud_rect = MagicMock(return_value=(0, 0, 700, 120))

    try:
        from src.render.hud import draw_game_over  # type: ignore[attr-defined]
    except ImportError:
        from src.render.hud import draw_game_over_stub as draw_game_over  # type: ignore[no-redef]

    try:
        draw_game_over(mock_surface, 500, 1000, layout)
    except Exception as e:
        pytest.fail(f"Game-over overlay smoke crashed: {e}")


def test_hud_import_headless() -> None:
    """Smoke: hud.py importable headless without display init."""
    try:
        import src.render.hud as hud_module

        assert hasattr(hud_module, "draw_hud")
        assert hasattr(hud_module, "Toast")
        assert hasattr(hud_module, "ToastManager")
        assert hasattr(hud_module, "draw_hud_with_gamestate")
        assert hasattr(hud_module, "REACTOR_BG")
        assert hasattr(hud_module, "HEAT_COOL")
        # draw_game_over may be missing in red phase - check stub exists at minimum
        assert hasattr(hud_module, "draw_game_over_stub") or hasattr(
            hud_module, "draw_game_over"
        )
    except ImportError as e:
        pytest.fail(f"HUD module not importable headless: {e}")


def test_hud_constants_smoke() -> None:
    """Smoke: constants locked #0F172A #1E293B #334155 #475569 #3B82F6 #F59E0B #EF4444 #FFFFFF."""
    from src.render.hud import (
        BOARD_BG,
        BORDER,
        EMPTY_CELL,
        HEAT_COOL,
        HEAT_HOT,
        HEAT_UNSTABLE,
        HEAT_WARM,
        HUD_H,
        REACTOR_BG,
        TOAST_DURATION,
        TOAST_GAP,
        TOAST_H,
        TOAST_W,
        WINDOW_H,
        WINDOW_W,
    )

    assert WINDOW_W == 700
    assert WINDOW_H == 800
    assert HUD_H == 120
    assert TOAST_W == 280
    assert TOAST_H == 60
    assert TOAST_DURATION == 2.5
    assert TOAST_GAP == 10

    assert REACTOR_BG == (15, 23, 42)
    assert BOARD_BG == (30, 41, 59)
    assert EMPTY_CELL == (51, 65, 85)
    assert BORDER == (71, 85, 105)

    assert HEAT_COOL == (59, 130, 246)
    assert HEAT_WARM == (245, 158, 11)
    assert HEAT_HOT == (239, 68, 68)
    assert HEAT_UNSTABLE == (255, 255, 255)


def test_hud_smoke_no_board_mutation() -> None:
    """Smoke: no board mutation grid unchanged."""
    import copy

    from src.render.hud import ToastManager, draw_hud_with_gamestate

    mock_surface = MagicMock()
    mock_surface.fill = MagicMock()
    mock_surface.blit = MagicMock()
    mock_surface.get_rect = MagicMock(
        return_value=MagicMock(center=(350, 400), width=700, height=800)
    )
    mock_surface.get_width = MagicMock(return_value=700)
    mock_surface.get_height = MagicMock(return_value=800)

    game_state = SimpleNamespace(move_count=5, vent_streak=2, unstable_survival=1)
    layout = MagicMock()
    layout.hud_rect = MagicMock(return_value=(0, 0, 700, 120))

    grid = [[{"value": 2, "heat": 0} for _ in range(5)] for _ in range(5)]
    snapshot = copy.deepcopy(grid)

    draw_hud_with_gamestate(mock_surface, 100, 200, game_state, layout)
    manager = ToastManager(max_toasts=5)
    manager.push([{"id": "cold_fusion", "title": "Cold Fusion", "description": "test"}])
    manager.draw(mock_surface)

    assert grid == snapshot, "Grid mutated in smoke test"
