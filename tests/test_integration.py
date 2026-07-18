"""
tests/test_integration.py — Integration verification for turn pipeline.

Purpose:
    Verifies locked ordering ADR-009, new tile heat=0 immunity, GameContext
    correctness, 10 moves seeded simulation, game-over, no pygame leak,
    seeded RNG determinism. Headless, deterministic, injectable Random only.

System:
    tests/ per Phase 2 architecture. Part of integration verification
    subsystem. ADR-009 Turn Pipeline Locked, ADR-011 Board vs Twist
    Ownership, ADR-015 Headless Testability.

Dependencies:
    stdlib only: random, sys, tempfile, pathlib, typing.
    Plus src.core.achievements Achievements GameContext, board Tile Board
    Direction BOARD_SIZE create_empty_grid, history HistorySnapshot
    HistoryStack, score ScoreState, rules is_game_over is_legal_move,
    twist get_turn_pipeline_order apply_heat_generation spread_heat
    vent_heat check_unstable. No pygame import.

Used-By:
    pytest runner for integration verification of board+rules+score+
    history+twist+achievements turn pipeline.

Public Interface:
    Helpers: _make_empty_grid, _grid_with_tiles, _deep_copy_grid,
        _grids_equal_value_and_heat, _calc_avg_heat
    Tests: test_turn_pipeline_order_locked, test_new_tile_heat_0_immune_same_turn,
        test_game_context_correctness, test_10_moves_seeded_simulation,
        test_game_over_only_when_no_empty_and_no_merge,
        test_no_pygame_import, test_seeded_rng_determinism
"""

from __future__ import annotations

import random
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from src.core.achievements import Achievements, GameContext
from src.core.board import BOARD_SIZE, Board, Direction, Tile, create_empty_grid
from src.core.history import HistorySnapshot, HistoryStack
from src.core.score import ScoreState
from src.core import rules as rules_module
from src.core import twist as twist_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_empty_grid():
    """Create empty 5x5 grid via create_empty_grid.

    Returns:
        5x5 grid of None.
    """
    return create_empty_grid()


def _grid_with_tiles(tiles_spec: List[tuple]) -> List[List[Optional[Tile]]]:
    """Create grid with tiles from spec list.

    Args:
        tiles_spec: List of (r,c,value,heat) tuples.

    Returns:
        5x5 grid with Tile objects at specified positions.
    """
    grid = _make_empty_grid()
    for r, c, v, h in tiles_spec:
        grid[r][c] = Tile(value=v, heat=h)
    return grid


def _deep_copy_grid(grid):
    """Deep copy grid via Tile(value, heat) manual copy.

    Args:
        grid: Source 5x5 grid.

    Returns:
        Deep copied grid with isolated Tile objects.
    """
    new_grid = []
    for r in range(BOARD_SIZE):
        row = []
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is None:
                row.append(None)
            else:
                row.append(Tile(value=cell.value, heat=cell.heat))
        new_grid.append(row)
    return new_grid


def _grids_equal_value_and_heat(g1, g2) -> bool:
    """Compare two grids by value and heat equality.

    Args:
        g1: First grid.
        g2: Second grid.

    Returns:
        True if grids equal by value and heat, False otherwise.
    """
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            a = g1[r][c]
            b = g2[r][c]
            if a is None and b is None:
                continue
            if a is None or b is None:
                return False
            if a.value != b.value or a.heat != b.heat:
                return False
    return True


def _calc_avg_heat(grid) -> float:
    """Calculate average heat over existing tiles.

    Args:
        grid: 5x5 grid to scan.

    Returns:
        Average heat float, 0.0 if no tiles.
    """
    total = 0
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = grid[r][c]
            if cell is not None:
                total += cell.heat
                count += 1
    return total / count if count else 0.0


# ---------------------------------------------------------------------------
# 1. Pipeline ordering locked
# ---------------------------------------------------------------------------


def test_turn_pipeline_order_locked():
    """AC-1: Verify locked 8-step pipeline ordering via get_turn_pipeline_order."""
    expected = [
        "slide",
        "calc_merge_heat",
        "apply_gen",
        "spread",
        "vent",
        "spawn_heat_0",
        "check_unstable",
        "evaluate_achievements",
    ]
    pipeline_order = twist_module.get_turn_pipeline_order()

    assert pipeline_order == expected, f"Expected {expected}, got {pipeline_order}"
    assert len(pipeline_order) == 8, f"Expected length 8, got {len(pipeline_order)}"

    # Verify ordering indices strictly increasing
    indices = {name: pipeline_order.index(name) for name in expected}
    assert indices["slide"] < indices["calc_merge_heat"]
    assert indices["calc_merge_heat"] < indices["apply_gen"]
    assert indices["apply_gen"] < indices["spread"]
    assert indices["spread"] < indices["vent"]
    assert indices["vent"] < indices["spawn_heat_0"]
    assert indices["spawn_heat_0"] < indices["check_unstable"]
    assert indices["check_unstable"] < indices["evaluate_achievements"]


# ---------------------------------------------------------------------------
# 2. New tile heat=0 immune same turn
# ---------------------------------------------------------------------------


def test_new_tile_heat_0_immune_same_turn():
    """AC-1: New tile spawned after spread/vent has heat=0 immune same turn."""
    rng = random.Random(42)

    # Grid: two adjacent 2 tiles at (0,0) and (0,1) for merge, high heat tile at (2,2) heat=2
    grid = _grid_with_tiles(
        [
            (0, 0, 2, 0),
            (0, 1, 2, 0),
            (2, 2, 4, 2),
        ]
    )
    board = Board(grid=grid, rng=rng)

    # Slide LEFT — should merge (0,0)+(0,1) -> 4
    slide_result = board.slide(Direction.LEFT)
    assert slide_result.moved is True
    assert len(slide_result.merges) >= 1

    # Manual pipeline without spawn: apply heat gen -> spread -> vent
    grid_after_gen = twist_module.apply_heat_generation(
        slide_result.grid, slide_result.merges
    )
    grid_after_spread = twist_module.spread_heat(grid_after_gen)
    grid_after_vent = twist_module.vent_heat(grid_after_spread)

    # Capture state before spawn
    heat_before_spawn = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = grid_after_vent[r][c]
            if cell is not None:
                heat_before_spawn[(r, c)] = cell.heat

    # Spawn via Board._spawn_tile (pure, returns new grid)
    # Use board's rng which has been advanced by slide's internal spawn
    # For deterministic immunity check, use a fresh rng for spawn
    spawn_rng = random.Random(42)
    grid_after_spawn = board._spawn_tile(grid_after_vent, spawn_rng)

    # Find newly spawned position by diff
    new_pos = None
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            before = grid_after_vent[r][c]
            after = grid_after_spawn[r][c]
            if before is None and after is not None:
                new_pos = (r, c)
                break
        if new_pos:
            break

    # If no empty cells, spawn returns copy unchanged — skip immunity assert
    # In our setup there are many empties, so new_pos must exist
    assert new_pos is not None, "Expected new tile spawned, but no empty diff found"

    new_tile = grid_after_spawn[new_pos[0]][new_pos[1]]
    assert new_tile is not None
    assert new_tile.heat == 0, f"New tile heat expected 0, got {new_tile.heat}"

    # Verify existing tiles heat unchanged after spawn (no extra spread/vent)
    for (r, c), heat in heat_before_spawn.items():
        # Skip if this position is the new spawn (should not be in before)
        after_cell = grid_after_spawn[r][c]
        assert after_cell is not None
        assert after_cell.heat == heat, (
            f"Tile at {(r,c)} heat changed after spawn: {heat} -> {after_cell.heat}"
        )

    # Verify new tile not present in grid_after_vent
    assert grid_after_vent[new_pos[0]][new_pos[1]] is None


# ---------------------------------------------------------------------------
# 3. GameContext correctness
# ---------------------------------------------------------------------------


def test_game_context_correctness():
    """AC-2: GameContext contains correct 10 fields."""
    rng = random.Random(123)
    grid = _grid_with_tiles([(0, 0, 2, 0), (0, 1, 2, 0)])
    board = Board(grid=grid, rng=rng)

    with tempfile.TemporaryDirectory() as tmpdir:
        score_path = Path(tmpdir) / "high_score.json"
        score_state = ScoreState(high_score_path=score_path)
        history_stack = HistoryStack()
        achievements_mgr = Achievements()

        move_count = 0
        total_merges = 0
        vent_streak = 0
        unstable_survival = 0
        undo_count = 0

        slide_result = board.slide(Direction.LEFT)
        total_merges += len(slide_result.merges)
        move_count += 1

        grid_gen = twist_module.apply_heat_generation(
            slide_result.grid, slide_result.merges
        )
        grid_spread = twist_module.spread_heat(grid_gen)
        grid_vent = twist_module.vent_heat(grid_spread)
        unstable_positions = twist_module.check_unstable(grid_vent)

        twist_state = {
            "average_heat": _calc_avg_heat(grid_vent),
            "unstable_count": len(unstable_positions),
            "vent_streak": vent_streak,
            "unstable_survival": unstable_survival,
        }

        snapshot = HistorySnapshot(
            grid=grid_vent,
            score=score_state.current_score,
            twist_state=twist_state,
            move_number=move_count,
            direction=Direction.LEFT,
        )
        history_stack.push(snapshot)
        score_state.add(slide_result.score_delta)

        context = GameContext(
            board=grid_vent,
            score=score_state,
            history=history_stack,
            twist=twist_state,
            last_slide_result=slide_result,
            move_count=move_count,
            total_merges=total_merges,
            vent_streak=vent_streak,
            unstable_survival=unstable_survival,
            undo_count=undo_count,
        )

        # Assert all 10 fields
        assert context.board is grid_vent
        assert context.score is score_state
        assert context.history is history_stack
        assert context.twist is twist_state
        assert context.last_slide_result is slide_result
        assert context.move_count == move_count
        assert context.total_merges == total_merges
        assert context.vent_streak == vent_streak
        assert context.unstable_survival == unstable_survival
        assert context.undo_count == undo_count

        newly_unlocked = achievements_mgr.evaluate(context)
        assert isinstance(newly_unlocked, list)


# ---------------------------------------------------------------------------
# 4. 10 moves seeded simulation
# ---------------------------------------------------------------------------


def test_10_moves_seeded_simulation():
    """AC-3: 10 moves seeded simulation with score, history, achievements, replay."""
    rng = random.Random(999)
    initial_grid = _grid_with_tiles([(0, 0, 2, 0), (0, 1, 2, 0)])
    board = Board(grid=_deep_copy_grid(initial_grid), rng=rng)

    with tempfile.TemporaryDirectory() as tmpdir:
        score_path = Path(tmpdir) / "high_score.json"
        score_state = ScoreState(high_score_path=score_path)
        history_stack = HistoryStack()
        achievements_mgr = Achievements()

        move_count = 0
        total_merges = 0
        vent_streak = 0
        unstable_survival = 0
        undo_count = 0

        directions = [
            Direction.LEFT,
            Direction.RIGHT,
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.UP,
            Direction.RIGHT,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ]

        score_deltas: List[int] = []
        grids_history: List[List[List[Optional[Tile]]]] = []

        for direction in directions:
            # Check legality
            is_legal = rules_module.is_legal_move(direction, board.grid)
            if not is_legal:
                continue

            # Use manual pipeline to avoid double spawn confusion
            # First simulate slide without spawn via board's internal logic
            # We use board.slide which already spawns, but we will reconstruct
            # manual pipeline for verification: extract slide result then re-apply twist
            # For this test, we use board.slide for slide+spawn, then apply twist
            # phases on top? Instead, we follow pseudocode manual pipeline:
            # slide -> gen -> spread -> vent -> spawn

            # To get slide without spawn, we use rules simulation + board._process_line
            # Simpler: use board.slide to get merges and moved, but capture grid before spawn
            # by re-running _extract_lines/_process_line/_reconstruct_grid
            lines = board._extract_lines(board.grid, direction)
            base_positions = board._extract_base_positions(direction)
            processed_lines = []
            all_merges = []
            total_score = 0
            for idx, line in enumerate(lines):
                new_line, score, merges = board._process_line(
                    line, idx, direction, base_positions[idx]
                )
                processed_lines.append(new_line)
                total_score += score
                all_merges.extend(merges)
                for m in merges:
                    try:
                        object.__setattr__(m, "_tmp_line_idx", idx)
                    except Exception:
                        pass

            reconstructed = board._reconstruct_grid(
                processed_lines, direction, board.grid, all_merges
            )
            grid_no_spawn = reconstructed[0]
            moved = reconstructed[2]
            final_merges = reconstructed[3]

            if not moved:
                continue

            assert total_score >= 0

            grid_gen = twist_module.apply_heat_generation(grid_no_spawn, final_merges)
            grid_spread = twist_module.spread_heat(grid_gen)
            grid_vent = twist_module.vent_heat(grid_spread)
            unstable_positions = twist_module.check_unstable(grid_vent)

            # Vent streak logic: if any edge tile heat reduced vs spread
            vent_occurred = False
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if grid_spread[r][c] is None or grid_vent[r][c] is None:
                        continue
                    if (r == 0 or r == BOARD_SIZE - 1 or c == 0 or c == BOARD_SIZE - 1):
                        if grid_vent[r][c].heat < grid_spread[r][c].heat:
                            vent_occurred = True
                            break
                if vent_occurred:
                    break

            if vent_occurred:
                vent_streak += 1
            else:
                vent_streak = 0

            if len(unstable_positions) > 0:
                unstable_survival += 1

            total_merges += len(final_merges)
            move_count += 1

            twist_state = {
                "average_heat": _calc_avg_heat(grid_vent),
                "unstable_count": len(unstable_positions),
                "vent_streak": vent_streak,
                "unstable_survival": unstable_survival,
            }

            snapshot = HistorySnapshot(
                grid=grid_vent,
                score=score_state.current_score + total_score,
                twist_state=twist_state,
                move_number=move_count,
                direction=direction,
            )
            history_stack.push(snapshot)
            score_state.add(total_score)

            # Build SlideResult for context
            from src.core.board import SlideResult

            slide_result = SlideResult(
                grid=grid_vent,
                score_delta=total_score,
                moved=moved,
                merges=final_merges,
            )

            context = GameContext(
                board=grid_vent,
                score=score_state,
                history=history_stack,
                twist=twist_state,
                last_slide_result=slide_result,
                move_count=move_count,
                total_merges=total_merges,
                vent_streak=vent_streak,
                unstable_survival=unstable_survival,
                undo_count=undo_count,
            )

            newly_unlocked = achievements_mgr.evaluate(context)
            assert isinstance(newly_unlocked, list)

            # Spawn after vent
            grid_spawned = board._spawn_tile(grid_vent, board.rng)
            board.grid = _deep_copy_grid(grid_spawned)

            score_deltas.append(total_score)
            grids_history.append(_deep_copy_grid(board.grid))

            # Verify score equals sum of deltas
            assert score_state.current_score == sum(score_deltas)

        # After loop assertions
        assert 1 <= move_count <= 10, f"move_count {move_count} not in [1,10]"
        assert len(history_stack) == move_count

        # Test exact restore via undo
        if len(history_stack) > 0:
            last_snapshot = history_stack.undo()
            assert last_snapshot is not None
            # Push back to restore stack length
            history_stack.push(last_snapshot)
            assert len(history_stack) == move_count

        # Deterministic replay with same seed
        rng2 = random.Random(999)
        board2 = Board(grid=_deep_copy_grid(initial_grid), rng=rng2)
        score_deltas2: List[int] = []

        for direction in directions:
            is_legal = rules_module.is_legal_move(direction, board2.grid)
            if not is_legal:
                continue

            lines = board2._extract_lines(board2.grid, direction)
            base_positions = board2._extract_base_positions(direction)
            processed_lines = []
            all_merges = []
            total_score = 0
            for idx, line in enumerate(lines):
                new_line, score, merges = board2._process_line(
                    line, idx, direction, base_positions[idx]
                )
                processed_lines.append(new_line)
                total_score += score
                all_merges.extend(merges)
                for m in merges:
                    try:
                        object.__setattr__(m, "_tmp_line_idx", idx)
                    except Exception:
                        pass

            reconstructed = board2._reconstruct_grid(
                processed_lines, direction, board2.grid, all_merges
            )
            grid_no_spawn = reconstructed[0]
            moved = reconstructed[2]

            if not moved:
                continue

            grid_gen = twist_module.apply_heat_generation(
                grid_no_spawn, reconstructed[3]
            )
            grid_spread = twist_module.spread_heat(grid_gen)
            grid_vent = twist_module.vent_heat(grid_spread)
            grid_spawned = board2._spawn_tile(grid_vent, board2.rng)
            board2.grid = _deep_copy_grid(grid_spawned)
            score_deltas2.append(total_score)

        # Final grids equal and scores equal
        assert _grids_equal_value_and_heat(board.grid, board2.grid), (
            "Deterministic replay final grids differ"
        )
        assert sum(score_deltas) == sum(score_deltas2), (
            f"Score mismatch replay: {sum(score_deltas)} vs {sum(score_deltas2)}"
        )


# ---------------------------------------------------------------------------
# 5. Game-over only when no empty and no merge
# ---------------------------------------------------------------------------


def test_game_over_only_when_no_empty_and_no_merge():
    """AC-4: is_game_over true only when no empty and no merge any direction."""
    # Full board no merge: alternating 2 and 4 checkerboard no adjacent equals
    full_no_merge_grid = _make_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            # Checkerboard 2/4 ensures no adjacent equals
            val = 2 if (r + c) % 2 == 0 else 4
            full_no_merge_grid[r][c] = Tile(value=val, heat=0)

    result = rules_module.is_game_over(full_no_merge_grid)
    assert result is True, "Full board no merge should be game over"

    # Full board with one adjacent equal pair
    full_with_merge_grid = _deep_copy_grid(full_no_merge_grid)
    # Force (0,0) and (0,1) both 2
    full_with_merge_grid[0][0] = Tile(value=2, heat=0)
    full_with_merge_grid[0][1] = Tile(value=2, heat=0)
    result2 = rules_module.is_game_over(full_with_merge_grid)
    assert result2 is False, "Full board with merge should NOT be game over"

    # Not full grid with at least one empty
    not_full_grid = _make_empty_grid()
    not_full_grid[0][0] = Tile(value=2, heat=0)
    not_full_grid[0][1] = Tile(value=4, heat=0)
    result3 = rules_module.is_game_over(not_full_grid)
    assert result3 is False, "Not full board should NOT be game over"

    # Simulated grid from 10 moves final state — verify manual check if game over true
    simulated_grid = _grid_with_tiles([(0, 0, 2, 0), (1, 1, 4, 1)])
    result4 = rules_module.is_game_over(simulated_grid)
    if result4 is True:
        # Manual verification: no empty and no merge
        has_empty = any(
            simulated_grid[r][c] is None
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
        )
        assert not has_empty, "Game over true but empty exists"

        has_merge = False
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                cell = simulated_grid[r][c]
                if cell is None:
                    continue
                # Right neighbor
                if c + 1 < BOARD_SIZE and simulated_grid[r][c + 1] is not None:
                    if simulated_grid[r][c + 1].value == cell.value:
                        has_merge = True
                # Down neighbor
                if r + 1 < BOARD_SIZE and simulated_grid[r + 1][c] is not None:
                    if simulated_grid[r + 1][c].value == cell.value:
                        has_merge = True
        assert not has_merge, "Game over true but merge possible"


# ---------------------------------------------------------------------------
# 6. No pygame import
# ---------------------------------------------------------------------------


def test_no_pygame_import():
    """AC-5: No pygame in sys.modules after importing all core modules."""
    # Import all core modules
    import src.core.achievements  # noqa: F401
    import src.core.board  # noqa: F401
    import src.core.history  # noqa: F401
    import src.core.rules  # noqa: F401
    import src.core.score  # noqa: F401
    import src.core.twist  # noqa: F401

    has_pygame = "pygame" in sys.modules
    assert has_pygame is False, f"pygame found in sys.modules: {sys.modules.get('pygame')}"

    has_pygame_ce = "pygame-ce" in sys.modules
    assert has_pygame_ce is False, "pygame-ce found in sys.modules"

    # Also check that importing this test module itself didn't leak pygame
    assert "pygame" not in sys.modules


# ---------------------------------------------------------------------------
# 7. Seeded RNG determinism
# ---------------------------------------------------------------------------


def test_seeded_rng_determinism():
    """AC-6: Same seed yields identical grids and score deltas."""
    rng1 = random.Random(42)
    grid1 = _grid_with_tiles([(0, 0, 2, 0)])
    board1 = Board(grid=_deep_copy_grid(grid1), rng=rng1)

    rng2 = random.Random(42)
    grid2 = _grid_with_tiles([(0, 0, 2, 0)])
    board2 = Board(grid=_deep_copy_grid(grid2), rng=rng2)

    directions = [
        Direction.LEFT,
        Direction.UP,
        Direction.RIGHT,
        Direction.DOWN,
        Direction.LEFT,
    ]

    for direction in directions:
        result1 = board1.slide(direction)
        result2 = board2.slide(direction)

        assert _grids_equal_value_and_heat(result1.grid, result2.grid), (
            f"Grids differ for direction {direction}: "
            f"{result1.grid} vs {result2.grid}"
        )
        assert result1.score_delta == result2.score_delta, (
            f"score_delta differ for {direction}: "
            f"{result1.score_delta} vs {result2.score_delta}"
        )
        assert result1.moved == result2.moved, (
            f"moved differ for {direction}: {result1.moved} vs {result2.moved}"
        )
        assert len(result1.merges) == len(result2.merges), (
            f"merges len differ for {direction}: "
            f"{len(result1.merges)} vs {len(result2.merges)}"
        )
