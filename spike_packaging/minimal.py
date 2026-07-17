import pygame
import sys


def main():
    """Minimal pygame-ce window for PyInstaller spike - no game code dependency."""
    pygame.init()
    screen = pygame.display.set_mode((700, 800))
    pygame.display.set_caption("Favur 2048")
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (200, 100, 255), (300, 350, 100, 100))
    pygame.display.flip()
    pygame.time.wait(500)
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
