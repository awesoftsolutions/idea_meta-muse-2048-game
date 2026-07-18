"""
src/render/__init__.py — Render package exports.

Exports draw_board and helpers per Phase 3 architecture and Phase 4 HUD.
"""
# CHANGELOG:
# - Phase 3 Sprint 1: CREATED programmatic tile rendering heat identity
#   #3B82F6 #F59E0B #EF4444 #FFFFFF glow reactor chrome.
# - Phase 3 Sprint 2: VERIFIED exports draw_board lerp_heat_color
#   value_to_base_color blend_colors cell_rect final audit.
# - Phase 4 Sprint 1 Task 3: ADDED HUD exports draw_hud Toast ToastManager
#   draw_hud_with_gamestate draw_game_over_stub reactor chrome constants.
# - Phase 4 Sprint 2 Task 1: ADDED draw_game_over canonical export.

from src.render.effects import EffectManager
from src.render.hud import (
    BOARD_BG as HUD_BOARD_BG,
    BORDER as HUD_BORDER,
    EMPTY_CELL as HUD_EMPTY_CELL,
    HEAT_COOL,
    HEAT_HOT,
    HEAT_UNSTABLE,
    HEAT_WARM,
    HUD_H,
    MAX_TOASTS,
    REACTOR_BG,
    TOAST_DURATION,
    TOAST_GAP,
    TOAST_H,
    TOAST_W,
    WINDOW_H,
    WINDOW_W,
    Toast,
    ToastManager,
    draw_game_over,
    draw_game_over_stub,
    draw_hud,
    draw_hud_with_gamestate,
)

from src.render.tiles import (
    blend_colors,
    cell_rect,
    draw_board,
    lerp_heat_color,
    value_to_base_color,
)

__all__ = [
    "draw_board",
    "lerp_heat_color",
    "value_to_base_color",
    "blend_colors",
    "cell_rect",
    "EffectManager",
    "draw_hud",
    "draw_hud_with_gamestate",
    "draw_game_over",
    "draw_game_over_stub",
    "Toast",
    "ToastManager",
    "REACTOR_BG",
    "HEAT_COOL",
    "HEAT_WARM",
    "HEAT_HOT",
    "HEAT_UNSTABLE",
    "WINDOW_W",
    "WINDOW_H",
    "HUD_H",
    "TOAST_W",
    "TOAST_H",
    "TOAST_DURATION",
    "TOAST_GAP",
    "MAX_TOASTS",
    "HUD_BOARD_BG",
    "HUD_BORDER",
    "HUD_EMPTY_CELL",
]
