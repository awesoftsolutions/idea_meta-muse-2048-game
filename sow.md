# Statement of Work — 2048

**Version:** 1.0 · **Date:** June 2026 · **Status:** Final
> **Tier:** Hard · **Category:** GUI / puzzle game · **Verifies:** game-logic correctness, open-ended creative design, programmatic rendering, persistence, CI + cross-platform binary packaging

> You are building a new, standalone project from this specification. You are tasked with
> completing this Statement of Work **fully and completely**. While working, keep these key
> facts in mind:
>
> - This is a **greenfield project** — there is no existing code. Build it from scratch, exactly as the Project Structure specifies. Do not add files, modules, or features beyond the spec.
> - Use **Poetry** to run Python, always.
> - **Verify the real game-framework API before writing code** — confirm the installed version and that the calls you use exist. Never code against a remembered API.
> - **Separate game logic from rendering.** The entire `src/core/` layer must be importable and testable with no framework or display dependency.
> - **Seed all randomness** (tile spawns) through an injectable source so tests are deterministic.
> - **Tests must exercise real behavior** — slide/merge correctness, spawn distribution, undo, game-over, achievements, and the twist.
> - **Verify your own work** — run the game and tests, and capture screenshots plus scripted key presses (tiles, movement/merge feedback, achievement feedback, game-over).
> - **Complete every acceptance criterion.** Partial completion is not "done."
> - If the spec is genuinely ambiguous, make a reasonable choice, note it in the README, and continue.
> - Maintain a calm and professional demeanor.

## Reference Documents & File Locations

- The chosen game framework's documentation for the pinned version (verify before coding).
- PyInstaller documentation for the standalone-binary target.
- GitHub Actions documentation for the CI workflow.
- The Favur testing-architecture guide.
- `_SOW_TEMPLATE.md` — the standard this fixture conforms to.

## Overview

A native desktop puzzle game inspired by *2048*, built with a Python game framework and
compilable to a standalone cross-platform binary. The core is a 5×5 sliding-tile board
with merge mechanics, scoring, move history with undo, persisted high score, and at least
ten achievements. Beyond the baseline, the spec demands a committed **creative twist** and
one **unconventional mechanic**, so this fixture stresses not just correctness but
open-ended design judgment, programmatic visual feedback, and the full build/CI/packaging
pipeline. The logic layer is fully separated from rendering so the mechanics are unit-testable
headlessly.

## Pre-Implementation Research

Before building the full game, complete a discovery pass and prove the riskiest pieces:

1. **Framework + packaging spike.** Confirm the pinned framework version and that a window
   opens and draws a primitive; confirm PyInstaller can package a trivial build of it on the
   target OS. Packaging surprises are cheaper to find now than at the end.
2. **Twist exploration.** Generate several distinct twist ideas (see Creative Requirements),
   evaluate each against the constraints (preserves core mechanics, adds consistent tension,
   one unconventional mechanic, distinct identity), then **commit to one** and record the
   decision and the rejected alternatives in the README. This exploration is a required output,
   not a private step.
3. **Slide/merge model spike.** Validate the slide-and-merge resolution (including
   one-merge-per-tile) against a few hand-worked board states before wiring rendering.

## Requirements

### Functional Requirements

- The board is a **5×5** grid of tiles representing powers of two (2, 4, 8, 16, 32, 64, …).
- The game starts with a single **2** tile placed on the board.
- The player slides all tiles **vertically or horizontally** using the arrow keys (or equivalent).
- On each slide, every tile moves as far as possible in the slide direction; a tile stops when
  it reaches the board edge or a tile it cannot merge with.
- After each slide, **one new tile spawns** in a random empty cell: a **2** with 90% probability,
  a **4** with 10% probability.
- When two tiles of the same value collide during a slide, they **merge** into the next power of
  two (2+2=4, 4+4=8, …). Merges happen only as a result of a slide.
- **At most one merge per tile per move** (a tile that was just formed by a merge cannot merge
  again in the same move).
- The **score** increases by the value of each tile produced by a merge.
- The game keeps a **move history** and allows the player to **reverse (undo) moves**.
- The game **ends** when no empty cell exists to spawn a tile and no merge is possible in any
  direction.

### Technical Requirements

- Python 3.11+.
- A Python game framework as the only graphical runtime dependency (e.g. `pygame-ce`).
- **All graphics generated programmatically** — no external images, sprites, or fonts-as-assets.
- **No audio required.**
- Window title: exactly `Favur 2048`.
- Window size: 700×800, non-resizable.
- A small mode/scene label is drawn in a fixed corner as a test-mode overlay.

### Build & Tooling Requirements

- Poetry + `pyproject.toml` for dependencies and build.
- Clean separation of **game logic** and **rendering** (logic importable and testable with no
  framework/display dependency).
- Automated tests for all core game logic.
- **GitHub Actions CI** running both the test suite and a build step.
- A documented way to compile the game into a **standalone cross-platform executable**
  (Windows, macOS, Linux) — e.g. PyInstaller.
- **High score is persisted** to disk between runs.

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── board.py          # 5x5 grid, slide/merge resolution, spawn logic
│   │   ├── rules.py          # move legality, game-over detection
│   │   ├── score.py          # scoring + high-score persistence
│   │   ├── history.py        # move history + undo
│   │   ├── achievements.py   # achievement definitions + unlock evaluation
│   │   └── twist.py          # the committed creative twist + unconventional mechanic
│   ├── render/
│   │   ├── __init__.py
│   │   ├── tiles.py          # programmatic tile drawing (distinct per value)
│   │   ├── effects.py        # movement/merge feedback (animation, scaling, particles)
│   │   └── hud.py            # score, high score, achievement toasts
│   └── main.py               # framework init, window, loop, input dispatch, Escape-to-quit
├── tests/
│   ├── __init__.py
│   ├── test_board.py         # slide/merge correctness, single-merge-per-tile, spawn rules
│   ├── test_rules.py         # game-over detection, legal/illegal moves
│   ├── test_score.py         # scoring math, high-score persistence
│   ├── test_history.py       # undo restores exact prior state
│   ├── test_achievements.py  # each achievement unlocks under its condition
│   └── test_twist.py         # the twist mechanic behaves deterministically
├── .github/
│   └── workflows/
│       └── ci.yml            # test + build
├── visual-proof/            # screenshots + README manifest captured during the build (required)
├── pyproject.toml
└── README.md
```

## Implementation Details

- `src/core/board.py`: Pure-Python `Board` holding the 5×5 grid. Resolves a slide in a given
  direction (move + merge), enforces one-merge-per-tile, and spawns a new tile with the 90/10
  distribution. Spawn randomness must be injectable/seedable so tests are deterministic. No
  rendering imports.
- `src/core/rules.py`: Move legality (a move is legal only if it changes the board) and
  game-over detection (no empty cell and no possible merge in any direction).
- `src/core/score.py`: Tracks current score; loads and saves the persisted high score.
- `src/core/history.py`: Records board states and supports undo, restoring the exact prior
  board and score.
- `src/core/achievements.py`: At least **10** achievements with creative, distinct unlock
  conditions; evaluates state after each move and reports newly unlocked achievements.
- `src/core/twist.py`: Implements the committed creative twist and the unconventional mechanic
  (see Creative Requirements). Deterministic and unit-testable.
- `src/render/*`: All drawing done programmatically — visually distinct tiles per value, plus
  movement and merge feedback (animation, scaling, particles, or screen effects) and HUD.
- `src/main.py`: Initializes the framework, creates the 700×800 `Favur 2048` window, runs the
  main loop, dispatches arrow-key input and undo, and handles global Escape-to-quit.
- `README.md`: Title, overview, the chosen twist and its identity, installation, run
  instructions, controls, how to build the standalone binary, and how to run the tests.

## Creative Requirements

These are the heart of this fixture and must not be reduced to a vanilla clone.

- **Explore multiple distinct twist ideas before choosing one**, then **select one direction
  and fully commit to it.**
- The twist must: preserve all core mechanics above; introduce new decision-making, strategy,
  or player tension; and affect gameplay **consistently**, not occasionally.
- **Incorporate one unexpected or unconventional mechanic** that would not normally appear in a
  puzzle game, and make it feel natural.
- The game must have a **clear identity or personality** that influences visuals, mechanics, and
  feedback.

**Uniqueness pressure:** do not produce a standard 2048 clone or a common/obvious variant.
Introduce at least one surprising mechanic or system so the result feels like a distinct game,
not a variation — it should feel like it could not have been generated twice the same way.

## Visual & Interaction Requirements

- Each tile value is **visually distinct**.
- Movement and merges have **visual feedback** (animation, scaling, particles, or screen effects).
- **Strong visual consistency** across the game, expressing the chosen identity.
- All graphics are programmatic; no audio.
- Input: arrow keys (or equivalent) for movement; a key for undo; Escape to quit.

## Error Handling Strategy

- A high-score file that is missing, empty, or corrupt must not crash the game — treat it as a
  zero high score and overwrite it on the next save.
- An undo with no prior state is a no-op, not an error.
- An illegal move (one that changes nothing) must not spawn a new tile or alter the score.

## Testing Requirements

Per the Favur testing architecture, all of `src/core/` is unit-tested headlessly with no
framework or display import. Spawn randomness is injected/seeded so spawn-distribution and
game-over tests are deterministic. Coverage must include: slide/merge correctness with
one-merge-per-tile, the 90/10 spawn distribution over a seeded run, scoring math, high-score
persistence (including the corrupt-file path), undo restoring exact prior state, game-over
detection, each achievement's unlock condition, and the twist's deterministic behavior.

## Visual Verification Protocol

Visual verification is **continuous and artifact-gated** — not a final step. This build is large
enough that, without an enforced cadence, a run can finish the logic and never show a board.
Therefore:

- **First light early.** As soon as `Board` produces a real grid, draw the window with the title,
  background, and the actual board with its starting tile, and capture a screenshot — *before*
  animations, HUD, or achievements exist.
- **Screenshot every visible change.** Capture and save a screenshot to `visual-proof/` at the
  exit of every phase that touches rendering, and whenever the rendered output changes
  meaningfully. Never advance a phase without its screenshot.
- **`visual-proof/` is a required deliverable** containing: first light; tiles after a few real
  moves; a merge with its movement/merge feedback; an achievement toast; the game-over state;
  and a `visual-proof/README.md` manifest naming each file, what it shows, and the input sequence.
- **A run that completes without these artifacts is a FAILED run regardless of `pytest` status.**

## Implementation Phases

1. **Research & spikes** — exit when the framework/PyInstaller spike runs (a window opens and
   draws a primitive — capture it), the twist is chosen and recorded, and the slide/merge model
   is validated against hand-worked states.
2. **Core logic + tests** — board, rules, score, history, achievements, twist, all with passing
   headless tests. Exit when `poetry run pytest` is green with no rendering written yet.
3. **First light (screenshot-gated)** — draw the real board and its starting tile in the titled
   window, with arrow input moving tiles. **Exit only when a first-light screenshot is saved to
   `visual-proof/`.**
4. **Feedback, HUD & identity (screenshot-gated)** — movement/merge feedback, particles, HUD,
   achievement toasts, and the committed identity. **Exit when screenshots of a merge, a toast,
   and the game-over state are saved.**
5. **Visual-proof sweep** — capture any remaining per-criterion screenshots and finalize the
   `visual-proof/README.md` manifest. Exit when every Visual acceptance item is demonstrated.
6. **CI & packaging** — GitHub Actions (test + build) and the standalone binary. Exit when CI is
   green and a binary builds on the target OS.

## Acceptance Criteria

**Gating requirement (graded first):** a populated `visual-proof/` directory with the screenshots
and manifest below must be present. **A run that completes without it is a FAILED run even if all
tests pass.**

1. Sliding moves every tile maximally in the chosen direction, with edge and blocking behavior correct.
2. Equal-value tiles merge into the next power of two, with at most one merge per tile per move.
3. A new tile spawns after each board-changing move, 2 at ~90% and 4 at ~10% (verified over a seeded run).
4. The score increases by the value of each merged tile.
5. Undo restores the exact previous board state and score.
6. The game ends precisely when no empty cell and no possible merge remain.
7. The high score persists across separate runs.
8. At least 10 distinct achievements exist and each unlocks under its stated condition.
9. The committed twist and the unconventional mechanic are present and affect gameplay consistently.
10. The project is generated with the specified file structure.
11. All Python files are free of syntax errors.
12. `poetry run pytest` passes with **0 failures — mandatory**.
13. `poetry run python -m src.main` launches the game without errors.
14. `visual-proof/` contains first light, tiles after real moves, a merge with feedback, an achievement toast, and game-over — plus a manifest naming each file and its input sequence — captured progressively during the build, not only at the end.
15. GitHub Actions CI passes (test + build), and the standalone binary builds successfully.
## Appendix A — Sample phase exit checklist

A worked example of what "exit" looks like for Phase 2 (core logic), as a model for the rest:

- `Board.slide(direction)` returns the new grid and the score delta for all four directions.
- A 2+2 row merges to a single 4 and never to two 4s (one-merge-per-tile).
- A seeded run of 1,000 spawns yields ~90% 2s and ~10% 4s within tolerance.
- `history.undo()` after N moves restores the exact grid and score from move N−1.
- `rules.is_game_over()` is true only when no empty cell and no merge exist in any direction.
- `poetry run pytest` is green; `src/render/` and `src/main.py` do not yet exist.

## Document Control

| Version | Date | Change |
|---|---|---|
| 1.0 | June 2026 | Restructured from prose into the standard greenfield SOW format; added working agreement, research phase, error handling, testing requirements, and phased plan. |
