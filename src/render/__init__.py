"""
src/render/__init__.py — Render package exports.

Exports draw_board and helpers per Phase 3 architecture.
"""

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
