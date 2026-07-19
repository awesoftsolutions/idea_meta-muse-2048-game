from pathlib import Path
import struct
PNG8=b'\x89PNG\r\n\x1a\n'
files=[
 ('visual-proof/phase-3-first-light.png',10376),
 ('visual-proof/phase-4-merge.png',16571),
 ('visual-proof/phase-4-toast.png',21606),
 ('visual-proof/phase-4-gameover.png',41407),
 ('visual-proof/phase-5-tiles-after-moves.png',None)
]
ok=True
for p,exp in files:
    path=Path(p)
    if not path.exists():
        print(f'{p} MISSING')
        ok=False
        continue
    data=path.read_bytes()
    hdr=data[:8]==PNG8
    w=struct.unpack('>I',data[16:20])[0] if len(data)>=24 else 0
    h=struct.unpack('>I',data[20:24])[0] if len(data)>=24 else 0
    print(f'{p} size={len(data)} exp={exp} hdr={hdr} {w}x{h} valid={hdr and w==700 and h==800}')
    if not hdr or w!=700 or h!=800:
        ok=False
print('GATING', 'PASS' if ok else 'FAIL')
