"""Livespec E2E mock harness.

Per SPECIFICATION/contracts.md §"E2E harness contract": this module provides
one function per livespec sub-command. Each function generates a deterministic
JSON payload, writes it to a temp file, invokes the real bin/<cmd>.py wrapper,
and returns the subprocess.CompletedProcess result.

Used when LIVESPEC_E2E_HARNESS=mock. The mock DOES NOT stub wrappers; every
bin/<cmd>.py runs for real. Only the payload-generation step (normally
performed by the LLM) is replaced with deterministic content.

Seed-payload path convention (§"Seed-payload path convention"): the spec file
is placed at SPECIFICATION/spec.md (two path parts) so that history/v001/ and
proposed_changes/ materialize under SPECIFICATION/ and the doctor static phase
resolves the main spec root as <project_root>/SPECIFICATION/ by default.
"""

from __future__ import annotations

import json
import subprocess  # documented integration-test usage
import sys
import tempfile
from pathlib import Path

__all__ = [
    "critique",
    "doctor_static",
    "propose_change",
    "propose_change_invalid",
    "prune_history",
    "revise",
    "seed",
]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIN_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin"

_SEED_CONTENT_TEMPLATE = """\
# `{intent}`

<!-- region:project-intent -->

{intent}. This specification governs how changes are managed.

<!-- /region:project-intent -->

<!-- region:dod -->

A change MUST flow through the propose-change/revise loop before landing.

<!-- /region:dod -->
"""


def seed(*, project_root: Path, intent: str) -> subprocess.CompletedProcess[str]:
    """Invoke bin/seed.py with a deterministic minimal-template payload."""
    payload: dict[str, object] = {
        "template": "minimal",
        "intent": intent,
        "files": [
            {
                "path": "SPECIFICATION/spec.md",
                "content": _SEED_CONTENT_TEMPLATE.format(intent=intent),
            }
        ],
        "sub_specs": [],
    }
    return _invoke_with_json(
        wrapper="seed.py",
        flag="--seed-json",
        payload=payload,
        extra_args=["--project-root", str(project_root)],
    )


def propose_change(
    *,
    project_root: Path,
    intent: str,
    topic: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke bin/propose_change.py with a deterministic findings payload."""
    payload: dict[str, object] = {
        "findings": [
            {
                "name": intent[:60],
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": f"{intent}. This proposal MUST be accepted or rejected via the revise loop.",
                "motivation": intent,
                "proposed_changes": (
                    f"The spec MUST be updated to reflect: {intent}. "
                    "This change SHOULD improve clarity."
                ),
            }
        ]
    }
    return _invoke_with_json(
        wrapper="propose_change.py",
        flag="--findings-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(project_root / "SPECIFICATION"),
            "--project-root",
            str(project_root),
            topic,
        ],
    )


def propose_change_invalid(
    *,
    project_root: Path,
    topic: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke bin/propose_change.py with a schema-INVALID payload (exit 4).

    Per SPECIFICATION/contracts.md §"E2E harness contract §"Error paths":
    this function deliberately passes a payload that fails schema validation
    to exercise the retry-on-exit-4 path. The wrapper MUST return exit 4
    (ValidationError) on schema-invalid input.
    """
    invalid_payload: dict[str, object] = {
        "findings": [
            {
                "name": "invalid-proposal",
            }
        ]
    }
    return _invoke_with_json(
        wrapper="propose_change.py",
        flag="--findings-json",
        payload=invalid_payload,
        extra_args=[
            "--spec-target",
            str(project_root / "SPECIFICATION"),
            "--project-root",
            str(project_root),
            topic,
        ],
    )


def critique(
    *,
    project_root: Path,
    intent: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke bin/critique.py with a deterministic findings payload."""
    payload: dict[str, object] = {
        "findings": [
            {
                "name": f"Critique: {intent[:50]}",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": f"Ambiguity detected: {intent}. The spec MUST clarify this.",
                "motivation": intent,
                "proposed_changes": (
                    "The spec SHOULD be updated to resolve the identified ambiguity."
                ),
            }
        ]
    }
    return _invoke_with_json(
        wrapper="critique.py",
        flag="--findings-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(project_root / "SPECIFICATION"),
            "--project-root",
            str(project_root),
        ],
    )


def revise(*, project_root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke bin/revise.py, accepting all pending proposals.

    Discovers pending proposals under SPECIFICATION/proposed_changes/,
    generates an accept decision for each with empty resulting_files
    (accept without spec-file modification), and invokes the wrapper.
    """
    spec_target = project_root / "SPECIFICATION"
    proposed_changes_dir = spec_target / "proposed_changes"
    topics = sorted(
        p.stem
        for p in proposed_changes_dir.glob("*.md")
        if p.name != "README.md" and not p.stem.endswith("-revision")
    )
    decisions = [
        {
            "proposal_topic": topic,
            "decision": "accept",
            "rationale": f"Auto-accepted by E2E mock harness for topic: {topic}",
            "resulting_files": [],
        }
        for topic in topics
    ]
    payload: dict[str, object] = {"decisions": decisions}
    return _invoke_with_json(
        wrapper="revise.py",
        flag="--revise-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(spec_target),
            "--project-root",
            str(project_root),
        ],
    )


def doctor_static(*, project_root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke bin/doctor_static.py against the project."""
    return _run_wrapper(
        argv=[
            sys.executable,
            str(_BIN_DIR / "doctor_static.py"),
            "--project-root",
            str(project_root),
        ],
        cwd=project_root,
    )


def prune_history(*, project_root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke bin/prune_history.py against the project."""
    return _run_wrapper(
        argv=[
            sys.executable,
            str(_BIN_DIR / "prune_history.py"),
            "--skip-pre-check",
            "--project-root",
            str(project_root),
        ],
        cwd=project_root,
    )


def _invoke_with_json(
    *,
    wrapper: str,
    flag: str,
    payload: dict[str, object],
    extra_args: list[str],
) -> subprocess.CompletedProcess[str]:
    """Write payload to a temp file and invoke the wrapper with flag pointing at it."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        json.dump(payload, tmp)
        tmp_path = tmp.name
    return _run_wrapper(
        argv=[sys.executable, str(_BIN_DIR / wrapper), flag, tmp_path, *extra_args],
        cwd=_REPO_ROOT,
    )


def _run_wrapper(
    *,
    argv: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Invoke a wrapper subprocess. check=False so tests can assert on returncode."""
    return subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
