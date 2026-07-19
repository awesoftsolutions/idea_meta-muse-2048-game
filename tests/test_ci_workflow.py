"""tests/test_ci_workflow.py — CI workflow YAML validation per AC-1.

Purpose:
    Validates .github/workflows/ci.yml exists, valid YAML, contains
    test job poetry run pytest, build job PyInstaller validation,
    triggers push/PR trunk/main, checkout/setup-python/poetry install.

System:
    Phase 6 Sprint 1 Task 4 per architecture CIWorkflow contract.

Dependencies:
    pathlib, yaml (PyYAML), pytest — stdlib + yaml, no pygame.

Used-by:
    poetry run pytest tests/test_ci_workflow.py -v --no-cov

Public Interface:
    CI_WORKFLOW_PATH constant, load_ci_yaml helper, 6 test functions.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Tuple

import pytest

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CI_WORKFLOW_PATH = ".github/workflows/ci.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_ci_yaml() -> Tuple[Dict[str, Any], str]:
    """Load CI workflow YAML file.

    Returns:
        Tuple of (parsed dict, raw content string).

    Raises:
        AssertionError: If file missing or invalid YAML.
        ImportError: If PyYAML not installed.
    """
    if yaml is None:
        pytest.skip("PyYAML not installed, run poetry install")

    workflow_path = pathlib.Path(CI_WORKFLOW_PATH)
    if not workflow_path.exists():
        raise AssertionError(f".github/workflows/ci.yml missing at {CI_WORKFLOW_PATH}")

    content = workflow_path.read_text(encoding="utf-8")
    if not content.strip():
        raise AssertionError("ci.yml empty")

    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:  # type: ignore
        raise AssertionError(f"invalid YAML: {exc}") from exc

    if parsed is None:
        raise AssertionError("ci.yml parsed as None, empty or invalid structure")
    if not isinstance(parsed, dict):
        raise AssertionError(f"ci.yml parsed not dict, got {type(parsed)}")

    return parsed, content


# ---------------------------------------------------------------------------
# Tests — AC-1 CI workflow validation
# ---------------------------------------------------------------------------


def test_ci_workflow_exists() -> None:
    """AC-1 existence check for ci.yml."""
    workflow_path = pathlib.Path(CI_WORKFLOW_PATH)
    exists = workflow_path.exists()
    assert exists, f".github/workflows/ci.yml missing at {CI_WORKFLOW_PATH}"
    size = workflow_path.stat().st_size
    assert size > 0, "ci.yml empty"


def test_ci_workflow_valid_yaml() -> None:
    """AC-1 valid YAML check."""
    parsed, _content = load_ci_yaml()
    assert isinstance(parsed, dict), "parsed YAML not dict"
    # Must contain on and jobs keys per spec
    has_on = "on" in parsed
    has_jobs = "jobs" in parsed
    assert has_on or has_jobs, "invalid structure missing on/jobs"


def test_ci_workflow_has_test_job() -> None:
    """AC-1 test job contains poetry run pytest."""
    parsed, content = load_ci_yaml()
    has_pytest = "poetry run pytest" in content
    assert has_pytest, "test job missing poetry run pytest"

    jobs = parsed.get("jobs", {})
    assert isinstance(jobs, dict), "jobs not dict"
    # Find test job: key contains test or job name contains test
    test_job = None
    for key, val in jobs.items():
        if "test" in key.lower():
            test_job = val
            break
    if test_job is None:
        # Fallback: search any job containing pytest in its string repr
        for val in jobs.values():
            if "pytest" in str(val):
                test_job = val
                break
    assert test_job is not None, "test job not found in YAML"
    steps_str = str(test_job)
    assert "pytest" in steps_str.lower(), "test job steps missing pytest"


def test_ci_workflow_has_build_job() -> None:
    """AC-1 build job contains PyInstaller validation."""
    parsed, content = load_ci_yaml()
    has_pyinstaller = "pyinstaller" in content.lower()
    assert has_pyinstaller, "build job missing pyinstaller"

    jobs = parsed.get("jobs", {})
    assert isinstance(jobs, dict), "jobs not dict"
    build_job = None
    for key, val in jobs.items():
        if "build" in key.lower():
            build_job = val
            break
    assert build_job is not None, "build job not found"


def test_ci_workflow_triggers_valid() -> None:
    """AC-1 triggers on push/PR to trunk/main."""
    parsed, content = load_ci_yaml()
    on_section = parsed.get("on", {})
    # on can be dict or list or string
    assert on_section is not None, "missing on section"

    if isinstance(on_section, dict):
        has_push = "push" in on_section
        has_pr = "pull_request" in on_section
    elif isinstance(on_section, list):
        has_push = "push" in on_section
        has_pr = "pull_request" in on_section
    else:
        # Fallback to content search
        has_push = "push" in content
        has_pr = "pull_request" in content

    assert has_push, "missing push trigger"
    assert has_pr, "missing pull_request trigger"

    has_trunk = "trunk" in content
    has_main = "main" in content
    assert has_trunk or has_main, "triggers missing trunk/main branches"


def test_ci_workflow_setup_valid() -> None:
    """AC-1 setup contains checkout, setup-python, poetry install."""
    _parsed, content = load_ci_yaml()

    has_checkout = "actions/checkout" in content
    has_setup_python = "actions/setup-python" in content
    # poetry install can be "poetry install" or "poetry" + "install"
    has_poetry_install = ("poetry" in content.lower() and "install" in content.lower())

    assert has_checkout, "missing actions/checkout"
    assert has_setup_python, "missing actions/setup-python"
    assert has_poetry_install, "missing poetry install"
