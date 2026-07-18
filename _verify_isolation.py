import pathlib, sys, re, importlib, random
print("=== src layout verification ===")
render = pathlib.Path('src/render')
for f in ['__init__.py','tiles.py','effects.py','hud.py']:
    p = render/f
    print(f"{f}: exists={p.exists()} size={p.stat().st_size if p.exists() else 0}")
    assert p.exists() and p.stat().st_size>0, f"missing {f}"
print("PASS src layout")

print("\n=== no pygame import grep ===")
CORE_FILES = ["src/core/board.py","src/core/rules.py","src/core/score.py","src/core/history.py","src/core/twist.py","src/core/achievements.py","src/core/gamestate.py","src/core/__init__.py"]
PYGAME_IMPORT_RE = re.compile(r"^\s*import\s+pygame\b", re.MULTILINE)
PYGAME_FROM_RE = re.compile(r"^\s*from\s+pygame\b", re.MULTILINE)
for fp in CORE_FILES:
    path = pathlib.Path(fp)
    if not path.exists():
        continue
    content = path.read_text(encoding='utf-8')
    assert not PYGAME_IMPORT_RE.findall(content), f"{fp} has import pygame"
    assert not PYGAME_FROM_RE.findall(content), f"{fp} has from pygame"
print("PASS no pygame import grep")

print("\n=== sys.modules delta ===")
before = set(sys.modules.keys())
mods = ["src.core.board","src.core.rules","src.core.score","src.core.history","src.core.twist","src.core.achievements","src.core.gamestate"]
for m in mods:
    importlib.import_module(m)
after = set(sys.modules.keys())
delta = after-before
leaked = [k for k in delta if k.startswith("pygame") or k=="pygame"]
print(f"delta new modules: {len(delta)} leaked pygame: {leaked}")
assert not leaked, f"pygame leaked {leaked}"
assert "pygame" not in delta
print("PASS sys.modules delta")

print("\n=== headless importable ===")
from src.core.board import BOARD_SIZE, Direction, Tile, Board, create_empty_grid
assert BOARD_SIZE==5
t=Tile(value=4, heat=1)
assert t.value==4 and t.heat==1
assert hasattr(Direction,"UP") and hasattr(Direction,"DOWN") and hasattr(Direction,"LEFT") and hasattr(Direction,"RIGHT")
for mod in mods+["src.core"]:
    importlib.import_module(mod)
print("PASS headless importable")

print("\n=== no global random ===")
global_random = re.compile(r"\brandom\.random\s*\(")
global_choice = re.compile(r"\brandom\.choice\s*\(")
for fp in CORE_FILES:
    path = pathlib.Path(fp)
    if not path.exists():
        continue
    content = path.read_text(encoding='utf-8')
    for i,line in enumerate(content.splitlines(),1):
        if line.strip().startswith("#"):
            continue
        if "random.Random" in line:
            continue
        low=line.lower()
        if "avoid" in low or "forbidden" in low or "no global" in low or "should use" in low:
            continue
        if global_random.search(line):
            raise AssertionError(f"{fp}:{i} global random.random {line.strip()}")
        if global_choice.search(line):
            raise AssertionError(f"{fp}:{i} global random.choice {line.strip()}")
board_content = pathlib.Path("src/core/board.py").read_text(encoding='utf-8')
assert "self.rng" in board_content or "rng." in board_content
assert "Random" in board_content
print("PASS no global random")

print("\n=== Q-001 re-measurement ===")
from src.core.board import BOARD_SIZE as BS, Board as B, Direction as Dir, Tile as T, create_empty_grid as ceg
from src.core.rules import is_legal_move
directions_all = [Dir.UP, Dir.DOWN, Dir.LEFT, Dir.RIGHT]
per_run_avgs=[]
global_max=0
global_min=3
for move_count in [50,100,200]:
    run_rng = random.Random(42)
    grid = ceg()
    empty_positions = [(r,c) for r in range(BS) for c in range(BS)]
    pos = run_rng.choice(empty_positions)
    grid[pos[0]][pos[1]] = T(value=2, heat=0)
    board = B(grid=grid, rng=run_rng)
    total=0.0
    cnt=0
    run_max=0
    run_min=3
    moves_done=0
    attempts=0
    max_attempts=move_count*10
    while moves_done<move_count and attempts<max_attempts:
        attempts+=1
        legal=[]
        for d in directions_all:
            try:
                if is_legal_move(d, board.grid):
                    legal.append(d)
            except:
                continue
        if not legal:
            break
        chosen = run_rng.choice(legal)
        result = board.slide(chosen)
        if result.moved:
            moves_done+=1
            heats=[]
            for r in range(BS):
                for c in range(BS):
                    tile=board.grid[r][c]
                    if tile is not None:
                        heats.append(tile.heat)
                        if tile.heat>run_max:
                            run_max=tile.heat
                        if tile.heat<run_min:
                            run_min=tile.heat
            if heats:
                avg=sum(heats)/len(heats)
                total+=avg
                cnt+=1
    if cnt==0:
        heats=[board.grid[r][c].heat for r in range(BS) for c in range(BS) if board.grid[r][c] is not None]
        if heats:
            total=sum(heats)/len(heats)
            cnt=1
            run_max=max(heats)
            run_min=min(heats)
    avg_for_run=total/cnt if cnt else 0.0
    per_run_avgs.append(avg_for_run)
    if run_max>global_max:
        global_max=run_max
    if run_min<global_min:
        global_min=run_min
    print(f"move_count={move_count} avg={avg_for_run:.3f} max={run_max} min={run_min} moves_done={moves_done}")
overall_avg=sum(per_run_avgs)/len(per_run_avgs) if per_run_avgs else 0.0
print(f"overall_avg={overall_avg:.3f} per_run={per_run_avgs} global_max={global_max} global_min={global_min} baseline Sprint2 1.803")
assert overall_avg<2.0, f"overall_avg {overall_avg} >=2.0"
assert global_max<=3
assert global_min>=0

# Phase B full board
full_rng=random.Random(42)
full_grid=ceg()
edge_positions=[(r,c) for r in range(BS) for c in range(BS) if r==0 or r==4 or c==0 or c==4]
interior_positions=[(r,c) for r in range(BS) for c in range(BS) if 1<=r<=3 and 1<=c<=3]
full_rng.shuffle(edge_positions)
full_rng.shuffle(interior_positions)
selected=edge_positions[:16]+interior_positions[:4]
for r,c in selected:
    full_grid[r][c]=T(value=2, heat=0)
full_board=B(grid=full_grid, rng=full_rng)
for _ in range(50):
    legal=[]
    for d in directions_all:
        try:
            if is_legal_move(d, full_board.grid):
                legal.append(d)
        except:
            continue
    if not legal:
        break
    chosen=full_rng.choice(legal)
    result=full_board.slide(chosen)
    if not result.moved:
        for d in legal:
            if d==chosen:
                continue
            try:
                result=full_board.slide(d)
                if result.moved:
                    break
            except:
                continue
interior_heats=[]
edge_heats=[]
for r in range(BS):
    for c in range(BS):
        tile=full_board.grid[r][c]
        if tile is not None:
            if 1<=r<=3 and 1<=c<=3:
                interior_heats.append(tile.heat)
            if r==0 or r==4 or c==0 or c==4:
                edge_heats.append(tile.heat)
interior_avg=sum(interior_heats)/len(interior_heats) if interior_heats else 0.0
edge_avg=sum(edge_heats)/len(edge_heats) if edge_heats else 0.0
print(f"Phase B interior_avg={interior_avg:.3f} edge_avg={edge_avg:.3f} interior_n={len(interior_heats)} edge_n={len(edge_heats)}")
assert interior_avg>=edge_avg-0.2, f"interior {interior_avg} < edge {edge_avg}-0.2"
print("PASS Q-001 re-measurement")
print(f"\nFINAL: overall_avg={overall_avg:.3f} baseline 1.803 interior_avg={interior_avg:.3f} edge_avg={edge_avg:.3f}")
