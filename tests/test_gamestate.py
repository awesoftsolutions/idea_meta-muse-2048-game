"""
tests/test_gamestate.py — GameState aggregator Q-005 final validation.

Covers AC-10 to AC-12, AC-21 to AC-26 per pseudocode phase_3_sprint_2_wave1_tasks_1_2_code.md:
- GameState creation defaults 0
- vent_streak increments consecutive 1,2,3,4,5 and last_vent_occurred True
- vent_streak resets on False
- unstable_survival increments/resets
- undo_count total invocations, move_count increments
- twist vent_heat returns vent_occurred bool, check_unstable returns unstable_present bool
- history snapshot includes GameState exact restore
- equality and repr

Headless, stdlib only, no pygame.
"""

from __future__ import annotations

import sys
from typing import List, Optional

from src.core.board import BOARD_SIZE, Tile, create_empty_grid


def test_gamestate_creation_defaults_0() -> None:
    """AC-21: GameState creation defaults 0 vent_streak=0 unstable_survival=0 undo_count=0 move_count=0 last_vent_occurred=False last_unstable_present=False."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.vent_streak == 0
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False


def test_vent_streak_increments_consecutive_1_2_3_4_5() -> None:
    """AC-10: vent_streak increments on vent_occurred True consecutive 1,2,3,4,5 and last_vent_occurred True."""
    from src.core.gamestate import GameState

    gs = GameState()
    for i in range(1, 6):
        gs.update_after_turn(vent_occurred=True, unstable_present=False)
        assert gs.vent_streak == i, f"Expected {i}, got {gs.vent_streak}"
        assert gs.last_vent_occurred is True
    assert gs.move_count == 5


def test_vent_streak_resets_on_false() -> None:
    """AC-11: vent_streak resets to 0 on vent_occurred False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.vent_streak = 3
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.vent_streak == 0
    assert gs.last_vent_occurred is False


def test_unstable_survival_increments_on_true() -> None:
    """AC-12: unstable_survival increments on unstable_present True."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 1
    assert gs.last_unstable_present is True
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 2
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 3


def test_unstable_survival_resets_on_false() -> None:
    """Edge: unstable_survival resets on unstable_present False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.unstable_survival = 2
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.unstable_survival == 0
    assert gs.last_unstable_present is False


def test_undo_count_increments_total_invocations() -> None:
    """AC-22: undo_count increments on increment_undo total invocations ever not reset unless explicit."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.increment_undo()
    assert gs.undo_count == 1
    gs.increment_undo()
    gs.increment_undo()
    assert gs.undo_count == 3
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.undo_count == 3, "undo_count should not reset on update_after_turn"
    gs.reset_on_new_game()
    assert gs.undo_count == 0


def test_move_count_increments_on_update_after_turn() -> None:
    """AC-23: move_count increments on update_after_turn."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.move_count == 0
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.move_count == 1
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    assert gs.move_count == 2


def test_twist_vent_heat_returns_vent_occurred_bool() -> None:
    """AC-24: twist vent_heat returns vent_occurred True when edge tile vented False otherwise."""
    from src.core.twist import vent_heat

    # Edge tile heat 1 should vent to 0 => vent_occurred True
    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=1)
    new_grid, vent_occurred = vent_heat(grid)
    assert vent_occurred is True
    assert new_grid[0][0] is not None and new_grid[0][0].heat == 0

    # Interior tile heat 1 edge None => vent_occurred False
    grid2 = create_empty_grid()
    grid2[2][2] = Tile(value=2, heat=1)
    new_grid2, vent_occurred2 = vent_heat(grid2)
    assert vent_occurred2 is False

    # Edge tile heat 0 no vent => False
    grid3 = create_empty_grid()
    grid3[0][0] = Tile(value=2, heat=0)
    _, vent_occurred3 = vent_heat(grid3)
    assert vent_occurred3 is False


def test_twist_check_unstable_returns_unstable_present_bool() -> None:
    """AC-25: check_unstable returns unstable_present True when any heat>=3."""
    from src.core.twist import check_unstable

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=3)
    positions, unstable_present = check_unstable(grid)
    assert unstable_present is True
    assert (0, 0) in positions

    grid2 = create_empty_grid()
    grid2[0][0] = Tile(value=2, heat=0)
    _, unstable_present2 = check_unstable(grid2)
    assert unstable_present2 is False


def test_history_snapshot_includes_gamestate_exact_restore() -> None:
    """AC-26: history snapshot includes GameState exact restore after undo."""
    from src.core.board import Direction
    from src.core.gamestate import GameState
    from src.core.history import HistorySnapshot, HistoryStack

    gs = GameState()
    gs.vent_streak = 2
    gs.unstable_survival = 1
    gs.undo_count = 3
    gs.move_count = 5

    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)

    snapshot = HistorySnapshot(
        grid=grid, score=100, twist_state={}, move_number=1, direction=Direction.LEFT, game_state=gs
    )
    stack = HistoryStack()
    stack.push(snapshot)

    # Mutate original gs after push should not affect snapshot
    gs.vent_streak = 99

    popped = stack.undo()
    assert popped is not None
    assert popped.game_state is not None
    assert popped.game_state.vent_streak == 2
    assert popped.game_state.unstable_survival == 1
    assert popped.game_state.undo_count == 3
    assert popped.game_state.move_count == 5

    # Deep copy isolation: mutating popped should not affect original push
    popped.game_state.vent_streak = 100
    # Stack is empty after undo, but original snapshot in stack was popped, so check isolation via new push
    # The key isolation is that original gs mutation didn't affect snapshot


def test_gamestate_equality_and_repr() -> None:
    """Edge: GameState __eq__ and __repr__."""
    from src.core.gamestate import GameState

    gs1 = GameState()
    gs2 = GameState()
    assert gs1 == gs2

    gs1.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs1 != gs2

    gs2.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs1 == gs2

    repr_str = repr(gs1)
    assert "vent_streak" in repr_str
    assert "unstable_survival" in repr_str
    assert "undo_count" in repr_str


def test_gamestate_no_pygame_import() -> None:
    """Isolation: importing gamestate must not leak pygame via delta check."""
    before_has_pygame = "pygame" in sys.modules
    before_keys = set(sys.modules.keys())
    import src.core.gamestate  # noqa: F401

    after_keys = set(sys.modules.keys())
    new_keys = after_keys - before_keys
    if not before_has_pygame:
        pygame_new = [k for k in new_keys if "pygame" in k.lower()]
        assert not pygame_new, f"pygame leaked in delta: {pygame_new}"


def test_gamestate_definitions_locked_per_adr_016() -> None:
    """ADR-016 definitions locked: vent_streak any edge vented, unstable_survival survived with unstable present, undo_count total invocations."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 1

    gs2 = GameState()
    gs2.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs2.unstable_survival == 1

    gs3 = GameState()
    gs3.increment_undo()
    gs3.increment_undo()
    assert gs3.undo_count == 2
    gs3.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs3.undo_count == 2


def test_gamestate_reset_on_new_game() -> None:
    """reset_on_new_game resets all to 0/False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.increment_undo()
    gs.reset_on_new_game()
    assert gs.vent_streak == 0
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False
