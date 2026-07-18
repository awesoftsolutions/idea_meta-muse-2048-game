from pathlib import Path
p = Path("visual-proof/phase-4-effects.png")
data = p.read_bytes()
print(f"size {len(data)} header {data[:4].hex()} expected 89504e47")
# try pygame
try:
    import pygame
    pygame.init()
    img = pygame.image.load(str(p))
    print(f"dims {img.get_width()}x{img.get_height()}")
    pygame.quit()
except Exception as e:
    print(f"pygame load failed {e}")
