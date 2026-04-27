"""Tests for dev-tooling/checks/check_mutation.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import check_mutation  # noqa: E402

__all__: list[str] = []


_BASELINE_KILL_RATE = 75.0
_THRESHOLD_AT_BASELINE = 70.0
_BASELINE_AT_CEILING = 90.0
_PASSING_RATE = 78.0
_FAILING_RATE = 70.0
_TEST_THRESHOLD = 75.0
_PASS_RC = 0
_FAIL_RC = 1
_NEGATIVE_FIVE = -5.0


def _baseline_json(*, kill_rate: float, surviving: int, total: int) -> str:
    return json.dumps(
        {
            "baseline_reason": "test",
            "kill_rate_percent": kill_rate,
            "mutants_surviving": surviving,
            "mutants_total": total,
            "measured_at": "2026-04-26T06:25:00Z",
        }
    )


def test_parse_baseline_valid(*, tmp_path: Path) -> None:
    target = tmp_path / ".mutmut-baseline.json"
    target.write_text(
        _baseline_json(kill_rate=_BASELINE_KILL_RATE, surviving=10, total=40),
        encoding="utf-8",
    )
    parsed = check_mutation.parse_baseline(path=target)
    assert parsed is not None
    assert parsed.kill_rate_percent == _BASELINE_KILL_RATE


def test_parse_baseline_missing_returns_none(*, tmp_path: Path) -> None:
    assert check_mutation.parse_baseline(path=tmp_path / "absent.json") is None


def test_parse_baseline_malformed_returns_none(*, tmp_path: Path) -> None:
    target = tmp_path / ".mutmut-baseline.json"
    target.write_text("{not valid json}", encoding="utf-8")
    assert check_mutation.parse_baseline(path=target) is None


def test_compute_threshold_below_ceiling() -> None:
    """When baseline-5 < 80, the ratchet (baseline-5) wins."""
    assert (
        check_mutation.compute_threshold(baseline_kill_rate_percent=_BASELINE_KILL_RATE)
        == _THRESHOLD_AT_BASELINE
    )


def test_compute_threshold_at_ceiling() -> None:
    """When baseline-5 >= 80, the absolute 80% ceiling caps the threshold."""
    assert (
        check_mutation.compute_threshold(baseline_kill_rate_percent=_BASELINE_AT_CEILING)
        == check_mutation.ABSOLUTE_CEILING
    )


def test_compute_threshold_zero_baseline() -> None:
    """Pre-implementation placeholder baseline (0%) yields threshold = -5."""
    assert check_mutation.compute_threshold(baseline_kill_rate_percent=0.0) == _NEGATIVE_FIVE


def test_check_repo_passes_when_above_threshold() -> None:
    measured = check_mutation.MutationResult(
        kill_rate_percent=_PASSING_RATE,
        mutants_surviving=22,
        mutants_total=100,
    )
    baseline = check_mutation.MutationResult(
        kill_rate_percent=80.0,
        mutants_surviving=20,
        mutants_total=100,
    )
    rc = check_mutation.check_repo(
        measured=measured,
        baseline=baseline,
        threshold=_TEST_THRESHOLD,
    )
    assert rc == _PASS_RC


def test_check_repo_fails_below_threshold() -> None:
    measured = check_mutation.MutationResult(
        kill_rate_percent=_FAILING_RATE,
        mutants_surviving=30,
        mutants_total=100,
    )
    baseline = check_mutation.MutationResult(
        kill_rate_percent=80.0,
        mutants_surviving=20,
        mutants_total=100,
    )
    rc = check_mutation.check_repo(
        measured=measured,
        baseline=baseline,
        threshold=_TEST_THRESHOLD,
    )
    assert rc == _FAIL_RC
