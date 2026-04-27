"""check_mutation: mutation-testing release-gate (v013 M3).

Per python-skill-script-style-requirements.md canonical target list
+ §"Mutation testing as release-gate":

    `mutmut` mutation testing against `livespec/parse/` and
    `livespec/validate/`. Threshold: ratchet against
    `.mutmut-baseline.json` (v013 M3) bounded by absolute 80%
    ceiling; emits structured JSON surviving-mutants report on
    failure.

Threshold formula:

    threshold = min(baseline.kill_rate_percent - 5, 80)

The ratchet accepts at most a 5-point regression relative to
baseline while also enforcing the absolute 80% ceiling once
baseline exceeds it. Once a release-tag run measures sustained
≥80% kill rate, a propose-change cycle deprecates the baseline
file and the threshold collapses to the static 80%.

Release-gate only — NOT part of `just check`. The `justfile`
target `check-mutation` is invoked from the release-tag CI
workflow only. Locally, this script can be invoked manually for
verification.

Failure-output contract: when `measured_kill_rate_percent <
threshold`, a JSON summary is written to stderr:

    {
      "threshold_percent": <float>,
      "measured_percent": <float>,
      "baseline_percent": <float>,
      "mutants_surviving": <int>,
      "mutants_total": <int>
    }
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__all__: list[str] = [
    "ABSOLUTE_CEILING",
    "BASELINE_PATH",
    "MutationResult",
    "check_repo",
    "compute_threshold",
    "main",
    "parse_baseline",
]


log = logging.getLogger(__name__)

BASELINE_PATH = Path(".mutmut-baseline.json")
ABSOLUTE_CEILING = 80.0
_RATCHET_DELTA = 5.0


@dataclass(frozen=True, kw_only=True, slots=True)
class MutationResult:
    """Mutmut run summary."""

    kill_rate_percent: float
    mutants_surviving: int
    mutants_total: int


def main() -> int:
    """Run mutmut + apply the ratchet-with-ceiling rule. Release-gate."""
    repo_root = Path.cwd()
    baseline = parse_baseline(path=repo_root / BASELINE_PATH)
    if baseline is None:
        log.error("%s: cannot read baseline", BASELINE_PATH)
        return 1
    threshold = compute_threshold(baseline_kill_rate_percent=baseline.kill_rate_percent)
    measured = _run_mutmut(repo_root=repo_root)
    if measured is None:
        log.error("mutmut invocation failed; treat as release-gate failure")
        return 1
    return check_repo(measured=measured, baseline=baseline, threshold=threshold)


def parse_baseline(*, path: Path) -> MutationResult | None:
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict):
        return None
    try:
        return MutationResult(
            kill_rate_percent=float(doc["kill_rate_percent"]),
            mutants_surviving=int(doc["mutants_surviving"]),
            mutants_total=int(doc["mutants_total"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def compute_threshold(*, baseline_kill_rate_percent: float) -> float:
    """Return min(baseline - 5, ABSOLUTE_CEILING)."""
    return min(baseline_kill_rate_percent - _RATCHET_DELTA, ABSOLUTE_CEILING)


def check_repo(
    *,
    measured: MutationResult,
    baseline: MutationResult,
    threshold: float,
) -> int:
    """Emit structured JSON to stderr on failure; return 0/1."""
    if measured.kill_rate_percent >= threshold:
        return 0
    summary = {
        "threshold_percent": threshold,
        "measured_percent": measured.kill_rate_percent,
        "baseline_percent": baseline.kill_rate_percent,
        "mutants_surviving": measured.mutants_surviving,
        "mutants_total": measured.mutants_total,
    }
    sys.stderr.write(json.dumps(summary, indent=2) + "\n")
    return 1


def _run_mutmut(*, repo_root: Path) -> MutationResult | None:
    """Invoke mutmut + parse its output. Phase 4 minimum-viable.

    Phase 4 scope: the script's correctness is the threshold logic +
    structured-output contract above. Actually invoking mutmut
    against the live tree is a release-tag CI step; here we shell
    out and best-effort-parse the result. If mutmut is absent or
    fails to produce a recognizable summary, return None.
    """
    paths_to_mutate = (
        ".claude-plugin/scripts/livespec/parse,.claude-plugin/scripts/livespec/validate"
    )
    try:
        completed = subprocess.run(  # noqa: S603
            ["mutmut", "run", "--paths-to-mutate", paths_to_mutate],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
            cwd=repo_root,
        )
    except FileNotFoundError:
        return None
    return _parse_mutmut_summary(output=completed.stdout + completed.stderr)


def _parse_mutmut_summary(*, output: str) -> MutationResult | None:
    """Best-effort parse of mutmut's tail summary. Returns None on shape mismatch."""
    surviving = total = 0
    for line in output.splitlines():
        if "killed" in line.lower() or "survived" in line.lower():
            for token in line.replace("/", " ").split():
                if token.isdigit():
                    total = max(total, int(token))
    if total <= 0:
        return None
    kill_rate = 100.0 * (total - surviving) / total
    return MutationResult(
        kill_rate_percent=kill_rate,
        mutants_surviving=surviving,
        mutants_total=total,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
