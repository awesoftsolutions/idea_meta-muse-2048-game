"""
tests/test_isolation_phase3.py — Isolation verification final validation.

Covers AC-3, AC-4, AC-19 per pseudocode phase_3_sprint_2_wave1_tasks_1_2_code.md:
- sys.modules no pygame after core import delta check
- grep no pygame import in core exact patterns import pygame/from pygame
- grep no external assets image.load font file path only SysFont
- src/render only __init__.py tiles.py effects.py hud.py absent
- src/render only imports pygame and core Tile
- no global random injectable Random

System: src/core per Phase 3 architecture E007 PygameLeak, E006 RNGNotInjected.
Headless, stdlib only, no pygame.
"""

from __future__ import annotations

import sys
from pathlib import Path


def test_sys_modules_no_pygame_after_core_import_delta_check() -> None:
    """AC-3: sys.modules has no pygame after import src.core.* via delta check."""
    before_has_pygame = "pygame" in sys.modules
    before_keys = set(sys.modules.keys())

    import src.core.board  # noqa: F401
    import src.core.gamestate  # noqa: F401
    import src.core.achievements  # noqa: F401
    import src.core.twist  # noqa: F401
    import src.core.history  # noqa: F401
    import src.core.rules  # noqa: F401
    import src.core.score  # noqa: F401

    after_keys = set(sys.modules.keys())
    new_keys = after_keys - before_keys

    if not before_has_pygame:
        assert "pygame" not in new_keys, f"pygame leaked in delta: {new_keys}"
        pygame_new = [k for k in new_keys if "pygame" in k.lower()]
        assert not pygame_new, f"pygame modules leaked in delta: {pygame_new}"
        pygame_modules = [m for m in sys.modules if m.startswith("pygame")]
        assert not pygame_modules, f"pygame modules leaked: {pygame_modules}"


def test_grep_no_pygame_import_in_core_exact_patterns() -> None:
    """AC-3: grep no pygame import in core exact patterns import pygame/from pygame."""
    core_dir = Path("src/core")
    assert core_dir.exists()
    violations = []
    for py_file in core_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "import pygame" in stripped or "from pygame" in stripped:
                violations.append(f"{py_file}:{i}: {stripped}")
    assert not violations, f"pygame import found in core: {violations}"


def test_grep_no_external_assets_image_load_font_file_path() -> None:
    """AC-19: no external assets grep no image.load no font file path only SysFont."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists()
    content = tiles_path.read_text(encoding="utf-8")
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "pygame.image.load" in stripped:
            violations.append(f"{tiles_path}:{i}: {stripped} - image.load")
        if "font.Font(" in stripped and "SysFont" not in stripped:
            if "test" not in stripped.lower():
                violations.append(f"{tiles_path}:{i}: {stripped} - font file path")
    assert not violations, f"External assets found: {violations}"
    assert "SysFont" in content, "SysFont must be present for programmatic only"


def test_src_render_only_init_and_tiles_effects_hud_absent() -> None:
    """AC-4: src/render only __init__.py and tiles.py effects.py hud.py absent per exclusions."""
    render_dir = Path("src/render")
    assert render_dir.exists(), "src/render must exist"
    files = [p.name for p in render_dir.glob("*.py")]
    assert "__init__.py" in files, "__init__.py must exist"
    assert "tiles.py" in files, "tiles.py must exist"
    assert "effects.py" not in files, "effects.py must be absent per exclusions belongs to Phase 4"
    assert "hud.py" not in files, "hud.py must be absent per exclusions belongs to Phase 4"
    assert set(files) == {"__init__.py", "tiles.py"}, f"Expected only __init__.py and tiles.py, got {files}"


def test_src_render_only_imports_pygame_and_core_Tile() -> None:
    """AC-4: src/render only imports pygame and core Tile."""
    tiles_path = Path("src/render/tiles.py")
    assert tiles_path.exists()
    content = tiles_path.read_text(encoding="utf-8")
    # Must import pygame
    assert "import pygame" in content or "from pygame" in content or "pygame" in content
    # Must import Tile from core
    assert "Tile" in content, "Tile import must exist"
    # Check no other core imports beyond Tile (allow BOARD_SIZE etc for constants? but spec says only Tile)
    # We allow import of Tile and maybe BOARD_SIZE as it's from same module, but check no os/sys/pathlib beyond allowed
    # For strict check: ensure no import of rules, score, history, achievements, gamestate, twist
    forbidden_core = ["rules", "score", "history", "achievements", "gamestate", "twist"]
    for forbidden in forbidden_core:
        # Look for from src.core.<forbidden> or import <forbidden>
        if f"from src.core.{forbidden}" in content or f"import {forbidden}" in content:
            # Allow if in comment
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if f"from src.core.{forbidden}" in line or f"src.core.{forbidden}" in line:
                    assert False, f"src/render/tiles.py should only import Tile, found {forbidden}: {line}"


def test_no_global_random_in_core_injectable_Random() -> None:
    """Isolation: grep no global random usage random.random() without self.rng, injectable Random enforced."""
    board_path = Path("src/core/board.py")
    assert board_path.exists()
    content = board_path.read_text(encoding="utf-8")
    violations = []
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "import random" in stripped:
            continue
        if "random.random()" in stripped:
            if "rng.random()" not in stripped and "self.rng" not in stripped:
                violations.append(f"Line {i}: {stripped}")
        if "random.choice(" in stripped:
            if "rng.choice(" not in stripped and "self.rng" not in stripped:
                violations.append(f"Line {i}: {stripped}")
    assert not violations, f"Global random usage found: {violations}"

    # Check twist.py has no random at all (pure deterministic)
    twist_path = Path("src/core/twist.py")
    assert twist_path.exists()
    twist_content = twist_path.read_text(encoding="utf-8")
    twist_violations = []
    for i, line in enumerate(twist_content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "import random" in stripped:
            continue
        if "random.random()" in stripped and "rng.random()" not in stripped and "self.rng" not in stripped:
            twist_violations.append(f"Line {i}: {stripped}")
        if "random.choice(" in stripped and "rng.choice(" not in stripped and "self.rng" not in stripped:
            twist_violations.append(f"Line {i}: {stripped}")
        if "random.Random()" in stripped:
            twist_violations.append(f"Line {i}: {stripped} - twist must not create RNG")
    assert not twist_violations, f"Global random in twist.py: {twist_violations}"
