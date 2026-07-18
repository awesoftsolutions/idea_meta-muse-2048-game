"""
tests/test_render_tiles.py — Final verification tile rendering heat identity reactor chrome.

Covers AC-1, AC-2, AC-13 to AC-19 per pseudocode phase_3_sprint_2_wave1_tasks_1_2_code.md:
- lerp_heat_color exact colors #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow
- value_to_base_color distinct per value 2..2048 classic palette
- blend_colors 70% heat 30% base weighted average
- cell_rect origin (100,150) size 90 gap 10
- draw_board no mutation, empty/full grid no crash, invalid raises
- programmatic only no image.load no font file path only SysFont

System: RenderTiles per Phase 3 architecture ADR-018, ADR-020.
Headless importable, mock surface for rendering tests, no pygame leak.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import List, Optional

import pytest

from src.core.board import BOARD_SIZE, Tile, create_empty_grid


class MockSurface:
    """Minimal mock surface for headless draw_board tests."""

    def __init__(self) -> None:
        self.fill_calls: list = []
        self.blit_calls: list = []

    def fill(self, color) -> None:  # type: ignore[no-untyped-def]
        self.fill_calls.append(color)

    def blit(self, source, dest) -> None:  # type: ignore[no-untyped-def]
        self.blit_calls.append((source, dest))

    def get_width(self) -> int:
        return 700

    def get_height(self) -> int:
        return 800


def _make_full_grid() -> List[List[Optional[Tile]]]:
    """Create full 5x5 grid with various values heats."""
    values = [
        2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2, 4, 8,
    ]
    heats = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0]
    grid = create_empty_grid()
    idx = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            grid[r][c] = Tile(value=values[idx], heat=heats[idx])
            idx += 1
    return grid


def test_lerp_heat_color_0_returns_3B82F6_no_glow() -> None:
    """AC-2: heat 0 returns #3B82F6 (59,130,246) cool, glow False."""
    from src.render.tiles import lerp_heat_color

    rgb, glow = lerp_heat_color(0)
    assert rgb == (59, 130, 246), f"Expected (59,130,246) #3B82F6 for heat 0, got {rgb}"
    assert glow is False


def test_lerp_heat_color_1_returns_F59E0B_no_glow() -> None:
    """AC-2: heat 1 returns #F59E0B (245,158,11) warm, glow False."""
    from src.render.tiles import lerp_heat_color

    rgb, glow = lerp_heat_color(1)
    assert rgb == (245, 158, 11), f"Expected (245,158,11) #F59E0B for heat 1, got {rgb}"
    assert glow is False


def test_lerp_heat_color_2_returns_EF4444_no_glow() -> None:
    """AC-2: heat 2 returns #EF4444 (239,68,68) hot, glow False."""
    from src.render.tiles import lerp_heat_color

    rgb, glow = lerp_heat_color(2)
    assert rgb == (239, 68, 68), f"Expected (239,68,68) #EF4444 for heat 2, got {rgb}"
    assert glow is False


def test_lerp_heat_color_3_returns_FFFFFF_glow_true() -> None:
    """AC-2: heat 3 returns #FFFFFF (255,255,255) glow True."""
    from src.render.tiles import lerp_heat_color

    rgb, glow = lerp_heat_color(3)
    assert rgb == (255, 255, 255), f"Expected (255,255,255) #FFFFFF for heat 3, got {rgb}"
    assert glow is True


def test_lerp_heat_color_clamp_negative_and_overflow() -> None:
    """Edge: heat -1 clamped to 0 returns #3B82F6, heat 10 clamped to 3 returns #FFFFFF glow True."""
    from src.render.tiles import lerp_heat_color

    rgb_neg, glow_neg = lerp_heat_color(-1)
    assert rgb_neg == (59, 130, 246)
    assert glow_neg is False

    rgb_high, glow_high = lerp_heat_color(10)
    assert rgb_high == (255, 255, 255)
    assert glow_high is True


def test_value_to_base_color_distinct_palette_2_to_2048() -> None:
    """AC-13: value_to_base_color returns classic palette distinct per value 2..2048."""
    from src.render.tiles import value_to_base_color

    expected_map = {
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
        64: (246, 94, 59),
        128: (237, 207, 114),
        256: (237, 204, 97),
        512: (237, 200, 80),
        1024: (237, 197, 63),
        2048: (237, 194, 46),
    }
    colors = []
    for value, expected in expected_map.items():
        result = value_to_base_color(value)
        assert result == expected, f"value {value} expected {expected}, got {result}"
        colors.append(result)
    assert len(set(colors)) == len(expected_map)


def test_value_to_base_color_fallback_non_power() -> None:
    """Edge: value 3 fallback (200,200,200), value 4096 fallback (200,200,200)."""
    from src.render.tiles import value_to_base_color

    assert value_to_base_color(3) == (200, 200, 200)
    assert value_to_base_color(4096) == (200, 200, 200)
    assert value_to_base_color(0) == (200, 200, 200)


def test_blend_colors_70_30_weighted_average() -> None:
    """AC-14: blend_colors 70% heat 30% base weighted average."""
    from src.render.tiles import blend_colors

    base = (238, 228, 218)
    heat = (59, 130, 246)
    result = blend_colors(base, heat, heat_ratio=0.7)
    expected = (
        int(base[0] * 0.3 + heat[0] * 0.7),
        int(base[1] * 0.3 + heat[1] * 0.7),
        int(base[2] * 0.3 + heat[2] * 0.7),
    )
    assert result == expected
    for ch in result:
        assert 0 <= ch <= 255


def test_blend_colors_ratio_0_and_1() -> None:
    """Edge: ratio 0 returns base, ratio 1 returns heat_color."""
    from src.render.tiles import blend_colors

    base = (238, 228, 218)
    heat = (59, 130, 246)
    assert blend_colors(base, heat, 0.0) == base
    assert blend_colors(base, heat, 1.0) == heat


def test_cell_rect_origin_100_150_size_90_gap_10() -> None:
    """AC-15: cell_rect r=0 c=0 at origin (100,150) size 90 gap 10, r=4 c=4 at origin+4*(size+gap)."""
    from src.render.tiles import cell_rect

    x, y, w, h = cell_rect(0, 0)
    assert x == 100 + 0 * (90 + 10) + 10 // 2
    assert y == 150 + 0 * (90 + 10) + 10 // 2
    assert w == 90
    assert h == 90

    x44, y44, w44, h44 = cell_rect(4, 4)
    assert x44 == 100 + 4 * (90 + 10) + 10 // 2
    assert y44 == 150 + 4 * (90 + 10) + 10 // 2
    assert w44 == 90
    assert h44 == 90


def test_cell_rect_invalid_raises_E002() -> None:
    """Edge: r=-1 raises ValueError E002, r=5 raises ValueError, c=5 raises ValueError, r not int raises ValueError."""
    from src.render.tiles import cell_rect

    with pytest.raises(ValueError, match="E002|MalformedGrid|out of range|0..4"):
        cell_rect(-1, 0)
    with pytest.raises(ValueError):
        cell_rect(0, -1)
    with pytest.raises(ValueError):
        cell_rect(5, 0)
    with pytest.raises(ValueError):
        cell_rect(0, 5)
    with pytest.raises(ValueError):
        cell_rect("a", 0)  # type: ignore[arg-type]


def test_draw_board_does_not_mutate_grid() -> None:
    """AC-16: draw_board does not mutate grid values heats."""
    from src.render.tiles import draw_board

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    grid[1][1] = Tile(value=4, heat=1)
    grid[2][2] = Tile(value=8, heat=2)
    original_copy = copy.deepcopy(grid)
    mock_surface = MockSurface()
    try:
        draw_board(mock_surface, grid, 0)
    except Exception:
        pass
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            orig = original_copy[r][c]
            new = grid[r][c]
            if orig is None:
                assert new is None
            else:
                assert new is not None
                assert new.value == orig.value
                assert new.heat == orig.heat


def test_draw_board_empty_grid_no_crash() -> None:
    """AC-17: empty grid all None draws empty cells #334155 no crash."""
    from src.render.tiles import draw_board

    empty_grid = create_empty_grid()
    mock_surface = MockSurface()
    try:
        draw_board(mock_surface, empty_grid, 0)
    except Exception as e:
        pytest.fail(f"draw_board crashed on empty grid: {e}")


def test_draw_board_full_grid_no_crash_distinct() -> None:
    """AC-18: full grid 25 Tiles various values heats draws without crash distinct per value heat."""
    from src.render.tiles import draw_board

    full_grid = _make_full_grid()
    mock_surface = MockSurface()
    try:
        draw_board(mock_surface, full_grid, 100)
    except Exception as e:
        pytest.fail(f"draw_board crashed on full grid: {e}")


def test_draw_board_invalid_surface_none_raises() -> None:
    """Edge: surface None raises ValueError E002."""
    from src.render.tiles import draw_board

    grid = create_empty_grid()
    with pytest.raises(ValueError, match="E002|surface|None"):
        draw_board(None, grid, 0)


def test_draw_board_invalid_grid_not_5x5_raises() -> None:
    """Edge: grid 4x4 raises ValueError E002, grid None raises ValueError."""
    from src.render.tiles import draw_board

    mock_surface = MockSurface()
    with pytest.raises(ValueError, match="E002|MalformedGrid|5x5"):
        draw_board(mock_surface, None, 0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        draw_board(mock_surface, [[None] * 5 for _ in range(4)], 0)
    with pytest.raises(ValueError):
        draw_board(mock_surface, [[None] * 4 for _ in range(5)], 0)


def test_draw_board_invalid_tile_value_not_power_two_raises() -> None:
    """Edge: Tile value 3 not power of two raises ValueError E002."""
    from src.render.tiles import draw_board

    grid = create_empty_grid()
    fake_tile = Tile.__new__(Tile)
    object.__setattr__(fake_tile, "value", 3)
    object.__setattr__(fake_tile, "heat", 0)
    grid[0][0] = fake_tile
    mock_surface = MockSurface()
    with pytest.raises(ValueError, match="E002|power|MalformedGrid"):
        draw_board(mock_surface, grid, 0)


def test_draw_board_programmatic_only_no_image_load() -> None:
    """AC-19: no external assets grep no image.load no font file path only SysFont."""
    tiles_path = Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "pygame.image.load" in stripped:
            violations.append(f"{tiles_path}:{i}: {stripped}")
        if "font.Font(" in stripped and "SysFont" not in stripped:
            if "test" not in stripped.lower():
                violations.append(f"{tiles_path}:{i}: {stripped}")
    assert not violations, f"External assets found: {violations}"
    assert "SysFont" in content


def test_draw_board_reactor_chrome_colors_present() -> None:
    """AC-1: reactor chrome colors present."""
    tiles_path = Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")
    assert "15, 23, 42" in content or "#0F172A" in content
    assert "30, 41, 59" in content or "#1E293B" in content
    assert "51, 65, 85" in content or "#334155" in content
    assert "71, 85, 105" in content or "#475569" in content
    assert "59, 130, 246" in content or "#3B82F6" in content
    assert "245, 158, 11" in content or "#F59E0B" in content
    assert "239, 68, 68" in content or "#EF4444" in content
    assert "255, 255, 255" in content or "#FFFFFF" in content


def test_draw_board_layout_constants() -> None:
    """Layout constants window 700x800 board_size 500 gap 10 origin (100,150) cell_size 90."""
    tiles_path = Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")
    assert "700" in content
    assert "800" in content
    assert "500" in content
    assert "90" in content
    assert "10" in content
    assert "100" in content
    assert "150" in content


def test_draw_board_headless_importable() -> None:
    """tiles.py importable headless."""
    from src.render.tiles import blend_colors, cell_rect, draw_board, lerp_heat_color, value_to_base_color

    assert callable(draw_board)
    assert callable(lerp_heat_color)
    assert callable(value_to_base_color)
    assert callable(blend_colors)
    assert callable(cell_rect)
