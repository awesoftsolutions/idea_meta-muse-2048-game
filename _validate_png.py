import pathlib, struct
p=pathlib.Path('visual-proof/phase-3-first-light.png')
print('exists', p.exists())
s=p.stat().st_size if p.exists() else 0
print('size', s)
data=p.read_bytes()
print('header', list(data[:8]))
assert data[:4]==bytes([0x89,0x50,0x4E,0x47]), f"Invalid header {data[:4].hex()}"
idx=data.find(b'IHDR')
assert idx!=-1, "No IHDR"
w=int.from_bytes(data[idx+4:idx+8],'big')
h=int.from_bytes(data[idx+8:idx+12],'big')
print(f'{w}x{h}')
assert w==700 and h==800, f"Dimensions mismatch {w}x{h}"
print('PNG VALID 700x800 header 89 50 4E 47')
