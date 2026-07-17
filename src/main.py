"""Framework spike window for Favur 2048.

Opens a 700x800 non-resizable window titled Favur 2048,
draws a primitive shape, handles Escape-to-quit.

Purpose:
    Validate pygame-ce installation and API existence per SOW mandate,
    prove window creation 700x800 non-resizable titled Favur 2048,
    demonstrate programmatic drawing via draw.rect/circle.

System:
    FrameworkSpike per ADR-001, depends on pygame-ce ^2.5.0 only,
    no dependency on core logic, isolated spike prototype.

Public Interface:
    verify_pygame_api() -> bool: Verify 11 required pygame-ce APIs exist.
    main() -> None: Init, create window, draw primitive, event loop 60 FPS, clean quit.
"""

from __future__ import annotations

import sys

import pygame


def verify_pygame_api() -> bool:
    """Verify required pygame-ce APIs exist per SOW mandate.

    Checks existence of 11 required APIs:
    init, display.set_mode, display.set_caption, event.get,
    QUIT, KEYDOWN, K_ESCAPE, draw.rect, draw.circle,
    time.Clock, quit.

    Returns:
        True if all required APIs exist.

    Raises:
        ImportError: If pygame-ce is not installed or any required API is missing.
    """
    try:
        import pygame as _pg  # noqa: F401 - verify importable
    except ImportError as exc:
        raise ImportError(
            "pygame-ce not installed, run poetry install"
        ) from exc

    required = [
        ("pygame.init", lambda: callable(getattr(pygame, "init", None))),
        ("pygame.display.set_mode", lambda: callable(getattr(getattr(pygame, "display", None), "set_mode", None))),
        ("pygame.display.set_caption", lambda: callable(getattr(getattr(pygame, "display", None), "set_caption", None))),
        ("pygame.event.get", lambda: callable(getattr(getattr(pygame, "event", None), "get", None))),
        ("pygame.QUIT", lambda: hasattr(pygame, "QUIT")),
        ("pygame.KEYDOWN", lambda: hasattr(pygame, "KEYDOWN")),
        ("pygame.K_ESCAPE", lambda: hasattr(pygame, "K_ESCAPE")),
        ("pygame.draw.rect", lambda: callable(getattr(getattr(pygame, "draw", None), "rect", None))),
        ("pygame.draw.circle", lambda: callable(getattr(getattr(pygame, "draw", None), "circle", None))),
        ("pygame.time.Clock", lambda: callable(getattr(getattr(pygame, "time", None), "Clock", None))),
        ("pygame.quit", lambda: callable(getattr(pygame, "quit", None))),
    ]

    missing = [name for name, check in required if not check()]
    if missing:
        raise ImportError(
            f"Missing pygame-ce APIs: {', '.join(missing)}. "
            "Verify installed docs, run poetry install, expected pygame-ce ^2.5.0"
        )
    return True


def main() -> None:
    """Framework spike entry point.

    Init pygame, create 700x800 non-resizable window titled Favur 2048,
    draw primitive, handle QUIT/Escape, 60 FPS, clean quit.

    Returns:
        None. Enters event loop until QUIT or Escape, then exits via sys.exit(0).

    Raises:
        RuntimeError: If pygame.init fails or returns None.
        ImportError: If pygame-ce API verification fails (propagated from verify_pygame_api).
    """
    verify_pygame_api()

    init_result = pygame.init()
    if init_result is None:
        raise RuntimeError("pygame.init() returned None, init failed")

    # FrameworkConfig constants per SOW fixed requirements
    title = "Favur 2048"
    fps = 60
    background_color = (187, 173, 160)

    # Non-resizable per SOW, flags=0 for fixed size window
    # Do NOT pass resizable flag, use 0 for non-resizable default
    # Window size (700, 800) per SOW fixed requirements
    screen = pygame.display.set_mode((700, 800), flags=0)
    pygame.display.set_caption(title)

    clock = pygame.time.Clock()

    # Background fill programmatic
    screen.fill(background_color)

    # Primitive drawing - both rect and circle to prove APIs work
    # Rect at (250,300,200,200) with contrasting color (238,228,218)
    pygame.draw.rect(screen, (238, 228, 218), (250, 300, 200, 200))
    # Circle at (350,400) radius 50 red for visibility
    pygame.draw.circle(screen, (255, 0, 0), (350, 400), 50)

    pygame.display.flip()

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break

            if running:
                # tick(60) caps at 60 FPS per FrameworkConfig
                clock.tick(fps)
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
