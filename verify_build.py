import sys
print("=== Build Verification ===")
# Test 1: py_compile already done via poetry run, but test import
print("Test headless import...")
try:
    import src.core.board
    import src.core.rules
    from src.core import Tile, Board, Direction
    print("HEADLESS IMPORT: PASS")
    import_ok = True
except Exception as e:
    print(f"HEADLESS IMPORT: FAIL - {e}")
    import_ok = False
    import traceback
    traceback.print_exc()

# Test 2: pygame leak check
print("Test pygame leak...")
if import_ok:
    if 'pygame' in sys.modules or 'pygame_ce' in sys.modules:
        print("PYGAME LEAK: FAIL - pygame in sys.modules")
        print(f"Found: {[k for k in sys.modules.keys() if 'pygame' in k.lower()]}")
    else:
        print("PYGAME LEAK: PASS - no pygame in sys.modules")
else:
    print("PYGAME LEAK: SKIP - import failed")

# Test 3: Tile, Board, Direction availability
print("Test exports...")
try:
    from src.core import Tile, Board, Direction
    t = Tile(value=2, heat=0)
    print(f"Tile creation: PASS - {t}")
    print("EXPORTS: PASS")
except Exception as e:
    print(f"EXPORTS: FAIL - {e}")
    import traceback
    traceback.print_exc()
