"""
tests/test_gamestate.py — TDD red-phase tests for GameState aggregator Q-005.

Covers AC-1 to AC-6 per pseudocode phase_3_sprint_1_wave1_gamestate_mergeinfo_main.md:
- AC-1 creation defaults 0/False
- AC-2 vent_streak increments on True consecutive 1-5
- AC-3 vent_streak resets on False
- AC-4 unstable_survival increments on True
- AC-5 unstable_survival resets on False
- AC-6 undo_count increments total invocations ever
- Extra: move_count increments, reset_on_new_game, definitions locked per ADR-016

Headless, stdlib only, no pygame. TDD red phase: MUST FAIL initially because
src/core/gamestate.py does not exist yet. Expected: ModuleNotFoundError.

System: src/core per Phase 3 architecture ADR-016 GameState aggregator ownership.
"""

from __future__ import annotations

import sys


def test_gamestate_creation_defaults() -> None:
    """AC-1: When GameState is created, all counters 0 and flags False."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.vent_streak == 0, f"vent_streak expected 0 got {gs.vent_streak}"
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False


def test_vent_streak_increments() -> None:
    """AC-2: vent_streak increments by 1 on vent_occurred True, consecutive 1..5."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 1
    assert gs.last_vent_occurred is True

    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 2

    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 3

    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 4

    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 5, f"expected 5 after 5 consecutive True, got {gs.vent_streak}"
    assert gs.last_vent_occurred is True


def test_vent_streak_resets() -> None:
    """AC-3: vent_streak resets to 0 on vent_occurred False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.vent_streak = 3
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.vent_streak == 0, f"expected reset to 0, got {gs.vent_streak}"
    assert gs.last_vent_occurred is False

    # True -> False -> True sequence
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 1
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.vent_streak == 0
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 1


def test_unstable_survival_increments() -> None:
    """AC-4: unstable_survival increments on unstable_present True."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 1
    assert gs.last_unstable_present is True

    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 2

    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 3


def test_unstable_survival_resets() -> None:
    """AC-5: unstable_survival resets to 0 on unstable_present False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.unstable_survival = 2
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.unstable_survival == 0
    assert gs.last_unstable_present is False


def test_undo_count_increments() -> None:
    """AC-6: undo_count increments total invocations ever, not reset on update_after_turn."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.undo_count == 0
    gs.increment_undo()
    assert gs.undo_count == 1
    gs.increment_undo()
    assert gs.undo_count == 2

    # update_after_turn must NOT reset undo_count
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.undo_count == 2, "undo_count should not reset on update_after_turn"

    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    assert gs.undo_count == 2, "undo_count should survive update_after_turn"


def test_move_count_increments() -> None:
    """move_count increments on each update_after_turn."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.move_count == 0
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.move_count == 1
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    assert gs.move_count == 2


def test_reset_on_new_game() -> None:
    """reset_on_new_game resets all to 0/False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.increment_undo()
    gs.increment_undo()
    # Now reset
    gs.reset_on_new_game()
    assert gs.vent_streak == 0
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False


def test_gamestate_equality() -> None:
    """GameState equality based on all fields."""
    from src.core.gamestate import GameState

    gs1 = GameState()
    gs2 = GameState()
    assert gs1 == gs2

    gs1.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs1 != gs2

    gs2.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs1 == gs2


def test_no_pygame_import() -> None:
    """Isolation: importing gamestate must not leak pygame."""
    assert "pygame" not in sys.modules, "pygame should not be loaded before test"
    import src.core.gamestate  # noqa: F401

    assert "pygame" not in sys.modules, "pygame leaked via gamestate import"


# ---------------------------------------------------------------------------
# Wave2 comprehensive: consecutive 5, definitions locked per ADR-016
# ---------------------------------------------------------------------------


def test_vent_streak_increments_consecutive_5() -> None:
    """AC-10: vent_streak increments 1,2,3,4,5 consecutive and move_count 5."""
    from src.core.gamestate import GameState

    gs = GameState()
    for i in range(1, 6):
        gs.update_after_turn(vent_occurred=True, unstable_present=False)
        assert gs.vent_streak == i, f"Expected {i}, got {gs.vent_streak}"
        assert gs.last_vent_occurred is True
    assert gs.move_count == 5


def test_vent_streak_resets_on_false() -> None:
    """AC-10: vent_streak resets on False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.vent_streak = 3
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.vent_streak == 0
    assert gs.last_vent_occurred is False


def test_unstable_survival_increments_wave2() -> None:
    """AC-11: unstable_survival increments on True (Wave2 explicit)."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 1
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 2
    gs.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs.unstable_survival == 3
    assert gs.last_unstable_present is True


def test_unstable_survival_resets_wave2() -> None:
    """AC-11: unstable_survival resets on False (Wave2 explicit)."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.unstable_survival = 2
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.unstable_survival == 0
    assert gs.last_unstable_present is False


def test_undo_count_increments_total_invocations() -> None:
    """AC-12: undo_count increments total invocations ever."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.increment_undo()
    assert gs.undo_count == 1
    gs.increment_undo()
    assert gs.undo_count == 2
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.undo_count == 2, "undo_count should not reset on update_after_turn"


def test_move_count_increments_explicit() -> None:
    """move_count increments on each update_after_turn."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.move_count == 0
    gs.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs.move_count == 1
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    assert gs.move_count == 2


def test_reset_on_new_game_explicit() -> None:
    """reset_on_new_game resets all to 0/False."""
    from src.core.gamestate import GameState

    gs = GameState()
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.update_after_turn(vent_occurred=True, unstable_present=True)
    gs.increment_undo()
    gs.increment_undo()
    gs.reset_on_new_game()
    assert gs.vent_streak == 0
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False


def test_definitions_locked_per_adr_016() -> None:
    """ADR-016 definitions locked: vent_streak any edge vented, unstable_survival survived with unstable present, undo_count total invocations."""
    from src.core.gamestate import GameState

    gs = GameState()
    # vent_streak = consecutive moves where any edge tile vented (vent_occurred True)
    gs.update_after_turn(vent_occurred=True, unstable_present=False)
    assert gs.vent_streak == 1
    # unstable_survival = consecutive moves survived with unstable >=3 present
    gs2 = GameState()
    gs2.update_after_turn(vent_occurred=False, unstable_present=True)
    assert gs2.unstable_survival == 1
    # undo_count = total undo invocations ever
    gs3 = GameState()
    gs3.increment_undo()
    gs3.increment_undo()
    assert gs3.undo_count == 2
    gs3.update_after_turn(vent_occurred=False, unstable_present=False)
    assert gs3.undo_count == 2, "undo_count total invocations ever not reset unless explicit"


def test_gamestate_creation_defaults_explicit() -> None:
    """AC-9: GameState creation defaults 0/False."""
    from src.core.gamestate import GameState

    gs = GameState()
    assert gs.vent_streak == 0
    assert gs.unstable_survival == 0
    assert gs.undo_count == 0
    assert gs.move_count == 0
    assert gs.last_vent_occurred is False
    assert gs.last_unstable_present is False