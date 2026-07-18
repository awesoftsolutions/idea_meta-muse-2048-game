"""src/core/gamestate.py — GameState aggregator for Q-005 ownership.

Implements GameState dataclass owning streak counters per ADR-016:
vent_streak consecutive moves where any edge tile vented,
unstable_survival consecutive moves survived with unstable >=3 present,
undo_count total undo invocations ever, move_count total moves,
last_vent_occurred and last_unstable_present flags.

Purpose: Single owner of streak counters owned by main.py, passed via
GameContext to achievements, included in HistorySnapshot for exact restore.

System: src/core per Phase 3 architecture ADR-016.

Dependencies: stdlib only — dataclasses, typing. Never pygame-ce.

Used-by: src/core/__init__.py exports, src/core/history.py snapshot,
src/main.py production loop, tests/test_gamestate.py.

Public interface:
    - GameState: dataclass vent_streak, unstable_survival, undo_count,
      move_count, last_vent_occurred, last_unstable_present,
      methods update_after_turn, increment_undo, reset_on_new_game,
      __eq__, __repr__, __post_init__ clamping.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GameState:
    """Aggregator for streak counters Q-005 ownership per ADR-016.

    Attributes:
        vent_streak: Consecutive moves where vent occurred (any edge tile heat reduced).
        unstable_survival: Consecutive moves survived with unstable >=3 present.
        undo_count: Total undo invocations ever.
        move_count: Total moves executed.
        last_vent_occurred: Whether last turn had vent.
        last_unstable_present: Whether last turn had unstable.

    Definitions locked per ADR-016.
    """

    vent_streak: int = 0
    unstable_survival: int = 0
    undo_count: int = 0
    move_count: int = 0
    last_vent_occurred: bool = False
    last_unstable_present: bool = False

    def __post_init__(self) -> None:
        """Validate and clamp fields to 0/False defaults."""
        if self.vent_streak is None or not isinstance(self.vent_streak, int):
            object.__setattr__(self, "vent_streak", 0)
        if self.unstable_survival is None or not isinstance(self.unstable_survival, int):
            object.__setattr__(self, "unstable_survival", 0)
        if self.undo_count is None or not isinstance(self.undo_count, int):
            object.__setattr__(self, "undo_count", 0)
        if self.move_count is None or not isinstance(self.move_count, int):
            object.__setattr__(self, "move_count", 0)
        if self.last_vent_occurred is None:
            object.__setattr__(self, "last_vent_occurred", False)
        if self.last_unstable_present is None:
            object.__setattr__(self, "last_unstable_present", False)

        # Clamp negatives to 0
        if self.vent_streak < 0:
            object.__setattr__(self, "vent_streak", 0)
        if self.unstable_survival < 0:
            object.__setattr__(self, "unstable_survival", 0)
        if self.undo_count < 0:
            object.__setattr__(self, "undo_count", 0)
        if self.move_count < 0:
            object.__setattr__(self, "move_count", 0)

        # Coerce bools
        object.__setattr__(self, "last_vent_occurred", bool(self.last_vent_occurred))
        object.__setattr__(self, "last_unstable_present", bool(self.last_unstable_present))

    def update_after_turn(self, vent_occurred: bool, unstable_present: bool) -> None:
        """Update streak counters based on turn booleans, increment move_count.

        Args:
            vent_occurred: True if any edge tile vented this turn.
            unstable_present: True if any tile heat>=3 present this turn.
        """
        # Coerce to bool per spec
        vent_occurred = bool(vent_occurred)
        unstable_present = bool(unstable_present)

        if vent_occurred:
            self.vent_streak = self.vent_streak + 1
        else:
            self.vent_streak = 0
        self.last_vent_occurred = vent_occurred

        if unstable_present:
            self.unstable_survival = self.unstable_survival + 1
        else:
            self.unstable_survival = 0
        self.last_unstable_present = unstable_present

        self.move_count = self.move_count + 1

    def increment_undo(self) -> None:
        """Increment undo_count total invocations ever."""
        self.undo_count = self.undo_count + 1

    def reset_on_new_game(self) -> None:
        """Reset all counters to 0/False for new game."""
        self.vent_streak = 0
        self.unstable_survival = 0
        self.undo_count = 0
        self.move_count = 0
        self.last_vent_occurred = False
        self.last_unstable_present = False

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if not isinstance(other, GameState):
            return False
        return (
            self.vent_streak == other.vent_streak
            and self.unstable_survival == other.unstable_survival
            and self.undo_count == other.undo_count
            and self.move_count == other.move_count
            and self.last_vent_occurred == other.last_vent_occurred
            and self.last_unstable_present == other.last_unstable_present
        )

    def __repr__(self) -> str:
        return (
            f"GameState(vent_streak={self.vent_streak}, "
            f"unstable_survival={self.unstable_survival}, "
            f"undo_count={self.undo_count}, "
            f"move_count={self.move_count}, "
            f"last_vent_occurred={self.last_vent_occurred}, "
            f"last_unstable_present={self.last_unstable_present})"
        )
