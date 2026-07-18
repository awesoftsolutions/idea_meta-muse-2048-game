import pygame, random, sys
from pathlib import Path
pygame.init()
screen = pygame.display.set_mode((700,800), flags=0)
pygame.display.set_caption("Favur 2048")
from src.core.board import Board, Tile
from src.render.tiles import draw_board
from src.render.effects import EffectManager

rng = random.Random(42)
board = Board(rng=rng)
board.grid = [[None for _ in range(5)] for _ in range(5)]
board.grid[2][2] = Tile(value=2, heat=0)
board.grid[1][1] = Tile(value=4, heat=1)

# draw board
draw_board(screen, board.grid, 0)

# effect manager with particles
em = EffectManager()
class _SyntheticMerge:
    def __init__(self, pos, value, heat_gen, source_heats):
        self.position = pos
        self.value = value
        self.heat_gen = heat_gen
        self.source_heats = source_heats
        self.source_positions = [pos, pos]

synthetic = [
    _SyntheticMerge((2,2), 4, 1, (0,0)),
    _SyntheticMerge((1,1), 8, 2, (1,1)),
]
em.start_merge(synthetic)
em.update(0.05)
em.draw(screen, None)

Path("visual-proof").mkdir(parents=True, exist_ok=True)
pygame.image.save(screen, "visual-proof/phase-4-effects.png")
print("saved 700x800")
# verify
import pathlib
p = pathlib.Path("visual-proof/phase-4-effects.png")
data = p.read_bytes()
print(f"header {data[:4].hex()} size {len(data)}")
img = pygame.image.load(str(p))
print(f"dims {img.get_width()}x{img.get_height()}")
pygame.quit()
