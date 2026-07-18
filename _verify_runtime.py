from src.core import Tile, Board, Direction, SlideResult, MergeInfo, BOARD_SIZE, HEAT_MIN, HEAT_MAX, create_empty_grid, is_legal_move, is_game_over
import src.core as core_mod
print('ok')
print(core_mod.__all__)

import sys
before = set(sys.modules.keys())
import src.core
after = set(sys.modules.keys())
delta = after - before
pygame_delta = [k for k in delta if k == "pygame" or k.startswith("pygame.")]
print(f"pygame delta: {pygame_delta}")
assert "pygame" not in after or "pygame" in before, "pygame leak"
print("no pygame leak ok")

# Check file ends with newline
content = open("src/core/__init__.py", encoding="utf-8").read()
assert content.endswith("\n"), "must end with newline"
assert "import pygame" not in content
assert "from pygame" not in content
assert "from src.core.board import" not in content
assert "from src.core.rules import" not in content
print("file structure ok")
