"""Generate first-light screenshot headless."""
from __future__ import annotations

import pathlib

import pygame

from src.core.board import Tile, create_empty_grid
from src.render.tiles import draw_board


def main() -> None:
    pygame.init()
    surface = pygame.Surface((700, 800))
    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    draw_board(surface, grid, 0)
    out_dir = pathlib.Path("visual-proof")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "phase-3-first-light.png"
    try:
        pygame.image.save(surface, str(out_path))
        print(f"saved {out_path} 700x800")
        with open(out_path, "rb") as f:
            header = f.read(8)
        print(f"header={header.hex()} size={out_path.stat().st_size}")
        expected = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        assert header == expected, f"Invalid PNG header {header.hex()}"
        assert out_path.stat().st_size > 1000
    except OSError as e:
        print(f"Warning: Screenshot save failed: {e}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
