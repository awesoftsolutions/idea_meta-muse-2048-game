import pathlib
import struct

for p in pathlib.Path('visual-proof').glob('*.png'):
    data = p.read_bytes()
    ok = data[:4] == b'\x89PNG'
    w = struct.unpack('>I', data[16:20])[0] if len(data) >= 24 else 0
    h = struct.unpack('>I', data[20:24])[0] if len(data) >= 24 else 0
    print(f"{p.name}: size={len(data)} header_ok={ok} {w}x{h}")
