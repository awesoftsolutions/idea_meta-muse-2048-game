"""Core exports facade for headless 5x5 Tile board with rules.

Purpose: Re-exports 9 board symbols (Tile, Board, Direction, SlideResult,
    MergeInfo, BOARD_SIZE, HEAT_MIN, HEAT_MAX, create_empty_grid) plus
    2 rules symbols (is_legal_move, is_game_over) per remediation wave
    and pseudocode exports verification. Ensures src/core is importable
    headlessly without pygame per ADR-015 and E007.

System: src/core per Phase 2 architecture.

Dependencies: .board and .rules modules (stdlib only, no pygame).

Used-by: tests/test_isolation_phase2.py, tests/test_board.py,
    tests/test_rules.py, future game loop.

Public interface:
    - Tile, Board, Direction, SlideResult, MergeInfo, BOARD_SIZE,
      HEAT_MIN, HEAT_MAX, create_empty_grid re-exported from .board
    - is_legal_move, is_game_over re-exported from .rules
"""
# CHANGELOG:
# - Phase 2 Sprint 1: __all__ 11 exports restoration - 9 board symbols (Tile,
#   Board, Direction, SlideResult, MergeInfo, BOARD_SIZE, HEAT_MIN, HEAT_MAX,
#   create_empty_grid) plus 2 rules symbols (is_legal_move, is_game_over).
#   Ensures src/core importable headlessly without pygame per ADR-015/E007.
# - Phase 1 Sprint 1: Initial core facade.

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
from .rules import (
    is_legal_move,
    is_game_over,
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
    "is_legal_move",
    "is_game_over",
]
