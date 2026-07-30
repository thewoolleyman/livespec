"""gh_feature_surfaces — hermetic compatibility check for required gh commands.

Livespec automation depends on specific GitHub CLI surfaces in both local
sandboxes and CI monitors. This check verifies those surfaces with local
`--help` parsing only: no repository lookup, no GitHub API call, and no network
dependency. A stale `gh` binary therefore fails before downstream automation can
silently interpret an unsupported command as "no checks found".

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics flow
through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at module
import time.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = ["main"]


def _run_gh_help(*, gh_path: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [gh_path, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _checks_json_problem(*, gh_path: str) -> str | None:
    """Return a diagnostic when `gh pr checks --json` is not locally parseable."""
    result = _run_gh_help(gh_path=gh_path, args=["pr", "checks", "--json", "name", "--help"])
    if result.returncode == 0:
        return None
    detail = (result.stderr or result.stdout).strip()
    return f"`gh pr checks --json name --help` failed locally: {detail}"


def _update_branch_problem(*, gh_path: str) -> str | None:
    """Return a diagnostic when `gh pr update-branch` is unavailable."""
    result = _run_gh_help(gh_path=gh_path, args=["pr", "update-branch", "--help"])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return f"`gh pr update-branch --help` failed locally: {detail}"
    help_text = result.stdout + result.stderr
    if help_text.strip() == "" or "gh pr update-branch" in help_text:
        return None
    return "`gh pr update-branch --help` resolved to `gh pr` help, not the update-branch command"


def _collect_problems(*, gh_path: str) -> list[str]:
    problems: list[str] = []
    checks_problem = _checks_json_problem(gh_path=gh_path)
    if checks_problem is not None:
        problems.append(checks_problem)
    update_branch_problem = _update_branch_problem(gh_path=gh_path)
    if update_branch_problem is not None:
        problems.append(update_branch_problem)
    return problems


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("gh_feature_surfaces")
    gh_path = shutil.which("gh")
    if gh_path is None:
        log.error("gh compatibility check failed", issue="gh: not on PATH")
        return 1
    problems = _collect_problems(gh_path=gh_path)
    if problems:
        for problem in problems:
            log.error("gh compatibility check failed", issue=problem)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
