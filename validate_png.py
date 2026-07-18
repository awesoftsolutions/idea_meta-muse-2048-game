import pathlib
p=pathlib.Path('visual-proof/phase-3-first-light.png')
data=p.read_bytes()
print(f'exists={p.exists()} size={len(data)}')
print('header', list(data[:8]))
assert data[:4]==bytes([0x89,0x50,0x4E,0x47]), 'bad header'
idx=data.find(b'IHDR')
w=int.from_bytes(data[idx+4:idx+8],'big')
h=int.from_bytes(data[idx+8:idx+12],'big')
print(f'dims {w}x{h}')
assert w==700 and h==800, f'dim mismatch {w}x{h}'
print('PNG VALID 700x800 header 89 50 4E 47')

c=pathlib.Path('visual-proof/README.md').read_text()
checks=[
    ('phase-3-first-light.png' in c, 'filename'),
    ('what it shows' in c.lower(), 'what it shows'),
    ('input_sequence' in c, 'input_sequence'),
    ('observation_id' in c, 'observation_id'),
    ('700x800' in c, '700x800'),
    ('#3B82F6' in c, 'heat color'),
    ('Favur 2048' in c, 'title'),
    ('obs_000002' in c or 'first-light-001' in c, 'obs id'),
    ('Real board' in c or 'real board' in c.lower(), 'real board desc'),
    ('launch no input' in c.lower(), 'launch no input'),
]
for ok,name in checks:
    print(f'{name}: {ok}')
assert all(o for o,_ in checks), 'manifest incomplete'
print('MANIFEST OK')

c2=pathlib.Path('src/main.py').read_text()
checks2=[
    ('700' in c2 and '800' in c2, '700x800'),
    ('Favur 2048' in c2, 'title'),
    ('pygame.image.save' in c2, 'image.save'),
    ('mkdir' in c2, 'mkdir'),
    ('parents=True' in c2, 'parents True'),
    ('exist_ok=True' in c2, 'exist_ok True'),
    ('OSError' in c2, 'OSError handling'),
    ('visual-proof' in c2, 'visual-proof path'),
]
for ok,n in checks2:
    print(f'{n}: {ok}')
assert all(o for o,_ in checks2)
print('MAIN.PY OK')
