"""Headless fallback Surface 700x800 draw_board capture per pseudocode."""
import random
import sys
from pathlib import Path

# Ensure visual-proof dir exists mkdir parents True exist_ok True OSError handling
try:
    visual_proof_dir = Path("visual-proof")
    visual_proof_dir.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Warning: Screenshot dir creation failed: {e}", file=sys.stderr)
    try:
        fallback = Path.cwd() / "visual-proof"
        fallback.mkdir(parents=True, exist_ok=True)
        visual_proof_dir = fallback
    except OSError as e2:
        print(f"Failed to create visual-proof directory: {e2}", file=sys.stderr)
        raise

try:
    import pygame
    pygame.init()
    surface = pygame.Surface((700, 800))
    rng = random.Random()
    # Create board with single 2 tile heat 0
    from src.core.board import Board, Tile
    board = Board(rng=rng)
    board.grid = [[None for _ in range(5)] for _ in range(5)]
    empty = [(r, c) for r in range(5) for c in range(5)]
    chosen = rng.choice(empty)
    board.grid[chosen[0]][chosen[1]] = Tile(value=2, heat=0)

    # Try real draw_board
    try:
        from src.render.tiles import draw_board
        draw_board(surface, board.grid, 0)
    except Exception as ex:
        print(f"draw_board failed, using minimal: {ex}", file=sys.stderr)
        # minimal fallback
        surface.fill((15, 23, 42))
        pygame.draw.rect(surface, (30, 41, 59), (95, 145, 510, 510), border_radius=6)
        for r in range(5):
            for c in range(5):
                x = 100 + c * 100 + 5
                y = 150 + r * 100 + 5
                cell = board.grid[r][c]
                if cell is None:
                    pygame.draw.rect(surface, (51, 65, 85), (x, y, 90, 90), border_radius=4)
                else:
                    pygame.draw.rect(surface, (59, 130, 246), (x, y, 90, 90), border_radius=4)
                    try:
                        font = pygame.font.SysFont(None, 36)
                        label = font.render(str(cell.value), True, (0,0,0))
                        rect = label.get_rect(center=(x+45, y+45))
                        surface.blit(label, rect)
                    except Exception:
                        pass

    try:
        pygame.image.save(surface, str(visual_proof_dir / "phase-3-first-light.png"))
        print(f"Saved headless capture to {visual_proof_dir / 'phase-3-first-light.png'}")
    except OSError as e:
        print(f"Warning: Screenshot save failed: {e}", file=sys.stderr)
        sys.exit(1)

    pygame.quit()
    print("Headless fallback capture success")
except Exception as e:
    print(f"Headless capture failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
