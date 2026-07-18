"""
tests/test_isolation_phase2.py — Isolation verification for Phase 2 Sprint 1 Task 4.

Verifies tech debt isolation per ADR-015 headless testability and ADR-007 no render.
Checks src/ layout has no src/render/, no pygame import leak via sys.modules snapshot
and grep exact patterns "import pygame" / "from pygame", Tile dataclass migration clean
(no parallel grids, injectable Random not global random, headless importable without
DISPLAY), exports verification for src/core/__init__.py (Tile, Board, Direction,
SlideResult, MergeInfo, BOARD_SIZE etc), technical_debt.md 0 active debt, and pytest
green for test_board and test_rules.

AC mapping:
- AC-1 pygame not in sys.modules -> test_no_pygame_sysmodules_board, test_no_pygame_sysmodules_rules, test_no_pygame_grep
- AC-2 src/render/ does not exist -> test_src_render_absent
- AC-3 Tile dataclass not parallel grids no global random headless -> test_board_headless_importable_without_DISPLAY, test_no_global_random_usage
- AC-4 __init__.py exports -> test_init_exports_verification
- AC-5 0 active debt -> test_technical_debt_zero_active
- AC-6 pytest green -> verified by running test_board + test_rules (covered by CI, not duplicated here)

No pygame import in this file. Headless, no DISPLAY required. stdlib only + src.core.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
SRC_RENDER = SRC_DIR / "render"
SRC_CORE = SRC_DIR / "core"
BOARD_PY = SRC_CORE / "board.py"
RULES_PY = SRC_CORE / "rules.py"
INIT_PY = SRC_CORE / "__init__.py"
TECH_DEBT_MD = PROJECT_ROOT / "technical_debt.md"


def _assert_no_pygame_in_modules(modules_snapshot: set[str], context: str) -> None:
    """Assert no pygame key in given sys.modules snapshot."""
    assert "pygame" not in modules_snapshot, f"{context}: 'pygame' found in sys.modules"
    pygame_keys = [k for k in modules_snapshot if k == "pygame" or k.startswith("pygame.")]
    assert not pygame_keys, f"{context}: pygame keys found in sys.modules: {pygame_keys}"


def _assert_no_pygame_in_delta(
    before: set[str], after: set[str], context: str
) -> None:
    """Delta check: if pygame already present before (pollution), only check new keys."""
    delta = after - before
    pygame_delta = [k for k in delta if k == "pygame" or k.startswith("pygame.")]
    assert not pygame_delta, f"{context}: new pygame keys in delta: {pygame_delta}"
    # Also absolute check if not polluted before
    if "pygame" not in before:
        _assert_no_pygame_in_modules(after, context)


# ---------------------------------------------------------------------------
# Test: test_src_render_absent — AC-2
# ---------------------------------------------------------------------------


def test_src_render_absent() -> None:
    """AC-2: src/render/ must not exist per ADR-007. Negative existence check."""
    # Method 1: pathlib existence check, FileNotFoundError treated as absent PASS
    try:
        exists = SRC_RENDER.exists()
    except FileNotFoundError:
        exists = False
    assert not exists, f"src/render/ must not exist per ADR-007, found at {SRC_RENDER}"

    # Method 2: directory listing of src/ for render entry (case-insensitive)
    try:
        src_entries = [p.name.lower() for p in SRC_DIR.iterdir()]
    except FileNotFoundError:
        src_entries = []
    assert "render" not in src_entries, f"src/ listing contains render entry: {src_entries}"

    # Also verify src/ contains expected items
    try:
        src_names = [p.name for p in SRC_DIR.iterdir()]
    except FileNotFoundError:
        src_names = []
    # At minimum core must exist
    assert "core" in src_names, f"src/ should contain core/, got {src_names}"


# ---------------------------------------------------------------------------
# Test: test_no_pygame_sysmodules_board — AC-1
# ---------------------------------------------------------------------------


def test_no_pygame_sysmodules_board() -> None:
    """AC-1: No pygame in sys.modules after importing src.core.board."""
    before = set(sys.modules.keys())
    # Use importlib to allow snapshot
    import src.core.board as board_mod  # noqa: F401 — import for side effect check

    # Re-import via importlib to ensure fresh path if needed
    importlib.import_module("src.core.board")
    after = set(sys.modules.keys())

    _assert_no_pygame_in_modules(after, "board import absolute")
    _assert_no_pygame_in_delta(before, after, "board import delta")


# ---------------------------------------------------------------------------
# Test: test_no_pygame_sysmodules_rules — AC-1
# ---------------------------------------------------------------------------


def test_no_pygame_sysmodules_rules() -> None:
    """AC-1: No pygame in sys.modules after importing src.core.rules."""
    before = set(sys.modules.keys())
    importlib.import_module("src.core.rules")
    after = set(sys.modules.keys())

    _assert_no_pygame_in_modules(after, "rules import absolute")
    _assert_no_pygame_in_delta(before, after, "rules import delta")


# ---------------------------------------------------------------------------
# Test: test_board_headless_importable_without_DISPLAY — AC-3 headless part
# ---------------------------------------------------------------------------


def test_board_headless_importable_without_DISPLAY() -> None:
    """AC-3 headless: Board importable without DISPLAY, BOARD_SIZE 5, Direction enum, Tile instantiation."""
    # Import without DISPLAY env — should not raise containing DISPLAY or pygame
    try:
        import src.core.board as board_module
    except Exception as exc:
        msg = str(exc).lower()
        assert "display" not in msg, f"Import failed due to DISPLAY: {exc}"
        assert "pygame" not in msg, f"Import failed due to pygame: {exc}"
        raise

    # Check Board class exists
    assert hasattr(board_module, "Board"), "Board class missing in src.core.board"
    assert hasattr(board_module, "BOARD_SIZE"), "BOARD_SIZE missing"
    assert board_module.BOARD_SIZE == 5, f"BOARD_SIZE expected 5, got {board_module.BOARD_SIZE}"

    # Direction enum checks
    assert hasattr(board_module, "Direction"), "Direction missing"
    Direction = board_module.Direction
    for name in ("UP", "DOWN", "LEFT", "RIGHT"):
        assert hasattr(Direction, name), f"Direction.{name} missing"

    # Tile instantiation
    Tile = board_module.Tile
    tile = Tile(value=4, heat=1)
    assert tile.value == 4
    assert tile.heat == 1

    # Board 5x5 grid with injected RNG
    import random

    rng = random.Random(42)
    board = board_module.Board(grid=None, rng=rng)
    assert board.grid is not None
    assert len(board.grid) == 5
    assert all(len(row) == 5 for row in board.grid)
    assert board.rng is rng

    # create_empty_grid
    empty = board_module.create_empty_grid()
    assert len(empty) == 5
    assert all(len(row) == 5 for row in empty)


# ---------------------------------------------------------------------------
# Test: test_no_global_random_usage — AC-3 no global random
# ---------------------------------------------------------------------------


def test_no_global_random_usage() -> None:
    """AC-3: Verify no global random usage, injectable RNG pattern, no parallel grids."""
    content = BOARD_PY.read_text(encoding="utf-8")

    # Parallel grids must not exist — desync risk per ADR-008
    assert "heat_grid" not in content, "heat_grid found — parallel grid desync risk"
    assert "value_grid" not in content, "value_grid found — parallel grid desync risk"

    # Injectable RNG checks
    assert "self.rng" in content, "self.rng usage missing — injectable RNG required"
    assert "random.Random" in content, "random.Random type check missing"
    assert "rng.choice" in content, "rng.choice usage missing"
    assert "rng.random" in content, "rng.random usage missing"

    # Global random usage checks — search for random.random() and random.choice without rng prefix
    # Requirement: no random.random() without rng. prefix, no random.choice without rng prefix
    lines = content.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comments? Requirement says exact patterns treat any occurrence as FAIL to be safe,
        # but for global random we must ensure no bare random.random() / random.choice
        # Allow if line contains "rng.random" or "rng.choice" or "self.rng"
        if "random.random()" in line:
            # If line also contains rng. prefix for random, it's still global if bare exists
            # Check if bare random.random() appears without rng. in same line context
            # We require that any random.random() occurrence must be preceded by rng. or self.rng
            # Simplest: if "rng.random" not in line and "self.rng" not in line, fail
            # But board.py uses rng.random() via param rng, so line contains rng.random
            # So check: if line contains "random.random()" literal, it's global usage
            # because injectable uses rng.random() not random.random()
            assert False, f"Global random.random() found at board.py:{idx}: {stripped}"
        if "random.choice" in line:
            # Same logic: bare random.choice is global, should be rng.choice
            # Allow only if line is import or type check? import random is ok
            # But random.choice literal is forbidden
            # Check if it's import line
            if stripped.startswith("import random"):
                continue
            # If line contains rng.choice, it won't contain random.choice, so this is bare
            assert False, f"Global random.choice found at board.py:{idx}: {stripped}"

    # Also check rules.py should not use random at all (or at least no global random)
    rules_content = RULES_PY.read_text(encoding="utf-8")
    # rules.py should not import random per design (pure simulation)
    # If it does, ensure no random.random() / random.choice
    for idx, line in enumerate(rules_content.splitlines(), start=1):
        if "random.random()" in line or "random.choice" in line:
            assert False, f"Global random usage in rules.py:{idx}: {line.strip()}"

    # Tile dataclass checks
    assert "@dataclass" in content, "@dataclass missing for Tile"
    assert "class Tile" in content, "class Tile missing"
    assert "value:" in content, "Tile value field missing"
    assert "heat:" in content, "Tile heat field missing"
    # Grid type should be Optional[Tile] not Optional[int] old spike format
    # Check that Grid alias uses Tile
    assert "Optional[\"Tile\"]" in content or "Optional[Tile]" in content, "Grid type should be Optional[Tile]"


# ---------------------------------------------------------------------------
# Test: test_init_exports_verification — AC-4
# ---------------------------------------------------------------------------


def test_init_exports_verification() -> None:
    """AC-4: __init__.py exports Tile Board Direction SlideResult MergeInfo."""
    content = INIT_PY.read_text(encoding="utf-8")

    required = ["Tile", "Board", "Direction", "SlideResult", "MergeInfo"]
    for sym in required:
        assert sym in content, f"{sym} missing in src/core/__init__.py content"

    # Check import statement contains from .board import
    assert "from .board import" in content, "from .board import missing in __init__.py"

    # Check __all__ contains required symbols
    assert "__all__" in content, "__all__ missing in __init__.py"
    for sym in required:
        assert f'"{sym}"' in content or f"'{sym}'" in content, f"{sym} missing in __all__"

    # Runtime import verification
    from src.core import (  # noqa: F401 — runtime check
        BOARD_SIZE,
        Board,
        Direction,
        MergeInfo,
        SlideResult,
        Tile,
    )

    assert BOARD_SIZE == 5
    # Type checks
    assert isinstance(Tile(value=2, heat=0), Tile)
    # Board is class
    assert isinstance(Board, type)
    # Direction is enum-like with UP/DOWN/LEFT/RIGHT
    assert hasattr(Direction, "UP")
    assert hasattr(Direction, "DOWN")
    assert hasattr(Direction, "LEFT")
    assert hasattr(Direction, "RIGHT")


# ---------------------------------------------------------------------------
# Test: test_technical_debt_zero_active — AC-5
# ---------------------------------------------------------------------------


def test_technical_debt_zero_active() -> None:
    """AC-5: technical_debt.md shows 0 active debt."""
    assert TECH_DEBT_MD.exists(), f"technical_debt.md not found at {TECH_DEBT_MD}"
    content = TECH_DEBT_MD.read_text(encoding="utf-8")

    # Check summary line with 0 active (case-insensitive)
    lower = content.lower()
    assert "0 active" in lower, "technical_debt.md should contain '0 active' summary"

    # Check TD-001 RESOLVED present
    assert "RESOLVED" in content, "technical_debt.md should contain RESOLVED entry"
    # Ensure no new active debt introduced — if file contains active table rows not resolved,
    # we check that summary says 0 active and no ACTIVE status besides resolved
    # Simple heuristic: count ACTIVE status that is not RESOLVED in table?
    # For now, rely on 0 active summary as per pseudocode
    # Additional: ensure file mentions isolation verification or Task 7 or no debt
    # (from Phase 1) — but for Phase 2 we just need 0 active
    assert "active" in lower, "technical_debt.md should mention active debt summary"


# ---------------------------------------------------------------------------
# Test: test_no_pygame_grep — AC-1 secondary
# ---------------------------------------------------------------------------


def test_no_pygame_grep() -> None:
    """AC-1 secondary: grep exact patterns import pygame / from pygame in board.py rules.py __init__.py."""
    for file_path in (BOARD_PY, RULES_PY, INIT_PY):
        assert file_path.exists(), f"{file_path} not found"
        content = file_path.read_text(encoding="utf-8")
        # Exact substring search per pseudocode — any occurrence FAIL to be safe
        assert "import pygame" not in content, f"'import pygame' found in {file_path.name}"
        assert "from pygame" not in content, f"'from pygame' found in {file_path.name}"
