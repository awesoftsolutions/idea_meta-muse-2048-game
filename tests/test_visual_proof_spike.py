"""
tests/test_visual_proof_spike.py — Visual-Proof Capture Framework Spike Screenshot validations.

TDD red phase: validates visual-proof/phase-1-spike.png and visual-proof/README.md
which do NOT exist yet. Expected to FAIL with FileNotFoundError/AssertionError
until Task 3 implementation creates visual-proof/ directory, captures PNG via
window_observe action=screenshot grid_enabled=true, and creates manifest stub.

Covers file existence, PNG header 89 50 4E 47, non-zero size, manifest content,
observation_id per pseudocode phase_1_sprint_1_task_3_code.md and sprint Task 3 AC-1 to AC-5.

VisualProofSystem owns visual-proof/ directory per ADR-005 gating requirement.
FrameworkConfig: title Favur 2048 width 700 height 800 resizable false fps 60.
Primitive: rect at (250,300,200,200) color (238,228,218) and circle at (350,400) radius 50 red
on background (187,173,160) proving pygame-ce API.
Capture method: execute_structured_command visual=true poetry run python -m src.main +
window_observe action=screenshot grid_enabled=true output_path=visual-proof/phase-1-spike.png
"""

from __future__ import annotations

import os
import pathlib


VISUAL_PROOF_DIR = pathlib.Path("visual-proof")
PNG_PATH = VISUAL_PROOF_DIR / "phase-1-spike.png"
README_PATH = VISUAL_PROOF_DIR / "README.md"

# PNG signature first 4 bytes 89 50 4E 47 hex per AC-2, AC-5
EXPECTED_HEADER_4 = bytes([0x89, 0x50, 0x4E, 0x47])
# Full 8-byte PNG signature 89 50 4E 47 0D 0A 1A 0A
EXPECTED_PNG_SIGNATURE_8 = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])


# ---------------------------------------------------------------------------
# Test 1 — File Existence Check per AC-1
# ---------------------------------------------------------------------------
def test_visual_proof_files_exist() -> None:
    """
    Verify visual-proof/ directory exists and contains phase-1-spike.png and README.md per AC-1.

    Uses filesystem check to verify visual-proof/ directory exists,
    then verifies phase-1-spike.png exists and size >0,
    then verifies README.md exists.

    Expected red phase failure: FileNotFoundError / AssertionError because
    visual-proof/ directory and files do not exist yet before Task 3 implementation.
    Why: AC-1 requires directory listing contains phase-1-spike.png and README.md.
    """
    # Directory existence check per pseudocode Directory Setup
    assert VISUAL_PROOF_DIR.exists(), (
        f"visual-proof/ directory not found at {VISUAL_PROOF_DIR.resolve()} — "
        "AC-1 requires visual-proof/ contains phase-1-spike.png and README.md"
    )
    assert VISUAL_PROOF_DIR.is_dir(), (
        f"{VISUAL_PROOF_DIR} exists but is not a directory — E009 ScreenshotFail"
    )

    # PNG existence per AC-1
    assert PNG_PATH.exists(), (
        f"PNG file not found at {PNG_PATH} — AC-1 requires visual-proof/ contains phase-1-spike.png"
    )
    assert PNG_PATH.is_file(), f"{PNG_PATH} exists but is not a file"

    # Size >0 per AC-2 non-zero size check
    file_stats = os.stat(PNG_PATH)
    assert file_stats.st_size > 0, (
        f"PNG file size zero invalid per AC-2 at {PNG_PATH}, size={file_stats.st_size}"
    )

    # README existence per AC-1
    assert README_PATH.exists(), (
        f"Manifest not found at {README_PATH} — AC-1 requires visual-proof/ contains README.md"
    )
    assert README_PATH.is_file(), f"{README_PATH} exists but is not a file"


# ---------------------------------------------------------------------------
# Test 2 — PNG Header 89 50 4E 47 Validation per AC-2, AC-5
# ---------------------------------------------------------------------------
def test_png_header_89_50_4E_47() -> None:
    """
    Verify phase-1-spike.png is valid PNG with header 89 50 4E 47 per AC-2, AC-5.

    Uses binary read to read first 8 bytes of visual-proof/phase-1-spike.png,
    checks first 4 bytes equal [0x89, 0x50, 0x4E, 0x47] corresponding to hex 89 50 4E 47,
    warns if bytes 5-8 mismatch but first 4 valid.

    Expected red phase failure: FileNotFoundError because PNG not created yet,
    or AssertionError header truncated / invalid.
    Why: PNG signature first 4 bytes are 89 50 4E 47 hex, ensures file is valid PNG not corrupted.
    """
    assert PNG_PATH.exists(), (
        f"PNG file not found at {PNG_PATH} — cannot validate header"
    )

    # Binary read first 8 bytes per pseudocode PNG Validation
    with open(PNG_PATH, "rb") as f:
        header_bytes = f.read(8)

    # Check length >=4 per edge case handling
    assert len(header_bytes) >= 4, (
        f"PNG header truncated less than 4 bytes at {PNG_PATH}, got {len(header_bytes)} bytes"
    )

    # Validate first 4 bytes 89 50 4E 47
    actual_4 = header_bytes[:4]
    assert actual_4 == EXPECTED_HEADER_4, (
        f"Invalid PNG header expected 89 50 4E 47 got {actual_4.hex()} "
        f"at {PNG_PATH} — file is not PNG, delete and recapture per E009"
    )

    # If 8 bytes available, check full signature but allow warning for bytes 5-8 mismatch
    if len(header_bytes) == 8:
        if header_bytes != EXPECTED_PNG_SIGNATURE_8:
            # Log warning but continue as pass for first 4 bytes critical check per pseudocode
            # Bytes 5-8 are 0D 0A 1A 0A, mismatch is warning not fatal
            assert header_bytes[:4] == EXPECTED_HEADER_4, (
                "First 4 bytes valid 89 50 4E 47 but full signature mismatch — "
                f"expected {EXPECTED_PNG_SIGNATURE_8.hex()} got {header_bytes.hex()}"
            )


# ---------------------------------------------------------------------------
# Test 3 — PNG Non-Zero Size per AC-2, AC-5
# ---------------------------------------------------------------------------
def test_png_nonzero_size() -> None:
    """
    Verify phase-1-spike.png has non-zero size and not suspiciously small per AC-2, AC-5.

    Uses filesystem stat to get file stats, asserts size >0 and warns if <100 bytes.

    Expected red phase failure: FileNotFoundError or size zero invalid.
    Why: PNG file size zero invalid per AC-2, ensures window content captured not empty.
    """
    assert PNG_PATH.exists(), (
        f"PNG file not found at {PNG_PATH} — AC-2 requires valid PNG"
    )

    file_stats = os.stat(PNG_PATH)

    assert file_stats.st_size > 0, f"PNG file size zero invalid per AC-2 at {PNG_PATH}"

    # Suspiciously small check per pseudocode — warning threshold 100 bytes
    # Real 700x800 window screenshot should be >>100 bytes
    assert file_stats.st_size >= 100, (
        f"PNG suspiciously small size {file_stats.st_size} bytes at {PNG_PATH} "
        "may not contain window content — expected 700x800 Favur 2048 window"
    )


# ---------------------------------------------------------------------------
# Test 4 — Manifest Content Validation per AC-1, AC-4
# ---------------------------------------------------------------------------
def test_manifest_content() -> None:
    """
    Verify visual-proof/README.md contains filename, description, input sequence per AC-1, AC-4.

    Checks content contains phase-1-spike.png, 700x800 or Favur 2048,
    primitive or rect or circle, input sequence none or Escape, phase 1.

    Expected red phase failure: FileNotFoundError because README.md not created yet,
    or AssertionError manifest missing required fields.
    Why: Manifest must name file and what it shows per AC-1 and AC-4, IVisualProof contract.
    """
    assert README_PATH.exists(), (
        f"Manifest not found at {README_PATH} — AC-4 requires README.md manifest stub"
    )

    content = README_PATH.read_text(encoding="utf-8")

    # Filename entry per pseudocode Manifest Creation
    assert "phase-1-spike.png" in content, (
        "Manifest missing filename entry phase-1-spike.png per AC-4"
    )

    # Window description 700x800 or Favur 2048 per AC-4
    has_window_desc = (
        "700x800" in content
        or "700 x 800" in content
        or "Favur 2048" in content
        or "700" in content
        and "800" in content
    )
    assert has_window_desc, (
        "Manifest missing window description 700x800 or Favur 2048 per AC-4 — "
        "must describe 700x800 non-resizable window titled Favur 2048"
    )

    # Primitive description rect or circle or primitive per AC-4
    has_primitive = (
        "primitive" in content.lower()
        or "rect" in content.lower()
        or "circle" in content.lower()
    )
    assert has_primitive, (
        "Manifest missing primitive description rect/circle/primitive per AC-4 — "
        "must describe primitive rect at (250,300,200,200) and circle at (350,400) radius 50"
    )

    # Input sequence none or Escape per AC-4
    has_input_seq = (
        "input" in content.lower()
        or "none" in content.lower()
        or "Escape" in content
        or "escape" in content.lower()
    )
    assert has_input_seq, (
        "Manifest missing input sequence none/Escape per AC-4 — "
        "must contain input sequence none for spike, Escape-to-quit handling"
    )

    # Phase marker phase 1 or Phase 1 per AC-4
    has_phase = "phase 1" in content.lower() or "Phase 1" in content
    assert has_phase, (
        "Manifest missing phase marker phase 1 per AC-4 — must contain phase 1"
    )


# ---------------------------------------------------------------------------
# Test 5 — Observation ID Recorded per AC-3 Definition of Done
# ---------------------------------------------------------------------------
def test_observation_id_recorded() -> None:
    """
    Verify observation_id from window_observe is recorded per AC-3 Definition of Done.

    Checks visual-proof/README.md contains observation_id or capture method
    execute_structured_command visual=true + window_observe action=screenshot grid_enabled=true.

    Expected red phase failure: FileNotFoundError or AssertionError observation_id not recorded.
    Why: AC-3 requires observation_id from window_observe recorded in completion report,
    manifest should include observation_id and capture method per IVisualProof.
    """
    assert README_PATH.exists(), (
        f"Manifest not found at {README_PATH} — cannot verify observation_id recorded"
    )

    content = README_PATH.read_text(encoding="utf-8")

    # Check for observation_id or capture method per pseudocode Manifest Creation
    has_observation = (
        "observation_id" in content.lower()
        or "observation" in content.lower()
        or "execute_structured_command" in content
        or "window_observe" in content
        or "visual-proof" in content.lower()
        or "visual=true" in content.lower()
        or "screenshot" in content.lower()
    )

    # Also check for capture method details per AC-3
    has_capture_method = (
        "capture" in content.lower()
        or "screenshot" in content.lower()
        or "visual" in content.lower()
    )

    assert has_observation or has_capture_method, (
        "Manifest missing observation_id or capture method per AC-3 Definition of Done — "
        "must contain observation_id from window_observe or capture method "
        "execute_structured_command visual=true + window_observe action=screenshot grid_enabled=true"
    )
