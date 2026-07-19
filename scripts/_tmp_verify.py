import pathlib, struct, re
vp = pathlib.Path('visual-proof')
PNG8 = b'\x89PNG\r\n\x1a\n'
for p in sorted(vp.glob('*.png')):
    data = p.read_bytes()
    h8 = data[:8] == PNG8
    size = len(data)
    w=h=None
    if len(data)>=24:
        try:
            w=struct.unpack('>I', data[16:20])[0]
            h=struct.unpack('>I', data[20:24])[0]
        except Exception as e:
            print(p.name, 'struct err', e)
    print(f"{p.name} {size} header8={h8} dims={w}x{h}")
manifest = pathlib.Path('visual-proof/README.md').read_text(encoding='utf-8')
obs = re.findall(r'obs_0000\d+', manifest)
print('obs distinct', sorted(set(obs)), len(set(obs)))
print('file: count', manifest.count('- file:'))
print('### count', manifest.count('###'))
print('has shows', 'shows:' in manifest.lower() or 'what it shows' in manifest.lower())
print('has input', 'input:' in manifest.lower())
print('has observation_id', 'observation_id' in manifest.lower())
print('has spike', 'phase-1-spike' in manifest)
# readme lines
print('README lines', len(pathlib.Path('README.md').read_text(encoding='utf-8').splitlines()))
# technical debt
td = pathlib.Path('technical_debt.md').read_text(encoding='utf-8')
print('active debt check', '0 active' in td.lower())
# dist
dist = pathlib.Path('dist')
print('dist exists', dist.exists(), 'items', list(dist.iterdir()) if dist.exists() else [])
# ci yaml
import yaml
ci = pathlib.Path('.github/workflows/ci.yml').read_text(encoding='utf-8')
parsed = yaml.safe_load(ci)
print('ci jobs', list(parsed.get('jobs', {}).keys()))
print('ci valid', True)
