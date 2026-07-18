"""
tests/test_twist.py — TDD red-phase tests for Thermal Entropy Core twist mechanics.

Covers all 13 ACs from pseudocode blueprint:
- Heat gen formula floor(log2(V)/2) clamped 0-3 table V=4->1,8->1,16->2,32->2,64->3
- Spread orthogonal lower deterministic
- Vent edge vs interior, never negative
- Unstable >=3 collection
- Spawn heat=0 immunity via ordering
- Cool-merge bonus
- Turn pipeline ordering locked
- Seeded determinism
- Average heat measurement Q-001 50/100/200 moves
- No pygame import isolation

Headless, stdlib + pytest only, no pygame.
TDD red phase: these tests MUST FAIL initially because src/core/twist.py does not exist yet.
Expected failure: ModuleNotFoundError for src.core.twist.

System: src/core per Phase 2 architecture ADR-010, ADR-011, ADR-009.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

from src.core.board import (
    BOARD_SIZE,
    HEAT_MAX,
    HEAT_MIN,
    MergeInfo,
    Tile,
    create_empty_grid,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

Grid = List[List[Optional[Tile]]]


def make_empty_grid() -> Grid:
    """Create 5x5 None grid."""
    return create_empty_grid()


def make_grid_with_tiles(mapping: Dict[Tuple[int, int], Tuple[int, int]]) -> Grid:
    """Create grid from {(r,c): (value, heat)} mapping."""
    grid = make_empty_grid()
    for (r, c), (value, heat) in mapping.items():
        grid[r][c] = Tile(value=value, heat=heat)
    return grid


def deep_copy_grid(grid: Grid) -> Grid:
    """Deep copy via Tile(value, heat)."""
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


def count_tiles(grid: Grid) -> int:
    """Count non-None tiles."""
    return sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if grid[r][c] is not None)


def average_heat(grid: Grid) -> float:
    """Average heat across tiles, 0 if empty."""
    heats = [grid[r][c].heat for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if grid[r][c] is not None]
    if not heats:
        return 0.0
    return sum(heats) / len(heats)


def get_tile(grid: Grid, r: int, c: int) -> Optional[Tile]:
    """Get tile at position."""
    return grid[r][c]


# ---------------------------------------------------------------------------
# AC-13: No pygame import isolation
# ---------------------------------------------------------------------------


def test_no_pygame_import_in_test_file_itself():
    """Test file itself must not import pygame (headless) - AST based to avoid self-match."""
    import ast

    this_file = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(this_file, filename=str(Path(__file__)))
    forbidden_mod = "pygame"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not (
                    alias.name == forbidden_mod or alias.name.startswith(forbidden_mod + ".")
                ), f"test file must not import {forbidden_mod}: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not (
                mod == forbidden_mod or mod.startswith(forbidden_mod + ".")
            ), f"test file must not import from {forbidden_mod}: {mod}"


def test_no_pygame_import_in_twist_module():
    """AC-13: When twist module is imported, pygame not in sys.modules delta."""
    before = set(sys.modules.keys())
    # This import will FAIL in red phase because twist.py does not exist yet
    import src.core.twist as twist_module  # noqa: F401

    after = set(sys.modules.keys())
    delta = after - before
    assert "pygame" not in delta, f"pygame leaked in delta: {delta & {'pygame'}}"
    assert "pygame" not in sys.modules, "pygame must not be in sys.modules after importing twist"

    # Also grep file content for forbidden imports - use concatenated strings to avoid self-match
    twist_path = Path("src/core/twist.py")
    if twist_path.exists():
        content = twist_path.read_text(encoding="utf-8")
        forbidden_import = "import" + " " + "pygame"
        forbidden_from = "from" + " " + "pygame"
        assert forbidden_import not in content, "twist.py must not import pygame"
        assert forbidden_from not in content, "twist.py must not import from pygame"
        # No bare random.Random() creation inside functions? Check for global random usage
        # Allowed: typing, math, copy, random (but only via injected rng)
        # Forbidden: random.Random() inside function body without injection
        # We allow import random but not bare random.random() without self.rng/rng prefix
        # Simple heuristic: count occurrences of "random.Random()" - should be 0
        # Board.py is allowed to create Random, twist.py must not
        assert content.count("random.Random()") == 0, "twist.py must not create RNG via random.Random()"


def test_no_global_random_usage_in_twist():
    """No global random.random() without rng prefix in twist.py."""
    twist_path = Path("src/core/twist.py")
    if not twist_path.exists():
        # Red phase: file missing, force failure via import
        import src.core.twist  # noqa: F401

    content = twist_path.read_text(encoding="utf-8")
    # Look for bare random.random() or random.choice without rng.
    # Allowed patterns: rng.choice, rng.random, self.rng
    # Forbidden: random.choice, random.random, random.randint at module level inside functions
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Skip import line
        if "import random" in stripped:
            continue
        # Check for forbidden bare random usage
        if "random.random()" in stripped and "rng.random()" not in stripped and "self.rng" not in stripped:
            # Allow if it's in a comment or type hint? Already filtered comment
            # This is a violation
            assert False, f"Line {i} uses bare random.random(): {line}"
        if "random.choice(" in stripped and "rng.choice(" not in stripped and "self.rng" not in stripped:
            assert False, f"Line {i} uses bare random.choice(): {line}"


# ---------------------------------------------------------------------------
# AC-1..AC-5: Heat gen formula table floor(log2(V)/2) clamped 0-3
# ---------------------------------------------------------------------------


def test_heat_gen_V4():
    """AC-1: V=4 log2=2 floor(1)=1."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(4) == 1


def test_heat_gen_V8():
    """AC-2: V=8 log2=3 floor(1.5)=1."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(8) == 1


def test_heat_gen_V16():
    """AC-3: V=16 log2=4 floor(2)=2."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(16) == 2


def test_heat_gen_V32():
    """AC-4: V=32 log2=5 floor(2.5)=2."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(32) == 2


def test_heat_gen_V64_clamped():
    """AC-5: V=64 log2=6 floor(3)=3 clamped."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(64) == 3


def test_heat_gen_V2_zero():
    """Edge: V=2 log2=1 floor(0.5)=0."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(2) == 0


def test_heat_gen_V128_clamped():
    """V=128 log2=7 floor(3.5)=3 clamped."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(128) == 3


def test_heat_gen_V256_clamped():
    """V=256 log2=8 floor(4)=4 clamped to 3."""
    from src.core.twist import _calc_heat_gen_value

    assert _calc_heat_gen_value(256) == 3


def test_heat_gen_table_comprehensive():
    """Comprehensive table V=4->1,8->1,16->2,32->2,64->3 plus edges."""
    from src.core.twist import _calc_heat_gen_value

    cases = [
        (2, 0),
        (4, 1),
        (8, 1),
        (16, 2),
        (32, 2),
        (64, 3),
        (128, 3),
        (256, 3),
        (512, 3),
        (1024, 3),
        (1, 0),  # invalid <2 returns 0
        (0, 0),
    ]
    for value, expected in cases:
        result = _calc_heat_gen_value(value)
        assert result == expected, f"V={value} expected {expected} got {result}"
        assert HEAT_MIN <= result <= HEAT_MAX, f"heat {result} out of range 0-3"


def test_apply_heat_generation_basic():
    """AC-1..5: apply_heat_generation adds heat_gen to merged tile clamped 0-3."""
    from src.core.twist import apply_heat_generation

    grid = make_grid_with_tiles({(2, 2): (4, 0)})
    merges = [MergeInfo(position=(2, 2), value=4, source_positions=[(2, 1), (2, 0)], heat_gen=1)]
    new_grid = apply_heat_generation(grid, merges)
    assert new_grid[2][2] is not None
    assert new_grid[2][2].value == 4
    assert new_grid[2][2].heat == 1  # 0 + 1

    # Clamped: existing heat 3 + gen 1 stays 3
    grid2 = make_grid_with_tiles({(1, 1): (64, 3)})
    merges2 = [MergeInfo(position=(1, 1), value=64, source_positions=[(1, 0), (1, 1)], heat_gen=3)]
    new_grid2 = apply_heat_generation(grid2, merges2)
    assert new_grid2[1][1].heat == 3  # clamped


def test_apply_heat_generation_deep_copy():
    """apply_heat_generation must not mutate input grid."""
    from src.core.twist import apply_heat_generation

    grid = make_grid_with_tiles({(0, 0): (4, 0), (1, 1): (8, 1)})
    original_copy = deep_copy_grid(grid)
    merges = [MergeInfo(position=(0, 0), value=4, source_positions=[(0, 1)], heat_gen=1)]
    _ = apply_heat_generation(grid, merges)
    # Original unchanged
    assert grid[0][0].heat == original_copy[0][0].heat
    assert grid[1][1].heat == original_copy[1][1].heat


def test_apply_heat_generation_empty_grid():
    """Empty grid returns empty unchanged."""
    from src.core.twist import apply_heat_generation

    grid = make_empty_grid()
    new_grid = apply_heat_generation(grid, [])
    assert count_tiles(new_grid) == 0


# ---------------------------------------------------------------------------
# AC-6: Spread heat orthogonal lower deterministic transfer 1
# ---------------------------------------------------------------------------


def test_spread_lower_orthogonal():
    """AC-6: tile heat 2 neighbor 0 orthogonal => neighbor becomes 1 deterministic."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles({(2, 2): (2, 2), (2, 3): (2, 0)})
    new_grid = spread_heat(grid)
    assert new_grid[2][2].heat == 2, "source stays 2"
    assert new_grid[2][3].heat == 1, "neighbor 0->1"


def test_spread_deterministic_repeat():
    """Spread deterministic: same input same output on repeat."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles({(1, 1): (4, 3), (1, 2): (2, 0), (2, 1): (2, 1)})
    out1 = spread_heat(grid)
    out2 = spread_heat(grid)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            t1 = out1[r][c]
            t2 = out2[r][c]
            if t1 is None and t2 is None:
                continue
            assert t1 is not None and t2 is not None
            assert t1.heat == t2.heat, f"non-deterministic at {(r,c)} {t1.heat} vs {t2.heat}"


def test_spread_orthogonal_only_not_diagonal():
    """Spread only orthogonal, not diagonal."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles({(2, 2): (2, 2), (3, 3): (2, 0)})  # diagonal
    new_grid = spread_heat(grid)
    assert new_grid[3][3].heat == 0, "diagonal should not spread"


def test_spread_empty_skipped():
    """Empty neighbors skipped, no crash."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles({(0, 0): (2, 2)})
    new_grid = spread_heat(grid)
    assert new_grid[0][0].heat == 2
    assert count_tiles(new_grid) == 1


def test_spread_multiple_sources_accumulate_clamped():
    """Multiple higher neighbors accumulate +2 clamped to 3."""
    from src.core.twist import spread_heat

    # Center 0 surrounded by two heat 2 orthogonal
    grid = make_grid_with_tiles(
        {
            (1, 1): (2, 2),
            (1, 3): (2, 2),
            (1, 2): (2, 0),
        }
    )
    new_grid = spread_heat(grid)
    # Center receives from both left and right? Actually positions (1,1) neighbor (1,2) yes, (1,3) neighbor (1,2) yes => +2
    assert new_grid[1][2].heat == 2, f"expected 2 from two sources, got {new_grid[1][2].heat}"

    # Clamped to 3
    grid2 = make_grid_with_tiles(
        {
            (0, 1): (2, 3),
            (1, 0): (2, 3),
            (1, 2): (2, 3),
            (2, 1): (2, 3),
            (1, 1): (2, 2),
        }
    )
    new_grid2 = spread_heat(grid2)
    assert new_grid2[1][1].heat == 3, "clamped to 3 even with 4 sources"


def test_spread_source_does_not_lose_heat():
    """Source tile does NOT lose heat (radiation model)."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles({(2, 2): (4, 3), (2, 3): (2, 0)})
    new_grid = spread_heat(grid)
    assert new_grid[2][2].heat == 3, "source should not lose heat"


def test_spread_empty_grid():
    """Empty grid spread returns empty."""
    from src.core.twist import spread_heat

    grid = make_empty_grid()
    new_grid = spread_heat(grid)
    assert count_tiles(new_grid) == 0


# ---------------------------------------------------------------------------
# AC-7: Vent edge -1 interior unchanged never negative
# ---------------------------------------------------------------------------


def test_vent_edge_vs_interior():
    """AC-7: edge heat 2->1, interior 2 stays 2, heat never negative."""
    from src.core.twist import vent_heat

    grid = make_grid_with_tiles(
        {
            (0, 0): (2, 2),  # edge
            (2, 2): (2, 2),  # interior
            (0, 1): (2, 0),  # edge heat 0
        }
    )
    new_grid = vent_heat(grid)
    assert new_grid[0][0].heat == 1, "edge 2->1"
    assert new_grid[2][2].heat == 2, "interior stays 2"
    assert new_grid[0][1].heat == 0, "heat never negative 0 stays 0"


def test_vent_all_edge_positions():
    """All 16 edge positions vent -1."""
    from src.core.twist import vent_heat

    edge_positions = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if r == 0 or r == BOARD_SIZE - 1 or c == 0 or c == BOARD_SIZE - 1:
                edge_positions.append((r, c))
    assert len(edge_positions) == 16, f"expected 16 edge cells, got {len(edge_positions)}"

    mapping = {pos: (2, 2) for pos in edge_positions}
    grid = make_grid_with_tiles(mapping)
    new_grid = vent_heat(grid)
    for pos in edge_positions:
        assert new_grid[pos[0]][pos[1]].heat == 1, f"edge {pos} should vent 2->1"


def test_vent_interior_unchanged():
    """Interior 3x3 (r=1..3,c=1..3) unchanged."""
    from src.core.twist import vent_heat

    interior = [(r, c) for r in range(1, 4) for c in range(1, 4)]
    mapping = {pos: (4, 2) for pos in interior}
    grid = make_grid_with_tiles(mapping)
    new_grid = vent_heat(grid)
    for pos in interior:
        assert new_grid[pos[0]][pos[1]].heat == 2, f"interior {pos} should stay 2"


def test_vent_never_negative():
    """Heat never negative, 0 stays 0."""
    from src.core.twist import vent_heat

    grid = make_grid_with_tiles({(0, 0): (2, 0), (0, 4): (2, 1), (4, 0): (2, 0)})
    new_grid = vent_heat(grid)
    assert new_grid[0][0].heat == 0
    assert new_grid[0][4].heat == 0  # 1->0
    assert new_grid[4][0].heat == 0


def test_vent_empty_grid():
    """Empty grid vent returns empty."""
    from src.core.twist import vent_heat

    grid = make_empty_grid()
    new_grid = vent_heat(grid)
    assert count_tiles(new_grid) == 0


def test_vent_deep_copy():
    """vent_heat must not mutate input."""
    from src.core.twist import vent_heat

    grid = make_grid_with_tiles({(0, 0): (2, 2)})
    orig_heat = grid[0][0].heat
    _ = vent_heat(grid)
    assert grid[0][0].heat == orig_heat


# ---------------------------------------------------------------------------
# AC-8: Unstable >=3 collection
# ---------------------------------------------------------------------------


def test_unstable_collection():
    """AC-8: heat>=3 collected, heat 2 not."""
    from src.core.twist import check_unstable

    grid = make_grid_with_tiles({(1, 1): (2, 3), (2, 2): (4, 2), (3, 3): (8, 3)})
    unstable = check_unstable(grid)
    assert (1, 1) in unstable
    assert (3, 3) in unstable
    assert (2, 2) not in unstable
    assert len(unstable) == 2


def test_unstable_empty_board():
    """Empty board returns empty list."""
    from src.core.twist import check_unstable

    grid = make_empty_grid()
    unstable = check_unstable(grid)
    assert unstable == []


def test_unstable_all_heat_levels():
    """Only heat>=3 unstable, 0,1,2 not."""
    from src.core.twist import check_unstable

    grid = make_grid_with_tiles(
        {
            (0, 0): (2, 0),
            (0, 1): (2, 1),
            (0, 2): (2, 2),
            (0, 3): (2, 3),
            (0, 4): (4, 3),
        }
    )
    unstable = check_unstable(grid)
    assert len(unstable) == 2
    assert (0, 3) in unstable
    assert (0, 4) in unstable


def test_unstable_mixed_board():
    """Mixed board with many tiles."""
    from src.core.twist import check_unstable

    mapping = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            heat = (r + c) % 4
            mapping[(r, c)] = (2, heat)
    grid = make_grid_with_tiles(mapping)
    unstable = check_unstable(grid)
    expected = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if (r + c) % 4 == 3]
    assert set(unstable) == set(expected)


# ---------------------------------------------------------------------------
# AC-9: Spawn heat=0 immune via ordering
# ---------------------------------------------------------------------------


def test_spawn_heat0_immune_via_ordering():
    """AC-9: new tile heat=0 and pipeline order spawn after vent ensures not vented same turn."""
    from src.core.twist import get_turn_pipeline_order, vent_heat

    order = get_turn_pipeline_order()
    # Verify ordering: vent before spawn_heat_0
    assert "vent" in order
    assert "spawn_heat_0" in order
    vent_idx = order.index("vent")
    spawn_idx = order.index("spawn_heat_0")
    assert vent_idx < spawn_idx, f"vent must be before spawn, got order {order}"

    # Simulate: if we spawn at edge after vent, it should stay 0
    # If we incorrectly vent after spawn, edge tile would go 0->0 (still 0) but test logic:
    # Create grid with edge tile heat 0 newly spawned, vent it -> should stay 0 (never negative)
    # The immunity is about ordering, not about vent logic itself
    # So we test that new tile heat is 0 and pipeline says spawn after vent
    grid = make_grid_with_tiles({(0, 0): (2, 0)})  # newly spawned at edge
    # If we call vent after spawn (wrong order), heat stays 0 (clamped)
    # But correct order is spawn after vent, so new tile never sees vent same turn
    # We verify by checking that vent does not make heat negative, and ordering is correct
    new_grid = vent_heat(grid)
    assert new_grid[0][0].heat == 0, "new tile at edge heat 0 stays 0 even if vented (clamped), but pipeline ensures it is not vented same turn"

    # Additional check: spawn tile is always heat 0 per Board._spawn_tile
    from src.core.board import Board

    rng = random.Random(42)
    board = Board(rng=rng)
    board.grid = make_empty_grid()
    board.grid[0][0] = Tile(value=2, heat=2)
    spawned_pos = board.spawn_tile(rng=rng)
    assert spawned_pos is not None
    assert board.grid[spawned_pos[0]][spawned_pos[1]].heat == 0, "spawned tile must have heat 0"


def test_spawn_heat0_value_distribution():
    """Spawned tile value 2 90% or 4 10% heat 0."""
    from src.core.board import Board

    rng = random.Random(123)
    counts = {2: 0, 4: 0}
    for _ in range(100):
        board = Board(rng=random.Random(rng.randint(0, 100000)))
        board.grid = make_empty_grid()
        pos = board.spawn_tile(rng=board.rng)
        if pos:
            val = board.grid[pos[0]][pos[1]].value
            counts[val] += 1
            assert board.grid[pos[0]][pos[1]].heat == 0
    # Should have mostly 2s
    assert counts[2] > counts[4], f"expected more 2s than 4s, got {counts}"
    assert counts[2] + counts[4] == 100


# ---------------------------------------------------------------------------
# AC-12: Cool-merge bonus heat 0 merge
# ---------------------------------------------------------------------------


def test_cool_merge_bonus_heat0():
    """AC-12: heat 0 merge gives bonus."""
    from src.core.twist import calculate_cool_merge_bonus

    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 1), (0, 2)], heat_gen=1),
    ]
    # Need original grid with source positions heat 0
    # For simplicity, create original grid where source positions are heat 0
    orig_grid = make_grid_with_tiles({(0, 1): (2, 0), (0, 2): (2, 0), (0, 0): (4, 0)})
    bonus = calculate_cool_merge_bonus(merges, orig_grid)
    assert bonus >= 1, f"expected bonus >=1 for heat 0 merge, got {bonus}"


def test_cool_merge_bonus_heat1_no_bonus():
    """Heat 1 merge no bonus."""
    from src.core.twist import calculate_cool_merge_bonus

    grid = make_grid_with_tiles({(0, 0): (4, 1), (0, 1): (2, 1), (0, 2): (2, 1)})
    merges = [
        MergeInfo(position=(0, 0), value=4, source_positions=[(0, 1), (0, 2)], heat_gen=1),
    ]
    bonus = calculate_cool_merge_bonus(merges, grid)
    assert bonus == 0, f"expected 0 bonus for heat 1 merge, got {bonus}"


def test_cool_merge_bonus_empty_merges():
    """Empty merges list returns 0 bonus."""
    from src.core.twist import calculate_cool_merge_bonus

    grid = make_empty_grid()
    bonus = calculate_cool_merge_bonus([], grid)
    assert bonus == 0


# ---------------------------------------------------------------------------
# AC-10: Turn pipeline ordering locked
# ---------------------------------------------------------------------------


def test_turn_pipeline_ordering_locked():
    """AC-10: get_turn_pipeline_order returns locked list."""
    from src.core.twist import get_turn_pipeline_order

    order = get_turn_pipeline_order()
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
    assert order == expected, f"pipeline order must be locked {expected}, got {order}"


def test_turn_pipeline_ordering_seeded_scenario():
    """Seeded scenario verifying intermediate heat states after each phase."""
    from src.core.board import Board, Direction
    from src.core.twist import apply_heat_generation, check_unstable, get_turn_pipeline_order, spread_heat, vent_heat

    order = get_turn_pipeline_order()
    assert order == [
        "slide",
        "calc_merge_heat",
        "apply_gen",
        "spread",
        "vent",
        "spawn_heat_0",
        "check_unstable",
        "evaluate_achievements",
    ]

    rng = random.Random(42)
    # Create a known grid with merge possible
    grid = make_grid_with_tiles(
        {
            (0, 0): (2, 0),
            (0, 1): (2, 0),
            (1, 0): (4, 1),
            (1, 1): (2, 2),
        }
    )
    board = Board(grid=grid, rng=rng)
    result = board.slide(Direction.LEFT, rng=rng)
    assert result.moved, "expected move"

    # Phase: calc_merge_heat already in MergeInfo.heat_gen
    # Phase: apply_gen
    grid_after_gen = apply_heat_generation(result.grid, result.merges)
    # Check heat increased on merged positions
    for merge in result.merges:
        r, c = merge.position
        if grid_after_gen[r][c] is not None:
            assert grid_after_gen[r][c].heat >= 0

    # Phase: spread
    grid_after_spread = spread_heat(grid_after_gen)

    # Phase: vent
    grid_after_vent = vent_heat(grid_after_spread)

    # Phase: spawn heat 0 (already done in board.slide if moved)
    # Verify spawned tile heat 0
    # Find new tile that wasn't in original
    # For simplicity, check all tiles heat in range
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = grid_after_vent[r][c]
            if tile is not None:
                assert 0 <= tile.heat <= 3

    # Phase: check_unstable
    unstable = check_unstable(grid_after_vent)
    assert isinstance(unstable, list)
    for pos in unstable:
        r, c = pos
        assert grid_after_vent[r][c] is not None
        assert grid_after_vent[r][c].heat >= 3


def test_turn_pipeline_string_representation():
    """Pipeline string slide->gen->spread->vent->spawn heat=0->unstable->achievements."""
    from src.core.twist import get_turn_pipeline_order

    order = get_turn_pipeline_order()
    pipeline_str = "->".join(order)
    # Check key substrings
    assert "slide" in pipeline_str
    assert "apply_gen" in pipeline_str or "gen" in pipeline_str
    assert "spread" in pipeline_str
    assert "vent" in pipeline_str
    assert "spawn_heat_0" in pipeline_str
    assert "check_unstable" in pipeline_str


# ---------------------------------------------------------------------------
# Seeded determinism
# ---------------------------------------------------------------------------


def test_seeded_determinism_same_seed_same_transitions():
    """Same seed same heat transitions deterministic."""
    from src.core.twist import apply_heat_generation, spread_heat, vent_heat

    # Same initial grid
    grid1 = make_grid_with_tiles({(2, 2): (4, 1), (2, 3): (2, 0), (0, 0): (2, 2)})
    grid2 = deep_copy_grid(grid1)

    merges = [MergeInfo(position=(2, 2), value=4, source_positions=[(2, 1)], heat_gen=1)]

    # Apply same pipeline
    g1 = apply_heat_generation(grid1, merges)
    g1 = spread_heat(g1)
    g1 = vent_heat(g1)

    g2 = apply_heat_generation(grid2, merges)
    g2 = spread_heat(g2)
    g2 = vent_heat(g2)

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            t1 = g1[r][c]
            t2 = g2[r][c]
            if t1 is None and t2 is None:
                continue
            assert t1 is not None and t2 is not None
            assert t1.value == t2.value
            assert t1.heat == t2.heat, f"non-deterministic at {(r,c)} with same seed"


def test_spread_determinism_no_rng():
    """Spread must be deterministic without RNG."""
    from src.core.twist import spread_heat

    grid = make_grid_with_tiles(
        {
            (1, 1): (2, 3),
            (1, 2): (2, 0),
            (2, 1): (2, 1),
            (2, 2): (2, 0),
        }
    )
    results = []
    for _ in range(5):
        new_grid = spread_heat(deep_copy_grid(grid))
        # Serialize heats
        heats = tuple(
            (r, c, new_grid[r][c].heat) if new_grid[r][c] else (r, c, None)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
        )
        results.append(heats)
    # All same
    assert all(r == results[0] for r in results), "spread not deterministic across 5 runs"


# ---------------------------------------------------------------------------
# AC-11: Average heat measurement Q-001 50/100/200 moves seeded
# ---------------------------------------------------------------------------


def test_average_heat_measurement_Q001():
    """AC-11: Average heat over 50/100/200 moves seeded, document if >2.0 tuning note."""
    from src.core.board import Board, Direction
    from src.core.twist import apply_heat_generation, spread_heat, vent_heat

    seeds = [42, 123, 999]
    move_counts = [50, 100, 200]
    directions = [Direction.LEFT, Direction.RIGHT, Direction.UP, Direction.DOWN]

    print("\n=== Q-001 Average Heat Measurement ===")
    all_averages = []

    for seed in seeds:
        for move_count_target in move_counts:
            # Reset for each move count? We run cumulative
            # For simplicity, run move_count_target moves from current state
            # Actually run fresh for each target to keep independent
            test_rng = random.Random(seed)
            # Need to re-init board with empty then spawn? Use board as is
            test_board = Board(rng=random.Random(seed))
            test_board.grid = make_empty_grid()
            test_board.grid[0][0] = Tile(value=2, heat=0)
            test_board.grid[1][1] = Tile(value=2, heat=0)

            moves_done = 0
            attempts = 0
            max_attempts = move_count_target * 5  # allow failed moves

            while moves_done < move_count_target and attempts < max_attempts:
                direction = test_rng.choice(directions)
                result = test_board.slide(direction, rng=test_rng)
                if result.moved:
                    # Apply twist pipeline manually for measurement
                    # Note: board.slide already spawns, but we need to apply heat gen, spread, vent
                    # For measurement, we simulate full pipeline:
                    # result.grid already has spawn, but we need to apply gen->spread->vent
                    # Actually board.slide does not apply twist yet, so we apply here
                    grid_after_gen = apply_heat_generation(result.grid, result.merges)
                    grid_after_spread = spread_heat(grid_after_gen)
                    grid_after_vent = vent_heat(grid_after_spread)
                    test_board.grid = grid_after_vent
                    moves_done += 1
                attempts += 1

            avg = average_heat(test_board.grid)
            all_averages.append(avg)
            print(f"Seed {seed} Moves {move_count_target}: avg heat {avg:.3f} tiles {count_tiles(test_board.grid)}")

            # Document tuning rationale if >2.0
            if avg > 2.0:
                print(
                    f"  TUNING NOTE Q-001: avg heat {avg:.3f} >2.0 for seed {seed} moves {move_count_target} "
                    f"- consider increasing vent rate or reducing heat gen formula"
                )

            # Assert measurement completed (not asserting avg threshold, just documenting)
            assert 0.0 <= avg <= 3.0, f"avg heat {avg} out of range 0-3"

    overall_avg = sum(all_averages) / len(all_averages) if all_averages else 0
    print(f"Overall average heat across all runs: {overall_avg:.3f}")
    print(f"Max average observed: {max(all_averages):.3f}" if all_averages else "No data")
    print("=== End Q-001 Measurement ===")

    # If overall average >2.0, capture tuning note but don't fail test
    # The AC says document tuning rationale if >2.0, not fail
    if overall_avg > 2.0:
        print(
            f"Q-001 TUNING REQUIRED: overall avg {overall_avg:.3f} >2.0 - "
            f"thermal runaway risk, consider: increase VENT_AMOUNT, reduce heat gen, or increase edge ratio"
        )
    # Test passes as long as measurement completed
    assert len(all_averages) == len(seeds) * len(move_counts)


def test_average_heat_never_exceeds_max():
    """Average heat never exceeds HEAT_MAX 3."""
    from src.core.twist import spread_heat, vent_heat

    grid = make_empty_grid()
    # Fill board with high heat tiles
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            grid[r][c] = Tile(value=2, heat=3)

    # Apply spread and vent many times, average should stay <=3
    for _ in range(10):
        grid = spread_heat(grid)
        grid = vent_heat(grid)
        avg = average_heat(grid)
        assert avg <= 3.0, f"avg {avg} exceeds max 3"
        assert avg >= 0.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_invalid_grid_raises():
    """Invalid grid not 5x5 raises ValueError E002."""
    from src.core.twist import apply_heat_generation, check_unstable, spread_heat, vent_heat

    invalid_grid = [[None] * 4 for _ in range(4)]  # 4x4
    with pytest.raises(ValueError, match="E002"):
        apply_heat_generation(invalid_grid, [])
    with pytest.raises(ValueError, match="E002"):
        spread_heat(invalid_grid)
    with pytest.raises(ValueError, match="E002"):
        vent_heat(invalid_grid)
    with pytest.raises(ValueError, match="E002"):
        check_unstable(invalid_grid)


def test_is_edge_position():
    """_is_edge_position helper."""
    from src.core.twist import _is_edge_position

    assert _is_edge_position(0, 0) is True
    assert _is_edge_position(0, 2) is True
    assert _is_edge_position(4, 4) is True
    assert _is_edge_position(2, 0) is True
    assert _is_edge_position(2, 4) is True
    assert _is_edge_position(2, 2) is False
    assert _is_edge_position(1, 1) is False
    assert _is_edge_position(3, 3) is False


def test_heat_clamped_both_directions():
    """Heat clamped 0-3 in all operations."""
    from src.core.twist import apply_heat_generation, spread_heat, vent_heat

    # Gen clamped
    grid = make_grid_with_tiles({(0, 0): (256, 3)})
    merges = [MergeInfo(position=(0, 0), value=256, source_positions=[(0, 1)], heat_gen=3)]
    new_grid = apply_heat_generation(grid, merges)
    assert new_grid[0][0].heat == 3

    # Vent clamped
    grid2 = make_grid_with_tiles({(0, 0): (2, 0)})
    new_grid2 = vent_heat(grid2)
    assert new_grid2[0][0].heat == 0

    # Spread clamped
    grid3 = make_grid_with_tiles({(1, 1): (2, 3), (1, 2): (2, 3)})
    new_grid3 = spread_heat(grid3)
    assert new_grid3[1][1].heat <= 3
    assert new_grid3[1][2].heat <= 3
    # Use rng to satisfy linter if needed - actually no rng needed
    _ = BOARD_SIZE