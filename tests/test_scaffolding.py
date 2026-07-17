"""
Scaffolding verification tests for Task 1 - TDD red phase.

Tests file inspection and integration per pseudocode TDD Test Structure.
Three groups: dependency declaration, poetry check integration, layout verification.
All tests non-interactive, use pathlib and subprocess, exit on own.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def _read_pyproject() -> str:
    """Read pyproject.toml content or raise if missing."""
    path = pathlib.Path("pyproject.toml")
    assert path.exists(), "pyproject.toml does not exist - scaffolding not created yet"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test group: dependency declaration via file inspection - covers AC-1
# ---------------------------------------------------------------------------


def test_pyproject_declares_python_version() -> None:
    """Verify pyproject.toml declares python ^3.11 per architecture config."""
    content = _read_pyproject()
    assert "python" in content.lower(), "python dependency not found in pyproject.toml"
    assert "^3.11" in content, (
        "python ^3.11 not declared - expected ^3.11 per architecture config"
    )


def test_pyproject_declares_pygame_ce() -> None:
    """Verify pyproject.toml declares pygame-ce ^2.5.0 exact name."""
    content = _read_pyproject()
    assert "pygame-ce" in content, (
        "pygame-ce not declared - check exact name pygame-ce not pygame per ADR-001"
    )
    assert "^2.5.0" in content, "pygame-ce ^2.5.0 not declared per architecture config"


def test_pyproject_declares_pyinstaller() -> None:
    """Verify pyproject.toml declares PyInstaller ^6.0 case-sensitive."""
    content = _read_pyproject()
    # Case-sensitive check per pseudocode edge case
    assert "PyInstaller" in content, (
        "PyInstaller not declared - case-sensitive PyInstaller required"
    )
    assert "^6.0" in content, "PyInstaller ^6.0 not declared per architecture config"


def test_pyproject_declares_pytest() -> None:
    """Verify pyproject.toml declares pytest ^8.0."""
    content = _read_pyproject()
    assert "pytest" in content, "pytest not declared in pyproject.toml"
    assert "^8.0" in content, "pytest ^8.0 not declared per architecture config"


# ---------------------------------------------------------------------------
# Test group: poetry check integration - covers AC-2
# ---------------------------------------------------------------------------


def test_poetry_check_passes() -> None:
    """Run poetry check and assert exit code 0, no errors."""
    result = subprocess.run(
        ["poetry", "check"],
        capture_output=True,
        text=True,
        cwd=pathlib.Path.cwd(),
    )
    # Log output for debugging if fails
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}", file=sys.stderr)
        print(f"STDERR: {result.stderr}", file=sys.stderr)
    assert result.returncode == 0, (
        f"poetry check failed with exit code {result.returncode}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert (
        "error" not in combined or "no error" in combined or result.returncode == 0
    ), f"poetry check output contains error: {result.stdout} {result.stderr}"
    assert "invalid" not in combined, (
        f"poetry check invalid TOML: {result.stdout} {result.stderr}"
    )


# ---------------------------------------------------------------------------
# Test group: layout verification - covers AC-3 and AC-4
# ---------------------------------------------------------------------------


def test_src_init_exists() -> None:
    """Verify src/__init__.py exists as package marker."""
    path = pathlib.Path("src/__init__.py")
    assert path.exists(), "src/__init__.py does not exist - required per SOW structure"
    # Allow empty or whitespace/comments only per pseudocode
    content = path.read_text(encoding="utf-8").strip()
    if content:
        # If non-empty, ensure no executable code beyond comments
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            assert line.startswith("#") or not line, (
                f"src/__init__.py should be empty marker, found code: {line}"
            )


def test_src_core_init_exists() -> None:
    """Verify src/core/__init__.py exists as package marker."""
    path = pathlib.Path("src/core/__init__.py")
    assert path.exists(), (
        "src/core/__init__.py does not exist - required for board spike"
    )
    # Size check - should be empty marker
    content = path.read_text(encoding="utf-8").strip()
    if content:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            assert line.startswith("#") or not line, (
                f"src/core/__init__.py should be empty marker, found: {line}"
            )


def test_tests_init_exists() -> None:
    """Verify tests/__init__.py exists as package marker."""
    path = pathlib.Path("tests/__init__.py")
    assert path.exists(), (
        "tests/__init__.py does not exist - required for pytest discovery"
    )


def test_gitignore_contains_required() -> None:
    """Verify .gitignore contains dist/, __pycache__, .venv, .favur/ per AC-4."""
    path = pathlib.Path(".gitignore")
    assert path.exists(), ".gitignore does not exist"
    content = path.read_text(encoding="utf-8")
    assert "dist/" in content, ".gitignore missing dist/ entry - must not be removed"
    assert "__pycache__" in content, ".gitignore missing __pycache__ entry"
    assert ".venv" in content, ".gitignore missing .venv entry"
    assert ".favur/" in content, ".gitignore missing .favur/ entry per kickoff"


def test_no_out_of_scope_artifacts() -> None:
    """Negative checks per ADR-007 - no render, no production core modules."""
    src_path = pathlib.Path("src")
    if src_path.exists():
        assert not (src_path / "render").exists(), (
            "src/render/ should NOT exist in Phase 1 per ADR-007 - out of scope"
        )
        assert not (src_path / "core" / "rules.py").exists(), (
            "src/core/rules.py should NOT exist - belongs to Phase 2"
        )
        assert not (src_path / "core" / "score.py").exists(), (
            "src/core/score.py should NOT exist - belongs to Phase 2"
        )
        assert not (src_path / "core" / "history.py").exists(), (
            "src/core/history.py should NOT exist - belongs to Phase 2"
        )
        assert not (src_path / "core" / "achievements.py").exists(), (
            "src/core/achievements.py should NOT exist - belongs to Phase 2"
        )
        assert not (src_path / "core" / "twist.py").exists(), (
            "src/core/twist.py should NOT exist - belongs to Phase 2"
        )
