"""HUD with score, high_score, achievement toasts, reactor chrome identity.

Purpose:
    Implements HUD overlay on 700x800 Favur 2048 window with reactor chrome
    #0F172A background, #1E293B board, #334155 empty, #475569 border and
    heat identity #3B82F6 cool 0 -> #F59E0B warm 1 -> #EF4444 hot 2 ->
    #FFFFFF unstable glow. Provides Toast queue timed 2-3 sec stacking
    vertical gap 10 max 5 alpha fading last 0.5 sec scale pulse
    1.0->1.2->1.0 200ms particles per heat. Programmatic only via pygame
    draw rect/circle SysFont SRCALPHA temp surface no external assets
    no board mutation headless importable.

System:
    RenderHUD per Phase 4 Sprint 2 Task 1. Part of src/render
    subsystem per Phase 4 architecture IHUDRenderer, IToastManager,
    IGameOverOverlay. Part of src/render subsystem per Phase 4 architecture.

Dependencies:
    pygame-ce (local import for headless fallback, programmatic only
    rect/circle/alpha SysFont, no external image loading, no font file path),
    stdlib math random dataclasses typing,
    No src/core imports to preserve headless separation (only Any for
    game_state/layout duck typing).

Used-by:
    - src/render/__init__.py exports draw_hud, draw_hud_with_gamestate,
      ToastManager, draw_game_over, Toast
    - src/main.py wiring HUD + toasts + game-over overlay R restart screenshot hooks
    - tests/test_hud.py 29 unit tests
    - tests/test_hud_smoke.py 7 smoke tests
    - tests/test_phase_exit_verification.py HUD verification

Public Interface:
    Constants:
        REACTOR_BG: Tuple[int,int,int] = (15,23,42) #0F172A
        BOARD_BG: Tuple[int,int,int] = (30,41,59) #1E293B
        EMPTY_CELL: Tuple[int,int,int] = (51,65,85) #334155
        BORDER: Tuple[int,int,int] = (71,85,105) #475569
        HEAT_COOL: Tuple[int,int,int] = (59,130,246) #3B82F6
        HEAT_WARM: Tuple[int,int,int] = (245,158,11) #F59E0B
        HEAT_HOT: Tuple[int,int,int] = (239,68,68) #EF4444
        HEAT_UNSTABLE: Tuple[int,int,int] = (255,255,255) #FFFFFF
        WINDOW_W: int = 700, WINDOW_H: int = 800, HUD_H: int = 120
        TOAST_W: int = 200, TOAST_H: int = 60, TOAST_DURATION: float = 2.5
        TOAST_GAP: int = 10, MAX_TOASTS: int = 5
        WINDOW_WIDTH: int = 700 alias
        WINDOW_HEIGHT: int = 800 alias
        TOAST_WIDTH: int = 200 alias
        TOAST_HEIGHT: int = 60 alias
    Classes:
        Toast dataclass:
            Attributes:
                achievement_id: str, title: str, description: str,
                elapsed: float=0.0, duration: float=2.5, y_offset: int=0,
                alpha: int=255, scale: float=1.0, heat_treatment: str="cool",
                particles: List[Dict[str,Any]]=field(default_factory=list)
            Methods:
                __post_init__() -> None
                    Initializes heat_treatment and particles from achievement_id.
        ToastManager class:
            Attributes: max_toasts: int, toasts: List[Toast]
            Methods:
                __init__(self, max_toasts: int=5) -> None
                    Initializes empty toast queue.
                push(self, achievements: List[Any]) -> None
                    Pushes achievements as toasts with stacking and pulse.
                    Args: achievements List of achievement dicts or objects.
                    Raises: ValueError if achievements is None.
                update(self, dt: float) -> None
                    Advances queue timing and animation.
                    Args: dt delta time seconds.
                    Raises: ValueError if dt is None or negative.
                draw(self, surface: Any) -> None
                    Draws toasts stacking top-right with reactor chrome and particles.
                    Args: surface pygame surface 700x800 or mock.
                    Raises: ValueError if surface is None.
                has_visible(self) -> bool
                    Checks if any toast visible, True if len>0 and any alpha>0.
    Functions:
        _heat_color_for_treatment(treatment: str) -> Tuple[int,int,int]
            Maps heat treatment string to RGB color.
        _determine_heat_treatment(achievement_id: str) -> str
            Determines heat treatment from achievement_id substrings.
        _create_toast_particles(heat_treatment: str, x: float, y: float) -> List[Dict[str,Any]]
            Creates toast particles per heat identity.
        _draw_reactor_chrome_panel(surface: Any, rect: Tuple[int,int,int,int], color: Tuple[int,int,int], border_color: Tuple[int,int,int], alpha: int=255) -> None
            Draws reactor chrome panel with background and border.
            Raises: ValueError if surface is None.
        draw_hud(surface: Any, score: int, high_score: int, game_state: Any, layout: Any) -> None
            Draws HUD area top background #0F172A score current top-left SysFont 36.
            Args: surface 700x800, score current, high_score persisted, game_state
            with move_count vent_streak unstable_survival, layout with hud_rect.
            Raises: ValueError if surface None or game_state None.
        draw_hud_with_gamestate(surface: Any, score: int, high_score: int, game_state: Any, layout: Any) -> None
            Wrapper for backward compat, calls draw_hud with same args.
            Args: surface, score, high_score, game_state, layout.
            Raises: ValueError if surface None or game_state None.
        draw_game_over(surface: Any, score: int, high_score: int, layout: Any=None) -> None
            Draws game-over overlay dim 50% alpha #0F172A 700x800 Game Over centered.
            Args: surface 700x800, score final, high_score persisted, layout optional.
            Raises: ValueError if surface None.
        draw_game_over_stub(surface: Any, score: int, high_score: int, layout: Any=None) -> None
            Minimal stub for game-over overlay maintaining compat, calls draw_game_over.
            Args: surface 700x800, score final, high_score, layout optional.
            Raises: ValueError if surface None.
"""
# CHANGELOG:
# - Phase 4 Sprint 1: CREATED ToastManager with Toast dataclass achievement_id
#   title description elapsed duration y_offset alpha scale heat_treatment
#   particles, heat-aware particles cool #3B82F6 calm drift warm #F59E0B flicker
#   hot #EF4444 intense spark unstable #FFFFFF burst, stacking vertical gap 10
#   max 5 alpha fading last 0.5 sec scale pulse 1.0->1.2->1.0 200ms reactor
#   chrome #0F172A #1E293B #334155 #475569 programmatic only rect/circle alpha
#   SysFont no board mutation headless importable.
# - Phase 4 Sprint 2 Task 1: REFINED draw_hud canonical signature
#   (surface, score, high_score, game_state, layout) per IHUDRenderer,
#   implemented draw_game_over full spec dim 50% alpha #0F172A overlay
#   700x800 Game Over centered SysFont 48 final score high-score restart
#   prompt Press R to restart, kept draw_game_over_stub compat.
# - Phase 4 Sprint 3: VERIFIED ToastManager HUD toasts gameover overlay
#   wiring in main loop screenshot gating, no logic change, changelog compliance.
# - Phase 5 Sprint 2: FINALIZED visual-proof sweep manifest 7+ entries
#   obs_000001-012 gating PASS Q-001 avg 1.385, toast base_x 10 width 200
#   stacking gap 10 max 5 alpha fading scale pulse verification.
# - Phase 6 Sprint 1: Q-018 FIX base_y 130 below HUD_H 120px —
#   Toast base_y 130 y=130+idx*(60+10) no overlap Score (20,20) Best 550,
#   toast_rect base_y 130 below HUD_H 120px, packaging hardening CI workflow
#   validation, visual-proof sweep finalization.

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Constants — reactor chrome and heat identity per spec
# ---------------------------------------------------------------------------

# Reactor chrome #0F172A #1E293B #334155 #475569
REACTOR_BG: Tuple[int, int, int] = (15, 23, 42)  # #0F172A
BOARD_BG: Tuple[int, int, int] = (30, 41, 59)  # #1E293B
EMPTY_CELL: Tuple[int, int, int] = (51, 65, 85)  # #334155
BORDER: Tuple[int, int, int] = (71, 85, 105)  # #475569

# Heat identity #3B82F6 #F59E0B #EF4444 #FFFFFF
HEAT_COOL: Tuple[int, int, int] = (59, 130, 246)  # #3B82F6 cool 0 calm drift 2-3 particles
HEAT_WARM: Tuple[int, int, int] = (245, 158, 11)  # #F59E0B warm 1 flicker 4-5
HEAT_HOT: Tuple[int, int, int] = (239, 68, 68)  # #EF4444 hot 2 intense spark 6-8
HEAT_UNSTABLE: Tuple[int, int, int] = (255, 255, 255)  # #FFFFFF unstable 3 glow burst 10+

# Window and HUD layout
WINDOW_W: int = 700
WINDOW_H: int = 800
HUD_H: int = 120
TOAST_W: int = 200
TOAST_H: int = 60
TOAST_DURATION: float = 2.5
TOAST_GAP: int = 10
MAX_TOASTS: int = 5

# Aliases for compatibility
WINDOW_WIDTH: int = WINDOW_W
WINDOW_HEIGHT: int = WINDOW_H
TOAST_WIDTH: int = 200
TOAST_HEIGHT: int = TOAST_H


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _heat_color_for_treatment(treatment: str) -> Tuple[int, int, int]:
    """Map heat treatment string to RGB color.

    Args:
        treatment: cool/warm/hot/unstable string.

    Returns:
        RGB tuple per heat identity.
    """
    if treatment == "cool":
        return HEAT_COOL
    if treatment == "warm":
        return HEAT_WARM
    if treatment == "hot":
        return HEAT_HOT
    if treatment == "unstable":
        return HEAT_UNSTABLE
    return HEAT_COOL


def _determine_heat_treatment(achievement_id: str) -> str:
    """Determine heat treatment from achievement_id substrings.

    Args:
        achievement_id: Achievement identifier string.

    Returns:
        Heat treatment string cool/warm/hot/unstable.
    """
    if not isinstance(achievement_id, str):
        return "cool"
    lower_id = achievement_id.lower()
    if "unstable" in lower_id or "entropy" in lower_id:
        return "unstable"
    if "hot" in lower_id or "vent" in lower_id:
        return "hot"
    if "warm" in lower_id or "heat" in lower_id:
        return "warm"
    if "cold" in lower_id or "fusion" in lower_id:
        return "cool"
    return "cool"


def _create_toast_particles(
    heat_treatment: str, x: float, y: float
) -> List[Dict[str, Any]]:
    """Create toast particles per heat identity.

    Args:
        heat_treatment: cool/warm/hot/unstable.
        x: Screen x coordinate for spawn.
        y: Screen y coordinate for spawn.

    Returns:
        List of particle dicts with x,y,vx,vy,life,max_life,color,size,alpha,heat.
    """
    if heat_treatment == "cool":
        count = random.randint(2, 3)
    elif heat_treatment == "warm":
        count = random.randint(4, 5)
    elif heat_treatment == "hot":
        count = random.randint(6, 8)
    elif heat_treatment == "unstable":
        count = random.randint(10, 12)
    else:
        count = random.randint(2, 3)

    color = _heat_color_for_treatment(heat_treatment)
    particles: List[Dict[str, Any]] = []

    for i in range(count):
        if heat_treatment == "cool":
            vx = random.uniform(-30, 30)
            vy = random.uniform(-30, -10)
            size = random.randint(2, 3)
            life = 1.0
            alpha = 200
        elif heat_treatment == "warm":
            vx = random.uniform(-60, 60)
            vy = random.uniform(-50, -20)
            size = random.randint(2, 4)
            life = 0.8
            alpha = random.randint(150, 255)
        elif heat_treatment == "hot":
            vx = random.uniform(-100, 100)
            vy = random.uniform(-80, -40)
            size = random.randint(3, 5)
            life = 0.6
            alpha = 255
        else:  # unstable white burst 360 degrees
            angle = (2 * math.pi * i) / max(count, 1)
            speed = random.uniform(80, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(4, 6)
            life = 0.5
            alpha = 255

        particle = {
            "x": x,
            "y": y,
            "vx": vx,
            "vy": vy,
            "life": life,
            "max_life": life,
            "color": color,
            "size": size,
            "alpha": alpha,
            "heat": heat_treatment,
        }
        particles.append(particle)

    return particles


def _draw_reactor_chrome_panel(
    surface: Any,
    rect: Tuple[int, int, int, int],
    color: Tuple[int, int, int],
    border_color: Tuple[int, int, int],
    alpha: int = 255,
) -> None:
    """Draw reactor chrome panel with background and border.

    Args:
        surface: Pygame surface or mock surface.
        rect: (x,y,w,h) rectangle.
        color: Background RGB.
        border_color: Border RGB #475569.
        alpha: Alpha 0-255, if <255 uses SRCALPHA temp surface.

    Raises:
        ValueError: If surface is None.
    """
    if surface is None:
        raise ValueError("surface None")

    try:
        import pygame
    except ImportError:
        pygame = None  # type: ignore

    x, y, w, h = rect

    if pygame is not None:
        try:
            if alpha < 255:
                temp = pygame.Surface((w, h), pygame.SRCALPHA)
                temp.fill((color[0], color[1], color[2], alpha))
                surface.blit(temp, (x, y))
            else:
                pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, border_color, rect, 2)
        except (ValueError, TypeError, AttributeError, RuntimeError):
            try:
                if pygame is not None:
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, border_color, rect, 2)
            except (ValueError, TypeError, AttributeError, RuntimeError):
                pass
    else:
        try:
            surface.fill(color)  # type: ignore
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass


# ---------------------------------------------------------------------------
# Toast dataclass
# ---------------------------------------------------------------------------


@dataclass
class Toast:
    """Single achievement toast with animation state scaling particles.

    Attributes:
        achievement_id: Achievement identifier e.g., cold_fusion.
        title: Display title.
        description: Short description.
        elapsed: Time since push seconds.
        duration: Display duration sec 2.5.
        y_offset: Stacking vertical offset.
        alpha: Fading alpha 0-255.
        scale: Pulse scaling 1.0->1.2->1.0.
        heat_treatment: cool/warm/hot/unstable derived from achievement type.
        particles: Scaling particles per heat identity.
    """

    achievement_id: str
    title: str
    description: str
    elapsed: float = 0.0
    duration: float = 2.5
    y_offset: int = 0
    alpha: int = 255
    scale: float = 1.0
    heat_treatment: str = "cool"
    particles: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize heat_treatment and particles from achievement_id."""
        derived = _determine_heat_treatment(self.achievement_id)
        self.heat_treatment = derived

        base_x = 10
        base_y = 130  # Q-018 fix: below HUD_H 120px to avoid Score (20,20) and Best 550
        toast_x = float(base_x + TOAST_W // 2)
        toast_y = float(base_y + TOAST_H // 2)
        if not self.particles:
            self.particles = _create_toast_particles(self.heat_treatment, toast_x, toast_y)

        self.scale = 1.0
        self.alpha = 255
        self.elapsed = 0.0


# ---------------------------------------------------------------------------
# ToastManager
# ---------------------------------------------------------------------------


class ToastManager:
    """Queue timed stacking Thermal Entropy treatment.

    Manages toast queue max 5, timed 2-3 sec, stacking gap 10px,
    non-blocking, alpha fading last 0.5 sec, scale pulse 1.0->1.2->1.0.
    """

    def __init__(self, max_toasts: int = 5) -> None:
        """Initialize empty toast queue.

        Args:
            max_toasts: Maximum toasts bounded to prevent memory leak.
        """
        self.max_toasts: int = max_toasts
        self.toasts: List[Toast] = []

    def push(self, achievements: List[Any]) -> None:
        """Push achievements as toasts with stacking and pulse.

        Args:
            achievements: List of achievement dicts or objects with id/title/description.

        Raises:
            ValueError: If achievements is None with message achievements None.
        """
        if achievements is None:
            raise ValueError("achievements None")

        if len(achievements) == 0:
            return

        for achievement in achievements:
            if len(self.toasts) >= self.max_toasts:
                self.toasts.pop(0)

            achievement_id = ""
            title = ""
            description = ""

            if isinstance(achievement, dict):
                achievement_id = str(achievement.get("id", achievement.get("achievement_id", "")))
                title = str(achievement.get("title", achievement_id))
                description = str(achievement.get("description", ""))
            else:
                achievement_id = str(
                    getattr(achievement, "id", getattr(achievement, "achievement_id", str(achievement)))
                )
                title = str(getattr(achievement, "title", achievement_id))
                description = str(getattr(achievement, "description", ""))

            toast = Toast(
                achievement_id=achievement_id,
                title=title,
                description=description,
            )

            toast.scale = 1.2
            toast.y_offset = len(self.toasts) * (TOAST_H + TOAST_GAP)

            self.toasts.append(toast)

        for idx, t in enumerate(self.toasts):
            t.y_offset = idx * (TOAST_H + TOAST_GAP)

    def update(self, dt: float) -> None:
        """Advance queue timing and animation.

        Args:
            dt: Delta time seconds.

        Raises:
            ValueError: If dt is None or negative with message dt negative.
        """
        if dt is None:
            raise ValueError("dt None")
        if not isinstance(dt, (int, float)):
            raise ValueError("dt None")
        if dt < 0:
            raise ValueError("dt negative")
        if dt == 0:
            return

        for toast in self.toasts:
            toast.elapsed += dt

            if toast.elapsed > toast.duration - 0.5:
                remaining = toast.duration - toast.elapsed
                if remaining < 0:
                    remaining = 0
                toast.alpha = int(255 * (remaining / 0.5))
                if toast.alpha < 0:
                    toast.alpha = 0
                if toast.alpha > 255:
                    toast.alpha = 255
            else:
                toast.alpha = 255

            if toast.elapsed < 0.2:
                toast.scale = 1.0 + 0.2 * (1 - toast.elapsed / 0.2)
            else:
                toast.scale = 1.0

            for p in toast.particles:
                try:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["life"] -= dt
                    max_life = p.get("max_life", 1.0)
                    if max_life > 0:
                        p["alpha"] = int(255 * p["life"] / max_life)
                    else:
                        p["alpha"] = 0
                    if p["alpha"] < 0:
                        p["alpha"] = 0
                    if p["alpha"] > 255:
                        p["alpha"] = 255
                except (KeyError, TypeError, ValueError):
                    continue

            toast.particles = [p for p in toast.particles if p.get("life", 0) > 0]

        self.toasts = [t for t in self.toasts if t.elapsed < t.duration]

        for idx, t in enumerate(self.toasts):
            t.y_offset = idx * (TOAST_H + TOAST_GAP)

    def draw(self, surface: Any) -> None:
        """Draw toasts stacking top-right with reactor chrome and particles.

        Args:
            surface: Pygame surface 700x800 or mock surface.

        Raises:
            ValueError: If surface is None with message surface None.
        """
        if surface is None:
            raise ValueError("surface None")

        try:
            import pygame
        except ImportError:
            pygame = None  # type: ignore

        for index, toast in enumerate(self.toasts):
            base_x = 10
            # Q-018 fix: base_y 130 below HUD_H 120px y=130+idx*(60+10) no overlap Score (20,20) Best 550
            base_y = 130 + toast.y_offset  # 130+idx*(60+10) where y_offset=idx*(TOAST_H+TOAST_GAP)

            scaled_w = int(TOAST_W * toast.scale)
            scaled_h = int(TOAST_H * toast.scale)
            cx = base_x + TOAST_W // 2
            cy = base_y + TOAST_H // 2
            draw_x = cx - scaled_w // 2
            draw_y = cy - scaled_h // 2

            bg_color = _heat_color_for_treatment(toast.heat_treatment)

            try:
                _draw_reactor_chrome_panel(
                    surface,
                    (draw_x, draw_y, scaled_w, scaled_h),
                    bg_color,
                    BORDER,
                    alpha=toast.alpha,
                )
            except ValueError:
                raise
            except (ValueError, TypeError, AttributeError, RuntimeError):
                pass

            if pygame is not None:
                try:
                    title_font = pygame.font.SysFont(None, 20)
                    title_text = title_font.render(toast.title, True, (255, 255, 255))
                    if toast.alpha < 255:
                        temp_title = pygame.Surface(
                            (title_text.get_width(), title_text.get_height()), pygame.SRCALPHA
                        )
                        temp_title.blit(title_text, (0, 0))
                        temp_title.set_alpha(toast.alpha)
                        surface.blit(temp_title, (draw_x + 5, draw_y + 5))
                    else:
                        surface.blit(title_text, (draw_x + 5, draw_y + 5))

                    desc_font = pygame.font.SysFont(None, 16)
                    desc_text = desc_font.render(toast.description, True, (200, 200, 200))
                    if toast.alpha < 255:
                        temp_desc = pygame.Surface(
                            (desc_text.get_width(), desc_text.get_height()), pygame.SRCALPHA
                        )
                        temp_desc.blit(desc_text, (0, 0))
                        temp_desc.set_alpha(toast.alpha)
                        surface.blit(temp_desc, (draw_x + 5, draw_y + 25))
                    else:
                        surface.blit(desc_text, (draw_x + 5, draw_y + 25))

                    for p in toast.particles:
                        try:
                            if p.get("alpha", 0) <= 0:
                                continue
                            px = int(p.get("x", 0))
                            py = int(p.get("y", 0))
                            size = int(p.get("size", 2))
                            color = p.get("color", bg_color)
                            alpha = int(p.get("alpha", 255))
                            diam = max(1, size * 2)
                            temp_p = pygame.Surface((diam, diam), pygame.SRCALPHA)
                            pygame.draw.circle(
                                temp_p,
                                (color[0], color[1], color[2], alpha),
                                (size, size),
                                size,
                            )
                            surface.blit(temp_p, (px - size, py - size))
                        except (ValueError, TypeError, KeyError, AttributeError):
                            try:
                                pygame.draw.circle(
                                    surface,
                                    p.get("color", bg_color),
                                    (int(p.get("x", 0)), int(p.get("y", 0))),
                                    int(p.get("size", 2)),
                                )
                            except (ValueError, TypeError, AttributeError, KeyError, RuntimeError):
                                pass
                        except (ValueError, TypeError, AttributeError, KeyError, RuntimeError):
                            pass
                except (ValueError, TypeError, AttributeError, RuntimeError):
                    pass

    def has_visible(self) -> bool:
        """Check if any toast visible.

        Returns:
            True if len>0 and any alpha>0.
        """
        if len(self.toasts) == 0:
            return False
        for toast in self.toasts:
            if toast.alpha > 0:
                return True
        return False


# ---------------------------------------------------------------------------
# Primary HUD draw function canonical architecture signature IHUDRenderer
# ---------------------------------------------------------------------------


def draw_hud(
    surface: Any,
    score: int,
    high_score: int,
    game_state: Any,
    layout: Any,
) -> None:
    """Draw HUD area top background #0F172A score current top-left SysFont 36.

    Implements IHUDRenderer canonical signature per architecture:
    draw_hud(surface, score, high_score, game_state, layout) with reactor
    chrome #0F172A #1E293B #334155 #475569 and heat legend #3B82F6 #F59E0B
    #EF4444 #FFFFFF.

    Args:
        surface: Pygame surface 700x800.
        score: Current score int.
        high_score: Best score int.
        game_state: GameState with move_count vent_streak unstable_survival.
        layout: RenderLayout with hud_rect() or None uses default (0,0,700,120).

    Raises:
        ValueError: If surface is None or game_state is None.
    """
    if surface is None:
        raise ValueError("surface None")
    if game_state is None:
        raise ValueError("game_state None")

    if score is None:
        score = 0
    if high_score is None:
        high_score = 0

    try:
        import pygame
    except ImportError:
        pygame = None  # type: ignore

    # Determine hud_rect: if layout not None and has hud_rect callable -> call else default
    hud_rect: Tuple[int, int, int, int] = (0, 0, WINDOW_W, HUD_H)
    if layout is not None:
        try:
            hud_rect_method = getattr(layout, "hud_rect", None)
            if callable(hud_rect_method):
                result = hud_rect_method()
                if result is not None and len(result) == 4:
                    hud_rect = tuple(result)  # type: ignore
        except (AttributeError, ValueError, TypeError, RuntimeError):
            pass

    # Draw reactor chrome background #0F172A via _draw_reactor_chrome_panel
    try:
        _draw_reactor_chrome_panel(surface, hud_rect, REACTOR_BG, BORDER, alpha=255)
    except ValueError:
        raise
    except (ValueError, TypeError, AttributeError, RuntimeError):
        pass

    if pygame is not None:
        # Score current top-left SysFont None 36 white "Score: {score}" at (20,20)
        try:
            score_font = pygame.font.SysFont(None, 36)
            score_text = score_font.render(f"Score: {score}", True, (255, 255, 255))
            surface.blit(score_text, (20, 20))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # High-score top-right SysFont None 24 warm #F59E0B "Best: {high_score}"
        try:
            high_font = pygame.font.SysFont(None, 24)
            high_text = high_font.render(f"Best: {high_score}", True, HEAT_WARM)
            try:
                surf_w = surface.get_width()
            except (AttributeError, ValueError, TypeError, RuntimeError):
                surf_w = WINDOW_W
            hx = surf_w - 150
            if hx < 0:
                hx = 20
            surface.blit(high_text, (hx, 20))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Move count middle SysFont 24 white "Moves: {game_state.move_count}" at (200,20)
        try:
            move_count = getattr(game_state, "move_count", None)
            if move_count is not None:
                font = pygame.font.SysFont(None, 24)
                text = font.render(f"Moves: {move_count}", True, (255, 255, 255))
                surface.blit(text, (200, 20))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # vent_streak indicator any edge vented: getattr vent_streak int if >0 render
        try:
            vent_streak = getattr(game_state, "vent_streak", 0)
            if isinstance(vent_streak, int):
                if vent_streak > 0:
                    font = pygame.font.SysFont(None, 24)
                    text = font.render(f"Vent: {vent_streak}", True, HEAT_WARM)
                    surface.blit(text, (350, 20))
                else:
                    # Still render with cool color for visibility when 0? per spec show indicator
                    # Render only if >0 to avoid clutter, but spec says indicator any edge vented
                    pass
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # unstable_survival indicator survived with unstable present
        try:
            unstable_survival = getattr(game_state, "unstable_survival", 0)
            if isinstance(unstable_survival, int) and unstable_survival > 0:
                font = pygame.font.SysFont(None, 24)
                text = font.render(f"Survival: {unstable_survival}", True, HEAT_UNSTABLE)
                surface.blit(text, (450, 20))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Heat legend #3B82F6 #F59E0B #EF4444 #FFFFFF small rects 15x15 with labels
        try:
            legend_x = 20
            legend_y = 60
            heat_colors = [HEAT_COOL, HEAT_WARM, HEAT_HOT, HEAT_UNSTABLE]
            heat_labels = ["cool", "warm", "hot", "unstable"]
            legend_font = pygame.font.SysFont(None, 14)
            for idx, (h_color, h_label) in enumerate(zip(heat_colors, heat_labels)):
                lx = legend_x + idx * (15 + 40)
                try:
                    pygame.draw.rect(surface, h_color, (lx, legend_y, 15, 15))
                except (ValueError, TypeError, AttributeError, RuntimeError):
                    pass
                try:
                    label_text = legend_font.render(h_label, True, (255, 255, 255))
                    surface.blit(label_text, (lx + 18, legend_y))
                except (ValueError, TypeError, AttributeError, RuntimeError):
                    pass
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Reactor chrome border #475569 around hud_rect width 2
        try:
            pygame.draw.rect(surface, BORDER, hud_rect, 2)
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Mode label overlay fixed corner per SOW Thermal Entropy Core bottom-left SysFont 18 border #475569 at (20,100)
        try:
            mode_font = pygame.font.SysFont(None, 18)
            mode_text = mode_font.render("Thermal Entropy Core", True, BORDER)
            surface.blit(mode_text, (20, 100))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass


# ---------------------------------------------------------------------------
# Wrapper for backward compat calling canonical draw_hud
# ---------------------------------------------------------------------------


def draw_hud_with_gamestate(
    surface: Any,
    score: int,
    high_score: int,
    game_state: Any,
    layout: Any,
) -> None:
    """Wrapper for backward compat, calls draw_hud with same args.

    Args:
        surface: Pygame surface.
        score: Current score.
        high_score: Best score.
        game_state: GameState with move_count, vent_streak, unstable_survival.
        layout: RenderLayout with hud_rect() or None uses default.

    Raises:
        ValueError: If surface is None or game_state is None.
    """
    if surface is None:
        raise ValueError("surface None")
    if game_state is None:
        raise ValueError("game_state None")

    try:
        draw_hud(surface, score, high_score, game_state, layout)
    except ValueError:
        raise
    except (ValueError, TypeError, AttributeError, RuntimeError):
        pass


# ---------------------------------------------------------------------------
# Game-over overlay full spec IGameOverOverlay
# ---------------------------------------------------------------------------


def draw_game_over(
    surface: Any,
    score: int,
    high_score: int,
    layout: Any = None,
) -> None:
    """Draw game-over overlay dim 50% alpha #0F172A 700x800 Game Over centered.

    Implements IGameOverOverlay per architecture: overlay surface 700x800
    alpha 128 50% #0F172A dim background, Game Over label centered SysFont 48
    bold final score high-score restart prompt Press R to restart.

    Args:
        surface: Pygame surface 700x800.
        score: Final score int.
        high_score: Best score int.
        layout: Optional RenderLayout.

    Raises:
        ValueError: If surface is None.
    """
    if surface is None:
        raise ValueError("surface None")

    if score is None:
        score = 0
    if high_score is None:
        high_score = 0

    try:
        import pygame
    except ImportError:
        pygame = None  # type: ignore

    if pygame is not None:
        # Create overlay surface clipped to y>=HUD_H to preserve HUD top 120px
        # HUD preserved during game-over dim top 120px per Q-016
        try:
            overlay = pygame.Surface((WINDOW_W, WINDOW_H - HUD_H), pygame.SRCALPHA)
            overlay.fill((REACTOR_BG[0], REACTOR_BG[1], REACTOR_BG[2], 128))
            surface.blit(overlay, (0, HUD_H))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Game Over label centered SysFont None 48 bold #FFFFFF "Game Over" at centered WINDOW_W//2 - rect.width//2, 400
        try:
            font_large = pygame.font.SysFont(None, 48)
            game_over_text = font_large.render("Game Over", True, (255, 255, 255))
            try:
                rect = game_over_text.get_rect()
                cx = WINDOW_W // 2 - rect.width // 2
            except (AttributeError, ValueError, TypeError, RuntimeError):
                cx = 250
            surface.blit(game_over_text, (cx, 400))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Final score high-score SysFont 36 white "Score: {score} Best: {high_score}" centered at WINDOW_W//2 - width//2,450
        try:
            font_mid = pygame.font.SysFont(None, 36)
            final_text = font_mid.render(f"Score: {score} Best: {high_score}", True, (255, 255, 255))
            try:
                rect = final_text.get_rect()
                cx = WINDOW_W // 2 - rect.width // 2
            except (AttributeError, ValueError, TypeError, RuntimeError):
                cx = 200
            surface.blit(final_text, (cx, 450))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Reactor meltdown/cool-down identity: subtle tint via overlay already #0F172A
        # Restart prompt Press R to restart SysFont 24 #F59E0B centered at 500
        try:
            font_small = pygame.font.SysFont(None, 24)
            restart_text = font_small.render("Press R to restart", True, HEAT_WARM)
            try:
                rect = restart_text.get_rect()
                cx = WINDOW_W // 2 - rect.width // 2
            except (AttributeError, ValueError, TypeError, RuntimeError):
                cx = 250
            surface.blit(restart_text, (cx, 500))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass

        # Escape prompt Press Escape to quit SysFont 18 #475569 centered at 530
        try:
            font_tiny = pygame.font.SysFont(None, 18)
            esc_text = font_tiny.render("Press Escape to quit", True, BORDER)
            try:
                rect = esc_text.get_rect()
                cx = WINDOW_W // 2 - rect.width // 2
            except (AttributeError, ValueError, TypeError, RuntimeError):
                cx = 250
            surface.blit(esc_text, (cx, 530))
        except (ValueError, TypeError, AttributeError, RuntimeError):
            pass


# ---------------------------------------------------------------------------
# Minimal stub for backward compat calling full draw_game_over
# ---------------------------------------------------------------------------


def draw_game_over_stub(
    surface: Any,
    score: int,
    high_score: int,
    layout: Any = None,
) -> None:
    """Minimal stub for game-over overlay maintaining compat.

    Args:
        surface: Pygame surface 700x800.
        score: Final score.
        high_score: Best score.
        layout: Optional layout.

    Raises:
        ValueError: If surface is None.
    """
    if surface is None:
        raise ValueError("surface None")

    draw_game_over(surface, score, high_score, layout)
