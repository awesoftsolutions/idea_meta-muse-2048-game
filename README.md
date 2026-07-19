# Favur 2048

[![CI](https://github.com/placeholder/repo/actions/workflows/ci.yml/badge.svg)](https://github.com/placeholder/repo/actions/workflows/ci.yml)

## Overview
Favur 2048 is a reimagined 5x5 tile-merging puzzle built with Pygame. Slide tiles, merge matching values, chase high scores — but with a twist that adds constant tension and distinct identity beyond vanilla 2048.

Core preserved: 5x5 grid, four-directional slide, matching merge doubles value, random spawn after each move, win/lose detection. Twist adds thermodynamic pressure without breaking the core loop.

## Twist Exploration

### The Challenge
Vanilla 2048 clones fail uniqueness pressure. Requirements:
1. Preserve core 5x5 slide/merge
2. Add consistent tension (not one-off gimmick)
3. Include unconventional mechanic (not just obstacles/power-ups)
4. Create distinct visual and mechanical identity
5. Surprise players — not "bigger board" or "different goal number"

### Ideas Evaluated (5)

#### 1. Thermal Entropy Core [COMMITTED]
- **Description**: Every merge generates heat. Heat spreads to orthogonal neighbors each turn. Edge tiles vent heat. Overheated tiles (heat >= 3) become Unstable — they cannot merge and will crack (downgrade) if not cooled.
- **Unconventional Mechanic**: Thermodynamics — heat diffusion, venting, thermal runaway as core puzzle pressure.
- **Gameplay Effect**: Player must plan merges to keep heat near edges, creates hot/cold zones, forces inefficient merges to cool board.

#### 2. Chrono Echo
- **Description**: Ghost tiles from 3 moves ago reappear at 30% opacity. If ghost overlaps real tile, must resolve by merging or ghost becomes solid blocker for 2 turns.
- **Unconventional Mechanic**: Temporal echo — past board state haunts present.
- **Gameplay Effect**: Memory pressure, forces consideration of future echo placement.

#### 3. Gravity Well Singularity
- **Description**: A singularity token drifts one cell per move toward highest tile cluster. Tiles adjacent to singularity are pulled one step toward it before player slide resolves.
- **Unconventional Mechanic**: Orbital physics — moving attractor with pre-slide pull phase.
- **Gameplay Effect**: Board constantly warps, high-value cluster becomes risk/reward.

#### 4. Mycelial Bloom
- **Description**: Merged tiles leave mycelium trails connecting their origin cells. Connected tiles of same value auto-merge if path exists. Mycelium decays after 4 turns unless refreshed.
- **Unconventional Mechanic**: Fungal network — mycology-based connectivity.
- **Gameplay Effect**: Rewards chain planning, creates organic network visuals.

#### 5. Quantum Entanglement
- **Description**: Every 5th spawn creates an entangled pair (same value, linked color). Merging one instantly doubles the other. If one is blocked from moving, both are blocked.
- **Unconventional Mechanic**: Quantum linking — paired fate across distance.
- **Gameplay Effect**: Risk/reward pairing, spatial reasoning across board.

### Evaluation Matrix

| Idea | Preserves Core 5x5 | Consistent Tension | Unconventional Mechanic | Distinct Identity | Pros | Cons |
|------|-------------------|-------------------|------------------------|------------------|------|------|
| Thermal Entropy Core | PASS - slide/merge unchanged, heat is overlay | PASS - heat accumulates every merge, constant venting decisions | PASS - thermodynamics, heat diffusion not seen in 2048 | PASS - Reactor Core: glowing tiles, heat shimmer, meltdown alarm | Constant pressure, visual feedback natural, merge->heat mapping intuitive, scales with skill | Adds spawn logic complexity, needs heat UI |
| Chrono Echo | PASS | PASS - ghosts every 3 moves | PASS - temporal echo | PASS - Time Anomaly glitch aesthetic | Deep strategy, surprising | Confusing to teach, memory heavy, visual clutter |
| Gravity Well | PASS | PASS - singularity moves each turn | PASS - orbital attractor | PASS - Cosmic Singularity | Dynamic board, strong visual | Can feel random, disrupts planning, frustrates |
| Mycelial Bloom | PASS | PASS - network spreads/decays | PASS - fungal mycology | PASS - Organic Growth | Unique organic theme, linking novel | Hard to balance, niche theme, pathfinding overhead |
| Quantum Entanglement | PASS | PASS - paired risk permanent | PASS - quantum pairing | PASS - Quantum Lab | Novel pairing, high risk/reward | Complex to teach, edge cases on block, pair tracking |

### Committed Twist: Thermal Entropy Core

**Name**: Thermal Entropy Core

**Identity Statement**: You are containing a reactor core. Each merge is a reaction generating heat. The board is the containment vessel. Edges are cooling vents. Let it overheat and tiles crack, lose value, and threaten meltdown. Visual identity: dark reactor interior, tiles glow from cool blue (heat 0) to white-hot (heat 3), heat shimmer particle effect on unstable tiles, edge vents pulse when venting. Audio: low reactor hum rising with average heat.

**Consistent Gameplay Effect**:
- Heat Generation: Merge of value V generates floor(log2(V)/2) heat on resulting tile (2->0, 4->1, 8->1, 16->2, etc.)
- Heat Spread: End of turn, each tile with heat>0 spreads 1 heat to each orthogonal neighbor with lower heat (max 3)
- Venting: Any tile on edge reduces heat by 1 per turn automatically
- Unstable: Heat >=3 = Unstable — cannot merge, displays crack overlay, if still >=3 next turn start, downgrades to half value and heat resets to 1
- Cool Merge: Merging with edge tile vents 1 extra heat from result
- Tension Curve: Early game low heat manageable, mid game heat management becomes primary puzzle, late game thermal runaway forces sacrifice merges

**Rationale**: 
- Preserves core perfectly — heat is overlay, does not alter slide/merge rules
- Consistent tension — every merge has thermal cost, no safe moves late game
- Unconventional — thermodynamics in 2048 is novel, not obstacle/power-up reskin
- Distinct identity — reactor theme strong, programmatic visuals (no asset dependency)
- Surprising — players expect tile puzzle, get heat management sim
- Naturally integrates — merge->heat is intuitive, vent->edge is spatial

**Implementation Hooks**:
- Tile model adds heat: int 0-3
- Board adds heat_spread() and vent() phases after slide
- Renderer adds heat color lerp: #3B82F6 (0) -> #F59E0B (1) -> #EF4444 (2) -> #FFFFFF (3) with glow
- Score bonus for cool merges

### Rejected Alternatives

1. **Chrono Echo** — Rejected: High cognitive load, ghost overlap resolution confusing, violates "easy to learn" principle. Time travel thematically weak for 2048.

2. **Gravity Well Singularity** — Rejected: Pre-slide pull phase breaks player agency, feels random when singularity drifts into cluster. Tension is inconsistent (depends on singularity position).

3. **Mycelial Bloom** — Rejected: Pathfinding for auto-merge adds complexity and performance cost, fungal theme niche, network visual hard to render programmatically without clutter.

4. **Quantum Entanglement** — Rejected: Pair tracking edge cases (what if one entangled tile merges with third tile?), blocking rule frustrates, teaching quantum concept distracts from core loop.

All rejected ideas documented in docs/twist-exploration.md with full pros/cons.

## Thermal Entropy Core Identity

You are containing a reactor core. Each merge is a reaction generating heat. The board is the containment vessel. Edges are cooling vents. Let it overheat and tiles crack, lose value, and threaten meltdown.

- **Twist Name**: Thermal Entropy Core
- **Heat Colors**: #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow
  - 0 = cool blue #3B82F6 calm reactor
  - 1 = warm amber #F59E0B heating
  - 2 = hot red #EF4444 critical
  - 3 = unstable white #FFFFFF white-hot glow with particle shimmer
- **Reactor Chrome Palette**:
  - #0F172A dark reactor interior background
  - #1E293B slate board container
  - #334155 empty cell
  - #475569 border chrome and grid lines
- **Heat Mechanics**:
  - Heat Generation: floor(log2(V)/2) on merge result (2->0, 4->1, 8->1, 16->2, 32->2, 64->3 capped)
  - Venting: edge tiles reduce heat by -1 per turn automatically
  - Unstable: heat >=3 = Unstable — cannot merge, crack overlay, downgrades next turn if still >=3
  - Cool Merge: merging with edge tile vents 1 extra heat
- **Visual Identity**: dark reactor interior #0F172A, tiles lerp #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF with glow, heat shimmer on unstable, edge vents pulse when venting, low reactor hum rising with average heat.

## Installation

Requirements:
- Python 3.11+
- Poetry 1.8+
- pygame-ce dependency (installed via Poetry)

```bash
poetry install
```

This installs `pygame-ce` and all dev dependencies including `pytest` and `PyInstaller`.

## Running

```bash
poetry run python -m src.main
# or
poetry run favur-2048
```

## Controls

- Arrow keys / WASD: Slide tiles (UP/DOWN/LEFT/RIGHT)
- U or Z: Undo last move
- R: Restart game
- Escape: Quit

## How to Run Tests

Tests run headless (no window required) using `pygame-ce` offscreen driver.

```bash
poetry run pytest
# verbose
poetry run pytest -v
# specific file
poetry run pytest tests/test_readme_finalization.py -v
```

- 213+ tests green expected on trunk
- Headless mode: SDL_VIDEODRIVER offscreen handled in test setup
- No watch mode — pytest runs once and exits

## How to Build Standalone Binary

Build a single-file executable with PyInstaller:

```bash
poetry run pyinstaller --onefile --windowed --name favur-2048 src/main.py
```

Notes:
- `--onefile` bundles into single executable
- `--windowed` prevents console popup on Windows (GUI app)
- `--name favur-2048` sets output name
- If pygame modules are missed, add `--hidden-import pygame` or `--hidden-import pygame-ce`
- Alternative via spec file: `poetry run pyinstaller favur-2048.spec`
- Output: `dist/favur-2048.exe` on Windows, `dist/favur-2048` on macOS/Linux
- Verify build log exit 0 and output size>0

### Platform Notes

- **Windows**: produces `dist/favur-2048.exe`, `--windowed` prevents console popup, double-click to run
- **macOS**: produces `dist/favur-2048`, may require `chmod +x dist/favur-2048`, Gatekeeper may require right-click Open or `xattr -d com.apple.quarantine dist/favur-2048`
- **Linux**: produces `dist/favur-2048`, requires executable permission `chmod +x dist/favur-2048`, run via `./dist/favur-2048`

## Visual Proof

Visual regression proof is tracked in `visual-proof/README.md` with 10 entries obs_000001-012.

Manifest fields: file, what it shows, input sequence, observation_id

Required images:
- `phase-1-spike.png` — initial spike prototype
- `phase-3-first-light.png` — first light render
- `phase-4-merge.png` — merge animation
- `phase-4-toast.png` — toast notification
- `phase-4-gameover.png` — game over screen
- `phase-5-tiles-after-moves.png` — tiles after moves
- Optional: `phase-6-binary.png` — standalone binary running

See `visual-proof/README.md` for full manifest with observation IDs obs_000001 through obs_000012.

## Project Structure

- src/config/ — constants (palette, layout, animation)
- src/game/ — board, tile, heat system
- src/render/ — Pygame rendering, heat color lerp #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF
- src/main.py — entry point for `poetry run python -m src.main` and PyInstaller
- docs/twist-exploration.md — full evaluation
- visual-proof/ — screenshots + visual-proof/README.md manifest (10 entries obs_000001-012)
- tests/ — 213+ tests, headless
