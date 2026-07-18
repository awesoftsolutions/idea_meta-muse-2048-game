"""
tests/test_achievements.py — TDD tests for 12 distinct achievements + Q-004 final validation.

Covers merges, score, heat, undo, board state plus Q-004 cold_fusion fix final validation
per pseudocode phase_3_sprint_2_wave1_tasks_1_2_code.md:
- cold_fusion true only when any merge source_heats == (0,0)
- false when (2,0)(1,1)(2,1) only no false positives
- true mixed with one (0,0), false empty merges, false None context

Headless, stdlib only, no pygame.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from src.core.board import BOARD_SIZE, MergeInfo, SlideResult, Tile, create_empty_grid
from src.core.history import HistoryStack
from src.core.score import ScoreState


def make_empty_grid() -> List[List[Optional[Tile]]]:
    return create_empty_grid()


def make_tile_grid(int_grid: List[List[Optional[int]]]) -> List[List[Optional[Tile]]]:
    result: List[List[Optional[Tile]]] = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            val = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            if val is None:
                result[r][c] = None
            else:
                result[r][c] = Tile(value=val, heat=0)
    return result


def _empty_int_grid() -> List[List[Optional[int]]]:
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def make_full_tile_grid(value: int = 2, heat: int = 0) -> List[List[Optional[Tile]]]:
    grid: List[List[Optional[Tile]]] = []
    for _ in range(BOARD_SIZE):
        row: List[Optional[Tile]] = []
        for _ in range(BOARD_SIZE):
            row.append(Tile(value=value, heat=heat))
        grid.append(row)
    return grid


def make_score_state(current_score: int = 0) -> ScoreState:
    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir) / "high_score.json"
    state = ScoreState(high_score_path=tmp_path)
    state.current_score = current_score
    return state


def make_slide_result(merges: Optional[List[MergeInfo]] = None) -> SlideResult:
    grid = create_empty_grid()
    return SlideResult(grid=grid, score_delta=0, moved=False, merges=merges if merges is not None else [])


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
    from src.core.achievements import GameContext

    effective_board = board if board is not None else create_empty_grid()
    effective_score = score if score is not None else make_score_state(0)
    effective_history = history if history is not None else HistoryStack()
    effective_twist = twist if twist is not None else {}
    effective_slide = last_slide_result if last_slide_result is not None else make_slide_result()
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


def test_achievement_def_creation() -> None:
    from src.core.achievements import AchievementDef

    def cond(ctx: object) -> bool:
        return True

    result = AchievementDef(id="first_merge", name="First Merge", description="test", condition=cond)
    assert result.id == "first_merge"
    assert result.unlocked is False


def test_game_context_fields() -> None:
    ctx = make_context()
    assert ctx.board is not None
    assert hasattr(ctx, "move_count")
    assert hasattr(ctx, "total_merges")


def test_first_merge_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(total_merges=1, move_count=1)
    newly = mgr.evaluate(ctx)
    assert "first_merge" in [a.id for a in newly]


def test_first_merge_no_false_positive() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(total_merges=0, move_count=1)
    newly = mgr.evaluate(ctx)
    assert "first_merge" not in [a.id for a in newly]


def test_128_tile_unlocks() -> None:
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    int_grid[0][0] = 128
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, move_count=1)
    assert "128_tile" in [a.id for a in mgr.evaluate(ctx)]


def test_128_tile_no_false_positive() -> None:
    from src.core.achievements import Achievements

    int_grid = _empty_int_grid()
    int_grid[0][0] = 64
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, move_count=1)
    assert "128_tile" not in [a.id for a in mgr.evaluate(ctx)]


def test_triple_merge_unlocks() -> None:
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=4, source_positions=[(0, 2), (0, 3)], heat_gen=1),
        MergeInfo(position=(0, 2), value=8, source_positions=[(1, 0), (1, 1)], heat_gen=1),
    ]
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=merges), move_count=1)
    assert "triple_merge" in [a.id for a in mgr.evaluate(ctx)]


def test_cool_operator_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(vent_streak=5, move_count=5)
    assert "cool_operator" in [a.id for a in mgr.evaluate(ctx)]


def test_meltdown_survivor_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(unstable_survival=3, move_count=3)
    assert "meltdown_survivor" in [a.id for a in mgr.evaluate(ctx)]


def test_undo_master_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(undo_count=5, move_count=5)
    assert "undo_master" in [a.id for a in mgr.evaluate(ctx)]


def test_score_1000_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(score=make_score_state(1000), move_count=10)
    assert "score_1000" in [a.id for a in mgr.evaluate(ctx)]


def test_full_board_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(board=make_full_tile_grid(), move_count=10)
    assert "full_board" in [a.id for a in mgr.evaluate(ctx)]


def test_heat_wave_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(board=make_full_tile_grid(value=2, heat=2), move_count=10)
    assert "heat_wave" in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_unlocks() -> None:
    from src.core.achievements import Achievements

    merge = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
    slide_result = make_slide_result(merges=[merge])
    int_grid = _empty_int_grid()
    int_grid[0][0] = 4
    tile_grid = make_tile_grid(int_grid)
    mgr = Achievements()
    ctx = make_context(board=tile_grid, last_slide_result=slide_result, move_count=1)
    assert "cold_fusion" in [a.id for a in mgr.evaluate(ctx)]


def test_chain_reaction_unlocks() -> None:
    from src.core.achievements import Achievements

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1),
        MergeInfo(position=(0, 1), value=8, source_positions=[(0, 2), (0, 3)], heat_gen=1),
    ]
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=merges), move_count=1)
    assert "chain_reaction" in [a.id for a in mgr.evaluate(ctx)]


def test_centurion_unlocks() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(move_count=100)
    assert "centurion" in [a.id for a in mgr.evaluate(ctx)]


def test_get_all_returns_12_distinct() -> None:
    from src.core.achievements import Achievements

    mgr = Achievements()
    all_ach = mgr.get_all()
    assert len(all_ach) == 12
    assert len(set(a.id for a in all_ach)) == 12


def test_no_pygame_import() -> None:
    """AC-8: pygame not in sys.modules after importing achievements via delta check."""
    before_has_pygame = "pygame" in sys.modules
    before_keys = set(sys.modules.keys())
    import src.core.achievements  # noqa: F401

    after_keys = set(sys.modules.keys())
    new_keys = after_keys - before_keys
    if not before_has_pygame:
        pygame_new = [k for k in new_keys if "pygame" in k.lower()]
        assert not pygame_new, f"pygame leaked in delta: {pygame_new}"


# ---------------------------------------------------------------------------
# Q-004 Final Validation — cold_fusion fix per pseudocode
# ---------------------------------------------------------------------------


def test_cold_fusion_true_only_0_0() -> None:
    """AC-8: cold_fusion true when any merge source_heats == (0,0)."""
    from src.core.achievements import Achievements

    merge = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
    object.__setattr__(merge, "source_heats", (0, 0))
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=[merge]), move_count=1)
    assert "cold_fusion" in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_2_0_no_false_positive() -> None:
    """AC-9: cold_fusion false when (2,0) only."""
    from src.core.achievements import Achievements

    m = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
    object.__setattr__(m, "source_heats", (2, 0))
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=[m]), move_count=1)
    assert "cold_fusion" not in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_1_1_no_false_positive() -> None:
    """AC-9: false when (1,1) only."""
    from src.core.achievements import Achievements

    m = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
    object.__setattr__(m, "source_heats", (1, 1))
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=[m]), move_count=1)
    assert "cold_fusion" not in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_2_1_no_false_positive() -> None:
    """AC-9: false when (2,1) only."""
    from src.core.achievements import Achievements

    m = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
    object.__setattr__(m, "source_heats", (2, 1))
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=[m]), move_count=1)
    assert "cold_fusion" not in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_mixed_hot_merges_no_false_positive() -> None:
    """AC-9: false when merges (2,0)(1,1)(2,1) only no false positives."""
    from src.core.achievements import Achievements

    merges = []
    for heats in [(2, 0), (1, 1), (2, 1)]:
        mm = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
        object.__setattr__(mm, "source_heats", heats)
        merges.append(mm)
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=merges), move_count=1)
    assert "cold_fusion" not in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_true_mixed_with_one_0_0() -> None:
    """Edge: true when mixed list contains one (0,0) among hot merges."""
    from src.core.achievements import Achievements

    merges = []
    for heats in [(2, 0), (0, 0), (1, 1)]:
        mm = MergeInfo(position=(0, 0), value=4, source_positions=[(0, 0), (0, 1)], heat_gen=1)
        object.__setattr__(mm, "source_heats", heats)
        merges.append(mm)
    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=merges), move_count=1)
    assert "cold_fusion" in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_empty_merges() -> None:
    """Edge: false when no merges."""
    from src.core.achievements import Achievements

    mgr = Achievements()
    ctx = make_context(last_slide_result=make_slide_result(merges=[]), move_count=1)
    assert "cold_fusion" not in [a.id for a in mgr.evaluate(ctx)]


def test_cold_fusion_false_none_context() -> None:
    """Edge: false when context None."""
    from src.core.achievements import GameContext

    # Directly test condition_cold_fusion via factory
    from src.core.achievements import _create_achievements_list

    achievements = _create_achievements_list()
    cold_fusion_def = next(a for a in achievements if a.id == "cold_fusion")
    assert cold_fusion_def.condition(None) is False
