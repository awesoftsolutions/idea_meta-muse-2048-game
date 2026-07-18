"""
tests/test_tiles_refined.py — TDD tests for tiles.py refinement.

Covers AC-9 to AC-13: unified blend 70% heat 30% base, no debug dot x+w-10,
no gray fallback (200,200,200), value_to_base_color beyond 2048 not gray,
blend_colors 70% heat 30% base, lerp_heat_color exact colors.

System: Phase 4 Sprint 1 Tasks 1 & 2 Step 2 TDD red phase.
"""

from __future__ import annotations

import pathlib
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from src.core.board import Tile
from src.render.tiles import (
    blend_colors,
    cell_rect,
    lerp_heat_color,
    value_to_base_color,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_surface() -> MagicMock:
    """Mock surface for draw_board tests."""
    surface = MagicMock()
    surface.fill = MagicMock()
    surface.blit = MagicMock()
    surface.get_rect = MagicMock(return_value=MagicMock(center=(0, 0)))
    return surface


@pytest.fixture
def empty_grid() -> List[List[Optional[Tile]]]:
    """5x5 empty grid."""
    return [[None for _ in range(5)] for _ in range(5)]


@pytest.fixture
def full_grid() -> List[List[Optional[Tile]]]:
    """5x5 full grid with various values and heats."""
    values = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 2, 4, 8]
    heats = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0]
    grid: List[List[Optional[Tile]]] = []
    idx = 0
    for _ in range(5):
        row: List[Optional[Tile]] = []
        for _ in range(5):
            row.append(Tile(value=values[idx], heat=heats[idx]))
            idx += 1
        grid.append(row)
    return grid


# ---------------------------------------------------------------------------
# AC-9, AC-13: Unified blend 70% heat 30% base
# ---------------------------------------------------------------------------


def test_draw_board_unified_blend() -> None:
    """AC-9, AC-13: blend_colors unified 70% heat 30% base weighted average."""
    heat_color = (59, 130, 246)  # #3B82F6 cool
    base_color = (238, 228, 218)  # 2 tile

    result = blend_colors(base_color, heat_color, heat_ratio=0.7)

    # Expected: 70% heat 30% base
    expected_r = int(base_color[0] * 0.3 + heat_color[0] * 0.7)
    expected_g = int(base_color[1] * 0.3 + heat_color[1] * 0.7)
    expected_b = int(base_color[2] * 0.3 + heat_color[2] * 0.7)

    assert result == (expected_r, expected_g, expected_b), (
        f"Blend {result} != expected {(expected_r, expected_g, expected_b)} "
        f"for 70% heat 30% base. Got inverted?"
    )


def test_blend_colors_70_30() -> None:
    """AC-13: blend_colors returns weighted average 70% heat 30% base unified not inverted."""
    base = (100, 100, 100)
    heat = (200, 200, 200)

    result = blend_colors(base, heat, heat_ratio=0.7)

    # 70% heat 30% base: 100*0.3 + 200*0.7 = 30 + 140 = 170
    assert result == (170, 170, 170), f"Expected (170,170,170) got {result} - inverted blend?"

    # Inverted would be 100*0.7 + 200*0.3 = 70+60=130
    assert result != (130, 130, 130), "Blend is inverted 70% base 30% heat, should be 70% heat 30% base"


def test_blend_colors_ratio_clamping() -> None:
    """EC-15: blend_colors ratio out of range clamped 0..1."""
    base = (100, 100, 100)
    heat = (200, 200, 200)

    # Ratio <0 clamped to 0 -> 100% base
    result_low = blend_colors(base, heat, heat_ratio=-0.5)
    assert result_low == (100, 100, 100)

    # Ratio >1 clamped to 1 -> 100% heat
    result_high = blend_colors(base, heat, heat_ratio=1.5)
    assert result_high == (200, 200, 200)


def test_blend_colors_exact_heat_colors() -> None:
    """AC-9: blend with exact heat colors #3B82F6 #F59E0B #EF4444 #FFFFFF."""
    base = (238, 228, 218)

    # Cool #3B82F6
    cool = (59, 130, 246)
    result_cool = blend_colors(base, cool, 0.7)
    assert result_cool[0] == int(base[0] * 0.3 + cool[0] * 0.7)

    # Warm #F59E0B
    warm = (245, 158, 11)
    result_warm = blend_colors(base, warm, 0.7)
    assert result_warm[0] == int(base[0] * 0.3 + warm[0] * 0.7)

    # Hot #EF4444
    hot = (239, 68, 68)
    result_hot = blend_colors(base, hot, 0.7)
    assert result_hot[0] == int(base[0] * 0.3 + hot[0] * 0.7)

    # Unstable #FFFFFF
    unstable = (255, 255, 255)
    result_unstable = blend_colors(base, unstable, 0.7)
    assert result_unstable[0] == int(base[0] * 0.3 + unstable[0] * 0.7)


# ---------------------------------------------------------------------------
# AC-10: No debug dot x+w-10
# ---------------------------------------------------------------------------


def test_no_debug_dot() -> None:
    """AC-10: tiles.py no debug heat dot pattern x+w-10 removed."""
    tiles_path = pathlib.Path("src/render/tiles.py")
    assert tiles_path.exists(), "src/render/tiles.py not found"

    content = tiles_path.read_text(encoding="utf-8")

    # Check for debug dot pattern x+w-10 or x + w - 10
    assert "x+w-10" not in content, "Found debug dot pattern x+w-10 in tiles.py"
    assert "x + w - 10" not in content, "Found debug dot pattern x + w - 10 in tiles.py"
    # Also check for the specific circle at (x+w-10,y+10,5) pattern
    # The bug is at line 351: pygame.draw.circle(surface, dot_color, (x + w - 10, y + 10), 5)
    # After fix, this should not exist
    # We allow it in comments but not in code - check non-comment lines
    non_comment_lines = [
        line for line in content.splitlines() if not line.strip().startswith("#") and "x + w - 10" in line
    ]
    assert len(non_comment_lines) == 0, f"Debug dot still present in code: {non_comment_lines}"


def test_no_debug_dot_circle_pattern() -> None:
    """AC-10: No debug circle at (x+w-10,y+10,5) pattern."""
    tiles_path = pathlib.Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")

    # Look for draw.circle with w-10 pattern in non-comment lines
    lines = content.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "draw.circle" in line and "w - 10" in line:
            pytest.fail(f"Debug dot circle found at line {i}: {line.strip()}")


# ---------------------------------------------------------------------------
# AC-11: No gray fallback (200,200,200)
# ---------------------------------------------------------------------------


def test_no_gray_fallback() -> None:
    """AC-11: tiles.py no gray fallback (200,200,200) palette extension implemented."""
    tiles_path = pathlib.Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")

    # Check for FALLBACK_COLOR = (200,200,200) or return (200,200,200) in code
    # Allow in comments but not in active code for value_to_base_color
    # The bug is at lines 69,147,149: FALLBACK_COLOR and return (200,200,200)
    # After fix, should not return gray for >2048

    # Count occurrences of (200, 200, 200) in non-comment, non-docstring code
    # Simple heuristic: check lines that are not comments and contain (200, 200, 200)
    non_comment_gray = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "(200, 200, 200)" in line:
            non_comment_gray.append(line.strip())

    # After fix, there should be zero occurrences in code
    # Currently there are 3 (red phase) - this test should FAIL initially
    assert len(non_comment_gray) == 0, (
        f"Gray fallback (200,200,200) still present in tiles.py code: {non_comment_gray}. "
        "Fix to palette extension lerp beyond 2048."
    )


def test_no_fallback_color_constant_gray() -> None:
    """AC-11: FALLBACK_COLOR should not be gray (200,200,200) after fix."""
    tiles_path = pathlib.Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")

    # Check if FALLBACK_COLOR is defined as (200,200,200)
    if "FALLBACK_COLOR" in content:
        for line in content.splitlines():
            if "FALLBACK_COLOR" in line and "(200, 200, 200)" in line and not line.strip().startswith("#"):
                pytest.fail(f"FALLBACK_COLOR still gray: {line.strip()}")


# ---------------------------------------------------------------------------
# AC-12: value_to_base_color beyond 2048 not gray
# ---------------------------------------------------------------------------


def test_value_to_base_color_beyond_2048() -> None:
    """AC-12: value_to_base_color >2048 returns palette extension not gray (200,200,200)."""
    gray = (200, 200, 200)

    color_4096 = value_to_base_color(4096)
    assert color_4096 != gray, f"value_to_base_color(4096) returned gray {gray}, should be palette extension"

    color_8192 = value_to_base_color(8192)
    assert color_8192 != gray, f"value_to_base_color(8192) returned gray {gray}, should be palette extension"

    color_16384 = value_to_base_color(16384)
    assert color_16384 != gray, f"value_to_base_color(16384) returned gray {gray}"


def test_value_to_base_color_beyond_2048_distinct() -> None:
    """AC-12: palette extension distinct per value beyond 2048."""
    color_2048 = value_to_base_color(2048)
    color_4096 = value_to_base_color(4096)
    color_8192 = value_to_base_color(8192)

    assert color_4096 != color_2048, "4096 color should be distinct from 2048"
    assert color_8192 != color_4096, "8192 color should be distinct from 4096"
    assert color_8192 != color_2048, "8192 color should be distinct from 2048"


def test_value_to_base_color_classic_palette() -> None:
    """Classic palette 2..2048 distinct per value."""
    colors = {}
    for value in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]:
        color = value_to_base_color(value)
        assert color != (200, 200, 200), f"Value {value} returned gray fallback"
        colors[value] = color

    # All distinct
    unique_colors = set(colors.values())
    assert len(unique_colors) == len(colors), "Classic palette colors should be distinct per value"


def test_value_to_base_color_invalid_not_gray() -> None:
    """EC-13: value 0 or 1 or negative returns fallback not gray (200,200,200)."""
    gray = (200, 200, 200)

    # After fix, invalid values should not return gray either
    # They should return dark color like (60,60,60) or via log2 formula
    color_0 = value_to_base_color(0)
    assert color_0 != gray, f"value_to_base_color(0) returned gray {gray}"

    color_1 = value_to_base_color(1)
    assert color_1 != gray, f"value_to_base_color(1) returned gray {gray}"


# ---------------------------------------------------------------------------
# lerp_heat_color exact colors
# ---------------------------------------------------------------------------


def test_lerp_heat_color_exact() -> None:
    """lerp_heat_color returns #3B82F6 0 #F59E0B 1 #EF4444 2 #FFFFFF 3 glow."""
    color_0, glow_0 = lerp_heat_color(0)
    assert color_0 == (59, 130, 246), f"Heat 0 color {color_0} != (59,130,246) #3B82F6"
    assert glow_0 is False

    color_1, glow_1 = lerp_heat_color(1)
    assert color_1 == (245, 158, 11), f"Heat 1 color {color_1} != (245,158,11) #F59E0B"
    assert glow_1 is False

    color_2, glow_2 = lerp_heat_color(2)
    assert color_2 == (239, 68, 68), f"Heat 2 color {color_2} != (239,68,68) #EF4444"
    assert glow_2 is False

    color_3, glow_3 = lerp_heat_color(3)
    assert color_3 == (255, 255, 255), f"Heat 3 color {color_3} != (255,255,255) #FFFFFF"
    assert glow_3 is True


def test_lerp_heat_color_clamping() -> None:
    """EC-16: heat out of range clamped 0-3."""
    color_neg, _ = lerp_heat_color(-1)
    assert color_neg == (59, 130, 246), "Heat -1 should clamp to 0 #3B82F6"

    color_high, glow_high = lerp_heat_color(10)
    assert color_high == (255, 255, 255), "Heat 10 should clamp to 3 #FFFFFF"
    assert glow_high is True


def test_lerp_heat_color_non_int() -> None:
    """lerp_heat_color handles non-int via int conversion or defaults to 0."""
    color, _ = lerp_heat_color("1")  # type: ignore[arg-type]
    assert color == (245, 158, 11), "String '1' should convert to heat 1 #F59E0B"

    color_invalid, _ = lerp_heat_color("invalid")  # type: ignore[arg-type]
    assert color_invalid == (59, 130, 246), "Invalid string should default to 0 #3B82F6"


# ---------------------------------------------------------------------------
# cell_rect and draw_board no mutation
# ---------------------------------------------------------------------------


def test_cell_rect_valid() -> None:
    """cell_rect returns (x,y,w,h) for valid r,c."""
    x, y, w, h = cell_rect(0, 0)
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert w == 90
    assert h == 90

    x2, y2, _, _ = cell_rect(4, 4)
    assert x2 > x
    assert y2 > y


def test_cell_rect_invalid_raises() -> None:
    """cell_rect invalid r,c raises ValueError E002."""
    with pytest.raises(ValueError, match="E002"):
        cell_rect(5, 0)

    with pytest.raises(ValueError, match="E002"):
        cell_rect(0, 5)

    with pytest.raises(ValueError, match="E002"):
        cell_rect(-1, 0)


def test_draw_board_no_mutation(empty_grid: List[List[Optional[Tile]]], mock_surface: MagicMock) -> None:
    """draw_board does not mutate grid values heats."""
    from src.render.tiles import draw_board

    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    grid[0][0] = Tile(value=2, heat=0)
    grid[1][1] = Tile(value=4, heat=1)

    original = [[(cell.value, cell.heat) if cell is not None else None for cell in row] for row in grid]

    try:
        draw_board(mock_surface, grid, score=0)
    except Exception:
        # Mock surface may cause issues but should not crash validation
        pass

    after = [[(cell.value, cell.heat) if cell is not None else None for cell in row] for row in grid]
    assert original == after, "draw_board mutated grid"


def test_draw_board_empty_grid_no_crash(empty_grid: List[List[Optional[Tile]]], mock_surface: MagicMock) -> None:
    """draw_board empty grid all None draws empty cells #334155 no crash."""
    from src.render.tiles import draw_board

    try:
        draw_board(mock_surface, empty_grid, score=0)
    except Exception as e:
        pytest.fail(f"draw_board crashed on empty grid: {e}")


def test_draw_board_full_grid_no_crash(full_grid: List[List[Optional[Tile]]], mock_surface: MagicMock) -> None:
    """draw_board full grid 25 Tiles various values heats draws without crash."""
    from src.render.tiles import draw_board

    try:
        draw_board(mock_surface, full_grid, score=100)
    except Exception as e:
        pytest.fail(f"draw_board crashed on full grid: {e}")


def test_draw_board_surface_none_raises() -> None:
    """draw_board surface None raises ValueError."""
    from src.render.tiles import draw_board

    grid: List[List[Optional[Tile]]] = [[None for _ in range(5)] for _ in range(5)]
    with pytest.raises(ValueError):
        draw_board(None, grid, score=0)


def test_draw_board_invalid_grid_raises(mock_surface: MagicMock) -> None:
    """draw_board invalid grid raises ValueError."""
    from src.render.tiles import draw_board

    with pytest.raises(ValueError):
        draw_board(mock_surface, [[None] * 4] * 5, score=0)  # 4 cols not 5

    with pytest.raises(ValueError):
        draw_board(mock_surface, [[None] * 5] * 4, score=0)  # 4 rows not 5


def test_no_external_assets_tiles() -> None:
    """No external assets in tiles.py no image.load no font.Font file path only SysFont."""
    tiles_path = pathlib.Path("src/render/tiles.py")
    content = tiles_path.read_text(encoding="utf-8")

    assert "image.load" not in content, "Found image.load in tiles.py - programmatic only violation"

    # Check font.Font file path - only SysFont allowed
    lines_with_font_font = [
        line for line in content.splitlines() if "font.Font" in line and "SysFont" not in line and not line.strip().startswith("#")
    ]
    assert len(lines_with_font_font) == 0, f"Found font.Font file path in tiles.py: {lines_with_font_font}"

    assert "SysFont" in content, "SysFont not found in tiles.py"
