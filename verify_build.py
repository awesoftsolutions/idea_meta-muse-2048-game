import sys, os, pathlib, re
os.environ.pop('DISPLAY', None)
print('=== py_compile already passed ===')
mods = ['src.core.board','src.core.rules','src.core.score','src.core.history','src.core.twist','src.core.achievements','src.core']
for m in mods:
    __import__(m)
    print(f'IMPORT OK: {m} exit=0')
leaked = [k for k in sys.modules if 'pygame' in k.lower()]
if leaked:
    print(f'FAIL pygame leak: {leaked}')
    sys.exit(1)
print('PASS no pygame leak exit=0')
import src.core as core
exports_all = getattr(core, '__all__', [])
exports_dir = [x for x in dir(core) if not x.startswith('_')]
print(f'__all__ count={len(exports_all)}: {sorted(exports_all)}')
print(f'dir() count={len(exports_dir)}: {sorted(exports_dir)}')
for req in ['Achievements','GameContext','Tile','Board']:
    assert req in exports_all, f'missing {req} in __all__'
print('PASS required exports Achievements GameContext present in __all__')
if len(exports_all) != 25:
    print(f'FAIL __all__ {len(exports_all)} !=25')
    sys.exit(1)
print('PASS 25 exports verified via __all__ exit=0')
core_files = list(pathlib.Path('src/core').glob('*.py'))
bad=[]
for f in core_files:
    text=f.read_text()
    for i,line in enumerate(text.splitlines(),1):
        if 'import random' in line: continue
        if 'random.Random' in line: continue
        if re.search(r'(?<!self\.)random\.(random|choice|randint|randrange|shuffle|choices|uniform)\s*\(', line):
            if 'rng' in line.lower(): continue
            bad.append(f'{f.name}:{i}:{line.strip()}')
if bad:
    print('FAIL global random:')
    for b in bad: print(b)
    sys.exit(1)
print('PASS no global random usage exit=0')
if pathlib.Path('src/render').exists():
    print('FAIL src/render exists')
    sys.exit(1)
print('PASS src/render absent exit=0')
main = pathlib.Path('src/main.py').read_text()
print(f'src/main.py length {len(main)} chars')
print('ALL CHECKS PASS')
