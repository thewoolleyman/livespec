"""Tests for dev-tooling/checks/check_mutation.py.

Per SPECIFICATION/constraints.md §"Enforcement suite — Release-gate targets":
check_mutation runs mutmut against livespec/parse/ + validate/ and compares
the kill rate against the .mutmut-baseline.json ratchet (capped at 80%).
First-run mode: when baseline shows total=0 (placeholder), the check runs
mutmut, saves the result as the real baseline, and exits 0.

Tests invoke check_mutation.py via subprocess with a fake mutmut package
injected through PYTHONPATH, following the established dev-tooling test
pattern. This approach lets mutmut properly substitute the mutated module
when running its own tests.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_MUTATION_SCRIPT = _REPO_ROOT / "dev-tooling" / "checks" / "check_mutation.py"


def _make_fake_mutmut(*, tmp_path: Path, killed: int, total: int, run_rc: int = 0) -> Path:
    """Write a fake mutmut package into tmp_path that emits deterministic results."""
    pkg = tmp_path / "mutmut"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text(
        f"""\
import sys
if sys.argv[1] == "run":
    sys.exit({run_rc})
elif sys.argv[1] == "results":
    print("Killed: {killed}")
    print("Survived: {total - killed}")
    print("Total: {total}")
    sys.exit(0)
""",
        encoding="utf-8",
    )
    return tmp_path


def _run_check(
    *,
    tmp_path: Path,
    fake_mutmut_dir: Path,
    baseline: dict[str, object] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run check_mutation.py in tmp_path with a fake mutmut."""
    import os

    if baseline is not None:
        (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(fake_mutmut_dir)},
    )


def test_baseline_is_placeholder_first_run(*, tmp_path: Path) -> None:
    """total=0 in baseline → first-run mode: saves baseline, exits 0."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    baseline = {"kill_rate_percent": 0, "mutants_surviving": 0, "mutants_total": 0}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["mutants_total"] == 20
    assert written["kill_rate_percent"] == pytest.approx(85.0)


def test_no_baseline_file_treated_as_placeholder(*, tmp_path: Path) -> None:
    """Missing .mutmut-baseline.json → treated as placeholder → first-run mode."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert (tmp_path / ".mutmut-baseline.json").is_file()


def test_parse_mutmut_results_parses_killed_total(*, tmp_path: Path) -> None:
    """Killed and Total fields are parsed from mutmut results output."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=18, total=20)
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_derive_exit_code_passes_at_floor(*, tmp_path: Path) -> None:
    """Kill rate at exactly 80% floor passes."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=16, total=20)
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_derive_exit_code_fails_below_80_percent(*, tmp_path: Path) -> None:
    """Kill rate below 80% always fails."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=3, total=20)
    baseline = {"kill_rate_percent": 0.0, "mutants_surviving": 0, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 1, "unexpected pass"


def test_derive_exit_code_fails_on_regression(*, tmp_path: Path) -> None:
    """Kill rate above floor but below baseline fails (regression)."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    baseline = {"kill_rate_percent": 90.0, "mutants_surviving": 2, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 1, "unexpected pass"


def test_update_baseline_on_improvement(*, tmp_path: Path) -> None:
    """Improved kill rate updates baseline."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=20, total=20)
    baseline = {"kill_rate_percent": 85.0, "mutants_surviving": 3, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["kill_rate_percent"] == pytest.approx(100.0)


def test_no_baseline_update_when_equal(*, tmp_path: Path) -> None:
    """Kill rate == baseline: passes but does not update baseline."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=16, total=20)
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["kill_rate_percent"] == pytest.approx(80.0)


def test_mutmut_run_failure_returns_1(*, tmp_path: Path) -> None:
    """Mutmut run returning non-0/1 exit code causes check to fail."""
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=0, total=0, run_rc=2)
    baseline = {"kill_rate_percent": 0, "mutants_surviving": 0, "mutants_total": 0}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 1


def test_zero_mutants_non_first_run_passes(*, tmp_path: Path) -> None:
    """Zero total mutants in non-first-run mode passes (nothing to kill)."""
    # baseline has total>0 → not placeholder; but current run returns total=0
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=0, total=0, run_rc=0)
    baseline = {"kill_rate_percent": 85.0, "mutants_surviving": 3, "mutants_total": 20}
    result = _run_check(tmp_path=tmp_path, fake_mutmut_dir=fake, baseline=baseline)
    assert result.returncode == 0
