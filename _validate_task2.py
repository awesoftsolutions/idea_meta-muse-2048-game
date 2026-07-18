import struct
from pathlib import Path
for p in [Path("visual-proof/phase-4-merge.png"), Path("visual-proof/phase-4-toast.png"), Path("visual-proof/phase-4-gameover.png")]:
    data = p.read_bytes()
    print(p, len(data), data[:8].hex())
    assert data[:4]==b'\x89PNG'
    assert data[:8]==b'\x89PNG\r\n\x1a\n'
    w=struct.unpack(">I", data[16:20])[0]
    h=struct.unpack(">I", data[20:24])[0]
    print(f"  {w}x{h}")
    assert w==700 and h==800
print("all valid")
