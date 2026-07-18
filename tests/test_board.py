"""
tests/test_board.py — Headless comprehensive board tests with Tile dataclass + Q-004 final validation.

Covers slide correctness all 4 directions, one-merge-per-tile, chain prevention,
no-move detection, RNG injection, spawn distribution, spawn heat=0 immune,
no pygame import, plus Q-004 MergeInfo source_heats final validation per
pseudocode phase_3_sprint_2_wave1_tasks_1_2_code.md:
- source_heats (0,0)(2,0)(1,1)(2,1) captured correctly during _process_line
- new_heat max+gen clamped 0-3
- slide with source_heats integration

Production board: src/core/board.py with Tile dataclass value+heat,
Direction enum, SlideResult, MergeInfo with source_heats, BOARD_SIZE=5.
"""

from __future__ import annotations

import math
import random
import sys
from typing import List, Optional

from src.core.board import BOARD_SIZE, Board, Direction, Tile, create_empty_grid


def make_tile_grid(int_grid: List[List[Optional[int]]]) -> List[List[Optional[Tile]]]:
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
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            if v is None:
                result[r][c] = None
            else:
                h = (
                    heat_grid[r][c]
                    if r < len(heat_grid) and c < len(heat_grid[r]) and heat_grid[r][c] is not None
                    else 0
                )
                result[r][c] = Tile(value=v, heat=int(h))
    return result


def grid_to_int_values(grid: List[List[Optional[Tile]]]) -> List[List[Optional[int]]]:
    out: List[List[Optional[int]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[int]] = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            row.append(None if cell is None else cell.value)
        out.append(row)
    return out


def assert_grids_equal_values(
    actual: List[List[Optional[Tile]]],
    expected: List[List[Optional[int]]],
) -> None:
    actual_int = grid_to_int_values(actual)
    assert actual_int == expected, f"Grid values mismatch.\nActual:   {actual_int}\nExpected: {expected}"


def create_board_with_grid(int_grid: List[List[Optional[int]]], seed: int = 42) -> Board:
    tile_grid = make_tile_grid(int_grid)
    rng = random.Random(seed)
    return Board(grid=tile_grid, rng=rng)


def _count_tiles(grid: List[List[Optional[Tile]]]) -> int:
    cnt = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] is not None:
                cnt += 1
    return cnt


def _empty_int_grid() -> List[List[Optional[int]]]:
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def test_helpers_conversion() -> None:
    int_grid: List[List[Optional[int]]] = _empty_int_grid()
    int_grid[0] = [2, 4, None, 8, None]
    tile_grid = make_tile_grid(int_grid)
    assert tile_grid[0][0] is not None and tile_grid[0][0].value == 2
    assert tile_grid[0][0].heat == 0
    assert tile_grid[0][2] is None
    back = grid_to_int_values(tile_grid)
    assert back == int_grid


def test_slide_left_basic() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, None, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 4
    assert result.moved is True
    assert len(result.merges) == 1
    assert result.merges[0].value == 4
    assert result.merges[0].heat_gen == math.floor(math.log2(4) / 2)
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert _count_tiles(result.grid) == 2


def test_slide_right_basic() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, None, None, 2, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.RIGHT)
    assert result.score_delta == 4
    assert result.moved is True
    assert result.grid[0][4] is not None and result.grid[0][4].value == 4
    assert _count_tiles(result.grid) == 2


def test_slide_up_basic() -> None:
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    int_grid[1][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.UP)
    assert result.score_delta == 4
    assert result.moved is True
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4


def test_slide_down_basic() -> None:
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    int_grid[1][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.DOWN)
    assert result.score_delta == 4
    assert result.moved is True
    assert result.grid[4][0] is not None and result.grid[4][0].value == 4


def test_maximal_blocking() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 2, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0


def test_one_merge_per_tile() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 2, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 4
    assert len(result.merges) == 1
    assert result.grid[0][0] is not None and result.grid[0][0].value == 4
    assert result.grid[0][1] is not None and result.grid[0][1].value == 2


def test_one_merge_four_same() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 2, 2, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 8
    assert len(result.merges) == 2


def test_chain_prevention() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [4, 4, 8, None, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 8
    assert len(result.merges) == 1
    vals = grid_to_int_values(result.grid)
    flat = [v for row in vals for v in row if v is not None]
    assert 16 not in flat


def test_chain_prevention_complex() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 2, 4, 4, None]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.score_delta == 12
    assert len(result.merges) == 2


def test_no_move_empty_board() -> None:
    int_grid = _empty_int_grid()
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0


def test_no_move_full_no_merge() -> None:
    int_grid: List[List[Optional[int]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[int]] = []
        for c in range(BOARD_SIZE):
            row.append(2 if (r + c) % 2 == 0 else 4)
        int_grid.append(row)
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False


def test_no_move_already_aligned() -> None:
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 8, 16, 32]
    board = create_board_with_grid(int_grid, seed=42)
    result = board.slide(Direction.LEFT)
    assert result.moved is False


def test_rng_deterministic_seeded() -> None:
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    board1 = create_board_with_grid(int_grid, seed=123)
    board2 = create_board_with_grid(int_grid, seed=123)
    result1 = board1.slide(Direction.RIGHT)
    result2 = board2.slide(Direction.RIGHT)
    vals1 = grid_to_int_values(result1.grid)
    vals2 = grid_to_int_values(result2.grid)
    assert vals1 == vals2


def test_spawn_distribution_1000_runs() -> None:
    count_2 = 0
    count_4 = 0
    base_seed = 42
    for i in range(1000):
        int_grid = _empty_int_grid()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not (r == 2 and c == 2):
                    int_grid[r][c] = 2
        board = create_board_with_grid(int_grid, seed=base_seed + i)
        pos = board.spawn_tile()
        assert pos == (2, 2)
        spawned = board.grid[2][2]
        assert spawned is not None
        assert spawned.value in (2, 4)
        assert spawned.heat == 0
        if spawned.value == 2:
            count_2 += 1
        else:
            count_4 += 1
    assert 850 <= count_2 <= 950
    assert 50 <= count_4 <= 150


def test_spawn_heat_zero_immune() -> None:
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
    assert board.grid[r][c].heat == 0


def test_no_pygame_import() -> None:
    """AC-5 pygame not in sys.modules after import src.core.board via delta check."""
    before_has_pygame = "pygame" in sys.modules
    before_keys = set(sys.modules.keys())
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    board = create_board_with_grid(int_grid, seed=42)
    _ = board.slide(Direction.LEFT)
    after_keys = set(sys.modules.keys())
    new_keys = after_keys - before_keys
    if not before_has_pygame:
        pygame_new = [k for k in new_keys if "pygame" in k.lower()]
        assert not pygame_new, f"pygame leaked in delta: {pygame_new}"


def test_headless_importable() -> None:
    from src.core.board import BOARD_SIZE as BS, Board as B, Direction as D, Tile as T, create_empty_grid as ceg

    assert BS == 5
    assert D.LEFT.value == "LEFT"
    rng = random.Random(42)
    b = B(rng=rng)
    assert b.size == 5
    empty = ceg()
    assert len(empty) == 5
    t = T(value=2, heat=0)
    assert t.value == 2


# ---------------------------------------------------------------------------
# Q-004 Final Validation — MergeInfo source_heats per pseudocode
# ---------------------------------------------------------------------------


def test_mergeinfo_source_heats_0_0_captured() -> None:
    """AC-5: MergeInfo source_heats (0,0) captured correctly."""
    from src.core.board import Board, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert len(result.merges) >= 1
    found = False
    for m in result.merges:
        sh = getattr(m, "source_heats", None)
        assert sh is not None
        if sh == (0, 0):
            found = True
            break
    assert found


def test_mergeinfo_source_heats_2_0_captured() -> None:
    """AC-6: source_heats (2,0) captured."""
    from src.core.board import Board, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=2)
    grid[0][1] = Tile(value=2, heat=0)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert getattr(result.merges[0], "source_heats", None) == (2, 0)


def test_mergeinfo_source_heats_1_1_captured() -> None:
    """AC-7: source_heats (1,1) captured."""
    from src.core.board import Board, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=4, heat=1)
    grid[0][1] = Tile(value=4, heat=1)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert getattr(result.merges[0], "source_heats", None) == (1, 1)


def test_mergeinfo_source_heats_2_1_captured() -> None:
    """Additional: source_heats (2,1) captured."""
    from src.core.board import Board, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=8, heat=2)
    grid[0][1] = Tile(value=8, heat=1)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert getattr(result.merges[0], "source_heats", None) == (2, 1)


def test_new_heat_max_plus_gen_clamped_0_3() -> None:
    """AC-20: new_heat = max(prev.heat, tile.heat) + heat_gen clamped 0-3."""
    from src.core.board import Board, Tile, create_empty_grid

    # Case 1: value 4 heat_gen 1, prev 2 curr 0 => max 2 +1 =3 clamped 3
    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=2)
    grid[0][1] = Tile(value=2, heat=0)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert len(result.merges) == 1
    # After gen 3, vent edge -1 => 2, allow both 2 and 3
    merged_tile = result.grid[0][0]
    assert merged_tile is not None
    assert merged_tile.heat in (2, 3)

    # Case 2: value 64 heat_gen 3, prev 2 curr 1 => max 2+3=5 clamped 3
    grid2 = create_empty_grid()
    grid2[0][0] = Tile(value=32, heat=2)
    grid2[0][1] = Tile(value=32, heat=1)
    board2 = Board(grid=grid2, rng=random.Random(42))
    result2 = board2.slide(Direction.LEFT)
    assert len(result2.merges) == 1
    merged2 = result2.grid[0][0]
    assert merged2 is not None
    assert merged2.heat in (2, 3)


def test_slide_with_source_heats_integration() -> None:
    """Integration: Board slide returns SlideResult with merges source_heats correctly."""
    from src.core.board import Board, Tile, create_empty_grid

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    grid[0][1] = Tile(value=2, heat=0)
    board = Board(grid=grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert len(result.merges) >= 1
    assert getattr(result.merges[0], "source_heats", None) == (0, 0)
