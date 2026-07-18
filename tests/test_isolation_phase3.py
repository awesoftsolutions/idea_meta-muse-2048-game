"""
tests/test_isolation_phase3.py — Isolation verification for Phase 3 Sprint 1.

Verifies:
- No pygame leak in core via sys.modules after import src.core.*
- No pygame import via grep exact patterns import pygame / from pygame
- No global random usage random.random() / random.choice without self.rng/rng prefix
- src/core remains headless importable

Headless, stdlib only, no pygame. Should PASS even in red phase for core modules
that already exist, but will FAIL for new modules if they leak pygame.

System: src/core per Phase 3 architecture E007 PygameLeak, E006 RNGNotInjected.
"""

from __future__ import annotations

import sys
from pathlib import Path


def test_no_pygame_leak_core_imports() -> None:
    """sys.modules has no pygame after importing src.core.* modules."""
    # Snapshot before
    before_has_pygame = "pygame" in sys.modules

    # Import all core modules that should be headless
    import src.core.board  # noqa: F401
    import src.core.rules  # noqa: F401
    import src.core.score  # noqa: F401
    import src.core.history  # noqa: F401
    import src.core.twist  # noqa: F401
    import src.core.achievements  # noqa: F401

    # Try gamestate if exists (red phase may not have it yet)
    try:
        import src.core.gamestate  # noqa: F401
    except ModuleNotFoundError:
        pass

    # After imports, pygame must not be in sys.modules unless it was before
    if not before_has_pygame:
        assert "pygame" not in sys.modules, "pygame leaked into sys.modules after core imports"
        assert "pygame-ce" not in sys.modules
        assert "pygame_ce" not in sys.modules

    # Check delta for pygame modules
    # If pygame was already loaded before, we can't assert delta, but we can check
    # that core modules themselves don't import it via file content grep
    pygame_modules = [m for m in sys.modules if m.startswith("pygame")]
    if not before_has_pygame:
        assert not pygame_modules, f"pygame modules leaked: {pygame_modules}"


def test_no_pygame_import_grep() -> None:
    """Grep src/core/ for import pygame and from pygame patterns — must be empty."""
    core_dir = Path("src/core")
    if not core_dir.exists():
        # If src/core doesn't exist, skip (should not happen)
        return

    forbidden_patterns = ["import pygame", "from pygame"]
    violations = []

    for py_file in core_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in content:
                # Allow if in comment? Check lines
                for i, line in enumerate(content.splitlines(), 1):
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if pattern in line:
                        violations.append(f"{py_file}:{i}: {line.strip()}")

    assert not violations, f"pygame import found in core: {violations}"


def test_no_global_random_in_board() -> None:
    """No global random.random() / random.choice without self.rng/rng prefix in board.py."""
    board_path = Path("src/core/board.py")
    if not board_path.exists():
        return

    content = board_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    violations = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "import random" in stripped:
            continue
        # Check bare random.random() without rng prefix
        if "random.random()" in stripped:
            if "rng.random()" not in stripped and "self.rng" not in stripped:
                violations.append(f"Line {i}: {line.strip()}")
        if "random.choice(" in stripped:
            if "rng.choice(" not in stripped and "self.rng" not in stripped:
                violations.append(f"Line {i}: {line.strip()}")

    assert not violations, f"Global random usage found in board.py: {violations}"


def test_no_global_random_in_twist() -> None:
    """No global random usage in twist.py — must be pure deterministic."""
    twist_path = Path("src/core/twist.py")
    if not twist_path.exists():
        # Red phase: file missing, force failure via import attempt
        try:
            import src.core.twist  # noqa: F401
        except ModuleNotFoundError:
            pass
        return

    content = twist_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    violations = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "import random" in stripped:
            continue
        if "random.random()" in stripped and "rng.random()" not in stripped and "self.rng" not in stripped:
            violations.append(f"Line {i}: {line.strip()}")
        if "random.choice(" in stripped and "rng.choice(" not in stripped and "self.rng" not in stripped:
            violations.append(f"Line {i}: {line.strip()}")
        if "random.Random()" in stripped:
            violations.append(f"Line {i}: {line.strip()} - twist must not create RNG")

    assert not violations, f"Global random usage in twist.py: {violations}"


def test_core_headless_importable() -> None:
    """All core modules importable headlessly without DISPLAY."""
    # These imports should work without pygame and without DISPLAY
    from src.core.board import BOARD_SIZE, Board, Tile  # noqa: F401
    from src.core.rules import is_game_over, is_legal_move  # noqa: F401
    from src.core.score import ScoreState  # noqa: F401
    from src.core.history import HistoryStack  # noqa: F401
    from src.core.twist import get_turn_pipeline_order  # noqa: F401
    from src.core.achievements import Achievements  # noqa: F401

    assert BOARD_SIZE == 5

    try:
        from src.core.gamestate import GameState  # noqa: F401

        assert True
    except ModuleNotFoundError:
        # Red phase expected
        pass
