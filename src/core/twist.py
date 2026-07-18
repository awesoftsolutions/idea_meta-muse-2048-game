"""
Thermal Entropy Core deterministic heat mechanics.

Purpose:
    Implements pure deterministic heat mechanics for 2048 twist: heat generation
    floor(log2(V)/2) clamped 0-3 per ADR-010, orthogonal lower spread transfer 1
    with two-phase delta accumulation per ADR-011, edge venting -1 clamped >=0,
    unstable detection >=3, cool-merge bonus for heat 0 sources, and locked turn
    pipeline ordering per ADR-009. All functions are pure, no mutation of input,
    deep copy via Tile(value, heat) duck typing.

System:
    src/core per Phase 2 architecture. Part of Thermal Entropy Core subsystem.
    ADR-009 Turn Pipeline Locked, ADR-010 Heat Formula, ADR-011 Board vs Twist
    Ownership. Logic-Rendering Separation enforced: no pygame import.

Dependencies:
    stdlib only: math (log2, floor), typing (TYPE_CHECKING, List, Optional, Tuple).
    TYPE_CHECKING import of src.core.board.Tile and MergeInfo for type hints only.
    No runtime import of board at top level per ADR-011 acyclic. No RNG creation,
    no global random, never imports pygame.

Used-By:
    src/core/board.py (Board class calls apply_heat_generation, spread_heat,
    vent_heat, check_unstable, calculate_cool_merge_bonus, get_turn_pipeline_order),
    tests/test_twist.py (comprehensive AC coverage), future game loop.

Public Interface:
    Constants: BOARD_SIZE: int = 5, HEAT_MIN: int = 0, HEAT_MAX: int = 3,
        VENT_AMOUNT: int = -1, UNSTABLE_THRESHOLD: int = 3
    Types: Grid = List[List[Optional[Tile]]], MergeList = List[MergeInfo]
    Functions:
        _validate_grid(grid: Grid) -> None: Validates 5x5 else ValueError E002.
        _copy_tile(cell: object, new_heat: Optional[int] = None) -> Optional[object]:
            Deep copy Tile-like via duck typing.
        _deep_copy_grid(grid: Grid) -> Grid: Deep copy via Tile(value, heat).
        _is_edge_position(r: int, c: int, size: int = 5) -> bool: Edge detection.
        _calc_heat_gen_value(value: int) -> int: floor(log2(V)/2) clamped 0-3.
        apply_heat_generation(grid: Grid, merges: MergeList) -> Grid: Pure, adds heat_gen.
        spread_heat(grid: Grid) -> Grid: Deterministic orthogonal lower transfer 1,
            two-phase delta, source does not lose heat, empty skipped, diagonal ignored.
        vent_heat(grid: Grid) -> Grid: Edge -1 clamped >=0, interior unchanged.
        check_unstable(grid: Grid) -> List[Tuple[int, int]]: Collects heat>=3.
        calculate_cool_merge_bonus(merges: MergeList, grid: Grid) -> int: Bonus for heat 0.
        get_turn_pipeline_order() -> List[str]: Locked ordering
            ["slide","calc_merge_heat","apply_gen","spread","vent",
             "spawn_heat_0","check_unstable","evaluate_achievements"].

Turn pipeline locked per ADR-009:
    slide->gen->spread->vent->spawn heat=0->unstable->achievements
    Detailed: slide -> calc_merge_heat -> apply_gen -> spread -> vent -> spawn_heat_0
    -> check_unstable -> evaluate_achievements
    Spawn immunity: spawn after heat phases ensures new tile heat=0 does not
    participate in spread/vent same turn.

Heat gen formula floor(log2(V)/2) clamped 0-3 per ADR-010.
Spread orthogonal lower transfer 1 deterministic per ADR-011.
Vent edge -1 clamped >=0 interior unchanged.
Unstable threshold >=3.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BOARD_SIZE: int = 5
HEAT_MIN: int = 0
HEAT_MAX: int = 3
VENT_AMOUNT: int = -1
UNSTABLE_THRESHOLD: int = 3

# Type alias for grid - use object to avoid circular import at runtime
# Actual Tile type is src.core.board.Tile but we avoid top-level import per ADR-011
if TYPE_CHECKING:
    from src.core.board import MergeInfo as MergeInfoType
    from src.core.board import Tile as TileType

    Grid = List[List[Optional[TileType]]]
    MergeList = List[MergeInfoType]
else:
    Grid = List[List[Optional[object]]]
    MergeList = List[object]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_grid(grid: Grid) -> None:
    """Validate 5x5 shape else raise ValueError E002.

    Args:
        grid: Grid to validate.

    Raises:
        ValueError: If grid not 5x5 (E002).
    """
    if len(grid) != BOARD_SIZE:
        raise ValueError(f"E002 MalformedGrid: Expected 5x5 grid, got {len(grid)} rows")
    for r, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != BOARD_SIZE:
            length = len(row) if isinstance(row, list) else -1
            raise ValueError(
                f"E002 MalformedGrid: Expected 5x5 grid, row {r} has length {length}"
            )


def _copy_tile(cell: object, new_heat: Optional[int] = None) -> Optional[object]:
    """Deep copy a Tile-like object via duck typing to avoid circular import.

    Args:
        cell: Tile or None.
        new_heat: Optional override for heat.

    Returns:
        New Tile instance or None.
    """
    if cell is None:
        return None
    # Duck typing: cell has value and heat attributes
    value = getattr(cell, "value")
    heat = getattr(cell, "heat")
    if new_heat is not None:
        heat = new_heat
    # Try to create via same class to avoid importing board at top level
    try:
        return cell.__class__(value=value, heat=heat)
    except (TypeError, AttributeError, ValueError):
        # Fallback: local import Tile
        # Justification for local import (ADR-011): board.py does not import twist
        # at top level (verified), so no cycle. This fallback is defensive for
        # duck-typing failure when cell.__class__ constructor signature differs
        # or raises TypeError/AttributeError/ValueError. Keeps top-level acyclic.
        from src.core.board import Tile as TileClass

        return TileClass(value=value, heat=heat)


def _deep_copy_grid(grid: Grid) -> Grid:
    """Deep copy grid via Tile(value, heat) duck typing.

    Args:
        grid: 5x5 grid.

    Returns:
        Deep copied grid.
    """
    new_grid: Grid = []
    for r in range(BOARD_SIZE):
        row: List[Optional[object]] = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            row.append(_copy_tile(cell))
        new_grid.append(row)
    return new_grid


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _is_edge_position(r: int, c: int, size: int = 5) -> bool:
    """Check if position is edge per vent logic.

    Args:
        r: Row index.
        c: Column index.
        size: Board size, default 5.

    Returns:
        True if edge (r==0 or r==size-1 or c==0 or c==size-1), else False.
    """
    return r == 0 or r == size - 1 or c == 0 or c == size - 1


def _calc_heat_gen_value(value: int) -> int:
    """Calculate floor(log2(V)/2) clamped 0-3 per ADR-010.

    Args:
        value: Merged tile value V.

    Returns:
        Heat generation int 0-3.

    Examples:
        V=4 log2=2 floor(1)=1
        V=8 log2=3 floor(1.5)=1
        V=16 log2=4 floor(2)=2
        V=32 log2=5 floor(2.5)=2
        V=64 log2=6 floor(3)=3 clamped
    """
    if not isinstance(value, int) or value < 2:
        return 0
    try:
        log2_val = math.log2(value)
    except ValueError:
        return 0
    heat = math.floor(log2_val / 2)
    # Clamp 0-3
    if heat < HEAT_MIN:
        heat = HEAT_MIN
    if heat > HEAT_MAX:
        heat = HEAT_MAX
    return int(heat)


# ---------------------------------------------------------------------------
# Core pure functions
# ---------------------------------------------------------------------------


def apply_heat_generation(grid: Grid, merges: MergeList) -> Grid:
    """Apply heat generation to merged tiles per MergeInfo list.

    Args:
        grid: 5x5 List[List[Optional[Tile]]] current board.
        merges: List[MergeInfo] with position and value.

    Returns:
        New grid with updated heat on merged positions.

    Raises:
        ValueError: If grid not 5x5 (E002).
    """
    _validate_grid(grid)
    new_grid = _deep_copy_grid(grid)

    for merge in merges:
        # Extract position
        pos = getattr(merge, "position", None)
        if pos is None:
            continue
        r, c = pos
        # Defensive range check
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            continue
        if new_grid[r][c] is None:
            continue
        # Compute heat_gen: use merge.heat_gen if set else recalc
        heat_gen_attr = getattr(merge, "heat_gen", None)
        if heat_gen_attr is not None:
            heat_gen = heat_gen_attr
        else:
            val = getattr(merge, "value", 0)
            heat_gen = _calc_heat_gen_value(val)

        existing_heat = getattr(new_grid[r][c], "heat", 0)
        new_heat = existing_heat + heat_gen
        # Clamp 0-3
        if new_heat < HEAT_MIN:
            new_heat = HEAT_MIN
        if new_heat > HEAT_MAX:
            new_heat = HEAT_MAX
        new_grid[r][c] = _copy_tile(new_grid[r][c], new_heat=new_heat)

    return new_grid


def spread_heat(grid: Grid) -> Grid:
    """Deterministic orthogonal spread from higher heat to lower heat neighbor transfer 1.

    Two-phase: accumulate heat_delta matrix then apply clamped.

    Args:
        grid: 5x5 List[List[Optional[Tile]]].

    Returns:
        Grid with spread applied deterministically.

    Raises:
        ValueError: If grid not 5x5 (E002).
    """
    _validate_grid(grid)
    new_grid = _deep_copy_grid(grid)

    # heat_delta matrix 5x5 zeros
    heat_delta: List[List[int]] = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # Directions orthogonal
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is None:
                continue
            current_heat = getattr(cell, "heat", 0)
            if current_heat == 0:
                continue
            for dr, dc in dirs:
                nr = r + dr
                nc = c + dc
                if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                    continue
                neighbor = grid[nr][nc]
                if neighbor is None:
                    continue
                neighbor_heat = getattr(neighbor, "heat", 0)
                if current_heat > neighbor_heat:
                    heat_delta[nr][nc] += 1

    # Apply deltas
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if new_grid[r][c] is None:
                continue
            delta = heat_delta[r][c]
            if delta > 0:
                existing = getattr(new_grid[r][c], "heat", 0)
                new_heat = existing + delta
                if new_heat > HEAT_MAX:
                    new_heat = HEAT_MAX
                if new_heat < HEAT_MIN:
                    new_heat = HEAT_MIN
                new_grid[r][c] = _copy_tile(new_grid[r][c], new_heat=new_heat)

    return new_grid


def vent_heat(grid: Grid) -> Grid:
    """Edge venting -1 heat per turn clamped >=0 interior unchanged.

    Args:
        grid: 5x5 List[List[Optional[Tile]]].

    Returns:
        Grid with edge tiles vented -1, interior unchanged, never negative.

    Raises:
        ValueError: If grid not 5x5 (E002).
    """
    _validate_grid(grid)
    new_grid = _deep_copy_grid(grid)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = new_grid[r][c]
            if cell is None:
                continue
            if _is_edge_position(r, c, BOARD_SIZE):
                existing = getattr(cell, "heat", 0)
                new_heat = existing + VENT_AMOUNT  # VENT_AMOUNT = -1
                if new_heat < HEAT_MIN:
                    new_heat = HEAT_MIN
                if new_heat > HEAT_MAX:
                    new_heat = HEAT_MAX
                new_grid[r][c] = _copy_tile(cell, new_heat=new_heat)
            else:
                # Interior unchanged
                continue

    return new_grid


def check_unstable(grid: Grid) -> List[Tuple[int, int]]:
    """Collect positions where heat >=3 unstable threshold.

    Args:
        grid: 5x5 List[List[Optional[Tile]]].

    Returns:
        List of (r,c) unstable positions.

    Raises:
        ValueError: If grid not 5x5 (E002).
    """
    _validate_grid(grid)
    unstable: List[Tuple[int, int]] = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is None:
                continue
            heat = getattr(cell, "heat", 0)
            if heat >= UNSTABLE_THRESHOLD:
                unstable.append((r, c))
    return unstable


def calculate_cool_merge_bonus(merges: MergeList, grid: Grid) -> int:
    """Cool-merge bonus for heat 0 merges per architecture config.

    If all source_positions tiles in original grid had heat 0, bonus +=1 per merge.

    Args:
        merges: List[MergeInfo].
        grid: 5x5 grid to check heat (original grid before merge).

    Returns:
        Int bonus score.
    """
    bonus = 0
    for merge in merges:
        source_positions = getattr(merge, "source_positions", [])
        if not source_positions:
            # If no source_positions, check merged tile itself? But spec says source tiles heat 0
            # For safety, skip if no sources
            continue
        all_cool = True
        for sr, sc in source_positions:
            if not (0 <= sr < BOARD_SIZE and 0 <= sc < BOARD_SIZE):
                all_cool = False
                break
            # grid may be larger than 5x5? Validate via _validate_grid? But bonus should be tolerant
            # For invalid grid case, we treat as not cool
            try:
                cell = grid[sr][sc]
            except IndexError:
                all_cool = False
                break
            if cell is None:
                all_cool = False
                break
            heat = getattr(cell, "heat", None)
            if heat is None:
                all_cool = False
                break
            if heat != 0:
                all_cool = False
                break
        if all_cool:
            bonus += 1
    return bonus


def get_turn_pipeline_order() -> List[str]:
    """Return locked turn pipeline ordering per ADR-009.

    Locked ordering: slide->gen->spread->vent->spawn heat=0->unstable->achievements
    Detailed: slide -> calc_merge_heat -> apply_gen -> spread -> vent -> spawn_heat_0
    -> check_unstable -> evaluate_achievements

    Spawn immunity: spawn after heat phases ensures new tile heat=0 does not
    participate in spread/vent same turn.

    Returns:
        Ordered list of pipeline steps:
        ["slide","calc_merge_heat","apply_gen","spread","vent",
         "spawn_heat_0","check_unstable","evaluate_achievements"]
    """
    return [
        "slide",
        "calc_merge_heat",
        "apply_gen",
        "spread",
        "vent",
        "spawn_heat_0",
        "check_unstable",
        "evaluate_achievements",
    ]
