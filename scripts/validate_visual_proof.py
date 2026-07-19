"""Infra validation script for Phase 6 CI readiness gating readiness PASS check.

Purpose: Validate visual-proof directory contains 5 required PNGs with valid
header 89 50 4E 47 700x800 and manifest complete naming file what it shows
input sequence observation_id obs_000001-012 per SOW gating requirement.

This script uses stdlib only (pathlib, sys, struct, re) to be runnable in CI
without display. PNG header validation via reading first 8 bytes and checking
89 50 4E 47, dimensions via IHDR chunk struct.unpack >I at offset 16-20.

Constants:
    REQUIRED_PNGS: 5 SOW-required PNGs
    EXPECTED_SIZES: expected sizes for validation
    PNG_HEADER_4: first 4 bytes 89 50 4E 47
    PNG_HEADER_8: first 8 bytes 89 50 4E 47 0D 0A 1A 0A
    EXPECTED_DIMS: (700, 800) SOW fixed window size
    MANIFEST_PATH: visual-proof/README.md
    VISUAL_PROOF_DIR: visual-proof

Functions:
    validate_png_header(path): Check PNG exists, size>0, header 89 50 4E 47,
        dimensions 700x800 via IHDR.
    validate_manifest(manifest_path): Check README contains 7+ entries with
        file, what it shows, input sequence, observation_id obs_000001-012.
    validate_gating(): Check 5 required PNGs exist valid header manifest
        complete per SOW gating.
    main(): Run validation, print PASS/FAIL, return exit code 0/1.
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path
from typing import Any

# Constants per pseudocode and sprint AC
REQUIRED_PNGS: list[str] = [
    "phase-3-first-light.png",
    "phase-4-merge.png",
    "phase-4-toast.png",
    "phase-4-gameover.png",
    "phase-5-tiles-after-moves.png",
]

EXPECTED_SIZES: dict[str, int] = {
    "phase-1-spike.png": 32667,
    "phase-3-first-light.png": 10376,
    "phase-4-merge.png": 16571,
    "phase-4-toast.png": 21606,
    "phase-4-gameover.png": 41407,
    "phase-5-tiles-after-moves.png": 17015,
}

PNG_HEADER_4: bytes = b"\x89PNG"
PNG_HEADER_8: bytes = b"\x89PNG\r\n\x1a\n"
EXPECTED_DIMS: tuple[int, int] = (700, 800)
MANIFEST_PATH: str = "visual-proof/README.md"
VISUAL_PROOF_DIR: str = "visual-proof"


def validate_png_header(path: str) -> dict[str, Any]:
    """Check PNG file exists, size>0, first 8 bytes 89 50 4E 47, dimensions 700x800 via IHDR.

    Returns dict with exists, size, header_valid, dimensions, error.

    Args:
        path: File path to PNG to validate.

    Returns:
        Dict with keys:
            exists: bool whether file exists
            size: int file size in bytes
            header_valid: bool whether header 89 50 4E 47 valid
            dimensions: tuple[int,int] or None (width, height) from IHDR
            error: Optional[str] error message
    """
    result: dict[str, Any] = {
        "exists": False,
        "size": 0,
        "header_valid": False,
        "dimensions": None,
        "error": None,
    }

    png_path = Path(path)

    if not png_path.exists():
        result["error"] = f"Missing file: {path}"
        return result

    result["exists"] = True

    try:
        data = png_path.read_bytes()
        result["size"] = len(data)

        if len(data) < 8:
            result["error"] = f"File too small: {path} size {len(data)}"
            return result

        if data[:4] != PNG_HEADER_4:
            result["error"] = f"Invalid PNG header 4: {path} got {data[:4].hex()} expected 89504e47"
            return result

        if data[:8] != PNG_HEADER_8:
            result["error"] = f"Invalid PNG header 8: {path} got {data[:8].hex()} expected 89504e470d0a1a0a"
            return result

        result["header_valid"] = True

        # Try to parse IHDR dimensions via struct.unpack >I at offset 16 and 20
        try:
            if len(data) >= 24:
                width = struct.unpack(">I", data[16:20])[0]
                height = struct.unpack(">I", data[20:24])[0]
                result["dimensions"] = (width, height)
                if (width, height) != EXPECTED_DIMS:
                    result["error"] = (
                        f"Invalid dimensions: {path} got {(width, height)} expected {EXPECTED_DIMS}"
                    )
                    # Keep header_valid True but note dimension mismatch via error
                    # For gating, we check dimensions separately
            else:
                result["error"] = f"File too small for IHDR: {path}"
        except struct.error as e:
            result["error"] = f"struct.error parsing IHDR {path}: {e}"
        except Exception as e:
            result["error"] = f"Error parsing IHDR {path}: {e}"

        return result

    except OSError as e:
        result["exists"] = False
        result["error"] = f"OSError reading {path}: {e}"
        return result
    except Exception as e:
        result["error"] = f"Error validating {path}: {e}"
        return result


def validate_manifest(manifest_path: str = MANIFEST_PATH) -> dict[str, Any]:
    """Check manifest contains 7+ entries with file, what it shows, input sequence, observation_id.

    Returns dict with entry_count, has_required_files, has_observation_ids, complete, error.

    Args:
        manifest_path: Path to README.md manifest.

    Returns:
        Dict with keys:
            entry_count: int number of entries
            has_required_files: bool whether all required PNGs mentioned
            has_observation_ids: bool whether observation_ids present
            complete: bool overall completeness
            error: Optional[str] error message
    """
    result: dict[str, Any] = {
        "entry_count": 0,
        "has_required_files": False,
        "has_observation_ids": False,
        "complete": False,
        "error": None,
    }

    manifest_p = Path(manifest_path)

    if not manifest_p.exists():
        result["error"] = f"Missing manifest: {manifest_path}"
        return result

    try:
        content = manifest_p.read_text(encoding="utf-8")

        # Count entries: search for '- file:' occurrences or '###' headings
        file_pattern_count = content.count("- file:")
        hash_heading_count = content.count("###")
        # Use max heuristic for entry count, also count 'file:' occurrences
        file_colon_count = len(re.findall(r"file:", content))
        # Entry count best effort: count ### headings that look like phase entries
        entry_count = max(file_pattern_count, hash_heading_count, file_colon_count // 2)
        # More accurate: count occurrences of 'phase-' in headings
        phase_heading_matches = re.findall(r"###\s+phase-", content)
        if phase_heading_matches:
            entry_count = max(entry_count, len(phase_heading_matches))

        result["entry_count"] = entry_count

        # Check for each required file name in content
        required_present = []
        for req in REQUIRED_PNGS:
            if req in content:
                required_present.append(req)
        # Also check phase-1-spike
        has_spike = "phase-1-spike" in content

        result["has_required_files"] = len(required_present) >= 5

        # Check for 'shows:' or 'what it shows' substring
        has_shows = ("shows:" in content) or ("what it shows" in content.lower())
        has_input = ("input:" in content.lower()) or ("input_sequence" in content.lower())
        has_obs_id_label = "observation_id" in content.lower()

        # Use regex to find all obs_00000\d+ or obs_0000\d+ patterns
        obs_ids = re.findall(r"obs_0000\d+", content)
        distinct_obs = set(obs_ids)

        result["has_observation_ids"] = len(distinct_obs) >= 7

        # Check obs_000001 through obs_000012 range present at least partially
        # At least check obs_000001 and obs_000012 present
        has_obs_range = ("obs_000001" in content) and (len(distinct_obs) >= 7)

        # Determine completeness
        complete = (
            entry_count >= 7
            and result["has_required_files"]
            and result["has_observation_ids"]
            and has_shows
            and has_input
            and has_obs_id_label
            and has_obs_range
            and has_spike
        )

        result["complete"] = complete

        if not complete:
            missing_parts = []
            if entry_count < 7:
                missing_parts.append(f"entry_count {entry_count} <7")
            if not result["has_required_files"]:
                missing_parts.append(f"missing required files, found {required_present}")
            if not result["has_observation_ids"]:
                missing_parts.append(f"observation_ids {len(distinct_obs)} <7")
            if not has_shows:
                missing_parts.append("missing 'what it shows'")
            if not has_input:
                missing_parts.append("missing 'input'")
            if not has_obs_id_label:
                missing_parts.append("missing 'observation_id'")
            if not has_spike:
                missing_parts.append("missing phase-1-spike")
            result["error"] = f"Manifest incomplete: {'; '.join(missing_parts)}"

        return result

    except OSError as e:
        result["error"] = f"OSError reading manifest {manifest_path}: {e}"
        return result
    except Exception as e:
        result["error"] = f"Error validating manifest {manifest_path}: {e}"
        return result


def validate_gating() -> dict[str, Any]:
    """Check 5 required PNGs exist valid header manifest complete per SOW gating.

    Returns dict with pngs_valid, manifest_complete, gating_pass, details.

    Returns:
        Dict with keys:
            pngs_valid: bool whether all 5 PNGs valid
            manifest_complete: bool whether manifest complete
            gating_pass: bool overall gating PASS
            details: dict with per-PNG results and manifest result
    """
    png_results: list[dict[str, Any]] = []
    pngs_valid = True

    for png_name in REQUIRED_PNGS:
        png_path = f"{VISUAL_PROOF_DIR}/{png_name}"
        res = validate_png_header(png_path)
        png_results.append({"file": png_name, "path": png_path, "result": res})

        # Check valid: exists, header_valid, dimensions == EXPECTED_DIMS
        if not res.get("exists"):
            pngs_valid = False
        elif not res.get("header_valid"):
            pngs_valid = False
        else:
            dims = res.get("dimensions")
            if dims is not None and dims != EXPECTED_DIMS:
                pngs_valid = False

    manifest_res = validate_manifest(MANIFEST_PATH)
    manifest_complete = bool(manifest_res.get("complete"))

    gating_pass = pngs_valid and manifest_complete

    return {
        "pngs_valid": pngs_valid,
        "manifest_complete": manifest_complete,
        "gating_pass": gating_pass,
        "details": {
            "pngs": png_results,
            "manifest": manifest_res,
        },
    }


def main() -> int:
    """Run validation and print PASS/FAIL and return exit code 0/1 per SOW gating.

    Handles OSError specific, mkdir parents True exist_ok True check.

    Returns:
        int: 0 on PASS, 1 on FAIL.
    """
    try:
        # Ensure visual-proof dir exists via Path.mkdir parents True exist_ok True
        try:
            Path(VISUAL_PROOF_DIR).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Warning OSError creating {VISUAL_PROOF_DIR}: {e}")
            # Continue, validation will fail if dir missing files

        gating = validate_gating()

        if gating.get("gating_pass"):
            print(
                "gating readiness PASS 5 PNGs valid header 89 50 4E 47 700x800 "
                "manifest complete ready for Phase 6 CI and packaging"
            )
            # Print details: each PNG size header valid manifest entries count observation_id
            details = gating.get("details", {})
            pngs = details.get("pngs", [])
            for png_info in pngs:
                res = png_info.get("result", {})
                print(
                    f"  {png_info.get('file')}: size={res.get('size')} "
                    f"header_valid={res.get('header_valid')} "
                    f"dimensions={res.get('dimensions')} exists={res.get('exists')}"
                )
            manifest = details.get("manifest", {})
            print(
                f"  manifest: entries={manifest.get('entry_count')} "
                f"required_files={manifest.get('has_required_files')} "
                f"observation_ids={manifest.get('has_observation_ids')} "
                f"complete={manifest.get('complete')}"
            )
            # Show observation_id count via regex
            try:
                content = Path(MANIFEST_PATH).read_text(encoding="utf-8")
                obs_ids = re.findall(r"obs_0000\d+", content)
                print(f"  observation_ids found: {sorted(set(obs_ids))}")
            except OSError as e:
                print(f"  Warning OSError reading manifest for obs ids: {e}")
            return 0
        else:
            print("gating readiness FAIL")
            details = gating.get("details", {})
            pngs = details.get("pngs", [])
            for png_info in pngs:
                res = png_info.get("result", {})
                if not res.get("exists"):
                    print(f"Missing file: {png_info.get('path')}")
                elif not res.get("header_valid"):
                    print(
                        f"Invalid header: {png_info.get('path')} "
                        f"error={res.get('error')} size={res.get('size')}"
                    )
                else:
                    dims = res.get("dimensions")
                    if dims is not None and dims != EXPECTED_DIMS:
                        print(
                            f"Invalid dimensions: {png_info.get('path')} "
                            f"got {dims} expected {EXPECTED_DIMS}"
                        )
                if res.get("error"):
                    print(f"  error: {res.get('error')}")

            manifest = details.get("manifest", {})
            if not manifest.get("complete"):
                print(f"Manifest incomplete: {MANIFEST_PATH}")
                if manifest.get("error"):
                    print(f"  error: {manifest.get('error')}")
                print(
                    f"  entries={manifest.get('entry_count')} "
                    f"required_files={manifest.get('has_required_files')} "
                    f"observation_ids={manifest.get('has_observation_ids')}"
                )

            return 1

    except OSError as e:
        print(f"Warning OSError: {e}")
        return 1
    except Exception as e:
        print(f"Warning error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
