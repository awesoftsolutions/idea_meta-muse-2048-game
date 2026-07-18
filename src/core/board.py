"""
src/core/board.py — Production board with Tile dataclass and slide/merge.
Pure-Python 5x5 board with Tile dataclass, injectable RNG, headless.

Implements 5x5 2048 board logic: Tile dataclass value+heat, Direction enum,
MergeInfo with heat_gen floor(log2(V)/2), SlideResult, Board with injectable
RNG, compress-merge-compress with merged-flag preventing double merge, spawn
90/10 heat=0 immune per ADR-009. Allowed imports only: random, math, copy,
typing, dataclasses, enum. No pygame import, no global random usage — only
self.rng / rng.

Purpose: Production board for the2048 5x5 puzzle with Thermal Entropy Core
    twist integration. Implements Tile dataclass value+heat single source of
    truth per ADR-008, Board central owner of grid storage slide/merge spawn
    per ADR-011, injectable random.Random per ADR-015, no pygame import per
    E007 headless testability.

System: src/core per Phase 2 architecture.

Dependencies: stdlib only — math, random, dataclasses, enum, typing,
    __future__. Never pygame-ce.

Used-by: src/core/rules.py, src/core/twist.py (future), tests/test_board.py,
    tests/test_isolation_phase2.py, tests/test_rules.py.

Public interface:
    - Tile: dataclass value power-of-two >=2, heat 0-3 clamped, __post_init__
      validation E002, __eq__, __repr__
    - Direction: Enum UP/DOWN/LEFT/RIGHT with __str__
    - MergeInfo: dataclass position, value, source_positions, heat_gen
      floor(log2(V)/2) clamped 0-3 per ADR-010
    - SlideResult: dataclass grid, score_delta, moved, merges
    - Board: class grid 5x5 Optional[Tile], rng Random injectable,
      methods __init__, _validate_grid, _validate_direction,
      _get_empty_cells, get_empty_cells, _extract_lines,
      _extract_base_positions, _process_line with merged-flag,
      _reconstruct_grid, _spawn_tile with rng.choice/rng.random heat=0,
      spawn_tile, slide returning SlideResult, raises ValueError E001/E002,
      TypeError E006
    - BOARD_SIZE: constant 5
    - HEAT_MIN: constant 0
    - HEAT_MAX: constant 3
    - create_empty_grid: function returns 5x5 None grid
    - _is_power_of_two, _calc_heat_gen, _validate_grid, _validate_direction:
      internal helpers
"""
# CHANGELOG:
# - Phase 3 Sprint 1: MODIFIED MergeInfo source_heats Tuple[int,int]
#   (prev.heat, tile.heat) captured during _process_line new_heat max+gen
#   clamped 0-3 Q-004.
# - Phase 3 Sprint 2: VERIFIED MergeInfo source_heats Q-004 cold_fusion fix
#   final audit production board pipeline locked.
# - Phase 2 Sprint 1: Production board implementation - Tile dataclass with
#   value (power-of-two >=2) + heat (0-3 clamped), Direction enum UP/DOWN/
#   LEFT/RIGHT, SlideResult (grid, score_delta, moved, merges), MergeInfo
#   (position, value, source_positions, heat_gen floor(log2(V)/2) clamped 0-3).
#   5x5 grid Optional[Tile], slide all 4 directions maximal blocking with
#   one-merge-per-tile via merged-flag (compress-merge-compress), spawn 90/10
#   injectable Random (rng.choice/rng.random) heat=0 immune per ADR-009.
#   Fix duplicate docstring - single module docstring with future import at top.
# - Phase 1 Sprint 1: Initial board scaffolding.

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BOARD_SIZE: int = 5
HEAT_MIN: int = 0
HEAT_MAX: int = 3

# Type aliases
Grid = List[List[Optional["Tile"]]]
IntGrid = List[List[Optional[int]]]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_power_of_two(value: int) -> bool:
    """Check if value is power of two >=2.

    Args:
        value: Integer to check.

    Returns:
        True if value is power of two >=2, False otherwise.
    """
    if not isinstance(value, int):
        return False
    if value < 2:
        return False
    return (value & (value - 1)) == 0


def _calc_heat_gen(value: int) -> int:
    """
    Calculate heat_gen = floor(log2(V)/2) clamped 0-3 per ADR-010.

    Examples: V=4->1, 8->1, 16->2, 32->2, 64->3, 128->3, 256->4 clamped to 3.
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


def _validate_grid(grid: Optional[Grid]) -> None:
    """Validate 5x5 shape and Tile values.

    Args:
        grid: Optional 5x5 grid to validate.

    Raises:
        ValueError: If grid not 5x5 or Tile invalid (E002).
    """
    if grid is None:
        return
    if len(grid) != BOARD_SIZE:
        raise ValueError(f"E002 MalformedGrid: Expected 5x5 grid, got {len(grid)} rows")
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
                raise ValueError(f"E002 MalformedGrid: Cell ({r},{c}) not Tile or None")
            if not _is_power_of_two(cell.value):
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) value {cell.value} not power-of-two"
                )
            if not isinstance(cell.heat, int):
                raise ValueError(f"E002 MalformedGrid: Cell ({r},{c}) heat not int")
            if cell.heat < HEAT_MIN or cell.heat > HEAT_MAX:
                raise ValueError(
                    f"E002 MalformedGrid: Cell ({r},{c}) heat {cell.heat} out of range 0-3"
                )


def _validate_direction(direction) -> None:
    """Validate direction in UP/DOWN/LEFT/RIGHT.

    Args:
        direction: Direction enum or string to validate.

    Raises:
        ValueError: If direction invalid (E001).
    """
    if isinstance(direction, Direction):
        return
    if isinstance(direction, str) and direction in ("UP", "DOWN", "LEFT", "RIGHT"):
        return
    raise ValueError(
        f"E001 InvalidDirection: '{direction}' invalid, valid directions are [UP,DOWN,LEFT,RIGHT]"
    )


def create_empty_grid() -> Grid:
    """Create 5x5 grid filled with None.

    Returns:
        5x5 grid of None.
    """
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


# ---------------------------------------------------------------------------
# Tile dataclass
# ---------------------------------------------------------------------------


@dataclass
class Tile:
    """Tile with value power-of-two >=2 and heat 0-3 clamped per ADR-008.

    Attributes:
        value: Tile value, must be power of two >=2.
        heat: Heat level clamped 0-3, max preserved on merge.

    Raises:
        ValueError: If value is not power of two >=2 (E002).
    """

    value: int
    heat: int = 0

    def __post_init__(self) -> None:
        if not _is_power_of_two(self.value):
            raise ValueError(
                f"E002 MalformedGrid: Tile value {self.value} not power of two >=2"
            )
        if not isinstance(self.heat, int):
            raise ValueError("E002 MalformedGrid: Tile heat must be int")
        # Clamp heat 0-3 per AC-1
        self.heat = max(HEAT_MIN, min(HEAT_MAX, self.heat))

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if not isinstance(other, Tile):
            return False
        return self.value == other.value and self.heat == other.heat

    def __repr__(self) -> str:
        return f"Tile(value={self.value}, heat={self.heat})"


# ---------------------------------------------------------------------------
# Direction enum
# ---------------------------------------------------------------------------


class Direction(Enum):
    """Slide direction enum for board moves.

    Attributes:
        UP: Slide up.
        DOWN: Slide down.
        LEFT: Slide left.
        RIGHT: Slide right.
    """

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# MergeInfo dataclass
# ---------------------------------------------------------------------------


@dataclass
class MergeInfo:
    """Single merge event with position, value, source_positions, heat_gen per ADR-010.

    Extended per ADR-017 with source_heats for Q-004 cold_fusion fix:
    source_heats = (prev.heat, tile.heat) captured during _process_line.

    Attributes:
        position: Final (r,c) position of merged tile after reconstruction.
        value: Merged tile value (sum of sources).
        source_positions: List of (r,c) source positions that merged.
        heat_gen: Heat generated floor(log2(V)/2) clamped 0-3.
        source_heats: Tuple of source heats (prev.heat, tile.heat) for cold_fusion fix.

    Raises:
        ValueError: If position invalid or value not power of two (E002).
    """

    position: Tuple[int, int]
    value: int
    source_positions: List[Tuple[int, int]] = field(default_factory=list)
    heat_gen: int = 0
    source_heats: Tuple[int, int] = (0, 0)

    def __post_init__(self) -> None:
        if not _is_power_of_two(self.value):
            raise ValueError(f"E002 MalformedGrid: MergeInfo value {self.value} not power of two")
        # Clamp heat_gen 0-3
        if not isinstance(self.heat_gen, int):
            raise ValueError("E002 MergeInfo heat_gen must be int")
        self.heat_gen = max(HEAT_MIN, min(HEAT_MAX, self.heat_gen))
        # Validate position
        if not isinstance(self.position, tuple) or len(self.position) != 2:
            raise ValueError(f"E002 MergeInfo position invalid: {self.position}")
        r, c = self.position
        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            raise ValueError(f"E002 MergeInfo position out of range: {self.position}")
        # Validate source_heats tuple len 2, clamp 0-3
        if not isinstance(self.source_heats, (tuple, list)) or len(self.source_heats) != 2:
            object.__setattr__(self, "source_heats", (0, 0))
        else:
            try:
                h0 = int(self.source_heats[0])
                h1 = int(self.source_heats[1])
            except (ValueError, TypeError, AttributeError, IndexError):
                object.__setattr__(self, "source_heats", (0, 0))
            else:
                h0 = max(HEAT_MIN, min(HEAT_MAX, h0))
                h1 = max(HEAT_MIN, min(HEAT_MAX, h1))
                object.__setattr__(self, "source_heats", (h0, h1))
        if self.source_positions is None:
            object.__setattr__(self, "source_positions", [])


# ---------------------------------------------------------------------------
# SlideResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class SlideResult:
    """Return type of Board.slide() per IBoardSlide contract.

    Attributes:
        grid: Resulting 5x5 grid after slide and optional spawn.
        score_delta: Sum of merged values.
        moved: Whether any tile moved or merged.
        merges: List of MergeInfo events with heat_gen.
        vent_occurred: Whether any edge tile vented this turn.
        unstable_present: Whether any tile heat>=3 present after turn.
        unstable_positions: List of unstable positions.
        heat_state: Optional dict with heat pipeline state.

    Raises:
        ValueError: If grid not 5x5 or score_delta negative (E002).
    """

    grid: Grid
    score_delta: int
    moved: bool
    merges: List[MergeInfo] = field(default_factory=list)
    vent_occurred: bool = False
    unstable_present: bool = False
    unstable_positions: List[Tuple[int, int]] = field(default_factory=list)
    heat_state: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_grid(self.grid)
        if not isinstance(self.score_delta, int) or self.score_delta < 0:
            raise ValueError(f"E002 SlideResult score_delta must be int >=0, got {self.score_delta}")
        if not isinstance(self.moved, bool):
            raise ValueError("E002 SlideResult moved must be bool")
        if not isinstance(self.merges, list):
            raise ValueError("E002 SlideResult merges must be list")
        if not isinstance(self.vent_occurred, bool):
            object.__setattr__(self, "vent_occurred", bool(self.vent_occurred))
        if not isinstance(self.unstable_present, bool):
            object.__setattr__(self, "unstable_present", bool(self.unstable_present))
        if self.unstable_positions is None:
            object.__setattr__(self, "unstable_positions", [])
        if self.heat_state is None:
            object.__setattr__(self, "heat_state", {})


# ---------------------------------------------------------------------------
# Board class
# ---------------------------------------------------------------------------


class Board:
    """Pure-Python 5x5 2048 board with injectable RNG, Tile grid.

    Attributes:
        grid: Current 5x5 grid of Optional[Tile].
        rng: Injected random.Random for deterministic spawn.

    Raises:
        ValueError: If grid malformed (E002).
        TypeError: If rng not random.Random (E006).
    """

    def __init__(
        self,
        grid: Optional[Grid] = None,
        rng: Optional[random.Random] = None,
    ) -> None:
        """Initialize 5x5 board, optional Tile grid and injectable RNG."""
        if grid is None:
            self.grid: Grid = create_empty_grid()
        else:
            _validate_grid(grid)
            # Deep copy via Tile(value,heat) to preserve heat
            self.grid = []
            for r in range(BOARD_SIZE):
                row: List[Optional[Tile]] = []
                for c in range(BOARD_SIZE):
                    cell = grid[r][c]
                    if cell is None:
                        row.append(None)
                    else:
                        row.append(Tile(value=cell.value, heat=cell.heat))
                self.grid.append(row)

        if rng is None:
            self.rng = random.Random()
        else:
            if not isinstance(rng, random.Random):
                raise TypeError("E006 RNGNotInjected: Board requires random.Random")
            self.rng = rng

        self.size = BOARD_SIZE

    # ------------------------------------------------------------------
    # Validation wrappers
    # ------------------------------------------------------------------
    def _validate_grid(self, grid: Grid) -> None:
        """Validate grid via module-level helper.

        Args:
            grid: 5x5 grid to validate.

        Raises:
            ValueError: If grid malformed (E002).
        """
        _validate_grid(grid)

    def _validate_direction(self, direction) -> None:
        """Validate direction via module-level helper.

        Args:
            direction: Direction enum or string to validate.

        Raises:
            ValueError: If direction invalid (E001).
        """
        _validate_direction(direction)

    # ------------------------------------------------------------------
    # Empty cells
    # ------------------------------------------------------------------
    def _get_empty_cells(self, grid: Grid) -> List[Tuple[int, int]]:
        """Return list of (r,c) where grid is None.

        Args:
            grid: 5x5 grid to scan.

        Returns:
            List of (r,c) empty positions.
        """
        empty: List[Tuple[int, int]] = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if grid[r][c] is None:
                    empty.append((r, c))
        return empty

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        """Public wrapper returning empty cells of self.grid.

        Returns:
            List of (r,c) empty positions in current grid.
        """
        return self._get_empty_cells(self.grid)

    # ------------------------------------------------------------------
    # Extract lines per direction
    # ------------------------------------------------------------------
    def _extract_lines(
        self, grid: Grid, direction: Direction
    ) -> List[List[Optional[Tile]]]:
        """Extract rows or columns as lines per direction.

        Args:
            grid: 5x5 grid to extract from.
            direction: Direction to extract lines for.

        Returns:
            List of lines, each line is list of Optional[Tile] in slide order.

        Raises:
            ValueError: If direction invalid (E001) or grid malformed (E002).
        """
        _validate_direction(direction)
        _validate_grid(grid)
        lines: List[List[Optional[Tile]]] = []

        # Normalize direction to enum if string passed (should already be enum here)
        if isinstance(direction, str):
            direction = Direction(direction)

        if direction == Direction.LEFT:
            for r in range(BOARD_SIZE):
                line = list(grid[r])  # copy left to right
                lines.append(line)
        elif direction == Direction.RIGHT:
            for r in range(BOARD_SIZE):
                line = list(reversed(grid[r]))  # reversed copy
                lines.append(line)
        elif direction == Direction.UP:
            for c in range(BOARD_SIZE):
                line = [grid[r][c] for r in range(BOARD_SIZE)]  # top to bottom
                lines.append(line)
        elif direction == Direction.DOWN:
            for c in range(BOARD_SIZE):
                line = [grid[r][c] for r in reversed(range(BOARD_SIZE))]  # bottom to top
                lines.append(line)
        return lines

    def _extract_base_positions(
        self, direction: Direction
    ) -> List[List[Tuple[int, int]]]:
        """Compute base_positions per direction for MergeInfo source tracking.

        Args:
            direction: Direction to compute base positions for.

        Returns:
            List of position lists, each inner list maps line index to board (r,c).
        """
        base_positions: List[List[Tuple[int, int]]] = []
        if direction == Direction.LEFT:
            for r in range(BOARD_SIZE):
                row_pos = [(r, c) for c in range(BOARD_SIZE)]
                base_positions.append(row_pos)
        elif direction == Direction.RIGHT:
            for r in range(BOARD_SIZE):
                row_pos = [(r, BOARD_SIZE - 1 - c) for c in range(BOARD_SIZE)]
                base_positions.append(row_pos)
        elif direction == Direction.UP:
            for c in range(BOARD_SIZE):
                col_pos = [(r, c) for r in range(BOARD_SIZE)]
                base_positions.append(col_pos)
        elif direction == Direction.DOWN:
            for c in range(BOARD_SIZE):
                col_pos = [(BOARD_SIZE - 1 - r, c) for r in range(BOARD_SIZE)]
                base_positions.append(col_pos)
        return base_positions

    # ------------------------------------------------------------------
    # Process line with merged-flag
    # ------------------------------------------------------------------
    def _process_line(
        self,
        line: List[Optional[Tile]],
        line_index: int,
        direction: Direction,
        base_positions: List[Tuple[int, int]],
    ) -> Tuple[List[Optional[Tile]], int, List[MergeInfo]]:
        """
        Compress-merge-compress single line with merged-flag preventing double merge.

        Returns (new_line, score_delta, merges) where new_line is left-aligned
        length BOARD_SIZE, merges have placeholder positions to be finalized later.
        """
        if len(line) != BOARD_SIZE:
            raise ValueError(f"E002 MalformedGrid: line length {len(line)} != {BOARD_SIZE}")

        # Step 1: compress - filter None, keep Tile objects with original positions
        compressed_tiles: List[Tile] = []
        compressed_positions: List[Tuple[int, int]] = []
        for idx, cell in enumerate(line):
            if cell is not None:
                if not isinstance(cell, Tile):
                    raise ValueError(f"E002 MalformedGrid: line contains non-Tile at index {idx}")
                compressed_tiles.append(cell)
                compressed_positions.append(base_positions[idx])

        # Step 2: merge adjacent equals with merged-flag
        new_line_vals: List[Tile] = []
        merged_flags: List[bool] = []
        # Track source positions for each tile in new_line_vals for merge tracking
        new_line_source_positions: List[List[Tuple[int, int]]] = []
        merges: List[MergeInfo] = []
        score_delta = 0

        # Track source heats parallel to source positions
        new_line_source_heats: List[Tuple[int, int]] = []

        for i, tile in enumerate(compressed_tiles):
            if (
                new_line_vals
                and new_line_vals[-1].value == tile.value
                and not merged_flags[-1]
            ):
                # Merge possible - capture source heats BEFORE merge per ADR-017
                prev_tile = new_line_vals[-1]
                prev_heat = prev_tile.heat
                curr_heat = tile.heat
                source_heats_tuple = (prev_heat, curr_heat)
                new_value = prev_tile.value * 2
                heat_gen = _calc_heat_gen(new_value)
                # new_heat = max(prev, curr) + heat_gen clamped 0-3 per ADR-017
                new_heat_with_gen = max(prev_heat, curr_heat) + heat_gen
                new_heat_with_gen = max(HEAT_MIN, min(HEAT_MAX, new_heat_with_gen))
                new_tile = Tile(value=new_value, heat=new_heat_with_gen)

                # Replace last tile
                new_line_vals[-1] = new_tile
                merged_flags[-1] = True

                score_delta += new_value

                # Collect MergeInfo with placeholder position, finalization in reconstruct
                prev_sources = new_line_source_positions[-1]
                source_positions = prev_sources + [compressed_positions[i]]
                new_line_source_positions[-1] = source_positions
                new_line_source_heats[-1] = source_heats_tuple

                merge_info = MergeInfo(
                    position=(0, 0),
                    value=new_value,
                    source_positions=source_positions,
                    heat_gen=heat_gen,
                    source_heats=source_heats_tuple,
                )
                merges.append(merge_info)
            else:
                # No merge, append copy
                new_tile = Tile(value=tile.value, heat=tile.heat)
                new_line_vals.append(new_tile)
                merged_flags.append(False)
                new_line_source_positions.append([compressed_positions[i]])
                new_line_source_heats.append((tile.heat, 0))

        # Step 3: pad None to BOARD_SIZE (left-aligned)
        new_line: List[Optional[Tile]] = list(new_line_vals)
        while len(new_line) < BOARD_SIZE:
            new_line.append(None)

        # For reconstruct, we need to know merge indices in new_line_vals
        # We have merges in order of appearance; their index in new_line_vals corresponds
        # to the order they were merged. We need to map merge to its final index.
        # Since merges are appended in order, we can compute merge_index by tracking.
        # To simplify, we will return merges with an extra attribute via closure?
        # Instead, we will let _reconstruct_grid recompute positions based on merge order
        # and new_line_vals length. For LEFT, merge positions are at indices where merges occurred.
        # We need to know which indices in new_line_vals are merged.
        # We have merged_flags indicating which entries are merged results.
        # So we can store merge_index mapping.

        # Build list of (merge, merge_index_in_new_line_vals)
        # Iterate over new_line_vals with merged_flags to assign merges in order
        indexed_merges: List[Tuple[MergeInfo, int]] = []
        merge_iter = iter(merges)
        for idx, is_merged in enumerate(merged_flags):
            if is_merged:
                try:
                    m = next(merge_iter)
                    indexed_merges.append((m, idx))
                except StopIteration:
                    break

        # We return new_line and also store indexed merges via attribute on merges?
        # To keep signature simple, we will return new_line, score_delta, indexed_merges
        # But spec says return List[MergeInfo]. We will instead return merges with
        # position still placeholder and let reconstruct handle via merged_flags.
        # For simplicity, we attach _merge_index to each MergeInfo via setattr (allowed).
        for (merge_obj, merge_idx) in indexed_merges:
            # Store temporary index for reconstruct
            object.__setattr__(merge_obj, "_tmp_index", merge_idx)  # type: ignore

        return new_line, score_delta, merges

    # ------------------------------------------------------------------
    # Reconstruct grid per direction
    # ------------------------------------------------------------------
    def _reconstruct_grid(
        self,
        processed_lines: List[List[Optional[Tile]]],
        direction: Direction,
        original_grid: Grid,
        all_merges: List[MergeInfo],
    ) -> Tuple[Grid, int, bool, List[MergeInfo]]:
        """
        Reconstruct 5x5 grid from processed lines per direction, detect moved,
        finalize MergeInfo positions.
        """
        new_grid = create_empty_grid()
        final_merges: List[MergeInfo] = []

        # Group merges by line_index for position finalization
        # all_merges is flat list in line order; we need to know line_index per merge
        # We will reconstruct grouping by iterating processed_lines and using _tmp_index

        # Build line-wise merge groups
        # Since _process_line stored _tmp_index, we can group by line
        # We need to know which merges belong to which line.
        # We will have passed all_merges as flat list but we need line association.
        # Instead, we will rely on processed_lines order and all_merges order.
        # For simplicity, we will re-derive merges per line from processed_lines
        # using the _tmp_index attribute.

        # Organize merges per line index
        # We need to know line_index for each merge. We will have to track during slide.
        # To avoid complexity, we will in slide() pass all_merges_with_line_idx.
        # Here we assume all_merges already has _tmp_line_idx attribute if set.

        if direction == Direction.LEFT:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    new_grid[r][c] = processed_lines[r][c]
                # Update merge positions for this row
                for merge in all_merges:
                    line_idx = getattr(merge, "_tmp_line_idx", None)
                    if line_idx is not None and line_idx != r:
                        continue
                    tmp_idx = getattr(merge, "_tmp_index", 0)
                    final_merge = MergeInfo(
                        position=(r, tmp_idx),
                        value=merge.value,
                        source_positions=merge.source_positions,
                        heat_gen=merge.heat_gen,
                        source_heats=getattr(merge, "source_heats", (0, 0)),
                    )
                    # Preserve hack attributes if needed for downstream
                    object.__setattr__(final_merge, "_tmp_index", tmp_idx)  # type: ignore
                    if line_idx is not None:
                        object.__setattr__(final_merge, "_tmp_line_idx", line_idx)  # type: ignore
                    final_merges.append(final_merge)

        elif direction == Direction.RIGHT:
            for r in range(BOARD_SIZE):
                non_none = [tile for tile in processed_lines[r] if tile is not None]
                padded = [None] * (BOARD_SIZE - len(non_none)) + non_none
                new_grid[r] = padded
                offset = BOARD_SIZE - len(non_none)
                for merge in all_merges:
                    line_idx = getattr(merge, "_tmp_line_idx", None)
                    if line_idx is not None and line_idx != r:
                        continue
                    tmp_idx = getattr(merge, "_tmp_index", 0)
                    final_pos = (r, offset + tmp_idx)
                    final_merge = MergeInfo(
                        position=final_pos,
                        value=merge.value,
                        source_positions=merge.source_positions,
                        heat_gen=merge.heat_gen,
                        source_heats=getattr(merge, "source_heats", (0, 0)),
                    )
                    object.__setattr__(final_merge, "_tmp_index", tmp_idx)  # type: ignore
                    if line_idx is not None:
                        object.__setattr__(final_merge, "_tmp_line_idx", line_idx)  # type: ignore
                    final_merges.append(final_merge)

        elif direction == Direction.UP:
            for c in range(BOARD_SIZE):
                for r in range(BOARD_SIZE):
                    new_grid[r][c] = processed_lines[c][r]
                for merge in all_merges:
                    line_idx = getattr(merge, "_tmp_line_idx", None)
                    if line_idx is not None and line_idx != c:
                        continue
                    tmp_idx = getattr(merge, "_tmp_index", 0)
                    final_pos = (tmp_idx, c)
                    final_merge = MergeInfo(
                        position=final_pos,
                        value=merge.value,
                        source_positions=merge.source_positions,
                        heat_gen=merge.heat_gen,
                        source_heats=getattr(merge, "source_heats", (0, 0)),
                    )
                    object.__setattr__(final_merge, "_tmp_index", tmp_idx)  # type: ignore
                    if line_idx is not None:
                        object.__setattr__(final_merge, "_tmp_line_idx", line_idx)  # type: ignore
                    final_merges.append(final_merge)

        elif direction == Direction.DOWN:
            for c in range(BOARD_SIZE):
                for idx in range(BOARD_SIZE):
                    new_grid[BOARD_SIZE - 1 - idx][c] = processed_lines[c][idx]
                for merge in all_merges:
                    line_idx = getattr(merge, "_tmp_line_idx", None)
                    if line_idx is not None and line_idx != c:
                        continue
                    tmp_idx = getattr(merge, "_tmp_index", 0)
                    final_pos = (BOARD_SIZE - 1 - tmp_idx, c)
                    final_merge = MergeInfo(
                        position=final_pos,
                        value=merge.value,
                        source_positions=merge.source_positions,
                        heat_gen=merge.heat_gen,
                        source_heats=getattr(merge, "source_heats", (0, 0)),
                    )
                    object.__setattr__(final_merge, "_tmp_index", tmp_idx)  # type: ignore
                    if line_idx is not None:
                        object.__setattr__(final_merge, "_tmp_line_idx", line_idx)  # type: ignore
                    final_merges.append(final_merge)

        # Detect moved: compare new_grid vs original_grid by value
        moved = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                orig = original_grid[r][c]
                new = new_grid[r][c]
                if orig is None and new is None:
                    continue
                if orig is None and new is not None:
                    moved = True
                    break
                if orig is not None and new is None:
                    moved = True
                    break
                # Both Tiles
                if orig.value != new.value:  # type: ignore
                    moved = True
                    break
                # If values equal but positions changed, grid comparison already catches
                # via None vs Tile shift, but same values moved? Example [2,None,None,None,None]
                # LEFT no move, but [None,None,None,None,2] LEFT moves to [2,None...] -> orig None vs new Tile detected above.
            if moved:
                break

        # Total score will be computed outside, but we return 0 placeholder
        return new_grid, 0, moved, final_merges

    # ------------------------------------------------------------------
    # Spawn
    # ------------------------------------------------------------------
    def _spawn_tile(self, grid: Grid, rng: random.Random) -> Grid:
        """Spawn 2 (90%) or 4 (10%) in random empty cell using rng, return new grid.

        Args:
            grid: 5x5 grid.
            rng: Random instance for choice and random.

        Returns:
            New grid with spawned Tile heat=0, or copy if no empty.
        """
        empty = self._get_empty_cells(grid)
        if not empty:
            # No empty cells — return deep copy unchanged (E009)
            new_grid: Grid = []
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
        chosen = rng.choice(empty)
        is_two = rng.random() < 0.9
        val = 2 if is_two else 4
        new_grid = []
        for r in range(BOARD_SIZE):
            row: List[Optional[Tile]] = []
            for c in range(BOARD_SIZE):
                cell = grid[r][c]
                if cell is None:
                    row.append(None)
                else:
                    row.append(Tile(value=cell.value, heat=cell.heat))
            new_grid.append(row)
        new_grid[chosen[0]][chosen[1]] = Tile(value=val, heat=0)
        return new_grid

    def spawn_tile(self, rng: Optional[random.Random] = None) -> Optional[Tuple[int, int]]:
        """Public spawn that mutates self.grid, returns position or None if no empty.

        Args:
            rng: Optional Random, uses self.rng if None.

        Returns:
            Spawned position or None if no empty cells.
        """
        use_rng = rng if rng is not None else self.rng
        empty = self._get_empty_cells(self.grid)
        if not empty:
            return None
        chosen = use_rng.choice(empty)
        is_two = use_rng.random() < 0.9
        val = 2 if is_two else 4
        self.grid[chosen[0]][chosen[1]] = Tile(value=val, heat=0)
        return chosen

    def slide(self, direction, rng: Optional[random.Random] = None) -> SlideResult:
        """Slide tiles in direction, return SlideResult with full pipeline locked.

        Pipeline locked per ADR-009: slide->gen->spread->vent->spawn heat=0->unstable.
        New tiles heat=0 immune same turn because spawn after spread/vent.

        Args:
            direction: Direction enum or string UP/DOWN/LEFT/RIGHT.
            rng: Optional Random for spawn, uses self.rng if None.

        Returns:
            SlideResult with grid, score_delta, moved, merges, vent_occurred,
            unstable_present, unstable_positions.

        Raises:
            ValueError: If direction invalid (E001).
        """
        self._validate_direction(direction)
        dir_enum = direction if isinstance(direction, Direction) else Direction(direction)
        lines = self._extract_lines(self.grid, dir_enum)
        base_positions = self._extract_base_positions(dir_enum)
        processed_lines: List[List[Optional[Tile]]] = []
        all_merges: List[MergeInfo] = []
        total_score = 0
        for idx, line in enumerate(lines):
            new_line, score, merges = self._process_line(line, idx, dir_enum, base_positions[idx])
            processed_lines.append(new_line)
            total_score += score
            all_merges.extend(merges)
            for m in merges:
                object.__setattr__(m, "_tmp_line_idx", idx)  # type: ignore
        reconstructed = self._reconstruct_grid(processed_lines, dir_enum, self.grid, all_merges)
        new_grid = reconstructed[0]
        moved = reconstructed[2]
        final_merges = reconstructed[3]

        vent_occurred = False
        unstable_present = False
        unstable_positions: List[Tuple[int, int]] = []

        if not moved:
            # No move: return early with defaults, no heat phases, no spawn
            result_grid: Grid = []
            for r in range(BOARD_SIZE):
                row: List[Optional[Tile]] = []
                for c in range(BOARD_SIZE):
                    cell = new_grid[r][c]
                    if cell is None:
                        row.append(None)
                    else:
                        row.append(Tile(value=cell.value, heat=cell.heat))
                result_grid.append(row)
            # Update self.grid to reconstructed (unchanged) for consistency
            self.grid = []
            for r in range(BOARD_SIZE):
                row: List[Optional[Tile]] = []
                for c in range(BOARD_SIZE):
                    cell = new_grid[r][c]
                    if cell is None:
                        row.append(None)
                    else:
                        row.append(Tile(value=cell.value, heat=cell.heat))
                self.grid.append(row)
            return SlideResult(
                grid=result_grid,
                score_delta=total_score,
                moved=False,
                merges=final_merges,
                vent_occurred=False,
                unstable_present=False,
                unstable_positions=[],
                heat_state={},
            )

        # Pipeline locked: gen already done in _process_line (max+gen), then spread -> vent -> spawn -> unstable
        # Local import to avoid circular (twist avoids top-level board import)
        from src.core.twist import (  # noqa: WPS433 - local import intentional per ADR-011
            check_unstable,
            spread_heat,
            vent_heat,
        )

        # gen already applied in _process_line as max(prev,curr)+heat_gen clamped
        # So we start from new_grid directly for spread
        grid_after_gen = new_grid

        # spread: orthogonal lower transfer 1
        try:
            grid_after_spread = spread_heat(grid_after_gen)
        except (ValueError, TypeError, AttributeError):
            grid_after_spread = grid_after_gen

        # vent: edge -1, returns (grid, vent_occurred)
        try:
            vent_result = vent_heat(grid_after_spread)
            if isinstance(vent_result, tuple) and len(vent_result) == 2:
                grid_after_vent, vent_occurred = vent_result
            else:
                grid_after_vent = vent_result  # type: ignore
                vent_occurred = False
        except (ValueError, TypeError, AttributeError):
            grid_after_vent = grid_after_spread
            vent_occurred = False

        # spawn heat=0 after spread/vent for immunity
        use_rng = rng if rng is not None else self.rng
        empty_cells = self._get_empty_cells(grid_after_vent)
        if empty_cells:
            grid_after_spawn = self._spawn_tile(grid_after_vent, use_rng)
        else:
            grid_after_spawn = grid_after_vent

        # unstable: check heat>=3
        try:
            unstable_result = check_unstable(grid_after_spawn)
            if isinstance(unstable_result, tuple) and len(unstable_result) == 2:
                unstable_positions, unstable_present = unstable_result
            else:
                unstable_positions = unstable_result  # type: ignore
                unstable_present = len(unstable_positions) > 0
        except (ValueError, TypeError, AttributeError):
            unstable_positions = []
            unstable_present = False

        # Update self.grid deep copy
        self.grid = []
        for r in range(BOARD_SIZE):
            row: List[Optional[Tile]] = []
            for c in range(BOARD_SIZE):
                cell = grid_after_spawn[r][c]
                if cell is None:
                    row.append(None)
                else:
                    row.append(Tile(value=cell.value, heat=cell.heat))
            self.grid.append(row)

        # Deep copy for SlideResult
        result_grid = []
        for r in range(BOARD_SIZE):
            row: List[Optional[Tile]] = []
            for c in range(BOARD_SIZE):
                cell = grid_after_spawn[r][c]
                if cell is None:
                    row.append(None)
                else:
                    row.append(Tile(value=cell.value, heat=cell.heat))
            result_grid.append(row)

        return SlideResult(
            grid=result_grid,
            score_delta=total_score,
            moved=moved,
            merges=final_merges,
            vent_occurred=bool(vent_occurred),
            unstable_present=bool(unstable_present),
            unstable_positions=list(unstable_positions),
            heat_state={
                "vent_occurred": bool(vent_occurred),
                "unstable_present": bool(unstable_present),
            },
        )