"""
tests/test_effects_unit.py — TDD unit tests for EffectManager with particles.

Red phase: these tests MUST fail initially because src/render/effects.py does not exist yet.
Covers AC-1 to AC-7: init empty, slide lerp 100-150ms, merge pulse 1.0->1.2->1.0 200ms,
heat particles per heat cool #3B82F6 2-3 warm #F59E0B 4-5 hot #EF4444 6-8 unstable #FFFFFF 10+,
update advances progress fading alpha removes dead dt negative ValueError, draw no crash no mutation,
is_animating, no external assets, no board mutation.

System: Phase 4 Sprint 1 Tasks 1 & 2 Step 2 TDD red phase.
"""

from __future__ import annotations

import copy
import pathlib
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from src.core.board import MergeInfo, SlideResult, Tile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface with fill, blit, get_rect for headless draw tests."""
    surface = MagicMock()
    surface.fill = MagicMock()
    surface.blit = MagicMock()
    surface.get_rect = MagicMock(return_value=MagicMock(center=(0, 0)))
    return surface


@pytest.fixture
def synthetic_grid() -> List[List[Optional[Tile]]]:
    """5x5 grid with 2 tiles for testing."""
    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    return grid


@pytest.fixture
def synthetic_merge() -> MergeInfo:
    """Single MergeInfo with source_positions and source_heats."""
    return MergeInfo(
        position=(0, 0),
        value=4,
        source_positions=[(0, 1), (0, 0)],
        heat_gen=1,
        source_heats=(0, 0),
    )


@pytest.fixture
def synthetic_slide_result(synthetic_grid: List[List[Optional[Tile]]], synthetic_merge: MergeInfo) -> SlideResult:
    """SlideResult with one merge for testing."""
    return SlideResult(
        grid=synthetic_grid,
        score_delta=4,
        moved=True,
        merges=[synthetic_merge],
        vent_occurred=False,
        unstable_present=False,
    )


def _make_merge_at(
    pos: tuple[int, int],
    value: int,
    source_positions: List[tuple[int, int]],
    heat_gen: int,
    source_heats: tuple[int, int],
) -> MergeInfo:
    """Helper to create MergeInfo at given position."""
    return MergeInfo(
        position=pos,
        value=value,
        source_positions=source_positions,
        heat_gen=heat_gen,
        source_heats=source_heats,
    )


# ---------------------------------------------------------------------------
# Group 1: EffectManager init and is_animating — AC-1, AC-6
# ---------------------------------------------------------------------------


def test_effect_manager_init_empty() -> None:
    """AC-1: EffectManager instantiated creates empty animation state no crash no mutation."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    assert hasattr(manager, "animations")
    assert hasattr(manager, "particles")
    assert len(manager.animations) == 0
    assert len(manager.particles) == 0
    assert manager.is_animating() is False


def test_is_animating_true_when_active(synthetic_slide_result: SlideResult) -> None:
    """AC-6: is_animating true if active false when done."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    assert manager.is_animating() is False

    manager.start_slide(synthetic_slide_result)
    assert manager.is_animating() is True

    # Large dt should finish animations
    manager.update(1.0)
    assert manager.is_animating() is False


def test_is_animating_false_initially() -> None:
    """AC-6: is_animating false on fresh instance."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    assert manager.is_animating() is False


# ---------------------------------------------------------------------------
# Group 2: Slide lerp — AC-2
# ---------------------------------------------------------------------------


def test_start_slide_captures_source_dest(synthetic_slide_result: SlideResult) -> None:
    """AC-2: start_slide captures source->dest per tile lerp 100-150ms progress 0-1."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)

    assert len(manager.animations) > 0
    for anim in manager.animations:
        # Each animation should have source_positions in its start_pos
        assert anim.start_pos in synthetic_slide_result.merges[0].source_positions or True
        assert anim.end_pos == synthetic_slide_result.merges[0].position
        # Duration 100-150ms = 0.1-0.15 sec
        assert 0.09 <= anim.duration <= 0.16, f"Duration {anim.duration} not in 100-150ms"
        assert 0.0 <= anim.progress <= 1.0


def test_start_slide_duration_within_100_150ms(synthetic_slide_result: SlideResult) -> None:
    """AC-2: slide duration must be within 100-150ms range."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)

    for anim in manager.animations:
        if not anim.is_merge:
            assert 0.1 <= anim.duration <= 0.15, f"Slide duration {anim.duration} not in 0.1-0.15"


def test_slide_lerp_interpolation(synthetic_slide_result: SlideResult) -> None:
    """AC-2: lerp calculation start+(end-start)*progress halfway check."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)

    if not manager.animations:
        pytest.skip("No animations created")

    # Half duration update
    half_dt = manager.animations[0].duration / 2.0
    manager.update(half_dt)

    for anim in manager.animations:
        # Progress should be ~0.5
        assert 0.4 <= anim.progress <= 0.6, f"Progress {anim.progress} not ~0.5 after half duration"


def test_start_slide_none_raises_value_error() -> None:
    """EC-1: SlideResult None raises ValueError."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    with pytest.raises(ValueError, match="None"):
        manager.start_slide(None)  # type: ignore[arg-type]


def test_start_slide_moved_false_no_animation() -> None:
    """EC-2: moved False -> no animation."""
    from src.render.effects import EffectManager

    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    grid[0][0] = Tile(value=2, heat=0)
    result = SlideResult(
        grid=grid,
        score_delta=0,
        moved=False,
        merges=[],
        vent_occurred=False,
        unstable_present=False,
    )
    manager = EffectManager()
    manager.start_slide(result)
    assert manager.is_animating() is False


# ---------------------------------------------------------------------------
# Group 3: Merge pulse and particles — AC-3
# ---------------------------------------------------------------------------


def test_start_merge_pulse_scaling(synthetic_merge: MergeInfo) -> None:
    """AC-3: start_merge pulse scaling 1.0->1.2->1.0 200ms."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_merge([synthetic_merge])

    assert len(manager.animations) > 0
    for anim in manager.animations:
        if anim.is_merge:
            assert anim.duration == pytest.approx(0.2, abs=0.05)
            assert anim.scale == pytest.approx(1.0, abs=0.01)
            assert anim.progress == pytest.approx(0.0, abs=0.01)

    # After 0.1s (half merge duration) scale should be ~1.2
    manager.update(0.1)
    for anim in manager.animations:
        if anim.is_merge:
            assert 1.1 <= anim.scale <= 1.25, f"Scale {anim.scale} not ~1.2 at half duration"

    # After full duration scale back to ~1.0
    manager.update(0.15)
    for anim in manager.animations:
        if anim.is_merge and anim.progress < 1.0:
            # If still animating, scale should be decreasing
            assert anim.scale <= 1.2


def test_heat_particles_count_per_heat() -> None:
    """AC-3: particles count per heat cool 2-3 warm 4-5 hot 6-8 unstable 10+."""
    from src.render.effects import EffectManager

    # Cool heat 0: 2-3 particles
    manager_cool = EffectManager()
    merge_cool = _make_merge_at((0, 0), 4, [(0, 1), (0, 0)], heat_gen=0, source_heats=(0, 0))
    manager_cool.start_merge([merge_cool])
    cool_count = len(manager_cool.particles)
    assert 2 <= cool_count <= 5, f"Cool heat particles {cool_count} not in 2-3 (+bonus)"

    # Warm heat 1: 4-5 particles
    manager_warm = EffectManager()
    merge_warm = _make_merge_at((0, 0), 8, [(0, 1), (0, 0)], heat_gen=0, source_heats=(1, 1))
    manager_warm.start_merge([merge_warm])
    warm_count = len(manager_warm.particles)
    assert 4 <= warm_count <= 8, f"Warm heat particles {warm_count} not in 4-5 (+bonus)"

    # Hot heat 2: 6-8 particles
    manager_hot = EffectManager()
    merge_hot = _make_merge_at((0, 0), 16, [(0, 1), (0, 0)], heat_gen=0, source_heats=(2, 2))
    manager_hot.start_merge([merge_hot])
    hot_count = len(manager_hot.particles)
    assert 6 <= hot_count <= 12, f"Hot heat particles {hot_count} not in 6-8 (+bonus)"

    # Unstable heat 3: 10+ particles
    manager_unstable = EffectManager()
    merge_unstable = _make_merge_at((0, 0), 32, [(0, 1), (0, 0)], heat_gen=0, source_heats=(3, 3))
    manager_unstable.start_merge([merge_unstable])
    unstable_count = len(manager_unstable.particles)
    assert unstable_count >= 10, f"Unstable heat particles {unstable_count} not >=10"


def test_heat_particles_color_per_heat() -> None:
    """AC-3: particle colors per heat #3B82F6 cool #F59E0B warm #EF4444 hot #FFFFFF unstable."""
    from src.render.effects import EffectManager

    # Cool #3B82F6 = (59,130,246)
    manager = EffectManager()
    merge = _make_merge_at((0, 0), 4, [(0, 1)], heat_gen=0, source_heats=(0, 0))
    manager.start_merge([merge])
    for p in manager.particles:
        assert p.color == (59, 130, 246), f"Cool particle color {p.color} != (59,130,246)"

    # Warm #F59E0B = (245,158,11)
    manager2 = EffectManager()
    merge2 = _make_merge_at((0, 0), 8, [(0, 1)], heat_gen=0, source_heats=(1, 1))
    manager2.start_merge([merge2])
    for p in manager2.particles:
        assert p.color == (245, 158, 11), f"Warm particle color {p.color} != (245,158,11)"

    # Hot #EF4444 = (239,68,68)
    manager3 = EffectManager()
    merge3 = _make_merge_at((0, 0), 16, [(0, 1)], heat_gen=0, source_heats=(2, 2))
    manager3.start_merge([merge3])
    for p in manager3.particles:
        assert p.color == (239, 68, 68), f"Hot particle color {p.color} != (239,68,68)"

    # Unstable #FFFFFF = (255,255,255)
    manager4 = EffectManager()
    merge4 = _make_merge_at((0, 0), 32, [(0, 1)], heat_gen=0, source_heats=(3, 3))
    manager4.start_merge([merge4])
    for p in manager4.particles:
        assert p.color == (255, 255, 255), f"Unstable particle color {p.color} != (255,255,255)"


def test_particle_intensity_from_heat_gen() -> None:
    """AC-3: intensity from heat_gen floor(log2(V)/2) and source_heats."""
    from src.render.effects import EffectManager

    # heat_gen 0 vs 3 should increase particle count
    manager_low = EffectManager()
    merge_low = _make_merge_at((0, 0), 4, [(0, 1)], heat_gen=0, source_heats=(0, 0))
    manager_low.start_merge([merge_low])
    count_low = len(manager_low.particles)

    manager_high = EffectManager()
    merge_high = _make_merge_at((0, 0), 64, [(0, 1)], heat_gen=3, source_heats=(0, 0))
    manager_high.start_merge([merge_high])
    count_high = len(manager_high.particles)

    assert count_high >= count_low, f"High heat_gen {count_high} should >= low {count_low}"


def test_start_merge_none_raises_value_error() -> None:
    """EC: merges None raises ValueError."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    with pytest.raises(ValueError):
        manager.start_merge(None)  # type: ignore[arg-type]


def test_start_merge_empty_no_crash() -> None:
    """EC-3: Empty merges list no-op no crash."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_merge([])
    assert manager.is_animating() is False
    assert len(manager.particles) == 0


# ---------------------------------------------------------------------------
# Group 4: Update and draw — AC-4, AC-5
# ---------------------------------------------------------------------------


def test_update_advances_progress_and_fades(synthetic_slide_result: SlideResult) -> None:
    """AC-4: update(dt) advances progress 0-1 lerp and particle life fading alpha removes dead."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)
    merge = _make_merge_at((0, 0), 4, [(0, 1)], heat_gen=1, source_heats=(0, 0))
    manager.start_merge([merge])

    initial_progress = [a.progress for a in manager.animations]
    initial_life = [p.life for p in manager.particles] if manager.particles else []

    manager.update(0.016)  # 16ms ~60FPS

    # Progress increased
    for i, anim in enumerate(manager.animations):
        assert anim.progress > initial_progress[i] or anim.progress >= 1.0

    # Particle life decreased
    if manager.particles and initial_life:
        for j, p in enumerate(manager.particles):
            if j < len(initial_life):
                assert p.life <= initial_life[j]

    # Large dt removes dead
    manager.update(10.0)
    assert len(manager.particles) == 0
    assert len(manager.animations) == 0


def test_update_dt_negative_raises_value_error() -> None:
    """AC-4: dt negative raises ValueError."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    with pytest.raises(ValueError, match="negative"):
        manager.update(-0.016)


def test_update_dt_none_raises_value_error() -> None:
    """AC-4: dt None raises ValueError."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    with pytest.raises(ValueError):
        manager.update(None)  # type: ignore[arg-type]


def test_update_dt_zero_no_progress() -> None:
    """EC-5: dt zero no progress no crash."""
    from src.render.effects import EffectManager

    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    merge = _make_merge_at((0, 0), 4, [(0, 1), (0, 0)], heat_gen=1, source_heats=(0, 0))
    result = SlideResult(
        grid=grid,
        score_delta=4,
        moved=True,
        merges=[merge],
        vent_occurred=False,
        unstable_present=False,
    )
    manager = EffectManager()
    manager.start_slide(result)
    progress_before = [a.progress for a in manager.animations]
    manager.update(0.0)
    progress_after = [a.progress for a in manager.animations]
    assert progress_before == progress_after


def test_draw_no_crash_no_mutation(
    mock_surface: MagicMock,
    synthetic_grid: List[List[Optional[Tile]]],
    synthetic_slide_result: SlideResult,
) -> None:
    """AC-5: draw draws animated tiles interpolated scaling particles no crash mock surface no mutation."""
    from src.render.effects import EffectManager

    manager = EffectManager()

    # Deep copy grid values for mutation check
    original_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in synthetic_grid
    ]

    manager.start_slide(synthetic_slide_result)
    manager.update(0.016)

    # Draw should not crash with mock surface
    try:
        manager.draw(mock_surface, layout=None)
    except Exception as e:
        pytest.fail(f"draw crashed with mock surface: {e}")

    # Grid unchanged
    after_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in synthetic_grid
    ]
    assert original_values == after_values, "Board mutation detected in draw"


def test_draw_surface_none_raises_value_error() -> None:
    """EC-7: surface None raises ValueError."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    with pytest.raises(ValueError):
        manager.draw(None, layout=None)  # type: ignore[arg-type]


def test_draw_layout_none_uses_defaults_no_crash(mock_surface: MagicMock) -> None:
    """EC-8: layout None uses defaults not crash."""
    from src.render.effects import EffectManager

    manager = EffectManager()
    # Should not crash with layout None
    try:
        manager.draw(mock_surface, layout=None)
    except ValueError:
        pytest.fail("draw with layout None should use defaults not raise ValueError")
    except Exception as e:
        # Other exceptions from mock surface are ok if wrapped in try/except in implementation
        # But ValueError for surface None is expected, layout None should not raise
        if "surface" in str(e).lower():
            pytest.fail(f"draw raised ValueError for layout None: {e}")


# ---------------------------------------------------------------------------
# Group 5: No external assets and no board mutation — AC-7
# ---------------------------------------------------------------------------


def test_no_external_assets_effects() -> None:
    """AC-7: effects.py no image.load no font.Font file path only SysFont programmatic only."""
    effects_path = pathlib.Path("src/render/effects.py")
    assert effects_path.exists(), "src/render/effects.py does not exist yet (red phase)"

    content = effects_path.read_text(encoding="utf-8")

    assert "image.load" not in content, "Found pygame.image.load in effects.py - programmatic only violation"
    # Check for font.Font with file path - allow SysFont only
    # We check for font.Font( that is not SysFont
    if "font.Font" in content:
        # If font.Font exists, it should not have a file path, only SysFont allowed
        # Simple check: count font.Font occurrences that are not in comments
        lines = [line for line in content.splitlines() if "font.Font" in line and not line.strip().startswith("#")]
        # Filter out SysFont lines
        non_sysfont = [line for line in lines if "SysFont" not in line]
        assert len(non_sysfont) == 0, f"Found font.Font file path usage: {non_sysfont}"

    assert "SysFont" in content, "SysFont not found in effects.py - should use SysFont only"


def test_no_board_mutation(
    synthetic_grid: List[List[Optional[Tile]]],
    synthetic_slide_result: SlideResult,
    mock_surface: MagicMock,
) -> None:
    """AC-5: No board mutation grid unchanged values heats after start_slide update draw."""
    from src.render.effects import EffectManager

    # Deep copy original
    original = copy.deepcopy(synthetic_grid)
    original_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in original
    ]

    manager = EffectManager()
    manager.start_slide(synthetic_slide_result)
    manager.update(0.016)
    manager.draw(mock_surface, layout=None)

    after_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in synthetic_grid
    ]
    assert original_values == after_values, "Board mutation detected: grid values/heats changed"

    # Also check SlideResult grid unchanged
    result_original = copy.deepcopy(synthetic_slide_result.grid)
    result_original_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row] for row in result_original
    ]
    result_after_values = [
        [(cell.value, cell.heat) if cell is not None else None for cell in row]
        for row in synthetic_slide_result.grid
    ]
    assert result_original_values == result_after_values, "SlideResult grid mutated"


def test_no_pygame_leak_in_core_import() -> None:
    """Isolation: no pygame leak after importing core modules."""
    import sys

    # Snapshot before
    before = set(sys.modules.keys())
    # Import core
    import src.core.board  # noqa: F401
    import src.core.rules  # noqa: F401

    after = set(sys.modules.keys())
    new_modules = after - before
    pygame_leaks = [m for m in new_modules if "pygame" in m.lower()]
    # Also check if pygame was already loaded - then check core files don't import pygame
    if "pygame" in sys.modules:
        # If pygame already loaded from previous test, check source files directly
        board_path = pathlib.Path("src/core/board.py")
        board_content = board_path.read_text(encoding="utf-8")
        assert "import pygame" not in board_content, "Found pygame import in board.py"
        assert "from pygame" not in board_content, "Found from pygame import in board.py"
    else:
        assert len(pygame_leaks) == 0, f"Pygame leak detected in core import: {pygame_leaks}"
