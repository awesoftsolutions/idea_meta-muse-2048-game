import sys
import os
import pathlib
import py_compile
import re

root = pathlib.Path('.')
print("=== 1. py_compile ===")
files = [
    "src/core/__init__.py",
    "src/core/board.py",
    "src/core/gamestate.py",
    "src/core/rules.py",
    "src/core/score.py",
    "src/core/history.py",
    "src/core/twist.py",
    "src/core/achievements.py",
    "src/main.py",
    "src/render/__init__.py",
    "src/render/tiles.py",
]
ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"  PASS {f}")
    except Exception as e:
        print(f"  FAIL {f}: {e}")
        ok = False
print(f"py_compile overall: {'PASS' if ok else 'FAIL'}")

print("\n=== 2. Import checks ===")
# core imports without pygame
try:
    import src.core.board as board_mod
    import src.core.rules as rules_mod
    import src.core.score as score_mod
    import src.core.history as history_mod
    import src.core.twist as twist_mod
    import src.core.achievements as ach_mod
    import src.core.gamestate as gs_mod
    import src.core as core_mod
    print("  PASS src.core.board")
    print("  PASS src.core.rules")
    print("  PASS src.core.score")
    print("  PASS src.core.history")
    print("  PASS src.core.twist")
    print("  PASS src.core.achievements")
    print("  PASS src.core.gamestate")
    print("  PASS src.core")
except Exception as e:
    print(f"  FAIL import: {e}")
    import traceback; traceback.print_exc()

# render tiles importable (should work without pygame installed because pygame import is inside function)
try:
    # Mock pygame to allow import if needed
    import types
    if 'pygame' not in sys.modules:
        # create minimal mock so top-level doesn't fail, but tiles.py doesn't import pygame at top
        pass
    import src.render.tiles as tiles_mod
    print("  PASS src.render.tiles")
except Exception as e:
    print(f"  FAIL src.render.tiles: {e}")
    import traceback; traceback.print_exc()

print("\n=== 3. Pygame leak check ===")
# fresh process check: we already imported core, check sys.modules for pygame
leaked = [m for m in sys.modules.keys() if 'pygame' in m.lower()]
if leaked:
    print(f"  LEAK detected: {leaked}")
else:
    print("  CLEAN no pygame in sys.modules after core import")
# Also check core files for import pygame string
for f in ["src/core/__init__.py","src/core/board.py","src/core/gamestate.py","src/core/rules.py","src/core/score.py","src/core/history.py","src/core/twist.py","src/core/achievements.py"]:
    content = pathlib.Path(f).read_text()
    if re.search(r'^\s*import pygame|^\s*from pygame', content, re.MULTILINE):
        print(f"  LEAK file contains pygame import: {f}")
    else:
        print(f"  CLEAN {f} no pygame import")

print("\n=== 4. Exports verification ===")
import src.core as core
all_list = core.__all__
print(f"  __all__ count: {len(all_list)}")
print(f"  __all__ list: {all_list}")
print(f"  count==26: {len(all_list)==26}")
for name in ["GameState","MergeInfo","source_heats"]:
    if name == "source_heats":
        # check MergeInfo field
        from src.core.board import MergeInfo
        has = "source_heats" in MergeInfo.__dataclass_fields__
        print(f"  MergeInfo has source_heats field: {has}")
    else:
        print(f"  has {name}: {name in all_list}")

print("\n=== 5. Global random check ===")
# Check for random.random() or random.choice etc not using self.rng or rng.
violations = []
for f in files:
    if "core" not in f:
        continue
    content = pathlib.Path(f).read_text()
    # Look for random.XXX where not self.rng or rng.
    # Allow import random, and usage of random.Random, but not random.choice/random.random/random.randint at module level
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # detect global random usage: random.choice, random.random, random.randint, random.randrange, random.shuffle
        if re.search(r'\brandom\.(choice|random|randint|randrange|shuffle|sample)\s*\(', line):
            # allow if preceded by self.rng or rng variable? Actually pattern is random. not self.rng.
            # So this is violation if it's exactly random.
            violations.append(f"{f}:{i}: {line.strip()}")
if violations:
    print(f"  VIOLATION found {len(violations)}:")
    for v in violations:
        print(f"    {v}")
else:
    print("  CLEAN no global random usage")

print("\n=== 6. Render dir check ===")
render_path = pathlib.Path("src/render")
if render_path.exists():
    files_in_render = sorted([p.name for p in render_path.iterdir() if p.is_file()])
    print(f"  exists: True, files: {files_in_render}")
    print(f"  only __init__.py and tiles.py: {set(files_in_render)=={'__init__.py','tiles.py'}}")
    print(f"  effects.py absent: {'effects.py' not in files_in_render}")
    print(f"  hud.py absent: {'hud.py' not in files_in_render}")
else:
    print("  FAIL src/render does not exist")

print("\n=== 7. main.py constants check ===")
main_content = pathlib.Path("src/main.py").read_text()
checks = {
    "700": "700" in main_content,
    "800": "800" in main_content,
    "Favur 2048 exact title": '"Favur 2048"' in main_content or "'Favur 2048'" in main_content,
    "flags=0": "flags=0" in main_content,
    "700x800 tuple": "(700,800)" in main_content or "(700, 800)" in main_content or "window_width = 700" in main_content,
}
for k,v in checks.items():
    print(f"  {k}: {v}")
# More precise
has_title_exact = 'Favur 2048' in main_content
has_700 = re.search(r'window_width\s*=\s*700|700', main_content) is not None
has_800 = re.search(r'window_height\s*=\s*800|800', main_content) is not None
has_flags = 'flags=0' in main_content
print(f"  Overall main.py constants PASS: {has_title_exact and has_700 and has_800 and has_flags}")

print("\n=== 8. Overall ===")
print("DONE")
