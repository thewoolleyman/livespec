"""branch_protection_alignment — `.github/workflows/ci.yml` matches branch protection.

Guard Layer 1 mechanical check that prevents the v039-D1-style
drift where a CI job is added or removed without updating the
master-branch required-checks list (or vice versa).

Two-direction comparison:

- Required check missing from ci.yml's matrix → ERROR (the
  v039 / `check-tests` failure: GitHub blocks merges because
  the required check never reports).
- ci.yml job that is NOT in the required list → WARNING (some
  jobs are intentionally not required, e.g., experimental
  workflows; emit a diagnostic but exit 0).

External state: the script shells out to `gh api` to fetch the
required-checks list. When `gh` is unavailable or unauthenticated
locally, the check exits 0 with a structured warning so local
pre-commit runs are not blocked; CI sets `GH_TOKEN` so the call
always succeeds in CI.

Output discipline matches sibling checks: structlog JSON to stderr;
no `print`, no `sys.stderr.write`.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402

__all__: list[str] = []


_REPO_OWNER_REPO = "thewoolleyman/livespec"
_CI_YML_PATH = Path(".github/workflows/ci.yml")
_MATRIX_TARGET_LINE = re.compile(r"^\s*-\s*([\w-]+)\s*$")
_MATRIX_HEADER = re.compile(r"^\s*matrix:\s*$")
_MATRIX_TARGET_KEY = re.compile(r"^\s*target:\s*$")


def _parse_ci_matrix(*, source: str) -> set[str]:
    """Extract the matrix.target job names from ci.yml.

    Walks the file line-by-line looking for the `matrix:` table,
    then the `target:` key, then bullet entries that look like
    job slugs (`- check-foo`). Stops collecting once a non-bullet
    non-comment line outside the bullet block is hit.
    """
    targets: set[str] = set()
    in_matrix = False
    in_target_list = False
    for raw in source.splitlines():
        if _MATRIX_HEADER.match(raw):
            in_matrix = True
            in_target_list = False
            continue
        if not in_matrix:
            continue
        if _MATRIX_TARGET_KEY.match(raw):
            in_target_list = True
            continue
        if in_target_list:
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = _MATRIX_TARGET_LINE.match(raw)
            if match is None:
                # End of bullet list (next YAML key or section).
                in_target_list = False
                continue
            targets.add(match.group(1))
    return targets


def _fetch_required_contexts(*, log: structlog.stdlib.BoundLogger) -> set[str] | None:
    """Fetch master branch protection's required_status_checks.contexts.

    Returns None and logs a warning when `gh` is unavailable or the
    API call fails (so local pre-commit runs are not blocked); CI
    has `GH_TOKEN` set so this returns the populated set there.
    """
    if shutil.which("gh") is None:
        log.warning(
            "gh CLI not on PATH; skipping branch-protection alignment check",
            hint="install gh CLI or run in CI with GH_TOKEN set",
        )
        return None
    api_path = (
        f"repos/{_REPO_OWNER_REPO}/branches/master/protection/required_status_checks/contexts"
    )
    completed = subprocess.run(
        ["gh", "api", api_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        log.warning(
            "gh api call failed; skipping branch-protection alignment check",
            stderr=completed.stderr.strip()[:200],
            hint="check gh auth status",
        )
        return None
    payload: object = json.loads(completed.stdout)
    if not isinstance(payload, list):
        log.error("unexpected gh api response shape", payload_type=type(payload).__name__)
        return None
    contexts: set[str] = set()
    for entry in payload:
        if isinstance(entry, str):
            contexts.add(entry)
    return contexts


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_branch_protection_alignment")
    cwd = Path.cwd()
    ci_yml = cwd / _CI_YML_PATH
    if not ci_yml.is_file():
        log.error("ci.yml missing", path=str(_CI_YML_PATH))
        return 1
    matrix_targets = _parse_ci_matrix(source=ci_yml.read_text(encoding="utf-8"))
    if not matrix_targets:
        log.error("ci.yml matrix.target is empty or unparseable", path=str(_CI_YML_PATH))
        return 1
    required = _fetch_required_contexts(log=log)
    if required is None:
        return 0
    missing_from_ci = required - matrix_targets
    not_required = matrix_targets - required
    for name in sorted(missing_from_ci):
        log.error(
            "required check has no matching ci.yml job",
            check=name,
            hint="add to ci.yml matrix or remove from branch protection",
        )
    for name in sorted(not_required):
        log.warning(
            "ci.yml job is not in branch-protection required list",
            check=name,
            hint="optional jobs are allowed; informational only",
        )
    if missing_from_ci:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
