"""Tests for Phase 4 Sprint 3 Task 2 visual-proof PNGs merge toast gameover.

Pseudocode: registry://pseudocode/phase_4_sprint_3_task_2_code.md
Covers AC-1 to AC-5 plus OSError handling robustness.

Validation approach:
- PNG header 89 50 4E 47 via pathlib read_bytes data[:4]==b'\\x89PNG'
- Full 8-byte signature 89 50 4E 47 0D 0A 1A 0A
- IHDR dimensions 700x800 via struct.unpack >I at offset 16-20
- Manifest entries file/shows/input/observation_id obs_ pattern
- Visual launch via src/main.py inspection not GUI launch in pytest
- OSError specific handling not bare except

TDD red phase: expected FAIL if PNGs missing, PASS after capture.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path
from unittest.mock import patch


PNG_SIGNATURE_4 = b"\x89PNG"
PNG_SIGNATURE_8 = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 700
EXPECTED_HEIGHT = 800
VISUAL_PROOF_DIR = Path("visual-proof")
MERGE_PNG = VISUAL_PROOF_DIR / "phase-4-merge.png"
TOAST_PNG = VISUAL_PROOF_DIR / "phase-4-toast.png"
GAMEOVER_PNG = VISUAL_PROOF_DIR / "phase-4-gameover.png"
MANIFEST = VISUAL_PROOF_DIR / "README.md"
MAIN_PY = Path("src/main.py")


def validate_png_header(path: Path) -> bool:
    """Validate PNG exists size>0 header 89 50 4E 47.

    Args:
        path: PNG file path.

    Returns:
        True if valid PNG header.

    Raises:
        OSError: If file read fails (handled by caller).
    """
    if not path.exists():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) == 0:
        return False
    if data[:4] != PNG_SIGNATURE_4:
        return False
    if len(data) >= 8 and data[:8] != PNG_SIGNATURE_8:
        return False
    return True


def validate_png_dimensions_ihdr(
    path: Path, expected_width: int = 700, expected_height: int = 800
) -> bool:
    """Parse IHDR chunk for 700x800 dimensions without DISPLAY.

    PNG structure: 8-byte signature + 4-byte length + 4-byte type IHDR
    + 4-byte width + 4-byte height big-endian uint32 at offset 16-20.

    Args:
        path: PNG file path.
        expected_width: Expected width 700.
        expected_height: Expected height 800.

    Returns:
        True if dimensions match.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) < 24:
        return False
    if data[:8] != PNG_SIGNATURE_8:
        return False
    try:
        # Offset 8: chunk length 4 bytes big-endian should be 13 for IHDR
        # Offset 12: chunk type 4 bytes should be b'IHDR'
        chunk_type = data[12:16]
        if chunk_type != b"IHDR":
            return False
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
        if width != expected_width or height != expected_height:
            return False
    except (ValueError, TypeError, struct.error):
        return False
    return True


def test_merge_png_exists_valid_header() -> None:
    """AC-1 merge PNG exists valid PNG header 89 50 4E 47 700x800."""
    assert MERGE_PNG.exists(), f"{MERGE_PNG} missing"
    data = MERGE_PNG.read_bytes()
    assert len(data) > 0, "merge PNG empty"
    assert data[:4] == PNG_SIGNATURE_4, f"header mismatch {data[:4]!r} expected 89 50 4E 47"
    assert data[:8] == PNG_SIGNATURE_8, f"8-byte signature mismatch {data[:8]!r}"
    assert validate_png_header(MERGE_PNG), "merge PNG header validation failed"
    assert validate_png_dimensions_ihdr(
        MERGE_PNG, EXPECTED_WIDTH, EXPECTED_HEIGHT
    ), f"merge PNG dimensions not {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"


def test_toast_png_exists_valid_header() -> None:
    """AC-2 toast PNG exists valid header 89 50 4E 47 700x800."""
    assert TOAST_PNG.exists(), f"{TOAST_PNG} missing"
    data = TOAST_PNG.read_bytes()
    assert len(data) > 0, "toast PNG empty"
    assert data[:4] == PNG_SIGNATURE_4, f"header mismatch {data[:4]!r}"
    assert data[:8] == PNG_SIGNATURE_8, "8-byte signature mismatch"
    assert validate_png_header(TOAST_PNG), "toast PNG header validation failed"
    assert validate_png_dimensions_ihdr(
        TOAST_PNG, EXPECTED_WIDTH, EXPECTED_HEIGHT
    ), f"toast PNG dimensions not {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"


def test_gameover_png_exists_valid_header() -> None:
    """AC-3 gameover PNG exists valid header showing overlay 700x800 size>1000."""
    assert GAMEOVER_PNG.exists(), f"{GAMEOVER_PNG} missing"
    data = GAMEOVER_PNG.read_bytes()
    assert len(data) > 0, "gameover PNG empty"
    assert len(data) > 1000, f"gameover PNG too small {len(data)} bytes expected >1000"
    assert data[:4] == PNG_SIGNATURE_4, f"header mismatch {data[:4]!r}"
    assert data[:8] == PNG_SIGNATURE_8, "8-byte signature mismatch"
    assert validate_png_header(GAMEOVER_PNG), "gameover PNG header validation failed"
    assert validate_png_dimensions_ihdr(
        GAMEOVER_PNG, EXPECTED_WIDTH, EXPECTED_HEIGHT
    ), f"gameover PNG dimensions not {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"


def test_manifest_contains_three_entries_with_observation_id() -> None:
    """AC-4 README contains entries for 3 PNGs naming file shows input observation_id."""
    assert MANIFEST.exists(), f"{MANIFEST} missing"
    content = MANIFEST.read_text(encoding="utf-8")

    # Check file names present
    assert "phase-4-merge.png" in content, "merge entry missing in manifest"
    assert "phase-4-toast.png" in content, "toast entry missing in manifest"
    assert "phase-4-gameover.png" in content, "gameover entry missing in manifest"

    # Check SOW Visual Verification Protocol fields
    assert "shows:" in content, "shows: field missing"
    assert "input:" in content, "input: field missing"
    assert "observation_id:" in content, "observation_id: field missing"

    # Check descriptions per variant
    # Merge: feedback particles scaling heat glow
    assert re.search(r"merge.*feedback|feedback.*merge", content, re.IGNORECASE), \
        "merge description missing feedback particles"
    # Toast: Thermal Entropy identity
    assert "Thermal Entropy" in content or "thermal entropy" in content.lower(), \
        "toast Thermal Entropy identity missing"
    # Gameover: restart prompt
    assert "restart" in content.lower(), "gameover restart prompt missing"

    # Check observation_id pattern obs_00000*
    obs_pattern = re.compile(r"obs_\d+")
    matches = obs_pattern.findall(content)
    assert len(matches) >= 3, f"expected >=3 observation_id obs_ pattern, found {matches}"

    # Check specific format "- file: X, shows: Y, input: Z, observation_id: obs_N"
    # At least check that file: pattern exists for each
    assert content.count("file:") >= 3, "expected >=3 file: entries"


def test_visual_launch_700x800_favur_2048_window() -> None:
    """AC-5 python -m src.main 700x800 Favur 2048 window verified via file inspection and PNGs.

    Headless friendly: verifies src/main.py contains Favur 2048 title and 700x800,
    plus PNGs exist valid header dimensions and manifest observation_id.
    Does not launch GUI in pytest to keep non-interactive.
    """
    # Verify src/main.py contains Favur 2048 exact title
    assert MAIN_PY.exists(), f"{MAIN_PY} missing"
    main_content = MAIN_PY.read_text(encoding="utf-8")
    assert "Favur 2048" in main_content, "Favur 2048 title missing in src/main.py"
    assert "700" in main_content and "800" in main_content, "700x800 dimensions missing in src/main.py"

    # Verify window creation flags=0 non-resizable per spec
    assert "set_mode" in main_content, "set_mode missing"
    assert "set_caption" in main_content, "set_caption missing"

    # Verify screenshot hooks exist
    assert "phase-4-merge.png" in main_content, "merge screenshot hook missing"
    assert "phase-4-toast.png" in main_content, "toast screenshot hook missing"
    assert "phase-4-gameover.png" in main_content, "gameover screenshot hook missing"
    assert "pygame.image.save" in main_content, "image.save missing"

    # Verify PNGs exist valid header dimensions (if captured)
    for png_path in [MERGE_PNG, TOAST_PNG, GAMEOVER_PNG]:
        assert png_path.exists(), f"{png_path} missing for visual launch verification"
        assert validate_png_header(png_path), f"{png_path} invalid header"
        assert validate_png_dimensions_ihdr(
            png_path, EXPECTED_WIDTH, EXPECTED_HEIGHT
        ), f"{png_path} dimensions not {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"

    # Verify manifest contains observation_id
    assert MANIFEST.exists(), "manifest missing for visual launch verification"
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    assert "observation_id" in manifest_text, "observation_id missing in manifest"
    assert re.search(r"obs_\d+", manifest_text), "obs_ pattern missing in manifest"


def test_ensure_visual_proof_dir_oserror_handling() -> None:
    """Robustness: OSError specific handling not bare except, ensure_visual_proof_dir returns False on OSError."""
    # Test OSError handling via mock
    with patch.object(Path, "mkdir", side_effect=OSError("mock disk full")):
        # Import after patch to test function behavior
        from src.main import ensure_visual_proof_dir

        result = ensure_visual_proof_dir()
        assert result is False, "ensure_visual_proof_dir should return False on OSError"

    # Verify no bare except: in src/main.py only specific exceptions
    main_content = MAIN_PY.read_text(encoding="utf-8")
    # Find bare except: pattern - except: with no exception type
    bare_except_pattern = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
    bare_matches = bare_except_pattern.findall(main_content)
    assert len(bare_matches) == 0, f"bare except: found {len(bare_matches)} times, must use specific except OSError etc"

    # Verify specific except patterns exist
    assert "except OSError" in main_content, "except OSError handling missing"
    assert "except (ValueError, TypeError, pygame.error)" in main_content or \
           "except (ValueError, TypeError" in main_content, \
        "specific except (ValueError, TypeError, pygame.error) missing"
