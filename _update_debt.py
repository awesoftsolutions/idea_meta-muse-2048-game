import pathlib
p=pathlib.Path("technical_debt.md")
content=p.read_text(encoding='utf-8')
# Replace summary line
content=content.replace("10 total · 0 active · 10 resolved", "11 total · 0 active · 11 resolved")
# Add TD-011 row after TD-010
old_row="| TD-010 | Bare except swallowing in board.py and draw paths | Fix bare except to specific exception handling except (ValueError, TypeError, pygame.error) with logging per E017, grep no bare except pattern except: no matches, only specific tuples | LOW | 2026-07-18 | RESOLVED |"
new_row="""| TD-010 | Bare except swallowing in board.py and draw paths | Fix bare except to specific exception handling except (ValueError, TypeError, pygame.error) with logging per E017, grep no bare except pattern except: no matches, only specific tuples | LOW | 2026-07-18 | RESOLVED |
| TD-011 | Phase 4 Sprint 3 Isolation Verification Q-001 Re-measurement | Phase 4 Sprint 3 Task 3 isolation verification Q-001 re-measurement PASS per pseudocode registry://pseudocode/phase_4_sprint_3_task_3_code.md: src layout [__init__.py, core/, main.py, render/] with render __init__.py tiles.py effects.py hud.py present programmatic only size>0 PASS, no pygame leak via sys.modules delta snapshot before/after import src.core.board rules score history twist achievements gamestate delta check no pygame PASS, grep no pygame import exact patterns ^\\s*import\\s+pygame\\b ^\\s*from\\s+pygame\\b for all 8 core files PASS, no external assets grep no image.load no font.Font file path only SysFont programmatic only PASS, tiles.py no debug heat dot x+w-10 no gray fallback (200,200,200) palette extension fixed dual renderer unified 70% heat 30% base PASS, bare except fixed grep no except: pattern only specific except (ValueError, TypeError, pygame.error) and except OSError PASS, effects.py exists exports EffectManager no external assets PASS, hud.py exists exports draw_hud ToastManager draw_game_over no external assets PASS, headless importable without DISPLAY BOARD_SIZE 5 Tile(value=4,heat=1) Direction UP DOWN LEFT RIGHT all core modules importable PASS, no global random usage injectable Random pattern self.rng rng.choice rng.random no bare random.random() or random.choice PASS, Q-001 re-measurement Random(42) seeded 50/100/200 moves overall avg 1.385 <2.0 max <=3 clamp 0-3 tuning rationale captured reference Sprint2 avg 1.803 PASS, interior 9 tiles vs edge 16 tiles heat distribution center hot spot vs cool edges metaphor validated interior_avg 2.400 edge_avg 1.286 interior higher avg than edge due to vent -1 edge only and spread lower orthogonal accumulating interior PASS, pytest 18 passed 0 failed isolation phase4 PASS, 0 active debt | LOW | 2026-07-18 | RESOLVED |"""
if old_row in content:
    content=content.replace(old_row, new_row)
    print("replaced table row")
else:
    print("old row not found")
    # try alternative
    if "| TD-010 |" in content:
        content=content.replace("| TD-010 | Bare except swallowing", new_row.splitlines()[0] + "\n" + "| TD-011 |")
        print("fallback")

# Also update summary paragraph that mentions 0 active debt details - append Phase 4 Sprint 3 info
# Find the long summary line starting with "10 total" already replaced, need to append new info
# Replace the summary paragraph tail
old_summary_tail="pytest 11 passed 0 failed isolation phase4 PASS, 0 active debt."
new_summary_tail="pytest 11 passed 0 failed isolation phase4 PASS, 0 active debt. Phase 4 Sprint 3 Task 3 isolation verification Q-001 re-measurement PASS per pseudocode registry://pseudocode/phase_4_sprint_3_task_3_code.md: src layout render __init__.py tiles.py effects.py hud.py present PASS, no pygame leak sys.modules delta PASS, no pygame import grep PASS, no external assets PASS, tiles.py no debug dot no gray fallback dual renderer unified 70% heat 30% base PASS, bare except fixed PASS, effects.py hud.py exist programmatic only PASS, headless importable PASS, no global random PASS, Q-001 re-measurement Random(42) 50/100/200 moves overall avg 1.385 <2.0 max <=3 clamp 0-3 tuning rationale reference Sprint2 avg 1.803 interior 9 vs edge 16 center hot spot vs cool edges metaphor validated interior_avg 2.400 edge_avg 1.286 PASS, pytest 18 passed 0 failed isolation phase4 PASS, 11 total 0 active 11 resolved 0 active debt."

if old_summary_tail in content:
    content=content.replace(old_summary_tail, new_summary_tail)
    print("updated summary tail")

p.write_text(content, encoding='utf-8')
print("written")
