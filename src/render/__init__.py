"""
src/render/__init__.py — Render package exports.

Exports draw_board and helpers per Phase 3 architecture.
"""
# CHANGELOG:
# - Phase 3 Sprint 1: CREATED programmatic tile rendering heat identity
#   #3B82F6 #F59E0B #EF4444 #FFFFFF glow reactor chrome.

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
]
