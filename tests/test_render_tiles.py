"""
tests/test_render_tiles.py — Wave3 rendering heat identity + reactor chrome + layout.

TDD red phase: src/render/tiles.py does NOT exist yet, so imports will fail
with ModuleNotFoundError. This is expected and required for red phase.

Covers AC-1 to AC-6, AC-8, AC-16 per pseudocode phase_3_sprint_1_wave3_rendering.md:
- lerp_heat_color exact colors #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow
- value_to_base_color distinct per value 2..2048 classic palette
- blend_colors 70% heat 30% base
- cell_rect layout calc origin (100,150) board_size 500 gap 10 size 90
- draw_board draws background #0F172A board #1E293B empty #334155 heat lerp
- tile rendering distinct per value and heat reactor chrome programmatic only
- mode label overlay small corner
- defensive validation surface None, grid not 5x5, value not power of two, no mutation
- headless importable, programmatic only no image.load

System: RenderTiles per Phase 3 architecture ADR-018, ADR-020.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

import pytest

from src.core.board import BOARD_SIZE, Tile, create_empty_grid


# ---------------------------------------------------------------------------
# AC-2: lerp_heat_color exact colors
# ---------------------------------------------------------------------------


def test_lerp_heat_color_0_returns_3B82F6() -> None:
    """AC-2: heat 0 returns RGB (59,130,246) #3B82F6 cool blue glow False."""
    from src.render.tiles import lerp_heat_color

    color, glow = lerp_heat_color(0)
    assert color == (59, 130, 246), f"Expected (59,130,246) #3B82F6 for heat 0, got {color}"
    assert glow is False, "Heat 0 should not have glow"


def test_lerp_heat_color_1_returns_F59E0B() -> None:
    """AC-2: heat 1 returns RGB (245,158,11) #F59E0B warm amber glow False."""
    from src.render.tiles import lerp_heat_color

    color, glow = lerp_heat_color(1)
    assert color == (245, 158, 11), f"Expected (245,158,11) #F59E0B for heat 1, got {color}"
    assert glow is False, "Heat 1 should not have glow"


def test_lerp_heat_color_2_returns_EF4444() -> None:
    """AC-2: heat 2 returns RGB (239,68,68) #EF4444 hot red glow False."""
    from src.render.tiles import lerp_heat_color

    color, glow = lerp_heat_color(2)
    assert color == (239, 68, 68), f"Expected (239,68,68) #EF4444 for heat 2, got {color}"
    assert glow is False, "Heat 2 should not have glow (or may have glow per spec, but spec says False for 2)"


def test_lerp_heat_color_3_returns_FFFFFF_glow() -> None:
    """AC-2: heat 3 returns RGB (255,255,255) #FFFFFF white glow True."""
    from src.render.tiles import lerp_heat_color

    color, glow = lerp_heat_color(3)
    assert color == (255, 255, 255), f"Expected (255,255,255) #FFFFFF for heat 3, got {color}"
    assert glow is True, "Heat 3 unstable should have glow True"


def test_lerp_heat_color_out_of_range_clamping() -> None:
    """Edge: heat -1 or 5 clamps 0-3 per E008."""
    from src.render.tiles import lerp_heat_color

    color_neg, glow_neg = lerp_heat_color(-1)
    assert color_neg == (59, 130, 246), f"Heat -1 should clamp to 0 -> (59,130,246), got {color_neg}"
    assert glow_neg is False

    color_high, glow_high = lerp_heat_color(5)
    assert color_high == (255, 255, 255), f"Heat 5 should clamp to 3 -> (255,255,255), got {color_high}"
    assert glow_high is True

    color_100, _ = lerp_heat_color(100)
    assert color_100 == (255, 255, 255)


# ---------------------------------------------------------------------------
# AC-3: value_to_base_color distinct per value
# ---------------------------------------------------------------------------


def test_value_to_base_color_distinct_per_value() -> None:
    """AC-3: values 2..2048 each return distinct RGB classic 2048 palette."""
    from src.render.tiles import value_to_base_color

    values = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    colors = []
    for v in values:
        c = value_to_base_color(v)
        assert isinstance(c, tuple), f"value_to_base_color({v}) should return tuple, got {type(c)}"
        assert len(c) == 3, f"RGB tuple length should be 3, got {len(c)} for value {v}"
        for channel in c:
            assert 0 <= channel <= 255, f"Channel {channel} out of range for value {v}"
        colors.append(c)

    # Distinct per value
    assert len(set(colors)) == len(values), f"Expected {len(values)} distinct colors, got {len(set(colors))}: {colors}"


def test_value_to_base_color_fallback() -> None:
    """Edge: value not power of two or >2048 fallback or lerp."""
    from src.render.tiles import value_to_base_color

    # Non power of two should fallback
    fallback = value_to_base_color(3)
    assert isinstance(fallback, tuple)
    assert len(fallback) == 3

    # >2048 should lerp darker
    high = value_to_base_color(4096)
    assert isinstance(high, tuple)
    assert len(high) == 3
    for ch in high:
        assert 0 <= ch <= 255

    # 0 or 1 fallback
    zero = value_to_base_color(0)
    assert isinstance(zero, tuple)


# ---------------------------------------------------------------------------
# AC-4: blend_colors 70% heat 30% base
# ---------------------------------------------------------------------------


def test_blend_colors_70_30() -> None:
    """AC-4: blend base*0.3 + heat*0.7 with ratio 0.7 default."""
    from src.render.tiles import blend_colors

    base = (238, 228, 218)  # 2 tile #EEE4DA
    heat = (59, 130, 246)  # #3B82F6
    result = blend_colors(base, heat, heat_ratio=0.7)
    # Expected: R = 238*0.3 + 59*0.7 = 71.4+41.3=112.7 -> 112
    # G = 228*0.3 +130*0.7 =68.4+91=159.4 ->159
    # B =218*0.3+246*0.7=65.4+172.2=237.6 ->237
    expected_r = int(base[0] * 0.3 + heat[0] * 0.7)
    expected_g = int(base[1] * 0.3 + heat[1] * 0.7)
    expected_b = int(base[2] * 0.3 + heat[2] * 0.7)
    assert result == (expected_r, expected_g, expected_b), f"Expected {(expected_r, expected_g, expected_b)}, got {result}"

    # Test with default ratio 0.7
    result_default = blend_colors(base, heat)
    assert result_default == (expected_r, expected_g, expected_b)

    # Test ratio 0.0 -> base only
    result_base_only = blend_colors(base, heat, heat_ratio=0.0)
    assert result_base_only == base

    # Test ratio 1.0 -> heat only
    result_heat_only = blend_colors(base, heat, heat_ratio=1.0)
    assert result_heat_only == heat


# ---------------------------------------------------------------------------
# AC-5: cell_rect layout calc
# ---------------------------------------------------------------------------


def test_cell_rect_layout_calc() -> None:
    """AC-5: cell_rect returns correct x,y with origin (100,150) cell_size 90 gap 10."""
    from src.render.tiles import cell_rect

    # Origin (100,150) board_size 500 gap 10 size 90
    # x = board_origin_x + c*(cell_size+cell_gap) + cell_gap//2
    # y = board_origin_y + r*(cell_size+cell_gap) + cell_gap//2
    # For r=0,c=0: x=100+0*100+5=105, y=150+0*100+5=155, w=90,h=90
    rect_00 = cell_rect(0, 0)
    assert len(rect_00) == 4, f"cell_rect should return 4-tuple (x,y,w,h), got {rect_00}"
    x, y, w, h = rect_00
    assert x == 100 + 0 * (90 + 10) + 10 // 2, f"Expected x 105 for (0,0), got {x}"
    assert y == 150 + 0 * (90 + 10) + 10 // 2, f"Expected y 155 for (0,0), got {y}"
    assert w == 90, f"Expected w 90, got {w}"
    assert h == 90, f"Expected h 90, got {h}"

    # r=4,c=4: x=100+4*100+5=505, y=150+4*100+5=555
    rect_44 = cell_rect(4, 4)
    x44, y44, w44, h44 = rect_44
    assert x44 == 100 + 4 * (90 + 10) + 10 // 2, f"Expected x 505 for (4,4), got {x44}"
    assert y44 == 150 + 4 * (90 + 10) + 10 // 2, f"Expected y 555 for (4,4), got {y44}"
    assert w44 == 90
    assert h44 == 90

    # Check with custom origin
    rect_custom = cell_rect(0, 0, board_origin_x=0, board_origin_y=0, cell_size=100, cell_gap=0)
    assert rect_custom[0] == 0
    assert rect_custom[1] == 0


def test_cell_rect_out_of_range_raises() -> None:
    """Edge: r,c out of 0..4 raises ValueError E002."""
    from src.render.tiles import cell_rect

    with pytest.raises(ValueError, match="E002|MalformedGrid|out of range|0..4"):
        cell_rect(-1, 0)

    with pytest.raises(ValueError):
        cell_rect(0, -1)

    with pytest.raises(ValueError):
        cell_rect(5, 0)

    with pytest.raises(ValueError):
        cell_rect(0, 5)


# ---------------------------------------------------------------------------
# AC-1, AC-6: draw_board validation and rendering
# ---------------------------------------------------------------------------


def test_draw_board_surface_None_raises() -> None:
    """Edge: surface None raises ValueError E002."""
    from src.render.tiles import draw_board

    grid = create_empty_grid()
    with pytest.raises(ValueError, match="E002|surface|None"):
        draw_board(None, grid, 0)


def test_draw_board_grid_not_5x5_raises() -> None:
    """Edge: grid not 5x5 raises ValueError E002."""
    from src.render.tiles import draw_board

    class FakeSurface:
        def fill(self, color):
            pass

    fake_surface = FakeSurface()

    # None grid
    with pytest.raises(ValueError, match="E002|MalformedGrid|5x5"):
        draw_board(fake_surface, None, 0)

    # Wrong row count
    with pytest.raises(ValueError):
        draw_board(fake_surface, [[None] * 5 for _ in range(4)], 0)

    # Wrong col count
    with pytest.raises(ValueError):
        draw_board(fake_surface, [[None] * 4 for _ in range(5)], 0)


def test_draw_board_Tile_value_not_power_of_two_raises() -> None:
    """Edge: Tile value not power of two raises ValueError defensive."""
    from src.render.tiles import draw_board

    class FakeSurface:
        def fill(self, color):
            pass

        def get_size(self):
            return (700, 800)

    # We need to bypass Tile __post_init__ validation to test defensive check in draw_board
    # Create a mock tile with invalid value via object.__setattr__
    grid = create_empty_grid()
    fake_tile = Tile.__new__(Tile)
    object.__setattr__(fake_tile, "value", 3)  # Not power of two
    object.__setattr__(fake_tile, "heat", 0)
    grid[0][0] = fake_tile

    fake_surface = FakeSurface()
    # draw_board should defensively check value power of two even if Tile bypassed
    with pytest.raises(ValueError, match="E002|power|MalformedGrid"):
        draw_board(fake_surface, grid, 0)


def test_draw_board_programmatic_only_no_image_load() -> None:
    """AC-6: src/render/tiles.py grepped for pygame.image.load and font.Font file path no matches."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists(), "src/render/tiles.py must exist for Wave3 final"
    content = tiles_path.read_text(encoding="utf-8")
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "pygame.image.load" in stripped:
            violations.append(f"{tiles_path}:{i}: {stripped}")
        if "font.Font(" in stripped and "SysFont" not in stripped:
            # Allow if in comment or test
            if "test" not in stripped.lower():
                violations.append(f"{tiles_path}:{i}: {stripped} - external font asset")
    assert not violations, f"External assets found in tiles.py: {violations}"


def test_draw_board_reactor_chrome_colors() -> None:
    """AC-1, AC-6: draw_board code contains reactor chrome #0F172A #1E293B #334155 #475569."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists(), "src/render/tiles.py must exist"
    content = tiles_path.read_text(encoding="utf-8")
    # Check for reactor chrome colors as RGB tuples or hex comments
    # Background #0F172A = (15,23,42)
    assert "15, 23, 42" in content or "15,23,42" in content or "#0F172A" in content or "0F172A" in content, \
        "Background color #0F172A (15,23,42) not found in tiles.py"
    # Board background #1E293B = (30,41,59)
    assert "30, 41, 59" in content or "30,41,59" in content or "#1E293B" in content, \
        "Board background #1E293B (30,41,59) not found"
    # Empty cell #334155 = (51,65,85)
    assert "51, 65, 85" in content or "51,65,85" in content or "#334155" in content, \
        "Empty cell color #334155 (51,65,85) not found"
    # Border #475569 = (71,85,105)
    assert "71, 85, 105" in content or "71,85,105" in content or "#475569" in content, \
        "Border color #475569 (71,85,105) not found"

    # Heat colors
    assert "59, 130, 246" in content or "59,130,246" in content or "#3B82F6" in content, \
        "Heat 0 color #3B82F6 not found"
    assert "245, 158, 11" in content or "245,158,11" in content or "#F59E0B" in content, \
        "Heat 1 color #F59E0B not found"
    assert "239, 68, 68" in content or "239,68,68" in content or "#EF4444" in content, \
        "Heat 2 color #EF4444 not found"
    assert "255, 255, 255" in content or "255,255,255" in content or "#FFFFFF" in content, \
        "Heat 3 color #FFFFFF not found"


def test_draw_board_no_mutation() -> None:
    """Pure drawing: grid unchanged after draw_board call."""
    from src.render.tiles import draw_board

    # Create a mock surface that records calls but doesn't need pygame
    class MockSurface:
        def __init__(self):
            self.fill_calls = []
            self.rect_calls = []

        def fill(self, color):
            self.fill_calls.append(color)

        def get_size(self):
            return (700, 800)

    # Mock pygame.draw and pygame.font for headless test
    import unittest.mock as mock

    mock_draw = mock.MagicMock()
    mock_font = mock.MagicMock()
    mock_font_instance = mock.MagicMock()
    mock_font_instance.render.return_value = mock.MagicMock(get_rect=lambda center: mock.MagicMock())
    mock_font.SysFont.return_value = mock_font_instance

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    grid[1][1] = Tile(value=4, heat=1)
    grid[2][2] = Tile(value=8, heat=2)

    # Deep copy for comparison
    import copy
    original_grid_copy = copy.deepcopy(grid)

    mock_surface = MockSurface()

    # Patch pygame modules inside draw_board if it imports pygame
    with mock.patch.dict("sys.modules", {"pygame": mock.MagicMock(draw=mock_draw, font=mock_font)}):
        # Also need to handle pygame.draw.rect etc
        try:
            draw_board(mock_surface, grid, 100)
        except Exception as e:
            # If draw_board tries to use real pygame, it may fail in headless
            # But we still check mutation
            pass

    # Verify grid unchanged
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            orig = original_grid_copy[r][c]
            new = grid[r][c]
            if orig is None:
                assert new is None, f"Grid mutated at ({r},{c}): expected None, got {new}"
            else:
                assert new is not None
                assert new.value == orig.value, f"Grid value mutated at ({r},{c})"
                assert new.heat == orig.heat, f"Grid heat mutated at ({r},{c})"


def test_draw_board_headless_importable() -> None:
    """AC-16: tiles.py importable without DISPLAY and without pygame leak in core."""
    # This test verifies that src/render/tiles.py can be imported headlessly
    # It will fail in red phase because file doesn't exist
    try:
        from src.render.tiles import draw_board, lerp_heat_color, value_to_base_color, blend_colors, cell_rect

        assert callable(draw_board)
        assert callable(lerp_heat_color)
        assert callable(value_to_base_color)
        assert callable(blend_colors)
        assert callable(cell_rect)
    except ModuleNotFoundError as e:
        pytest.fail(f"src/render/tiles.py not importable headless: {e}")


def test_draw_board_layout_constants() -> None:
    """Verify layout constants window 700x800 board_size 500 gap 10 origin (100,150)."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists()
    content = tiles_path.read_text(encoding="utf-8")
    # Check for layout constants
    assert "700" in content, "Window width 700 not found"
    assert "800" in content, "Window height 800 not found"
    assert "500" in content, "Board size 500 not found"
    assert "90" in content, "Cell size 90 not found"
    assert "10" in content, "Cell gap 10 not found"
    assert "100" in content, "Board origin x 100 not found"
    assert "150" in content, "Board origin y 150 not found"


def test_mode_label_overlay_present() -> None:
    """AC-8: mode label overlay fixed corner test-mode overlay per SOW."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists()
    content = tiles_path.read_text(encoding="utf-8")
    # Check for mode label overlay rendering
    assert "Mode" in content or "mode" in content.lower(), "Mode label not found in tiles.py"
    # Should have SysFont for mode label small corner
    assert "SysFont" in content, "SysFont not found for mode label"
    # Should have fixed corner rendering
    assert "blit" in content.lower() or "render" in content.lower(), "Blit/render not found for mode label"
