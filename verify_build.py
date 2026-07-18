import py_compile, sys, pathlib, os
files = ["src/core/score.py","src/core/history.py","src/core/twist.py","src/core/__init__.py","src/core/board.py","src/core/rules.py"]
print("=== py_compile ===")
ok=True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"PASS {f}")
    except Exception as e:
        print(f"FAIL {f}: {e}")
        ok=False

print("\n=== headless importable ===")
try:
    os.environ.pop("DISPLAY", None)
    for mod in list(sys.modules.keys()):
        if "pygame" in mod:
            del sys.modules[mod]
    import src.core as core
    print("PASS headless importable")
except Exception as e:
    print(f"FAIL headless importable: {e}")
    ok=False

print("\n=== pygame leak check ===")
try:
    has_pygame = any("pygame" in k for k in sys.modules.keys())
    if has_pygame:
        leaked = [k for k in sys.modules.keys() if "pygame" in k]
        print(f"FAIL pygame leak: {leaked}")
        ok=False
    else:
        print("PASS no pygame leak")
except Exception as e:
    print(f"FAIL pygame leak check error: {e}")
    ok=False

print("\n=== src/render absent ===")
try:
    p = pathlib.Path("src/render")
    if p.exists():
        print(f"FAIL src/render exists: {list(p.iterdir())}")
        ok=False
    else:
        print("PASS src/render absent")
except Exception as e:
    print(f"FAIL src/render check error: {e}")
    ok=False

print("\n=== exports verification ===")
try:
    import src.core
    exports = getattr(src.core, "__all__", [])
    print(f"exports count: {len(exports)}")
    print(f"exports: {exports}")
    if len(exports) == 22:
        print("PASS 22 exports")
    else:
        print(f"FAIL expected 22 got {len(exports)}")
        ok=False
    expected = ["Tile","Board","Direction","SlideResult","MergeInfo","BOARD_SIZE","HEAT_MIN","HEAT_MAX","create_empty_grid","is_legal_move","is_game_over","ScoreState","Score","DEFAULT_HIGH_SCORE_PATH","HistorySnapshot","HistoryStack","apply_heat_generation","spread_heat","vent_heat","check_unstable","calculate_cool_merge_bonus","get_turn_pipeline_order"]
    missing = [x for x in expected if x not in exports]
    if missing:
        print(f"FAIL missing exports: {missing}")
        ok=False
    else:
        print("PASS all expected exports present")
except Exception as e:
    print(f"FAIL exports verification: {e}")
    ok=False

print("\n=== FINAL ===")
if ok:
    print("BUILD PASS exit 0")
    sys.exit(0)
else:
    print("BUILD FAIL exit 1")
    sys.exit(1)
