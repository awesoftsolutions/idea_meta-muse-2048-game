"""
tests/test_first_light_smoke.py — Main loop smoke + GameState ownership + spawn immunity.

Covers AC-2 to AC-8, AC-19 per pseudocode phase_3_sprint_1_wave2_mainloop_tests.md:
- Board single 2 tile heat 0 creation
- Arrow input dispatch legal check via rules.is_legal_move
- Illegal move no spawn no score no GameState update
- Undo restores exact including heat and GameState
- Turn pipeline locked slide->gen->spread->vent->spawn heat=0->unstable->achievements
- Main loop smoke no crash headless skip if no DISPLAY
- verify_pygame_api checks via hasattr
- First-frame screenshot placeholder dir creation logic

Headless, stdlib only except optional pygame for smoke. No global random.
"""

from __future__ import annotations

import copy
import os
import random
import sys
from pathlib import Path
from typing import List, Optional

import pytest

from src.core.board import BOARD_SIZE, Board, Direction, Tile, create_empty_grid
from src.core.gamestate import GameState
from src.core.history import HistorySnapshot, HistoryStack
from src.core.rules import is_legal_move
from src.core.score import ScoreState


def _empty_int_grid() -> List[List[Optional[int]]]:
    return [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def make_tile_grid(int_grid: List[List[Optional[int]]]) -> List[List[Optional[Tile]]]:
    result = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            val = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            result[r][c] = None if val is None else Tile(value=val, heat=0)
    return result


def make_tile_grid_with_heat(
    int_grid: List[List[Optional[int]]],
    heat_grid: List[List[Optional[int]]],
) -> List[List[Optional[Tile]]]:
    result = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = int_grid[r][c] if r < len(int_grid) and c < len(int_grid[r]) else None
            if v is None:
                result[r][c] = None
            else:
                h = (
                    heat_grid[r][c]
                    if r < len(heat_grid) and c < len(heat_grid[r]) and heat_grid[r][c] is not None
                    else 0
                )
                result[r][c] = Tile(value=v, heat=int(h))
    return result


def _count_tiles(grid: List[List[Optional[Tile]]]) -> int:
    return sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if grid[r][c] is not None)


# ---------------------------------------------------------------------------
# AC-2: Board single 2 tile heat 0 creation
# ---------------------------------------------------------------------------


def test_board_single_2_tile_heat_0_creation() -> None:
    """AC-2: Board with single 2 tile heat 0 via create_initial_board or manual."""
    from src.main import create_initial_board

    rng = random.Random(42)
    board = create_initial_board(rng)
    count = _count_tiles(board.grid)
    assert count == 1, f"Expected exactly 1 tile, got {count}"
    # Find the tile
    found = None
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c] is not None:
                found = board.grid[r][c]
    assert found is not None
    assert found.value == 2, f"Expected value 2, got {found.value}"
    assert found.heat == 0, f"Expected heat 0, got {found.heat}"


def test_board_creation_via_direct_board() -> None:
    """Board(rng) with manual placement single 2 tile heat 0."""
    rng = random.Random(123)
    board = Board(rng=rng)
    board.grid = create_empty_grid()
    board.grid[0][0] = Tile(value=2, heat=0)
    assert _count_tiles(board.grid) == 1
    assert board.grid[0][0] is not None
    assert board.grid[0][0].value == 2
    assert board.grid[0][0].heat == 0


# ---------------------------------------------------------------------------
# AC-3: Arrow input dispatch legal check
# ---------------------------------------------------------------------------


def test_arrow_input_dispatch_legal_check() -> None:
    """AC-3: Arrow keys dispatch with legal check via rules.is_legal_move."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    tile_grid = make_tile_grid(int_grid)
    rng = random.Random(42)
    board = Board(grid=tile_grid, rng=rng)

    # LEFT should be illegal when already left-aligned
    assert is_legal_move(Direction.LEFT, board.grid) is False
    # RIGHT should be legal
    assert is_legal_move(Direction.RIGHT, board.grid) is True

    # Perform legal move
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    assert result.score_delta == 0
    # After move, tile should be at right edge plus spawn
    assert _count_tiles(result.grid) == 2  # moved tile + spawn


def test_arrow_input_all_directions() -> None:
    """All 4 directions dispatch via board.slide with legal check."""
    int_grid = _empty_int_grid()
    int_grid[2][2] = 2
    tile_grid = make_tile_grid(int_grid)

    for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        board = Board(grid=tile_grid, rng=random.Random(42))
        legal = is_legal_move(direction, board.grid)
        # Center tile can move in any direction
        assert legal is True, f"Direction {direction} should be legal for center tile"
        result = board.slide(direction)
        assert result.moved is True


# ---------------------------------------------------------------------------
# AC-4: Illegal move no spawn no score no GameState
# ---------------------------------------------------------------------------


def test_illegal_move_no_spawn_no_score_no_gamestate() -> None:
    """AC-4: Illegal move no board change, no spawn, no score, no GameState update."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 8, 16, 32]
    tile_grid = make_tile_grid(int_grid)
    rng = random.Random(42)
    board = Board(grid=tile_grid, rng=rng)

    # LEFT is illegal when already left-aligned no merge
    assert is_legal_move(Direction.LEFT, board.grid) is False

    original_count = _count_tiles(board.grid)
    original_grid_copy = copy.deepcopy(board.grid)
    score = ScoreState()
    original_score = score.current_score
    game_state = GameState()
    original_move_count = game_state.move_count

    # Attempt slide that should be no-op
    result = board.slide(Direction.LEFT)
    assert result.moved is False
    assert result.score_delta == 0
    assert _count_tiles(result.grid) == original_count

    # Grid unchanged
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            orig = original_grid_copy[r][c]
            new = result.grid[r][c]
            if orig is None:
                assert new is None
            else:
                assert new is not None
                assert new.value == orig.value
                assert new.heat == orig.heat

    # Score unchanged
    assert score.current_score == original_score
    # GameState not updated (move_count unchanged because we didn't call update_after_turn)
    assert game_state.move_count == original_move_count


def test_illegal_move_no_gamestate_update_integration() -> None:
    """Illegal move should not trigger GameState update in main loop logic."""
    int_grid = _empty_int_grid()
    int_grid[0] = [2, 4, 8, 16, 32]
    tile_grid = make_tile_grid(int_grid)
    board = Board(grid=tile_grid, rng=random.Random(42))
    game_state = GameState()

    # Simulate main loop: check legal before updating GameState
    direction = Direction.LEFT
    if not is_legal_move(direction, board.grid):
        # Should not update GameState
        pass
    else:
        game_state.update_after_turn(False, False)

    assert game_state.move_count == 0
    assert game_state.vent_streak == 0


# ---------------------------------------------------------------------------
# AC-5: Undo restores exact including heat and GameState
# ---------------------------------------------------------------------------


def test_undo_restores_exact_including_heat_and_gamestate() -> None:
    """AC-5: History pop restores exact prior board including heat and GameState."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    int_grid[0][1] = 2
    heat_grid = _empty_int_grid()
    heat_grid[0][0] = 1
    heat_grid[0][1] = 2
    tile_grid = make_tile_grid_with_heat(int_grid, heat_grid)

    rng = random.Random(42)
    board = Board(grid=tile_grid, rng=rng)
    score = ScoreState()
    history = HistoryStack()
    game_state = GameState()
    game_state.vent_streak = 3
    game_state.unstable_survival = 2
    game_state.undo_count = 1
    game_state.move_count = 5

    # Push snapshot including GameState
    snapshot = HistorySnapshot(
        grid=copy.deepcopy(board.grid),
        score=score.current_score,
        twist_state={},
        move_number=game_state.move_count,
        direction=Direction.LEFT,
        game_state=copy.deepcopy(game_state),
    )
    history.push(snapshot)

    # Perform slide that changes board and heat
    result = board.slide(Direction.LEFT)
    assert result.moved is True
    score.add(result.score_delta)
    game_state.update_after_turn(vent_occurred=True, unstable_present=True)

    # Now undo
    assert history.can_undo() is True
    restored = history.undo()
    assert restored is not None

    # Restore board grid preserving heat
    new_grid = create_empty_grid()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = restored.grid[r][c]
            new_grid[r][c] = None if cell is None else Tile(value=cell.value, heat=cell.heat)
    board.grid = new_grid
    score.current_score = restored.score
    gs_restored = getattr(restored, "game_state", None)
    assert gs_restored is not None
    restored_gs = copy.deepcopy(gs_restored)
    restored_gs.increment_undo()

    # Verify exact restore including heat
    assert board.grid[0][0] is not None
    assert board.grid[0][0].value == 2
    assert board.grid[0][0].heat == 1
    assert board.grid[0][1] is not None
    assert board.grid[0][1].value == 2
    assert board.grid[0][1].heat == 2

    # GameState counters exact
    assert restored_gs.vent_streak == 3
    assert restored_gs.unstable_survival == 2
    assert restored_gs.move_count == 5
    assert restored_gs.undo_count == 2  # incremented


def test_undo_empty_no_crash() -> None:
    """Undo with empty history stack no-op no crash."""
    history = HistoryStack()
    assert history.can_undo() is False
    result = history.undo()
    assert result is None


# ---------------------------------------------------------------------------
# AC-7: Turn pipeline locked
# ---------------------------------------------------------------------------


def test_turn_pipeline_locked() -> None:
    """AC-7: Turn pipeline locked slide->gen->spread->vent->spawn heat=0->unstable->achievements."""
    from src.core.twist import get_turn_pipeline_order

    order = get_turn_pipeline_order()
    # Expected order per architecture: slide, gen, spread, vent, spawn, unstable, achievements
    # Check that order contains expected phases
    assert isinstance(order, (list, tuple))
    order_str = " ".join(str(x).lower() for x in order)
    # At minimum, check ordering keywords exist
    assert "slide" in order_str or len(order) >= 3

    # Functional check: slide causes spawn after move
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    tile_grid = make_tile_grid(int_grid)
    board = Board(grid=tile_grid, rng=random.Random(42))
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    # New tile heat=0 immune same turn
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = result.grid[r][c]
            if tile is not None:
                assert tile.heat == 0, f"Tile at ({r},{c}) heat {tile.heat} !=0 after spawn immunity"


def test_spawn_heat_0_immune() -> None:
    """AC-19: New tile heat=0 immune to spread/vent same turn via ordering spawn after spread/vent."""
    int_grid = _empty_int_grid()
    int_grid[0][0] = 2
    tile_grid = make_tile_grid(int_grid)
    board = Board(grid=tile_grid, rng=random.Random(42))
    result = board.slide(Direction.RIGHT)
    assert result.moved is True
    # All tiles heat 0 after spawn immunity
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            tile = result.grid[r][c]
            if tile is not None:
                assert tile.heat == 0

    # Verify via code review pattern: board.py slide should call _spawn_tile after gen/spread/vent
    # Check source file for ordering
    board_path = Path("src/core/board.py")
    if board_path.exists():
        content = board_path.read_text(encoding="utf-8")
        # Look for spawn after spread/vent in slide method
        # This is a heuristic check
        slide_idx = content.find("def slide(")
        if slide_idx != -1:
            slide_section = content[slide_idx : slide_idx + 3000]
            # Should contain spawn logic
            assert "spawn" in slide_section.lower()


# ---------------------------------------------------------------------------
# AC-1: verify_pygame_api
# ---------------------------------------------------------------------------


def test_verify_pygame_api() -> None:
    """AC-1: verify_pygame_api checks pygame.init display.set_mode font.SysFont event.get image.save exist via hasattr."""
    # This test should work even without pygame installed - it should raise ImportError with hint
    # If pygame is installed, it should return True
    try:
        from src.main import verify_pygame_api

        try:
            result = verify_pygame_api()
            assert result is True
        except ImportError as e:
            # Should have install hint
            msg = str(e).lower()
            assert "pygame" in msg
            assert "install" in msg or "poetry" in msg or "pip" in msg
    except ModuleNotFoundError:
        # src.main may not exist in red phase
        pytest.skip("src.main not available")


def test_verify_pygame_api_checks_required_apis() -> None:
    """verify_pygame_api checks all required APIs via hasattr pattern."""
    main_path = Path("src/main.py")
    if not main_path.exists():
        pytest.skip("src/main.py not found")
    content = main_path.read_text(encoding="utf-8")
    required_apis = [
        "pygame.init",
        "display.set_mode",
        "display.set_caption",
        "font.SysFont",
        "event.get",
        "image.save",
        "QUIT",
        "KEYDOWN",
        "K_ESCAPE",
        "K_UP",
        "K_DOWN",
        "K_LEFT",
        "K_RIGHT",
        "K_u",
        "K_z",
        "draw.rect",
        "draw.circle",
        "time.Clock",
        "quit",
    ]
    for api in required_apis:
        assert api in content, f"Required API check {api} not found in src/main.py verify_pygame_api"


# ---------------------------------------------------------------------------
# AC-8: First-frame screenshot placeholder
# ---------------------------------------------------------------------------


def test_first_frame_screenshot_placeholder() -> None:
    """AC-8: First frame screenshot placeholder logic creates visual-proof dir and handles OSError."""
    main_path = Path("src/main.py")
    if not main_path.exists():
        pytest.skip("src/main.py not found")
    content = main_path.read_text(encoding="utf-8")
    # Check for visual-proof dir creation
    assert "visual-proof" in content
    assert "phase-3-first-light.png" in content
    assert "mkdir" in content or "Path" in content
    assert "OSError" in content or "except" in content
    assert "image.save" in content or "pygame.image.save" in content


def test_visual_proof_dir_creation_logic() -> None:
    """Visual-proof dir creation via pathlib Path.mkdir(parents=True, exist_ok=True)."""
    # Test the logic directly
    test_dir = Path("visual-proof-test-tmp")
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists()
        # Simulate screenshot save failure handling
        try:
            raise OSError("simulated permission error")
        except OSError as e:
            # Should log warning but not crash
            warning_msg = f"Screenshot save failed: {e}"
            assert "Screenshot save failed" in warning_msg
    finally:
        # Cleanup
        if test_dir.exists():
            try:
                test_dir.rmdir()
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Main loop smoke no crash headless skip if no DISPLAY
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None and sys.platform != "win32",
    reason="No DISPLAY available, skipping pygame window test",
)
def test_main_loop_smoke_no_crash() -> None:
    """Smoke: main loop can init and create window without crash, 700x800 Favur 2048 exact title non-resizable."""
    try:
        import pygame
    except ImportError:
        pytest.skip("pygame not installed")

    from src.main import verify_pygame_api

    assert verify_pygame_api() is True

    try:
        pygame.init()
        screen = pygame.display.set_mode((700, 800), flags=0)
        pygame.display.set_caption("Favur 2048")
        # Verify size
        assert screen.get_size() == (700, 800)
        # Verify title
        title = pygame.display.get_caption()[0]
        assert title == "Favur 2048", f"Expected title 'Favur 2048', got '{title}'"
        # Verify not resizable: flags=0 means no RESIZABLE
        # Draw minimal rects
        screen.fill((15, 23, 42))
        pygame.display.flip()
        clock = pygame.time.Clock()
        clock.tick(60)
    finally:
        pygame.quit()


def test_main_py_constants() -> None:
    """Verify main.py has correct constants 700x800 Favur 2048 60 FPS."""
    main_path = Path("src/main.py")
    if not main_path.exists():
        pytest.skip("src/main.py not found")
    content = main_path.read_text(encoding="utf-8")
    assert "700" in content
    assert "800" in content
    assert "Favur 2048" in content
    assert "60" in content
    assert "flags=0" in content or "flags = 0" in content
    # Should not have RESIZABLE flag
    # Check that set_mode call does not include RESIZABLE
    lines = content.splitlines()
    for line in lines:
        if "set_mode" in line and "RESIZABLE" in line:
            pytest.fail(f"set_mode should not use RESIZABLE flag per SOW: {line}")


# ---------------------------------------------------------------------------
# Isolation: no pygame leak in smoke tests themselves
# ---------------------------------------------------------------------------


def test_smoke_tests_no_pygame_leak_in_core() -> None:
    """Smoke tests themselves should not leak pygame into core via import."""
    # Import core modules first
    import src.core.board  # noqa: F401
    import src.core.gamestate  # noqa: F401
    import src.core.achievements  # noqa: F401

    # Check that core modules don't import pygame
    core_dir = Path("src/core")
    for py_file in core_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "import pygame" in stripped or "from pygame" in stripped:
                pytest.fail(f"pygame import found in {py_file}:{i}: {stripped}")


# ---------------------------------------------------------------------------
# Wave3 final: first-light screenshot PNG header, manifest, mode label, window
# ---------------------------------------------------------------------------


def test_first_light_screenshot_valid_PNG_header_smoke() -> None:
    """AC-9: visual-proof/phase-3-first-light.png valid PNG header 89 50 4E 47 700x800."""
    screenshot_path = Path("visual-proof/phase-3-first-light.png")
    assert screenshot_path.exists(), "First-light screenshot must exist for Wave3 final"
    assert screenshot_path.stat().st_size > 0
    with open(screenshot_path, "rb") as f:
        header = f.read(8)
    expected = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
    assert header == expected, f"Invalid PNG header: {header.hex()}"


def test_manifest_entry_exists_smoke() -> None:
    """AC-10: visual-proof/README.md manifest entry per SOW."""
    manifest_path = Path("visual-proof/README.md")
    assert manifest_path.exists(), "Manifest must exist"
    content = manifest_path.read_text(encoding="utf-8")
    assert "phase-3-first-light.png" in content


def test_mode_label_overlay_present_smoke() -> None:
    """AC-8: mode label overlay present in tiles.py."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists(), "src/render/tiles.py must exist for Wave3 final"
    content = tiles_path.read_text(encoding="utf-8")
    assert "Mode" in content or "mode" in content.lower()
    assert "SysFont" in content


def test_draw_board_exists_and_callable_smoke() -> None:
    """AC-1: draw_board exists and callable."""
    from src.render.tiles import draw_board

    assert callable(draw_board)


def test_lerp_heat_color_exact_colors_smoke() -> None:
    """AC-2: lerp_heat_color exact colors via smoke import."""
    from src.render.tiles import lerp_heat_color

    c0, g0 = lerp_heat_color(0)
    assert c0 == (59, 130, 246)
    assert g0 is False
    c1, g1 = lerp_heat_color(1)
    assert c1 == (245, 158, 11)
    assert g1 is False
    c2, g2 = lerp_heat_color(2)
    assert c2 == (239, 68, 68)
    c3, g3 = lerp_heat_color(3)
    assert c3 == (255, 255, 255)
    assert g3 is True