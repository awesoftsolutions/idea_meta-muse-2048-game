import sys
print("=== Build Verification ===")
# 1. Check src.core.board headless importable no pygame
print("Test 1: src.core.board headless import")
try:
    import src.core.board as board_mod
    # Ensure pygame not in sys.modules after import
    if 'pygame' in sys.modules:
        print("FAIL: pygame imported when importing src.core.board")
        sys.exit(1)
    print("PASS: src.core.board importable headless, no pygame")
except Exception as e:
    print(f"FAIL: src.core.board import failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 2. Check src.main importable (may import pygame but should be importable)
print("Test 2: src.main importable")
try:
    # Need to check if pygame available
    import importlib.util
    spec = importlib.util.find_spec("pygame")
    if spec is None:
        print("SKIP: pygame not installed, src.main import would fail but that's env issue")
    else:
        import src.main as main_mod
        assert hasattr(main_mod, 'verify_pygame_api')
        assert hasattr(main_mod, 'main')
        print("PASS: src.main importable")
except Exception as e:
    print(f"FAIL: src.main import failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

# 3. Check board functionality
print("Test 3: Board slide functionality")
try:
    from src.core.board import Board
    import random
    rng = random.Random(42)
    b = Board(grid=[[2,2,None,None,None]] + [[None]*5]*4, rng=rng)
    new_grid, score, moved = b.slide("LEFT")
    assert moved == True
    assert score == 4
    print(f"PASS: Board slide works, score={score}, moved={moved}")
except Exception as e:
    print(f"FAIL: Board slide failed: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

print("=== All Build Checks PASS ===")
