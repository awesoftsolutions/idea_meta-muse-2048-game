"""
tests/test_board_build_fix.py — Build verification for board.py duplicate docstring fix.

Red phase documentation:
- Current src/core/board.py contains two module docstrings at lines 1-11 and 13-49,
  pushing `from __future__ import annotations` to line 51.
- This violates Python spec: future imports must be at beginning after docstring.
- Expected failure before fix: `python -m py_compile src/core/board.py` exits 1
  with SyntaxError: from __future__ imports must occur at the beginning of the file.
- Lint reports F404 future import not at beginning and E402 import not at top.
- This file's tests use file content inspection, AST parsing, and subprocess
  to avoid importing the broken module during red phase, ensuring tests are
  runnable even when board.py fails py_compile.

After fix:
- Single merged docstring at top, future import immediately after, py_compile exit 0,
  no F404/E402, no pygame, allowed imports only, pytest green, headless importable.

AC mapping:
- AC-1: test_single_docstring_count
- AC-2: test_merged_content_contains_both
- AC-3: test_future_import_position
- AC-4: test_py_compile_exit_0
- AC-5: test_pytest_green, test_board_importable_headless
- AC-6: test_no_pygame_import, test_allowed_imports_only
- AC-7: test_no_F404_E402
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

BOARD_PATH = Path("src/core/board.py")
ALLOWED_IMPORTS = {"__future__", "math", "random", "dataclasses", "enum", "typing", "copy"}
FORBIDDEN_IMPORTS = {"pygame", "pygame-ce", "pygame_ce"}


def _read_board_content() -> str:
    """Read board.py content.

    Returns:
        File content as string.
    """
    return BOARD_PATH.read_text(encoding="utf-8")


def _get_module_docstring_via_ast(content: str) -> str | None:
    """Extract module docstring via AST if parsable, else None.

    Args:
        content: File content.

    Returns:
        Docstring or None if AST fails.
    """
    try:
        tree = ast.parse(content)
        return ast.get_docstring(tree)
    except SyntaxError:
        return None


# ---------------------------------------------------------------------------
# Test Group 1: Syntax and Build Verification (AC-4, AC-3, AC-7)
# ---------------------------------------------------------------------------


def test_py_compile_exit_0() -> None:
    """AC-4: py_compile src/core/board.py exits 0 with no SyntaxError.

    Uses subprocess to avoid importing broken module.
    """
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(BOARD_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"py_compile failed exit {result.returncode}: "
        f"stdout={result.stdout} stderr={result.stderr}"
    )


def test_future_import_position() -> None:
    """AC-3: Future import immediately after docstring before other imports."""
    content = _read_board_content()
    lines = content.splitlines()

    # Find docstring end via AST if possible, else heuristic
    docstring_end_line = -1
    try:
        tree = ast.parse(content)
        # If AST parses, future import must be at top - find its line
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                # Check it's first non-docstring statement
                # Find first statement that is not Expr (docstring)
                first_non_docstring_idx = 0
                for idx, stmt in enumerate(tree.body):
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                        # docstring
                        continue
                    first_non_docstring_idx = idx
                    break
                # Future import should be at first_non_docstring_idx
                assert isinstance(tree.body[first_non_docstring_idx], ast.ImportFrom)
                assert tree.body[first_non_docstring_idx].module == "__future__"
                break
        # Also check line positions via text
        for i, line in enumerate(lines):
            if "from __future__ import annotations" in line:
                docstring_end_line = i
                break
    except SyntaxError:
        # Red phase: AST fails, check raw line position
        for i, line in enumerate(lines):
            if "from __future__ import annotations" in line:
                docstring_end_line = i
                break
        # In red phase this will be line 50 (0-indexed) = line 51
        # After fix it should be early (line 2-5)
        # We assert it exists and is before other imports
        assert docstring_end_line != -1, "Future import not found"

    assert docstring_end_line != -1, "from __future__ import annotations not found"

    # Future import should be immediately after merged docstring.
    # Merged docstring is ~46 lines, so future import at line 48 is expected.
    # Allow up to 60 to account for longer merged docstring, but must be <60.
    assert docstring_end_line < 60, (
        f"Future import at line {docstring_end_line + 1} too far down, "
        f"expected within first 60 lines after single merged docstring"
    )

    # Ensure no code (except docstring/comments/blank) before future import
    import_pattern = re.compile(r"^\s*(import\s+\w+|from\s+\w+\s+import)")
    for idx, line in enumerate(lines[:docstring_end_line]):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        # Inside docstring? Skip if we are within triple quotes
        # Heuristic: if line contains only docstring content, skip
        if import_pattern.match(line):
            # Allow only if it's future import (but we are before it, so none should exist)
            if "__future__" in line:
                continue
            assert False, f"Found import before future import at line {idx + 1}: {line}"


def test_no_F404_E402() -> None:
    """AC-7: No F404 future import not at beginning and no E402 import not at top.

    Verifies via AST position and manual check, plus flake8 if available.
    """
    content = _read_board_content()
    lines = content.splitlines()

    # Manual F404 check: future import must be first statement after docstring
    future_line_idx = None
    for i, line in enumerate(lines):
        if "from __future__ import annotations" in line:
            future_line_idx = i
            break
    assert future_line_idx is not None, "Future import missing"

    # Check no non-docstring, non-comment, non-blank code before future import
    in_docstring = False
    docstring_delim = None
    for i in range(future_line_idx):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Track triple-quoted docstring
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                delim = '"""' if '"""' in stripped else "'''"
                # Count occurrences
                count = stripped.count(delim)
                if count == 1:
                    in_docstring = True
                    docstring_delim = delim
                elif count >= 2:
                    # Single line docstring or start+end same line
                    # If it's opening and closing on same line, not entering
                    # Heuristic: if line is exactly docstring start, check if ends later
                    # For simplicity, if count==2 and line != delim, it's a complete docstring
                    pass
                continue
        else:
            if docstring_delim and docstring_delim in line:
                in_docstring = False
            continue
        # If we are here and not in docstring, it's code before future import -> F404/E402
        # Allow only blank/comments/docstring
        if stripped and not stripped.startswith("#"):
            # If it's inside docstring we already skipped, so this is violation
            # But need to ensure we didn't miss docstring detection
            # For merged docstring, everything before future import should be docstring
            # So any import or code here is violation
            if re.match(r"^\s*(import|from|class|def|@)", line):
                assert False, f"F404/E402 violation: code before future import at line {i + 1}: {line}"

    # Try flake8 if installed
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(BOARD_PATH), "--select=F404,E402"],
            capture_output=True,
            text=True,
        )
        # flake8 returns 0 if no errors, 1 if errors found
        assert result.stdout.strip() == "", (
            f"Flake8 F404/E402 found: {result.stdout} {result.stderr}"
        )
    except FileNotFoundError:
        # flake8 not installed, manual check above suffices
        pass


# ---------------------------------------------------------------------------
# Test Group 2: Docstring Merge Verification (AC-1, AC-2)
# ---------------------------------------------------------------------------


def test_single_docstring_count() -> None:
    """AC-1: Exactly one module docstring at top, no second stray."""
    content = _read_board_content()

    # Count top-level triple-quoted strings at beginning via AST if parsable
    try:
        tree = ast.parse(content)
        # Count Expr nodes at module level that are string constants at top
        docstring_count = 0
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    docstring_count += 1
                else:
                    break
            else:
                break
        assert docstring_count == 1, f"Expected exactly 1 module docstring, found {docstring_count}"
    except SyntaxError:
        # Red phase: AST fails due to future import position
        # Fallback: count triple-quoted blocks at start of file
        # Expect 2 in red phase, 1 after fix
        # For this test to pass after fix, we expect 1 block
        # During red phase this test will FAIL, which is expected TDD red
        first_100_lines = "\n".join(content.splitlines()[:100])
        # Count """ occurrences
        count_delim = first_100_lines.count('"""')
        # Each docstring has 2 delimiters
        num_docstrings = count_delim // 2
        assert num_docstrings == 1, (
            f"Expected 1 module docstring at top, found {num_docstrings} "
            f"(delim count {count_delim}). Red phase has 2 docstrings."
        )


def test_merged_content_contains_both() -> None:
    """AC-2: Merged docstring contains both original and verification contract info."""
    content = _read_board_content()
    docstring = _get_module_docstring_via_ast(content)

    if docstring is None:
        # Red phase fallback: extract first docstring via text
        # Find first """...""" block
        match = re.search(r'"""(.*?)"""', content, re.DOTALL)
        assert match is not None, "No docstring found"
        # For red phase, we have two docstrings, need to check both contain keywords
        # Combine first 2000 chars for keyword search
        combined = content[:3000].lower()
        docstring_lower = combined
    else:
        docstring_lower = docstring.lower()

    # Required keywords from pseudocode: Tile, slide/merge, RNG, headless, 5x5, heat
    keywords = {
        "tile": "Tile dataclass",
        "slide": "slide/merge",
        "rng": "injectable RNG",
        "headless": "headless",
        "5x5": "5x5 board",
        "heat": "heat",
    }
    found = []
    missing = []
    for key, desc in keywords.items():
        if key in docstring_lower:
            found.append(desc)
        else:
            missing.append(desc)

    assert len(found) >= 4, (
        f"Merged docstring should contain at least 4 of 6 key phrases {list(keywords.values())}, "
        f"found {found}, missing {missing}. Docstring: {docstring_lower[:500]}"
    )


# ---------------------------------------------------------------------------
# Test Group 3: Import Compliance (AC-6)
# ---------------------------------------------------------------------------


def test_no_pygame_import() -> None:
    """AC-6: No pygame import — headless requirement.

    Checks import statements only, not docstring mentions of pygame-ce
    which are allowed as documentation about forbidden dependencies.
    """
    content = _read_board_content()
    # Check for actual import statements, not docstring mentions
    import_pattern = re.compile(r"^\s*(import\s+pygame|from\s+pygame)", re.MULTILINE)
    assert not import_pattern.search(content), "Found pygame import statement in board.py"
    # Also check for import lines containing pygame
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "pygame" not in stripped.lower(), f"Found pygame in import line: {line}"
    # Also check sys.modules if board already imported
    try:
        import sys

        assert "pygame" not in sys.modules, "pygame in sys.modules"
    except Exception:
        pass


def test_allowed_imports_only() -> None:
    """AC-6: Only allowed stdlib imports present."""
    content = _read_board_content()
    try:
        tree = ast.parse(content)
        imports_found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    imports_found.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    imports_found.add(root)
        # Filter out allowed
        disallowed = imports_found - ALLOWED_IMPORTS
        # Also check forbidden explicitly
        forbidden_found = imports_found & FORBIDDEN_IMPORTS
        assert not forbidden_found, f"Forbidden imports found: {forbidden_found}"
        assert not disallowed, (
            f"Disallowed imports found: {disallowed}, allowed only {ALLOWED_IMPORTS}"
        )
    except SyntaxError:
        # Red phase: AST fails, fallback to regex import scan
        import_lines = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_\-]*)", content, re.MULTILINE)
        found = set(import_lines)
        forbidden_found = found & FORBIDDEN_IMPORTS
        assert not forbidden_found, f"Forbidden imports in red phase fallback: {forbidden_found}"
        disallowed = found - ALLOWED_IMPORTS
        # In red phase, disallowed should still be empty because file has only allowed imports
        assert not disallowed, f"Disallowed imports in fallback: {disallowed}"


# ---------------------------------------------------------------------------
# Test Group 4: Regression — Existing Board Logic Unchanged (AC-5)
# ---------------------------------------------------------------------------


def test_board_importable_headless() -> None:
    """AC-5/6: Board importable headlessly without display dependency."""
    # Use subprocess to test headless import in clean process
    code = (
        "from src.core.board import Board, Tile, Direction, MergeInfo, SlideResult, BOARD_SIZE; "
        "import random; "
        "rng=random.Random(42); "
        "b=Board(rng=rng); "
        "assert b.size==5; "
        "assert BOARD_SIZE==5; "
        "print('import OK')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Headless import failed: stdout={result.stdout} stderr={result.stderr}"
    )
    assert "import OK" in result.stdout


def test_pytest_green() -> None:
    """AC-5: Existing board tests still pass after syntax fix.

    Runs pytest on tests/test_board.py in subprocess to avoid import issues in red phase.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_board.py", "-v", "--tb=short", "-q"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"pytest tests/test_board.py failed exit {result.returncode}: "
        f"stdout={result.stdout[-2000:]} stderr={result.stderr[-2000:]}"
    )
