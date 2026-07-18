"""
src/core/rules.py — IRules contract implementation.

Implements is_legal_move and is_game_over pure Python headless,
no pygame, no spawn, no heat phases during legality simulation.
Compress-merge-compress with merged-flag, value-only diff ignoring heat.
"""

from __future__ import annotations

from typing import List, Optional

from src.core.board import BOARD_SIZE, Direction, Tile

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_DIRECTIONS: List[str] = ["UP", "DOWN", "LEFT", "RIGHT"]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_power_of_two(value: int) -> bool:
    """Check if value is power of two >=2.

    Args:
        value: Integer to check.

    Returns:
        True if power of two >=2.
    """
    if not isinstance(value, int):
        return False
    if value < 2:
        return False
    return (value & (value - 1)) == 0


def _validate_direction(direction) -> Direction:
    """Validate direction per E001.

    Args:
        direction: Direction enum or string.

    Returns:
        Direction enum.

    Raises:
        ValueError: If direction invalid (E001).
    """
    if isinstance(direction, Direction):
        return direction
    if isinstance(direction, str) and direction in VALID_DIRECTIONS:
        return Direction(direction)
    raise ValueError(
        f"E001 InvalidDirection: '{direction}' invalid, "
        f"valid directions are [UP,DOWN,LEFT,RIGHT]"
    )


def _validate_grid(grid: Optional[List[List[Optional[Tile]]]]) -> None:
    """Validate 5x5 grid shape and Tile types per E002.

    Args:
        grid: Grid to validate.

    Raises:
        ValueError: If grid malformed (E002).
    """
    if grid is None:
        raise ValueError("E002 MalformedGrid: grid is None, expected 5x5")
    if not isinstance(grid, list) or len(grid) != BOARD_SIZE:
        raise ValueError(
            f"E002 MalformedGrid: Expected 5x5 grid, got "
            f"{len(grid) if isinstance(grid, list) else 'invalid'} rows"
        )
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            raise ValueError(
                f"E002 MalformedGrid: Expected 5x5 grid, row {r} has length "
                f"{len(row) if isinstance(row, list) else 'invalid'}"
            )
        for c, cell in enumerate(row):
            if cell is None:
                continue
            if not isinstance(cell, Tile):
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) not Tile or None"
                )
            if not _is_power_of_two(cell.value):
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) value "
                    f"{cell.value} not power-of-two"
                )
            if not isinstance(cell.heat, int):
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) heat not int"
                )
            if cell.heat < 0 or cell.heat > 3:
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) heat "
                    f"{cell.heat} out of range 0-3"
                )


def _deep_copy_grid(
    grid: List[List[Optional[Tile]]],
) -> List[List[Optional[Tile]]]:
    """Deep copy grid via Tile(value,heat).

    Args:
        grid: Source grid.

    Returns:
        New 5x5 grid copy.
    """
    new_grid: List[List[Optional[Tile]]] = []
    for r in range(BOARD_SIZE):
        row: List[Optional[Tile]] = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is None:
                row.append(None)
            else:
                row.append(Tile(value=cell.value, heat=cell.heat))
        new_grid.append(row)
    return new_grid


def _extract_line_for_rules(
    grid: List[List[Optional[Tile]]],
    direction: Direction,
    index: int,
) -> List[Optional[Tile]]:
    """Extract line per direction for simulation.

    Args:
        grid: Source grid.
        direction: Direction enum.
        index: Row or column index.

    Returns:
        List of Optional[Tile] length BOARD_SIZE.
    """
    if direction == Direction.LEFT:
        return list(grid[index])
    if direction == Direction.RIGHT:
        return list(reversed(grid[index]))
    if direction == Direction.UP:
        return [grid[r][index] for r in range(BOARD_SIZE)]
    # DOWN
    return [grid[r][index] for r in reversed(range(BOARD_SIZE))]


def _process_line_no_spawn(
    line: List[Optional[Tile]],
) -> List[Optional[Tile]]:
    """Compress-merge-compress with merged-flag, no spawn, no heat_gen.

    Args:
        line: Input line length BOARD_SIZE.

    Returns:
        Processed line left-aligned length BOARD_SIZE.
    """
    # Step 1 compress: filter None, keep Tiles with value
    compressed: List[Tile] = [
        Tile(value=t.value, heat=t.heat) for t in line if t is not None
    ]

    # Step 2 merge with merged-flag
    new_vals: List[Tile] = []
    merged_flags: List[bool] = []

    for tile in compressed:
        if (
            new_vals
            and new_vals[-1].value == tile.value
            and not merged_flags[-1]
        ):
            # Merge
            new_value = new_vals[-1].value * 2
            new_heat = max(new_vals[-1].heat, tile.heat)
            new_tile = Tile(value=new_value, heat=new_heat)
            new_vals[-1] = new_tile
            merged_flags[-1] = True
        else:
            new_vals.append(Tile(value=tile.value, heat=tile.heat))
            merged_flags.append(False)

    # Step 3 pad None to BOARD_SIZE left-aligned
    result: List[Optional[Tile]] = list(new_vals)
    while len(result) < BOARD_SIZE:
        result.append(None)
    return result


def _simulate_slide_without_spawn(
    grid: List[List[Optional[Tile]]],
    direction: Direction,
) -> List[List[Optional[Tile]]]:
    """Pure helper: compress-merge-compress simulation, no spawn.

    Args:
        grid: Source grid.
        direction: Direction enum.

    Returns:
        New 5x5 grid after simulated slide.
    """
    new_grid: List[List[Optional[Tile]]] = [
        [None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
    ]

    if direction == Direction.LEFT:
        for r in range(BOARD_SIZE):
            line = _extract_line_for_rules(grid, Direction.LEFT, r)
            processed = _process_line_no_spawn(line)
            new_grid[r] = processed

    elif direction == Direction.RIGHT:
        for r in range(BOARD_SIZE):
            line = _extract_line_for_rules(grid, Direction.RIGHT, r)
            processed = _process_line_no_spawn(line)
            non_none = [t for t in processed if t is not None]
            padded: List[Optional[Tile]] = [None] * (
                BOARD_SIZE - len(non_none)
            ) + non_none
            new_grid[r] = padded

    elif direction == Direction.UP:
        for c in range(BOARD_SIZE):
            line = _extract_line_for_rules(grid, Direction.UP, c)
            processed = _process_line_no_spawn(line)
            for r in range(BOARD_SIZE):
                new_grid[r][c] = processed[r]

    else:  # DOWN
        for c in range(BOARD_SIZE):
            line = _extract_line_for_rules(grid, Direction.DOWN, c)
            processed = _process_line_no_spawn(line)
            for idx in range(BOARD_SIZE):
                new_grid[BOARD_SIZE - 1 - idx][c] = processed[idx]

    return new_grid


def _grids_differ_by_value(
    grid_a: List[List[Optional[Tile]]],
    grid_b: List[List[Optional[Tile]]],
) -> bool:
    """Compare two grids by presence and Tile.value only, ignoring heat.

    Args:
        grid_a: First grid.
        grid_b: Second grid.

    Returns:
        True if differ by value/presence, False otherwise.
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            a = grid_a[r][c]
            b = grid_b[r][c]
            if a is None and b is None:
                continue
            if a is None and b is not None:
                return True
            if a is not None and b is None:
                return True
            # Both not None
            if a.value != b.value:  # type: ignore[union-attr]
                return True
            # heat ignored intentionally per AC-7
    return False


def _has_empty(grid: List[List[Optional[Tile]]]) -> bool:
    """Check if any None cell exists.

    Args:
        grid: Grid to scan.

    Returns:
        True if empty cell exists.
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if grid[r][c] is None:
                return True
    return False


def _has_merge_possible(grid: List[List[Optional[Tile]]]) -> bool:
    """Check adjacent equal values for possible merge.

    Args:
        grid: Grid to scan.

    Returns:
        True if merge possible.
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is None:
                continue
            current_value = cell.value
            # Check right neighbor
            if c + 1 < BOARD_SIZE and grid[r][c + 1] is not None:
                if grid[r][c + 1].value == current_value:  # type: ignore[union-attr]
                    return True
            # Check down neighbor
            if r + 1 < BOARD_SIZE and grid[r + 1][c] is not None:
                if grid[r + 1][c].value == current_value:  # type: ignore[union-attr]
                    return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_legal_move(
    direction: Direction | str,
    grid: List[List[Optional[Tile]]],
) -> bool:
    """Return True if sliding grid in direction would change board values.

    Args:
        direction: Direction enum or string UP/DOWN/LEFT/RIGHT.
        grid: 5x5 grid of Optional[Tile].

    Returns:
        True if move would change board values, False otherwise.

    Raises:
        ValueError: E001 if direction invalid, E002 if grid malformed.
    """
    direction_enum = _validate_direction(direction)
    _validate_grid(grid)
    copied = _deep_copy_grid(grid)
    simulated = _simulate_slide_without_spawn(copied, direction_enum)
    return _grids_differ_by_value(grid, simulated)


def is_game_over(grid: List[List[Optional[Tile]]]) -> bool:
    """Return True only when no empty cells and no merge possible.

    Args:
        grid: 5x5 grid of Optional[Tile].

    Returns:
        True if game over, False otherwise.

    Raises:
        ValueError: E002 if grid malformed.
    """
    _validate_grid(grid)

    if _has_empty(grid):
        return False

    if _has_merge_possible(grid):
        return False

    # Defense in depth: simulate all 4 directions
    for dir_enum in [
        Direction.UP,
        Direction.DOWN,
        Direction.LEFT,
        Direction.RIGHT,
    ]:
        simulated = _simulate_slide_without_spawn(grid, dir_enum)
        if _grids_differ_by_value(grid, simulated):
            return False

    return True
