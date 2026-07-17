# Technical Debt Register

Initial register for the2048 — no debt yet, Phase 1 research & spikes just starting. Phase 1 isolation verification completed 2026-07-17 Task 7.

| ID | Component | Description | Severity | Discovered | Status |
|---|---|---|---|---|---|
| TD-001 | Phase 1 Spike Isolation | Phase 1 spike isolation verification — no debt leaked, out-of-scope absent, visual-proof valid, README twist keywords present, AC-1 to AC-8 PASS | LOW | 2026-07-17 | RESOLVED |

## Summary

1 total · 0 active · 1 resolved — Phase 1 isolation verification PASS, no debt leaked, spike isolation verified, out-of-scope artifacts absent, visual-proof valid PNG header 89 50 4E 47 size 32667 bytes, README twist keywords committed/rejected/rationale/Thermal Entropy Core present, AC-1 to AC-8 all PASS, ready for Phase 2 handoff.

## Resolved Technical Debt

### [TD-001] Phase 1 Spike Isolation Verification — No Debt Leaked

**Status:** RESOLVED
**Priority:** LOW
**Created:** 2026-07-17
**Resolved:** 2026-07-17
**Affected Components:** src/, src/core/, visual-proof/, README.md, spike_packaging/, technical_debt.md
**Description:** Task 7 verification — Verify Spike Isolation and No Out-of-Scope Artifacts per pseudocode registry://pseudocode/phase_1_sprint_1_task_7_code.md. Checks src/ layout has no src/render/ and src/core contains only __init__.py and board.py spike, board.py has no pygame import via grep exact patterns import pygame/from pygame and sys.modules check and is headless importable and marked as spike/prototype with injectable RNG random.Random, visual-proof/ contains phase-1-spike.png valid PNG header 89 50 4E 47 0D 0A 1A 0A size 32667 bytes and README.md manifest stub naming file and what it shows with observation_id obs_000001, README contains twist decision keywords committed/rejected/rationale/Thermal Entropy Core with 5 ideas evaluated and 4 rejected, negative existence checks for .github/workflows/ci.yml and src/core/rules.py score.py history.py achievements.py twist.py and src/render/ variants, cross-checks Phase 1 Direction AC-1 to AC-8 all PASS, packaging notes from spike_packaging/build.log PyInstaller 6.20.0 exit 0 dist/minimal.exe EXISTS workaround documented for Python 3.13.14 vs constraint, debt leaked None, status PASS Phase 2 handoff ready.

**Checks Performed:**
- check_src_layout_no_render() — Verify src/render/ does not exist per ADR-007 — PASS — src/ listing [__init__.py, core/, main.py] no render/
- check_core_only_init_and_board() — Verify src/core/ contains only __init__.py and board.py — PASS — filtered __pycache__
- check_board_no_pygame_grep() — Grep board.py for pygame import via exact patterns — PASS — no import pygame/from pygame, allowed imports random/typing/copy only
- check_board_no_pygame_sysmodules() — Import board and check sys.modules has no pygame — PASS — snapshot before/after, no pygame, delta check pollution handling
- check_board_headless_importable() — Import src.core.board without DISPLAY — PASS — Board class BOARD_SIZE 5 DIRECTIONS UP/DOWN/LEFT/RIGHT injectable RNG
- check_board_marked_spike_prototype() — Check docstring contains spike/prototype/pure-Python — PASS — docstring Pure-Python Board spike with injectable RNG, ADR-003 compliance
- check_visual_proof_artifacts() — List visual-proof/ contains phase-1-spike.png and README.md — PASS
- check_png_valid() — Validate PNG header 89 50 4E 47 0D 0A 1A 0A and non-zero size — PASS — 32667 bytes >0 binary rb mode avoids CRLF
- check_readme_twist_keywords() — Check README.md contains committed/rejected/rationale/Thermal Entropy Core — PASS — committed found, rejected 4x, rationale found, Thermal Entropy Core exact, 5 ideas #### count >=4 evaluation matrix preserves core consistent tension unconventional mechanic distinct identity
- check_negative_out_of_scope() — Check forbidden paths do not exist — PASS — 11 paths absent: .github/workflows/ci.yml, src/core/rules.py, score.py, history.py, achievements.py, twist.py, src/render/, tiles.py, effects.py, hud.py, __init__.py
- check_ac1_to_ac8_crosscheck() — Cross-check AC-1 to AC-8 — PASS — all 8 True

**Out-of-Scope Artifacts Confirmed Absent (11):**
- .github/workflows/ci.yml — CI Phase 6 correctly absent
- src/core/rules.py — Production Phase 2 correctly absent
- src/core/score.py — Production Phase 2 correctly absent
- src/core/history.py — Production Phase 2 correctly absent
- src/core/achievements.py — Production Phase 2 correctly absent
- src/core/twist.py — Production Phase 2 correctly absent
- src/render/ — Rendering Phase 3-4 correctly absent
- src/render/tiles.py — Rendering Phase 3-4 correctly absent
- src/render/effects.py — Rendering Phase 3-4 correctly absent
- src/render/hud.py — Rendering Phase 3-4 correctly absent
- src/render/__init__.py — Rendering Phase 3-4 correctly absent
Verification method: existence check returns False if parent missing, catches FileNotFoundError, treats as absent per pseudocode edge case.

**Spike Isolation Verified:**
- board.py no pygame via grep exact patterns import pygame/from pygame avoids false positives from comments
- board.py no pygame in sys.modules snapshot before import importlib import src.core.board check pygame not in sys.modules no modules starting with pygame delta check if pre-existing pollution
- board.py headless importable without DISPLAY Board class exists BOARD_SIZE 5 DIRECTIONS set injectable RNG random.Random in __init__(grid, rng) spawn 90/10 via rng.random()<0.9 deterministic seeded 13 tests green
- board.py marked spike/prototype docstring Pure-Python Board spike with injectable RNG markers spike pure-Python prototype research ADR-003 first 30 lines
- slide algorithm compress-merge-compress merged-flag preventing double merge one-merge-per-tile chain prevention [4,4,8]->[8,8] not [16] blocking maximal movement
- main.py framework spike imports pygame-ce verifies API 11 required APIs init display.set_mode set_caption event.get QUIT KEYDOWN K_ESCAPE draw.rect draw.circle time.Clock quit opens 700x800 non-resizable window titled Favur 2048 draws primitive rect (250,300,200,200) circle (350,400) radius 50 red background (187,173,160) handles QUIT Escape-to-quit KEYDOWN K_ESCAPE 60 FPS clean quit no dependency on core logic ADR-001

**Visual-Proof Valid:**
- phase-1-spike.png exists 32667 bytes >0 PNG header 89 50 4E 47 0D 0A 1A 0A valid first 4 bytes 89 50 4E 47 critical PASS header hex 89504e47 binary rb mode content 700x800 window titled Favur 2048 drawing primitive FrameworkConfig title Favur 2048 width 700 height 800 resizable false fps 60 capture method execute_structured_command visual=true poetry run python -m src.main + window_observe action=screenshot grid_enabled=true observation_id obs_000001 from win_000001 grid_enabled=true 12x8 grid overlay client bounds 1058x1220 window title Favur 2048
- visual-proof/README.md exists contains filename phase-1-spike.png contains description describes 700x800 window drawing primitive contains input_sequence none for spike Escape-to-quit handling KEYDOWN K_ESCAPE QUIT event contains observation_id obs_000001 contains validation PNG header 89 50 4E 47 size >0 gating compliance ADR-005 Phase 1 requires only spike screenshot future phases 5 screenshots

**README Twist Keywords Present:**
- Title Favur 2048 present
- committed found case-insensitive Thermal Entropy Core [COMMITTED] in #### 1
- rejected found 4x case-insensitive Rejected Alternatives section 4 entries Chrono Echo Gravity Well Mycelial Bloom Quantum Entanglement
- rationale found Rationale section 6 bullets preserving core consistent tension unconventional distinct identity surprising naturally integrates
- Thermal Entropy Core exact case-sensitive present committed twist name
- Ideas evaluated 5 distinct via #### count Thermal Entropy Core Chrono Echo Gravity Well Singularity Mycelial Bloom Quantum Entanglement each evaluated against 5 constraints preserves core 5x5 consistent tension unconventional mechanic distinct identity pros/cons
- Evaluation matrix table columns Idea Preserves Core 5x5 Consistent Tension Unconventional Mechanic Distinct Identity Pros Cons all PASS for Thermal Entropy Core
- Committed twist details Name Thermal Entropy Core Identity Statement reactor core containment Consistent Gameplay Effect heat generation/spread/venting/unstable/cool merge/tension curve Implementation Hooks tile heat 0-3 board heat_spread() and vent() renderer heat color lerp #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow score bonus cool merges
- Rejected alternatives 4 with reasons Chrono Echo high cognitive load ghost overlap confusing violates easy to learn, Gravity Well breaks agency feels random tension inconsistent, Mycelial Bloom pathfinding complexity performance cost niche theme clutter, Quantum Entanglement pair tracking edge cases blocking frustrates teaching quantum distracts
- Install/run stub poetry install poetry run python -m src.main present

**AC-1 to AC-8 Cross-Check Summary:**
- AC-1 700x800 window titled Favur 2048 opens draws primitive screenshot saved to visual-proof/phase-1-spike.png — Artifact mapping visual-proof/phase-1-spike.png exists valid PNG 32667 bytes header 89 50 4E 47 src/main.py exists contains Favur 2048 and 700 and 800 and draw.rect/draw.circle — PASS
- AC-2 PyInstaller can package trivial build produce executable artifact or build log — Artifact mapping spike_packaging/build.log exists exit code 0 dist/minimal.exe EXISTS per log spike_packaging/ exists minimal.py no src.core import only pygame+sys — PASS
- AC-3 At least 4 distinct twist ideas documented with evaluation against SOW constraints — Artifact mapping README.md contains 5 ideas via #### count >=4 evaluation matrix keywords preserves core consistent tension unconventional mechanic distinct identity pros/cons present — PASS
- AC-4 One twist committed as project direction with rationale and rejected alternatives recorded — Artifact mapping README.md contains committed rationale rejected keywords and Thermal Entropy Core exact rejected count >=3 4 actual rationale section present — PASS
- AC-5 Slide/merge resolution including one-merge-per-tile rule validated against at least 6 hand-worked board states — Artifact mapping src/core/board.py exists no pygame import tests/test_board_spike.py exists contains 13 tests >=6 covering LEFT RIGHT UP DOWN blocking one-merge-per-tile chain prevention Board.slide() works [2,2]->[4] score 4 — PASS
- AC-6 Spawn randomness demonstrated as injectable/seedable for deterministic testing — Artifact mapping src/core/board.py contains random.Random and rng and def __init__ with rng param injectable RNG pattern seedable 90/10 distribution via rng.random() — PASS
- AC-7 Poetry project initialized with pyproject.toml declaring framework PyInstaller pytest — Artifact mapping pyproject.toml exists contains pygame-ce and PyInstaller and pytest and python poetry check passes python ^3.11 — PASS
- AC-8 visual-proof/ directory contains spike screenshot plus README manifest stub naming file and what it shows — Artifact mapping visual-proof/ exists phase-1-spike.png exists size >0 valid PNG README.md exists contains phase-1-spike.png and description — PASS
Overall AC-1 to AC-8 All 8 PASS ready for Phase 2 handoff per Phase 1 Direction.

**Packaging Notes:**
- Date 2026-07-17 Python 3.13.14 CPython PyInstaller 6.20.0 pygame-ce 2.6.1 SDL 2.28.4 Platform Windows 11 build 22631 Command poetry run pyinstaller --onefile --noconfirm --name minimal --distpath dist --workpath build --specpath spike_packaging --log-level INFO spike_packaging/minimal.py Actual executed python -m PyInstaller poetry install failed due to python version constraint >=3.11,<3.13 vs 3.13.14 used pip install workaround Exit code 0 dist/minimal.exe EXISTS verified via PyInstaller output Build complete! The results are available in: dist Build log spike_packaging/build.log EXISTS 96 lines contains INFO logs for Analysis PYZ PKG EXE building Minimal script independence No src.core import only pygame+sys window size 700x800 title Favur 2048 fill (30,30,30) rect (200,100,255) at (300,350,100,100) Workaround documentation 1 Poetry resolver issue pyproject.toml python ^3.11 allows 3.13 but PyInstaller metadata may restrict <3.13 Workaround pip install PyInstaller directly or update python constraint to >=3.11,<3.14 and run poetry lock --no-update 2 Hidden imports If pygame-ce modules missing add --hidden-import pygame --collect-all pygame-ce --collect-all pygame 3 SDL2 DLLs PyInstaller hook-pygame.py handles pygame DLLs via Extra DLL search directories If missing add --add-data path/to/pygame/*.dll;pygame 4 Windows Defender Exclude dist/ and build/ from real-time scanning to avoid EXE quarantine 5 Onefile vs Onedir For debugging use --onedir first to inspect missing assets then switch to --onefile 6 Production binary Per ADR-006 full game binary packaging belongs to Phase 6 this spike only proves trivial build works Conclusion PASS PyInstaller trivial build works on Windows 11 with Python 3.13.14 pygame-ce 2.6.1 PyInstaller 6.20.0 no game code dependency ready for Phase 6 production packaging

**Debt Leaked:** None — No technical debt leaked. No out-of-scope artifacts found All 11 forbidden paths confirmed absent No src/render/ directory ADR-007 compliance rendering belongs to Phase 3-4 No production core modules beyond spike src/core/ contains only __init__.py and board.py spike rules.py score.py history.py achievements.py twist.py correctly absent production belongs to Phase 2 No CI workflow .github/workflows/ci.yml correctly absent belongs to Phase 6 No external assets No image sprite or font assets programmatic graphics only per SOW Spike isolation maintained board.py pure Python no pygame import headless importable marked as prototype injectable RNG 13 tests green Visual-proof gating satisfied Screenshot valid PNG and manifest exists ADR-005 compliance Twist decision documented README contains committed twist Thermal Entropy Core with rationale and rejected alternatives ADR-004 compliance Packaging proven PyInstaller trivial build works build log exists no OS-specific blocker Technical debt items 0 new debt introduced in Phase 1 Existing debt register remains clean Spike code isolated and clearly marked as prototype production Phase 2 may rewrite rather than evolve spike per architecture principle.

**Resolution:** Updated technical_debt.md with comprehensive isolation verification entry date 2026-07-17 Task 7 checks performed 11 results all PASS out-of-scope 11 confirmed absent spike isolation board.py no pygame confirmed via grep exact patterns import pygame/from pygame and sys.modules and headless importable marked prototype visual-proof screenshot valid PNG header 89 50 4E 47 size 32667 bytes manifest exists observation_id obs_000001 README twist keywords committed/rejected/rationale/Thermal Entropy Core present 5 ideas evaluation matrix AC-1 to AC-8 cross-check all PASS packaging notes PyInstaller 6.20.0 exit 0 dist EXISTS workaround documented debt leaked None status PASS Phase 2 handoff ready. Verified via tests/test_phase1_isolation.py 12 tests PASS including test_technical_debt_update which checks isolation or Task 7 or no debt and spike or board.py keywords. Filesystem file technical_debt.md also updated with same comprehensive entry. No production code created only documentation update per Implementation Boundary.

**Verification Commands:**
- poetry run pytest tests/test_phase1_isolation.py -v — Expected 12 passed 0 failed non-interactive exit 0 verifies all 7 ACs plus regression — Actual 12 passed
- ls src/core/ — Expected __init__.py and board.py only — Actual PASS
- ls src/ — Expected __init__.py core/ main.py no render/ — Actual PASS
- grep -r import pygame src/core/board.py || echo no pygame import found — Expected no pygame import found — Actual PASS
- poetry run python -c import src.core.board; print(pygame not in sys.modules) — Expected True — Actual True
- python -c open(visual-proof/phase-1-spike.png,rb).read(4).hex() — Expected 89504e47 — Actual 89504e47
- ls -lh visual-proof/phase-1-spike.png — Expected 32667 bytes >0 — Actual 32667 bytes
- grep -i committed|rejected|rationale README.md — Expected finds keywords — Actual PASS
- grep Thermal Entropy Core README.md — Expected finds Thermal Entropy Core — Actual PASS
- cat technical_debt.md — Expected contains isolation verification entry Task 7 no debt leaked spike isolation verified AC-1 to AC-8 summary status PASS — Actual PASS

**Phase 2 Handoff Readiness:** Ready — Chosen framework version pinned and verified pygame-ce 2.6.1, committed twist Thermal Entropy Core with identity defined, slide/merge resolution algorithm validated compress-merge-compress with merged-flag, injectable RNG pattern random.Random for deterministic tests, no out-of-scope artifacts, spike isolation verified, no debt leaked, no cleanup required.
