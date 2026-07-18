"""
tests/test_hud_smoke.py — Smoke test for HUD rendering.

Optional smoke test headless skip if no DISPLAY, verifies init and draw one frame no crash.
Non-interactive run-once.

System: Phase 4 Sprint 1 Task 3 Wave2 Step 2 TDD red phase smoke.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest


def _has_display() -> bool:
    """Check if display available for real pygame surface."""
    if os.name == "nt":
        return True
    return os.environ.get("DISPLAY") is not None or os.environ.get("WAYLAND_DISPLAY") is not None


@pytest.mark.skipif(not _has_display(), reason="No DISPLAY, skipping real pygame surface smoke")
def test_hud_smoke_real_surface() -> None:
    """Smoke: init pygame, create 700x800 surface, draw_hud one frame no crash."""
    try:
        import pygame
    except ImportError:
        pytest.skip("pygame not installed")

    # Ensure pygame init does not crash
    try:
        pygame.init()
    except Exception:
        pytest.skip("pygame init failed headless")

    try:
        surface = pygame.Surface((700, 800))
        from src.render.hud import ToastManager, draw_hud

        # Draw empty HUD
        draw_hud(surface, 0, 0, [], None)

        # Draw with score
        draw_hud(surface, 1234, 5678, [], None)

        # Draw with achievements and toasts
        manager = ToastManager(max_toasts=5)
        manager.push([{"id": "cold_fusion", "title": "Cold Fusion", "description": "First"}])
        draw_hud(surface, 100, 200, [{"id": "cold_fusion"}], manager)

        # Update and draw again
        manager.update(0.016)
        manager.draw(surface)

        # Verify surface still valid
        assert surface.get_width() == 700
        assert surface.get_height() == 800

    finally:
        try:
            pygame.quit()
        except Exception:
            pass


def test_hud_smoke_mock_surface() -> None:
    """Smoke: mock surface init and draw one frame no crash headless always runnable."""
    from src.render.hud import ToastManager, draw_hud

    mock_surface = MagicMock()
    mock_surface.fill = MagicMock()
    mock_surface.blit = MagicMock()
    mock_surface.get_rect = MagicMock(return_value=MagicMock(center=(0, 0), width=700, height=800))
    mock_surface.get_width = MagicMock(return_value=700)
    mock_surface.get_height = MagicMock(return_value=800)

    # Init manager
    manager = ToastManager(max_toasts=5)
    assert manager.has_visible() is False

    # Push and draw
    manager.push([{"id": "cold_fusion", "title": "Cold Fusion", "description": "Smoke test"}])
    assert manager.has_visible() is True

    try:
        draw_hud(mock_surface, 100, 200, [], manager)
    except Exception as e:
        pytest.fail(f"Smoke mock surface draw_hud crashed: {e}")

    try:
        manager.update(0.016)
        manager.draw(mock_surface)
    except Exception as e:
        pytest.fail(f"Smoke mock surface manager draw crashed: {e}")

    # After large dt, should expire
    manager.update(3.0)
    assert manager.has_visible() is False


def test_hud_import_headless() -> None:
    """Smoke: hud.py importable headless without display init."""
    # This should not require DISPLAY
    try:
        import src.render.hud as hud_module

        assert hasattr(hud_module, "draw_hud")
        assert hasattr(hud_module, "Toast")
        assert hasattr(hud_module, "ToastManager")
        assert hasattr(hud_module, "draw_hud_with_gamestate")
        assert hasattr(hud_module, "REACTOR_BG")
        assert hasattr(hud_module, "HEAT_COOL")
    except ImportError as e:
        pytest.fail(f"HUD module not importable headless (red phase expected if not implemented): {e}")


def test_hud_constants_smoke() -> None:
    """Smoke: constants defined and match spec."""
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
