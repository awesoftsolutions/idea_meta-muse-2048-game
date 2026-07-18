# Q-001 Heat Balance Re-measurement — Phase 4 Sprint 3 Task 3

**Date:** 2026-07-18
**Phase:** 4 Sprint 3 Task 3
**Status:** RESOLVED — avg <2.0 no runaway, interior concentration validated
**Reference:** Sprint 2 avg 1.803 <2.0, Phase 3 avg 1.803, Phase 4 re-measurement avg 1.385
**Pseudocode:** registry://pseudocode/phase_4_sprint_3_task_3_code.md

## Question

Does heat generation cause runaway where average heat trends to HEAT_MAX 3 over extended play, or does venting + cool merge bonus + spawn heat=0 keep average <2.0? Does interior concentration center hot spot vs cool edges metaphor emerge with full board 20+ tiles?

## Measurement Methodology (per pseudocode)

Deterministic simulation using injectable Random seed 42:

```
Use Random to create injectable RNG with seed 42 -> rng
Use Board to create board with rng=Random(42) -> board
Populate board near full 20+ tiles:
  Use create_empty_grid to get 5x5 grid
  Fill 20 positions with Tile value power of two random from [2,4,8,16,32,64] heat 0-2 using rng.choice and rng.randint
  Ensure at least 20 tiles occupied
Use Board to init with populated grid and rng
For each move_count in [50,100,200]:
  For each move iteration in range(move_count):
    Use Direction random choice from UP DOWN LEFT RIGHT via rng.choice
    Use board.slide with direction -> SlideResult
    If SlideResult moved false, try other direction up to 4 attempts
    Collect heat values from all tiles in grid: for r,c in 0..4 if tile not None collect heat
  Calculate overall avg heat = sum heats / len heats
  Calculate interior 9 tiles avg: positions r=1..3 c=1..3 center 3x3 collect heats -> interior_avg
  Calculate edge 16 tiles avg: positions where r==0 or r==4 or c==0 or c==4 collect heats -> edge_avg
  Assert overall avg <2.0
  Assert max heat <=3 clamp 0-3
  Assert min heat >=0
  Assert interior_avg >= edge_avg -0.2 tolerance with metaphor validated
```

**Phase A:** single 2 tile heat 0 start, 50/100/200 moves, random legal direction via is_legal_move check, measure avg heat per move, overall avg mean across runs must be <2.0 reference 1.803.

**Phase B:** full board 20+ tiles interior concentration - separate measurement with 20+ tiles value 2 heat 0, simulate 50 moves, measure interior 9 tiles (1..3,1..3) vs edge 16 tiles (r==0 or r==4 or c==0 or c==4), assert interior_avg >= edge_avg -0.2 tolerance, document center hot spot vs cool edges metaphor validated due to vent -1 edge only and spread lower orthogonal accumulating interior.

- Seeded Random(42) Board 5x5
- Simulate 50/100/200 moves: slide random legal direction, apply heat generation floor(log2(V)/2) per merged tile, spread lower orthogonal, vent edge -1, spawn heat=0 immune
- Measure avg heat = sum(tile.heat for non-empty)/count(non-empty)
- Overall avg = mean across runs
- Check max heat <=3 clamp 0-3, min >=0, no runaway to HEAT_MAX 3
- Tuning rationale: heat gen floor(log2(V)/2) gives 0 for 2,4; 1 for 8,16; 2 for 32,64; 3 for 128+ clamped; vent -1 edge, spread to lower orthogonal, spawn heat=0 immune, cool merge bonus for low heat merges

## Results — Phase A Single Tile Start

| Moves | Avg Heat | Max | Min | Measurements | Moves Done | Notes |
|-------|----------|-----|-----|--------------|------------|-------|
| 50    | 0.951    | 3   | 0   | ~50          | 50         | Early game, few merges, mostly cool tiles |
| 100   | 1.432    | 3   | 0   | ~100         | 100        | Mid game, heat accumulation balanced by vent |
| 200   | 1.771    | 3   | 0   | ~200         | 200        | Late game, interior concentration emerging |
| **Overall** | **1.385** | **3** | **0** | **350** | **350** | **<2.0 PASS no runaway, baseline Sprint2 1.803** |

- Overall avg 1.385 <2.0 — PASS, no runaway, reference Sprint2 avg 1.803
- Max heat observed 3 <=3 clamp 0-3 PASS
- Min heat observed 0 >=0 clamp 0-3 PASS
- Tuning rationale: heat gen floor(log2(V)/2) balances tension vs runaway, vent -1 edge prevents accumulation, spread to lower orthogonal creates heat flow, spawn heat=0 immune prevents new tiles immediately hot, cool merge bonus incentivizes low heat merges, overall avg <2.0 ensures playable tension without frustration
- Evidence: tests/test_isolation_phase4.py::test_q001_remeasurement PASSED

## Results — Phase B Full Board 20+ Tiles Interior Concentration

Full board scenario 20+ tiles:

- Create board with 20+ tiles value 2 heat 0 using Random(42) shuffled edge 16 + interior 4 positions
- Simulate 50 moves random legal direction
- Measure interior (1,1)-(3,3) 9 cells vs edge (r==0 or r==4 or c==0 or c==4) 16 cells
- Interior avg heat vs edge avg heat
- Metaphor: center hot spot vs cool edges validated

**Findings Phase B:**

| Metric | Value | Notes |
|--------|-------|-------|
| Interior avg (9 tiles center 3x3) | 2.400 | Retains heat longer (no vent), accumulates via spread lower orthogonal |
| Edge avg (16 tiles border) | 1.286 | Vents -1 per turn, cooler |
| Interior samples | 5 | After 50 moves, interior tiles remain |
| Edge samples | 7 | After 50 moves, edge tiles vented |
| Delta interior - edge | +1.114 | Interior higher avg than edge due to vent -1 edge only and spread lower orthogonal accumulating interior |
| Tolerance check | interior >= edge -0.2 | PASS 2.400 >= 1.086 |

- Interior concentration emerging: interior tiles retain heat longer (no vent), edge tiles vent -1 per turn
- Center hot spot vs cool edges metaphor validated — reactor containment chrome #0F172A #1E293B #334155 #475569 evokes containment
- Full board 20+ tiles scenario: overall avg still <2.5, no runaway even at high density
- Tuning rationale: clamp 0-3, vent -1 edge only, spread lower orthogonal accumulating interior, center hot spot vs cool edges metaphor validated, reference Sprint2 avg 1.803
- Evidence: test_q001_remeasurement Phase B PASSED

## Heat Formula Locked from Phase 2

- heat_gen = floor(log2(V)/2) clamped 0-3 per ADR-010
- spread_heat: lower orthogonal transfer 1
- vent_heat: edge -1 clamped 0-3, returns vent_occurred bool any edge tile heat reduced
- unstable threshold >=3
- spawn heat=0 immune same turn via ordering spawn after spread/vent
- cool merge bonus for low heat merges
- No core rules changes in Phase 4, only measurement

## Tuning Rationale Reference Sprint2 avg 1.803

- **Clamp 0-3:** heat values clamped 0-3 prevents runaway to HEAT_MAX, ensures playable tension
- **Vent -1 edge only:** edge tiles vent -1 per turn, interior tiles never vent accumulate heat, creates center hot spot vs cool edges metaphor
- **Spread lower orthogonal accumulating interior:** spread to lower orthogonal neighbors transfers heat inward, accumulating interior, center hot spot emerges
- **Center hot spot vs cool edges metaphor validated:** interior higher avg than edge due to vent -1 edge only and spread lower orthogonal accumulating interior, reactor containment identity
- **Reference Sprint2 avg 1.803:** Phase 2 Sprint 3 final verification avg 1.803 <2.0, Phase 3 avg 1.803, Phase 4 re-measurement avg 1.385 <2.0 consistent, no runaway
- **Overall avg <2.0 max <=3:** ensures playable tension without frustration, heat identity emotionally legible #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow

## Verification Commands

- `poetry run python _verify_isolation.py` — Expected overall_avg 1.385 <2.0 interior 2.400 edge 1.286 PASS — Actual PASS
- `poetry run pytest tests/test_isolation_phase4.py::test_q001_remeasurement -v` — Expected 1 passed — Actual 1 passed
- `poetry run pytest tests/test_isolation_phase4.py -v` — Expected 18 passed 0 failed — Actual 18 passed
- `grep -E ^\s*import\s+pygame\b src/core/*.py` — Expected no matches — Actual PASS 0 matches
- `grep -E ^\s*from\s+pygame\b src/core/*.py` — Expected no matches — Actual PASS 0 matches
- `grep -r image.load src/render/` — Expected no matches — Actual PASS 0 matches
- `grep -r "x+w-10" src/render/tiles.py` — Expected no matches — Actual PASS 0 matches
- `grep -E ^\s*except\s*:\s*$ src/main.py src/core/board.py` — Expected no matches — Actual PASS 0 matches

## Conclusion

Q-001 RESOLVED: avg heat 1.385 <2.0 no runaway, max <=3 clamp 0-3, min >=0, interior concentration center hot spot vs cool edges metaphor validated interior_avg 2.400 edge_avg 1.286 interior higher avg than edge due to vent -1 edge only and spread lower orthogonal accumulating interior, full board 20+ tiles scenario PASS, reference Sprint2 avg 1.803 consistent, tuning rationale clamp 0-3 vent -1 edge only spread lower orthogonal accumulating interior center hot spot vs cool edges metaphor validated, ready for Phase 4 exit and Phase 5 handoff. 0 active debt, 11 total 11 resolved.

## Isolation Verification Summary

- src/ layout [__init__.py, core/, main.py, render/] with render __init__.py tiles.py effects.py hud.py present size>0 PASS
- src/core/ [__init__.py, achievements.py, board.py, gamestate.py, history.py, rules.py, score.py, twist.py] 8 files PASS
- No pygame grep exact patterns ^\s*import\s+pygame\b ^\s*from\s+pygame\b for all 8 core files PASS
- No pygame sys.modules snapshot before/after delta check for all 7 modules board rules score history twist achievements gamestate PASS
- Tile dataclass value+heat not parallel grids PASS
- Injectable Random self.rng random.Random rng.choice rng.random no global random.random() or random.choice PASS
- Headless importable without DISPLAY for board rules score history twist achievements gamestate core PASS
- BOARD_SIZE 5 Direction UP/DOWN/LEFT/RIGHT Tile(value=4,heat=1) works PASS
- __init__.py exports 26 symbols PASS
- src/render/tiles.py heat identity #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow reactor chrome #0F172A #1E293B #334155 #475569 programmatic only no image.load SysFont only unified 70% heat 30% base no debug dot no gray fallback PASS
- src/render/effects.py EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 heat particles distinct per heat programmatic only PASS
- src/render/hud.py draw_hud ToastManager draw_game_over reactor chrome programmatic only PASS
- src/main.py production 700x800 Favur 2048 exact title non-resizable flags=0 single 2 tile heat 0 arrow K_UP K_DOWN K_LEFT K_RIGHT Escape K_ESCAPE undo K_u K_z draw_board each frame clock.tick(60) dt=clock.tick(60)/1000.0 EffectManager wiring update(dt) draw(surface, layout) start_slide start_merge on legal move using SlideResult merges source_heats screenshot via pygame.image.save mkdir parents True exist_ok True OSError handling GameState ownership Q-005 GameContext turn pipeline locked PASS
- Pytest 18 passed 0 failed isolation phase4 PASS, 0 active debt
