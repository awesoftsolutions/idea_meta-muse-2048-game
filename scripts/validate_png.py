import pathlib
p = pathlib.Path("visual-proof/phase-1-spike.png")
data = p.read_bytes()
print(f"size={len(data)}")
header = data[:8]
print(f"header_hex={header.hex()}")
print(f"header_4={header[:4].hex()} expected 89504e47")
assert len(data) > 0, "size zero"
assert header[:4] == bytes([0x89, 0x50, 0x4E, 0x47]), f"invalid header {header[:4].hex()}"
print("PNG validation PASS header 89 50 4E 47 size>0")
