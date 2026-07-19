import struct, pathlib
p=pathlib.Path('visual-proof')
for f in sorted(p.glob('*.png')):
    data=f.read_bytes()
    if len(data)>=24:
        w=struct.unpack('>I', data[16:20])[0]
        h=struct.unpack('>I', data[20:24])[0]
        print(f"{f.name}: {w}x{h} size={len(data)} header={data[:8].hex()}")
    else:
        print(f"{f.name}: too small {len(data)}")
