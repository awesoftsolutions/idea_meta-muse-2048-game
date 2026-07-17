# Twist Exploration — Favur 2048

**Version**: 1.0
**Date**: 2026-07-17
**Status**: Active
**Task**: Phase 1 Sprint 1 Task 5

## Overview
Evaluation of 5 distinct twist ideas against SOW creative requirements and ADR-004 TwistExploration criteria.

## Constraints (from SOW)
1. Preserve core 5x5 slide/merge
2. Add consistent tension (not one-off)
3. Include unconventional mechanic (not vanilla obstacle/power-up)
4. Create distinct visual and mechanical identity
5. Uniqueness pressure — surprise, not clone

## Ideas

### Idea 1: Thermal Entropy Core [COMMITTED]
- **Description**: Merge generates heat, heat spreads orthogonally, edges vent, heat>=3 unstable and cracks.
- **Unconventional Mechanic**: Thermodynamics — heat diffusion, venting, thermal runaway.
- **Preserves Core**: Yes — overlay system, slide/merge rules unchanged.
- **Tension**: Yes — heat accumulates every move, constant management.
- **Identity**: Reactor Core — glowing tiles blue->white, shimmer, meltdown alarm.
- **Pros**: Constant decisions, visual feedback natural, intuitive merge->heat mapping, scales with skill, programmatic rendering friendly.
- **Cons**: Adds spawn logic complexity, needs heat UI, balancing heat values requires tuning.
- **Score**: 5/5 PASS

### Idea 2: Chrono Echo
- **Description**: Ghost tiles from 3 moves ago reappear at 30% opacity, overlapping ghosts become blockers.
- **Unconventional Mechanic**: Temporal echo — past state haunts present.
- **Preserves Core**: Yes.
- **Tension**: Yes — ghosts interfere every 3 moves.
- **Identity**: Time Anomaly — glitch aesthetic, scanlines.
- **Pros**: Deep strategy, surprising, memory challenge.
- **Cons**: Confusing to teach, visual clutter, memory heavy, violates easy-to-learn.
- **Score**: 4/5 PASS but rejected for complexity.

### Idea 3: Gravity Well Singularity
- **Description**: Moving singularity drifts toward highest cluster, pulls adjacent tiles pre-slide.
- **Unconventional Mechanic**: Orbital physics — moving attractor.
- **Preserves Core**: Yes — pull is pre-phase.
- **Tension**: Partial — depends on singularity position, can feel random.
- **Identity**: Cosmic Singularity — dark center, lensing effect.
- **Pros**: Dynamic board, strong visual, emergent.
- **Cons**: Breaks agency, feels random, frustrates planning, inconsistent tension.
- **Score**: 3/5 FAIL tension consistency.

### Idea 4: Mycelial Bloom
- **Description**: Merged tiles leave mycelium trails, connected same-value tiles auto-merge, trails decay.
- **Unconventional Mechanic**: Fungal mycology — network connectivity.
- **Preserves Core**: Yes.
- **Tension**: Yes — network spreads/decays.
- **Identity**: Organic Growth — fungal veins, organic glow.
- **Pros**: Unique organic theme, linking novel, rewards chain planning.
- **Cons**: Pathfinding overhead, hard to balance, niche theme, visual clutter.
- **Score**: 4/5 PASS but rejected for complexity.

### Idea 5: Quantum Entanglement
- **Description**: Every 5th spawn creates entangled pair, merging one doubles other, blocking linked.
- **Unconventional Mechanic**: Quantum linking — paired fate.
- **Preserves Core**: Yes.
- **Tension**: Yes — paired risk permanent.
- **Identity**: Quantum Lab — linked color pulse, particle line.
- **Pros**: Novel pairing, high risk/reward, spatial reasoning.
- **Cons**: Complex to teach, edge cases on merge, pair tracking overhead, blocking frustrates.
- **Score**: 4/5 PASS but rejected for edge cases.

## Evaluation Matrix

| Idea | Preserves Core | Consistent Tension | Unconventional | Distinct Identity | Pros | Cons | Verdict |
|------|---------------|-------------------|----------------|-------------------|------|------|---------|
| Thermal Entropy Core | PASS | PASS | PASS thermodynamics | PASS Reactor Core | Constant pressure, visual natural, intuitive | Balancing needed | COMMITTED |
| Chrono Echo | PASS | PASS | PASS temporal | PASS Time Glitch | Deep, surprising | Confusing, clutter | REJECTED - complexity |
| Gravity Well | PASS | FAIL inconsistent | PASS orbital | PASS Cosmic | Dynamic, visual | Random, breaks agency | REJECTED - agency |
| Mycelial Bloom | PASS | PASS | PASS mycology | PASS Organic | Unique, linking | Pathfinding, niche | REJECTED - complexity |
| Quantum Entanglement | PASS | PASS | PASS quantum | PASS Quantum Lab | Novel, risk/reward | Edge cases, teach | REJECTED - edge cases |

## Committed Twist Details

**Name**: Thermal Entropy Core
**Type**: Overlay system — heat: int 0-3 per tile

**Rules**:
- Heat Generation: floor(log2(V)/2) on merge result
- Heat Spread: end of turn, spread 1 to orthogonal lower-heat neighbors
- Venting: edge tiles -1 heat per turn
- Unstable: heat>=3 cannot merge, crack overlay, downgrades next turn if still >=3
- Cool Merge: merging with edge tile vents extra 1

**Visual Identity**:
- Palette: heat 0 #3B82F6 blue, 1 #F59E0B amber, 2 #EF4444 red, 3 #FFFFFF white-hot
- Effects: glow radius = heat*2px, shimmer particles on heat 3, edge vent pulse animation
- Theme: reactor interior dark #0F172A, containment vessel border

**Rationale**:
- Only idea with PASS on all 5 constraints without caveats
- Thermodynamics novel in 2048 space
- Heat naturally maps to merge (reaction = heat)
- Tension curve perfect: early manageable, late runaway
- Programmatic rendering: color lerp + glow, no assets needed
- Distinct identity strong and marketable

**Rejected Alternatives Summary**:
- Chrono Echo: rejected for cognitive load and visual clutter
- Gravity Well: rejected for agency break and inconsistent tension
- Mycelial Bloom: rejected for pathfinding complexity and niche theme
- Quantum Entanglement: rejected for edge cases and teaching complexity
