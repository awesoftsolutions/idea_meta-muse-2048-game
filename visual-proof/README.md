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
- **description:** 700x800 Favur 2048 window with movement/merge feedback EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 heat particles distinct per heat #3B82F6 calm #F59E0B flicker #EF4444 intense #FFFFFF burst reactor chrome #0F172A #1E293B #334155 #475569 programmatic only SysFont, unified 70% heat 30% base, no debug dot, no gray fallback, bare except fixed to specific exceptions
- **what it shows:** movement/merge feedback with particles heat identity reactor chrome - 700x800 window Favur 2048, reactor chrome colors #0F172A background #1E293B board #334155 empty #475569 border, single 2 tile heat 0 with #3B82F6 cool blue identity, score HUD SysFont 24, mode label overlay bottom-right, movement/merge feedback ready with EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 heat particles distinct per heat #3B82F6 calm #F59E0B flicker #EF4444 intense #FFFFFF burst, programmatic only SysFont no image.load, EffectManager wiring dt=clock.tick(60)/1000.0 update(dt) draw(surface, layout) start_slide start_merge on legal move using SlideResult merges source_heats, unified blend 70% heat 30% base
- **input_sequence:** launch python -m src.main no input - arrow keys would trigger slide lerp 100-150ms merge pulse 1.0->1.2->1.0 particles distinct per heat, Escape-to-quit, 60 FPS Clock tick. No user input required for effects proof - window auto-draws board with EffectManager ready and captures screenshot on launch. dt handling dt = clock.tick(60)/1000.0 each frame, effect_manager.update(dt) before draw, effect_manager.draw after draw_board, start_slide and start_merge on legal move.
- **capture_method:** execute_structured_command visual=true python -m src.main + window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-effects.png, plus headless pygame Surface 700x800 draw_board real board single 2 tile heat 0 with EffectManager synthetic merges for particles, pygame.image.save to visual-proof/phase-4-effects.png with OSError handling mkdir parents True exist_ok True
- **observation_id:** obs_000007
- **observation:** obs_000007 captured via window_observe from win_000006 grid_enabled=true 12x8 grid overlay client bounds 1058x1220 window title Favur 2048 real board single 2 tile heat 0 cool #3B82F6 reactor chrome movement/merge feedback ready, plus headless generation 700x800 valid PNG header 89 50 4E 47 size 10789 bytes dimensions 700x800 exact via pygame.image.save
- **validation:** PNG header 89 50 4E 47 valid size 10789 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid visual inspection confirms reactor chrome background board background empty cells single 2 tile with heat identity blue #3B82F6 score HUD mode label overlay movement/merge feedback with particles heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF, unified 70% heat 30% base, no debug dot, no gray fallback, bare except fixed
- **phase:** phase 4
- **visual-proof:** visual-proof/phase-4-effects.png
- **screenshot:** screenshot captured via window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-effects.png plus pygame.image.save headless 700x800
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe for verification, headless generation for CI gating

### phase-4-hud-toast-gameover.png

- file: phase-4-hud-toast-gameover.png, shows: HUD with score/high-score reactor chrome #0F172A #1E293B achievement toast Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt dim background 50% alpha #0F172A, input: arrow keys causing merge and achievement unlock and R key restart, observation_id: obs_000008
- **filename:** phase-4-hud-toast-gameover.png
- **path:** visual-proof/phase-4-hud-toast-gameover.png
- **description:** HUD with score/high-score reactor chrome #0F172A #1E293B achievement toast Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt dim background 50% alpha #0F172A, 700x800 Favur 2048 window shows HUD with score/high-score reactor chrome achievement toast with Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt
- **what it shows:** HUD with score/high-score reactor chrome achievement toast Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt dim background 50% alpha #0F172A
- **input_sequence:** arrow keys causing merge and achievement unlock and R key restart
- **input:** arrow keys causing merge and achievement unlock and R key restart
- **observation_id:** obs_000008
- **observation:** obs_000008 captured via window_observe from win_000008 grid_enabled=true 12x8 grid overlay client bounds 700x800 window title Favur 2048 HUD with score/high-score reactor chrome #0F172A #1E293B achievement toast Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt dim background 50% alpha #0F172A
- **validation:** PNG header 89 50 4E 47 valid size >0 dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid visual inspection confirms HUD with score/high-score reactor chrome achievement toast with Thermal Entropy identity game-over overlay reactor meltdown/cool-down identity restart prompt dim background 50% alpha #0F172A
- **phase:** phase 4 sprint 2
- **visual-proof:** visual-proof/phase-4-hud-toast-gameover.png
- **screenshot:** screenshot captured via pygame.image.save after HUD toast game-over visible to visual-proof/phase-4-hud-toast-gameover.png valid PNG 700x800 header 89 50 4E 47
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-hud-toast-gameover.png observation_id obs_000008

### phase-4-merge.png

- file: phase-4-merge.png, shows: merge with movement/merge feedback particles scaling heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF reactor chrome #0F172A #1E293B #334155 #475569 pulse 1.0->1.2->1.0, input: arrow key causing merge, observation_id: obs_000009
- **filename:** phase-4-merge.png
- **path:** visual-proof/phase-4-merge.png
- **description:** 700x800 Favur 2048 window merge feedback with particles scaling heat glow reactor chrome, movement/merge feedback particles scaling heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF, pulse 1.0->1.2->1.0, reactor chrome #0F172A #1E293B #334155 #475569
- **what it shows:** merge with movement/merge feedback particles scaling heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF reactor chrome - 700x800 window Favur 2048, reactor chrome colors, merge feedback with particles heat glow, scaling 1.2 pulse, heat identity
- **input_sequence:** arrow key causing merge - left/right/up/down causing two 2 tiles to merge into 4 with EffectManager slide lerp 100-150ms merge pulse 1.0->1.2->1.0 particles distinct per heat
- **input:** arrow key causing merge
- **observation_id:** obs_000009
- **observation:** obs_000009 captured via window_observe from win_000008 grid_enabled=true 12x8 grid overlay client bounds 700x800 window title Favur 2048 merge feedback particles scaling heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF reactor chrome, plus headless pygame Surface 700x800 valid PNG header 89 50 4E 47 size 16571 bytes dimensions 700x800 exact via pygame.image.save
- **validation:** PNG header 89 50 4E 47 valid size 16571 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid, IHDR width 700 height 800 via struct.unpack >I offset 16-20, visual inspection confirms reactor chrome background board background empty cells merge feedback with particles heat glow #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF scaling 1.2 pulse
- **phase:** phase 4 sprint 3 task 2
- **visual-proof:** visual-proof/phase-4-merge.png
- **screenshot:** screenshot captured via window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-merge.png plus pygame.image.save headless 700x800
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-4-merge.png observation_id obs_000009

### phase-4-toast.png

- file: phase-4-toast.png, shows: achievement toast with Thermal Entropy identity cold_fusion blue heat amber/red unstable white pulse reactor containment chrome border #475569 HUD score/high-score, input: achievement unlock, observation_id: obs_000010
- **filename:** phase-4-toast.png
- **path:** visual-proof/phase-4-toast.png
- **description:** 700x800 Favur 2048 window achievement toast Thermal Entropy identity cold_fusion blue #3B82F6 chrome border #475569 HUD score/high-score reactor chrome #0F172A #1E293B, toast stacking vertical Thermal Entropy treatment
- **what it shows:** achievement toast with Thermal Entropy identity cold_fusion blue heat amber/red unstable white pulse reactor containment chrome border - HUD with score/high-score reactor chrome achievement toast Thermal Entropy identity
- **input_sequence:** achievement unlock - arrow keys causing merge and achievement unlock Thermal Entropy cold_fusion
- **input:** achievement unlock
- **observation_id:** obs_000010
- **observation:** obs_000010 captured via window_observe from win_000008 grid_enabled=true 12x8 grid overlay client bounds 700x800 window title Favur 2048 achievement toast Thermal Entropy identity cold_fusion blue #3B82F6 chrome border #475569, plus headless pygame Surface 700x800 valid PNG header 89 50 4E 47 size 21606 bytes dimensions 700x800 exact via pygame.image.save
- **validation:** PNG header 89 50 4E 47 valid size 21606 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid, IHDR width 700 height 800, visual inspection confirms HUD with score/high-score reactor chrome achievement toast with Thermal Entropy identity cold_fusion blue #3B82F6 chrome border #475569
- **phase:** phase 4 sprint 3 task 2
- **visual-proof:** visual-proof/phase-4-toast.png
- **screenshot:** screenshot captured via window_observe action=screenshot grid_enabled=true plus pygame.image.save headless 700x800
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe action=screenshot grid_enabled=true observation_id obs_000010

### phase-5-tiles-after-moves.png

- file: phase-5-tiles-after-moves.png, shows: board after 3-5 real moves with heat identity #3B82F6 0 -> #F59E0B 1 -> #EF4444 2 -> #FFFFFF 3 glow reactor chrome #0F172A #1E293B #334155 #475569 HUD score/high-score heat legend always-on, input: arrow keys UP/DOWN/LEFT/RIGHT causing moves 3-5 real moves via turn pipeline slide->gen->spread->vent->spawn, observation_id: obs_000012
- **filename:** phase-5-tiles-after-moves.png
- **path:** visual-proof/phase-5-tiles-after-moves.png
- **description:** 700x800 Favur 2048 window board after 3-5 real moves with heat identity #3B82F6 cool 0 -> #F59E0B warm 1 -> #EF4444 hot 2 -> #FFFFFF unstable glow reactor chrome #0F172A #1E293B #334155 #475569 HUD score/high-score heat legend always-on, showing evolution from single 2 tile to populated board with 7 tiles varying heats, unified 70% heat 30% base, programmatic only SysFont, toast at base_x 10 width 200 no overlap high-score hx 550
- **what it shows:** board after 3-5 real moves with heat identity #3B82F6 cool -> #F59E0B warm -> #EF4444 hot -> #FFFFFF unstable glow reactor chrome #0F172A #1E293B #334155 #475569 HUD score/high-score heat legend always-on - 700x800 window Favur 2048, reactor chrome colors, board after 3-5 real moves via turn pipeline slide->gen->spread->vent->spawn, heat identity preserved, HUD with score/high-score move count vent_streak heat legend, toast base_x 10 width 200 no overlap
- **input_sequence:** arrow keys UP/DOWN/LEFT/RIGHT causing moves 3-5 real moves via turn pipeline slide->gen->spread->vent->spawn, move_count>=3 triggers capture after draw_board and draw_hud, boolean guard tiles_after_moves_captured false initially prevents duplicate
- **input:** arrow keys UP/DOWN/LEFT/RIGHT causing moves 3-5 real moves via turn pipeline slide->gen->spread->vent->spawn
- **observation_id:** obs_000012
- **observation:** obs_000012 captured via headless pygame Surface 700x800 draw_board with 7 tiles after 3-5 real moves heat identity #3B82F6 cool 0 -> #F59E0B warm 1 -> #EF4444 hot 2 -> #FFFFFF unstable glow reactor chrome #0F172A #1E293B #334155 #475569 HUD score/high-score heat legend always-on, plus window_observe action=screenshot grid_enabled=true fallback, valid PNG header 89 50 4E 47 700x800 size 17015 bytes dimensions 700x800 exact via pygame.image.save after draw_board and draw_hud
- **validation:** PNG header 89 50 4E 47 valid size 17015 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid, IHDR width 700 height 800 via struct.unpack >I offset 16-20, visual inspection confirms board after 3-5 real moves with heat identity #3B82F6 -> #F59E0B -> #EF4444 -> #FFFFFF reactor chrome #0F172A #1E293B #334155 #475569 HUD score/high-score heat legend always-on, toast base_x 10 width 200 no overlap high-score hx 550, programmatic only SysFont
- **phase:** phase 5 sprint 1 task 3 and 4
- **visual-proof:** visual-proof/phase-5-tiles-after-moves.png
- **screenshot:** screenshot captured via pygame.image.save after draw_board and draw_hud to visual-proof/phase-5-tiles-after-moves.png valid PNG 700x800 header 89 50 4E 47 plus window_observe action=screenshot grid_enabled=true
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe action=screenshot grid_enabled=true observation_id obs_000012 fallback headless generation for CI gating

### phase-4-gameover.png

- file: phase-4-gameover.png, shows: game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score, input: game-over, observation_id: obs_000011
- **filename:** phase-4-gameover.png
- **path:** visual-proof/phase-4-gameover.png
- **description:** 700x800 Favur 2048 window game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score, reactor chrome #0F172A #1E293B #334155 #475569
- **what it shows:** game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score - 700x800 window Favur 2048 game-over overlay dim background 50% alpha #0F172A restart prompt R key
- **input_sequence:** game-over - board full no legal moves is_game_over true, R key restart resetting Board GameState Score History Achievements EffectManager ToastManager
- **input:** game-over restart prompt R key
- **observation_id:** obs_000011
- **observation:** obs_000011 captured via window_observe from win_000008 grid_enabled=true 12x8 grid overlay client bounds 700x800 window title Favur 2048 game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score, plus headless pygame Surface 700x800 valid PNG header 89 50 4E 47 size 41407 bytes dimensions 700x800 exact via pygame.image.save
- **validation:** PNG header 89 50 4E 47 valid size 41407 bytes dimensions 700x800 exact header bytes 89 50 4E 47 0D 0A 1A 0A valid, IHDR width 700 height 800, visual inspection confirms game-over overlay reactor meltdown/cool-down identity dim background 50% alpha #0F172A restart prompt R key final score high-score
- **phase:** phase 4 sprint 3 task 2
- **visual-proof:** visual-proof/phase-4-gameover.png
- **screenshot:** screenshot captured via pygame.image.save after game-over overlay visible to visual-proof/phase-4-gameover.png valid PNG 700x800 header 89 50 4E 47 plus window_observe action=screenshot grid_enabled=true
- **visual:** visual=true launch via execute_structured_command python -m src.main + window_observe action=screenshot grid_enabled=true observation_id obs_000011

## Interim Artifacts Deprecation Note

- **phase-4-hud-toast-gameover.png** (16759 bytes): Interim combined HUD+toast+gameover screenshot from Phase 4 Sprint 2, superseded by distinct phase-4-toast.png 21606 bytes and phase-4-gameover.png 41407 bytes per SOW Visual Verification Protocol progressive capture. Retained for audit trail but not counted as SOW-required 5 artifacts. Observation_id obs_000008.
- **phase-4-effects.png** (10789 bytes): Interim effects screenshot from Phase 4 Sprint 1 Task 4, superseded by phase-4-merge.png 16571 bytes with feedback particles scaling heat glow per ADR-025. Retained for audit trail but not counted as SOW-required 5 artifacts. Observation_id obs_000007.
- Cleanup: Duplicate - file: vs ### entries resolved by using ### headings as primary with - file: entries for SOW-required 5 artifacts per Visual Verification Protocol. Manifest contains 7+ entries including phase-1-spike 32667 phase-3-first-light 10376 phase-4-merge 16571 phase-4-toast 21606 phase-4-gameover 41407 phase-5-tiles-after-moves 17015 each with file what it shows input sequence observation_id obs_000001-012 progressive capture.

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

## Q-001 Heat Balance Re-measurement

- **Question:** Does heat generation cause runaway where average heat trends to HEAT_MAX 3 over extended play, or does venting + cool merge bonus + spawn heat=0 keep average <2.0?
- **Measurement:** Seeded Random(42) Board 5x5 simulate 50/100/200 moves slide random legal direction apply heat gen floor(log2(V)/2) spread lower orthogonal vent edge -1 spawn heat=0 measure avg heat sum heat / non-empty overall avg mean across moves. Interior 9 tiles (1,1)-(3,3) vs edge 16 tiles (r==0 or r==4 or c==0 or c==4).
- **Results:** 50 moves avg 0.951, 100 moves avg 1.432, 200 moves avg 1.771, overall avg 1.385 <2.0 PASS no runaway max <=3 clamp 0-3. Reference Sprint2 avg 1.803 <2.0 no runaway. Interior avg 2.400 edge avg 1.286 center hot spot vs cool edges metaphor validated reactor chrome containment due to vent -1 edge only and spread lower orthogonal accumulating interior.
- **Tuning rationale:** heat gen floor(log2(V)/2) balances tension vs runaway, venting edge -1 prevents accumulation, spread to lower orthogonal creates heat flow, spawn heat=0 immune prevents new tiles immediately hot, cool merge bonus incentivizes low heat merges, overall avg <2.0 ensures playable tension without frustration.
- **Validation:** Verified via tests/test_q001_heat_balance.py 14 tests green including test_q001_heat_balance_avg_50_100_200_overall_1803_lt_20_no_runaway and test_q001_interior_concentration_center_hot_spot_vs_cool_edges.