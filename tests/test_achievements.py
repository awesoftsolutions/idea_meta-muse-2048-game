"""
tests/test_achievements.py — TDD tests for 12 distinct achievements.

Covers merges, score, heat, undo, board state using pure Python deterministic
synthetic GameContext. No pygame import, no global random, headless.

TDD red phase: these tests MUST FAIL initially because src/core/achievements.py
does not exist yet. Expected failure: ModuleNotFoundError / ImportError.

Production module under test: src/core/achievements.py
  - AchievementDef dataclass id, name, description, condition, unlocked, unlock_move
  - GameContext dataclass board, score, history, twist, last_slide_result,
    move_count, total_merges, vent_streak, unstable_survival, undo_count
  - Achievements manager evaluate->newly unlocked, get_all 12 distinct, is_unlocked

Synthetic builders:
  - make_empty_grid() -> 5x5 None
  - make_tile_grid(int_grid) -> Tile grid heat 0
  - make_tile_grid_with_heat(int_grid, heat_grid) -> Tile grid with heats
  - make_context(**overrides) -> GameContext with defaults
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from src.core.board import (
    BOARD_SIZE,
    MergeInfo,
    SlideResult,
    Tile,
    create_empty_grid,
)
from src.core.history import HistoryStack
from src.core.score import ScoreState


# ---------------------------------------------------------------------------
# Helpers — Tile grids
# ---------------------------------------------------------------------------


def make_empty_grid() -> List[List[Optional[Tile]]]:
    """Return 5x5 None grid."""
    return create_empty_grid()


def make_tile_grid(
    int_grid: List[List[Optional[int]]],
) -> List[List[Optional[Tile]]]:
    """Convert int grid to Tile grid heat=0. None stays None."""
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            val = (
                int_grid[r][c]
                if r < len(int_grid) and c < len(int_grid[r])
                else None
            )
            if val is None:
                result[r][c] = None
            else:
                result[r][c] = Tile(value=val, heat=0)
    return result


def make_tile_grid_with_heat(
    int_grid: List[List[Optional[int]]],
    heat_grid: List[List[Optional[int]]],
) -> List[List[Optional[Tile]]]:
    """Convert int grid + heat grid to Tile grid with specified heats."""
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = (
                int_grid[r][c]
                if r < len(int_grid) and c < len(int_grid[r])
                else None
            )
            if v is None:
                result[r][c] = None
            else:
                h = (
                    heat_grid[r][c]
                    if r < len(heat_grid)
                    and c < len(heat_grid[r])
                    and heat_grid[r][c] is not None
                    else 0
                )
                result[r][c] = Tile(value=v, heat=int(h))
    return result


def _empty_int_grid() -> List[List[Optional[int]]]:
    """Return 5x5 None int grid."""
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def make_full_tile_grid(
    value: int = 2, heat: int = 0
) -> List[List[Optional[Tile]]]:
    """Return 5x5 full grid of Tile(value, heat)."""
    grid: List[List[Optional[Tile]]] = []
    for _ in range(BOARD_SIZE):
        row: List[Optional[Tile]] = []
        for _ in range(BOARD_SIZE):
            row.append(Tile(value=value, heat=heat))
        grid.append(row)
    return grid


def make_score_state(current_score: int = 0) -> ScoreState:
    """Create ScoreState with injectable temp path and given current_score."""
    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir) / "high_score.json"
    state = ScoreState(high_score_path=tmp_path)
    state.current_score = current_score
    return state


def make_slide_result(
    merges: Optional[List[MergeInfo]] = None,
) -> SlideResult:
    """Create SlideResult with empty grid and given merges."""
    grid = create_empty_grid()
    return SlideResult(
        grid=grid,
        score_delta=0,
        moved=False,
        merges=merges if merges is not None else [],
    )


def make_context(
    board: Optional[List[List[Optional[Tile]]]] = None,
    score: Optional[ScoreState] = None,
    history: Optional[HistoryStack] = None,
    twist: Optional[Dict] = None,
    last_slide_result: Optional[SlideResult] = None,
    move_count: int = 0,
    total_merges: int = 0,
    vent_streak: int = 0,
    unstable_survival: int = 0,
    undo_count: int = 0,
) -> object:
    """Synthetic GameContext builder with defaults.

    Returns GameContext instance from src.core.achievements.
    """
    # Import here to allow TDD red phase failure to be explicit
    from src.core.achievements import GameContext

    effective_board = board if board is not None else create_empty_grid()
    effective_score = score if score is not None else make_score_state(0)
    effective_history = history if history is not None else HistoryStack()
    effective_twist = twist if twist is not None else {}
    effective_slide = (
        last_slide_result if last_slide_result is not None else make_slide_result()
    )

    return GameContext(
        board=effective_board,
        score=effective_score,
        history=effective_history,
        twist=effective_twist,
        last_slide_result=effective_slide,
        move_count=move_count,
        total_merges=total_merges,
        vent_streak=vent_streak,
        unstable_survival=unstable_survival,
        undo_count=undo_count,
    )


# ---------------------------------------------------------------------------
# AC-1: AchievementDef creation
# ---------------------------------------------------------------------------


def test_achievement_def_creation() -> None:
    """AC-1: AchievementDef with id first_merge unlocked false initially."""
    from src.core.achievements import AchievementDef

    def cond(ctx: object) -> bool:
        return True

    result = AchievementDef(
        id="first_merge",
        name="First Merge",
        description="test",
        condition=cond,
    )
    assert result.id == "first_merge"
    assert result.unlocked is False
    assert result.unlock_move is None
    assert callable(result.condition)


# ---------------------------------------------------------------------------
# AC-9: GameContext fields
# ---------------------------------------------------------------------------


def test_game_context_fields() -> None:
    """AC-9: GameContext contains required fields."""
    ctx = make_context()
    assert ctx.board is not None
    assert ctx.score is not None
    assert hasattr(ctx, "move_count")
    assert hasattr(ctx, "total_merges")
    assert hasattr(ctx, "vent_streak")
    assert hasattr(ctx, "unstable_survival")
    assert hasattr(ctx, "undo_count")
    assert hasattr(ctx, "history")
    assert hasattr(ctx, "twist")
    assert hasattr(ctx, "last_slide_result")


# ---------------------------------------------------------------------------
# first_merge
# ---------------------------------------------------------------------------


def test_first_merge_unlocks() -> None:
    """AC-2: first_merge unlocks when total_merges>=1."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(total_merges=1, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "first_merge" in ids
    assert mgr.is_unlocked("first_merge") is True


def test_first_merge_no_false_positive() -> None:
    """AC-5: first_merge no false positive when total_merges=0."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(total_merges=0, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "first_merge" not in ids
    assert mgr.is_unlocked("first_merge") is False


# ---------------------------------------------------------------------------
# 128_tile
# ---------------------------------------------------------------------------


def test_128_tile_unlocks() -> None:
    """AC-3: 128_tile unlocks when Tile value 128 exists."""
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    int_grid[0][0] = 128
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "128_tile" in ids


def test_128_tile_no_false_positive() -> None:
    """AC-5: 128_tile no false positive when max value 64."""
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    int_grid[0][0] = 64
    int_grid[0][1] = 32
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "128_tile" not in ids


# ---------------------------------------------------------------------------
# triple_merge
# ---------------------------------------------------------------------------


def test_triple_merge_unlocks() -> None:
    """AC-4: triple_merge unlocks when 3 merges in one move."""
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=4, source_positions=[(0, 2), (0, 3)], heat_gen=1),
        MergeInfo(position=(0, 2), value=8, source_positions=[(1, 0), (1, 1)], heat_gen=1),
    ]
    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "triple_merge" in ids


def test_triple_merge_no_false_positive() -> None:
    """AC-5: triple_merge no false positive with 2 merges."""
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=4, source_positions=[(0, 2), (0, 3)], heat_gen=1),
    ]
    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "triple_merge" not in ids


# ---------------------------------------------------------------------------
# cool_operator
# ---------------------------------------------------------------------------


def test_cool_operator_unlocks() -> None:
    """cool_operator unlocks when vent_streak>=5."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(vent_streak=5, move_count=5)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cool_operator" in ids


def test_cool_operator_no_false_positive() -> None:
    """cool_operator no false positive when vent_streak=4."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(vent_streak=4, move_count=4)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cool_operator" not in ids


# ---------------------------------------------------------------------------
# meltdown_survivor
# ---------------------------------------------------------------------------


def test_meltdown_survivor_unlocks() -> None:
    """meltdown_survivor unlocks when unstable_survival>=3."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(unstable_survival=3, move_count=3)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "meltdown_survivor" in ids


def test_meltdown_survivor_no_false_positive() -> None:
    """meltdown_survivor no false positive when unstable_survival=2."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(unstable_survival=2, move_count=2)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "meltdown_survivor" not in ids


# ---------------------------------------------------------------------------
# undo_master
# ---------------------------------------------------------------------------


def test_undo_master_unlocks() -> None:
    """undo_master unlocks when undo_count>=5."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(undo_count=5, move_count=5)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "undo_master" in ids


def test_undo_master_no_false_positive() -> None:
    """undo_master no false positive when undo_count=4."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(undo_count=4, move_count=4)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "undo_master" not in ids


# ---------------------------------------------------------------------------
# score_1000
# ---------------------------------------------------------------------------


def test_score_1000_unlocks() -> None:
    """score_1000 unlocks when current_score>=1000."""
    from src.core.achievements import Achievements

    score_state = make_score_state(current_score=1000)
    mgr = Achievements()
    ctx = make_context(score=score_state, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "score_1000" in ids


def test_score_1000_no_false_positive() -> None:
    """score_1000 no false positive when current_score=999."""
    from src.core.achievements import Achievements

    score_state = make_score_state(current_score=999)
    mgr = Achievements()
    ctx = make_context(score=score_state, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "score_1000" not in ids


# ---------------------------------------------------------------------------
# full_board
# ---------------------------------------------------------------------------


def test_full_board_unlocks() -> None:
    """full_board unlocks when no empty cells."""
    from src.core.achievements import Achievements

    full_grid = make_full_tile_grid(value=2, heat=0)
    mgr = Achievements()
    ctx = make_context(board=full_grid, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "full_board" in ids


def test_full_board_no_false_positive() -> None:
    """full_board no false positive when one None cell."""
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    # Fill all but one
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if not (r == 0 and c == 0):
                int_grid[r][c] = 2
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "full_board" not in ids


# ---------------------------------------------------------------------------
# heat_wave
# ---------------------------------------------------------------------------


def test_heat_wave_unlocks() -> None:
    """heat_wave unlocks when avg heat >1.5."""
    from src.core.achievements import Achievements

    # 25 tiles heat 2 => avg 2.0
    full_grid = make_full_tile_grid(value=2, heat=2)
    mgr = Achievements()
    ctx = make_context(board=full_grid, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "heat_wave" in ids


def test_heat_wave_no_false_positive() -> None:
    """heat_wave no false positive when avg heat 1.0."""
    from src.core.achievements import Achievements

    full_grid = make_full_tile_grid(value=2, heat=1)
    mgr = Achievements()
    ctx = make_context(board=full_grid, move_count=10)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "heat_wave" not in ids


# ---------------------------------------------------------------------------
# cold_fusion
# ---------------------------------------------------------------------------


def test_cold_fusion_unlocks() -> None:
    """cold_fusion unlocks when merge two heat 0 tiles (heat_gen<=1 proxy)."""
    from src.core.achievements import Achievements

    # Merge with heat_gen 1 and source_positions >=2
    merge = MergeInfo(
        position=(0, 0),
        value=4,
        source_positions=[(0, 0), (0, 1)],
        heat_gen=1,
    )
    slide_result = make_slide_result(merges=[merge])
    int_grid = _empty_int_grid()
    int_grid[0][0] = 4
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(
        board=tile_grid, last_slide_result=slide_result, move_count=1
    )
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cold_fusion" in ids


def test_cold_fusion_no_false_positive() -> None:
    """cold_fusion no false positive when no merges."""
    from src.core.achievements import Achievements

    slide_result = make_slide_result(merges=[])
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cold_fusion" not in ids


# ---------------------------------------------------------------------------
# chain_reaction
# ---------------------------------------------------------------------------


def test_chain_reaction_unlocks() -> None:
    """chain_reaction unlocks when 2 merges second value > first."""
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=8, source_positions=[(0, 2), (0, 3)], heat_gen=1),
    ]
    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "chain_reaction" in ids


def test_chain_reaction_no_false_positive() -> None:
    """chain_reaction no false positive with single merge."""
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
    ]
    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "chain_reaction" not in ids


# ---------------------------------------------------------------------------
# centurion
# ---------------------------------------------------------------------------


def test_centurion_unlocks() -> None:
    """centurion unlocks when move_count>=100."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(move_count=100)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "centurion" in ids


def test_centurion_no_false_positive() -> None:
    """centurion no false positive when move_count=99."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(move_count=99)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "centurion" not in ids


# ---------------------------------------------------------------------------
# Additional: get_all, is_unlocked, evaluate semantics, isolation
# ---------------------------------------------------------------------------


def test_get_all_returns_12_distinct() -> None:
    """AC-6: get_all returns 12 distinct achievements."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    all_ach = mgr.get_all()
    assert len(all_ach) == 12, f"Expected 12, got {len(all_ach)}"
    ids = [a.id for a in all_ach]
    assert len(set(ids)) == 12, f"Duplicate ids found: {ids}"


def test_is_unlocked_true_after_unlock() -> None:
    """AC-7: is_unlocked true after unlock."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    assert mgr.is_unlocked("first_merge") is False
    ctx = make_context(total_merges=1, move_count=1)
    newly = mgr.evaluate(ctx)
    assert len(newly) == 1
    assert mgr.is_unlocked("first_merge") is True


def test_is_unlocked_false_before() -> None:
    """is_unlocked false before any unlock."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    assert mgr.is_unlocked("first_merge") is False
    assert mgr.is_unlocked("128_tile") is False
    assert mgr.is_unlocked("centurion") is False


def test_is_unlocked_unknown_id() -> None:
    """is_unlocked returns False for unknown id, not crash."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    assert mgr.is_unlocked("nonexistent") is False
    assert mgr.is_unlocked("") is False


def test_evaluate_returns_only_newly_unlocked() -> None:
    """Second evaluate same context returns empty (already unlocked)."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(total_merges=1, move_count=1)
    newly1 = mgr.evaluate(ctx)
    assert len(newly1) == 1
    newly2 = mgr.evaluate(ctx)
    assert len(newly2) == 0, "Already unlocked should return empty"


def test_evaluate_multiple_unlocks_same_move() -> None:
    """Multiple achievements can unlock same move, distinct ids."""
    from src.core.achievements import Achievements

    # Build context triggering many achievements at once
    full_grid = make_full_tile_grid(value=128, heat=2)
    score_state = make_score_state(current_score=1000)
    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=8, source_positions=[(0, 2), (0, 3)], heat_gen=1),
        MergeInfo(position=(0, 2), value=16, source_positions=[(1, 0), (1, 1)], heat_gen=1),
    ]
    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(
        board=full_grid,
        score=score_state,
        last_slide_result=slide_result,
        move_count=100,
        total_merges=10,
        vent_streak=5,
        unstable_survival=3,
        undo_count=5,
    )
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert len(newly) >= 5, f"Expected >=5 unlocks, got {len(newly)}: {ids}"
    assert len(set(ids)) == len(ids), f"Duplicate ids in newly unlocked: {ids}"


def test_no_pygame_import() -> None:
    """AC-8: pygame not in sys.modules after importing achievements."""
    # Snapshot before
    assert "pygame" not in sys.modules, "pygame should not be loaded before test"
    # Import achievements module
    import src.core.achievements  # noqa: F401

    assert "pygame" not in sys.modules, "pygame leaked via achievements import"
    assert "pygame-ce" not in sys.modules
    assert "pygame_ce" not in sys.modules


def test_deterministic_repeatability() -> None:
    """Same synthetic context twice yields same unlocks with fresh managers."""
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    int_grid[0][0] = 128
    tile_grid = make_tile_grid(int_grid)

    mgr1 = Achievements()
    ctx1 = make_context(board=tile_grid, total_merges=1, move_count=1)
    newly1 = mgr1.evaluate(ctx1)
    ids1 = sorted([a.id for a in newly1])

    mgr2 = Achievements()
    ctx2 = make_context(board=tile_grid, total_merges=1, move_count=1)
    newly2 = mgr2.evaluate(ctx2)
    ids2 = sorted([a.id for a in newly2])

    assert ids1 == ids2, f"Deterministic repeatability failed: {ids1} vs {ids2}"


def test_full_board_empty_no_unlock() -> None:
    """Edge: empty board should not unlock full_board."""
    from src.core.achievements import Achievements

    empty_grid = make_empty_grid()
    mgr = Achievements()
    ctx = make_context(board=empty_grid, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "full_board" not in ids
    assert "heat_wave" not in ids
    assert "128_tile" not in ids


# ---------------------------------------------------------------------------
# Phase 3 Sprint 1 — cold_fusion fix Q-004 source_heats both 0
# ---------------------------------------------------------------------------


def test_cold_fusion_true_0_0() -> None:
    """AC-17: cold_fusion true only when any merge source_heats == (0,0)."""
    from src.core.achievements import Achievements

    merge = MergeInfo(
        position=(0, 0),
        value=4,
        source_positions=[(0, 0), (0, 1)],
        heat_gen=1,
    )
    # Inject source_heats attribute for new API
    object.__setattr__(merge, "source_heats", (0, 0))

    slide_result = make_slide_result(merges=[merge])
    int_grid = _empty_int_grid()
    int_grid[0][0] = 4
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cold_fusion" in ids, f"Expected cold_fusion unlock for (0,0), got {ids}"


def test_cold_fusion_false_hot_merges() -> None:
    """AC-18: cold_fusion false for hot merges (2,0)(1,1)(2,1) no false positives."""
    from src.core.achievements import Achievements

    merges = []
    for heats in [(2, 0), (1, 1), (2, 1)]:
        m = MergeInfo(
            position=(0, 0),
            value=4,
            source_positions=[(0, 0), (0, 1)],
            heat_gen=1,
        )
        object.__setattr__(m, "source_heats", heats)
        merges.append(m)

    slide_result = make_slide_result(merges=merges)
    mgr = Achievements()
    ctx = make_context(last_slide_result=slide_result, move_count=1)
    newly = mgr.evaluate(ctx)
    ids = [a.id for a in newly]
    assert "cold_fusion" not in ids, f"cold_fusion should NOT unlock for hot merges {[(2,0),(1,1),(2,1)]}, got {ids}"

    # Also test each individually
    for heats in [(2, 0), (1, 1), (2, 1)]:
        m = MergeInfo(
            position=(0, 0),
            value=4,
            source_positions=[(0, 0), (0, 1)],
            heat_gen=1,
        )
        object.__setattr__(m, "source_heats", heats)
        sr = make_slide_result(merges=[m])
        mgr2 = Achievements()
        ctx2 = make_context(last_slide_result=sr, move_count=1)
        newly2 = mgr2.evaluate(ctx2)
        ids2 = [a.id for a in newly2]
        assert "cold_fusion" not in ids2, f"False positive for {heats}"