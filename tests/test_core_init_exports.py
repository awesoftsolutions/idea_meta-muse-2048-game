"""
tests/test_core_init_exports.py — TDD red-phase tests for __all__ restoration in src/core/__init__.py.

Purpose: Verify __all__ restoration per pseudocode phase_2_sprint_1_task_all_restoration.md.
Ensures src/core facade re-exports 11 symbols (9 board + 2 rules), no pygame leak,
F401 resolved, file structure clean.

AC mapping:
- AC-1 __all__ presence in file -> test_all_presence_contains_11_symbols
- AC-2 Exact __all__ list 11 symbols -> test_all_presence_contains_11_symbols
- AC-3 Runtime importable from src.core -> test_runtime_import_all_11_symbols
- AC-4 No pygame in sys.modules -> test_no_pygame_leak_after_core_import
- AC-7 F401 resolved (__all__ references all imports) -> test_f401_all_imports_in_all
- Edge: duplicate docstring / newline -> test_file_structure_no_duplicate_docstring

Headless, no DISPLAY required. stdlib only + src.core. No pygame import in this file.
"""

from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
SRC_CORE = SRC_DIR / "core"
BOARD_PY = SRC_CORE / "board.py"
RULES_PY = SRC_CORE / "rules.py"
INIT_PY = SRC_CORE / "__init__.py"

REQUIRED_SYMBOLS = [
    "Tile",
    "Board",
    "Direction",
    "SlideResult",
    "MergeInfo",
    "BOARD_SIZE",
    "HEAT_MIN",
    "HEAT_MAX",
    "create_empty_grid",
    "is_legal_move",
    "is_game_over",
]

BOARD_SYMBOLS = [
    "Tile",
    "Board",
    "Direction",
    "SlideResult",
    "MergeInfo",
    "BOARD_SIZE",
    "HEAT_MIN",
    "HEAT_MAX",
    "create_empty_grid",
]

RULES_SYMBOLS = ["is_legal_move", "is_game_over"]


# ---------------------------------------------------------------------------
# Helpers (mirrors test_isolation_phase2.py)
# ---------------------------------------------------------------------------


def _assert_no_pygame_in_modules(modules_snapshot: set[str], context: str) -> None:
    """Assert no pygame key in given sys.modules snapshot."""
    assert "pygame" not in modules_snapshot, f"{context}: 'pygame' found in sys.modules"
    pygame_keys = [k for k in modules_snapshot if k == "pygame" or k.startswith("pygame.")]
    assert not pygame_keys, f"{context}: pygame keys found in sys.modules: {pygame_keys}"


def _assert_no_pygame_in_delta(
    before: set[str], after: set[str], context: str
) -> None:
    """Delta check: if pygame already present before, only check new keys."""
    delta = after - before
    pygame_delta = [k for k in delta if k == "pygame" or k.startswith("pygame.")]
    assert not pygame_delta, f"{context}: new pygame keys in delta: {pygame_delta}"
    if "pygame" not in before:
        _assert_no_pygame_in_modules(after, context)


def _extract_all_list(content: str) -> list[str]:
    """Extract __all__ list via ast, fallback to regex."""
    try:
        tree = ast.parse(content)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            result: list[str] = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(
                                    elt.value, str
                                ):
                                    result.append(elt.value)
                            if result:
                                return result
    except SyntaxError:
        pass
    # Fallback regex: find __all__ = [ ... ]
    match = re.search(r"__all__\s*=\s*\[([^\]]+)\]", content, re.DOTALL)
    if match:
        inner = match.group(1)
        # extract quoted strings
        return re.findall(r"[\"']([^\"']+)[\"']", inner)
    return []


def _extract_imported_names(content: str) -> list[str]:
    """Extract names imported via from .board import ... and from .rules import ..."""
    names: list[str] = []
    # Find all from .board / .rules import lines (single or multi-line)
    # Simplify: regex for from .board import (...) or single line
    pattern = r"from\s+\.(?:board|rules)\s+import\s+(?:\(?([^\)]+)\)?|([^\n]+))"
    for m in re.finditer(pattern, content, re.DOTALL):
        group = m.group(1) or m.group(2) or ""
        # split by comma and strip
        for part in group.split(","):
            part = part.strip()
            # handle "as" alias - take first token
            if not part:
                continue
            # remove parentheses, newlines
            part = part.replace("(", "").replace(")", "").strip()
            if not part:
                continue
            # split on ' as '
            base = part.split(" as ")[0].strip()
            if base:
                # further split by whitespace/newline
                for token in re.split(r"\s+", base):
                    token = token.strip().strip(",")
                    if token and token not in names:
                        names.append(token)
    # Clean: filter valid identifiers
    cleaned = [n for n in names if n.isidentifier()]
    return cleaned


# ---------------------------------------------------------------------------
# Test Case 1: __all__ Presence — AC-1, AC-2
# ---------------------------------------------------------------------------


def test_all_presence_contains_11_symbols() -> None:
    """AC-1/AC-2: __all__ exists in __init__.py and contains 11 required symbols."""
    assert INIT_PY.exists(), f"{INIT_PY} not found"
    content = INIT_PY.read_text(encoding="utf-8")

    # __all__ must exist
    assert "__all__" in content, "__all__ missing in src/core/__init__.py"

    # Each required symbol must appear quoted in __all__
    for sym in REQUIRED_SYMBOLS:
        quoted_double = f'"{sym}"'
        quoted_single = f"'{sym}'"
        assert quoted_double in content or quoted_single in content, (
            f"{sym} missing in __all__ (expected quoted string in file)"
        )

    # Board import must exist
    assert "from .board import" in content, "from .board import missing in __init__.py"

    # Rules import must exist per remediation wave (11 symbols)
    assert "from .rules import" in content, (
        "from .rules import missing in __init__.py per remediation wave (needs is_legal_move, is_game_over)"
    )

    # Verify __all__ list extraction contains all 11
    all_list = _extract_all_list(content)
    assert all_list, "__all__ list could not be parsed or is empty"
    for sym in REQUIRED_SYMBOLS:
        assert sym in all_list, f"{sym} missing in parsed __all__ list {all_list}"

    # Order check: first 9 board then 2 rules per spec (containment already checked, order aids readability)
    # We assert exact order as per pseudocode to catch drift
    expected_order = REQUIRED_SYMBOLS
    assert all_list == expected_order, (
        f"__all__ order mismatch. Expected {expected_order}, got {all_list}"
    )


# ---------------------------------------------------------------------------
# Test Case 2: Runtime Import — AC-3
# ---------------------------------------------------------------------------


def test_runtime_import_all_11_symbols() -> None:
    """AC-3: All 11 symbols importable from src.core at runtime with basic behavior checks."""
    # Import src.core via importlib to ensure fresh
    core_mod = importlib.import_module("src.core")

    missing = [s for s in REQUIRED_SYMBOLS if not hasattr(core_mod, s)]
    assert not missing, f"Missing symbols in src.core module: {missing}"

    # Runtime instantiation checks per pseudocode
    Tile = getattr(core_mod, "Tile")
    tile = Tile(value=2, heat=0)
    assert tile.value == 2, f"Tile value expected 2, got {tile.value}"
    assert tile.heat == 0, f"Tile heat expected 0, got {tile.heat}"

    BOARD_SIZE = getattr(core_mod, "BOARD_SIZE")
    assert BOARD_SIZE == 5, f"BOARD_SIZE expected 5, got {BOARD_SIZE}"

    Direction = getattr(core_mod, "Direction")
    for name in ("UP", "DOWN", "LEFT", "RIGHT"):
        assert hasattr(Direction, name), f"Direction.{name} missing"

    # Rules callables
    is_legal_move = getattr(core_mod, "is_legal_move")
    is_game_over = getattr(core_mod, "is_game_over")
    assert callable(is_legal_move), "is_legal_move should be callable"
    assert callable(is_game_over), "is_game_over should be callable"

    # Also verify import via from src.core import ... syntax
    from src.core import (  # noqa: F401 - runtime check
        BOARD_SIZE as BS,
        HEAT_MAX,
        HEAT_MIN,
        Board,
        Direction as Dir,
        MergeInfo,
        SlideResult,
        Tile as T,
        create_empty_grid,
        is_game_over as igo,
        is_legal_move as ilm,
    )

    assert BS == 5
    assert HEAT_MIN == 0
    assert HEAT_MAX == 3
    assert isinstance(Board, type)
    assert callable(create_empty_grid)
    assert callable(ilm)
    assert callable(igo)


# ---------------------------------------------------------------------------
# Test Case 3: No Pygame Leak — AC-4
# ---------------------------------------------------------------------------


def test_no_pygame_leak_after_core_import() -> None:
    """AC-4: Importing src.core, board, rules must not pull pygame into sys.modules."""
    before = set(sys.modules.keys())

    # Import all three per pseudocode
    importlib.import_module("src.core")
    importlib.import_module("src.core.board")
    importlib.import_module("src.core.rules")

    after = set(sys.modules.keys())

    _assert_no_pygame_in_modules(after, "core import absolute")
    _assert_no_pygame_in_delta(before, after, "core import delta")

    # Grep check: file content must not contain import pygame / from pygame
    for file_path in (BOARD_PY, RULES_PY, INIT_PY):
        assert file_path.exists(), f"{file_path} not found"
        content = file_path.read_text(encoding="utf-8")
        assert "import pygame" not in content, f"'import pygame' found in {file_path.name}"
        assert "from pygame" not in content, f"'from pygame' found in {file_path.name}"


# ---------------------------------------------------------------------------
# Test Case 4: F401 Resolution — AC-7
# ---------------------------------------------------------------------------


def test_f401_all_imports_in_all() -> None:
    """AC-7: Every imported name in __init__.py must appear in __all__ to silence F401."""
    assert INIT_PY.exists(), f"{INIT_PY} not found"
    content = INIT_PY.read_text(encoding="utf-8")

    imported_names = _extract_imported_names(content)
    assert imported_names, "No imported names found in __init__.py (expected board + rules imports)"

    all_list = _extract_all_list(content)
    assert all_list, "__all__ missing or empty, cannot resolve F401"

    # Every imported name must be in __all__ with exact spelling
    for name in imported_names:
        assert name in all_list, (
            f"Imported name '{name}' not in __all__ {all_list} — F401 would remain"
        )

    # Also ensure __all__ does not contain extra unknown symbols beyond required + imported
    # (allow only required symbols)
    for sym in all_list:
        assert sym in REQUIRED_SYMBOLS, (
            f"Unexpected symbol '{sym}' in __all__ not in required list {REQUIRED_SYMBOLS}"
        )

    # Ensure no unused import would remain: count check
    assert len(all_list) == len(REQUIRED_SYMBOLS), (
        f"__all__ length {len(all_list)} != required {len(REQUIRED_SYMBOLS)}"
    )


# ---------------------------------------------------------------------------
# Test Case 5: File Structure — Edge cases
# ---------------------------------------------------------------------------


def test_file_structure_no_duplicate_docstring() -> None:
    """Edge: __init__.py must have single docstring, no duplicate, ends with newline, no pygame."""
    assert INIT_PY.exists(), f"{INIT_PY} not found"
    content = INIT_PY.read_text(encoding="utf-8")

    # File must end with newline per POSIX
    assert content.endswith("\n"), "__init__.py must end with newline"

    # No duplicate docstring: count triple-quoted blocks at top
    # Simple heuristic: find all \"\"\" occurrences before first import
    import_pos = content.find("from .board import")
    if import_pos == -1:
        import_pos = content.find("from .")
    assert import_pos != -1, "No import found in __init__.py"

    before_import = content[:import_pos]
    # Count triple double quotes
    triple_double = before_import.count('"""')
    triple_single = before_import.count("'''")
    # One docstring = 2 triple quotes (open+close) for double, or 2 for single
    # Allow 2 for double-quoted docstring, 0 for single if using double
    # Fail if more than 2 triple double quotes before import (duplicate docstring)
    assert triple_double <= 2, (
        f"Duplicate docstring suspected: {triple_double} triple double quotes before import"
    )
    assert triple_single <= 2, (
        f"Duplicate docstring suspected: {triple_single} triple single quotes before import"
    )
    # Total triple quotes before import should be exactly 2 (one docstring)
    total_triple = triple_double + triple_single
    assert total_triple == 2, (
        f"Expected single docstring (2 triple quotes) before import, got {total_triple}"
    )

    # No pygame import
    assert "import pygame" not in content
    assert "from pygame" not in content

    # No global random import (should be stdlib only + board/rules)
    # __init__.py should not import random directly
    assert "import random" not in content, "__init__.py should not import random"

    # Verify no absolute import from src.core.board inside __init__.py (causes self-reference)
    assert "from src.core.board import" not in content, (
        "Absolute import from src.core.board inside __init__.py causes circular self-reference, use relative"
    )
    assert "from src.core.rules import" not in content, (
        "Absolute import from src.core.rules inside __init__.py causes circular self-reference, use relative"
    )
