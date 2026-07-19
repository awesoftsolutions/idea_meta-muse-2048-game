import pathlib, struct, re
vp = pathlib.Path('visual-proof')
PNG8 = b'\x89PNG\r\n\x1a\n'
PNG4 = b'\x89PNG'
for p in sorted(vp.glob('*.png')):
    data = p.read_bytes()
    size = len(data)
    h4 = data[:4]==PNG4
    h8 = data[:8]==PNG8
    dims=None
    if len(data)>=24:
        try:
            w=struct.unpack('>I', data[16:20])[0]
            h=struct.unpack('>I', data[20:24])[0]
            dims=(w,h)
        except Exception as e:
            dims=f"err {e}"
    print(f"{p.name}: size={size} h4={h4} h8={h8} dims={dims}")

print("--- manifest ---")
content = (vp/'README.md').read_text(encoding='utf-8')
obs = re.findall(r'obs_0000\d+', content)
print(f"distinct obs: {sorted(set(obs))} count={len(set(obs))}")
print(f"entry count heuristics: file: {content.count('- file:')} ### {content.count('###')} phase- {len(re.findall(r'###\\s+phase-', content))}")
for req in ["phase-3-first-light.png","phase-4-merge.png","phase-4-toast.png","phase-4-gameover.png","phase-5-tiles-after-moves.png","phase-1-spike.png"]:
    print(f"{req} in manifest: {req in content}")
print(f"has shows: {'shows:' in content} what it shows: {'what it shows' in content.lower()} input: {'input:' in content.lower()} obs_id label: {'observation_id' in content.lower()}")

print("--- readme ---")
rm = pathlib.Path('README.md').read_text(encoding='utf-8')
print(f"lines: {len(rm.splitlines())}")

print("--- technical_debt ---")
td = pathlib.Path('technical_debt.md').read_text(encoding='utf-8')
m = re.search(r'0\s+active', td, re.IGNORECASE)
print(f"0 active found: {bool(m)}")

print("--- core exports ---")
init = pathlib.Path('src/core/__init__.py').read_text(encoding='utf-8')
import ast
tree = ast.parse(init)
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id=='__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    print(f"__all__ len: {len(node.value.elts)}")
                    print([e.value if isinstance(e, ast.Constant) else str(e) for e in node.value.elts])

print("--- dist ---")
dist = pathlib.Path('dist')
print(f"dist exists: {dist.exists()} items: {list(dist.iterdir()) if dist.exists() else []}")
