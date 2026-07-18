import pathlib, random, sys
from pathlib import Path
try:
    import pygame
    from src.core.board import Board, Tile
    from src.render.tiles import draw_board
    pygame.init()
    surface = pygame.Surface((700,800))
    rng = random.Random()
    board = Board(rng=rng)
    board.grid = [[None for _ in range(5)] for _ in range(5)]
    empty = [(r,c) for r in range(5) for c in range(5)]
    chosen = rng.choice(empty)
    board.grid[chosen[0]][chosen[1]] = Tile(value=2, heat=0)
    draw_board(surface, board.grid, 0)
    visual_proof_dir = Path("visual-proof")
    try:
        visual_proof_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Warning dir creation failed: {e}", file=sys.stderr)
    try:
        pygame.image.save(surface, str(visual_proof_dir / "phase-3-first-light.png"))
        print("Recaptured 700x800 PNG via headless fallback")
    except OSError as e:
        print(f"Warning save failed: {e}", file=sys.stderr)
        sys.exit(1)
    pygame.quit()
    # validate
    p = Path("visual-proof/phase-3-first-light.png")
    data = p.read_bytes()
    print(f"size {len(data)} header {list(data[:8])}")
    idx = data.find(b'IHDR')
    w = int.from_bytes(data[idx+4:idx+8],'big')
    h = int.from_bytes(data[idx+8:idx+12],'big')
    print(f"dims {w}x{h}")
    assert w==700 and h==800
    print("VALID")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback; traceback.print_exc()
    sys.exit(1)
