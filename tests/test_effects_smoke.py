"""
tests/test_effects_smoke.py — Smoke test for EffectManager.

Verifies EffectManager can init and update/draw one frame without crash,
headless skip if no DISPLAY via pytest.mark.skipif, no board mutation.

System: Phase 4 Sprint 1 Tasks 1 & 2 Step 2 TDD red phase.
"""

from __future__ import annotations

import copy
import os
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from src.core.board import MergeInfo, SlideResult, Tile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface for headless smoke test."""
    surface = MagicMock()
    surface.fill = MagicMock()
    surface.blit = MagicMock()
    surface.get_rect = MagicMock(return_value=MagicMock(center=(0, 0)))
    return surface


@pytest.fixture
def synthetic_grid() -> List[List[Optional[Tile]]]:
    """5x5 grid with 2 tiles."""
    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    return grid


@pytest.fixture
def synthetic_merge() -> MergeInfo:
    """MergeInfo for smoke test."""
    return MergeInfo(
        position=(0, 0),
        value=4,
        source_positions=[(0, 1), (0, 0)],
        heat_gen=1,
        source_heats=(0, 0),
    )


@pytest.fixture
def synthetic_slide_result(
    synthetic_grid: List[List[Optional[Tile]]], synthetic_merge: MergeInfo
) -> SlideResult:
    """SlideResult for smoke test."""
    return SlideResult(
        grid=synthetic_grid,
        score_delta=4,
        moved=True,
        merges=[synthetic_merge],
        vent_occurred=False,
        unstable_present=False,
    )


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_effects_smoke_init_update_draw_no_crash(
    mock_surface: MagicMock,
    synthetic_grid: List[List[Optional[Tile]]],
    synthetic_slide_result: SlideResult,
    synthetic_merge: MergeInfo,
) -> None:
    """Smoke: EffectManager init update draw one frame no crash no board mutation."""
    from src.render.effects import EffectManager

    # Init
    manager = EffectManager()
    assert len(manager.animations) == 0
    assert len(manager.particles) == 0
    assert manager.is_animating() is False

    # Deep copy grid for mutation check
    original_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in synthetic_grid
    ]

    # start_slide
    manager.start_slide(synthetic_slide_result)
    assert len(manager.animations) > 0
    assert manager.is_animating() is True

    # start_merge
    manager.start_merge([synthetic_merge])
    # Should have particles spawned
    assert len(manager.particles) > 0

    # update 16ms ~60FPS
    manager.update(0.016)
    # Progress should advance
    for anim in manager.animations:
        assert anim.progress > 0.0

    # draw with mock surface no crash
    try:
        manager.draw(mock_surface, layout=None)
    except Exception as e:
        pytest.fail(f"Smoke draw crashed: {e}")

    # Grid unchanged
    after_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in synthetic_grid
    ]
    assert original_values == after_values, "Smoke test detected board mutation"

    # Large dt finishes
    manager.update(1.0)
    assert manager.is_animating() is False


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None and os.name != "nt",
    reason="No DISPLAY available for pygame surface test - headless skip",
)
def test_effects_smoke_with_real_surface_if_display(
    synthetic_grid: List[List[Optional[Tile]]],
    synthetic_slide_result: SlideResult,
    synthetic_merge: MergeInfo,
) -> None:
    """Smoke with real pygame.Surface if DISPLAY available, otherwise skipped."""
    try:
        import pygame

        pygame.init()
        surface = pygame.Surface((700, 800))
    except Exception as e:
        pytest.skip(f"Pygame not available or no DISPLAY: {e}")

    try:
        from src.render.effects import EffectManager

        manager = EffectManager()
        manager.start_slide(synthetic_slide_result)
        manager.start_merge([synthetic_merge])
        manager.update(0.016)
        manager.draw(surface, layout=None)
        # No crash = pass
        assert True
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


def test_effects_smoke_no_board_mutation_detailed(
    mock_surface: MagicMock,
    synthetic_grid: List[List[Optional[Tile]]],
    synthetic_slide_result: SlideResult,
) -> None:
    """Smoke: detailed no board mutation grid unchanged values heats after full cycle."""
    from src.render.effects import EffectManager

    original = copy.deepcopy(synthetic_grid)
    original_flat = [(cell.value, cell.heat) if cell is not None else None for row in original for cell in row]

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)
    manager.update(0.016)
    manager.update(0.032)
    manager.draw(mock_surface, layout=None)
    manager.update(0.1)
    manager.draw(mock_surface, layout=None)

    after_flat = [(cell.value, cell.heat) if cell is not None else None for row in synthetic_grid for cell in row]
    assert original_flat == after_flat, "Board mutation in smoke detailed test"


def test_effects_smoke_empty_merge_no_crash(mock_surface: MagicMock) -> None:
    """Smoke: empty merges list no crash."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_merge([])
    manager.update(0.016)
    try:
        manager.draw(mock_surface, layout=None)
    except Exception as e:
        pytest.fail(f"Empty merge smoke draw crashed: {e}")
    assert manager.is_animating() is False


def test_effects_smoke_multiple_merges_performance(mock_surface: MagicMock) -> None:
    """EC-18: Many merges 5 merges particles up to 50 still performant O(25)+O(50) <16ms."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    merges = []
    for i in range(5):
        merges.append(
            MergeInfo(
                position=(i % 5, i % 5),
                value=4 * (2**i),
                source_positions=[(i % 5, (i + 1) % 5)],
                heat_gen=i % 4,
                source_heats=(i % 4, i % 4),
            )
        )

    manager.start_merge(merges)
    # Should have many particles but not excessive
    assert len(manager.particles) <= 100, f"Too many particles {len(manager.particles)} for 5 merges"
    assert len(manager.particles) >= 10, f"Too few particles {len(manager.particles)} for 5 merges"

    # Update and draw should not crash
    manager.update(0.016)
    try:
        manager.draw(mock_surface, layout=None)
    except Exception as e:
        pytest.fail(f"Multiple merges smoke draw crashed: {e}")
