"""E2E doctor version-contiguity gap test.

Per SPECIFICATION/scenarios.md: a seeded project whose `history/` carries `v001/` and
`v003/` with no `v002/` trips the `doctor-version-contiguity` static
check; the wrapper exits non-zero and the fail Finding names the first
missing version (`v002`).

This is the integration-tier (`tests.e2e.*`) test the scenarios.md
heading-coverage entry points at: it drives the real `bin/doctor_static.py`
wrapper end-to-end against a real on-disk history gap, which the unit
test `tests/livespec/doctor/static/test_version_contiguity.py` cannot
exercise (it calls the check function in isolation).
"""

from __future__ import annotations

import json
import shutil
import subprocess  # documented integration-test usage
from pathlib import Path

import harness
import pytest

__all__: list[str] = []


def _git(*, cwd: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
    )


@pytest.mark.e2e_golden
def test_doctor_version_contiguity_gap_fails(*, tmp_path: Path) -> None:
    """Seed → inject a v001/v003 history gap → doctor fails naming v002.

    The seed scaffolds `history/v001/`; copying that snapshot to
    `history/v003/` (skipping `v002/`) leaves a structurally valid
    pair of version directories whose ONLY anomaly is the numbering
    gap, isolating the `doctor-version-contiguity` fail.
    """
    _git(cwd=tmp_path, args=["init"])
    _git(cwd=tmp_path, args=["config", "user.email", "e2e-test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "E2E Test"])
    harness.seed_required_workflow_files(project_root=tmp_path)

    seed_result = harness.seed(
        project_root=tmp_path,
        intent="Doctor version-contiguity gap test project",
    )
    assert seed_result.returncode == 0, f"seed failed: {seed_result.stderr!r}"

    history_path = tmp_path / "SPECIFICATION" / "history"
    v001_path = history_path / "v001"
    v003_path = history_path / "v003"
    assert v001_path.is_dir(), "seed should scaffold history/v001/"
    shutil.copytree(v001_path, v003_path)

    _git(cwd=tmp_path, args=["add", "-A"])
    _git(cwd=tmp_path, args=["commit", "-m", "seed with v001/v003 history gap"])

    doctor_result = harness.doctor_static(project_root=tmp_path)
    assert (
        doctor_result.returncode != 0
    ), "doctor_static should fail on a v001/v003 history gap (no v002)"
    findings = json.loads(doctor_result.stdout)
    contiguity_fails = [
        f
        for f in findings["findings"]
        if f["check_id"] == "doctor-version-contiguity" and f["status"] == "fail"
    ]
    assert contiguity_fails, (
        "expected a doctor-version-contiguity fail Finding; "
        f"got findings={findings['findings']!r}"
    )
    assert "v002" in contiguity_fails[0]["message"], (
        "the version-contiguity fail Finding should name the first missing "
        f"version v002; got message={contiguity_fails[0]['message']!r}"
    )
