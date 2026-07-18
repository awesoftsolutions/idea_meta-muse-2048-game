"""
tests/test_history.py — TDD red-phase tests for HistorySnapshot deep copy exact restore.

Covers AC-1..AC-8 per pseudocode phase_2_sprint_2_task_2_code.md:
- AC-1 snapshot preserves value heat
- AC-2 push deep copy isolation
- AC-3 undo exact restore
- AC-4 empty undo noop E004
- AC-5 new move after undo clears redo A B C undo B push D => A B D
- AC-6 multiple undos
- AC-7 can_undo
- AC-8 no pygame import
- Extra: deep copy grid mutation isolation

Headless, no pygame import at module level. Expected to FAIL initially
because src/core/history.py does not exist (TDD red phase).
"""

from __future__ import annotations

import sys
from typing import Dict, List, Optional

from src.core.board import Direction, Tile, create_empty_grid

# This import will fail in red phase — expected.
from src.core.history import HistorySnapshot, HistoryStack

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def empty_grid() -> List[List[Optional[Tile]]]:
    """Return 5x5 None grid via create_empty_grid."""
    return create_empty_grid()


def sample_grid_with_heat() -> List[List[Optional[Tile]]]:
    """Grid with Tile(4,1) at (0,0), Tile(2,0) at (1,1), Tile(8,2) at (2,2)."""
    grid = create_empty_grid()
    grid[0][0] = Tile(value=4, heat=1)
    grid[1][1] = Tile(value=2, heat=0)
    grid[2][2] = Tile(value=8, heat=2)
    return grid


def sample_twist_state() -> Dict:
    """Sample twist_state dict with avg_heat, vent_streak, unstable_count."""
    return {"avg_heat": 1.2, "vent_streak": 3, "unstable_count": 1}


def make_snapshot(
    grid: List[List[Optional[Tile]]],
    score: int,
    twist_state: Dict,
    move_number: int,
    direction: Direction,
) -> HistorySnapshot:
    """Helper to create HistorySnapshot."""
    return HistorySnapshot(
        grid=grid,
        score=score,
        twist_state=twist_state,
        move_number=move_number,
        direction=direction,
    )


# ---------------------------------------------------------------------------
# AC-1: snapshot preserves value heat
# ---------------------------------------------------------------------------


def test_snapshot_preserves_value_heat() -> None:
    """AC-1: HistorySnapshot deep copy preserves Tile value and heat."""
    tile = Tile(value=4, heat=1)
    grid = create_empty_grid()
    grid[0][0] = tile

    snapshot = HistorySnapshot(
        grid=grid,
        score=100,
        twist_state={"avg_heat": 1.0},
        move_number=1,
        direction=Direction.LEFT,
    )

    assert snapshot.grid[0][0] is not None
    assert snapshot.grid[0][0].value == 4
    assert snapshot.grid[0][0].heat == 1
    assert snapshot.score == 100
    assert snapshot.twist_state["avg_heat"] == 1.0
    assert snapshot.move_number == 1
    assert snapshot.direction == Direction.LEFT
    # Ensure deep copy not reference
    assert snapshot.grid is not grid
    assert snapshot.grid[0][0] is not tile


# ---------------------------------------------------------------------------
# AC-2: push deep copy isolation
# ---------------------------------------------------------------------------


def test_push_deep_copy_isolation() -> None:
    """AC-2: push deep copy isolation mutating original doesn't affect stored."""
    original_tile = Tile(value=4, heat=1)
    grid = create_empty_grid()
    grid[0][0] = original_tile
    original_twist = {"a": 1}

    snapshot = make_snapshot(grid, score=10, twist_state=original_twist, move_number=1, direction=Direction.LEFT)
    stack = HistoryStack()
    stack.push(snapshot)

    # Mutate originals after push
    grid[0][0] = Tile(value=8, heat=3)
    grid[0][1] = Tile(value=2, heat=0)
    # Mutate twist dict
    original_twist["a"] = 999

    stored = stack.peek()
    assert stored is not None
    assert stored.grid[0][0] is not None
    assert stored.grid[0][0].value == 4, f"Expected 4 not {stored.grid[0][0].value}"
    assert stored.grid[0][0].heat == 1, f"Expected heat 1 not {stored.grid[0][0].heat}"
    assert stored.grid[0][1] is None, "Expected None not Tile 2"
    assert stored.twist_state["a"] == 1, f"Expected twist a=1 not {stored.twist_state['a']}"
    assert len(stack) == 1


# ---------------------------------------------------------------------------
# AC-3: undo exact restore
# ---------------------------------------------------------------------------


def test_undo_exact_restore() -> None:
    """AC-3: undo returns exact prior grid values heat score twist state."""
    grid1 = create_empty_grid()
    grid1[0][0] = Tile(value=2, heat=0)
    grid1[1][1] = Tile(value=4, heat=1)
    snapshot1 = make_snapshot(grid1, score=10, twist_state={"avg": 0.5}, move_number=1, direction=Direction.UP)

    stack = HistoryStack()
    stack.push(snapshot1)

    grid2 = create_empty_grid()
    grid2[2][2] = Tile(value=8, heat=2)
    snapshot2 = make_snapshot(grid2, score=20, twist_state={"avg": 1.5}, move_number=2, direction=Direction.DOWN)
    stack.push(snapshot2)

    restored2 = stack.undo()
    assert restored2 is not None
    assert restored2.grid[2][2] is not None
    assert restored2.grid[2][2].value == 8
    assert restored2.grid[2][2].heat == 2
    assert restored2.score == 20
    assert restored2.twist_state["avg"] == 1.5
    assert restored2.move_number == 2
    assert restored2.direction == Direction.DOWN

    restored1 = stack.undo()
    assert restored1 is not None
    assert restored1.grid[0][0] is not None
    assert restored1.grid[0][0].value == 2
    assert restored1.grid[0][0].heat == 0
    assert restored1.grid[1][1] is not None
    assert restored1.grid[1][1].value == 4
    assert restored1.grid[1][1].heat == 1
    assert restored1.score == 10
    assert restored1.twist_state["avg"] == 0.5
    assert restored1.move_number == 1
    assert restored1.direction == Direction.UP


# ---------------------------------------------------------------------------
# AC-4: empty undo noop E004
# ---------------------------------------------------------------------------


def test_undo_empty_noop() -> None:
    """AC-4: undo empty returns None no crash per E004."""
    stack = HistoryStack()
    result = stack.undo()

    assert result is None
    assert len(stack) == 0
    assert stack.can_undo() is False
    # Second undo also no-op
    result2 = stack.undo()
    assert result2 is None


# ---------------------------------------------------------------------------
# AC-5: new move after undo clears redo
# ---------------------------------------------------------------------------


def test_new_move_after_undo_clears_redo() -> None:
    """AC-5: push A B C undo to B push D => A B D not A B C D."""
    def make_distinct_snapshot(score_val: int, tile_val: int, move_num: int) -> HistorySnapshot:
        g = create_empty_grid()
        g[0][0] = Tile(value=tile_val, heat=0)
        return make_snapshot(g, score=score_val, twist_state={"s": score_val}, move_number=move_num, direction=Direction.LEFT)

    snap_a = make_distinct_snapshot(1, 2, 1)
    snap_b = make_distinct_snapshot(2, 4, 2)
    snap_c = make_distinct_snapshot(3, 8, 3)
    snap_d = make_distinct_snapshot(4, 16, 4)

    stack = HistoryStack()
    stack.push(snap_a)
    stack.push(snap_b)
    stack.push(snap_c)
    assert len(stack) == 3

    returned_c = stack.undo()
    assert returned_c is not None
    assert returned_c.score == 3
    assert len(stack) == 2

    stack.push(snap_d)
    assert len(stack) == 3

    peeked = stack.peek()
    assert peeked is not None
    assert peeked.score == 4
    assert peeked.grid[0][0].value == 16

    # Order should be D, B, A then None
    undo_d = stack.undo()
    assert undo_d is not None and undo_d.score == 4
    undo_b = stack.undo()
    assert undo_b is not None and undo_b.score == 2
    undo_a = stack.undo()
    assert undo_a is not None and undo_a.score == 1
    undo_none = stack.undo()
    assert undo_none is None
    assert len(stack) == 0


# ---------------------------------------------------------------------------
# AC-6: multiple undos
# ---------------------------------------------------------------------------


def test_multiple_undos() -> None:
    """AC-6: multiple undos push 3 undo twice returns second etc."""
    stack = HistoryStack()
    for i, score_val in enumerate([10, 20, 30], start=1):
        g = create_empty_grid()
        g[0][0] = Tile(value=2 * (2 ** (i - 1)), heat=0)  # 2,4,8
        snap = make_snapshot(g, score=score_val, twist_state={"n": i}, move_number=i, direction=Direction.UP)
        stack.push(snap)

    assert len(stack) == 3

    r3 = stack.undo()
    assert r3 is not None and r3.score == 30
    assert len(stack) == 2

    r2 = stack.undo()
    assert r2 is not None and r2.score == 20
    assert len(stack) == 1

    r1 = stack.undo()
    assert r1 is not None and r1.score == 10
    assert len(stack) == 0

    r_none = stack.undo()
    assert r_none is None
    assert len(stack) == 0
    assert stack.can_undo() is False


# ---------------------------------------------------------------------------
# AC-7: can_undo
# ---------------------------------------------------------------------------


def test_can_undo() -> None:
    """AC-7: can_undo true non-empty false empty and after clear."""
    stack = HistoryStack()
    assert stack.can_undo() is False
    assert len(stack) == 0

    g = create_empty_grid()
    g[0][0] = Tile(value=2, heat=0)
    snap = make_snapshot(g, score=5, twist_state={}, move_number=1, direction=Direction.RIGHT)
    stack.push(snap)

    assert stack.can_undo() is True
    assert len(stack) == 1

    stack.clear()
    assert stack.can_undo() is False
    assert len(stack) == 0

    # Push again
    stack.push(snap)
    assert stack.can_undo() is True

    stack.undo()
    assert stack.can_undo() is False, "can_undo should be False after undo to empty"


# ---------------------------------------------------------------------------
# AC-8: no pygame import
# ---------------------------------------------------------------------------


def test_no_pygame_import() -> None:
    """AC-8: history module import does not leak pygame per ADR-015."""
    before_modules = set(sys.modules.keys())

    # Force reimport check via importlib if already imported
    import importlib

    # If already imported, reload to capture delta; else import
    if "src.core.history" in sys.modules:
        importlib.reload(sys.modules["src.core.history"])
    else:
        importlib.import_module("src.core.history")

    after_modules = set(sys.modules.keys())

    assert "pygame" not in after_modules, "pygame leaked into sys.modules"
    assert "pygame-ce" not in after_modules

    delta = after_modules - before_modules
    pygame_leaks = [m for m in delta if m.startswith("pygame")]
    assert not pygame_leaks, f"pygame modules leaked: {pygame_leaks}"


# ---------------------------------------------------------------------------
# Extra: deep copy grid mutation isolation
# ---------------------------------------------------------------------------


def test_deep_copy_grid_mutation() -> None:
    """Extra isolation: mutating peeked snapshot does not affect internal stack."""
    grid = create_empty_grid()
    grid[0][0] = Tile(value=4, heat=1)
    snapshot = make_snapshot(grid, score=10, twist_state={"x": 1}, move_number=1, direction=Direction.LEFT)

    stack = HistoryStack()
    stack.push(snapshot)

    peeked = stack.peek()
    assert peeked is not None
    # Mutate peeked grid — replace with different Tile
    peeked.grid[0][0] = Tile(value=16, heat=3)
    peeked.twist_state["x"] = 999

    second_peek = stack.peek()
    assert second_peek is not None
    assert second_peek.grid[0][0] is not None
    assert second_peek.grid[0][0].value == 4, f"Expected 4 not {second_peek.grid[0][0].value}"
    assert second_peek.grid[0][0].heat == 1, f"Expected heat 1 not {second_peek.grid[0][0].heat}"
    assert second_peek.twist_state["x"] == 1, "twist_state isolation broken"
