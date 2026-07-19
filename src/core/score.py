"""src/core/score.py — ScoreState persistence atomic write corrupt handling.

Purpose: Implements ScoreState dataclass with current_score, high_score,
    high_score_path, last_save_success, plus methods add, load, save with
    atomic write via temp file rename and corrupt handling treating
    missing/empty/invalid JSON as zero per ADR-012, E003. Phase 6 packaging
    hardening adds writable fallback sys._MEIPASS aware.

System: src/core per Phase 2 architecture ADR-012, ADR-015, Phase 6 ADR-038.

Dependencies: stdlib only — json, os, sys, tempfile, pathlib, dataclasses, typing.
    Never pygame-ce per ADR-015.

Used-by: src/core/__init__.py exports, tests/test_score.py, src/main.py packaging,
    future game loop.

Public interface:
    - WRITABLE_DIR_NAME: str = ".favur-2048" writable user dir for frozen binary
    - HIGHSCORE_FILENAME: str = "highscore.json" file name in writable dir
    - LEGACY_HIGH_SCORE_PATH: Path = Path.home() / ".favur2048" / "high_score.json" backward compat
    - DEFAULT_HIGH_SCORE_PATH: Path = Path.home() / ".favur-2048" / "highscore.json" new location
    - _is_frozen() -> bool: checks sys._MEIPASS or sys.frozen for PyInstaller frozen binary
    - get_writable_dir() -> Path: returns writable user dir Path.home()/.favur-2048 mkdir parents True exist_ok True OSError fallback
    - get_highscore_path() -> Path: returns writable_dir/highscore.json sys._MEIPASS aware resource vs data separation
    - _validate_high_score_data(data) -> int: validates dict with high_score key int>=0 not bool
    - ScoreState: dataclass current_score, high_score, high_score_path, last_save_success
      methods __init__(high_score_path Optional[Path], initial_high_score int),
      add(delta), load(path Optional[Path])->int, save(path Optional[Path])->bool
    - Score alias for ScoreState
"""
# CHANGELOG:
# - Phase 2 Sprint 2: ScoreState persistence atomic write corrupt handling —
#   current_score, high_score, high_score_path injectable, last_save_success,
#   add with 0 no-op negative ignored non-int TypeError, load full corrupt
#   handling returning 0 never crash, save atomic temp file rename via
#   os.replace, helper _validate_high_score_data bool subclass check,
#   DEFAULT_HIGH_SCORE_PATH constant, stdlib only no pygame.
# - Phase 6 Sprint 1: PACKAGING HARDENING writable fallback sys._MEIPASS aware —
#   WRITABLE_DIR_NAME .favur-2048, HIGHSCORE_FILENAME highscore.json,
#   LEGACY_HIGH_SCORE_PATH backward compat, get_writable_dir mkdir parents
#   True exist_ok True OSError fallback relative, get_highscore_path
#   sys._MEIPASS aware resource vs data separation writable user dir not
#   _MEIPASS read-only, _is_frozen sys._MEIPASS frozen check, CI workflow
#   packaging hardening validation.

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Writable user dir for frozen binary packaging hardening per ADR-038
# Primary path uses .favur-2048 per Phase 6 spec, fallback .favur2048 for backward compat
WRITABLE_DIR_NAME: str = ".favur-2048"
HIGHSCORE_FILENAME: str = "highscore.json"
LEGACY_HIGH_SCORE_PATH: Path = Path.home() / ".favur2048" / "high_score.json"
DEFAULT_HIGH_SCORE_PATH: Path = Path.home() / WRITABLE_DIR_NAME / HIGHSCORE_FILENAME


def _is_frozen() -> bool:
    """Check if running in frozen binary (PyInstaller).

    Returns:
        True if frozen via sys._MEIPASS or sys.frozen attribute.
    """
    # sys._MEIPASS aware check for PyInstaller frozen binary
    if hasattr(sys, "_MEIPASS"):
        return True
    if getattr(sys, "frozen", False):
        return True
    return False


def get_writable_dir() -> Path:
    """Get writable user dir for high-score persistence.

    Uses pathlib.Path.home()/.favur-2048/highscore.json fallback per ADR-038.
    Handles OSError with fallback to relative path.

    Returns:
        Writable directory Path, created with mkdir parents=True exist_ok=True.
    """
    try:
        writable_dir = Path.home() / WRITABLE_DIR_NAME
        # Ensure dir exists with parents=True exist_ok=True
        writable_dir.mkdir(parents=True, exist_ok=True)
        return writable_dir
    except OSError:
        # Fallback to relative path if home not writable
        try:
            fallback = Path(".favur-2048")
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except OSError:
            return Path(".favur-2048")


def get_highscore_path() -> Path:
    """Get high-score file path in writable dir.

    Returns:
        Path to highscore.json in writable user dir.
    """
    # sys._MEIPASS aware: resource vs data separation
    # For frozen binary, still use writable user dir, not _MEIPASS (read-only)
    # _MEIPASS is for bundled resources, high-score must be writable
    if _is_frozen():
        # In frozen binary, use writable dir, not sys._MEIPASS
        base = get_writable_dir()
        return base / HIGHSCORE_FILENAME
    return get_writable_dir() / HIGHSCORE_FILENAME


# Backward compat alias for old path constant still used in tests
# Keep DEFAULT_HIGH_SCORE_PATH pointing to new location
# Old constant preserved as LEGACY_HIGH_SCORE_PATH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_high_score_data(data: object) -> int:
    """Validate loaded JSON data, return int >=0 or raise ValueError.

    Args:
        data: Parsed JSON object to validate.

    Returns:
        Validated high_score int >=0.

    Raises:
        ValueError: If data is None, not dict, missing key, non-int,
            bool subclass, negative.
    """
    if data is None:
        raise ValueError("None data")
    if not isinstance(data, dict):
        raise ValueError("not dict")
    if "high_score" not in data:
        raise ValueError("missing key")
    value = data["high_score"]
    # Bool is subclass of int — must reject before int check
    if isinstance(value, bool):
        raise ValueError("bool not allowed")
    if not isinstance(value, int):
        raise ValueError("non-int")
    if value < 0:
        raise ValueError("negative")
    return value


# ---------------------------------------------------------------------------
# ScoreState dataclass
# ---------------------------------------------------------------------------


@dataclass
class ScoreState:
    """Scoring and high-score persistence per ADR-012, E003.

    Attributes:
        current_score: Running score for current game.
        high_score: Persisted high score loaded from file.
        high_score_path: File location for JSON persistence, injectable.
        last_save_success: Tracks last save outcome.

    Public methods:
        add(delta): Increase current_score, update high_score if needed then save.
        load(path): Load high_score from JSON, return 0 on corrupt/missing/empty never crash.
        save(path): Atomically write high_score JSON via temp file rename, return bool.
    """

    current_score: int = 0
    high_score: int = 0
    high_score_path: Path = field(default_factory=lambda: DEFAULT_HIGH_SCORE_PATH)
    last_save_success: bool = True

    def __init__(
        self,
        high_score_path: Optional[Path] = None,
        initial_high_score: int = 0,
    ) -> None:
        """Initialize ScoreState with injectable path and optional initial high score.

        Args:
            high_score_path: Optional path for high-score JSON, injectable for tests.
                If None, uses DEFAULT_HIGH_SCORE_PATH.
            initial_high_score: Optional initial high score >0 to use directly,
                otherwise attempts to load existing high score from file.
        """
        # Resolve effective path
        if high_score_path is None:
            effective_path = DEFAULT_HIGH_SCORE_PATH
        else:
            try:
                effective_path = Path(high_score_path)
            except (ValueError, TypeError, AttributeError):
                effective_path = DEFAULT_HIGH_SCORE_PATH

        self.high_score_path: Path = effective_path
        self.current_score: int = 0
        self.last_save_success: bool = True

        if isinstance(initial_high_score, int) and not isinstance(
            initial_high_score, bool
        ):
            if initial_high_score > 0:
                self.high_score: int = initial_high_score
            else:
                # Load existing high score, never crash per E003
                try:
                    loaded = self.load(effective_path)
                    self.high_score = loaded
                except (ValueError, TypeError, AttributeError):
                    self.high_score = 0
        else:
            # Invalid initial_high_score type, fallback to load
            try:
                loaded = self.load(effective_path)
                self.high_score = loaded
            except (ValueError, TypeError, AttributeError):
                self.high_score = 0

    def add(self, delta: int) -> None:
        """Increase current_score by delta, update high_score if current exceeds high, then save.

        Args:
            delta: Merged value >=0 to add to current_score.

        Raises:
            TypeError: If delta is not int (except None treated as 0 no-op).
        """
        # Handle None as 0 no-op per defensive design
        if delta is None:
            return

        # Reject bool — bool is subclass of int
        if isinstance(delta, bool):
            raise TypeError("delta bool not allowed")

        if not isinstance(delta, int):
            raise TypeError(f"delta must be int, got {type(delta).__name__}")

        if delta < 0:
            # Negative ignored per spec
            return

        if delta == 0:
            return

        self.current_score = self.current_score + delta

        if self.current_score > self.high_score:
            self.high_score = self.current_score
            try:
                success = self.save(self.high_score_path)
                self.last_save_success = success
            except (ValueError, TypeError, AttributeError):
                self.last_save_success = False

    def load(self, path: Optional[Path] = None) -> int:
        """Load high_score from JSON file, return 0 on any corrupt/missing/empty, never crash.

        Args:
            path: Optional override path, uses self.high_score_path if None.

        Returns:
            Loaded high_score int >=0, or 0 on any corrupt/missing/empty case.
        """
        # Resolve effective path
        if path is None:
            effective_path = self.high_score_path
        else:
            try:
                effective_path = Path(path)
            except (ValueError, TypeError, AttributeError):
                return 0

        try:
            # Attempt to open and read
            with open(effective_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.strip() == "":
                return 0

            data = json.loads(content)
            validated = _validate_high_score_data(data)

            # Update self.high_score to max to avoid lowering? Spec says load returns int
            # and should update self.high_score. Use max to preserve higher in-memory value
            # unless file has higher, but for initializing case we want file value.
            # Choose: set to validated if validated > current high, else keep?
            # Simpler: if validated > self.high_score, update. Return validated.
            # For test expectations, when file has value, constructor should have that value.
            # So we update if validated > self.high_score OR if self.high_score==0 and validated>=0?
            # To satisfy persistence test, we need to update to validated when loading.
            # Implementation: if validated > self.high_score, update. But also if we are
            # explicitly loading, return file value and update to max.
            # We'll set self.high_score = max(self.high_score, validated) for safety,
            # but also ensure initial load works when high_score is 0.
            # Actually for exact file value return, we should set self.high_score to
            # validated if validated !=0? Let's use max to avoid lowering.
            if validated > self.high_score:
                self.high_score = validated
            # If self.high_score is 0 and validated is 0, keep 0.
            # For case where file has lower value than memory, we keep memory high.
            # However for constructor load, memory is 0 so it will take file value.
            # Edge: if file has 5 and memory has 10, we keep 10 but return 5 per spec
            # "load returns int". The test for persistence expects high_score 10 after reload.
            # So returning validated is correct, but self.high_score stays max.
            # For constructor case, self.high_score is 0, so it becomes validated.
            # To make constructor set exactly file value even if lower than existing?
            # Constructor starts with 0, so max works.
            # For explicit load after having higher score, should we overwrite?
            # Spec ambiguous. We'll implement: if validated > self.high_score, update,
            # else keep. Return validated.
            # However to satisfy test where state.high_score is 0 and file has 10,
            # max works.
            # For overwrite test, after corrupt file, add(20) saves 20, then new instance
            # loads 20 — constructor max works.
            # For load() returning file value even if lower, we return validated.
            # But also need to ensure that when file has valid value, self.high_score
            # becomes at least that value. So max is safe.
            # Special case: if self.high_score is 0 and file has 0, stays 0.
            # If we want load to always set self.high_score to validated (overwrite),
            # we would lose higher in-memory high. Choose max for safety.
            # Let's also handle case where self.high_score ==0 and validated>0 -> set.
            # Already covered by max.
            # For simplicity, if this load is called from __init__ when high_score is 0,
            # it will set to validated. Good.
            # If we want to ensure load always updates to validated when validated>0,
            # max does that.
            # We'll keep max logic.
            return validated

        except FileNotFoundError:
            return 0
        except IsADirectoryError:
            return 0
        except json.JSONDecodeError:
            return 0
        except ValueError:
            return 0
        except OSError:
            return 0
        except (ValueError, TypeError, AttributeError):
            return 0

    def save(self, path: Optional[Path] = None) -> bool:
        """Save high_score as JSON {high_score:int} via atomic temp file rename.

        Args:
            path: Optional override path, uses self.high_score_path if None.

        Returns:
            True on success, False on IOError or any failure, never crashes.
        """
        if path is None:
            effective_path = self.high_score_path
        else:
            try:
                effective_path = Path(path)
            except (ValueError, TypeError, AttributeError):
                self.last_save_success = False
                return False

        data = {"high_score": self.high_score}
        temp_path: Optional[str] = None

        try:
            parent_dir = effective_path.parent
            # Ensure parent directory exists
            parent_dir.mkdir(parents=True, exist_ok=True)

            # Create temp file in same directory for atomic rename
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(parent_dir),
                delete=False,
                suffix=".tmp",
            ) as temp_file:
                temp_path = temp_file.name
                json.dump(data, temp_file)
                temp_file.flush()
                try:
                    os.fsync(temp_file.fileno())
                except (ValueError, TypeError, AttributeError):
                    # fsync optional, ignore failure
                    pass

            # Atomic rename via os.replace (overwrite atomic on Windows and POSIX)
            os.replace(temp_path, effective_path)
            self.last_save_success = True
            return True

        except (OSError, IOError, PermissionError, ValueError, TypeError):
            # Cleanup temp file if created
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except (ValueError, TypeError, AttributeError):
                    pass
            self.last_save_success = False
            return False
        except (ValueError, TypeError, AttributeError):
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except (ValueError, TypeError, AttributeError):
                    pass
            self.last_save_success = False
            return False


# Alias for backward compatibility per pseudocode
Score = ScoreState
