"""Recapture first-light screenshot via headless fallback per SOW Visual Verification Protocol."""
import pathlib
import sys
import random

# Ensure visual-proof dir exists
visual_proof_dir = pathlib.Path("visual-proof")
visual_proof_dir.mkdir(parents=True, exist_ok=True)

try:
    import pygame
    from src.core.board import Tile, create_empty_grid
    from src.render.tiles import draw_board

    # Create 700x800 surface
    pygame.init()
    surface = pygame.Surface((700, 800))

    # Create real board single 2 tile heat 0
    rng = random.Random(42)
    grid = create_empty_grid()
    # Place single 2 tile heat 0 at random position via rng
    empty = [(r, c) for r in range(5) for c in range(5)]
    chosen = rng.choice(empty)
    grid[chosen[0]][chosen[1]] = Tile(value=2, heat=0)

    # Draw board
    draw_board(surface, grid, score=0)

    # Save via pygame.image.save with OSError handling
    try:
        pygame.image.save(surface, str(visual_proof_dir / "phase-3-first-light.png"))
        print(f"Recaptured screenshot to {visual_proof_dir / 'phase-3-first-light.png'}")
        # Validate
        data = (visual_proof_dir / "phase-3-first-light.png").read_bytes()
        print(f"size={len(data)} header_valid={data[:8]==bytes([0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A])}")
    except OSError as e:
        print(f"Warning: Screenshot save failed: {e}", file=sys.stderr)
        sys.exit(1)

    pygame.quit()

except Exception as e:
    print(f"Recapture failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
