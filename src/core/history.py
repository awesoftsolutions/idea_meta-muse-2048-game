"""
src/core/history.py — History snapshot deep copy exact restore.

Implements HistorySnapshot dataclass capturing grid List[List[Optional[Tile]]]
deep copy including heat 0-3, score int, twist_state dict, move_number int,
direction Direction, and HistoryStack with internal List[HistorySnapshot]
storage providing push deep copy isolation, undo pop return last or None
no-op empty per E004, can_undo len>0, clear, new move after undo clears redo.

Purpose: Exact restore for undo per ADR-013, headless per ADR-015.

System: src/core per Phase 2 architecture.

Dependencies: stdlib only — copy, dataclasses, typing. Plus src.core.board
Tile, Direction, BOARD_SIZE. Never pygame-ce.

Used-by: src/core/rules.py (future), tests/test_history.py.

Public interface:
    - HistorySnapshot: dataclass grid deep copy with heat, score, twist_state,
      move_number, direction, __post_init__ validation 5x5 E002
    - HistoryStack: class _stack List[HistorySnapshot], methods __init__,
      push deep copy isolation, undo pop return deep copy or None no-op E004,
      can_undo len>0, clear, __len__, peek deep copy without popping
    - _deep_copy_grid: helper deep copy grid with Tile(value,heat) manual copy
    - _deep_copy_twist_state: helper deep copy twist_state dict
"""
# CHANGELOG:
# - Phase 3 Sprint 1: MODIFIED GameState snapshot exact restore deep copy.
# - Phase 2 Sprint 2: HistorySnapshot deep copy exact restore — grid
#   List[List[Optional[Tile]]] deep copy including heat 0-3, score int,
#   twist_state dict, move_number int, direction Direction, __post_init__
#   validation 5x5 E002. HistoryStack push deep copy isolation, undo pop
#   return last or None no-op empty per E004, can_undo len>0, clear, new
#   move after undo clears redo, deep copy isolation, peek, __len__.

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.board import BOARD_SIZE, Direction, Tile

# Type alias for grid
Grid = List[List[Optional[Tile]]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deep_copy_grid(grid: Grid) -> Grid:
    """Deep copy grid with Tile(value,heat) manual copy for isolation.

    Args:
        grid: Original 5x5 grid of Optional[Tile].

    Returns:
        Deep copied grid with isolated Tile objects preserving value and heat.

    Raises:
        ValueError: If cell is not Tile or None, or grid not list.
    """
    if not isinstance(grid, list):
        raise ValueError("E002 MalformedGrid: Expected list for grid")

    # Defense in depth: deepcopy first, then manual Tile reconstruction
    copied_grid = copy.deepcopy(grid)

    new_grid: Grid = []
    for row_index, row in enumerate(copied_grid):
        if not isinstance(row, list):
            raise ValueError(f"E002 MalformedGrid: Row {row_index} not list")
        new_row: List[Optional[Tile]] = []
        for col_index, cell in enumerate(row):
            if cell is None:
                new_row.append(None)
            else:
                if isinstance(cell, Tile):
                    # Manual Tile copy preserves value and heat isolation
                    isolated_tile = Tile(value=cell.value, heat=cell.heat)
                    new_row.append(isolated_tile)
                else:
                    raise ValueError(
                        f"E002 MalformedGrid: Expected Tile or None at "
                        f"({row_index},{col_index}), got {type(cell)}"
                    )
        new_grid.append(new_row)

    return new_grid


def _deep_copy_twist_state(twist_state: Optional[Dict]) -> Dict:
    """Deep copy twist_state dict via copy.deepcopy.

    Args:
        twist_state: Dict containing heat stats, or None.

    Returns:
        Deep copied dict, or empty dict if None.
    """
    if twist_state is None:
        return {}
    return copy.deepcopy(twist_state)


# ---------------------------------------------------------------------------
# HistorySnapshot dataclass
# ---------------------------------------------------------------------------


@dataclass
class HistorySnapshot:
    """Exact snapshot for undo per ADR-013.

    Extended per Phase 3 with game_state field for exact restore including
    GameState counters.

    Attributes:
        grid: 5x5 board snapshot deep copied including Tile value and heat 0-3.
        score: Current score at snapshot time for exact restore.
        twist_state: Heat stats, vent streak, unstable count generic dict.
        move_number: Sequential move index for ordering and debugging.
        direction: Direction enum that led to this state.
        game_state: Optional GameState deep copied for exact restore.

    Raises:
        ValueError: If grid malformed E002, score negative, move_number negative,
            twist_state not dict, direction not Direction enum.
    """

    grid: Grid
    score: int
    twist_state: Dict
    move_number: int
    direction: Direction
    game_state: Optional[Any] = None

    def __post_init__(self) -> None:
        """Deep copy grid and twist_state, validate 5x5 shape, Tile heat."""
        # Validate grid required
        if self.grid is None:
            raise ValueError("E002 MalformedGrid: grid required")

        if not isinstance(self.grid, list):
            raise ValueError("E002 MalformedGrid: Expected 5x5 grid")

        if len(self.grid) != BOARD_SIZE:
            raise ValueError(
                f"E002 MalformedGrid: Expected 5x5 grid, got {len(self.grid)} rows"
            )

        for row in self.grid:
            if not isinstance(row, list) or len(row) != BOARD_SIZE:
                raise ValueError(
                    f"E002 MalformedGrid: Expected 5x5 grid, row length "
                    f"{len(row) if isinstance(row, list) else 'invalid'}"
                )

        # Deep copy grid with isolation
        isolated_grid = _deep_copy_grid(self.grid)
        object.__setattr__(self, "grid", isolated_grid)

        # Deep copy twist_state
        if not isinstance(self.twist_state, dict):
            raise ValueError("twist_state must be dict")
        isolated_twist = _deep_copy_twist_state(self.twist_state)
        object.__setattr__(self, "twist_state", isolated_twist)

        # Validate score
        if not isinstance(self.score, int) or self.score < 0:
            raise ValueError(f"score must be int >=0, got {self.score}")

        # Validate move_number
        if not isinstance(self.move_number, int) or self.move_number < 0:
            raise ValueError(
                f"move_number must be int >=0, got {self.move_number}"
            )

        # Validate direction
        if not isinstance(self.direction, Direction):
            raise ValueError(
                f"direction must be Direction enum, got {type(self.direction)}"
            )

        # Deep copy game_state if present
        if self.game_state is not None:
            # Reload-tolerant check: accept if class name matches GameState
            gs = self.game_state
            is_gamestate = False
            if type(gs).__name__ == "GameState" and hasattr(gs, "vent_streak"):
                is_gamestate = True
            else:
                try:
                    from src.core.gamestate import GameState as GSClass

                    if isinstance(gs, GSClass):
                        is_gamestate = True
                except (ValueError, TypeError, AttributeError):
                    pass
            if not is_gamestate:
                # Allow None, but if not None and not GameState-like, raise TypeError
                # For backward compat, if it's not GameState-like, keep as is? Raise for safety
                # But we allow any object with vent_streak for reload tolerance
                if not hasattr(gs, "vent_streak"):
                    raise TypeError(f"game_state must be GameState or None, got {type(gs)}")
            isolated_gs = copy.deepcopy(gs)
            object.__setattr__(self, "game_state", isolated_gs)


# ---------------------------------------------------------------------------
# HistoryStack class
# ---------------------------------------------------------------------------


class HistoryStack:
    """Stack of exact snapshots with deep copy isolation.

    Internal storage List[HistorySnapshot] with push performing deep copy of
    incoming snapshot, undo popping and returning deep copy or None no-op empty
    per E004, can_undo len>0, clear empties, __len__ returns count, peek returns
    deep copy of last without popping.

    New move after undo clears redo by natural pop semantics: push A B C,
    undo to B, push D => A B D. No separate redo stack needed.
    """

    def __init__(self) -> None:
        """Initialize empty stack."""
        self._stack: List[HistorySnapshot] = []

    def push(self, snapshot: HistorySnapshot) -> None:
        """Deep copy snapshot and append to stack.

        Truncates forward if after undo via natural pop — stack already popped
        forward history via undo, so push appends to current truncated stack.

        Args:
            snapshot: HistorySnapshot to push.

        Raises:
            ValueError: If snapshot is None.
            TypeError: If snapshot not instance of HistorySnapshot.
        """
        if snapshot is None:
            raise ValueError("snapshot required")

        # Reload-tolerant isinstance check: test_no_pygame_import reloads
        # src.core.history, which creates new class objects. Old instances
        # imported before reload would fail strict isinstance. Accept if
        # class name matches and required attributes exist.
        if not isinstance(snapshot, HistorySnapshot):
            if not (
                type(snapshot).__name__ == "HistorySnapshot"
                and hasattr(snapshot, "grid")
                and hasattr(snapshot, "score")
                and hasattr(snapshot, "twist_state")
                and hasattr(snapshot, "move_number")
                and hasattr(snapshot, "direction")
            ):
                raise TypeError("Expected HistorySnapshot")

        # Deep copy snapshot via copy.deepcopy
        deep_copied_snapshot = copy.deepcopy(snapshot)

        # Ensure grid isolation via helper
        isolated_grid = _deep_copy_grid(deep_copied_snapshot.grid)
        object.__setattr__(deep_copied_snapshot, "grid", isolated_grid)

        # Ensure twist_state isolation
        isolated_twist = _deep_copy_twist_state(
            deep_copied_snapshot.twist_state
        )
        object.__setattr__(
            deep_copied_snapshot, "twist_state", isolated_twist
        )

        # Ensure game_state isolation if present
        gs = getattr(deep_copied_snapshot, "game_state", None)
        if gs is not None:
            isolated_gs = copy.deepcopy(gs)
            object.__setattr__(deep_copied_snapshot, "game_state", isolated_gs)

        self._stack.append(deep_copied_snapshot)

    def undo(self) -> Optional[HistorySnapshot]:
        """Pop and return deep copy of last snapshot, None if empty no-op per E004.

        Returns:
            Deep copy of last HistorySnapshot, or None if stack empty.
            Exact prior state including grid values heat score twist_state
            move_number direction and game_state.
        """
        if len(self._stack) == 0:
            return None

        popped_snapshot = self._stack.pop()

        # Deep copy for return isolation
        returned_snapshot = copy.deepcopy(popped_snapshot)

        # Isolate grid and twist_state in returned copy
        isolated_grid = _deep_copy_grid(returned_snapshot.grid)
        object.__setattr__(returned_snapshot, "grid", isolated_grid)

        isolated_twist = _deep_copy_twist_state(returned_snapshot.twist_state)
        object.__setattr__(returned_snapshot, "twist_state", isolated_twist)

        gs = getattr(returned_snapshot, "game_state", None)
        if gs is not None:
            isolated_gs = copy.deepcopy(gs)
            object.__setattr__(returned_snapshot, "game_state", isolated_gs)

        return returned_snapshot

    def can_undo(self) -> bool:
        """Return True if stack non-empty, False otherwise.

        Returns:
            True if undo possible, False if empty.
        """
        return len(self._stack) > 0

    def clear(self) -> None:
        """Clear all history."""
        self._stack.clear()

    def __len__(self) -> int:
        """Return number of snapshots in stack.

        Returns:
            Count of snapshots.
        """
        return len(self._stack)

    def peek(self) -> Optional[HistorySnapshot]:
        """Return deep copy of last snapshot without popping, None if empty.

        Returns:
            Deep copy of last snapshot, or None if empty.
        """
        if len(self._stack) == 0:
            return None

        last_snapshot = self._stack[-1]
        peeked_copy = copy.deepcopy(last_snapshot)

        # Ensure isolation for peeked copy
        isolated_grid = _deep_copy_grid(peeked_copy.grid)
        object.__setattr__(peeked_copy, "grid", isolated_grid)

        isolated_twist = _deep_copy_twist_state(peeked_copy.twist_state)
        object.__setattr__(peeked_copy, "twist_state", isolated_twist)

        gs = getattr(peeked_copy, "game_state", None)
        if gs is not None:
            isolated_gs = copy.deepcopy(gs)
            object.__setattr__(peeked_copy, "game_state", isolated_gs)

        return peeked_copy