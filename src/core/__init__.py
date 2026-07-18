"""Core exports facade for headless 5x5 Tile board with rules, score, history, twist, achievements, gamestate.

Purpose: Re-exports board symbols (Tile, Board, Direction, SlideResult,
    MergeInfo, BOARD_SIZE, HEAT_MIN, HEAT_MAX, create_empty_grid) plus
    rules symbols (is_legal_move, is_game_over), score symbols (ScoreState,
    Score, DEFAULT_HIGH_SCORE_PATH), history symbols (HistorySnapshot,
    HistoryStack), twist symbols (apply_heat_generation, spread_heat,
    vent_heat, check_unstable, calculate_cool_merge_bonus,
    get_turn_pipeline_order), achievements symbols (Achievements,
    AchievementDef, GameContext), and gamestate symbols (GameState) per
    Phase 3 Sprint 1 Wave1 GameState ownership Q-005 and Q-004 fix.
    Ensures src/core is importable headlessly without pygame per ADR-015
    and E007. 26 exports total including GameState.

System: src/core per Phase 2 architecture.

Dependencies: .board, .rules, .score, .history, .twist, .achievements modules
    (stdlib only, no pygame).

Used-by: tests/test_isolation_phase2.py, tests/test_isolation_phase2_sprint2.py,
    tests/test_board.py, tests/test_rules.py, tests/test_score.py,
    tests/test_history.py, tests/test_twist.py, tests/test_achievements.py,
    future game loop.

Public interface:
    - Tile, Board, Direction, SlideResult, MergeInfo, BOARD_SIZE,
      HEAT_MIN, HEAT_MAX, create_empty_grid re-exported from .board
    - is_legal_move, is_game_over re-exported from .rules
    - ScoreState, Score, DEFAULT_HIGH_SCORE_PATH re-exported from .score
    - HistorySnapshot, HistoryStack re-exported from .history
    - apply_heat_generation, spread_heat, vent_heat, check_unstable,
      calculate_cool_merge_bonus, get_turn_pipeline_order re-exported from .twist
    - Achievements, AchievementDef, GameContext re-exported from .achievements
"""
# CHANGELOG:
# - Phase 2 Sprint 3 Task 3: __all__ 25 exports final verification - 9 board symbols
#   (Tile, Board, Direction, SlideResult, MergeInfo, BOARD_SIZE, HEAT_MIN, HEAT_MAX,
#   create_empty_grid) plus 2 rules symbols (is_legal_move, is_game_over),
#   3 score symbols (ScoreState, Score, DEFAULT_HIGH_SCORE_PATH),
#   2 history symbols (HistorySnapshot, HistoryStack),
#   6 twist symbols (apply_heat_generation, spread_heat, vent_heat,
#   check_unstable, calculate_cool_merge_bonus, get_turn_pipeline_order),
#   3 achievements symbols (Achievements, AchievementDef, GameContext).
#   Ensures src/core importable headlessly without pygame per ADR-015/E007.
#   Final verification PASS AC-1 to AC-10 Q-001 avg <2.0 ref 1.803.
# - Phase 2 Sprint 2 Task 4: __all__ 21 exports restoration.
# - Phase 2 Sprint 1: __all__ 11 exports restoration - 9 board symbols plus 2 rules.
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
from .history import (
    HistorySnapshot,
    HistoryStack,
)
from .rules import (
    is_game_over,
    is_legal_move,
)
from .score import (
    DEFAULT_HIGH_SCORE_PATH,
    Score,
    ScoreState,
)
from .achievements import (
    AchievementDef,
    Achievements,
    GameContext,
)
from .gamestate import GameState
from .twist import (
    apply_heat_generation,
    calculate_cool_merge_bonus,
    check_unstable,
    get_turn_pipeline_order,
    spread_heat,
    vent_heat,
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
    "ScoreState",
    "Score",
    "DEFAULT_HIGH_SCORE_PATH",
    "HistorySnapshot",
    "HistoryStack",
    "apply_heat_generation",
    "spread_heat",
    "vent_heat",
    "check_unstable",
    "calculate_cool_merge_bonus",
    "get_turn_pipeline_order",
    "Achievements",
    "AchievementDef",
    "GameContext",
    "GameState",
]