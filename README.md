# Favur 2048

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

## Installation

```bash
poetry install
```

## Running

```bash
poetry run python -m src.main
# or
poetry run favur-2048
```

## Controls
- Arrow keys / WASD: Slide
- R: Restart
- ESC: Quit

## Project Structure
- src/config/ — constants (palette, layout, animation)
- src/game/ — board, tile, heat system
- docs/twist-exploration.md — full evaluation
