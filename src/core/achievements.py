"""src/core/achievements.py — Achievements system with 12 distinct conditions.

Purpose: Implements AchievementDef dataclass with condition callable,
    GameContext dataclass aggregating board, score, history, twist,
    last_slide_result, move_count, total_merges, vent_streak,
    unstable_survival, undo_count, plus helpers _check_board_has_128,
    _check_full_board, _calc_average_heat, factory
    _create_achievements_list creating 12 distinct conditions, and
    Achievements manager with evaluate returning newly unlocked list,
    get_all returning 12 distinct, is_unlocked query. Pure Python
    deterministic, no pygame, no global random, headless testable.

System: src/core per Phase 2 architecture ADR-014, ADR-015.

Dependencies: stdlib only — dataclasses, typing. Plus src.core.board
    Tile, MergeInfo, SlideResult, BOARD_SIZE. Never pygame-ce.

Used-by: src/core/__init__.py exports, tests/test_achievements.py,
    future game loop integration Task 2.

Public interface:
    - AchievementDef: dataclass id, name, description, condition,
      unlocked bool=False, unlock_move Optional[int]=None,
      __post_init__ validation id non-empty condition callable
    - GameContext: dataclass board, score, history, twist,
      last_slide_result, move_count, total_merges, vent_streak,
      unstable_survival, undo_count, __post_init__ validation
    - Achievements: manager owning 12 achievements, methods
      __init__, evaluate, get_all, is_unlocked
    - _check_board_has_128, _check_full_board, _calc_average_heat:
      internal helpers
    - _create_achievements_list: factory creating 12 distinct
"""

# CHANGELOG:
# - Phase 3 Sprint 1: MODIFIED cold_fusion fix source_heats both 0 not proxy
#   no false positives Q-004 ADR-017.
# - Sprint 3 — 12 distinct achievements (first_merge, 128_tile, triple_merge,
#   cool_operator, meltdown_survivor, undo_master, score_1000, full_board,
#   heat_wave, cold_fusion, chain_reaction, centurion) with GameContext
#   aggregating board/score/history/twist/last_slide_result/move_count/
#   total_merges/vent_streak/unstable_survival/undo_count and Achievements
#   manager (evaluate, get_all, is_unlocked). Pure Python deterministic,
#   stdlib only, headless testable per ADR-014/ADR-015.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Type aliases (avoid hard import of ScoreState/HistoryStack to keep loose coupling)
# ---------------------------------------------------------------------------

BoardGrid = List[List[Optional[Any]]]


# ---------------------------------------------------------------------------
# AchievementDef dataclass
# ---------------------------------------------------------------------------


@dataclass
class AchievementDef:
    """Single achievement with condition callable.

    Attributes:
        id: Unique identifier, non-empty.
        name: Display name.
        description: Human readable description.
        condition: Callable[[GameContext], bool] pure function.
        unlocked: Whether achievement is unlocked, default False.
        unlock_move: Move count when unlocked, default None.

    Raises:
        ValueError: If id is empty.
        TypeError: If condition is None or not callable.
    """

    id: str
    name: str
    description: str
    condition: Callable[["GameContext"], bool]
    unlocked: bool = False
    unlock_move: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or self.id.strip() == "":
            raise ValueError("AchievementDef id must be non-empty string")
        if self.condition is None or not callable(self.condition):
            raise TypeError("AchievementDef condition must be callable")


# ---------------------------------------------------------------------------
# GameContext dataclass
# ---------------------------------------------------------------------------


@dataclass
class GameContext:
    """Container for all state needed to evaluate achievements.

    Attributes:
        board: BoardGrid 5x5 List[List[Optional[Tile]]] current board state.
        score: ScoreState with current_score attribute.
        history: HistoryStack for undo tracking.
        twist: HeatState or dict containing heat stats generic.
        last_slide_result: SlideResult with merges List[MergeInfo].
        move_count: Total moves executed.
        total_merges: Cumulative merges across game.
        vent_streak: Consecutive vent moves.
        unstable_survival: Moves survived with unstable tiles.
        undo_count: Number of undos performed.

    Raises:
        ValueError: If board is None, score is None, move_count <0.
    """

    board: BoardGrid
    score: Any
    history: Any
    twist: Any
    last_slide_result: Any
    move_count: int
    total_merges: int = 0
    vent_streak: int = 0
    unstable_survival: int = 0
    undo_count: int = 0

    def __post_init__(self) -> None:
        if self.board is None:
            raise ValueError("board required")
        if self.score is None:
            raise ValueError("score required")
        # move_count validation
        if self.move_count is None:
            raise ValueError("move_count must be >=0")
        if not isinstance(self.move_count, int) or self.move_count < 0:
            raise ValueError("move_count must be >=0")

        # Default None int fields to 0 for robustness
        if self.total_merges is None:
            object.__setattr__(self, "total_merges", 0)
        if self.vent_streak is None:
            object.__setattr__(self, "vent_streak", 0)
        if self.unstable_survival is None:
            object.__setattr__(self, "unstable_survival", 0)
        if self.undo_count is None:
            object.__setattr__(self, "undo_count", 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_board_has_128(board: BoardGrid) -> bool:
    """Check if any Tile value >=128 exists on board.

    Args:
        board: BoardGrid 5x5.

    Returns:
        True if any Tile value >=128, False otherwise.
    """
    if board is None:
        return False
    try:
        for row in board:
            if row is None:
                continue
            for cell in row:
                if cell is None:
                    continue
                # Tile has value attribute
                val = getattr(cell, "value", None)
                if val is not None and isinstance(val, int) and val >= 128:
                    return True
        return False
    except Exception:
        return False


def _check_full_board(board: BoardGrid) -> bool:
    """Check if board has no empty cells.

    Args:
        board: BoardGrid.

    Returns:
        True if no None cells, False otherwise.
    """
    if board is None:
        return False
    try:
        for row in board:
            if row is None:
                return False
            for cell in row:
                if cell is None:
                    return False
        return True
    except Exception:
        return False


def _calc_average_heat(board: BoardGrid) -> float:
    """Calculate average heat over existing tiles.

    Args:
        board: BoardGrid.

    Returns:
        Average heat float, 0.0 if no tiles.
    """
    if board is None:
        return 0.0
    total_heat = 0
    tile_count = 0
    try:
        for row in board:
            if row is None:
                continue
            for cell in row:
                if cell is not None:
                    h = getattr(cell, "heat", 0)
                    if isinstance(h, int):
                        total_heat += h
                        tile_count += 1
        if tile_count == 0:
            return 0.0
        return total_heat / tile_count
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Factory: _create_achievements_list - 12 distinct conditions
# ---------------------------------------------------------------------------


def _create_achievements_list() -> List[AchievementDef]:
    """Create 12 distinct AchievementDef instances with pure condition callables.

    Returns:
        List of 12 distinct AchievementDef.

    Notes:
        Conditions pure, no side effects, deterministic, handle None
        returning False to avoid false positives.
    """
    achievements: List[AchievementDef] = []

    def condition_first_merge(context: GameContext) -> bool:
        if context is None:
            return False
        if getattr(context, "total_merges", None) is None:
            return False
        try:
            return int(context.total_merges) >= 1
        except Exception:
            return False

    def condition_128_tile(context: GameContext) -> bool:
        if context is None:
            return False
        if getattr(context, "board", None) is None:
            return False
        return _check_board_has_128(context.board)

    def condition_triple_merge(context: GameContext) -> bool:
        if context is None:
            return False
        lsr = getattr(context, "last_slide_result", None)
        if lsr is None:
            return False
        merges = getattr(lsr, "merges", None)
        if merges is None:
            return False
        try:
            return len(merges) >= 3
        except Exception:
            return False

    def condition_cool_operator(context: GameContext) -> bool:
        if context is None:
            return False
        vs = getattr(context, "vent_streak", None)
        if vs is None:
            return False
        try:
            return int(vs) >= 5
        except Exception:
            return False

    def condition_meltdown_survivor(context: GameContext) -> bool:
        if context is None:
            return False
        us = getattr(context, "unstable_survival", None)
        if us is None:
            return False
        try:
            return int(us) >= 3
        except Exception:
            return False

    def condition_undo_master(context: GameContext) -> bool:
        if context is None:
            return False
        uc = getattr(context, "undo_count", None)
        if uc is None:
            return False
        try:
            return int(uc) >= 5
        except Exception:
            return False

    def condition_score_1000(context: GameContext) -> bool:
        if context is None:
            return False
        sc = getattr(context, "score", None)
        if sc is None:
            return False
        try:
            # Try current_score attribute, then score attribute, else 0
            if hasattr(sc, "current_score"):
                current = getattr(sc, "current_score")
            elif hasattr(sc, "score"):
                current = getattr(sc, "score")
            else:
                current = 0
            if current is None:
                return False
            return int(current) >= 1000
        except Exception:
            return False

    def condition_full_board(context: GameContext) -> bool:
        if context is None:
            return False
        if getattr(context, "board", None) is None:
            return False
        return _check_full_board(context.board)

    def condition_heat_wave(context: GameContext) -> bool:
        if context is None:
            return False
        if getattr(context, "board", None) is None:
            return False
        avg = _calc_average_heat(context.board)
        try:
            return float(avg) > 1.5
        except Exception:
            return False

    def condition_cold_fusion(context: GameContext) -> bool:
        """True only when any merge source_heats == (0,0) per ADR-017 Q-004 fix.

        No false positives for hot merges (2,0)(1,1)(2,1).

        Args:
            context: GameContext with board, score, history, twist,
                last_slide_result containing merges with source_heats.

        Returns:
            True if any merge has source_heats == (0,0), False otherwise
            including None context, empty merges, or hot merges.
        """
        if context is None:
            return False
        lsr = getattr(context, "last_slide_result", None)
        if lsr is None:
            return False
        merges = getattr(lsr, "merges", None)
        if merges is None:
            return False
        try:
            if len(merges) == 0:
                return False
        except Exception:
            return False
        try:
            for merge in merges:
                source_heats = getattr(merge, "source_heats", None)
                if source_heats is None:
                    continue
                try:
                    if isinstance(source_heats, (tuple, list)) and len(source_heats) == 2:
                        if source_heats[0] == 0 and source_heats[1] == 0:
                            return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def condition_chain_reaction(context: GameContext) -> bool:
        if context is None:
            return False
        lsr = getattr(context, "last_slide_result", None)
        if lsr is None:
            return False
        merges = getattr(lsr, "merges", None)
        if merges is None:
            return False
        try:
            if len(merges) < 2:
                return False
        except Exception:
            return False
        try:
            for i in range(1, len(merges)):
                prev_val = getattr(merges[i - 1], "value", None)
                curr_val = getattr(merges[i], "value", None)
                if prev_val is None or curr_val is None:
                    continue
                if int(curr_val) > int(prev_val):
                    return True
            return False
        except Exception:
            return False

    def condition_centurion(context: GameContext) -> bool:
        if context is None:
            return False
        mc = getattr(context, "move_count", None)
        if mc is None:
            return False
        try:
            return int(mc) >= 100
        except Exception:
            return False

    achievements.append(
        AchievementDef(
            id="first_merge",
            name="First Merge",
            description="Perform your first merge",
            condition=condition_first_merge,
        )
    )
    achievements.append(
        AchievementDef(
            id="128_tile",
            name="128 Tile",
            description="Create a 128 tile",
            condition=condition_128_tile,
        )
    )
    achievements.append(
        AchievementDef(
            id="triple_merge",
            name="Triple Merge",
            description="Perform 3 merges in one move",
            condition=condition_triple_merge,
        )
    )
    achievements.append(
        AchievementDef(
            id="cool_operator",
            name="Cool Operator",
            description="Maintain vent streak of 5",
            condition=condition_cool_operator,
        )
    )
    achievements.append(
        AchievementDef(
            id="meltdown_survivor",
            name="Meltdown Survivor",
            description="Survive 3 moves with unstable tiles",
            condition=condition_meltdown_survivor,
        )
    )
    achievements.append(
        AchievementDef(
            id="undo_master",
            name="Undo Master",
            description="Use undo 5 times",
            condition=condition_undo_master,
        )
    )
    achievements.append(
        AchievementDef(
            id="score_1000",
            name="Score 1000",
            description="Reach 1000 points",
            condition=condition_score_1000,
        )
    )
    achievements.append(
        AchievementDef(
            id="full_board",
            name="Full Board",
            description="Fill board with no empty cells",
            condition=condition_full_board,
        )
    )
    achievements.append(
        AchievementDef(
            id="heat_wave",
            name="Heat Wave",
            description="Average heat >1.5",
            condition=condition_heat_wave,
        )
    )
    achievements.append(
        AchievementDef(
            id="cold_fusion",
            name="Cold Fusion",
            description="Merge two heat 0 tiles",
            condition=condition_cold_fusion,
        )
    )
    achievements.append(
        AchievementDef(
            id="chain_reaction",
            name="Chain Reaction",
            description="2 merges where second value > first",
            condition=condition_chain_reaction,
        )
    )
    achievements.append(
        AchievementDef(
            id="centurion",
            name="Centurion",
            description="Reach 100 moves",
            condition=condition_centurion,
        )
    )

    return achievements


# ---------------------------------------------------------------------------
# Achievements Manager
# ---------------------------------------------------------------------------


class Achievements:
    """Manager owning 12 achievements, evaluating context, tracking unlocks.

    Attributes:
        _achievements: Internal list of AchievementDef.
        _by_id: Dict index id -> AchievementDef.

    Public methods:
        evaluate(context) -> List[AchievementDef]: returns newly unlocked.
        get_all() -> List[AchievementDef]: returns copy of 12 distinct.
        is_unlocked(id) -> bool: query unlock state.
    """

    def __init__(self) -> None:
        """Initialize manager with 12 distinct achievements."""
        result = _create_achievements_list()
        if len(result) != 12:
            raise ValueError(f"Expected 12 achievements, got {len(result)}")
        ids = [ach.id for ach in result]
        if len(set(ids)) != 12:
            raise ValueError("Duplicate achievement ids found")
        self._achievements: List[AchievementDef] = result
        self._by_id: Dict[str, AchievementDef] = {ach.id: ach for ach in result}

    def evaluate(self, context: GameContext) -> List[AchievementDef]:
        """Evaluate context and unlock matching achievements.

        Args:
            context: GameContext with board, score, etc.

        Returns:
            List of newly unlocked AchievementDef.

        Raises:
            ValueError: If context is None or board/score None.
        """
        if context is None:
            raise ValueError("GameContext required")
        if getattr(context, "board", None) is None or getattr(context, "score", None) is None:
            raise ValueError("Invalid context: board and score required")

        newly_unlocked: List[AchievementDef] = []
        for achievement in self._achievements:
            if achievement.unlocked:
                continue
            try:
                result = achievement.condition(context)
            except Exception:
                # Defensive: treat exception as False
                result = False
            if result:
                achievement.unlocked = True
                try:
                    achievement.unlock_move = int(context.move_count)
                except Exception:
                    achievement.unlock_move = 0
                newly_unlocked.append(achievement)
        return newly_unlocked

    def get_all(self) -> List[AchievementDef]:
        """Return copy of internal achievements list.

        Returns:
            Copy list of 12 distinct AchievementDef.
        """
        if not self._achievements:
            return []
        return list(self._achievements)

    def is_unlocked(self, achievement_id: str) -> bool:
        """Query if achievement is unlocked.

        Args:
            achievement_id: Achievement id to query.

        Returns:
            True if unlocked, False otherwise (including unknown id).
        """
        if achievement_id is None or achievement_id == "":
            return False
        if not isinstance(achievement_id, str):
            return False
        if achievement_id not in self._by_id:
            return False
        ach = self._by_id[achievement_id]
        return bool(ach.unlocked)
