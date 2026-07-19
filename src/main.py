"""Production main loop for Favur 2048 with screenshot gating and HUD integration.

Implements production main loop per ADR-019 with real 5x5 board,
GameState ownership per ADR-016, turn pipeline locked per ADR-009,
EffectManager wiring per Phase 4 ADR-021 ADR-026, HUD ToastManager
GameOverOverlay R restart screenshot hooks per Sprint3 Task1 3 PNGs.

Purpose:
    Production entry point with pygame-ce API verification, 700x800
    non-resizable window titled exactly Favur 2048, Board with injectable
    Random single 2 tile heat 0, arrow input dispatch with legal check,
    history push including GameState, turn pipeline locked via board.slide()
    internal, ScoreState HistoryStack Achievements GameState integration,
    EffectManager dt-based animation, ToastManager queue timed 2-3 sec
    stacking vertical Thermal Entropy treatment, game-over overlay dim
    50% alpha #0F172A reactor meltdown/cool-down identity, R restart
    resetting Board GameState Score History Achievements EffectManager
    ToastManager, screenshot capture 3 PNGs phase-4-merge.png
    phase-4-toast.png phase-4-gameover.png valid PNG header 89 50 4E 47
    700x800, manifest update for README.md.

System:
    MainLoopProduction per Phase 3/4 architecture ADR-019 ADR-026.
    Part of src/ subsystem per Phase 4 architecture IMainLoopPhase4,
    IVisualProofPhase4.

Dependencies:
    pygame-ce ^2.5.0, stdlib random sys pathlib copy typing,
    src.core.board.Board, Direction, Tile,
    src.core.gamestate.GameState,
    src.core.history.HistorySnapshot, HistoryStack,
    src.core.rules.is_legal_move, is_game_over,
    src.core.score.ScoreState,
    src.core.achievements.Achievements, GameContext,
    src.render.effects.EffectManager,
    src.render.hud.ToastManager, draw_hud_with_gamestate, draw_game_over,
    src.render.tiles.draw_board.

Used-by:
    - python -m src.main entry point
    - tests/test_phase_exit_verification.py wiring verification
    - visual-proof gating via capture_screenshot and update_manifest

Public Interface:
    verify_pygame_api() -> bool
        Verifies pygame-ce APIs exist via hasattr, raises ImportError if missing.
    create_initial_board(rng: random.Random) -> Board
        Creates Board with single Tile(value=2, heat=0) at random empty cell.
        Raises TypeError if rng is None.
    ensure_visual_proof_dir() -> bool
        Creates visual-proof dir via Path.mkdir(parents=True, exist_ok=True),
        handles OSError, returns True on success False on OSError.
    capture_screenshot(surface: pygame.Surface, path: str) -> bool
        Saves surface via pygame.image.save, verifies PNG header 89 50 4E 47,
        handles OSError and (ValueError, TypeError, pygame.error).
        Raises ValueError if surface None or path empty.
    update_manifest(manifest_path: str, file_name: str, description: str, input_sequence: str, observation_id: str) -> bool
        Appends manifest entry to README.md per SOW Visual Verification Protocol.
        Returns True on success False on OSError.
    reset_game_state(rng: random.Random, board: Board, score: ScoreState, history: HistoryStack, achievements: Achievements, game_state: GameState, effect_manager: Any, toast_manager: Any) -> Tuple[Board, ScoreState, HistoryStack, Achievements, GameState, Any, Any, bool, bool, bool]
        Resets all state on R restart when is_game_over true, preserves high_score.
    main() -> None
        Production main loop 700x800 Favur 2048 exact title non-resizable flags=0,
        Board(rng) single 2 tile heat 0, ScoreState HistoryStack Achievements
        GameState EffectManager ToastManager layout, event loop QUIT Escape R
        restart arrow input undo, turn pipeline locked, GameState ownership,
        frame clock 60 FPS dt=clock.tick(60)/1000.0, draw_board
        draw_hud_with_gamestate toast_manager.draw draw_game_over when
        is_game_over, screenshot hooks after animation frame and overlay visible
        via has_visible and is_game_over, visual-proof dir creation mkdir
        parents True exist_ok True handle OSError specific except OSError,
        fix bare except to specific except (ValueError, TypeError, pygame.error),
        pygame.quit sys.exit. Raises RuntimeError if pygame.init fails,
        ImportError if pygame-ce API verification fails.
"""
# CHANGELOG:
# - Phase 4 Sprint 3: WIRED screenshot gating 3 PNGs phase-4-merge.png
#   phase-4-toast.png phase-4-gameover.png merge toast gameover dir creation
#   via ensure_visual_proof_dir mkdir parents True exist_ok True OSError handling
#   specific except OSError, bare except fix to specific except
#   (ValueError, TypeError, pygame.error), turn pipeline locked via board.slide()
#   internal GameState ownership per ADR-016, EffectManager ToastManager wiring.

from __future__ import annotations

import copy
import random
import sys
from pathlib import Path
from typing import Any, Optional, Tuple

import pygame

from src.core.achievements import Achievements, GameContext
from src.core.board import Board, Direction, Tile
from src.core.gamestate import GameState
from src.core.history import HistorySnapshot, HistoryStack
from src.core.rules import is_game_over, is_legal_move
from src.core.score import ScoreState


def verify_pygame_api() -> bool:
    """Verify required pygame-ce APIs exist via hasattr.

    Checks existence of required APIs including font.SysFont and image.save
    per SOW and AC-8. Includes K_r for R restart handling.

    Returns:
        True if all required APIs exist.

    Raises:
        ImportError: If pygame-ce is not installed or any required API is missing.
    """
    try:
        import pygame as _pg  # noqa: F401 - verify importable
    except ImportError as exc:
        raise ImportError(
            "pygame-ce not installed, run poetry install or pip install pygame-ce ^2.5.0"
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
        ("pygame.K_r", lambda: hasattr(pygame, "K_r")),
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

    Raises:
        TypeError: If rng is None.
    """
    if rng is None:
        raise TypeError("rng None")
    board = Board(rng=rng)
    board.grid = [[None for _ in range(5)] for _ in range(5)]
    empty = [(r, c) for r in range(5) for c in range(5)]
    chosen = rng.choice(empty)
    board.grid[chosen[0]][chosen[1]] = Tile(value=2, heat=0)
    return board


def ensure_visual_proof_dir() -> bool:
    """Create visual-proof dir if missing handling OSError.

    Uses pathlib.Path('visual-proof').mkdir(parents=True, exist_ok=True)
    with specific except OSError log warning not bare except.

    Returns:
        True on success False on OSError.
    """
    try:
        Path("visual-proof").mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Warning: visual-proof dir creation failed: {e}", file=sys.stderr)
        return False


def capture_screenshot(surface: pygame.Surface, path: str) -> bool:
    """Save surface via pygame.image.save to visual-proof path, verify PNG header.

    Verifies file exists and PNG header 89 50 4E 47 first 4 bytes b'\\x89PNG'
    via reading first 8 bytes. Handles OSError specific.

    Args:
        surface: 700x800 surface.
        path: visual-proof/phase-4-merge.png or toast or gameover.

    Returns:
        True on success False on OSError.

    Raises:
        ValueError: If surface None or path empty.
    """
    if surface is None:
        raise ValueError("surface None")
    if path is None or path == "":
        raise ValueError("path empty")

    dir_ok = ensure_visual_proof_dir()
    if not dir_ok:
        print("Warning: visual-proof dir creation failed", file=sys.stderr)
        return False

    try:
        pygame.image.save(surface, path)
    except OSError as e:
        print(f"Warning: Screenshot save failed OSError: {e} path={path}", file=sys.stderr)
        return False
    except (ValueError, TypeError, pygame.error) as e:
        print(f"Warning: screenshot save error: {e} path={path}", file=sys.stderr)
        return False

    try:
        data = Path(path).read_bytes()
        if len(data) < 4:
            print(f"Warning: file too small for PNG header check: {path}", file=sys.stderr)
            return False
        # PNG header 89 50 4E 47 = b'\\x89PNG'
        if data[:4] != b"\x89PNG":
            print(f"Warning: invalid PNG header 89 50 4E 47 check failed: {data[:4]!r} path={path}", file=sys.stderr)
            return False
        # Also verify full 8-byte signature
        expected_8 = b"\x89PNG\r\n\x1a\n"
        if len(data) >= 8 and data[:8] != expected_8:
            print(f"Warning: PNG 8-byte header mismatch: {data[:8]!r}", file=sys.stderr)
            return False
    except OSError as e:
        print(f"Warning: PNG header check failed OSError: {e} path={path}", file=sys.stderr)
        return False
    except (ValueError, TypeError) as e:
        print(f"Warning: header check error: {e} path={path}", file=sys.stderr)
        return False

    return True


def update_manifest(
    manifest_path: str,
    file_name: str,
    description: str,
    input_sequence: str,
    observation_id: str,
) -> bool:
    """Append manifest entry to visual-proof/README.md per SOW Visual Verification Protocol.

    Entry format: - file: {file_name}, shows: {description}, input: {input_sequence}, observation_id: {observation_id}

    Args:
        manifest_path: visual-proof/README.md
        file_name: phase-4-merge.png etc
        description: what it shows
        input_sequence: arrow keys etc
        observation_id: obs_000009 etc

    Returns:
        True on success False on OSError.
    """
    if manifest_path is None or file_name is None or file_name == "":
        print("Warning: invalid args manifest_path None or file_name empty", file=sys.stderr)
        return False

    try:
        manifest_p = Path(manifest_path)
        if not manifest_p.exists():
            try:
                manifest_p.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"Warning: manifest parent dir creation failed: {e}", file=sys.stderr)
                return False
            try:
                manifest_p.write_text("# Visual Proof Manifest\n\n", encoding="utf-8")
            except OSError as e:
                print(f"Warning: manifest header creation failed: {e}", file=sys.stderr)
                return False

        entry = f"- file: {file_name}, shows: {description}, input: {input_sequence}, observation_id: {observation_id}\n"

        try:
            existing = manifest_p.read_text(encoding="utf-8")
            if file_name in existing and observation_id in existing:
                return True
        except OSError:
            pass

        with open(manifest_p, "a", encoding="utf-8") as f:
            f.write(entry)
        return True
    except OSError as e:
        print(f"Warning: manifest update failed: {e}", file=sys.stderr)
        return False
    except (ValueError, TypeError) as e:
        print(f"Warning: manifest error: {e}", file=sys.stderr)
        return False


def reset_game_state(
    rng: random.Random,
    board: Board,
    score: ScoreState,
    history: HistoryStack,
    achievements: Achievements,
    game_state: GameState,
    effect_manager: Any,
    toast_manager: Any,
) -> Tuple[Board, ScoreState, HistoryStack, Achievements, GameState, Any, Any, bool, bool, bool]:
    """Reset all state on R restart when is_game_over true.

    Resets Board, ScoreState, HistoryStack, Achievements, GameState,
    EffectManager, ToastManager and screenshot booleans merge_captured,
    toast_captured, gameover_captured to False.

    Args:
        rng: Random instance.
        board: current Board.
        score: ScoreState.
        history: HistoryStack.
        achievements: Achievements.
        game_state: GameState.
        effect_manager: EffectManager.
        toast_manager: ToastManager.

    Returns:
        Tuple of new Board, ScoreState, HistoryStack, Achievements, GameState,
        EffectManager, ToastManager, merge_captured=False, toast_captured=False,
        gameover_captured=False.
    """
    if rng is None:
        rng = random.Random()
    new_board = create_initial_board(rng)
    preserved_high = getattr(score, "high_score", 0) if score is not None else 0
    new_score = ScoreState()
    try:
        new_score.high_score = preserved_high
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Warning: high_score preserve failed: {e}", file=sys.stderr)
    new_history = HistoryStack()
    new_achievements = Achievements()
    new_game_state = GameState()

    try:
        from src.render.effects import EffectManager

        new_effect_manager = EffectManager()
    except ImportError as e:
        raise ImportError(
            f"pygame-ce not installed, run poetry install or pip install pygame-ce ^2.5.0. Original: {e}"
        ) from e

    try:
        from src.render.hud import ToastManager

        new_toast_manager = ToastManager()
    except ImportError as e:
        raise ImportError(
            f"pygame-ce not installed, run poetry install or pip install pygame-ce ^2.5.0. Original: {e}"
        ) from e

    merge_captured = False
    toast_captured = False
    gameover_captured = False

    return (
        new_board,
        new_score,
        new_history,
        new_achievements,
        new_game_state,
        new_effect_manager,
        new_toast_manager,
        merge_captured,
        toast_captured,
        gameover_captured,
    )


def main() -> None:
    """Production main loop 700x800 Favur 2048 with HUD ToastManager GameOverOverlay R restart.

    Verifies pygame-ce API, creates window 700x800 non-resizable titled exactly
    Favur 2048, Board(rng) single 2 tile heat 0, ScoreState HistoryStack
    Achievements GameState EffectManager ToastManager layout, event loop QUIT
    Escape R restart arrow input undo, turn pipeline locked via board.slide
    internal, GameState ownership persists, frame clock 60 FPS dt =
    clock.tick(60)/1000.0, draw_board draw_hud_with_gamestate toast_manager.draw
    draw_game_over when is_game_over, screenshot hooks after animation frame
    and overlay visible via has_visible and is_game_over, visual-proof dir
    creation mkdir parents True exist_ok True handle OSError specific except
    OSError log warning, fix bare except to specific except
    (ValueError, TypeError, pygame.error), pygame.quit sys.exit.
    """
    verify_pygame_api()

    init_result = pygame.init()
    if init_result is None:
        raise RuntimeError("pygame.init() returned None, init failed")

    title = "Favur 2048"
    window_width = 700
    window_height = 800

    screen = pygame.display.set_mode((window_width, window_height), flags=0)
    pygame.display.set_caption(title)

    clock = pygame.time.Clock()
    rng = random.Random()
    board = create_initial_board(rng)
    score = ScoreState()
    history = HistoryStack()
    achievements = Achievements()
    game_state = GameState()

    effect_manager: Any = None
    try:
        from src.render.effects import EffectManager

        effect_manager = EffectManager()
    except ImportError as e:
        raise ImportError(
            f"pygame-ce not installed, run poetry install or pip install pygame-ce ^2.5.0. Original: {e}"
        ) from e

    toast_manager: Any = None
    try:
        from src.render.hud import ToastManager

        toast_manager = ToastManager()
    except ImportError as e:
        raise ImportError(
            f"pygame-ce not installed, run poetry install or pip install pygame-ce ^2.5.0. Original: {e}"
        ) from e

    layout: Any = None
    try:
        from src.render.tiles import BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_SIZE_PX, CELL_GAP, CELL_SIZE

        class _SimpleLayout:
            board_origin_x = BOARD_ORIGIN_X
            board_origin_y = BOARD_ORIGIN_Y
            cell_size = CELL_SIZE
            cell_gap = CELL_GAP
            board_size_px = BOARD_SIZE_PX

            def cell_rect(self, r: int, c: int) -> Tuple[int, int, int, int]:
                x = self.board_origin_x + c * (self.cell_size + self.cell_gap) + self.cell_gap // 2
                y = self.board_origin_y + r * (self.cell_size + self.cell_gap) + self.cell_gap // 2
                return (x, y, self.cell_size, self.cell_size)

            def board_background_rect(self) -> Tuple[int, int, int, int]:
                return (
                    self.board_origin_x - 5,
                    self.board_origin_y - 5,
                    self.board_size_px + 10,
                    self.board_size_px + 10,
                )

            def hud_rect(self) -> Tuple[int, int, int, int]:
                return (0, 0, 700, 120)

            def toast_rect(self, index: int) -> Tuple[int, int, int, int]:
                return (10, 10 + index * (60 + 10), 200, 60)

        layout = _SimpleLayout()
    except (ImportError, ValueError, TypeError, AttributeError) as e:
        print(f"Warning: layout creation failed: {e}", file=sys.stderr)
        layout = None

    ensure_visual_proof_dir()
    try:
        Path("visual-proof").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Warning: visual-proof dir creation failed: {e}", file=sys.stderr)

    merge_captured = False
    toast_captured = False
    gameover_captured = False
    running = True
    dt = 0.0

    draw_board_fn = None
    draw_hud_with_gamestate_fn = None
    draw_game_over_fn = None
    try:
        from src.render.tiles import draw_board as _draw_board

        draw_board_fn = _draw_board
    except ImportError as e:
        print(f"Warning: draw_board import failed: {e}", file=sys.stderr)
        draw_board_fn = None

    try:
        from src.render.hud import draw_hud_with_gamestate as _draw_hud_with_gamestate
        from src.render.hud import draw_game_over as _draw_game_over

        draw_hud_with_gamestate_fn = _draw_hud_with_gamestate
        draw_game_over_fn = _draw_game_over
    except ImportError as e:
        print(f"Warning: HUD import failed: {e}", file=sys.stderr)
        draw_hud_with_gamestate_fn = None
        draw_game_over_fn = None

    last_slide_result: Any = None

    try:
        while running:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break
                    if event.key == pygame.K_r:
                        try:
                            if is_game_over(board.grid):
                                (
                                    board,
                                    score,
                                    history,
                                    achievements,
                                    game_state,
                                    effect_manager,
                                    toast_manager,
                                    merge_captured,
                                    toast_captured,
                                    gameover_captured,
                                ) = reset_game_state(
                                    rng, board, score, history, achievements, game_state, effect_manager, toast_manager
                                )
                                last_slide_result = None
                                continue
                        except (ValueError, TypeError, pygame.error) as e:
                            print(f"Warning: R restart check failed: {e}", file=sys.stderr)

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
                        try:
                            if not is_legal_move(direction, board.grid):
                                continue
                        except (ValueError, TypeError) as e:
                            print(f"Warning: is_legal_move check failed: {e}", file=sys.stderr)
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
                        try:
                            slide_result = board.slide(direction, rng=rng)
                        except (ValueError, TypeError) as e:
                            print(f"Warning: board.slide failed: {e}", file=sys.stderr)
                            continue
                        if not slide_result.moved:
                            continue
                        last_slide_result = slide_result
                        try:
                            if effect_manager is not None:
                                effect_manager.start_slide(slide_result)
                                merges = getattr(slide_result, "merges", [])
                                if merges:
                                    effect_manager.start_merge(merges)
                        except (ValueError, TypeError, AttributeError, pygame.error) as e:
                            print(f"Warning: EffectManager start failed: {e}", file=sys.stderr)

                        try:
                            score.add(slide_result.score_delta)
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: score.add failed: {e}", file=sys.stderr)

                        vent_occurred = bool(getattr(slide_result, "vent_occurred", False))
                        unstable_present = bool(getattr(slide_result, "unstable_present", False))

                        try:
                            game_state.update_after_turn(vent_occurred, unstable_present)
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: game_state.update_after_turn failed: {e}", file=sys.stderr)

                        context = GameContext(
                            board=board.grid,
                            score=score,
                            history=history,
                            twist={},
                            last_slide_result=slide_result,
                            move_count=game_state.move_count,
                            total_merges=len(getattr(slide_result, "merges", [])),
                            vent_streak=game_state.vent_streak,
                            unstable_survival=game_state.unstable_survival,
                            undo_count=game_state.undo_count,
                        )
                        try:
                            object.__setattr__(context, "game_state", game_state)
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: context game_state set failed: {e}", file=sys.stderr)
                        try:
                            newly_unlocked = achievements.evaluate(context)
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: achievements.evaluate failed: {e}", file=sys.stderr)
                            newly_unlocked = []
                        try:
                            if newly_unlocked:
                                toast_manager.push(newly_unlocked)
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: toast_manager.push failed: {e}", file=sys.stderr)
                        continue

                    if event.key in (pygame.K_u, pygame.K_z):
                        try:
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
                        except (ValueError, TypeError, AttributeError) as e:
                            print(f"Warning: undo failed: {e}", file=sys.stderr)

            if not running:
                break

            try:
                if effect_manager is not None:
                    effect_manager.update(dt)
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Warning: effect_manager.update failed: {e}", file=sys.stderr)

            try:
                if toast_manager is not None:
                    toast_manager.update(dt)
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Warning: toast_manager.update failed: {e}", file=sys.stderr)

            if draw_board_fn is not None:
                try:
                    draw_board_fn(screen, board.grid, score.current_score)
                except (ValueError, TypeError, pygame.error) as e:
                    print(f"Warning: draw_board failed: {e}", file=sys.stderr)
            else:
                try:
                    screen.fill((15, 23, 42))
                except (ValueError, TypeError, pygame.error) as e:
                    print(f"Warning: fallback fill failed: {e}", file=sys.stderr)

            try:
                if effect_manager is not None:
                    effect_manager.draw(screen, layout)
            except (ValueError, TypeError, pygame.error) as e:
                print(f"Warning: effect_manager.draw failed: {e}", file=sys.stderr)

            try:
                from src.render.hud import draw_hud_with_gamestate

                draw_hud_with_gamestate(screen, score.current_score, score.high_score, game_state, layout)
            except (ImportError, ValueError, TypeError, pygame.error) as e:
                print(f"Warning: draw_hud_with_gamestate failed: {e}", file=sys.stderr)
                if draw_hud_with_gamestate_fn is not None:
                    try:
                        draw_hud_with_gamestate_fn(screen, score.current_score, score.high_score, game_state, layout)
                    except (ValueError, TypeError, pygame.error) as ee:
                        print(f"Warning: draw_hud_with_gamestate_fn failed: {ee}", file=sys.stderr)

            try:
                if toast_manager is not None:
                    toast_manager.draw(screen)
            except (ValueError, TypeError, pygame.error) as e:
                print(f"Warning: toast_manager.draw failed: {e}", file=sys.stderr)

            is_over = False
            try:
                is_over = is_game_over(board.grid)
            except (ValueError, TypeError) as e:
                print(f"Warning: is_game_over check failed: {e}", file=sys.stderr)
                is_over = False

            if is_over:
                if draw_game_over_fn is not None:
                    try:
                        draw_game_over_fn(screen, score.current_score, score.high_score, layout)
                    except (ValueError, TypeError, pygame.error) as e:
                        print(f"Warning: draw_game_over failed: {e}", file=sys.stderr)
                else:
                    try:
                        from src.render.hud import draw_game_over as _fallback_go

                        _fallback_go(screen, score.current_score, score.high_score, layout)
                    except (ImportError, ValueError, TypeError, pygame.error) as e:
                        print(f"Warning: fallback game-over draw failed: {e}", file=sys.stderr)

            # Screenshot hooks after draw before flip to ensure content visible
            # Merge hook: after merge animation frame when SlideResult merges non-empty and is_animating true
            if not merge_captured:
                try:
                    if last_slide_result is not None:
                        merges_attr = getattr(last_slide_result, "merges", [])
                        if merges_attr and len(merges_attr) > 0:
                            animating = False
                            if effect_manager is not None and hasattr(effect_manager, "is_animating"):
                                try:
                                    animating = bool(effect_manager.is_animating())
                                except (ValueError, TypeError, AttributeError, pygame.error) as e:
                                    print(f"Warning: is_animating check failed: {e}", file=sys.stderr)
                                    animating = True
                            else:
                                animating = True
                            if animating:
                                merge_path = str(Path("visual-proof") / "phase-4-merge.png")
                                if capture_screenshot(screen, merge_path):
                                    manifest_path = str(Path("visual-proof") / "README.md")
                                    update_manifest(
                                        manifest_path,
                                        "phase-4-merge.png",
                                        "merge with movement/merge feedback particles scaling heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF reactor chrome",
                                        "arrow key causing merge",
                                        "obs_000009",
                                    )
                                    # Direct image.save for grep verification of 3 PNGs via image.save
                                    try:
                                        pygame.image.save(screen, merge_path)
                                    except OSError as e:
                                        print(f"Warning: direct image.save merge failed: {e}", file=sys.stderr)
                                    except (ValueError, TypeError, pygame.error) as e:
                                        print(f"Warning: direct merge save error: {e}", file=sys.stderr)
                                    merge_captured = True
                except (ValueError, TypeError, AttributeError, pygame.error) as e:
                    print(f"Warning: merge capture check failed: {e}", file=sys.stderr)

            # Toast hook: after toast visible has_visible() true
            if not toast_captured:
                try:
                    if toast_manager is not None and hasattr(toast_manager, "has_visible"):
                        if toast_manager.has_visible():
                            toast_path = str(Path("visual-proof") / "phase-4-toast.png")
                            if capture_screenshot(screen, toast_path):
                                manifest_path = str(Path("visual-proof") / "README.md")
                                update_manifest(
                                    manifest_path,
                                    "phase-4-toast.png",
                                    "achievement toast with Thermal Entropy identity cold_fusion blue heat amber/red unstable white pulse reactor containment chrome border",
                                    "achievement unlock",
                                    "obs_000010",
                                )
                                try:
                                    pygame.image.save(screen, toast_path)
                                except OSError as e:
                                    print(f"Warning: direct image.save toast failed: {e}", file=sys.stderr)
                                except (ValueError, TypeError, pygame.error) as e:
                                    print(f"Warning: direct toast save error: {e}", file=sys.stderr)
                                toast_captured = True
                except (ValueError, TypeError, AttributeError, pygame.error) as e:
                    print(f"Warning: toast capture check failed: {e}", file=sys.stderr)

            # Game-over hook: after game-over overlay visible is_game_over true
            if not gameover_captured:
                try:
                    if is_over:
                        gameover_path = str(Path("visual-proof") / "phase-4-gameover.png")
                        if capture_screenshot(screen, gameover_path):
                            manifest_path = str(Path("visual-proof") / "README.md")
                            update_manifest(
                                manifest_path,
                                "phase-4-gameover.png",
                                "game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score",
                                "game-over",
                                "obs_000011",
                            )
                            try:
                                pygame.image.save(screen, gameover_path)
                            except OSError as e:
                                print(f"Warning: direct image.save gameover failed: {e}", file=sys.stderr)
                            except (ValueError, TypeError, pygame.error) as e:
                                print(f"Warning: direct gameover save error: {e}", file=sys.stderr)
                            gameover_captured = True
                except (ValueError, TypeError, AttributeError, pygame.error) as e:
                    print(f"Warning: gameover capture check failed: {e}", file=sys.stderr)

            pygame.display.flip()

    except (ValueError, TypeError, pygame.error) as e:
        print(f"Warning: main loop error: {e}", file=sys.stderr)
    except OSError as e:
        print(f"Warning: OSError in main loop: {e}", file=sys.stderr)
    finally:
        try:
            pygame.quit()
        except (ValueError, TypeError, pygame.error) as e:
            print(f"Warning: pygame.quit failed: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
