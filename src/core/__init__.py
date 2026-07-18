"""src/core/__init__.py — Exports for production board.

Purpose:
    Public API surface for core board production. Re-exports Tile dataclass,
    Direction enum, MergeInfo, SlideResult, Board with injectable RNG, and
    constants BOARD_SIZE, HEAT_MIN, HEAT_MAX, plus create_empty_grid helper.

System:
    Pure-Python core module, no pygame, no global random. Used by game logic
    and tests. Board implements 5x5 2048 slide/merge with compress-merge-compress
    and merged-flag preventing double merge, spawn 90/10 heat=0 immune per ADR-009.

Dependencies:
    src.core.board — Tile, Board, Direction, MergeInfo, SlideResult, constants.

Used-by:
    Game controller, heat system, spawn system, tests.

Public Interface:
    Tile(value: int, heat: int = 0) — dataclass with clamped heat 0-3.
    Direction — Enum UP/DOWN/LEFT/RIGHT.
    MergeInfo(position, value, source_positions, heat_gen) — merge event.
    SlideResult(grid, score_delta, moved, merges) — slide return.
    Board(grid, rng) — 5x5 board with injectable RNG, slide() method.
    BOARD_SIZE, HEAT_MIN, HEAT_MAX — constants.
    create_empty_grid() -> Grid — 5x5 None grid.
"""

from .board import (
    BOARD_SIZE,
    HEAT_MAX,
    HEAT_MIN,
    Board,
    Direction,
    MergeInfo,
    SlideResult,
    Tile,
    create_empty_grid,
)

__all__ = [
    "Tile",
    "Board",
    "Direction",
    "SlideResult",
    "MergeInfo",
    "BOARD_SIZE",
    "HEAT_MIN",
    "HEAT_MAX",
    "create_empty_grid",
]
