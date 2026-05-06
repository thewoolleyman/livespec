"""E2E doctor-fail-then-fix test.

Per SPECIFICATION/contracts.md §"E2E harness contract §"Error paths": a
pre-seeded SPECIFICATION/spec.md with a mixed-case `Must` trips
bcp14-keyword-wellformedness; propose-change + revise with --skip-pre-check
fixes it; second doctor invocation exits 0.
"""

from __future__ import annotations

import json
import subprocess  # documented integration-test usage
import sys
from pathlib import Path

import fake_claude

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIN_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin"

_BAD_SPEC_CONTENT = """\
# `Doctor fail-then-fix test`

<!-- region:project-intent -->

This project Must comply with its own spec. The change MUST flow through revise.

<!-- /region:project-intent -->

<!-- region:dod -->

Changes MUST be reviewed.

<!-- /region:dod -->
"""

_FIXED_SPEC_CONTENT = """\
# `Doctor fail-then-fix test`

<!-- region:project-intent -->

This project MUST comply with its own spec. The change MUST flow through revise.

<!-- /region:project-intent -->

<!-- region:dod -->

Changes MUST be reviewed.

<!-- /region:dod -->
"""


def _git(*, cwd: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
    )


def test_doctor_fail_then_fix(*, tmp_path: Path) -> None:  # noqa: PLR0915
    """Pre-seed bad spec → doctor fails → propose-change + revise fix → doctor passes.

    PLR0915 noqa: multi-step integration test — sequential steps share state via
    tmp_path filesystem; extracting into helpers obscures the fix-then-verify flow.
    """
    _git(cwd=tmp_path, args=["init"])
    _git(cwd=tmp_path, args=["config", "user.email", "e2e-test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "E2E Test"])

    seed_result = fake_claude.seed(
        project_root=tmp_path, intent="Doctor fail-then-fix test project"
    )
    assert seed_result.returncode == 0, f"seed failed: {seed_result.stderr!r}"

    spec_path = tmp_path / "SPECIFICATION" / "spec.md"
    spec_path.write_text(_BAD_SPEC_CONTENT, encoding="utf-8")

    _git(cwd=tmp_path, args=["add", "-A"])
    _git(cwd=tmp_path, args=["commit", "-m", "seed with bad spec"])

    doctor_bad = fake_claude.doctor_static(project_root=tmp_path)
    assert doctor_bad.returncode != 0, "doctor_static should fail on mixed-case 'Must' in spec"
    bad_findings = json.loads(doctor_bad.stdout)
    fail_ids = [f["check_id"] for f in bad_findings["findings"] if f["status"] == "fail"]
    assert "doctor-bcp14-keyword-wellformedness" in fail_ids

    findings_payload: dict[str, object] = {
        "findings": [
            {
                "name": "Fix mixed-case Must to MUST",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "The spec uses mixed-case 'Must' which MUST be uppercase 'MUST'.",
                "motivation": "bcp14-keyword-wellformedness doctor check failed.",
                "proposed_changes": (
                    "Replace 'Must' with 'MUST' throughout SPECIFICATION/spec.md."
                ),
            }
        ]
    }
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(findings_payload, f)
        findings_path = f.name

    propose_result = subprocess.run(
        [
            sys.executable,
            str(_BIN_DIR / "propose_change.py"),
            "--findings-json",
            findings_path,
            "--spec-target",
            str(tmp_path / "SPECIFICATION"),
            "--project-root",
            str(tmp_path),
            "fix-must-case",
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert propose_result.returncode == 0, f"propose-change failed: {propose_result.stderr!r}"

    revise_payload: dict[str, object] = {
        "decisions": [
            {
                "proposal_topic": "fix-must-case",
                "decision": "accept",
                "rationale": "Accepted: fix mixed-case Must to uppercase MUST.",
                "resulting_files": [{"path": "spec.md", "content": _FIXED_SPEC_CONTENT}],
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(revise_payload, f)
        revise_path = f.name

    spec_target = tmp_path / "SPECIFICATION"
    revise_result = subprocess.run(
        [
            sys.executable,
            str(_BIN_DIR / "revise.py"),
            "--revise-json",
            revise_path,
            "--spec-target",
            str(spec_target),
            "--project-root",
            str(tmp_path),
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert revise_result.returncode == 0, f"revise failed: {revise_result.stderr!r}"

    _git(cwd=tmp_path, args=["add", "-A"])
    _git(cwd=tmp_path, args=["commit", "-m", "fix bcp14 Must -> MUST"])

    doctor_good = fake_claude.doctor_static(project_root=tmp_path)
    assert (
        doctor_good.returncode == 0
    ), f"doctor_static should pass after fix; stdout={doctor_good.stdout!r}"
