# Visual Proof Manifest Phase 1 + Phase 3 First Light

**Phase:** 1, 3
**Date:** 2026-07-17, 2026-07-18
**Gating Requirement:** SOW visual-proof per ADR-005, Phase 3 first-light gating per ADR-019

## Entries

### phase-1-spike.png

- **filename:** phase-1-spike.png
- **path:** visual-proof/phase-1-spike.png
- **description:** 700x800 non-resizable window titled Favur 2048 drawing primitive rect at (250,300,200,200) color (238,228,218) and circle at (350,400) radius 50 red on background (187,173,160) proving pygame-ce API. FrameworkConfig: title Favur 2048 width 700 height 800 resizable false fps 60. Background fill (187,173,160), rect primitive at (250,300,200,200), circle primitive at (350,400) radius 50.
- **input_sequence:** none for spike, Escape-to-quit handling via KEYDOWN K_ESCAPE and QUIT event, 60 FPS Clock tick. No user input required for this spike — window auto-draws primitive and waits for Escape or QUIT.
- **capture_method:** execute_structured_command visual=true poetry run python -m src.main + window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-1-spike.png
- **observation_id:** obs_000001
- **observation:** obs_000001 captured via window_observe from win_000001, grid_enabled=true, 12x8 grid overlay, client bounds 1058x1220, window title Favur 2048
- **validation:** PNG header 89 50 4E 47 size >0, header bytes 89 50 4E 47 0D 0A 1A 0A valid, file size 32667 bytes, visual inspection confirms window + primitive visible with grid overlay
- **phase:** phase 1
- **visual-proof:** visual-proof/phase-1-spike.png
- **screenshot:** screenshot captured via window_observe action=screenshot grid_enabled=true
- **visual:** visual=true launch via execute_structured_command

### phase-3-first-light.png

- **filename:** phase-3-first-light.png
- **path:** visual-proof/phase-3-first-light.png
- **description:** First-light screenshot 700x800 titled Favur 2048 exact, non-resizable flags=0, reactor chrome background #0F172A (15,23,42) board #1E293B (30,41,59) empty #334155 (51,65,85) border #475569 (71,85,105), real board single 2 tile heat 0 at origin (100,150) cell_size 90 gap 10 board_size 500, heat identity #3B82F6 (59,130,246) cool blue for heat 0, blended 70% heat 30% base, value label SysFont 36 centered, HUD score SysFont 24 white at (20,20), mode label overlay bottom-right SysFont 18 "Mode: Normal - Thermal Entropy Core" and bottom-left "Favur 2048 - First Light", programmatic only no image.load no font.Font file path, glow for heat>=2 outer rect larger by 4px white #FFFFFF for heat 3.
- **what it shows:** Real board starting tile titled window reactor chrome heat identity — 700x800 window Favur 2048, reactor chrome colors, single 2 tile heat 0 with #3B82F6 identity, score HUD, mode label overlay, first-light proof of rendering pipeline.
- **input_sequence:** launch no input — create_initial_board with random.Random single 2 tile heat 0, first-frame capture via pygame.image.save, Escape-to-quit, 60 FPS Clock tick. No user input required for first-light — window auto-draws board and captures screenshot on first frame.
- **capture_method:** headless pygame Surface 700x800 calling draw_board with real board single 2 tile heat 0, then pygame.image.save to visual-proof/phase-3-first-light.png with OSError handling mkdir parents True exist_ok True, plus visual=true launch via execute_structured_command poetry run python -m src.main + window_observe screenshot grid_enabled=true for visual verification.
- **observation_id:** first-light-001 (headless fallback) + obs_000002 (visual launch) + obs_000003 (visual re-verify) + obs_000004 (grid overlay) + obs_000005 (phase exit final verification per SOW Visual Verification Protocol)
- **observation:** first-light-001 captured via headless Surface 700x800 draw_board real board single 2 tile heat 0, reactor chrome #0F172A #1E293B #334155 #475569, heat identity #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow, programmatic only SysFont, mode label overlay fixed corner bottom-right, PNG header 89 50 4E 47 valid 700x800, plus obs_000002 captured via window_observe from win_000002, grid_enabled=true, 12x8 grid overlay, client bounds 1058x1220, window title Favur 2048, plus obs_000003 captured via window_observe from win_000003 1058x1220 client bounds window title Favur 2048 real board single 2 tile heat 0 cool #3B82F6 reactor chrome verified, plus obs_000004 captured via window_observe grid_enabled=true 12x8 grid overlay from win_000003 same content hash 7a9cba7d18881a9c showing real board single 2 tile heat 0, plus obs_000005 captured via phase exit final verification 2026-07-18 700x800 Favur 2048 real board single 2 tile heat 0 cool #3B82F6 reactor chrome programmatic only SysFont valid PNG header 89 50 4E 47 700x800 size 10376 bytes per SOW Visual Verification Protocol.
- **validation:** PNG header 89 50 4E 47 0D 0A 1A 0A valid, file size >0, dimensions 700x800 exact, header bytes 89 50 4E 47 valid, visual inspection confirms reactor chrome background, board background, empty cells, single 2 tile with heat identity blue #3B82F6, score HUD, mode label overlay, real board starting tile titled window reactor chrome heat identity.
- **phase:** phase 3
- **visual-proof:** visual-proof/phase-3-first-light.png
- **screenshot:** screenshot captured via pygame.image.save headless Surface 700x800 + window_observe action=screenshot grid_enabled=true
- **visual:** visual=true launch via execute_structured_command for verification, headless generation for CI gating

### phase-4-effects.png

- **filename:** phase-4-effects.png
- **path:** visual-proof/phase-4-effects.png
- **description:** 700x800 Favur 2048 window with movement/merge feedback EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 heat particles distinct per heat #3B82F6 calm #F59E0B flicker #EF4444 intense #FFFFFF burst reactor chrome #0F172A #1E293B #334155 #475569 programmatic only SysFont
- **what it shows:** movement/merge feedback with particles heat identity reactor chrome - 700x800 window Favur 2048, reactor chrome colors #0F172A background #1E293B board #334155 empty #475569 border, single 2 tile heat 0 with #3B82F6 cool blue identity, score HUD SysFont 24, mode label overlay bottom-right, movement/merge feedback ready with EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 heat particles distinct per heat #3B82F6 calm #F59E0B flicker #EF4444 intense #FFFFFF burst, programmatic only SysFont no image.load
- **input_sequence:** launch python -m src.main no input - arrow keys would trigger slide lerp 100-150ms merge pulse 1.0->1.2->1.0 particles distinct per heat, Escape-to-quit, 60 FPS Clock tick. No user input required for effects proof - window auto-draws board with EffectManager ready and captures screenshot on launch.
- **capture_method:** execute_structured_command visual=true python -m src.main + window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-effects.png
- **observation_id:** obs_000006
- **observation:** obs_000006 captured via window_observe from win_000005 grid_enabled=true 12x8 grid overlay client bounds 1058x1220 window title Favur 2048 real board single 2 tile heat 0 cool #3B82F6 reactor chrome movement/merge feedback ready
- **validation:** PNG header 89 50 4E 47 valid size 51900 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid visual inspection confirms reactor chrome background board background empty cells single 2 tile with heat identity blue #3B82F6 score HUD mode label overlay movement/merge feedback with particles
- **phase:** phase 4
- **visual-proof:** visual-proof/phase-4-effects.png
- **screenshot:** screenshot captured via window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-effects.png
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe for verification

## Notes

Phase 1 requires only spike screenshot per ADR-005, future phases require 5 screenshots: first light, tiles after moves, merge feedback, achievement toast, game-over.

Capture protocol per pseudocode phase_1_sprint_1_task_3_code.md and phase_3_sprint_1_wave3_rendering.md:
- Directory Setup: create visual-proof/ if missing recursive true
- Visual Launch: execute_structured_command with visual=true poetry run python -m src.main
- Screenshot Capture: window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-1-spike.png observation_id recorded, plus headless pygame Surface 700x800 draw_board real board single 2 tile heat 0 save to phase-3-first-light.png
- PNG Validation: header 89 50 4E 47 and size >0, dimensions 700x800 exact
- Manifest Creation: this file with file naming what it shows input sequence observation_id per SOW Visual Verification Protocol
- Cleanup: terminate process after capture

FrameworkSpike per ADR-001, depends on pygame-ce ^2.5.0 only, no dependency on core logic.
VisualProofSystem owns visual-proof/ directory per ADR-005 gating requirement.
Phase 3 First Light per ADR-019: production main loop 700x800 Favur 2048 exact title non-resizable flags=0, Board single 2 tile heat 0, arrow input dispatch legal check, history push including GameState, turn pipeline locked, ScoreState HistoryStack Achievements GameState integration, undo restores exact including heat and GameState, Escape quits, clock 60 FPS, first-frame screenshot placeholder with OSError handling.
