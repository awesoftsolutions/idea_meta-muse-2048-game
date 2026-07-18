"""Production main loop for Favur 2048.

Implements production main loop per ADR-019 with real 5x5 board,
GameState ownership per ADR-016, turn pipeline locked per ADR-009.

Purpose:
    Production entry point with pygame-ce API verification, 700x800
    non-resizable window titled exactly Favur 2048, Board with injectable
    Random single 2 tile heat 0, arrow input dispatch with legal check,
    history push including GameState, turn pipeline locked via board.slide()
    internal, ScoreState HistoryStack Achievements GameState integration,
    undo restores exact including heat and GameState, Escape quits,
    clock 60 FPS, first-frame screenshot placeholder.

System:
    MainLoopProduction per Phase 3 architecture ADR-019.

Dependencies:
    pygame-ce ^2.5.0, stdlib random sys pathlib copy, src.core.*,
    src.core.rules.is_legal_move.

Public Interface:
    verify_pygame_api() -> bool: Verify required pygame-ce APIs exist.
    create_initial_board(rng) -> Board: Create board with single 2 tile heat 0.
    main() -> None: Production main loop entry point.
"""

from __future__ import annotations

import copy
import random
import sys
from pathlib import Path
from typing import Optional

import pygame

from src.core.board import Board, Direction, Tile
from src.core.gamestate import GameState
from src.core.history import HistorySnapshot, HistoryStack
from src.core.rules import is_legal_move
from src.core.score import ScoreState
from src.core.achievements import Achievements, GameContext
from src.core.twist import vent_heat, check_unstable


def verify_pygame_api() -> bool:
    """Verify required pygame-ce APIs exist via hasattr.

    Checks existence of required APIs including font.SysFont and image.save
    per Task3 AC-20.

    Returns:
        True if all required APIs exist.

    Raises:
        ImportError: If pygame-ce is not installed or any required API is missing.
    """
    try:
        import pygame as _pg  # noqa: F401 - verify importable
    except ImportError as exc:
        raise ImportError(
            "pygame-ce not installed, run poetry install"
        ) from exc

    required = [
        ("pygame.init", lambda: callable(getattr(pygame, "init", None))),
        ("pygame.display.set_mode", lambda: callable(getattr(getattr(pygame, "display", None), "set_mode", None))),
        ("pygame.display.set_caption", lambda: callable(getattr(getattr(pygame, "display", None), "set_caption", None))),
        ("pygame.font.SysFont", lambda: callable(getattr(getattr(pygame, "font", None), "SysFont", None))),
        ("pygame.event.get", lambda: callable(getattr(getattr(pygame, "event", None), "get", None))),
        ("pygame.image.save", lambda: callable(getattr(getattr(pygame, "image", None), "save", None))),
        ("pygame.QUIT", lambda: hasattr(pygame, "QUIT")),
        ("pygame.KEYDOWN", lambda: hasattr(pygame, "KEYDOWN")),
        ("pygame.K_ESCAPE", lambda: hasattr(pygame, "K_ESCAPE")),
        ("pygame.K_UP", lambda: hasattr(pygame, "K_UP")),
        ("pygame.K_DOWN", lambda: hasattr(pygame, "K_DOWN")),
        ("pygame.K_LEFT", lambda: hasattr(pygame, "K_LEFT")),
        ("pygame.K_RIGHT", lambda: hasattr(pygame, "K_RIGHT")),
        ("pygame.K_u", lambda: hasattr(pygame, "K_u")),
        ("pygame.K_z", lambda: hasattr(pygame, "K_z")),
        ("pygame.draw.rect", lambda: callable(getattr(getattr(pygame, "draw", None), "rect", None))),
        ("pygame.draw.circle", lambda: callable(getattr(getattr(pygame, "draw", None), "circle", None))),
        ("pygame.time.Clock", lambda: callable(getattr(getattr(pygame, "time", None), "Clock", None))),
        ("pygame.quit", lambda: callable(getattr(pygame, "quit", None))),
    ]

    missing = [name for name, check in required if not check()]
    if missing:
        raise ImportError(
            f"Missing pygame-ce APIs: {', '.join(missing)}. "
            "Verify installed docs, run poetry install, expected pygame-ce ^2.5.0"
        )
    return True


def create_initial_board(rng: random.Random) -> Board:
    """Create Board with single 2 tile heat 0.

    Args:
        rng: Random instance for deterministic spawn.

    Returns:
        Board with single Tile(2,0).
    """
    board = Board(rng=rng)
    # Ensure empty then place single 2 tile heat 0
    board.grid = [[None for _ in range(5)] for _ in range(5)]
    empty = [(r, c) for r in range(5) for c in range(5)]
    chosen = rng.choice(empty)
    board.grid[chosen[0]][chosen[1]] = Tile(value=2, heat=0)
    return board


def _draw_minimal_board(screen: pygame.Surface, board: Board, score: ScoreState) -> None:
    """Draw minimal placeholder board 5x5 rects.

    Args:
        screen: Pygame surface 700x800.
        board: Board with grid.
        score: ScoreState for debug display.
    """
    background_color = (15, 23, 42)  # #0F172A
    board_bg = (30, 41, 59)  # #1E293B
    empty_cell = (51, 65, 85)  # #334155
    tile_colors = {
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
        64: (246, 94, 59),
        128: (237, 207, 114),
        256: (237, 204, 97),
        512: (237, 200, 80),
        1024: (237, 197, 63),
        2048: (237, 194, 46),
    }

    screen.fill(background_color)

    board_size_px = 500
    cell_gap = 10
    cell_size = board_size_px // 5 - cell_gap
    board_origin_x = (700 - board_size_px) // 2
    board_origin_y = 150

    pygame.draw.rect(
        screen,
        board_bg,
        (board_origin_x - 5, board_origin_y - 5, board_size_px + 10, board_size_px + 10),
        border_radius=6,
    )

    try:
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score.current_score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))
    except Exception:
        pass

    for r in range(5):
        for c in range(5):
            x = board_origin_x + c * (cell_size + cell_gap) + cell_gap // 2
            y = board_origin_y + r * (cell_size + cell_gap) + cell_gap // 2
            rect = (x, y, cell_size, cell_size)
            cell = board.grid[r][c]
            if cell is None:
                pygame.draw.rect(screen, empty_cell, rect, border_radius=4)
            else:
                base_color = tile_colors.get(cell.value, (200, 200, 200))
                heat_colors = {
                    0: (59, 130, 246),
                    1: (245, 158, 11),
                    2: (239, 68, 68),
                    3: (255, 255, 255),
                }
                heat_color = heat_colors.get(cell.heat, (59, 130, 246))
                blended = (
                    int(base_color[0] * 0.7 + heat_color[0] * 0.3),
                    int(base_color[1] * 0.7 + heat_color[1] * 0.3),
                    int(base_color[2] * 0.7 + heat_color[2] * 0.3),
                )
                pygame.draw.rect(screen, blended, rect, border_radius=4)
                try:
                    tile_font = pygame.font.SysFont(None, 28)
                    label = tile_font.render(str(cell.value), True, (0, 0, 0))
                    label_rect = label.get_rect(center=(x + cell_size // 2, y + cell_size // 2))
                    screen.blit(label, label_rect)
                except Exception:
                    pass


def main() -> None:
    """Production main loop 700x800 Favur 2048 real board arrow input undo Escape 60 FPS screenshot.

    Returns:
        None. Enters event loop until QUIT or Escape, then exits via sys.exit(0).

    Raises:
        RuntimeError: If pygame.init fails or returns None.
        ImportError: If pygame-ce API verification fails.
    """
    verify_pygame_api()

    init_result = pygame.init()
    if init_result is None:
        raise RuntimeError("pygame.init() returned None, init failed")

    title = "Favur 2048"
    window_width = 700
    window_height = 800
    fps = 60

    screen = pygame.display.set_mode((window_width, window_height), flags=0)
    pygame.display.set_caption(title)

    clock = pygame.time.Clock()
    rng = random.Random()
    board = create_initial_board(rng)
    score = ScoreState()
    history = HistoryStack()
    achievements = Achievements()
    game_state = GameState()
    first_frame = True
    running = True

    draw_board_fn = None
    try:
        from src.render.tiles import draw_board as _draw_board

        draw_board_fn = _draw_board
    except ImportError:
        draw_board_fn = None

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break
                    direction: Optional[Direction] = None
                    if event.key == pygame.K_UP:
                        direction = Direction.UP
                    elif event.key == pygame.K_DOWN:
                        direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT:
                        direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT:
                        direction = Direction.RIGHT

                    if direction is not None:
                        if not is_legal_move(board.grid, direction):
                            continue
                        snapshot = HistorySnapshot(
                            grid=copy.deepcopy(board.grid),
                            score=score.current_score,
                            twist_state={},
                            move_number=game_state.move_count,
                            direction=direction,
                            game_state=copy.deepcopy(game_state),
                        )
                        history.push(snapshot)
                        slide_result = board.slide(direction, rng=rng)
                        score.add(slide_result.score_delta)
                        try:
                            vent_result = vent_heat(board.grid)
                            if isinstance(vent_result, tuple):
                                _, vent_occurred = vent_result
                            else:
                                vent_occurred = False
                        except Exception:
                            vent_occurred = False

                        try:
                            unstable_result = check_unstable(board.grid)
                            if isinstance(unstable_result, tuple):
                                _, unstable_present = unstable_result
                            else:
                                unstable_present = len(unstable_result) > 0
                        except Exception:
                            unstable_present = False

                        game_state.update_after_turn(vent_occurred, unstable_present)

                        context = GameContext(
                            board=board.grid,
                            score=score,
                            history=history,
                            twist={},
                            last_slide_result=slide_result,
                            move_count=game_state.move_count,
                            total_merges=len(slide_result.merges),
                            vent_streak=game_state.vent_streak,
                            unstable_survival=game_state.unstable_survival,
                            undo_count=game_state.undo_count,
                        )
                        try:
                            object.__setattr__(context, "game_state", game_state)
                        except Exception:
                            pass
                        achievements.evaluate(context)
                        continue

                    if event.key in (pygame.K_u, pygame.K_z):
                        if history.can_undo():
                            restored = history.undo()
                            if restored is not None:
                                new_grid = []
                                for r in range(5):
                                    row = []
                                    for c in range(5):
                                        cell = restored.grid[r][c]
                                        if cell is None:
                                            row.append(None)
                                        else:
                                            row.append(Tile(value=cell.value, heat=cell.heat))
                                    new_grid.append(row)
                                board.grid = new_grid
                                score.current_score = restored.score
                                gs_restored = getattr(restored, "game_state", None)
                                if gs_restored is not None:
                                    game_state = copy.deepcopy(gs_restored)
                                game_state.increment_undo()

            if not running:
                break

            if draw_board_fn is not None:
                try:
                    draw_board_fn(screen, board.grid, score.current_score)
                except Exception:
                    _draw_minimal_board(screen, board, score)
            else:
                _draw_minimal_board(screen, board, score)

            pygame.display.flip()
            clock.tick(fps)

            if first_frame:
                try:
                    visual_proof_dir = Path("visual-proof")
                    visual_proof_dir.mkdir(parents=True, exist_ok=True)
                    pygame.image.save(screen, str(visual_proof_dir / "phase-3-first-light.png"))
                except OSError as e:
                    print(f"Warning: Screenshot save failed: {e}", file=sys.stderr)
                first_frame = False

    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
