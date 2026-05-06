"""check_mutation — release-gate mutation testing against livespec/parse/ + validate/.

Per SPECIFICATION/constraints.md §"Enforcement suite — Release-gate targets"
and PROPOSAL.md §"v013 M3": runs mutmut against `.claude-plugin/scripts/
livespec/parse/` and `.claude-plugin/scripts/livespec/validate/`, then
compares the kill rate against `.mutmut-baseline.json` using a ratchet-
with-ceiling mechanism:

  - Hard floor: kill_rate MUST be >= 80.0% (the v1 absolute minimum).
  - Ratchet: kill_rate MUST be >= the recorded baseline kill_rate_percent
    (no regression allowed once established).
  - First-run mode: when the baseline file records `mutants_total: 0`
    (the pre-implementation placeholder), the check runs mutmut, saves
    the result as the new baseline, and exits 0. This allows the very
    first release-tag CI run to capture the baseline without a hard fail.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics flow
through structlog (JSON to stderr).
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402 — vendor-path-aware import after sys.path insert.

__all__: list[str] = [
    "_baseline_is_placeholder",
    "_derive_exit_code",
    "_parse_mutmut_results",
    "_update_baseline",
]

_BASELINE_PATH = Path(".mutmut-baseline.json")
_PATHS_TO_MUTATE = ",".join(
    [
        ".claude-plugin/scripts/livespec/parse",
        ".claude-plugin/scripts/livespec/validate",
    ]
)
_KILL_RATE_FLOOR: float = 80.0


def _baseline_is_placeholder(*, baseline: dict[str, object]) -> bool:
    """Return True when the baseline is the pre-implementation placeholder (total=0)."""
    return int(baseline.get("mutants_total", 0)) == 0


def _parse_mutmut_results(*, output: str) -> tuple[int, int]:
    """Parse `mutmut results` output and return (killed, total).

    Expects lines like:
      Killed: 17
      Survived: 3
      Timeout: 0
      Total: 20
    Returns (killed=0, total=0) when totals are absent or unparseable.
    """
    killed = 0
    total = 0
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Killed:"):
            with contextlib.suppress(ValueError, IndexError):
                killed = int(stripped.split(":")[1].strip())
        elif stripped.startswith("Total:"):
            with contextlib.suppress(ValueError, IndexError):
                total = int(stripped.split(":")[1].strip())
    return killed, total


def _derive_exit_code(*, killed: int, total: int, baseline: dict[str, object]) -> int:
    """Return exit code 0 (pass) or 1 (fail) based on kill rate vs baseline + floor.

    Zero-mutant case (total=0) passes unconditionally — nothing to kill.
    """
    if total == 0:
        return 0
    kill_rate = (killed / total) * 100.0
    baseline_rate = float(baseline.get("kill_rate_percent", 0.0))
    if kill_rate < _KILL_RATE_FLOOR:
        return 1
    if kill_rate < baseline_rate:
        return 1
    return 0


def _update_baseline(*, baseline_path: Path, killed: int, total: int) -> None:
    """Write a new baseline JSON file with the current mutation results."""
    kill_rate = (killed / total) * 100.0 if total > 0 else 0.0
    payload: dict[str, object] = {
        "kill_rate_percent": round(kill_rate, 2),
        "mutants_surviving": total - killed,
        "mutants_total": total,
    }
    baseline_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_mutation")
    cwd = Path.cwd()
    baseline_path = cwd / _BASELINE_PATH

    baseline: dict[str, object] = {}
    if baseline_path.is_file():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    first_run = _baseline_is_placeholder(baseline=baseline)

    run_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mutmut",
            "run",
            f"--paths-to-mutate={_PATHS_TO_MUTATE}",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd),
    )
    if run_result.returncode not in (0, 1):
        log.error(
            "mutmut run failed",
            returncode=run_result.returncode,
            stderr=run_result.stderr[:500],
        )
        return 1

    results_result = subprocess.run(
        [sys.executable, "-m", "mutmut", "results"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd),
    )
    killed, total = _parse_mutmut_results(output=results_result.stdout)
    kill_rate = (killed / total) * 100.0 if total > 0 else 0.0

    log.info(
        "mutation results",
        killed=killed,
        total=total,
        kill_rate_percent=round(kill_rate, 2),
        first_run=first_run,
    )

    if first_run:
        _update_baseline(baseline_path=baseline_path, killed=killed, total=total)
        log.info("baseline captured", baseline_path=str(baseline_path))
        return 0

    exit_code = _derive_exit_code(killed=killed, total=total, baseline=baseline)
    if exit_code == 0:
        baseline_rate = float(baseline.get("kill_rate_percent", 0.0))
        if kill_rate > baseline_rate:
            _update_baseline(baseline_path=baseline_path, killed=killed, total=total)
            log.info("baseline improved and updated", new_rate=round(kill_rate, 2))
    else:
        baseline_rate = float(baseline.get("kill_rate_percent", 0.0))
        log.error(
            "kill rate below threshold",
            kill_rate=round(kill_rate, 2),
            baseline=baseline_rate,
            floor=_KILL_RATE_FLOOR,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
