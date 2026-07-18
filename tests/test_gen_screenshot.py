def test_gen():
    import pathlib, pygame
    from src.core.board import Tile, create_empty_grid
    from src.render.tiles import draw_board
    pygame.init()
    s = pygame.Surface((700,800))
    grid = create_empty_grid()
    grid[0][0] = Tile(value=2, heat=0)
    draw_board(s, grid, 0)
    pathlib.Path("visual-proof").mkdir(parents=True, exist_ok=True)
    pygame.image.save(s, "visual-proof/phase-3-first-light.png")
    pygame.quit()
    assert pathlib.Path("visual-proof/phase-3-first-light.png").exists()
