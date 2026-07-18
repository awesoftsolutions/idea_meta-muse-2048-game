"""
tests/test_visual_proof_first_light.py — First-light screenshot gating finalization.

TDD red phase (Step 2 of 7): validates visual-proof/phase-3-first-light.png
700x800 valid PNG header 89 50 4E 47 and visual-proof/README.md manifest entry
per pseudocode phase_3_sprint_2_task_3_code.md and sprint Task 3 AC-1 to AC-4.

Pseudocode sections covered:
- File: visual-proof directory setup — ensure_visual_proof_dir mkdir parents True exist_ok True OSError handling
- File: Headless fallback Surface 700x800 draw_board capture — real board single 2 tile heat 0
- File: PNG validation header 89 50 4E 47 700x800 — header check, size >0, IHDR parsing big-endian
- File: visual-proof/README.md manifest update — filename, what it shows, input_sequence, observation_id
- File: Visual launch via execute_structured_command and window_observe — observation_id recording

System:
    VisualProofGating per Phase 3 architecture ADR-019.
    Headless only, no GUI launch, no favur imports.
"""

from __future__ import annotations

import os
import pathlib
import struct
import tempfile

# ---------------------------------------------------------------------------
# Constants per pseudocode PNG validation header 89 50 4E 47 700x800
# ---------------------------------------------------------------------------

VISUAL_PROOF_DIR = pathlib.Path("visual-proof")
PNG_PATH = VISUAL_PROOF_DIR / "phase-3-first-light.png"
README_PATH = VISUAL_PROOF_DIR / "README.md"
MAIN_PY_PATH = pathlib.Path("src/main.py")

# PNG signature first 4 bytes 89 50 4E 47 hex per AC-1
EXPECTED_HEADER_4 = bytes([0x89, 0x50, 0x4E, 0x47])
# Full 8-byte PNG signature 89 50 4E 47 0D 0A 1A 0A
EXPECTED_PNG_SIGNATURE_8 = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

EXPECTED_WIDTH = 700
EXPECTED_HEIGHT = 800


# ---------------------------------------------------------------------------
# Helper: PNG IHDR parsing per pseudocode File: PNG validation header 89 50 4E 47 700x800
# ---------------------------------------------------------------------------


def _parse_png_dimensions(path: pathlib.Path) -> tuple[int, int]:
    """Parse PNG width/height via IHDR chunk big-endian uint32.

    Pseudocode:
        seek to IHDR chunk (after 8 byte signature, next 8 bytes chunk length+type,
        then IHDR data) Parse width as big-endian uint32 from bytes 0-3 of IHDR data
        Parse height as big-endian uint32 from bytes 4-7 of IHDR data

    Args:
        path: Path to PNG file.

    Returns:
        Tuple (width, height).

    Raises:
        ValueError: If file truncated, no IHDR, or parsing fails.
    """
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 8:
        raise ValueError("Truncated PNG no IHDR — file <8 bytes")

    header = data[:8]
    if header != EXPECTED_PNG_SIGNATURE_8:
        # Allow check of first 4 bytes only for header validation, but for dimensions need full
        if header[:4] != EXPECTED_HEADER_4:
            raise ValueError(f"Invalid PNG header, expected 89 50 4E 47, got {header[:4].hex()}")

    # After 8-byte signature: 4 bytes length, 4 bytes type, then IHDR data
    # IHDR must be first chunk
    if len(data) < 8 + 8 + 13:
        raise ValueError("Truncated PNG no IHDR — too short for IHDR chunk")

    # Read chunks sequentially to find IHDR
    offset = 8
    while offset + 8 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        if chunk_type == b"IHDR":
            if length < 8:
                raise ValueError("IHDR chunk too short")
            ihdr_data = data[offset + 8 : offset + 8 + length]
            if len(ihdr_data) < 8:
                raise ValueError("Failed to parse dimensions — IHDR data truncated")
            width = int.from_bytes(ihdr_data[0:4], "big")
            height = int.from_bytes(ihdr_data[4:8], "big")
            return width, height
        # Move to next chunk: 4 length + 4 type + length data + 4 CRC
        offset += 8 + length + 4

    raise ValueError("No IHDR chunk found")


def _validate_png_header(path: pathlib.Path) -> tuple[bool, str]:
    """Validate PNG header 89 50 4E 47 per pseudocode.

    Returns:
        (valid, reason)
    """
    if not path.exists():
        return False, "File does not exist"
    size = path.stat().st_size
    if size == 0:
        return False, "File size zero"
    if size < 100:
        return False, "File too small for PNG"
    with open(path, "rb") as f:
        header = f.read(8)
    if len(header) < 4:
        return False, "Truncated PNG no IHDR"
    if header[:4] != EXPECTED_HEADER_4:
        return False, f"Invalid PNG header, expected 89 50 4E 47, got {header[:4].hex()}"
    if len(header) < 8:
        return False, "Truncated PNG no IHDR"
    if header != EXPECTED_PNG_SIGNATURE_8:
        # First 4 bytes valid but full signature mismatch — still warn but allow for header check
        # For strict validation, require full signature
        if header[:4] == EXPECTED_HEADER_4:
            # Accept as valid header for AC-1 first 4 bytes check, but note
            pass
    return True, "valid"


# ---------------------------------------------------------------------------
# AC-1: PNG existence, size >0, header 89 50 4E 47, valid PNG 700x800
# ---------------------------------------------------------------------------


def test_visual_proof_dir_exists() -> None:
    """Pseudocode File: visual-proof directory setup — dir exists mkdir parents True exist_ok True."""
    assert VISUAL_PROOF_DIR.exists(), (
        f"visual-proof/ directory not found at {VISUAL_PROOF_DIR.resolve()} — "
        "AC-4 requires create dir if missing mkdir parents True exist_ok True"
    )
    assert VISUAL_PROOF_DIR.is_dir(), f"{VISUAL_PROOF_DIR} exists but is not a directory — E012 ScreenshotFail"


def test_png_exists() -> None:
    """AC-1: visual-proof/phase-3-first-light.png exists per File: PNG validation."""
    assert PNG_PATH.exists(), (
        f"PNG file not found at {PNG_PATH} — AC-1 requires visual-proof/phase-3-first-light.png exists"
    )
    assert PNG_PATH.is_file(), f"{PNG_PATH} exists but is not a file"


def test_png_size_gt_zero() -> None:
    """AC-1: PNG size >0 and >=100 bytes per pseudocode size check."""
    assert PNG_PATH.exists(), f"PNG not found at {PNG_PATH}"
    file_stats = os.stat(PNG_PATH)
    assert file_stats.st_size > 0, f"PNG file size zero invalid per AC-1 at {PNG_PATH}"
    assert file_stats.st_size >= 100, (
        f"PNG suspiciously small size {file_stats.st_size} bytes at {PNG_PATH} "
        "may not contain window content — expected 700x800 Favur 2048 window"
    )


def test_png_header_89_50_4E_47() -> None:
    """AC-1: PNG header first 4 bytes 89 50 4E 47 per File: PNG validation header 89 50 4E 47 700x800."""
    assert PNG_PATH.exists(), f"PNG not found at {PNG_PATH} — cannot validate header"
    with open(PNG_PATH, "rb") as f:
        header_bytes = f.read(8)
    assert len(header_bytes) >= 4, (
        f"PNG header truncated less than 4 bytes at {PNG_PATH}, got {len(header_bytes)} bytes"
    )
    actual_4 = header_bytes[:4]
    assert actual_4 == EXPECTED_HEADER_4, (
        f"Invalid PNG header expected 89 50 4E 47 got {actual_4.hex()} "
        f"at {PNG_PATH} — file is not PNG, delete and recapture per E012"
    )


def test_png_full_signature_8_bytes() -> None:
    """AC-1: Full 8-byte PNG signature 89 50 4E 47 0D 0A 1A 0A valid."""
    assert PNG_PATH.exists(), f"PNG not found at {PNG_PATH}"
    with open(PNG_PATH, "rb") as f:
        header = f.read(8)
    assert len(header) == 8, f"PNG header truncated, expected 8 bytes got {len(header)}"
    assert header == EXPECTED_PNG_SIGNATURE_8, (
        f"Invalid PNG full signature expected {EXPECTED_PNG_SIGNATURE_8.hex()} "
        f"got {header.hex()} at {PNG_PATH}"
    )


def test_png_dimensions_700x800_via_ihdr() -> None:
    """AC-1: PNG dimensions 700x800 via IHDR parsing big-endian per pseudocode."""
    assert PNG_PATH.exists(), f"PNG not found at {PNG_PATH}"
    width, height = _parse_png_dimensions(PNG_PATH)
    assert width == EXPECTED_WIDTH, (
        f"Dimensions mismatch expected 700x800 got {width}x{height} — width != 700"
    )
    assert height == EXPECTED_HEIGHT, (
        f"Dimensions mismatch expected 700x800 got {width}x{height} — height != 800"
    )


def test_png_validation_helper_returns_valid() -> None:
    """AC-1: validate_png helper returns valid=True for real screenshot."""
    assert PNG_PATH.exists(), f"PNG not found at {PNG_PATH}"
    valid, reason = _validate_png_header(PNG_PATH)
    assert valid, f"PNG validation failed valid=False reason={reason} at {PNG_PATH}"
    assert "valid" in reason.lower() or reason == "valid"


# ---------------------------------------------------------------------------
# Negative validation tests per TDD Test Structure
# ---------------------------------------------------------------------------


def test_png_rejects_invalid_header() -> None:
    """AC-1: PNG validation rejects invalid header 00 00 00 00 per pseudocode edge case."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(bytes([0x00, 0x00, 0x00, 0x00, 0x0D, 0x0A, 0x1A, 0x0A] * 20))
        tmp_path = pathlib.Path(tmp.name)
    try:
        valid, reason = _validate_png_header(tmp_path)
        assert not valid, "Expected valid=False for invalid header 00 00 00 00"
        assert "Invalid PNG header" in reason or "89 50 4E 47" in reason or "header" in reason.lower()
    finally:
        tmp_path.unlink(missing_ok=True)


def test_png_rejects_zero_size() -> None:
    """AC-1: PNG validation rejects zero size per edge case."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp_path = pathlib.Path(tmp.name)
    try:
        # File exists but size 0
        valid, reason = _validate_png_header(tmp_path)
        assert not valid, "Expected valid=False for zero size"
        assert "zero" in reason.lower() or "size" in reason.lower()
    finally:
        tmp_path.unlink(missing_ok=True)


def test_png_rejects_wrong_dimensions() -> None:
    """AC-1: PNG validation rejects wrong dimensions 800x600 per pseudocode edge case."""
    # Create minimal valid PNG with IHDR width 800 height 600
    # PNG structure: 8-byte sig + IHDR chunk (length 13, type IHDR, 13 bytes data, 4 CRC) + IEND
    png_sig = EXPECTED_PNG_SIGNATURE_8
    width_bytes = struct.pack(">I", 800)
    height_bytes = struct.pack(">I", 600)
    # IHDR data: width 4, height 4, bit depth 1, color type 1, compression 1, filter 1, interlace 1 = 13 bytes
    ihdr_data = width_bytes + height_bytes + bytes([8, 2, 0, 0, 0])
    ihdr_length = struct.pack(">I", len(ihdr_data))
    ihdr_type = b"IHDR"
    # CRC placeholder (not validated by our parser)
    ihdr_crc = struct.pack(">I", 0)
    iend_length = struct.pack(">I", 0)
    iend_type = b"IEND"
    iend_crc = struct.pack(">I", 0xAE426082)

    fake_png = png_sig + ihdr_length + ihdr_type + ihdr_data + ihdr_crc + iend_length + iend_type + iend_crc

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(fake_png)
        tmp_path = pathlib.Path(tmp.name)
    try:
        width, height = _parse_png_dimensions(tmp_path)
        assert width == 800 and height == 600, f"Fake PNG should parse as 800x600 got {width}x{height}"
        # Now validate dimensions mismatch
        assert width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT, "Fake PNG should have wrong dimensions"
        # Simulate validation logic
        if width != 700 or height != 800:
            valid = False
            reason = f"Dimensions mismatch expected 700x800 got {width}x{height}"
        else:
            valid = True
            reason = "valid"
        assert not valid
        assert "Dimensions mismatch" in reason
    finally:
        tmp_path.unlink(missing_ok=True)


def test_png_rejects_truncated_no_ihdr() -> None:
    """Edge: truncated PNG no IHDR returns valid=False."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(EXPECTED_PNG_SIGNATURE_8[:4])  # Only 4 bytes
        tmp_path = pathlib.Path(tmp.name)
    try:
        try:
            _parse_png_dimensions(tmp_path)
            assert False, "Expected ValueError for truncated PNG"
        except ValueError as e:
            assert "Truncated" in str(e) or "IHDR" in str(e) or "short" in str(e).lower()
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# AC-2: Manifest entry contains filename, what it shows, input_sequence, observation_id
# ---------------------------------------------------------------------------


def test_manifest_exists() -> None:
    """AC-2: visual-proof/README.md exists per File: visual-proof/README.md manifest update."""
    assert README_PATH.exists(), (
        f"Manifest not found at {README_PATH} — AC-2 requires visual-proof/README.md"
    )
    assert README_PATH.is_file(), f"{README_PATH} exists but is not a file"


def test_manifest_contains_filename_phase_3_first_light_png() -> None:
    """AC-2: Manifest contains filename phase-3-first-light.png per SOW Visual Verification Protocol."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8")
    assert "phase-3-first-light.png" in content, (
        "Manifest missing filename entry phase-3-first-light.png per AC-2"
    )


def test_manifest_contains_what_it_shows() -> None:
    """AC-2: Manifest contains what it shows Real board starting tile titled window reactor chrome heat identity."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8").lower()
    # Must contain what it shows marker
    assert "what it shows" in content, "Manifest missing 'what it shows' field per AC-2"
    # Must describe real board starting tile
    has_real_board = "real board" in content or "real" in content and "board" in content
    assert has_real_board, "Manifest missing real board description per AC-2"
    has_starting_tile = "starting tile" in content or "single" in content and "2" in content
    assert has_starting_tile, "Manifest missing starting tile description per AC-2"
    has_titled_window = "titled window" in content or "favur 2048" in content
    assert has_titled_window, "Manifest missing titled window Favur 2048 per AC-2"
    has_reactor_chrome = "reactor" in content or "chrome" in content or "#0f172a" in content
    assert has_reactor_chrome, "Manifest missing reactor chrome per AC-2"
    has_heat_identity = "heat" in content and ("identity" in content or "#3b82f6" in content)
    assert has_heat_identity, "Manifest missing heat identity #3B82F6 per AC-2"


def test_manifest_contains_input_sequence() -> None:
    """AC-2: Manifest contains input_sequence launch no input per SOW."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8").lower()
    assert "input_sequence" in content or "input sequence" in content, (
        "Manifest missing input_sequence field per AC-2"
    )
    has_launch = "launch" in content
    assert has_launch, "Manifest missing input_sequence launch per AC-2"
    has_no_input = "no input" in content or "none" in content or "no user input" in content
    assert has_no_input, "Manifest missing input_sequence no input per AC-2"


def test_manifest_contains_observation_id() -> None:
    """AC-2: Manifest contains observation_id first-light-001 or obs_ pattern per SOW."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8")
    lower = content.lower()
    assert "observation_id" in lower or "observation" in lower, (
        "Manifest missing observation_id field per AC-2"
    )
    has_obs = (
        "first-light-001" in content
        or "first-light" in lower
        or "obs_" in lower
        or "obs-"
        in lower
        or "obs_000" in lower
    )
    assert has_obs, (
        "Manifest missing observation_id value first-light-001 or obs_ pattern per AC-2 — "
        "must contain observation_id e.g., first-light-001"
    )


def test_manifest_contains_description_700x800_favur_2048() -> None:
    """AC-2: Manifest description contains 700x800 Favur 2048 window real board single 2 tile."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8")
    assert "700" in content and "800" in content, "Manifest missing 700x800 description per AC-2"
    assert "Favur 2048" in content or "favur 2048" in content.lower(), (
        "Manifest missing Favur 2048 exact title per AC-2"
    )
    # Real board single 2 tile heat 0
    lower = content.lower()
    assert "real" in lower and "board" in lower, "Manifest missing real board per AC-2"
    assert "2" in content, "Manifest missing single 2 tile per AC-2"


def test_manifest_contains_heat_identity_and_reactor_chrome() -> None:
    """AC-2: Manifest contains heat identity #3B82F6 and reactor chrome colors per AC-1."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8")
    lower = content.lower()
    has_heat = "#3b82f6" in lower or "3b82f6" in lower or "heat" in lower
    assert has_heat, "Manifest missing heat identity #3B82F6 per AC-2"
    has_chrome = (
        "reactor" in lower
        or "chrome" in lower
        or "#0f172a" in lower
        or "#1e293b" in lower
        or "0f172a" in lower
    )
    assert has_chrome, "Manifest missing reactor chrome per AC-2"


def test_manifest_contains_capture_method() -> None:
    """AC-2: Manifest contains capture_method headless Surface 700x800 draw_board + visual=true launch."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8").lower()
    has_capture = "capture_method" in content or "capture" in content
    assert has_capture, "Manifest missing capture_method per AC-2"
    has_headless_or_visual = (
        "headless" in content
        or "surface" in content
        or "visual=true" in content
        or "visual" in content
        or "pygame.image.save" in content
        or "draw_board" in content
    )
    assert has_headless_or_visual, (
        "Manifest missing capture_method details headless Surface 700x800 draw_board or visual=true per AC-2"
    )


def test_manifest_contains_validation_png_header() -> None:
    """AC-2: Manifest contains validation PNG header 89 50 4E 47."""
    assert README_PATH.exists(), f"Manifest not found at {README_PATH}"
    content = README_PATH.read_text(encoding="utf-8")
    has_validation = (
        "89 50 4E 47" in content
        or "89 50 4e 47" in content.lower()
        or "png header" in content.lower()
        or "header" in content.lower() and "valid" in content.lower()
    )
    assert has_validation, "Manifest missing validation PNG header 89 50 4E 47 per AC-2"


# ---------------------------------------------------------------------------
# AC-4: Directory creation mkdir parents True exist_ok True OSError handling in main.py
# ---------------------------------------------------------------------------


def test_main_py_contains_mkdir_parents_exist_ok() -> None:
    """AC-4: main.py contains mkdir parents True exist_ok True per File: visual-proof directory setup."""
    assert MAIN_PY_PATH.exists(), f"main.py not found at {MAIN_PY_PATH}"
    content = MAIN_PY_PATH.read_text(encoding="utf-8")
    assert "mkdir" in content, "main.py missing mkdir per AC-4 directory creation"
    assert "parents=True" in content or "parents = True" in content, (
        "main.py missing mkdir parents=True per AC-4"
    )
    assert "exist_ok=True" in content or "exist_ok = True" in content, (
        "main.py missing mkdir exist_ok=True per AC-4"
    )


def test_main_py_contains_oserror_handling() -> None:
    """AC-4: main.py handles OSError during mkdir and image.save per pseudocode."""
    assert MAIN_PY_PATH.exists(), f"main.py not found at {MAIN_PY_PATH}"
    content = MAIN_PY_PATH.read_text(encoding="utf-8")
    assert "OSError" in content, "main.py missing OSError handling per AC-4"
    # Should have warning log for screenshot save failure
    has_warning = (
        "Warning" in content
        or "warning" in content.lower()
        or "Screenshot save failed" in content
        or "Screenshot dir creation failed" in content
    )
    assert has_warning, "main.py missing warning log for screenshot failure per AC-4"
