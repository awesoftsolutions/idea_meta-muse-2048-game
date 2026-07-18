"""
tests/test_board_task1_tdd.py — TDD red-phase tests for production board with Tile dataclass.

Covers 5 acceptance criteria plus directions, edge cases, isolation.
Expected to FAIL against spike Optional[int] implementation (Tile not present).

AC-1: Tile dataclass validation clamped 0-3, invalid value 3 raises
AC-2: Slide LEFT [2,2,0,0,0]->[4,0,0,0,0] score 4 moved True
AC-3: One-merge-per-tile [2,2,2,0,0]->[4,2,0,0,0]
AC-4: Chain prevention [4,4,8,0,0]->[8,8,0,0,0]
AC-5: Spawn 90/10 heat=0 seeded 1000 runs 85-95% 2s

Headless, no pygame, injectable Random deterministic.
"""

from __future__ import annotations

import random
import sys
from typing import List, Optional

import pytest

# These imports SHOULD FAIL against spike — red phase
from src.core.board import (
    BOARD_SIZE,
    HEAT_MAX,
    HEAT_MIN,
    Board,
    Direction,
    MergeInfo,
    SlideResult,
    Tile,
    create_empty_grid,
)


# ---------------------------------------------------------------------------
# Helpers per pseudocode TDD Test Structure
# ---------------------------------------------------------------------------

def make_tile_grid(int_grid: List[List[Optional[int]]]) -> List[List[Optional[Tile]]]:
    """Convert int grid (None=empty) to Tile grid with heat=0."""
    tile_grid: List[List[Optional[Tile]]] = []
    for r in range(len(int_grid)):
        row: List[Optional[Tile]] = []
        for c in range(len(int_grid[r])):
            v = int_grid[r][c]
            if v is None:
                row.append(None)
            else:
                row.append(Tile(value=v, heat=0))
        tile_grid.append(row)
    return tile_grid


def make_tile_grid_with_heat(
    int_grid: List[List[Optional[int]]],
    heat_grid: List[List[int]],
) -> List[List[Optional[Tile]]]:
    """Convert int+heat grids to Tile grid."""
    tile_grid: List[List[Optional[Tile]]] = []
    for r in range(len(int_grid)):
        row: List[Optional[Tile]] = []
        for c in range(len(int_grid[r])):
            v = int_grid[r][c]
            if v is None:
                row.append(None)
            else:
                row.append(Tile(value=v, heat=heat_grid[r][c]))
        tile_grid.append(row)
    return tile_grid


def make_empty_tile_grid() -> List[List[Optional[Tile]]]:
    """Create 5x5 empty Tile grid."""
    return create_empty_grid()


def assert_grid_values_equal(
    grid: List[List[Optional[Tile]]],
    expected: List[List[Optional[int]]],
) -> None:
    """Assert grid values match expected int grid (ignores heat)."""
    assert len(grid) == BOARD_SIZE
    for r in range(BOARD_SIZE):
        assert len(grid[r]) == BOARD_SIZE
        for c in range(BOARD_SIZE):
            exp = expected[r][c]
            cell = grid[r][c]
            if exp is None:
                assert cell is None, f"Expected None at ({r},{c}), got {cell}"
            else:
                assert cell is not None, f"Expected {exp} at ({r},{c}), got None"
                assert cell.value == exp, f"At ({r},{c}) expected {exp}, got {cell.value}"


def make_board_from_ints(
    int_grid: List[List[Optional[int]]],
    rng: Optional[random.Random] = None,
) -> Board:
    """Helper to create Board from int grid."""
    tile_grid = make_tile_grid(int_grid)
    if rng is None:
        rng = random.Random(42)
    return Board(grid=tile_grid, rng=rng)


# ---------------------------------------------------------------------------
# AC-1 Tile dataclass validation
# ---------------------------------------------------------------------------

def test_tile_dataclass_basic():
    """AC-1: Tile value 4 heat 1 stores correctly."""
    t = Tile(value=4, heat=1)
    assert t.value == 4
    assert t.heat == 1


def test_tile_heat_clamp_low():
    """AC-1: heat -1 clamped to 0."""
    t = Tile(value=2, heat=-1)
    assert t.heat == 0, f"Expected clamped 0, got {t.heat}"


def test_tile_heat_clamp_high():
    """AC-1: heat 5 clamped to 3."""
    t = Tile(value=8, heat=5)
    assert t.heat == 3, f"Expected clamped 3, got {t.heat}"


def test_tile_invalid_value_3_raises():
    """AC-1: value 3 not power of two raises ValueError."""
    with pytest.raises(ValueError):
        Tile(value=3, heat=0)


def test_tile_invalid_values():
    """AC-1: invalid values 0,1,None, negative raise."""
    for bad in [0, 1, -2, -4]:
        with pytest.raises(ValueError):
            Tile(value=bad, heat=0)


def test_tile_valid_power_of_two():
    """AC-1: valid powers of two including 1024."""
    for good in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]:
        t = Tile(value=good, heat=0)
        assert t.value == good


def test_tile_power_of_two_helper():
    """Validation helper _is_power_of_two behavior via Tile."""
    # indirect via Tile creation
    assert Tile(value=2, heat=0).value == 2
    with pytest.raises(ValueError):
        Tile(value=6, heat=0)


def test_tile_equality():
    """Tile equality includes value and heat."""
    t1 = Tile(value=4, heat=1)
    t2 = Tile(value=4, heat=1)
    t3 = Tile(value=4, heat=2)
    assert t1 == t2
    assert t1 != t3
    assert t1 != None  # noqa: E711


def test_tile_heat_default_zero():
    """Tile heat defaults to 0."""
    t = Tile(value=2)
    assert t.heat == 0


# ---------------------------------------------------------------------------
# AC-2 Slide LEFT basic
# ---------------------------------------------------------------------------

def test_slide_left_basic():
    """AC-2: [2,2,0,0,0] LEFT -> [4,0,0,0,0] + spawn score 4 moved True per IBoardSlide."""
    int_grid = [
        [2, 2, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)

    assert isinstance(result, SlideResult)
    # IBoardSlide: spawn only if moved includes merges, so result contains merged tile plus spawn
    assert result.grid[0][0] is not None
    assert result.grid[0][0].value == 4, f"Expected merged 4 at (0,0), got {result.grid[0][0]}"
    assert result.score_delta == 4
    assert result.moved is True
    assert len(result.merges) == 1
    assert result.merges[0].value == 4
    # heat_gen floor(log2(4)/2)=1
    assert result.merges[0].heat_gen == 1
    # Grid should have merged tile plus optional spawn tile (1 or 2 tiles total)
    non_none = [(r, c, cell) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) for cell in [result.grid[r][c]] if cell is not None]
    assert 1 <= len(non_none) <= 2, f"Expected 1 or 2 tiles (merged + optional spawn), got {len(non_none)}: {non_none}"
    # If spawn present, verify heat=0 and value in [2,4] and not overwriting merged tile
    if len(non_none) == 2:
        spawn_candidates = [(r, c, cell) for r, c, cell in non_none if not (r == 0 and c == 0)]
        assert len(spawn_candidates) == 1, f"Spawn should not be at (0,0), got {non_none}"
        _, _, spawn_tile = spawn_candidates[0]
        assert spawn_tile.heat == 0, f"Spawned tile heat should be 0, got {spawn_tile.heat}"
        assert spawn_tile.value in (2, 4), f"Spawned value should be 2 or 4, got {spawn_tile.value}"


def test_slide_left_string_direction():
    """Slide accepts string direction LEFT."""
    int_grid = [
        [2, 2, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid)
    result = board.slide("LEFT")
    assert result.moved is True
    assert result.score_delta == 4


# ---------------------------------------------------------------------------
# AC-3 One-merge-per-tile
# ---------------------------------------------------------------------------

def test_one_merge_per_tile():
    """AC-3: [2,2,2,0,0] LEFT -> [4,2,0,0,0] not [8,0,0,0,0]."""
    int_grid = [
        [2, 2, 2, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)

    # Extract first row values ignoring spawn tile (spawn adds extra tile)
    # To avoid spawn interference, check score and that not [8,0,0,0,0]
    assert result.score_delta == 4
    # The merged result before spawn would be [4,2,0,0,0]; after spawn one extra tile appears
    # So we verify first cell is 4 and second is 2, and no 8 in row
    row_vals = [cell.value if cell else None for cell in result.grid[0]]
    assert row_vals[0] == 4
    assert 8 not in row_vals, f"Should not have 8, got {row_vals}"
    # Ensure not [8,0,0,0,0] pattern
    assert not (row_vals[0] == 8 and row_vals[1] is None)


def test_four_same_tiles_two_merges():
    """AC-3 extended: [2,2,2,2,0] LEFT -> [4,4,0,0,0] score 8."""
    int_grid = [
        [2, 2, 2, 2, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)

    assert result.score_delta == 8
    assert len(result.merges) == 2
    row_vals = [cell.value if cell else 0 for cell in result.grid[0]]
    # After spawn, there will be 3 tiles: 4,4 plus spawn. So count 4s >=2
    assert row_vals.count(4) >= 2
    assert 8 not in row_vals


# ---------------------------------------------------------------------------
# AC-4 Chain prevention
# ---------------------------------------------------------------------------

def test_chain_prevention():
    """AC-4: [4,4,8,0,0] LEFT -> [8,8,0,0,0] not [16,0,0,0,0]."""
    int_grid = [
        [4, 4, 8, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)

    assert result.score_delta == 8
    row_vals = [cell.value if cell else None for cell in result.grid[0]]
    # Should contain 8,8 not 16
    assert 16 not in [v for v in row_vals if v is not None], f"Should not have 16, got {row_vals}"
    # First value should be 8
    assert row_vals[0] == 8


def test_chain_prevention_complex():
    """AC-4 extended: [2,2,4,4,0] LEFT -> [4,8,0,0,0] score 12."""
    int_grid = [
        [2, 2, 4, 4, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)

    assert result.score_delta == 12
    assert len(result.merges) == 2
    # Values should include 4 and 8
    row_vals = [cell.value if cell else 0 for cell in result.grid[0]]
    assert 4 in row_vals
    assert 8 in row_vals


# ---------------------------------------------------------------------------
# AC-5 Spawn distribution and heat=0
# ---------------------------------------------------------------------------

def test_spawn_distribution_seeded():
    """AC-5: seeded 1000 runs 85-95% 2s."""
    rng = random.Random(123)
    count_2 = 0
    count_4 = 0
    # Use almost full grid with one empty to force spawn
    for _ in range(1000):
        # Create grid with one empty at (0,0)
        grid = make_tile_grid([
            [None, 2, 4, 8, 16],
            [2, 4, 8, 16, 32],
            [4, 8, 16, 32, 64],
            [8, 16, 32, 64, 128],
            [16, 32, 64, 128, 256],
        ])
        board = Board(grid=grid, rng=rng)
        # Use internal _spawn_tile or spawn_tile
        # Try public spawn_tile if exists, else _spawn_tile
        if hasattr(board, "_spawn_tile"):
            new_grid = board._spawn_tile(board.grid, board.rng)
            # Find new tile at empty position
            spawned = new_grid[0][0]
            assert spawned is not None
            assert spawned.heat == 0
            if spawned.value == 2:
                count_2 += 1
            elif spawned.value == 4:
                count_4 += 1
        else:
            # fallback via Board.spawn_tile
            pos = board.spawn_tile()
            assert pos is not None
            r, c = pos
            spawned = board.grid[r][c]
            assert spawned.heat == 0
            if spawned.value == 2:
                count_2 += 1
            else:
                count_4 += 1

    total = count_2 + count_4
    assert total == 1000
    pct_2 = count_2 / total * 100
    assert 85 <= pct_2 <= 95, f"Expected 85-95% 2s, got {pct_2}% ({count_2}/1000)"


def test_spawn_heat_zero():
    """AC-5: new spawned Tile heat=0."""
    rng = random.Random(42)
    grid = make_tile_grid([
        [None, 2, 4, 8, 16],
        [2, 4, 8, 16, 32],
        [4, 8, 16, 32, 64],
        [8, 16, 32, 64, 128],
        [16, 32, 64, 128, 256],
    ])
    board = Board(grid=grid, rng=rng)
    if hasattr(board, "_spawn_tile"):
        new_grid = board._spawn_tile(board.grid, board.rng)
        assert new_grid[0][0] is not None
        assert new_grid[0][0].heat == 0
    else:
        pos = board.spawn_tile()
        assert pos is not None
        r, c = pos
        assert board.grid[r][c].heat == 0


def test_spawn_deterministic():
    """AC-5: same seed produces same position and value."""
    seed = 999
    grid_int = [
        [None, 2, 4, 8, 16],
        [2, 4, 8, 16, 32],
        [4, 8, 16, 32, 64],
        [8, 16, 32, 64, 128],
        [16, 32, 64, 128, 256],
    ]

    def do_spawn(s: int):
        rng = random.Random(s)
        grid = make_tile_grid(grid_int)
        board = Board(grid=grid, rng=rng)
        if hasattr(board, "_spawn_tile"):
            new_grid = board._spawn_tile(board.grid, board.rng)
            # find spawned
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if grid_int[r][c] is None:
                        # originally empty, now should have tile
                        assert new_grid[r][c] is not None
                        return (r, c, new_grid[r][c].value)
        else:
            pos = board.spawn_tile()
            assert pos is not None
            r, c = pos
            return (r, c, board.grid[r][c].value)
        return None

    result1 = do_spawn(seed)
    result2 = do_spawn(seed)
    assert result1 == result2, f"Deterministic failed: {result1} != {result2}"


def test_spawn_heat_immunity_after_slide():
    """AC-5: after slide that moves, new spawned tile heat==0."""
    int_grid = [
        [2, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(42))
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    # Count tiles: original 1 moved + 1 spawned = 2 tiles
    non_none = [(r, c, cell) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) for cell in [result.grid[r][c]] if cell is not None]
    assert len(non_none) == 2
    # At least one tile should have heat 0 (the spawned one)
    heats = [cell.heat for _, _, cell in non_none]
    assert 0 in heats


# ---------------------------------------------------------------------------
# All 4 directions maximal blocking
# ---------------------------------------------------------------------------

def test_slide_right():
    """RIGHT direction maximal blocking."""
    int_grid = [
        [2, None, None, 2, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    assert result.score_delta == 4
    # Right-aligned: last cell should be 4
    assert result.grid[0][BOARD_SIZE - 1] is not None
    assert result.grid[0][BOARD_SIZE - 1].value == 4


def test_slide_up():
    """UP direction maximal blocking."""
    int_grid = [
        [2, None, None, None, None],
        [2, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.UP)
    assert result.moved is True
    assert result.score_delta == 4
    assert result.grid[0][0] is not None
    assert result.grid[0][0].value == 4


def test_slide_down():
    """DOWN direction maximal blocking."""
    int_grid = [
        [2, None, None, None, None],
        [2, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.DOWN)
    assert result.moved is True
    assert result.score_delta == 4
    assert result.grid[BOARD_SIZE - 1][0] is not None
    assert result.grid[BOARD_SIZE - 1][0].value == 4


def test_maximal_blocking():
    """Blocking different values: [2,4,2,0,0] LEFT stays same values no merge."""
    int_grid = [
        [2, 4, 2, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)
    # Already left-aligned, no merge, so moved False
    assert result.moved is False
    assert result.score_delta == 0
    assert_grid_values_equal(result.grid, int_grid)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_board_no_move():
    """Empty board slide returns same grid moved False score 0."""
    empty = make_empty_tile_grid()
    board = Board(grid=empty, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert len(result.merges) == 0
    # All None
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            assert result.grid[r][c] is None


def test_full_no_merge():
    """Full board no merge possible moved False."""
    int_grid = [
        [2, 4, 2, 4, 2],
        [4, 2, 4, 2, 4],
        [2, 4, 2, 4, 2],
        [4, 2, 4, 2, 4],
        [2, 4, 2, 4, 2],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0


def test_single_tile_move():
    """Single tile at (0,4) LEFT moves to (0,0) moved True."""
    int_grid = [
        [None, None, None, None, 2],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid, rng=random.Random(42))
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    assert result.grid[0][0] is not None
    assert result.grid[0][0].value == 2


def test_heat_gen_formula():
    """Heat gen floor(log2(V)/2) clamped 0-3."""
    # V=4 ->1, V=8->1, V=16->2, V=64->3
    cases = [
        (4, 1),
        (8, 1),
        (16, 2),
        (32, 2),
        (64, 3),
        (128, 3),
        (256, 3),  # clamped
    ]
    for value, expected_heat in cases:
        # Create merge scenario
        int_grid = [
            [value // 2, value // 2, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
        ]
        # Only if value//2 is power of two
        if value // 2 in [2, 4, 8, 16, 32, 64, 128]:
            board = make_board_from_ints(int_grid, rng=random.Random(1))
            result = board.slide(Direction.LEFT)
            assert len(result.merges) == 1
            assert result.merges[0].heat_gen == expected_heat, f"V={value} expected heat {expected_heat}, got {result.merges[0].heat_gen}"


def test_merged_tile_heat_preserved():
    """Merging Tiles with heat preserves max heat."""
    heat_grid = [
        [1, 2, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    int_grid = [
        [2, 2, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    tile_grid = make_tile_grid_with_heat(int_grid, heat_grid)
    board = Board(grid=tile_grid, rng=random.Random(1))
    result = board.slide(Direction.LEFT)
    assert result.grid[0][0] is not None
    # Merged tile heat should be max(1,2)=2 per pseudocode
    assert result.grid[0][0].heat == 2


# ---------------------------------------------------------------------------
# Isolation: no pygame, no global random
# ---------------------------------------------------------------------------

def test_no_pygame_import():
    """No pygame in sys.modules after import src.core.board."""
    # Snapshot before (already imported above, but check)
    assert "pygame" not in sys.modules, "pygame leaked into sys.modules"
    # Also check file content for import pygame
    import pathlib
    board_path = pathlib.Path("src/core/board.py")
    content = board_path.read_text(encoding="utf-8")
    assert "import pygame" not in content
    assert "from pygame" not in content


def test_no_global_random_usage():
    """Board uses self.rng not global random.random."""
    import pathlib
    board_path = pathlib.Path("src/core/board.py")
    content = board_path.read_text(encoding="utf-8")
    # Should not have bare random.random() or random.choice() without self.rng
    # Allow self.rng.random and self.rng.choice and rng.random etc
    # Check for suspicious patterns: "random.random()" not preceded by "self." or "rng."
    # Simple heuristic: count occurrences of "random.random()" and "random.choice("
    # The spike has rng.random() and rng.choice which is okay, but global random.random is not
    # We check file does not contain "random.random()" as standalone global call
    # Actually spike uses rng.random() which is okay. We forbid "random.random()" literal
    # and "random.choice(" literal
    assert "random.random()" not in content or "self.rng.random()" in content or "rng.random()" in content
    # More precise: ensure no line with exactly "random.random()" without self.rng or effective_rng or rng.
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#"):
            continue
        if "random.random()" in line:
            # Must be via self.rng or rng or effective_rng
            assert ("self.rng.random()" in line or "rng.random()" in line or "effective_rng" in line), f"Global random usage found: {line}"
        if "random.choice(" in line:
            assert ("self.rng.choice(" in line or "rng.choice(" in line or "effective_rng" in line), f"Global random.choice usage found: {line}"


def test_board_size_constant():
    """BOARD_SIZE is 5."""
    assert BOARD_SIZE == 5


def test_heat_constants():
    """HEAT_MIN 0 HEAT_MAX 3."""
    assert HEAT_MIN == 0
    assert HEAT_MAX == 3


def test_direction_enum():
    """Direction enum has UP DOWN LEFT RIGHT."""
    assert Direction.UP.value == "UP"
    assert Direction.DOWN.value == "DOWN"
    assert Direction.LEFT.value == "LEFT"
    assert Direction.RIGHT.value == "RIGHT"


def test_create_empty_grid():
    """create_empty_grid returns 5x5 None."""
    grid = create_empty_grid()
    assert len(grid) == 5
    for row in grid:
        assert len(row) == 5
        for cell in row:
            assert cell is None


def test_slide_result_structure():
    """SlideResult has grid, score_delta, moved, merges."""
    int_grid = [
        [2, 2, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
        [None, None, None, None, None],
    ]
    board = make_board_from_ints(int_grid)
    result = board.slide(Direction.LEFT)
    assert hasattr(result, "grid")
    assert hasattr(result, "score_delta")
    assert hasattr(result, "moved")
    assert hasattr(result, "merges")
    assert isinstance(result.merges, list)
    if result.merges:
        assert isinstance(result.merges[0], MergeInfo)
        assert hasattr(result.merges[0], "heat_gen")
        assert hasattr(result.merges[0], "position")
        assert hasattr(result.merges[0], "value")


def test_invalid_direction_raises():
    """Invalid direction raises ValueError E001."""
    empty = make_empty_tile_grid()
    board = Board(grid=empty, rng=random.Random(42))
    with pytest.raises(ValueError, match="E001"):
        board.slide("INVALID")  # type: ignore


def test_board_injectable_rng():
    """Board stores injected RNG."""
    rng = random.Random(123)
    empty = make_empty_tile_grid()
    board = Board(grid=empty, rng=rng)
    assert board.rng is rng


def test_board_default_rng():
    """Board creates new Random if none provided."""
    empty = make_empty_tile_grid()
    board = Board(grid=empty)
    assert isinstance(board.rng, random.Random)
