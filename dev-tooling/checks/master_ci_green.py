"""master_ci_green — master branch's most recent CI run is green.

Guard Layer 1 mechanical check that prevents the silent-red-master
pattern: master CI failed three weeks ago, every PR merged onto red
master inherited the brokenness, no agent surfaced it. The check
ensures master CI is in a known-green state at every commit.

External state: shells out to `gh run list` to fetch the most
recent master CI run's conclusion. When `gh` is unavailable or
unauthenticated locally, exits 0 with a structured warning so local
pre-commit runs are not blocked; CI sets `GH_TOKEN` so the call
always succeeds there.

Acceptable conclusions:
- "success"  → exit 0
- in-progress / queued → exit 0 with informational log (CI may
  not have caught up to a fresh master push yet)
- "failure" / "cancelled" / "timed_out" / "action_required" → exit 1
- empty list (no CI runs ever) → exit 0 with warning (probably a
  fresh repo)

Output discipline matches sibling checks: structlog JSON to stderr;
no `print`, no `sys.stderr.write`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402

__all__: list[str] = []


_GREEN_CONCLUSIONS: frozenset[str] = frozenset({"success"})
_PENDING_STATUSES: frozenset[str] = frozenset(
    {"queued", "in_progress", "waiting", "pending", "requested"},
)
_RED_CONCLUSIONS: frozenset[str] = frozenset(
    {"failure", "cancelled", "timed_out", "action_required", "stale", "startup_failure"},
)


def _fetch_latest_master_ci(
    *,
    log: structlog.stdlib.BoundLogger,
) -> tuple[str | None, str | None] | None:
    """Return (status, conclusion) for the latest master CI run.

    Returns None when `gh` is unavailable or the call fails (caller
    treats None as a non-blocking skip). On API success, returns the
    pair (`status`, `conclusion`); `conclusion` is None until the
    run completes.
    """
    if shutil.which("gh") is None:
        log.warning(
            "gh CLI not on PATH; skipping master-CI-green check",
            hint="install gh CLI or run in CI with GH_TOKEN set",
        )
        return None
    completed = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--branch",
            "master",
            "--limit",
            "1",
            "--workflow",
            "CI",
            "--json",
            "status,conclusion",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        log.warning(
            "gh api call failed; skipping master-CI-green check",
            stderr=completed.stderr.strip()[:200],
            hint="check gh auth status",
        )
        return None
    payload: object = json.loads(completed.stdout)
    if not isinstance(payload, list) or not payload:
        log.warning(
            "no CI runs on master yet; skipping master-CI-green check",
            hint="run CI on master to populate signal",
        )
        return None
    first: object = payload[0]
    if not isinstance(first, dict):
        log.error("unexpected gh response shape", payload_type=type(first).__name__)
        return None
    status_raw: object = first.get("status")
    conclusion_raw: object = first.get("conclusion")
    status = status_raw if isinstance(status_raw, str) else None
    conclusion = conclusion_raw if isinstance(conclusion_raw, str) else None
    return (status, conclusion)


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_master_ci_green")
    fetched = _fetch_latest_master_ci(log=log)
    if fetched is None:
        return 0
    status, conclusion = fetched
    if status in _PENDING_STATUSES:
        log.info(
            "master CI is still pending; treating as non-blocking",
            status=status,
            conclusion=conclusion,
        )
        return 0
    if conclusion in _GREEN_CONCLUSIONS:
        return 0
    if conclusion in _RED_CONCLUSIONS:
        log.error(
            "master CI is red on its most recent run",
            status=status,
            conclusion=conclusion,
            hint="fix master before landing new work",
        )
        return 1
    log.warning(
        "master CI returned an unrecognized conclusion; treating as non-blocking",
        status=status,
        conclusion=conclusion,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
