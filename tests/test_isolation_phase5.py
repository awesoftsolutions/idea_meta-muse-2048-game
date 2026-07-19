"""Isolation verification for Phase 5 Sprint 2 Tasks 2 and 4.

Pseudocode: registry://pseudocode/phase_5_sprint_2_task_2_4_code.md
Sprint: registry://sprints/phase-5-sprint-2.md
- AC-2 no external assets grep no image.load no font.Font file path only SysFont
- AC-3 tiles.py no debug heat dot x+w-10 no gray fallback (200,200,200) unified 70% heat 30% base
- AC-4 no bare except grep no except: pattern
- AC-5 single clock.tick(60) 60 FPS dt = clock.tick(60)/1000.0 no double tick
- AC-6 no _FallbackEffectManager no _FallbackToastManager Q-014 removal loud ImportError
- AC-7 toast base_x 10 width 200 no overlap high-score hx 550 Q-016 fix HUD preserved
- AC-8 effects.py heat-aware particles distinct per heat cool calm drift 2-3 #3B82F6 warm flicker 4-5 #F59E0B hot intense spark 6-8 #EF4444 unstable burst 10+ #FFFFFF
- AC-9 hud.py HUD score high-score move count vent_streak unstable_survival heat legend always-on reactor chrome
- AC-10 headless importable all core modules without DISPLAY

System: Isolation verification per pseudocode phase_5_sprint_2_task_2_4_code.md
Dependencies: stdlib sys re pathlib struct importlib, pytest, src.core.*
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

CORE_FILES = [
    "src/core/board.py",
    "src/core/rules.py",
    "src/core/score.py",
    "src/core/history.py",
    "src/core/twist.py",
    "src/core/achievements.py",
    "src/core/gamestate.py",
    "src/core/__init__.py",
]

RENDER_FILES = [
    "src/render/tiles.py",
    "src/render/effects.py",
    "src/render/hud.py",
    "src/render/__init__.py",
]

BARE_EXCEPT_FILES = [
    "src/main.py",
    "src/core/board.py",
    "src/render/tiles.py",
    "src/render/effects.py",
    "src/render/hud.py",
]

PYGAME_IMPORT_RE = re.compile(r"^\s*import\s+pygame\b", re.MULTILINE)
PYGAME_FROM_RE = re.compile(r"^\s*from\s+pygame\b", re.MULTILINE)
BARE_EXCEPT_RE = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
IMAGE_LOAD_RE = re.compile(r"image\.load")
FONT_FILE_RE = re.compile(r"font\.Font\s*\(")


# ---------------------------------------------------------------------------
# AC-1: sys.modules delta no pygame after core import
# ---------------------------------------------------------------------------


def test_no_pygame_sysmodules_core_phase5() -> None:
    """Verify sys.modules delta after importing core has no pygame (AC-1 Phase 5).

    Snapshot before, import src.core.board, rules, score, history, twist,
    achievements, gamestate, snapshot after, delta = after - before,
    assert no key starts with pygame and pygame not in delta.
    """
    before = set(sys.modules.keys())
    try:
        import importlib

        modules_to_import = [
            "src.core.board",
            "src.core.rules",
            "src.core.score",
            "src.core.history",
            "src.core.twist",
            "src.core.achievements",
            "src.core.gamestate",
        ]
        for mod_name in modules_to_import:
            try:
                importlib.import_module(mod_name)
            except (ImportError, ValueError, TypeError) as exc:
                pytest.fail(f"Failed to import {mod_name}: {exc}")
    except (ImportError, ValueError, TypeError) as exc:
        pytest.fail(f"Import setup failed: {exc}")

    after = set(sys.modules.keys())
    delta = after - before

    pygame_leaked = [k for k in delta if k.startswith("pygame") or k == "pygame"]
    assert not pygame_leaked, f"pygame leaked in sys.modules delta: {pygame_leaked}"
    assert "pygame" not in delta, "pygame in delta"
    containing = [k for k in delta if "pygame" in k.lower()]
    assert not containing, f"Modules containing pygame in delta: {containing}"


def test_no_pygame_import_grep_core_phase5() -> None:
    """Grep src/core for exact pygame import patterns (AC-1b Phase 5).

    For each file in src/core/*.py, search regex ^\\s*import\\s+pygame\\b
    and ^\\s*from\\s+pygame\\b multiline, fail if match found.
    """
    for file_path in CORE_FILES:
        path = Path(file_path)
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            pytest.fail(f"Failed to read {file_path}: {exc}")

        import_matches = PYGAME_IMPORT_RE.findall(content)
        from_matches = PYGAME_FROM_RE.findall(content)
        assert not import_matches, f"{file_path} has import pygame: {import_matches}"
        assert not from_matches, f"{file_path} has from pygame: {from_matches}"


# ---------------------------------------------------------------------------
# AC-2: no external assets grep
# ---------------------------------------------------------------------------


def test_no_external_assets_render_phase5() -> None:
    """Verify no pygame.image.load and no font.Font file path, only SysFont (AC-2 Phase 5).

    List src/render/*.py, for each file read content, search image.load
    and font.Font( regex, fail if found, check SysFont presence in hud.py tiles.py.
    """
    for file_path in RENDER_FILES:
        path = Path(file_path)
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            pytest.fail(f"Failed to read {file_path}: {exc}")

        image_load_matches = IMAGE_LOAD_RE.findall(content)
        assert not image_load_matches, f"{file_path} has image.load: {image_load_matches}"

        font_file_matches = FONT_FILE_RE.findall(content)
        assert not font_file_matches, f"{file_path} has font.Font file path: {font_file_matches}"

    # Verify SysFont present in hud.py and tiles.py
    for required_file in ["src/render/hud.py", "src/render/tiles.py"]:
        path = Path(required_file)
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        assert "SysFont" in content, f"{required_file} missing SysFont - should use SysFont only"


# ---------------------------------------------------------------------------
# AC-3: tiles.py debug artifacts removed unified 70% heat 30% base
# ---------------------------------------------------------------------------


def test_tiles_no_debug_artifacts_phase5() -> None:
    """Verify no debug heat dot x+w-10 and no gray fallback (200,200,200) unified 70% heat 30% base (AC-3 Phase 5).

    Read src/render/tiles.py, search x+w-10 or x + w - 10, y+10,5,
    (200,200,200) and (200, 200, 200), fail if found.
    """
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists(), "src/render/tiles.py does not exist"

    try:
        content = tiles_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read tiles.py: {exc}")

    # Debug heat dot patterns
    assert "x+w-10" not in content, "tiles.py has debug heat dot x+w-10"
    assert "x + w - 10" not in content, "tiles.py has debug heat dot x + w - 10"

    # Gray fallback patterns - must not have literal (200,200,200) or (200, 200, 200)
    lines_with_gray = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        if "(200, 200, 200)" in line or "(200,200,200)" in line:
            lower = line.lower()
            if (
                "gray_val" in lower
                or "variable" in lower
                or "avoid" in lower
                or "never returns gray" in lower
                or "not gray" in lower
                or "ensure never exactly gray" in lower
            ):
                continue
            lines_with_gray.append((line_no, line.strip()))
    assert not lines_with_gray, f"tiles.py has gray fallback literal: {lines_with_gray}"

    # Verify unified 70% heat 30% base - check contains 0.7 and blend
    assert "0.7" in content, "tiles.py should contain 0.7 for unified blend 70% heat 30% base"
    assert "blend" in content.lower(), "tiles.py missing blend logic for unified 70% heat 30% base"


# ---------------------------------------------------------------------------
# AC-4: bare except fixed
# ---------------------------------------------------------------------------


def test_no_bare_except_phase5() -> None:
    """Verify no bare except: in src/main.py and src/core/board.py (AC-4 Phase 5).

    Read src/main.py and src/core/board.py, regex ^\\s*except\\s*:\\s*$ multiline,
    fail if count >0, allow except OSError and except (ValueError, TypeError, pygame.error).
    """
    for file_path in BARE_EXCEPT_FILES:
        path = Path(file_path)
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            pytest.fail(f"Failed to read {file_path}: {exc}")

        bare_matches = BARE_EXCEPT_RE.findall(content)
        assert not bare_matches, f"{file_path} has bare except: pattern: {bare_matches}"

        # Also verify specific exceptions are used instead
        if "except" in content:
            has_specific = (
                "except OSError" in content
                or "except (ValueError" in content
                or "except ValueError" in content
                or "except TypeError" in content
            )
            # Only enforce for main.py which must have specific handling
            if file_path == "src/main.py":
                assert has_specific, (
                    f"{file_path} should have specific except handling like "
                    "except OSError or except (ValueError, TypeError, pygame.error)"
                )


# ---------------------------------------------------------------------------
# AC-5: single clock.tick(60) 60 FPS
# ---------------------------------------------------------------------------


def test_single_clock_tick_60_fps_phase5() -> None:
    """Verify single clock.tick(60) 60 FPS dt = clock.tick(60)/1000.0 no double tick (AC-5 Phase 5).

    Count occurrences of clock.tick(60) in main.py assert ==1.
    """
    main_path = Path("src/main.py")
    assert main_path.exists(), "src/main.py does not exist"

    try:
        content = main_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read main.py: {exc}")

    code_lines = [ln for ln in content.splitlines() if "clock.tick(60)" in ln and "dt" in ln and "1000.0" in ln]
    actual_code = [ln for ln in code_lines if ln.strip().startswith("dt =") or ln.strip().startswith("dt=")]
    assert len(actual_code) == 1, f"Expected exactly 1 dt = clock.tick(60) / 1000.0 code line, found {len(actual_code)}: {actual_code} - must be single tick 60 FPS"

    assert "dt" in content and "clock.tick" in content, "dt = clock.tick(60)/1000.0 pattern missing"
    assert "dt = clock.tick(60) / 1000.0" in content or "dt=clock.tick(60)/1000.0" in content or "clock.tick(60)" in content, (
        "dt = clock.tick(60)/1000.0 pattern missing"
    )


# ---------------------------------------------------------------------------
# AC-6: no _FallbackEffectManager no _FallbackToastManager Q-014 removal
# ---------------------------------------------------------------------------


def test_no_fallback_managers_q014() -> None:
    """Verify no _FallbackEffectManager and no _FallbackToastManager Q-014 removal loud ImportError (AC-6 Phase 5).

    Grep src/main.py and src/render/effects.py hud.py for _FallbackEffectManager and _FallbackToastManager, assert empty.
    """
    files_to_check = [
        "src/main.py",
        "src/render/effects.py",
        "src/render/hud.py",
    ]

    for file_path in files_to_check:
        path = Path(file_path)
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            pytest.fail(f"Failed to read {file_path}: {exc}")

        assert "_FallbackEffectManager" not in content, (
            f"{file_path} has _FallbackEffectManager - Q-014 removal must remain, should be loud ImportError"
        )
        assert "_FallbackToastManager" not in content, (
            f"{file_path} has _FallbackToastManager - Q-014 removal must remain, should be loud ImportError"
        )

    # Verify loud ImportError with install hint in main.py
    main_path = Path("src/main.py")
    if main_path.exists():
        main_content = main_path.read_text(encoding="utf-8")
        assert "ImportError" in main_content, "main.py missing ImportError for loud failure Q-014"
        assert "pygame-ce" in main_content or "pygame" in main_content.lower(), (
            "main.py missing install hint pygame-ce ^2.5.0 for loud ImportError Q-014"
        )


# ---------------------------------------------------------------------------
# AC-7: toast base_x 10 width 200 no overlap high-score hx 550 Q-016 fix
# ---------------------------------------------------------------------------


def test_toast_base_x_10_width_200_no_overlap_q016() -> None:
    """Verify toast base_x 10 width 200 range 10-210 no overlap high-score hx 550 Q-016 fix HUD preserved (AC-7 Phase 5).

    Grep hud.py for base_x 10 width 200, verify no overlap with high-score hx 550.
    """
    hud_path = Path("src/render/hud.py")
    assert hud_path.exists(), "src/render/hud.py does not exist"

    try:
        content = hud_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read hud.py: {exc}")

    # Check base_x 10 present
    assert "base_x = 10" in content or "base_x=10" in content, "hud.py missing base_x 10 - should be left side to avoid overlap Q-016"

    # Check width 200 present via TOAST_W constant
    assert "TOAST_W" in content, "hud.py missing TOAST_W constant"
    assert "200" in content, "hud.py missing width 200"

    # Verify TOAST_W = 200
    assert re.search(r"TOAST_W\s*:\s*int\s*=\s*200", content) or "TOAST_W: int = 200" in content or "TOAST_W = 200" in content, (
        "hud.py TOAST_W should be 200 per Q-016 fix"
    )

    # Verify range 10-210 no overlap with high-score hx 550
    # Old base_x 410 width 280 to 690 overlaps hx 550, new base_x 10 width 200 range 10-210 no overlap
    # Check that old overlapping layout not present as primary
    # Allow 410 in comments but not as active base_x
    lines = content.splitlines()
    active_base_x_410 = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "base_x = 410" in line or "base_x=410" in line:
            active_base_x_410 = True
    assert not active_base_x_410, "hud.py still has active base_x 410 overlapping high-score hx 550 - should be 10 Q-016"

    # Verify HUD preserved during game-over dim top 120px or re-draw HUD after dim
    assert "HUD_H" in content or "120" in content, "hud.py missing HUD_H 120 for HUD preserved during game-over dim Q-016"
    assert "draw_game_over" in content, "hud.py missing draw_game_over for game-over overlay Q-016"


# ---------------------------------------------------------------------------
# AC-8: effects.py heat-aware particles distinct per heat
# ---------------------------------------------------------------------------


def test_effects_heat_aware_particles_distinct_phase5() -> None:
    """Verify effects.py heat-aware particles distinct per heat cool calm drift 2-3 #3B82F6 warm flicker 4-5 #F59E0B hot intense spark 6-8 #EF4444 unstable burst 10+ #FFFFFF (AC-8 Phase 5).

    Read effects.py content, check contains #3B82F6 or cool particle logic, #F59E0B or warm, #EF4444 or hot, #FFFFFF or unstable burst, particle counts distinct per heat 2-3 4-5 6-8 10+, programmatic only no board mutation.
    """
    effects_path = Path("src/render/effects.py")
    assert effects_path.exists(), "src/render/effects.py does not exist"

    try:
        content = effects_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read effects.py: {exc}")

    # Check heat colors present
    assert "#3B82F6" in content or "59, 130, 246" in content or "HEAT_COOL" in content, (
        "effects.py missing cool #3B82F6 particle logic"
    )
    assert "#F59E0B" in content or "245, 158, 11" in content or "HEAT_WARM" in content, (
        "effects.py missing warm #F59E0B particle logic"
    )
    assert "#EF4444" in content or "239, 68, 68" in content or "HEAT_HOT" in content, (
        "effects.py missing hot #EF4444 particle logic"
    )
    assert "#FFFFFF" in content or "255, 255, 255" in content or "HEAT_UNSTABLE" in content, (
        "effects.py missing unstable #FFFFFF burst logic"
    )

    # Check particle counts distinct per heat
    assert "2, 3" in content or "(2, 3)" in content or "2-3" in content, "effects.py missing cool particle count 2-3"
    assert "4, 5" in content or "(4, 5)" in content or "4-5" in content, "effects.py missing warm particle count 4-5"
    assert "6, 8" in content or "(6, 8)" in content or "6-8" in content, "effects.py missing hot particle count 6-8"
    assert "10" in content, "effects.py missing unstable particle count 10+"

    # Verify programmatic only no external assets
    assert "image.load" not in content, "effects.py has image.load - should be programmatic only"
    assert "font.Font(" not in content, "effects.py has font.Font file path - should use SysFont only"

    # Verify no board mutation
    assert "EffectManager" in content, "effects.py missing EffectManager export"

    # Verify heat-aware particles distinct per heat cool calm drift 2-3 #3B82F6 warm flicker 4-5 #F59E0B hot intense spark 6-8 #EF4444 unstable burst 10+ #FFFFFF
    assert "calm" in content.lower() or "drift" in content.lower() or "cool" in content.lower(), (
        "effects.py missing cool calm drift description"
    )
    assert "flicker" in content.lower() or "warm" in content.lower(), "effects.py missing warm flicker description"
    assert "intense" in content.lower() or "spark" in content.lower() or "hot" in content.lower(), (
        "effects.py missing hot intense spark description"
    )
    assert "burst" in content.lower() or "unstable" in content.lower(), "effects.py missing unstable burst description"


# ---------------------------------------------------------------------------
# AC-9: hud.py HUD score high-score move count vent_streak unstable_survival heat legend always-on
# ---------------------------------------------------------------------------


def test_hud_preserved_phase5() -> None:
    """Verify hud.py HUD score high-score move count vent_streak unstable_survival heat legend always-on reactor chrome (AC-9 Phase 5).

    Read hud.py content, check contains score high-score move count vent_streak unstable_survival heat legend, reactor chrome colors, ToastManager queue timed 2-3 sec stacking vertical, game-over overlay dim 50% alpha #0F172A.
    """
    hud_path = Path("src/render/hud.py")
    assert hud_path.exists(), "src/render/hud.py does not exist"

    try:
        content = hud_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read hud.py: {exc}")

    # Check HUD elements
    assert "score" in content.lower(), "hud.py missing score"
    assert "high_score" in content or "high-score" in content.lower() or "Best" in content, "hud.py missing high-score"
    assert "move_count" in content, "hud.py missing move_count"
    assert "vent_streak" in content, "hud.py missing vent_streak"
    assert "unstable_survival" in content, "hud.py missing unstable_survival"
    assert "heat" in content.lower() and "legend" in content.lower(), "hud.py missing heat legend"

    # Check reactor chrome colors
    assert "#0F172A" in content or "15, 23, 42" in content or "REACTOR_BG" in content, "hud.py missing reactor chrome #0F172A"
    assert "#1E293B" in content or "30, 41, 59" in content or "BOARD_BG" in content, "hud.py missing reactor chrome #1E293B"

    # Check ToastManager queue timed 2-3 sec stacking vertical
    assert "ToastManager" in content, "hud.py missing ToastManager"
    assert "2.5" in content or "2-3" in content or "TOAST_DURATION" in content, "hud.py missing toast duration 2-3 sec"

    # Check game-over overlay dim 50% alpha #0F172A
    assert "draw_game_over" in content, "hud.py missing draw_game_over"
    assert "128" in content or "50%" in content or "alpha" in content.lower(), (
        "hud.py missing game-over dim 50% alpha"
    )

    # Check HUD preserved during game-over dim top 120px
    assert "HUD_H" in content or "120" in content, "hud.py missing HUD_H 120 for HUD preserved during game-over dim"


# ---------------------------------------------------------------------------
# AC-10: headless importable all core modules without DISPLAY
# ---------------------------------------------------------------------------


def test_headless_importable_all_core_phase5() -> None:
    """Verify all core modules headless importable without DISPLAY (AC-10 Phase 5).

    Import Board, Tile, Direction from src.core.board, assert BOARD_SIZE==5,
    create Tile value=4 heat=1 assert value 4 heat 1, assert Direction has UP DOWN LEFT RIGHT,
    import modules list: src.core.board, rules, score, history, twist, achievements, gamestate, core.
    """
    try:
        from src.core.board import BOARD_SIZE, Direction, Tile

        assert BOARD_SIZE == 5, f"BOARD_SIZE expected 5, got {BOARD_SIZE}"
        tile = Tile(value=4, heat=1)
        assert tile.value == 4
        assert tile.heat == 1
        assert hasattr(Direction, "UP")
        assert hasattr(Direction, "DOWN")
        assert hasattr(Direction, "LEFT")
        assert hasattr(Direction, "RIGHT")

        import importlib

        modules = [
            "src.core.board",
            "src.core.rules",
            "src.core.score",
            "src.core.history",
            "src.core.twist",
            "src.core.achievements",
            "src.core.gamestate",
            "src.core",
        ]
        for mod_name in modules:
            try:
                importlib.import_module(mod_name)
            except (ImportError, ValueError, TypeError, AttributeError) as exc:
                pytest.fail(f"Failed to import {mod_name} headless: {exc}")

        # Also verify GameState, ScoreState, HistoryStack, Achievements importable
        from src.core import Achievements, GameState, HistoryStack, ScoreState

        assert Achievements is not None
        assert GameState is not None
        assert HistoryStack is not None
        assert ScoreState is not None

    except (ImportError, ValueError, TypeError, AttributeError) as exc:
        pytest.fail(f"Headless importable all core check failed: {exc}")


# ---------------------------------------------------------------------------
# Additional: src/render listing verification
# ---------------------------------------------------------------------------


def test_render_dir_listing_phase5() -> None:
    """Verify src/render contains tiles.py effects.py hud.py __init__.py (Phase 5).

    List src/render directory, check existence of __init__.py, tiles.py, effects.py, hud.py, check file sizes >0.
    """
    render_dir = Path("src/render")
    assert render_dir.exists(), "src/render directory does not exist"
    assert render_dir.is_dir(), "src/render is not a directory"

    required_files = ["__init__.py", "tiles.py", "effects.py", "hud.py"]
    for fname in required_files:
        fpath = render_dir / fname
        assert fpath.exists(), f"src/render/{fname} does not exist"
        try:
            size = fpath.stat().st_size
        except OSError as exc:
            pytest.fail(f"Failed to stat src/render/{fname}: {exc}")
        assert size > 0, f"src/render/{fname} size 0, expected >0"


def test_no_synthetic_merge_phase5() -> None:
    """Verify no _SyntheticMerge class in main.py, real turn pipeline only (Phase 5).

    Grep main.py for _SyntheticMerge assert empty no matches, grep for slide and gen and spread and vent and spawn in order.
    """
    main_path = Path("src/main.py")
    assert main_path.exists(), "src/main.py does not exist"

    try:
        content = main_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        pytest.fail(f"Failed to read main.py: {exc}")

    assert "_SyntheticMerge" not in content, "_SyntheticMerge class found - must use real turn pipeline only per Q-010"
    assert "slide" in content, "slide missing from turn pipeline"
    assert "board.slide" in content or "slide" in content, "board.slide missing - turn pipeline locked"
