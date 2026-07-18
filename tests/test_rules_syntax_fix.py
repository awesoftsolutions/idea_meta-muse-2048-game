"""
tests/test_rules_syntax_fix.py — Syntax fix verification for rules.py duplicate docstring.

Headless, pure Python, no pygame, deterministic, no DISPLAY.
Covers AC-1 to AC-5 per pseudocode phase_1_sprint_1_task_rules_fix_code.md:

AC-1: Exactly one module docstring exists covering lines 1-32 merged
AC-2: Merged content preserves both intents (short header + detailed Purpose/System/etc)
AC-3: Future import immediately after docstring before typing and board imports
AC-4: No pygame import remains
AC-5: py_compile succeeds no F404/E402
AC-6: Covered by tests/test_rules.py (10 functional tests)

This file is expected to FAIL in red phase before fix and PASS after fix.
"""

from __future__ import annotations

import ast
import py_compile
import sys
from pathlib import Path
from typing import List


RULES_PATH = Path(__file__).parent.parent / "src" / "core" / "rules.py"


def _read_rules_source() -> str:
    return RULES_PATH.read_text(encoding="utf-8")


def _get_module_docstring_nodes() -> List[ast.Expr]:
    """Return top-level string expression nodes before first import."""
    source = _read_rules_source()
    tree = ast.parse(source)
    docstring_exprs: List[ast.Expr] = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                docstring_exprs.append(node)
                continue
        # Stop at first import or non-docstring statement
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        # If we encounter a non-string expr, continue scanning for docstring count
        # but for duplicate detection we count all leading string literals
        if isinstance(node, ast.Expr):
            # Non-string expr would break docstring chain, but we still count
            continue
        # Any other statement ends leading docstring region
        if docstring_exprs:
            break
    return docstring_exprs


def test_py_compile_succeeds() -> None:
    """AC-1, AC-5: py_compile must succeed (no syntax error from duplicate docstring)."""
    # py_compile will raise if syntax invalid; duplicate docstrings are valid Python
    # but we check it compiles
    try:
        py_compile.compile(str(RULES_PATH), doraise=True)
    except py_compile.PyCompileError as exc:
        raise AssertionError(f"py_compile failed for {RULES_PATH}: {exc}") from exc


def test_single_module_docstring_count() -> None:
    """AC-1: Exactly one module docstring exists covering lines 1-32 merged."""
    source = _read_rules_source()
    tree = ast.parse(source)

    # Count leading string literals at module top
    leading_strings = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                leading_strings += 1
                continue
        # Stop counting after first non-string-leading region
        # But we need to detect duplicate: two consecutive string literals at top
        if leading_strings > 0 and not isinstance(node, ast.Expr):
            break
        if leading_strings == 0 and isinstance(node, (ast.Import, ast.ImportFrom)):
            break

    # More precise: count all Expr(Constant(str)) at very start before imports
    # Re-parse with explicit scan
    count = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                count += 1
                continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            break
        if count > 0:
            # After first docstring, any other statement ends docstring region
            # If it's another string, it's duplicate
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    count += 1
            break

    # Alternative robust check: read file and count triple-quoted blocks at top
    # For this test, we assert exactly 1 leading docstring
    assert count == 1, (
        f"Expected exactly 1 module docstring, found {count}. "
        f"File likely has duplicate docstrings (red phase). Source start:\n{source[:500]}"
    )

    # Also verify ast.get_docstring returns something
    doc = ast.get_docstring(tree)
    assert doc is not None, "Module docstring missing"
    assert len(doc) > 20, "Module docstring too short, expected merged content"


def test_merged_content_preserves_both_intents() -> None:
    """AC-2: Merged docstring preserves both intents."""
    source = _read_rules_source()
    tree = ast.parse(source)
    doc = ast.get_docstring(tree)
    assert doc is not None, "Module docstring missing, cannot verify merged content"

    # Short header intent from original first docstring
    assert "IRules" in doc or "is_legal_move" in doc, "Missing short header intent (IRules/is_legal_move)"
    assert "is_game_over" in doc, "Missing is_game_over in merged docstring"

    # Detailed intent keywords from second docstring
    required_keywords = [
        "Purpose:",
        "System:",
        "Dependencies:",
        "Used-by:",
        "Public interface:",
    ]
    for kw in required_keywords:
        assert kw in doc, f"Missing required keyword '{kw}' in merged docstring"

    # Additional checks for headless / no pygame mention or contract details
    assert "is_legal_move" in doc and "is_game_over" in doc, "Public API not described"


def test_future_import_position() -> None:
    """AC-3: Future import immediately after docstring before typing and board."""
    source = _read_rules_source()
    lines = source.splitlines()

    # Find end of first docstring (closing triple quotes)
    # Look for first occurrence of """ at start, then closing """
    in_docstring = False
    docstring_end_line = -1
    triple = '"""'
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not in_docstring:
            if stripped.startswith(triple):
                # Could be single line docstring
                if stripped.count(triple) >= 2 and len(stripped) > 3:
                    # Single line """..."""
                    in_docstring = False
                    docstring_end_line = idx
                    break
                else:
                    in_docstring = True
                    # Check if same line closes (not likely for module docstring)
                    # Continue
        else:
            if triple in line:
                docstring_end_line = idx
                break

    assert docstring_end_line != -1, "Could not find end of module docstring"

    # Find next non-empty, non-comment line after docstring
    next_code_line_idx = -1
    next_code_line = ""
    for j in range(docstring_end_line + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        next_code_line_idx = j
        next_code_line = stripped
        break

    assert next_code_line_idx != -1, "No code after docstring"
    assert "from __future__ import annotations" in next_code_line, (
        f"Expected 'from __future__ import annotations' immediately after docstring, "
        f"found at line {next_code_line_idx+1}: '{next_code_line}'. "
        f"Lines after docstring: {lines[docstring_end_line+1:docstring_end_line+5]}"
    )


def test_import_ordering() -> None:
    """AC-3: Import ordering typing then board after future import."""
    source = _read_rules_source()
    tree = ast.parse(source)

    imports: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

    # Must have future, typing, src.core.board in order
    assert "__future__" in imports, "Missing __future__ import"
    assert "typing" in imports, "Missing typing import"
    # Check board import present
    board_found = any("board" in imp for imp in imports)
    assert board_found, f"Missing board import, found imports: {imports}"

    # Order check
    future_idx = imports.index("__future__")
    typing_idx = imports.index("typing")
    # Find board index
    board_idx = -1
    for i, imp in enumerate(imports):
        if "board" in imp:
            board_idx = i
            break

    assert future_idx < typing_idx < board_idx, (
        f"Import order incorrect: expected __future__ < typing < board, "
        f"got indices future={future_idx}, typing={typing_idx}, board={board_idx}, "
        f"order={imports}"
    )


def test_no_pygame_import() -> None:
    """AC-4: No pygame import remains (import statement, not docstring mention)."""
    source = _read_rules_source()
    tree = ast.parse(source)

    # Check AST imports only - docstring may mention "no pygame" which is allowed
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "pygame" not in alias.name.lower(), f"Found pygame import: {alias.name}"
        if isinstance(node, ast.ImportFrom):
            if node.module and "pygame" in node.module.lower():
                raise AssertionError(f"Found pygame import from: {node.module}")

    # Also check raw source for import lines containing pygame (not comments/docstring)
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "pygame" not in stripped.lower(), f"Found pygame import line: {stripped}"

    # Runtime check via sys.modules after import
    assert "pygame" not in sys.modules, "pygame should not be in sys.modules before import"
    try:
        import src.core.rules  # noqa: F401

        assert "pygame" not in sys.modules, "src.core.rules must not import pygame"
    except (ModuleNotFoundError, SyntaxError):
        # Red phase: module may have SyntaxError due to duplicate docstring
        assert "pygame" not in sys.modules


def test_lint_f404_e402_clean() -> None:
    """AC-5: No F404/E402 - future import at beginning, imports at top."""
    source = _read_rules_source()
    lines = source.splitlines()

    # F404: from __future__ must be at beginning of file (after docstring only)
    # E402: module level import not at top of file

    # Find first import line
    first_import_line = -1
    future_import_line = -1
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from __future__ import"):
            future_import_line = idx
            if first_import_line == -1:
                first_import_line = idx
        elif stripped.startswith("from ") or stripped.startswith("import "):
            if first_import_line == -1 and "from __future__" not in stripped:
                first_import_line = idx

    assert future_import_line != -1, "Missing future import"

    # Future import must be within first 35 lines (after single merged docstring)
    # Original broken file had it at line 34 due to duplicate docstring (32 lines)
    # Fixed file should have it much earlier, e.g., line 2-30 range but after docstring
    # We check it's before line 32 (merged docstring should be ~32 lines max, but future right after)
    # Actually merged docstring covering lines 1-32 means future at line 33 or earlier?
    # Per AC-3: future immediately after docstring. So if docstring is 32 lines, future at 33.
    # But we want to ensure it's not at 34 due to duplicate. So check <=33 and >0
    # More robust: ensure no string literal after future import before other imports
    # i.e., only one docstring before future

    # Check no module-level string literal between future and typing imports
    tree = ast.parse(source)
    found_future = False
    string_after_future = False
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            found_future = True
            continue
        if found_future:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    string_after_future = True
                    break
            # Stop after first non-future import
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                break

    assert not string_after_future, (
        "Found string literal after future import - indicates duplicate docstring "
        "still present (second docstring after future import). F404/E402 would trigger."
    )

    # Also verify future import is first import
    assert future_import_line <= 35, (
        f"Future import at line {future_import_line+1} too far down, "
        f"expected immediately after single merged docstring (<=35). "
        f"Duplicate docstring likely still present."
    )
