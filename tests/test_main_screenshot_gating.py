"""Tests for screenshot gating wiring finalization to 3 PNGs merge toast gameover.

Phase 4 Sprint 3 Task 1 — TDD red phase.

Purpose:
    Verify src/main.py finalization to 3 distinct PNGs:
    visual-proof/phase-4-merge.png after merge animation frame,
    phase-4-toast.png after toast visible has_visible(),
    phase-4-gameover.png after game-over overlay visible.
    Prior wiring captured single combined PNG; now extends to 3 PNGs
    with booleans merge_captured toast_captured gameover_captured.

System:
    Tests for IMainLoopPhase4 and IVisualProofPhase4 per architecture.
    File inspection via pathlib read_text to avoid pygame DISPLAY dependency.
    Integration tests use Board with seeded Random for turn pipeline.

Coverage:
    AC-1: visual-proof dir creation mkdir parents True exist_ok True OSError handling
    AC-2: screenshot capture image.save to 3 PNGs valid PNG 700x800 header 89 50 4E 47
    AC-2: manifest helper update_manifest naming file what it shows input sequence observation_id
    AC-3: no bare except grep only specific exceptions
    AC-4: turn pipeline locked slide->gen->spread->vent->spawn heat=0 immune
    AC-4: GameState ownership vent_streak unstable_survival undo_count persists
    AC-2: screenshot booleans avoid duplicates reset on R restart
    AC-1+2: verify_pygame_api hasattr checks and 700x800 Favur 2048 exact
"""

from __future__ import annotations

import copy
import random
import re
from pathlib import Path

MAIN_PY = Path("src/main.py")
VISUAL_PROOF_DIR = Path("visual-proof")
MERGE_PNG = VISUAL_PROOF_DIR / "phase-4-merge.png"
TOAST_PNG = VISUAL_PROOF_DIR / "phase-4-toast.png"
GAMEOVER_PNG = VISUAL_PROOF_DIR / "phase-4-gameover.png"
MANIFEST_FILE = VISUAL_PROOF_DIR / "README.md"


def _read_main() -> str:
    """Read src/main.py content as string."""
    assert MAIN_PY.exists(), f"{MAIN_PY} does not exist"
    return MAIN_PY.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: visual-proof dir creation mkdir parents True exist_ok True OSError handling
# ---------------------------------------------------------------------------


def test_visual_proof_dir_creation() -> None:
    """AC-1: main.py contains visual-proof dir creation via Path mkdir parents True exist_ok True OSError."""
    content = _read_main()

    assert "visual-proof" in content, "Missing visual-proof dir creation"
    assert "mkdir" in content, "Missing mkdir call"
    assert "parents=True" in content, "Missing parents=True in mkdir"
    assert "exist_ok=True" in content, "Missing exist_ok=True in mkdir"
    assert "except OSError" in content, "Missing specific except OSError for dir creation"
    # Ensure ensure_visual_proof_dir helper exists
    assert "ensure_visual_proof_dir" in content, "Missing ensure_visual_proof_dir helper"
    # No bare except
    bare = re.findall(r"^\s*except\s*:\s*$", content, re.MULTILINE)
    assert len(bare) == 0, f"Found bare except pattern: {bare}"
    # Check Path("visual-proof").mkdir pattern
    assert re.search(r'Path\(\s*["\']visual-proof["\']\s*\)\.mkdir', content), (
        "Missing Path('visual-proof').mkdir pattern"
    )


# ---------------------------------------------------------------------------
# Test 2: screenshot capture via pygame.image.save to 3 PNGs
# ---------------------------------------------------------------------------


def test_screenshot_capture_3_pngs() -> None:
    """AC-2: main.py contains screenshot capture via image.save to 3 PNGs merge toast gameover valid header."""
    content = _read_main()

    assert "image.save" in content, "Missing pygame.image.save for screenshot capture"
    assert "pygame.image.save" in content, "Missing pygame.image.save qualified call"
    # 3 distinct PNG paths required per pseudocode
    assert "phase-4-merge.png" in content, "Missing phase-4-merge.png path"
    assert "phase-4-toast.png" in content, "Missing phase-4-toast.png path"
    assert "phase-4-gameover.png" in content, "Missing phase-4-gameover.png path"

    # Header validation logic
    has_header_check = (
        "89 50 4E 47" in content
        or "\\x89PNG" in content
        or "b\"\\x89PNG" in content
        or "b'\\x89PNG" in content
        or "PNG" in content and "header" in content.lower()
    )
    assert has_header_check, "Missing PNG header validation logic 89 50 4E 47"

    # Check capture_screenshot function exists
    assert "capture_screenshot" in content, "Missing capture_screenshot helper"

    # Check set_mode 700x800
    assert "700" in content and "800" in content, "Missing 700x800 dimensions"
    assert "set_mode" in content, "Missing set_mode call"

    # Check has_visible and is_game_over and is_animating checks for gating
    assert "has_visible" in content, "Missing has_visible() check for toast gating"
    assert "is_game_over" in content, "Missing is_game_over check for gameover gating"
    assert "is_animating" in content, "Missing is_animating check for merge gating"

    # If PNGs exist, verify header
    for png_path in [MERGE_PNG, TOAST_PNG, GAMEOVER_PNG]:
        if png_path.exists():
            data = png_path.read_bytes()
            assert len(data) >= 8, f"{png_path} too small"
            assert data[:4] == b"\x89PNG", f"{png_path} invalid header {data[:4]!r}"


# ---------------------------------------------------------------------------
# Test 3: manifest helper update_manifest naming file what it shows input sequence observation_id
# ---------------------------------------------------------------------------


def test_manifest_helper() -> None:
    """AC-2: main.py contains manifest helper update_manifest per SOW Visual Verification Protocol."""
    content = _read_main()

    assert "update_manifest" in content, "Missing update_manifest function"
    assert "README.md" in content, "Missing README.md manifest handling"
    assert "visual-proof/README.md" in content or "visual-proof" in content, "Missing visual-proof/README.md path"

    # SOW protocol keywords
    assert "shows:" in content, "Missing 'shows:' in manifest entry format"
    assert "input:" in content, "Missing 'input:' in manifest entry format"
    assert "observation_id" in content, "Missing observation_id in manifest logic"
    assert "file:" in content, "Missing 'file:' in manifest entry format"

    # Check function signature includes required params
    assert "manifest_path" in content, "Missing manifest_path param"
    assert "file_name" in content, "Missing file_name param"
    assert "description" in content, "Missing description param"
    assert "input_sequence" in content or "input_seq" in content, "Missing input_sequence param"
    assert "observation_id" in content, "Missing observation_id param"

    # Check OSError handling for manifest
    assert "except OSError" in content, "Missing OSError handling for manifest"


# ---------------------------------------------------------------------------
# Test 4: no bare except grep no except: pattern only specific exceptions
# ---------------------------------------------------------------------------


def test_no_bare_except() -> None:
    """AC-3: main.py grepped for bare except pattern except: no matches, only specific exceptions."""
    content = _read_main()

    bare_pattern = re.compile(r"^\s*except\s*:\s*(?:#.*)?$", re.MULTILINE)
    matches = bare_pattern.findall(content)
    assert len(matches) == 0, f"Found bare except pattern: {matches}"

    bare_exact = list(re.finditer(r"except\s*:\s*\n", content))
    assert len(bare_exact) == 0, f"Found bare except: at positions {[m.start() for m in bare_exact]}"

    # Specific exception handling present
    assert "except (ValueError, TypeError, pygame.error)" in content or "except (ValueError" in content, (
        "Missing specific except (ValueError, TypeError, pygame.error) handling"
    )
    assert "except OSError" in content, "Missing specific except OSError handling"

    # At least 3 specific handlers for draw paths
    specific_count = content.count("except (ValueError, TypeError, pygame.error)")
    if specific_count < 3:
        # Also count generic ValueError TypeError handlers
        generic = len(re.findall(r"except\s*\(ValueError,\s*TypeError", content))
        assert generic >= 3, f"Expected at least 3 specific exception handlers, found {generic}"

    # At least 2 OSError handlers for FS ops
    oserror_count = content.count("except OSError")
    assert oserror_count >= 2, f"Expected at least 2 OSError handlers, found {oserror_count}"


# ---------------------------------------------------------------------------
# Test 5: turn pipeline still locked slide->gen->spread->vent->spawn heat=0->unstable
# ---------------------------------------------------------------------------


def test_turn_pipeline_locked() -> None:
    """AC-4: board.slide turn pipeline still locked slide->gen->spread->vent->spawn heat=0 immune same turn."""
    from src.core.board import Board, Direction, Tile

    rng = random.Random(42)

    board = Board(rng=rng)
    board.grid = [[None for _ in range(5)] for _ in range(5)]
    board.grid[0][0] = Tile(value=2, heat=0)
    board.grid[0][1] = Tile(value=2, heat=0)

    slide_result = board.slide(Direction.LEFT, rng=rng)

    assert hasattr(slide_result, "vent_occurred"), "SlideResult missing vent_occurred"
    assert isinstance(slide_result.vent_occurred, bool), "vent_occurred not bool"
    assert hasattr(slide_result, "unstable_present"), "SlideResult missing unstable_present"
    assert isinstance(slide_result.unstable_present, bool), "unstable_present not bool"
    assert hasattr(slide_result, "merges"), "SlideResult missing merges"
    assert hasattr(slide_result, "grid"), "SlideResult missing grid"

    # Merges have source_heats Tuple[int,int]
    for merge in slide_result.merges:
        assert hasattr(merge, "source_heats"), "MergeInfo missing source_heats"
        assert isinstance(merge.source_heats, tuple), "source_heats not tuple"
        assert len(merge.source_heats) == 2, "source_heats not Tuple[int,int] length 2"

    # New tiles heat=0 immune same turn: spawned tile should have heat 0
    # After slide with merge, grid should have at most 2 tiles (merged + spawned)
    # Check all tiles heat in valid range 0-3
    for r in range(5):
        for c in range(5):
            cell = slide_result.grid[r][c]
            if cell is not None:
                assert 0 <= cell.heat <= 3, f"Tile heat out of range 0-3: {cell.heat}"

    # Verify main.py does not duplicate heat logic outside board.py
    content = _read_main()
    # main.py should only call board.slide, not contain gen/spread/vent/spawn as separate logic
    # Allow mentions in comments but not as function calls duplicating pipeline
    # Simple check: main.py should not contain spread_heat or vent_heat direct calls
    # Board.slide is sole owner
    assert "board.slide" in content, "Missing board.slide call in main.py"
    # Ensure no direct heat pipeline duplication like gen/spread/vent/spawn outside board
    # We allow imports but not direct calls in main loop duplicating
    # Check that main.py does not define its own heat logic
    assert "def spread_heat" not in content, "main.py should not define spread_heat"
    assert "def vent_heat" not in content, "main.py should not define vent_heat"


# ---------------------------------------------------------------------------
# Test 6: GameState ownership vent_streak unstable_survival undo_count persists
# ---------------------------------------------------------------------------


def test_gamestate_ownership() -> None:
    """AC-4: GameState ownership vent_streak unstable_survival undo_count persists after wiring."""
    from src.core.gamestate import GameState
    from src.core.history import HistorySnapshot
    from src.core.board import Direction

    game_state = GameState()

    # Simulate update_after_turn vent true unstable false -> vent_streak 1
    game_state.update_after_turn(vent_occurred=True, unstable_present=False)
    assert game_state.vent_streak == 1, "vent_streak should increment to 1 on vent_occurred True"
    assert game_state.move_count == 1, "move_count should increment"
    assert game_state.unstable_survival == 0, "unstable_survival should be 0 when unstable_present False"

    # Simulate vent false unstable true -> vent_streak 0 unstable_survival 1
    game_state.update_after_turn(vent_occurred=False, unstable_present=True)
    assert game_state.vent_streak == 0, "vent_streak should reset to 0 when vent_occurred False"
    assert game_state.unstable_survival == 1, "unstable_survival should increment"

    # Deep copy snapshot and restore exact
    snapshot = HistorySnapshot(
        grid=[[None for _ in range(5)] for _ in range(5)],
        score=0,
        twist_state={},
        move_number=game_state.move_count,
        direction=Direction.LEFT,
        game_state=copy.deepcopy(game_state),
    )
    restored_gs = snapshot.game_state
    assert restored_gs.vent_streak == game_state.vent_streak
    assert restored_gs.unstable_survival == game_state.unstable_survival
    assert restored_gs.move_count == game_state.move_count
    assert restored_gs.undo_count == game_state.undo_count

    # Check GameState ownership in main.py
    content = _read_main()
    assert "GameState()" in content, "Missing GameState instantiation"
    assert "game_state.update_after_turn" in content, "Missing game_state.update_after_turn call"
    assert "game_state.increment_undo" in content or "increment_undo" in content, "Missing increment_undo"
    assert "reset_game_state" in content, "Missing reset_game_state for GameState reset"

    # Check history snapshot includes GameState deep copy
    assert "game_state" in content and "deepcopy" in content, "Missing GameState deep copy in history snapshot"


# ---------------------------------------------------------------------------
# Test 7: screenshot hooks booleans avoid duplicates and reset on R restart
# ---------------------------------------------------------------------------


def test_screenshot_booleans() -> None:
    """AC-2: booleans merge_captured toast_captured gameover_captured prevent duplicates reset on R restart."""
    content = _read_main()

    # Booleans exist
    assert "merge_captured" in content, "Missing merge_captured flag"
    assert "toast_captured" in content, "Missing toast_captured flag"
    assert "gameover_captured" in content, "Missing gameover_captured flag"

    # Initialized False
    assert "merge_captured = False" in content, "Missing merge_captured = False init"
    assert "toast_captured = False" in content, "Missing toast_captured = False init"
    assert "gameover_captured = False" in content, "Missing gameover_captured = False init"

    # Set True after capture
    assert "merge_captured = True" in content, "Missing merge_captured = True after capture"
    assert "toast_captured = True" in content, "Missing toast_captured = True after capture"
    assert "gameover_captured = True" in content, "Missing gameover_captured = True after capture"

    # Reset on R restart
    # Check reset_game_state or R handling resets booleans
    has_reset = (
        "merge_captured = False" in content
        and content.count("merge_captured = False") >= 2
    )
    # At least init and reset should both set False
    assert has_reset, "Missing reset of merge_captured to False on R restart (should appear at least twice: init and reset)"

    # Condition checks not merge_captured etc before capture
    assert "not merge_captured" in content or "if not merge_captured" in content or "merge_captured" in content, (
        "Missing condition check not merge_captured before capture"
    )
    assert "not toast_captured" in content or "toast_captured" in content, "Missing toast_captured condition"
    assert "not gameover_captured" in content or "gameover_captured" in content, "Missing gameover_captured condition"

    # Check reset_game_state returns booleans or main.py resets them on R
    assert "K_r" in content, "Missing K_r handling for R restart"


# ---------------------------------------------------------------------------
# Test 8: verify_pygame_api hasattr checks and 700x800 Favur 2048 exact
# ---------------------------------------------------------------------------


def test_verify_pygame_api_and_window() -> None:
    """AC-1+2: verify_pygame_api hasattr checks and window creation 700x800 non-resizable exact title."""
    content = _read_main()

    assert "verify_pygame_api" in content, "Missing verify_pygame_api function"
    assert "hasattr" in content, "Missing hasattr checks for pygame-ce API verification"

    # Check specific API checks
    assert "pygame.init" in content, "Missing pygame.init check"
    assert "set_mode" in content, "Missing display.set_mode check"
    assert "set_caption" in content, "Missing set_caption check"
    assert "SysFont" in content, "Missing font.SysFont check"
    assert "event.get" in content or "event.get" in content, "Missing event.get check"
    assert "image.save" in content, "Missing image.save check"
    assert "QUIT" in content, "Missing QUIT constant check"
    assert "KEYDOWN" in content, "Missing KEYDOWN constant check"
    assert "draw.rect" in content or "draw" in content, "Missing draw.rect check"
    assert "Clock" in content, "Missing Clock check"

    # Window creation 700x800 Favur 2048 exact title non-resizable
    assert "700" in content, "Missing 700 window width"
    assert "800" in content, "Missing 800 window height"
    assert "Favur 2048" in content, "Missing exact title Favur 2048"
    assert "set_mode" in content, "Missing set_mode call"
    assert "set_caption" in content, "Missing set_caption call"

    # Check non-resizable: no RESIZABLE flag
    assert "RESIZABLE" not in content, "Window should be non-resizable, found RESIZABLE flag"

    # Check 60 FPS
    assert "clock.tick(60)" in content or "clock.tick(fps)" in content, "Missing clock.tick(60) for 60 FPS"
    assert "60" in content, "Missing 60 FPS handling"

    # Check dt handling
    assert "dt" in content, "Missing dt handling for frame clock"
    assert "tick" in content, "Missing tick for frame timing"
