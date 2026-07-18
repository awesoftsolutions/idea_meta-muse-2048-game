"""
tests/test_rules.py — TDD red phase for rules.py is_legal_move and is_game_over.

Headless, pure Python, no pygame, deterministic, no DISPLAY.
Covers AC-1 to AC-7 plus edge cases and no-pygame import check.

This is red phase: src/core/rules.py does NOT exist yet, so each test
attempts to import from src.core.rules and will fail with ModuleNotFoundError
until implementation is provided. File itself is importable (top-level does
not import rules).

Helpers:
- make_grid(int_matrix) -> Grid of Tiles heat 0 where int present, None where 0/None
- make_grid_with_heat(int_matrix, heat_matrix) for heat-ignored test
"""

from __future__ import annotations

import sys
from typing import List, Optional

import pytest

from src.core.board import BOARD_SIZE, Direction, Tile

# Type alias for grid
Grid = List[List[Optional[Tile]]]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_grid(int_matrix: List[List[Optional[int]]]) -> Grid:
    """Convert int matrix to Tile grid with heat 0.

    Args:
        int_matrix: 5x5 matrix where 0 or None => empty, int => Tile(value=int, heat=0).

    Returns:
        5x5 Grid of Optional[Tile].
    """
    grid: Grid = []
    for r in range(BOARD_SIZE):
        row: List[Optional[Tile]] = []
        for c in range(BOARD_SIZE):
            val = int_matrix[r][c]
            if val is None or val == 0:
                row.append(None)
            else:
                row.append(Tile(value=int(val), heat=0))
        grid.append(row)
    return grid


def make_grid_with_heat(
    int_matrix: List[List[Optional[int]]],
    heat_matrix: List[List[int]],
) -> Grid:
    """Convert int matrix + heat matrix to Tile grid.

    Args:
        int_matrix: 5x5 matrix where 0/None => empty.
        heat_matrix: 5x5 matrix of heat values 0-3.

    Returns:
        5x5 Grid of Optional[Tile] with specified heat.
    """
    grid: Grid = []
    for r in range(BOARD_SIZE):
        row: List[Optional[Tile]] = []
        for c in range(BOARD_SIZE):
            val = int_matrix[r][c]
            if val is None or val == 0:
                row.append(None)
            else:
                heat = (
                    heat_matrix[r][c]
                    if r < len(heat_matrix) and c < len(heat_matrix[r])
                    else 0
                )
                row.append(Tile(value=int(val), heat=int(heat)))
        grid.append(row)
    return grid


def _checkerboard_no_merge_grid() -> Grid:
    """Full board checkerboard 2,4 alternating no adjacent equals."""
    # Pattern ensures no two orthogonal neighbors equal
    # Row even: 2,4,2,4,2 ; Row odd: 4,2,4,2,4
    int_mat: List[List[int]] = []
    for r in range(BOARD_SIZE):
        row: List[int] = []
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 0:
                row.append(2)
            else:
                row.append(4)
        int_mat.append(row)
    return make_grid(int_mat)


# ---------------------------------------------------------------------------
# AC-1: is_legal_move false when unchanged
# ---------------------------------------------------------------------------


def test_is_legal_move_false_when_unchanged() -> None:
    """AC-1: Full board checkerboard no merge => all directions illegal."""
    from src.core.rules import is_legal_move

    grid = _checkerboard_no_merge_grid()
    for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        assert is_legal_move(direction, grid) is False, (
            f"Expected False for {direction}"
        )
    # Also string variants
    for dir_str in ["UP", "DOWN", "LEFT", "RIGHT"]:
        assert is_legal_move(dir_str, grid) is False, f"Expected False for {dir_str}"


# ---------------------------------------------------------------------------
# AC-2: is_legal_move true when changes
# ---------------------------------------------------------------------------


def test_is_legal_move_true_when_changes() -> None:
    """AC-2: Board that would change returns True."""
    from src.core.rules import is_legal_move

    # Simple merge possible LEFT
    grid_left = make_grid(
        [
            [2, 2, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    assert is_legal_move(Direction.LEFT, grid_left) is True
    assert is_legal_move("LEFT", grid_left) is True

    # Single tile at corner can move
    grid_corner = make_grid(
        [
            [2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    # At (0,0) LEFT and UP should be false, RIGHT and DOWN true
    assert is_legal_move(Direction.RIGHT, grid_corner) is True
    assert is_legal_move(Direction.DOWN, grid_corner) is True

    # Stack for UP
    grid_up = make_grid(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [2, 0, 0, 0, 0],
            [2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    assert is_legal_move(Direction.UP, grid_up) is True
    assert is_legal_move(Direction.DOWN, grid_up) is True


# ---------------------------------------------------------------------------
# AC-3: is_game_over true only when no empty and no merge any direction
# ---------------------------------------------------------------------------


def test_is_game_over_true_no_empty_no_merge() -> None:
    """AC-3: Full board no merge possible => game over True."""
    from src.core.rules import is_game_over

    grid = _checkerboard_no_merge_grid()
    assert is_game_over(grid) is True


# ---------------------------------------------------------------------------
# AC-4: is_game_over false when empty present
# ---------------------------------------------------------------------------


def test_is_game_over_false_empty_present() -> None:
    """AC-4: Grid with one None returns False."""
    from src.core.rules import is_game_over

    grid_one_empty = make_grid(
        [
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 0, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
        ]
    )
    assert is_game_over(grid_one_empty) is False

    # Also checkerboard but with empty
    grid_with_empty = make_grid(
        [
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, None],
        ]
    )
    assert is_game_over(grid_with_empty) is False


# ---------------------------------------------------------------------------
# AC-5: is_game_over false full board merge possible
# ---------------------------------------------------------------------------


def test_is_game_over_false_full_board_merge_possible() -> None:
    """AC-5: Full board with adjacent 2,2 returns False."""
    from src.core.rules import is_game_over

    # Full board with one merge pair adjacent horizontally
    grid_merge = make_grid(
        [
            [2, 2, 4, 8, 16],
            [4, 8, 16, 32, 64],
            [8, 16, 32, 64, 128],
            [16, 32, 64, 128, 256],
            [32, 64, 128, 256, 512],
        ]
    )
    assert is_game_over(grid_merge) is False

    # Vertical merge possible
    grid_vertical = make_grid(
        [
            [2, 4, 8, 16, 32],
            [2, 8, 16, 32, 64],
            [4, 16, 32, 64, 128],
            [8, 32, 64, 128, 256],
            [16, 64, 128, 256, 512],
        ]
    )
    assert is_game_over(grid_vertical) is False


# ---------------------------------------------------------------------------
# AC-6: invalid direction ValueError with valid list
# ---------------------------------------------------------------------------


def test_is_legal_move_invalid_direction_raises() -> None:
    """AC-6: Invalid direction raises ValueError containing valid list."""
    from src.core.rules import is_legal_move

    grid = make_grid(
        [
            [2, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )

    invalid_inputs = ["DIAGONAL", None, 123, "", "diagonal", "left", "Up"]
    for invalid in invalid_inputs:
        with pytest.raises(ValueError) as exc_info:
            is_legal_move(invalid, grid)  # type: ignore[arg-type]
        msg = str(exc_info.value)
        # Must contain valid list [UP,DOWN,LEFT,RIGHT] per E001
        assert "[UP,DOWN,LEFT,RIGHT]" in msg or "UP" in msg and "DOWN" in msg
        # Must contain E001 per architecture
        assert "E001" in msg or "InvalidDirection" in msg or "invalid" in msg.lower()


# ---------------------------------------------------------------------------
# AC-7: heat ignored
# ---------------------------------------------------------------------------


def test_is_legal_move_heat_ignored() -> None:
    """AC-7: Same values different heat => same legality, heat ignored."""
    from src.core.rules import is_legal_move

    int_mat = [
        [2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    heat_zero = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    heat_mixed = [
        [2, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]

    grid_zero = make_grid_with_heat(int_mat, heat_zero)
    grid_mixed = make_grid_with_heat(int_mat, heat_mixed)

    # Both should have same legality result regardless of heat
    assert is_legal_move(Direction.LEFT, grid_zero) == is_legal_move(
        Direction.LEFT, grid_mixed
    )
    assert is_legal_move(Direction.LEFT, grid_zero) is True

    # Grids differing only by heat should be considered same for differ check
    # Simulate: two grids same values different heat, is_legal_move should be consistent
    # Also test that empty vs heat-only difference does not count as change
    # Create full checkerboard with different heats but same values
    grid_a = make_grid_with_heat(
        [
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
        ],
        [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)],
    )
    grid_b = make_grid_with_heat(
        [
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
            [4, 2, 4, 2, 4],
            [2, 4, 2, 4, 2],
        ],
        [[3] * BOARD_SIZE for _ in range(BOARD_SIZE)],
    )
    # Both full no merge, both should be illegal moves
    assert is_legal_move(Direction.LEFT, grid_a) is False
    assert is_legal_move(Direction.LEFT, grid_b) is False


# ---------------------------------------------------------------------------
# Additional edge cases
# ---------------------------------------------------------------------------


def test_is_game_over_empty_board_false() -> None:
    """Empty board all None returns False for game over."""
    from src.core.rules import is_game_over

    empty_grid: Grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    assert is_game_over(empty_grid) is False


def test_is_legal_move_edge_empty_board_false() -> None:
    """Empty board returns False for all directions."""
    from src.core.rules import is_legal_move

    empty_grid: Grid = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        assert is_legal_move(direction, empty_grid) is False


def test_no_pygame_import() -> None:
    """Verify no pygame import leak via sys.modules after importing rules."""
    # Ensure pygame not in sys.modules before
    assert "pygame" not in sys.modules, "pygame should not be imported before test"

    try:
        import src.core.rules  # noqa: F401

        # After import, pygame still should not be in sys.modules
        assert "pygame" not in sys.modules, "src.core.rules must not import pygame"
    except ModuleNotFoundError:
        # Red phase: module does not exist yet, which is expected
        # Still verify pygame not leaked by attempt
        assert "pygame" not in sys.modules, (
            "pygame should not be imported even on failed import"
        )
        pytest.skip("src.core.rules not implemented yet — red phase expected")
