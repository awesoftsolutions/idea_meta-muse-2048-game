"""
tests/test_main_first_light.py — main.py first-light screenshot gating content checks.

TDD red phase (Step 2 of 7): validates src/main.py contains 700x800 Favur 2048
exact title, Board import, Random, arrow keys, Escape, draw_board call,
pygame.image.save, GameState, mkdir parents True exist_ok True per pseudocode
phase_3_sprint_2_task_3_code.md Task 3 AC-3 AC-4.

Pseudocode sections covered:
- File: src/main.py first-frame screenshot capture — pygame.image.save after first frame
- File: Headless fallback Surface 700x800 draw_board capture — real board single 2 tile heat 0
- File: Visual launch via execute_structured_command and window_observe — observation_id
- File: visual-proof directory setup — mkdir parents True exist_ok True OSError handling

System:
    MainLoopProduction per Phase 3 architecture ADR-019.
    Headless content checks only, no pygame init, no GUI launch.
"""

from __future__ import annotations

import pathlib

MAIN_PY_PATH = pathlib.Path("src/main.py")
TILES_PY_PATH = pathlib.Path("src/render/tiles.py")


def _read_main() -> str:
    assert MAIN_PY_PATH.exists(), f"main.py not found at {MAIN_PY_PATH}"
    return MAIN_PY_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-3 AC-4: main.py contains 700x800 Favur 2048 exact title
# ---------------------------------------------------------------------------


def test_main_contains_700_800() -> None:
    """AC-3 AC-4: main.py contains 700 800 per File: src/main.py first-frame screenshot capture."""
    content = _read_main()
    assert "700" in content, "main.py missing 700 width per AC-3"
    assert "800" in content, "main.py missing 800 height per AC-3"


def test_main_contains_favur_2048_exact_title() -> None:
    """AC-3: main.py contains exact title Favur 2048 via set_caption per ADR-019."""
    content = _read_main()
    assert "Favur 2048" in content, "main.py missing exact title Favur 2048 per AC-3"
    # Must have set_caption exact
    assert "set_caption" in content, "main.py missing set_caption per AC-3 exact title requirement"


def test_main_contains_set_mode_flags_0_no_resizable() -> None:
    """AC-3: main.py contains set_mode 700x800 flags=0 no RESIZABLE per ADR-019."""
    content = _read_main()
    assert "set_mode" in content, "main.py missing set_mode per AC-3"
    assert "flags=0" in content or "flags = 0" in content, (
        "main.py missing set_mode flags=0 non-resizable per AC-3 — must be flags=0 no RESIZABLE"
    )
    # Ensure no RESIZABLE flag used
    # Allow RESIZABLE in comments but not in set_mode call line
    for line in content.splitlines():
        if "set_mode" in line and "RESIZABLE" in line:
            assert False, f"main.py set_mode line contains RESIZABLE flag per AC-3 must be non-resizable: {line}"


def test_main_contains_board_import() -> None:
    """AC-3: main.py contains Board import per Existing References Verified."""
    content = _read_main()
    assert "Board" in content, "main.py missing Board import per AC-3"
    assert "from src.core.board import" in content or "import Board" in content, (
        "main.py missing Board import from src.core.board per AC-3"
    )


def test_main_contains_tile_import() -> None:
    """AC-3: main.py contains Tile import for single 2 tile heat 0."""
    content = _read_main()
    assert "Tile" in content, "main.py missing Tile import per AC-3 real board single 2 tile heat 0"


def test_main_contains_random_import() -> None:
    """AC-3: main.py contains random.Random injectable per ADR-019."""
    content = _read_main()
    assert "random" in content, "main.py missing random import per AC-3 injectable RNG"
    assert "Random" in content, "main.py missing Random per AC-3 injectable RNG"


def test_main_contains_create_initial_board_single_2_tile_heat_0() -> None:
    """AC-3 AC-4: main.py contains create_initial_board single 2 tile heat 0 per pseudocode."""
    content = _read_main()
    assert "create_initial_board" in content, "main.py missing create_initial_board per AC-4"
    # Check for Tile(value=2, heat=0) pattern
    has_single_2_tile = (
        "Tile(value=2" in content
        or "Tile(2" in content
        or "value=2" in content and "heat=0" in content
    )
    assert has_single_2_tile, "main.py missing single 2 tile heat 0 creation per AC-3 AC-4"


def test_main_contains_arrow_keys() -> None:
    """AC-3: main.py contains arrow keys K_UP K_DOWN K_LEFT K_RIGHT per IMainLoop."""
    content = _read_main()
    assert "K_UP" in content, "main.py missing K_UP per AC-3 arrow keys move tiles"
    assert "K_DOWN" in content, "main.py missing K_DOWN per AC-3"
    assert "K_LEFT" in content, "main.py missing K_LEFT per AC-3"
    assert "K_RIGHT" in content, "main.py missing K_RIGHT per AC-3"


def test_main_contains_escape() -> None:
    """AC-3: main.py contains Escape-to-quit K_ESCAPE per IMainLoop."""
    content = _read_main()
    assert "K_ESCAPE" in content or "K_ESCAPE" in content, "main.py missing K_ESCAPE per AC-3 Escape-to-quit"
    assert "ESCAPE" in content, "main.py missing ESCAPE handling per AC-3"


def test_main_contains_draw_board_call() -> None:
    """AC-3 AC-4: main.py contains draw_board call each frame per ADR-018."""
    content = _read_main()
    assert "draw_board" in content, "main.py missing draw_board call per AC-3 AC-4"
    # Should call with screen, board.grid, score — may be via alias draw_board_fn
    has_draw_call = (
        "draw_board(" in content
        or "draw_board_fn(" in content
        or "_draw_board(" in content
    )
    assert has_draw_call, "main.py missing draw_board() call per AC-3"


def test_main_contains_pygame_image_save() -> None:
    """AC-4: main.py contains pygame.image.save for screenshot capture per File: src/main.py first-frame screenshot capture."""
    content = _read_main()
    assert "pygame.image.save" in content or "image.save" in content, (
        "main.py missing pygame.image.save per AC-4 first-frame screenshot capture"
    )
    assert "phase-3-first-light.png" in content, (
        "main.py missing phase-3-first-light.png path per AC-4 screenshot capture"
    )


def test_main_contains_first_frame_logic() -> None:
    """AC-4: main.py contains first_frame flag for first-frame capture per pseudocode."""
    content = _read_main()
    assert "first_frame" in content, "main.py missing first_frame flag per AC-4 first-frame screenshot capture"


def test_main_contains_gamestate() -> None:
    """AC-3: main.py contains GameState ownership per ADR-016 Q-005."""
    content = _read_main()
    assert "GameState" in content, "main.py missing GameState per AC-3 Q-005 ownership"
    assert "game_state" in content.lower() or "GameState" in content, (
        "main.py missing game_state variable per AC-3"
    )


def test_main_contains_mkdir_parents_exist_ok() -> None:
    """AC-4: main.py contains mkdir parents True exist_ok True per File: visual-proof directory setup."""
    content = _read_main()
    assert "mkdir" in content, "main.py missing mkdir per AC-4 directory creation"
    assert "parents=True" in content or "parents = True" in content, (
        "main.py missing parents=True per AC-4"
    )
    assert "exist_ok=True" in content or "exist_ok = True" in content, (
        "main.py missing exist_ok=True per AC-4"
    )


def test_main_contains_oserror_handling() -> None:
    """AC-4: main.py contains OSError handling for mkdir and image.save per pseudocode."""
    content = _read_main()
    assert "OSError" in content, "main.py missing OSError handling per AC-4"
    # Warning logged
    assert "Warning" in content or "warning" in content.lower() or "Screenshot" in content, (
        "main.py missing warning log for OSError per AC-4"
    )


def test_main_contains_clock_tick_60() -> None:
    """AC-3: main.py contains clock.tick 60 FPS per ADR-019."""
    content = _read_main()
    assert "Clock" in content, "main.py missing Clock per AC-3 60 FPS"
    assert "tick" in content, "main.py missing clock.tick per AC-3"
    assert "60" in content, "main.py missing 60 FPS per AC-3"


def test_main_contains_verify_pygame_api() -> None:
    """AC-3: main.py contains verify_pygame_api per ADR-019 API verification."""
    content = _read_main()
    assert "verify_pygame_api" in content, "main.py missing verify_pygame_api per ADR-019"


def test_main_contains_is_legal_move() -> None:
    """AC-3: main.py contains is_legal_move check for arrow keys per AC-2 legal check."""
    content = _read_main()
    assert "is_legal_move" in content, "main.py missing is_legal_move per AC-3 arrow keys legal check"


def test_main_contains_history_snapshot_gamestate() -> None:
    """AC-3: main.py contains HistorySnapshot including game_state for undo exact restore."""
    content = _read_main()
    assert "HistorySnapshot" in content, "main.py missing HistorySnapshot per AC-3 undo exact"
    assert "game_state" in content, "main.py missing game_state in HistorySnapshot per AC-3"


def test_main_contains_visual_proof_path() -> None:
    """AC-4: main.py contains visual-proof directory path per File: visual-proof directory setup."""
    content = _read_main()
    assert "visual-proof" in content, "main.py missing visual-proof path per AC-4"


# ---------------------------------------------------------------------------
# Additional checks for tiles.py per AC-1 reactor chrome heat identity
# ---------------------------------------------------------------------------


def test_tiles_py_exists_and_contains_draw_board() -> None:
    """AC-1: src/render/tiles.py exists with draw_board API locked per ADR-018."""
    assert TILES_PY_PATH.exists(), f"tiles.py not found at {TILES_PY_PATH}"
    content = TILES_PY_PATH.read_text(encoding="utf-8")
    assert "def draw_board" in content, "tiles.py missing draw_board per ADR-018 API locked"
    assert "surface" in content and "grid" in content and "score" in content, (
        "tiles.py draw_board signature must contain surface grid score per ADR-018"
    )


def test_tiles_py_contains_heat_identity_colors() -> None:
    """AC-1: tiles.py contains heat identity #3B82F6 #F59E0B #EF4444 #FFFFFF per ADR-020."""
    assert TILES_PY_PATH.exists(), f"tiles.py not found at {TILES_PY_PATH}"
    content = TILES_PY_PATH.read_text(encoding="utf-8")
    # Check for heat colors via hex or rgb
    has_3b82f6 = "#3B82F6" in content or "#3b82f6" in content.lower() or "59, 130, 246" in content
    has_f59e0b = "#F59E0B" in content or "#f59e0b" in content.lower() or "245, 158, 11" in content
    has_ef4444 = "#EF4444" in content or "#ef4444" in content.lower() or "239, 68, 68" in content
    has_ffffff = "#FFFFFF" in content or "#ffffff" in content.lower() or "255, 255, 255" in content
    assert has_3b82f6, "tiles.py missing heat 0 #3B82F6 cool blue per AC-1"
    assert has_f59e0b, "tiles.py missing heat 1 #F59E0B warm amber per AC-1"
    assert has_ef4444, "tiles.py missing heat 2 #EF4444 hot red per AC-1"
    assert has_ffffff, "tiles.py missing heat 3 #FFFFFF glow per AC-1"


def test_tiles_py_contains_reactor_chrome_colors() -> None:
    """AC-1: tiles.py contains reactor chrome #0F172A #1E293B #334155 #475569 per ADR-020."""
    assert TILES_PY_PATH.exists(), f"tiles.py not found at {TILES_PY_PATH}"
    content = TILES_PY_PATH.read_text(encoding="utf-8")
    has_0f172a = "#0F172A" in content or "#0f172a" in content.lower() or "15, 23, 42" in content
    has_1e293b = "#1E293B" in content or "#1e293b" in content.lower() or "30, 41, 59" in content
    has_334155 = "#334155" in content or "51, 65, 85" in content
    has_475569 = "#475569" in content or "71, 85, 105" in content
    assert has_0f172a, "tiles.py missing background #0F172A per AC-1 reactor chrome"
    assert has_1e293b, "tiles.py missing board #1E293B per AC-1"
    assert has_334155, "tiles.py missing empty #334155 per AC-1"
    assert has_475569, "tiles.py missing border #475569 per AC-1"
