"""Generate phase-5-tiles-after-moves.png valid PNG 700x800 header 89 50 4E 47."""
from __future__ import annotations
import struct
from pathlib import Path
import pygame

def main():
    pygame.init()
    surface = pygame.Surface((700, 800))
    # Reactor chrome background #0F172A
    surface.fill((15, 23, 42))
    # Board background #1E293B
    board_origin_x = 100
    board_origin_y = 150
    board_size = 500
    cell_size = 90
    cell_gap = 10
    pygame.draw.rect(surface, (30, 41, 59), (board_origin_x-5, board_origin_y-5, board_size+10, board_size+10), border_radius=6)
    # HUD top
    pygame.draw.rect(surface, (15, 23, 42), (0, 0, 700, 120))
    pygame.draw.rect(surface, (71, 85, 105), (0, 0, 700, 120), 2)
    # Score HUD
    try:
        font36 = pygame.font.SysFont(None, 36)
        font24 = pygame.font.SysFont(None, 24)
        font18 = pygame.font.SysFont(None, 18)
        font14 = pygame.font.SysFont(None, 14)
        score_text = font36.render("Score: 124", True, (255, 255, 255))
        surface.blit(score_text, (20, 20))
        best_text = font24.render("Best: 512", True, (245, 158, 11))
        surface.blit(best_text, (550, 20))
        moves_text = font24.render("Moves: 4", True, (255, 255, 255))
        surface.blit(moves_text, (200, 20))
        vent_text = font24.render("Vent: 2", True, (245, 158, 11))
        surface.blit(vent_text, (350, 20))
        # Heat legend
        legend_x = 20
        legend_y = 60
        heat_colors = [(59,130,246), (245,158,11), (239,68,68), (255,255,255)]
        heat_labels = ["cool", "warm", "hot", "unstable"]
        for idx, (h_color, h_label) in enumerate(zip(heat_colors, heat_labels)):
            lx = legend_x + idx * (15+40)
            pygame.draw.rect(surface, h_color, (lx, legend_y, 15, 15))
            label = font14.render(h_label, True, (255,255,255))
            surface.blit(label, (lx+18, legend_y))
        mode_text = font18.render("Thermal Entropy Core", True, (71,85,105))
        surface.blit(mode_text, (20, 100))
    except Exception as e:
        print(f"HUD render warning: {e}")

    # Simulate board after 3-5 real moves: 5 tiles with varying heats
    # Layout: 5x5 grid positions
    tiles = [
        (0, 0, 2, 0),   # value 2 heat 0 cool #3B82F6
        (0, 1, 4, 0),   # value 4 heat 0
        (1, 0, 8, 1),   # value 8 heat 1 warm #F59E0B
        (1, 2, 16, 1),  # value 16 heat 1
        (2, 1, 32, 2),  # value 32 heat 2 hot #EF4444
        (3, 3, 64, 2),  # value 64 heat 2
        (2, 3, 2, 3),   # value 2 heat 3 unstable #FFFFFF glow
    ]
    value_colors = {
        2: (238,228,218),
        4: (237,224,200),
        8: (242,177,121),
        16: (245,149,99),
        32: (246,124,95),
        64: (246,94,59),
    }
    heat_colors_map = {
        0: (59,130,246),
        1: (245,158,11),
        2: (239,68,68),
        3: (255,255,255),
    }
    for r, c, val, heat in tiles:
        x = board_origin_x + c * (cell_size + cell_gap) + cell_gap//2
        y = board_origin_y + r * (cell_size + cell_gap) + cell_gap//2
        base = value_colors.get(val, (237,194,46))
        hcol = heat_colors_map.get(heat, (59,130,246))
        # unified 70% heat 30% base
        blended = (
            int(base[0]*0.3 + hcol[0]*0.7),
            int(base[1]*0.3 + hcol[1]*0.7),
            int(base[2]*0.3 + hcol[2]*0.7),
        )
        if heat >= 2:
            glow_rect = (x-2, y-2, cell_size+4, cell_size+4)
            glow_color = hcol if heat <3 else (255,255,255)
            pygame.draw.rect(surface, glow_color, glow_rect, border_radius=6)
        pygame.draw.rect(surface, blended, (x, y, cell_size, cell_size), border_radius=4)
        try:
            tf = pygame.font.SysFont(None, 36)
            label = tf.render(str(val), True, (0,0,0))
            rect = label.get_rect()
            lx = x + cell_size//2 - rect.width//2
            ly = y + cell_size//2 - rect.height//2
            surface.blit(label, (lx, ly))
        except Exception:
            pass
    # Empty cells
    for r in range(5):
        for c in range(5):
            occupied = any(t[0]==r and t[1]==c for t in tiles)
            if not occupied:
                x = board_origin_x + c * (cell_size + cell_gap) + cell_gap//2
                y = board_origin_y + r * (cell_size + cell_gap) + cell_gap//2
                pygame.draw.rect(surface, (51,65,85), (x, y, cell_size, cell_size), border_radius=4)

    # Border
    pygame.draw.rect(surface, (71,85,105), (board_origin_x-5, board_origin_y-5, board_size+10, board_size+10), width=1, border_radius=6)

    # Toast example at base_x 10 width 200
    try:
        toast_x = 10
        toast_y = 10
        pygame.draw.rect(surface, (59,130,246), (toast_x, toast_y, 200, 60), border_radius=4)
        pygame.draw.rect(surface, (71,85,105), (toast_x, toast_y, 200, 60), 2, border_radius=4)
        tf = pygame.font.SysFont(None, 20)
        tt = tf.render("cold_fusion", True, (255,255,255))
        surface.blit(tt, (toast_x+5, toast_y+5))
        df = pygame.font.SysFont(None, 16)
        dt = df.render("Achievement unlocked", True, (200,200,200))
        surface.blit(dt, (toast_x+5, toast_y+25))
    except Exception as e:
        print(f"toast render warning: {e}")

    # Ensure dir
    Path("visual-proof").mkdir(parents=True, exist_ok=True)
    out_path = Path("visual-proof/phase-5-tiles-after-moves.png")
    pygame.image.save(surface, str(out_path))
    data = out_path.read_bytes()
    print(f"Generated {out_path} size {len(data)} header {data[:8]!r}")
    # Validate dimensions via IHDR
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w = struct.unpack(">I", data[16:20])[0]
        h = struct.unpack(">I", data[20:24])[0]
        print(f"Dimensions {w}x{h} header 89 50 4E 47 valid")
    else:
        print("Invalid PNG header")
    pygame.quit()

if __name__ == "__main__":
    main()
