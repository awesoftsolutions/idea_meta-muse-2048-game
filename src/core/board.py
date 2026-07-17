"""
src/core/board.py — Pure-Python Board spike with injectable RNG.

Implements 5x5 2048 board logic: slide/merge with compress-merge-compress
and merged-flag preventing double merge, spawn 90/10, no pygame import.

Allowed imports only: random, typing, copy.
"""
# CHANGELOG: Sprint 1 - Created pure-Python 5x5 Board spike with injectable RNG, slide/merge compress-merge-compress logic, spawn 90/10.

from __future__ import annotations

import copy
import random
from typing import List, Optional, Tuple

# Module constants
BOARD_SIZE: int = 5
DIRECTIONS: List[str] = ["UP", "DOWN", "LEFT", "RIGHT"]
DIRECTIONS_SET = set(DIRECTIONS)

# Type alias
Grid = List[List[Optional[int]]]


def _is_power_of_two(value: int) -> bool:
    """Check if value is power of two >=2."""
    return isinstance(value, int) and value >= 2 and (value & (value - 1)) == 0


def _validate_grid(grid: Optional[Grid]) -> None:
    """Validate 5x5 shape and power-of-two values, raise ValueError E002 if invalid."""
    if grid is None:
        return
    if len(grid) != BOARD_SIZE:
        raise ValueError(f"E002 MalformedGrid: Expected 5x5 grid, got {len(grid)} rows")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError(f"E002 MalformedGrid: Expected 5x5 grid, row {r} has length {len(row) if isinstance(row, list) else 'invalid'}")
        for c, cell in enumerate(row):
            if cell is None:
                continue
            if not _is_power_of_two(cell):
                raise ValueError(f"E002 MalformedGrid: Cell ({r},{c}) value {cell} is not power-of-two or None")


def _validate_direction(direction: str) -> None:
    """Validate direction in UP/DOWN/LEFT/RIGHT, raise ValueError E001 if invalid."""
    if direction not in DIRECTIONS_SET:
        raise ValueError(f"E001 InvalidDirection: '{direction}' invalid, valid directions are {DIRECTIONS}")


def create_empty_grid() -> Grid:
    """Create 5x5 grid filled with None."""
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


class Board:
    """Pure-Python 5x5 2048 board with injectable RNG."""

    def __init__(
        self,
        grid: Optional[Grid] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize 5x5 board, optional grid and injectable RNG."""
        if grid is None:
            self.grid: Grid = create_empty_grid()
        else:
            _validate_grid(grid)
            self.grid = copy.deepcopy(grid)

        if rng is None:
            self.rng = random.Random()
        else:
            self.rng = rng

        self.size = BOARD_SIZE

    def _validate_grid(self, grid: Grid) -> None:
        _validate_grid(grid)

    def _validate_direction(self, direction: str) -> None:
        _validate_direction(direction)

    def _extract_lines(self, grid: Grid, direction: str) -> List[List[Optional[int]]]:
        """Extract rows or columns as lines per direction."""
        lines: List[List[Optional[int]]] = []
        if direction == "LEFT":
            for r in range(BOARD_SIZE):
                line = list(grid[r])  # copy left to right
                lines.append(line)
        elif direction == "RIGHT":
            for r in range(BOARD_SIZE):
                line = list(reversed(grid[r]))  # reversed copy
                lines.append(line)
        elif direction == "UP":
            for c in range(BOARD_SIZE):
                line = [grid[r][c] for r in range(BOARD_SIZE)]  # top to bottom
                lines.append(line)
        elif direction == "DOWN":
            for c in range(BOARD_SIZE):
                line = [grid[r][c] for r in reversed(range(BOARD_SIZE))]  # bottom to top
                lines.append(line)
        return lines

    def _process_line(self, line: List[Optional[int]]) -> Tuple[List[Optional[int]], int]:
        """Compress-merge-compress single line with merged-flag, return (new_line, score_delta)."""
        # Step compress: filter None
        compressed: List[int] = [cell for cell in line if cell is not None]

        # Step merge with merged-flag preventing double merge
        new_line_vals: List[int] = []
        merged: List[bool] = []
        score = 0

        for val in compressed:
            if new_line_vals and new_line_vals[-1] == val and not merged[-1]:
                # Merge
                new_line_vals[-1] = val * 2
                merged[-1] = True
                score += new_line_vals[-1]
            else:
                new_line_vals.append(val)
                merged.append(False)

        # Pad None to BOARD_SIZE
        new_line: List[Optional[int]] = [v for v in new_line_vals]  # type: ignore
        while len(new_line) < BOARD_SIZE:
            new_line.append(None)

        return new_line, score

    def _reconstruct_grid(self, lines: List[List[Optional[int]]], direction: str) -> Grid:
        """Reconstruct 5x5 grid from processed lines per direction."""
        grid = create_empty_grid()

        if direction == "LEFT":
            for r in range(BOARD_SIZE):
                grid[r] = list(lines[r])

        elif direction == "RIGHT":
            for r in range(BOARD_SIZE):
                # lines[r] is left-aligned result of reversed input
                # Need right-aligned reconstruction preserving order
                non_none = [v for v in lines[r] if v is not None]
                # Right-align: Nones left, values right preserving order
                padded = [None] * (BOARD_SIZE - len(non_none)) + non_none
                grid[r] = padded

        elif direction == "UP":
            for c in range(BOARD_SIZE):
                for r in range(BOARD_SIZE):
                    grid[r][c] = lines[c][r]

        elif direction == "DOWN":
            for c in range(BOARD_SIZE):
                # lines[c] is bottom-to-top compressed left, index0 = bottommost
                # Reconstruct bottom-aligned: place lines[c][0] at bottom row 4, etc.
                for idx in range(BOARD_SIZE):
                    grid[BOARD_SIZE - 1 - idx][c] = lines[c][idx]

        return grid

    def _get_empty_cells(self, grid: Grid) -> List[Tuple[int, int]]:
        """Return list of (r,c) where grid is None."""
        empty: List[Tuple[int, int]] = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if grid[r][c] is None:
                    empty.append((r, c))
        return empty

    def _spawn_tile(self, grid: Grid, rng: random.Random) -> Grid:
        """Spawn 2 (90%) or 4 (10%) in random empty cell using rng, return new grid."""
        empty_cells = self._get_empty_cells(grid)
        if not empty_cells:
            return copy.deepcopy(grid)

        # Choose position
        # Use rng.choice if available, else randrange
        try:
            pos = rng.choice(empty_cells)
        except AttributeError:
            idx = rng.randrange(len(empty_cells))
            pos = empty_cells[idx]

        # Choose value 90% 2, 10% 4
        p = rng.random()
        value = 2 if p < 0.9 else 4

        new_grid = copy.deepcopy(grid)
        r, c = pos
        new_grid[r][c] = value
        return new_grid

    def slide(
        self, direction: str, rng: Optional[random.Random] = None
    ) -> Tuple[Grid, int, bool]:
        """Slide tiles in direction, return (new_grid, score_delta, moved)."""
        _validate_direction(direction)
        _validate_grid(self.grid)

        effective_rng = rng if rng is not None else self.rng

        lines = self._extract_lines(self.grid, direction)

        total_score = 0
        processed_lines: List[List[Optional[int]]] = []

        for line in lines:
            new_line, line_score = self._process_line(line)
            processed_lines.append(new_line)
            total_score += line_score

        new_grid = self._reconstruct_grid(processed_lines, direction)

        # Detect moved
        moved = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if new_grid[r][c] != self.grid[r][c]:
                    moved = True
                    break
            if moved:
                break

        if moved:
            empty_cells = self._get_empty_cells(new_grid)
            if empty_cells:
                new_grid_with_spawn = self._spawn_tile(new_grid, effective_rng)
            else:
                new_grid_with_spawn = new_grid
        else:
            new_grid_with_spawn = new_grid

        return new_grid_with_spawn, total_score, moved
