"""
tests/test_score.py — Comprehensive ScoreState persistence tests per pseudocode TDD.

Covers scoring math merge 2+2=4 adds 4, persistence across instances,
corrupt handling missing/empty/invalid JSON/non-int/negative/missing key,
overwrite after corrupt, atomic write temp file rename, no pygame import
via sys.modules, headless importable.

Production module: src/core/score.py with ScoreState dataclass
  current_score, high_score, high_score_path, last_save_success,
  methods add, load, save, helper _validate_high_score_data,
  constant DEFAULT_HIGH_SCORE_PATH.

TDD red phase: this file is created before src/core/score.py exists,
so pytest will fail with ModuleNotFoundError/ImportError initially.
That is expected correct outcome for step 2 of 7.

System: src/core per Phase 2 architecture ADR-012, ADR-015, E003.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# ---------------------------------------------------------------------------
# Fixtures — injectable Path via TemporaryDirectory
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory Path, cleaned up after test."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def temp_path(temp_dir: Path) -> Path:
    """Provide a temp file Path inside temp_dir for high_score.json."""
    return temp_dir / "high_score.json"


@pytest.fixture
def score_state(temp_path: Path):
    """Create ScoreState with injectable temp path."""
    from src.core.score import ScoreState

    return ScoreState(high_score_path=temp_path)


# ---------------------------------------------------------------------------
# Group: Scoring Math
# ---------------------------------------------------------------------------


def test_score_math_merge_2_plus_2_equals_4_adds_4(temp_path: Path) -> None:
    """AC-1 When add(4) called then current_score 4 high_score 4 file {high_score:4}."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    assert state.current_score == 0
    assert state.high_score == 0

    state.add(4)

    assert state.current_score == 4, (
        f"Expected current_score 4, got {state.current_score}"
    )
    assert state.high_score == 4, f"Expected high_score 4, got {state.high_score}"
    assert state.last_save_success is True
    assert temp_path.exists(), (
        "high_score file should exist after add that updates high"
    )

    data = json.loads(temp_path.read_text(encoding="utf-8"))
    assert data == {"high_score": 4}, f"Expected {{high_score:4}}, got {data}"


def test_score_add_multiple_deltas(temp_path: Path) -> None:
    """Add 4 then 8 -> current 12 high 12."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    state.add(4)
    state.add(8)

    assert state.current_score == 12
    assert state.high_score == 12

    data = json.loads(temp_path.read_text(encoding="utf-8"))
    assert data["high_score"] == 12


def test_score_add_zero_no_op(temp_path: Path) -> None:
    """Add 0 is no-op, no file created if high still 0."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    state.add(0)

    assert state.current_score == 0
    assert state.high_score == 0


def test_score_add_negative_ignored(temp_path: Path) -> None:
    """Negative delta ignored per spec."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    state.add(4)
    state.add(-5)

    assert state.current_score == 4, "Negative delta should be ignored"
    assert state.high_score == 4


# ---------------------------------------------------------------------------
# Group: Persistence Across Instances
# ---------------------------------------------------------------------------


def test_high_score_persistence_save_and_load_across_instances(temp_path: Path) -> None:
    """Instance A add(10) save, Instance B same path load returns 10."""
    from src.core.score import ScoreState

    state_a = ScoreState(high_score_path=temp_path)
    state_a.add(10)
    assert state_a.save() is True

    state_b = ScoreState(high_score_path=temp_path)
    # __init__ should have loaded 10
    assert state_b.high_score == 10, (
        f"Expected high_score 10 after reload, got {state_b.high_score}"
    )

    loaded = state_b.load()
    assert loaded == 10


# ---------------------------------------------------------------------------
# Group: Corrupt Handling — must never crash, return 0
# ---------------------------------------------------------------------------


def test_corrupt_missing_returns_0_no_crash(temp_path: Path) -> None:
    """AC-2 Load from non-existent path returns 0 no crash."""
    from src.core.score import ScoreState

    # Ensure file does not exist
    if temp_path.exists():
        temp_path.unlink()

    state = ScoreState(high_score_path=temp_path)
    # Constructor should handle missing file returning 0
    assert state.high_score == 0

    result = state.load()
    assert result == 0, f"Expected 0 for missing file, got {result}"
    assert state.current_score == 0


def test_corrupt_empty_file_returns_0(temp_path: Path) -> None:
    """AC-3 Empty file returns 0 no crash."""
    from src.core.score import ScoreState

    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text("", encoding="utf-8")

    state = ScoreState(high_score_path=temp_path)
    result = state.load(temp_path)

    assert result == 0, f"Expected 0 for empty file, got {result}"


def test_corrupt_invalid_json_returns_0(temp_path: Path) -> None:
    """AC-4 Invalid JSON returns 0 no crash."""
    from src.core.score import ScoreState

    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text("{invalid json", encoding="utf-8")

    state = ScoreState(high_score_path=temp_path)
    result = state.load()

    assert result == 0, f"Expected 0 for invalid JSON, got {result}"


def test_corrupt_non_int_value_returns_0(temp_path: Path) -> None:
    """AC-5 Non-int JSON values return 0: string, float, bool, None, list, dict."""
    from src.core.score import ScoreState

    cases = [
        {"high_score": "not-an-int"},
        {"high_score": 3.14},
        {"high_score": True},
        {"high_score": False},
        {"high_score": None},
        {"high_score": [1]},
        {"high_score": {"a": 1}},
    ]

    for case in cases:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(json.dumps(case), encoding="utf-8")

        state = ScoreState(high_score_path=temp_path)
        result = state.load()

        assert result == 0, f"Expected 0 for case {case}, got {result}"


def test_corrupt_negative_returns_0(temp_path: Path) -> None:
    """Negative high_score returns 0."""
    from src.core.score import ScoreState

    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(json.dumps({"high_score": -5}), encoding="utf-8")

    state = ScoreState(high_score_path=temp_path)
    result = state.load()

    assert result == 0, f"Expected 0 for negative value, got {result}"


def test_corrupt_missing_key_returns_0(temp_path: Path) -> None:
    """Missing high_score key returns 0."""
    from src.core.score import ScoreState

    for bad in [{}, {"score": 100}, {"highScore": 10}]:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(json.dumps(bad), encoding="utf-8")

        state = ScoreState(high_score_path=temp_path)
        result = state.load()

        assert result == 0, f"Expected 0 for missing key case {bad}, got {result}"


# ---------------------------------------------------------------------------
# Group: Overwrite and Atomic Write
# ---------------------------------------------------------------------------


def test_overwrite_on_save_after_corrupt_file(temp_path: Path) -> None:
    """AC-7 Corrupt file then save overwrites valid JSON subsequent load returns new high."""
    from src.core.score import ScoreState

    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text("{corrupt", encoding="utf-8")

    state = ScoreState(high_score_path=temp_path)
    assert state.high_score == 0

    state.add(20)
    assert state.save() is True

    # File now valid JSON
    data = json.loads(temp_path.read_text(encoding="utf-8"))
    assert data == {"high_score": 20}

    # Subsequent load returns 20
    state2 = ScoreState(high_score_path=temp_path)
    assert state2.high_score == 20
    assert state2.load() == 20


def test_atomic_write_temp_file_rename_pattern(temp_path: Path) -> None:
    """AC-6 Save uses atomic temp file rename: no temp files remain, valid JSON, returns True."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    state.add(42)

    result = state.save()
    assert result is True
    assert state.last_save_success is True

    # No temp files remain in dir
    parent = temp_path.parent
    leftover_temps = (
        list(parent.glob("*.tmp"))
        + list(parent.glob("*.tmp.*"))
        + list(parent.glob("tmp*"))
    )
    # Filter out our target file itself
    leftover_temps = [p for p in leftover_temps if p != temp_path]
    assert len(leftover_temps) == 0, (
        f"Temp files remain after atomic save: {leftover_temps}"
    )

    # File content valid JSON with correct shape
    content = temp_path.read_text(encoding="utf-8")
    data = json.loads(content)
    assert isinstance(data, dict)
    assert "high_score" in data
    assert data["high_score"] == 42
    assert isinstance(data["high_score"], int)
    assert not isinstance(data["high_score"], bool)


def test_save_returns_bool_and_sets_last_save_success(temp_path: Path) -> None:
    """Save success returns True and last_save_success True; failure returns False."""
    from src.core.score import ScoreState

    state = ScoreState(high_score_path=temp_path)
    state.add(5)

    success = state.save()
    assert success is True
    assert state.last_save_success is True

    # Failure case: path is a directory
    dir_path = temp_path.parent / "a_directory"
    dir_path.mkdir(parents=True, exist_ok=True)

    state2 = ScoreState(high_score_path=temp_path)
    state2.add(10)
    fail_result = state2.save(dir_path)  # saving to a directory should fail
    assert fail_result is False, "Saving to directory path should return False"
    assert state2.last_save_success is False


# ---------------------------------------------------------------------------
# Group: Isolation — no pygame, headless
# ---------------------------------------------------------------------------


def test_no_pygame_import_via_sys_modules(temp_path: Path) -> None:
    """Verify src.core.score does not import pygame via sys.modules snapshot."""
    # Snapshot before
    before = set(sys.modules.keys())

    # Import module under test
    import src.core.score  # noqa: F401
    from src.core.score import ScoreState  # noqa: F401

    after = set(sys.modules.keys())
    new_modules = after - before

    # Check no pygame in newly imported modules
    pygame_leaks = [m for m in new_modules if "pygame" in m.lower()]
    assert len(pygame_leaks) == 0, (
        f"pygame leak detected in new modules: {pygame_leaks}"
    )

    # Also ensure pygame not in sys.modules at all after import
    assert "pygame" not in sys.modules, "pygame found in sys.modules after import"
    assert "pygame_ce" not in sys.modules
    assert "pygame-ce" not in sys.modules


def test_headless_importable_without_display() -> None:
    """Import src.core.score without DISPLAY env, no crash."""
    # This test runs headlessly; just importing should not require DISPLAY
    from src.core.score import (  # noqa: F401
        DEFAULT_HIGH_SCORE_PATH,
        ScoreState,
        _validate_high_score_data,
    )

    assert DEFAULT_HIGH_SCORE_PATH is not None
    assert isinstance(DEFAULT_HIGH_SCORE_PATH, Path)

    # _validate helper exists and rejects invalid
    try:
        _validate_high_score_data({"high_score": "bad"})
        assert False, "Should have raised ValueError for non-int"
    except ValueError:
        pass  # expected

    # ScoreState creation headless
    import tempfile as _tempfile

    with _tempfile.TemporaryDirectory() as td:
        p = Path(td) / "hs.json"
        s = ScoreState(high_score_path=p)
        assert s.current_score == 0
        assert s.high_score == 0
