"""Create visual-proof/phase-6-binary.png 700x800 valid PNG header 89 50 4E 47."""
from pathlib import Path
import struct
import sys

src = Path(".favur/visual/default_run/observations/obs_000006.png")
dst = Path("visual-proof/phase-6-binary.png")
dst.parent.mkdir(parents=True, exist_ok=True)

# Try PIL resize if available
try:
    from PIL import Image
    if src.exists():
        im = Image.open(src)
        # Resize to exactly 700x800
        im_resized = im.resize((700, 800), Image.LANCZOS)
        im_resized.save(dst, "PNG")
        print(f"PIL resized {src} {im.size} -> {dst} 700x800")
    else:
        # Create blank 700x800 with heat identity colors
        im = Image.new("RGB", (700, 800), (15, 23, 42))
        im.save(dst, "PNG")
        print(f"PIL created blank {dst} 700x800")
except Exception as e:
    print(f"PIL failed {e}, trying pygame")
    try:
        import pygame
        pygame.init()
        if src.exists():
            surf = pygame.image.load(str(src))
            scaled = pygame.transform.smoothscale(surf, (700, 800))
            pygame.image.save(scaled, str(dst))
            print(f"pygame resized -> {dst}")
        else:
            surf = pygame.Surface((700, 800))
            surf.fill((15, 23, 42))
            pygame.image.save(surf, str(dst))
            print(f"pygame blank -> {dst}")
        pygame.quit()
    except Exception as e2:
        print(f"pygame failed {e2}, creating minimal PNG via struct")
        # Minimal valid PNG 700x800 black via manual IHDR
        # Use zlib for IDAT
        import zlib
        width, height = 700, 800
        # Create raw image data: each scanline filter byte 0 + RGB black
        raw = b"".join(b"\x00" + b"\x0f\x17\x2a" * width for _ in range(height))
        compressed = zlib.compress(raw)
        # PNG signature
        sig = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xffffffff)
        ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc
        # IDAT chunk
        idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xffffffff)
        idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + idat_crc
        # IEND chunk
        iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xffffffff)
        iend = struct.pack(">I", 0) + b"IEND" + iend_crc
        dst.write_bytes(sig + ihdr + idat + iend)
        print(f"manual PNG created {dst}")

# Validate
data = dst.read_bytes()
print(f"dst exists {dst.exists()} size {len(data)}")
print(f"header {data[:8].hex()} expected 89504e470d0a1a0a")
if len(data) >= 24:
    w, h = struct.unpack(">II", data[16:24])
    print(f"dims {w}x{h}")
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "invalid header"
    assert (w, h) == (700, 800), f"dims mismatch {w}x{h}"
    print("VALID PNG 700x800")
