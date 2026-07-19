import pathlib, struct, re, ast, sys
vp=pathlib.Path('visual-proof')
files=['phase-1-spike.png','phase-3-first-light.png','phase-4-merge.png','phase-4-toast.png','phase-4-gameover.png','phase-5-tiles-after-moves.png','phase-6-binary.png']
PNG4=b'\x89PNG'
PNG8=b'\x89PNG\r\n\x1a\n'
print('--- PNG HEADER CHECK ---')
for f in files:
    p=vp/f
    if not p.exists():
        print(f'{f}: MISSING')
        continue
    data=p.read_bytes()
    h4=data[:4]==PNG4
    h8=data[:8]==PNG8
    size=len(data)
    dims=None
    if len(data)>=24:
        try:
            w=struct.unpack('>I', data[16:20])[0]
            h=struct.unpack('>I', data[20:24])[0]
            dims=(w,h)
        except Exception as e:
            dims=f'err {e}'
    print(f'{f}: size={size} h4={h4} h8={h8} dims={dims}')
print('--- README ---')
print(f"lines={len(pathlib.Path('README.md').read_text().splitlines())}")
print('--- TECH DEBT ---')
td=pathlib.Path('technical_debt.md').read_text()
print(f"0 active regex: {bool(re.search(r'0\\s+active', td, re.I))}")
print('--- DIST ---')
print(list(pathlib.Path('dist').glob('*')))
print('--- EXPORTS ---')
init=pathlib.Path('src/core/__init__.py').read_text()
tree=ast.parse(init)
exp=0
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id=='__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    exp=len(node.value.elts)
print(f'exports={exp}')
print('--- MANIFEST ---')
man=pathlib.Path('visual-proof/README.md').read_text()
obs=re.findall(r'obs_0000\d+', man)
print(f"distinct obs={len(set(obs))} list={sorted(set(obs))}")
print(f"entry count file: {man.count('- file:')} ### {man.count('###')}")
print('--- VALIDATION SCRIPT ---')
import subprocess
r=subprocess.run([sys.executable, 'scripts/validate_visual_proof.py'], capture_output=True, text=True, timeout=30)
print(f"exit={r.returncode}")
print(r.stdout[:2000])
print(r.stderr[:500])
