"""incident-ci prints ONLY the enablement reading the released plan recorded.

Work-item livespec-52hir3, this repository's mirror of livespec-dev-tooling-kg5qv4
(plan expedited-incident-response-flag, the livespec follow-up to
livespec-dev-tooling-ahl6vz):
`.github/workflows/ci.yml`'s incident-ci step keeps the released plan in a shell
variable, so the enablement reading the plan records (exdkra) could not be read
back from a run. The step now prints that one field to its log. The plan also
carries an environment map, so the step must never print the plan itself.

The test runs the step's own lines, taken from the committed workflow text,
under bash against a fake plan whose environment map holds a marker value, and
asserts the log line carries the enablement reading and not the marker. A
mutated copy that prints the whole plan is the negative control.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_YML = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

_ENABLEMENT_ASSIGNMENT = 'enablement="$(printf'
_ENABLEMENT_ECHO = 'echo "incident-ci: the released plan recorded enablement ${enablement}"'
_MARKER = "environment-value-that-must-never-be-logged"
_ENABLEMENT = {
    "armed": False,
    "detail": "confirmed 59912fe1",
    "installation": "127.0.0.1:8765",
    "reading": "absent",
}
_PLAN = {
    "enablement": _ENABLEMENT,
    "environment": {"EXAMPLE_SECRET": _MARKER},
    "mode": "expedited-repair",
    "selected": ["check-lint"],
}


def _echo_lines(*, source: str) -> list[str]:
    """The committed step's enablement lines, in workflow order, de-indented."""
    lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(_ENABLEMENT_ASSIGNMENT) or line.strip() == _ENABLEMENT_ECHO
    ]
    return lines


def _run(*, lines: list[str]) -> str:
    bash = shutil.which("bash")
    assert bash is not None
    script = 'plan="$(cat)"\n' + "\n".join(lines) + "\n"
    completed = subprocess.run(
        [bash, "-c", script],
        input=json.dumps(_PLAN),
        capture_output=True,
        check=True,
        text=True,
        env={"RELEASED_PYTHON": sys.executable, "PATH": "/usr/bin:/bin"},
    )
    return completed.stdout


def test_the_committed_step_prints_the_enablement_reading_and_nothing_else() -> None:
    lines = _echo_lines(source=_CI_YML.read_text(encoding="utf-8"))
    assert len(lines) == 2, lines
    assert lines[0].startswith(_ENABLEMENT_ASSIGNMENT)
    assert lines[1] == _ENABLEMENT_ECHO
    out = _run(lines=lines)
    assert out == (
        "incident-ci: the released plan recorded enablement "
        + json.dumps(_ENABLEMENT, sort_keys=True)
        + "\n"
    )
    assert _MARKER not in out


@pytest.mark.parametrize(
    "printed",
    [
        'echo "incident-ci: the released plan recorded enablement ${plan}"',
        'echo "incident-ci: the released plan recorded enablement ${enablement} ${plan}"',
    ],
)
def test_printing_the_plan_itself_is_caught(*, printed: str) -> None:
    lines = _echo_lines(source=_CI_YML.read_text(encoding="utf-8"))
    mutated = [lines[0], printed]
    out = _run(lines=mutated)
    assert _MARKER in out
