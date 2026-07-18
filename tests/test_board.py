"""
tests/test_board.py — Headless comprehensive board tests with Tile dataclass.

Covers slide correctness all 4 directions LEFT/RIGHT/UP/DOWN maximal blocking,
one-merge-per-tile [2,2,2,0,0]->[4,2,0,0,0], chain prevention [4,4,8,0,0]->[8,8,0,0,0],
no-move detection, RNG injection deterministic seeded, spawn distribution
seeded 1000 runs 85-95% 2s, new tile heat=0 immune, no pygame import via
sys.modules. Headless, no DISPLAY, no global random — only injected Random.

Production board: src/core/board.py with Tile dataclass value+heat,
Direction enum, SlideResult, MergeInfo, BOARD_SIZE=5, create_empty_grid,
spawn 90/10 heat=0 immune per ADR-009, injectable RNG.
"""

from __future__ import annotations

import math
import random
import sys
from typing import List, Optional

from src.core.board import (
    BOARD_SIZE,
    Board,
    Direction,
    Tile,
    create_empty_grid,
)

# ---------------------------------------------------------------------------
# Helpers — int list -> Tile grid and extraction for assertions
# ---------------------------------------------------------------------------


def make_tile_grid(int_grid: List[List[Optional[int]]]) -> List[List[Optional[Tile]]]:
    """Convert int list grid to Tile grid with heat=0. None stays None."""
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            val = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            if val is None:
                result[r][c] = None
            else:
                result[r][c] = Tile(value=val, heat=0)
    return result


def make_tile_grid_with_heat(
    int_grid: List[List[Optional[int]]],
    heat_grid: List[List[Optional[int]]],
) -> List[List[Optional[Tile]]]:
    """Convert int grid + heat grid to Tile grid with specified heat values."""
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            if v is None:
                result[r][c] = None
            else:
                h = (
                    heat_grid[r][c]
                    if r < len(heat_grid)
                    and c < len(heat_grid[r])
                    and heat_grid[r][c] is not None
                    else 0
                )
                result[r][c] = Tile(value=v, heat=int(h))
    return result


def grid_to_int_values(grid: List[List[Optional[Tile]]]) -> List[List[Optional[int]]]:
    """Extract int values from Tile grid for assertions. None stays None."""
    out: List[List[Optional[int]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[int]] = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            row.append(None if cell is None else cell.value)
        out.append(row)
    return out


def grid_to_heat_values(grid: List[List[Optional[Tile]]]) -> List[List[Optional[int]]]:
    """Extract heat values from Tile grid for heat assertions."""
    out: List[List[Optional[int]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[int]] = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            row.append(None if cell is None else cell.heat)
        out.append(row)
    return out


def assert_grids_equal_values(
    actual: List[List[Optional[Tile]]],
    expected: List[List[Optional[int]]],
) -> None:
    """Assert Tile grid values equal expected int grid with diff message."""
    actual_int = grid_to_int_values(actual)
    assert actual_int == expected, (
        f"Grid values mismatch.\nActual:   {actual_int}\nExpected: {expected}"
    )


def create_board_with_grid(
    int_grid: List[List[Optional[int]]], seed: int = 42
) -> Board:
    """Helper to create Board with Tile grid from int list and seeded RNG."""
    tile_grid = make_tile_grid(int_grid)
    rng = random.Random(seed)
    return Board(grid=tile_grid, rng=rng)


def _count_tiles(grid: List[List[Optional[Tile]]]) -> int:
    """Count non-None tiles."""
    cnt = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] is not None:
                cnt += 1
    return cnt


def _empty_int_grid() -> List[List[Optional[int]]]:
    """Return 5x5 None int grid."""
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


# ---------------------------------------------------------------------------
# Helpers conversion test
# ---------------------------------------------------------------------------


def test_helpers_conversion() -> None:
    """Helpers int->Tile and Tile->int roundtrip preserves values and None."""
    int_grid: List[List[Optional[int]]] = _empty_int_grid()
    int_grid[0] = [2, 4, None, 8, None]
    int_grid[1] = [16, None, 32, None, 64]
    tile_grid = make_tile_grid(int_grid)
    # Check Tile objects
    assert tile_grid[0][0] is not None and tile_grid[0][0].value == 2
    assert tile_grid[0][0].heat == 0
    assert tile_grid[0][2] is None
    # Roundtrip
    back = grid_to_int_values(tile_grid)
    assert back == int_grid
    # Heat extraction
    heat_vals = grid_to_heat_values(tile_grid)
    assert heat_vals[0][0] == 0
    assert heat_vals[0][2] is None
    # With heat
    heat_grid: List[List[Optional[int]]] = _empty_int_grid()
    heat_grid[0] = [1, 2, None, 3, None]
    tile_grid_h = make_tile_grid_with_heat(int_grid, heat_grid)
    assert tile_grid_h[0][0] is not None and tile_grid_h[0][0].heat == 1
    assert tile_grid_h[0][1] is not None and tile_grid_h[0][1].heat == 2


# ---------------------------------------------------------------------------
# Direction correctness — LEFT/RIGHT/UP/DOWN maximal blocking
# ---------------------------------------------------------------------------


def test_slide_left_basic() -> None:
    """AC-1 LEFT [2,2,0,0,0]->[4,0,0,0,0] score 4 moved True."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, None, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    # Board.slide spawns extra tile when moved True per contract
    assert result.score_delta == 4
    assert result.moved is True
    assert len(result.merges) == 1
    assert result.merges[0].value == 4
    # heat_gen floor(log2(4)/2)=1
    assert result.merges[0].heat_gen == math.floor(math.log2(4) / 2)
    # Merged tile must be at (0,0)
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    # Total tiles = merged 1 + spawn 1 =2
    assert _count_tiles(result.grid) == 2
    # No 8 present
    vals = grid_to_int_values(result.grid)
    flat = [v for row in vals for v in row if v is not None]
    assert 8 not in flat


def test_slide_right_basic() -> None:
    """RIGHT slide correctness [2,0,0,2,0]->[0,0,0,0,4] plus spawn."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, None, None, 2, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.RIGHT)
    assert result.score_delta == 4
    assert result.moved is True
    # Right-aligned merged tile at (0,4)
    assert result.grid[0][4] is not None and result.grid[0][4].value == 4
    assert _count_tiles(result.grid) == 2  # merged + spawn
    assert len(result.merges) == 1


def test_slide_up_basic() -> None:
    """UP slide correctness column [2,2,0,0,0]->[4,0,0,0,0] in column."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    int_grid[1][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.UP)
    assert result.score_delta == 4
    assert result.moved is True
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert _count_tiles(result.grid) == 2
    assert len(result.merges) == 1


def test_slide_down_basic() -> None:
    """DOWN slide correctness column [2,2,0,0,0] top -> bottom [0,0,0,0,4]."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    int_grid[1][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.DOWN)
    assert result.score_delta == 4
    assert result.moved is True
    # Bottom-aligned merged tile at (4,0)
    assert result.grid[4][0] is not None and result.grid[4][0].value == 4
    assert _count_tiles(result.grid) == 2
    assert len(result.merges) == 1


def test_maximal_blocking() -> None:
    """Maximal blocking: [2,4,2] stays, [2,0,4,0,2] LEFT -> [2,4,2,0,0] + spawn."""
    # Already left-aligned no merge -> moved False
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 2, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert_grids_equal_values(result.grid, int_grid)

    # Movement without merge
    int_grid2 = _empty_int_grid()
    int_grid2[0] = [2, None, 4, None, 2]
    board2 = create_board_with_grid(int_grid2, seed=42)
    result2 = board2.slide(Direction.LEFT)
    assert result2.moved is True
    assert result2.score_delta == 0
    # Core positions should be [2,4,2] left-aligned before spawn
    # After spawn, total tiles = 3 original +1 spawn =4
    assert _count_tiles(result2.grid) == 4
    # Check that 2,4,2 are present in row0 col0-2 in order ignoring spawn elsewhere
    # The spawn could be in row0 col3 or elsewhere, but col0-2 must be 2,4,2
    assert result2.grid[0][0] is not None and result2.grid[0][0].value == 2
    assert result2.grid[0][1] is not None and result2.grid[0][1].value == 4
    assert result2.grid[0][2] is not None and result2.grid[0][2].value == 2


# ---------------------------------------------------------------------------
# One-merge-per-tile
# ---------------------------------------------------------------------------


def test_one_merge_per_tile() -> None:
    """AC-2 [2,2,2,0,0]->[4,2,0,0,0] not [8,0,0,0,0] score 4."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 2, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 4
    assert result.moved is True
    assert len(result.merges) == 1
    # Core merged tiles at (0,0)=4, (0,1)=2 plus spawn
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert result.grid[0][1] is not None and result.grid[0][1].value == 2
    assert _count_tiles(result.grid) == 3  # 2 core + spawn
    # Ensure NOT [8,0,0,0,0] — no 8 present
    vals = grid_to_int_values(result.grid)
    flat = [v for row in vals for v in row if v is not None]
    assert 8 not in flat, f"Should not have 8, got {flat}"


def test_one_merge_four_same() -> None:
    """[2,2,2,2,0]->[4,4,0,0,0] two merges score 8 not [8,0,0,0,0]."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 2, 2, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 8
    assert result.moved is True
    assert len(result.merges) == 2
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert result.grid[0][1] is not None and result.grid[0][1].value == 4
    assert _count_tiles(result.grid) == 3  # 2 merged + spawn
    vals = grid_to_int_values(result.grid)
    flat = [v for row in vals for v in row if v is not None]
    assert 8 not in flat


# ---------------------------------------------------------------------------
# Chain prevention
# ---------------------------------------------------------------------------


def test_chain_prevention() -> None:
    """AC-3 [4,4,8,0,0]->[8,8,0,0,0] not [16,0,0,0,0] score 8."""
    int_grid = _empty_int_grid()
    int_grid[0] = [4, 4, 8, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 8
    assert result.moved is True
    assert len(result.merges) == 1
    assert result.grid[0][0] is not None and result.grid[0][0].value == 8
    assert result.grid[0][1] is not None and result.grid[0][1].value == 8
    assert _count_tiles(result.grid) == 3  # 2 core + spawn
    vals = grid_to_int_values(result.grid)
    flat = [v for row in vals for v in row if v is not None]
    assert 16 not in flat, f"Chain merge should not produce 16, got {flat}"


def test_chain_prevention_complex() -> None:
    """[2,2,4,4,0]->[4,8,0,0,0] score 12 two merges."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 4, 4, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 12  # 4+8
    assert result.moved is True
    assert len(result.merges) == 2
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert result.grid[0][1] is not None and result.grid[0][1].value == 8
    assert _count_tiles(result.grid) == 3  # 2 merged + spawn


# ---------------------------------------------------------------------------
# No-move detection
# ---------------------------------------------------------------------------


def test_no_move_empty_board() -> None:
    """Empty board slide moved False score 0 no spawn."""
    int_grid = _empty_int_grid()
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert _count_tiles(result.grid) == 0
    assert_grids_equal_values(result.grid, int_grid)


def test_no_move_full_no_merge() -> None:
    """Full board no merge possible moved False."""
    # Checkerboard alternating 2,4 — no adjacent equal horizontally or vertically
    int_grid: List[List[Optional[int]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[int]] = []
        for c in range(BOARD_SIZE):
            row.append(2 if (r + c) % 2 == 0 else 4)
        int_grid.append(row)
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert _count_tiles(result.grid) == BOARD_SIZE * BOARD_SIZE


def test_no_move_already_aligned() -> None:
    """Already left-aligned no merge moved False."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 8, 16, 32]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert_grids_equal_values(result.grid, int_grid)


# ---------------------------------------------------------------------------
# RNG injection deterministic seeded
# ---------------------------------------------------------------------------


def test_rng_deterministic_seeded() -> None:
    """Same seed same spawn position and value deterministic."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2

    board1 = create_board_with_grid(int_grid, seed=123)
    board2 = create_board_with_grid(int_grid, seed=123)

    result1 = board1.slide(Direction.RIGHT)
    result2 = board2.slide(Direction.RIGHT)

    vals1 = grid_to_int_values(result1.grid)
    vals2 = grid_to_int_values(result2.grid)
    assert vals1 == vals2, f"Same seed should produce same grid: {vals1} vs {vals2}"
    assert result1.score_delta == result2.score_delta
    assert result1.moved == result2.moved

    # Also test spawn_tile deterministic
    empty_grid = _empty_int_grid()
    # Almost full with one empty at (2,2)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not (r == 2 and c == 2):
                empty_grid[r][c] = 2
    b1 = create_board_with_grid(empty_grid, seed=999)
    b2 = create_board_with_grid(empty_grid, seed=999)
    pos1 = b1.spawn_tile()
    pos2 = b2.spawn_tile()
    assert pos1 == pos2
    assert pos1 == (2, 2)
    assert b1.grid[2][2] is not None and b2.grid[2][2] is not None
    assert b1.grid[2][2].value == b2.grid[2][2].value


# ---------------------------------------------------------------------------
# Spawn distribution seeded 1000 runs 85-95% 2s
# ---------------------------------------------------------------------------


def test_spawn_distribution_1000_runs() -> None:
    """AC-4 seeded 1000 runs 85-95% 2s within tolerance."""
    count_2 = 0
    count_4 = 0
    base_seed = 42
    for i in range(1000):
        int_grid = _empty_int_grid()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not (r == 2 and c == 2):
                    int_grid[r][c] = 2
        # Use advancing seed to get distribution but deterministic
        board = create_board_with_grid(int_grid, seed=base_seed + i)
        pos = board.spawn_tile()
        assert pos == (2, 2), f"Expected spawn at (2,2), got {pos}"
        spawned = board.grid[2][2]
        assert spawned is not None
        assert spawned.value in (2, 4)
        assert spawned.heat == 0
        if spawned.value == 2:
            count_2 += 1
        else:
            count_4 += 1

    assert count_2 + count_4 == 1000
    # 85-95% tolerance per AC-4
    assert 850 <= count_2 <= 950, f"count_2 {count_2} not in 850-950"
    assert 50 <= count_4 <= 150, f"count_4 {count_4} not in 50-150"
    # Print for completion report visibility
    print(
        f"Spawn distribution: count_2={count_2} ({count_2 / 10:.1f}%), count_4={count_4}"
    )


# ---------------------------------------------------------------------------
# Spawn heat=0 immune
# ---------------------------------------------------------------------------


def test_spawn_heat_zero_immune() -> None:
    """New spawn Tile heat=0 immune to spread/vent same turn."""
    int_grid = _empty_int_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not (r == 2 and c == 2):
                int_grid[r][c] = 2
    board = create_board_with_grid(int_grid, seed=42)
    pos = board.spawn_tile()
    assert pos is not None
    r, c = pos
    assert board.grid[r][c] is not None
    assert board.grid[r][c].value in (2, 4)
    assert board.grid[r][c].heat == 0

    # After slide that moves, new tile heat==0
    int_grid2 = _empty_int_grid()
    int_grid2[0][0] = 2
    board2 = create_board_with_grid(int_grid2, seed=42)
    result = board2.slide(Direction.RIGHT)
    assert result.moved is True
    # Check all tiles have heat 0
    for rr in range(BOARD_SIZE):
        for cc in range(BOARD_SIZE):
            tile = result.grid[rr][cc]
            if tile is not None:
                assert tile.heat == 0, f"Tile at ({rr},{cc}) heat {tile.heat} !=0"


# ---------------------------------------------------------------------------
# No pygame import via sys.modules
# ---------------------------------------------------------------------------


def test_no_pygame_import() -> None:
    """AC-5 pygame not in sys.modules after import src.core.board."""
    # Ensure board already imported does not pull pygame
    assert "pygame" not in sys.modules, "pygame found in sys.modules"
    assert "pygame-ce" not in sys.modules
    assert "pygame_ce" not in sys.modules
    # Also after creating Board and sliding, still no pygame
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    _ = board.slide(Direction.LEFT)
    assert "pygame" not in sys.modules
    assert "pygame-ce" not in sys.modules


def test_headless_importable() -> None:
    """Board importable headlessly without DISPLAY."""
    # Import check
    from src.core.board import (  # noqa: F401
        BOARD_SIZE as BS,
        Board as B,
        Direction as D,
        MergeInfo as MI,
        SlideResult as SR,
        Tile as T,
        create_empty_grid as ceg,
    )

    assert BS == 5
    assert D.LEFT.value == "LEFT"
    # Board creation with Random works
    rng = random.Random(42)
    b = B(rng=rng)
    assert b.size == 5
    # create_empty_grid returns 5x5 None
    empty = ceg()
    assert len(empty) == 5
    assert all(len(row) == 5 for row in empty)
    assert all(cell is None for row in empty for cell in row)
    # Tile creation
    t = T(value=2, heat=0)
    assert t.value == 2
    assert t.heat == 0


# ---------------------------------------------------------------------------
# Phase 3 Sprint 1 — MergeInfo source_heats extension Q-004
# ---------------------------------------------------------------------------


def test_mergeinfo_source_heats_0_0() -> None:
    """AC-12: MergeInfo source_heats == (0,0) when merging two heat 0 tiles."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    # Create line with two tiles heat 0 same value
    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert len(result.merges) >= 1
    # Find merge with source_heats (0,0)
    found = False
    for m in result.merges:
        sh = getattr(m, "source_heats", None)
        assert sh is not None, "MergeInfo must have source_heats field"
        if sh == (0, 0):
            found = True
            break
    assert found, f"Expected source_heats (0,0) not found, got {[getattr(m,'source_heats',None) for m in result.merges]}"


def test_mergeinfo_source_heats_2_0() -> None:
    """AC-13: source_heats == (2,0) captured correctly."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=2)
    grid[0][1] = Tile(value=2, heat=0)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert len(result.merges) >= 1
    sh = getattr(result.merges[0], "source_heats", None)
    assert sh is not None
    # Order may be (2,0) or (0,2) depending on prev vs curr, but spec says (prev.heat, tile.heat)
    # prev is first tile in line, tile is second
    assert sh == (2, 0), f"Expected (2,0) got {sh}"


def test_mergeinfo_source_heats_1_1() -> None:
    """AC-14: source_heats == (1,1) captured correctly."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=4, heat=1)
    grid[0][1] = Tile(value=4, heat=1)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    sh = getattr(result.merges[0], "source_heats", None)
    assert sh == (1, 1), f"Expected (1,1) got {sh}"


def test_mergeinfo_source_heats_2_1() -> None:
    """AC-15: source_heats == (2,1) captured correctly."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=8, heat=2)
    grid[0][1] = Tile(value=8, heat=1)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    sh = getattr(result.merges[0], "source_heats", None)
    assert sh == (2, 1), f"Expected (2,1) got {sh}"


def test_process_line_source_heats() -> None:
    """AC-16: _process_line captures prev.heat and tile.heat before merge, new_heat max+gen clamped."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=4, heat=2)
    grid[0][1] = Tile(value=4, heat=1)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT)
    assert len(result.merges) == 1
    merge = result.merges[0]
    assert getattr(merge, "source_heats", None) == (2, 1)
    # new_heat = max(2,1) + heat_gen(8) = 2 + 1 =3 clamped 0-3
    # heat_gen for value 8 is floor(log2(8)/2)=1
    # Check merged tile heat in result grid
    merged_tile = result.grid[0][0]
    assert merged_tile is not None
    # new_heat should be max(prev.heat, curr.heat) + heat_gen clamped
    # max(2,1)=2 +1=3
    assert merged_tile.heat == 3, f"Expected new_heat 3, got {merged_tile.heat}"


def test_spawn_heat_0_immune_after_source_heats() -> None:
    """AC-19: spawn heat=0 immune still holds after source_heats extension."""
    from src.core.board import Board, Direction, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    rng = random.Random(42)
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    # All tiles heat 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = result.grid[r][c]
            if tile is not None:
                assert tile.heat == 0, f"Tile at ({r},{c}) heat {tile.heat} !=0 after spawn immunity"