"""Tests for dev-tooling/checks/check_mutation.py.

Per SPECIFICATION/constraints.md §"Enforcement suite — Release-gate targets":
check_mutation runs mutmut against livespec/parse/ + validate/ and compares
the kill rate against the .mutmut-baseline.json ratchet (capped at 80%).
First-run mode: when baseline shows total=0 (placeholder), the check runs
mutmut, saves the result as the real baseline, and exits 0.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENDOR_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "_vendor"
sys.path.insert(0, str(_VENDOR_DIR))


def _load_check_mutation() -> ModuleType:
    """Load check_mutation.py via importlib without mutating sys.path."""
    path = _REPO_ROOT / "dev-tooling" / "checks" / "check_mutation.py"
    spec = importlib.util.spec_from_file_location("check_mutation", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_cm = _load_check_mutation()
_cm_vars = vars(_cm)
_baseline_is_placeholder = _cm_vars["_baseline_is_placeholder"]
_derive_exit_code = _cm_vars["_derive_exit_code"]
_parse_mutmut_results = _cm_vars["_parse_mutmut_results"]
_update_baseline = _cm_vars["_update_baseline"]

__all__: list[str] = []


def test_baseline_is_placeholder_true_when_total_zero() -> None:
    """Placeholder baseline has total=0."""
    baseline = {"kill_rate_percent": 0, "mutants_surviving": 0, "mutants_total": 0}
    assert _baseline_is_placeholder(baseline=baseline) is True


def test_baseline_is_placeholder_false_when_total_nonzero() -> None:
    """Real baseline has total > 0."""
    baseline = {"kill_rate_percent": 85.0, "mutants_surviving": 3, "mutants_total": 20}
    assert _baseline_is_placeholder(baseline=baseline) is False


def test_parse_mutmut_results_parses_killed_survived() -> None:
    """Parses mutmut results output format."""
    results_output = "Killed: 17\nSurvived: 3\nTimeout: 0\nTotal: 20\n"
    killed, total = _parse_mutmut_results(output=results_output)
    assert killed == 17
    assert total == 20


def test_parse_mutmut_results_zero_survived() -> None:
    """Handles zero-survived case."""
    results_output = "Killed: 20\nSurvived: 0\nTimeout: 0\nTotal: 20\n"
    killed, total = _parse_mutmut_results(output=results_output)
    assert killed == 20
    assert total == 20


def test_parse_mutmut_results_all_survived() -> None:
    """Handles all-survived (no kills) case."""
    results_output = "Killed: 0\nSurvived: 5\nTimeout: 0\nTotal: 5\n"
    killed, total = _parse_mutmut_results(output=results_output)
    assert killed == 0
    assert total == 5


def test_derive_exit_code_passes_above_threshold() -> None:
    """Kill rate above 80% and at or above baseline passes."""
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    code = _derive_exit_code(killed=18, total=20, baseline=baseline)
    assert code == 0


def test_derive_exit_code_fails_below_80_percent() -> None:
    """Kill rate below 80% always fails."""
    baseline = {"kill_rate_percent": 0.0, "mutants_surviving": 0, "mutants_total": 0}
    code = _derive_exit_code(killed=3, total=20, baseline=baseline)
    assert code == 1


def test_derive_exit_code_fails_on_regression() -> None:
    """Kill rate below prior baseline fails (regression)."""
    baseline = {"kill_rate_percent": 90.0, "mutants_surviving": 2, "mutants_total": 20}
    code = _derive_exit_code(killed=14, total=20, baseline=baseline)
    assert code == 1


def test_derive_exit_code_passes_when_zero_mutants() -> None:
    """Zero total mutants passes (nothing to kill)."""
    baseline = {"kill_rate_percent": 0.0, "mutants_surviving": 0, "mutants_total": 0}
    code = _derive_exit_code(killed=0, total=0, baseline=baseline)
    assert code == 0


def test_update_baseline_writes_to_file(*, tmp_path: Path) -> None:
    """Baseline is written to the file correctly."""
    baseline_path = tmp_path / ".mutmut-baseline.json"
    _update_baseline(
        baseline_path=baseline_path,
        killed=17,
        total=20,
    )
    written = json.loads(baseline_path.read_text())
    assert written["kill_rate_percent"] == pytest.approx(85.0)
    assert written["mutants_surviving"] == 3
    assert written["mutants_total"] == 20


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


def test_main_first_run_captures_baseline(*, tmp_path: Path) -> None:
    """First run (placeholder baseline) runs mutmut, saves baseline, exits 0."""
    import subprocess

    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    baseline = {"kill_rate_percent": 0, "mutants_surviving": 0, "mutants_total": 0}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["mutants_total"] == 20
    assert written["kill_rate_percent"] == pytest.approx(85.0)


def test_main_non_first_run_passes(*, tmp_path: Path) -> None:
    """Non-first run with kill rate >= 80% passes."""
    import subprocess

    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=18, total=20)
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_main_non_first_run_fails_regression(*, tmp_path: Path) -> None:
    """Non-first run with kill rate above floor but below baseline fails (regression)."""
    import subprocess

    # killed=17/20 = 85% is above the 80% floor but below baseline of 90%
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    baseline = {"kill_rate_percent": 90.0, "mutants_surviving": 2, "mutants_total": 20}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 1, f"unexpected pass; stderr={result.stderr!r}"


def test_main_non_first_run_improves_baseline(*, tmp_path: Path) -> None:
    """Non-first run with improved kill rate updates baseline."""
    import subprocess

    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=20, total=20)
    baseline = {"kill_rate_percent": 85.0, "mutants_surviving": 3, "mutants_total": 20}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 0
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["kill_rate_percent"] == pytest.approx(100.0)


def test_main_no_baseline_file_treats_as_placeholder(*, tmp_path: Path) -> None:
    """Missing baseline file is treated as placeholder → first-run mode."""
    import subprocess

    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=17, total=20)
    # No .mutmut-baseline.json in tmp_path at all

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert (tmp_path / ".mutmut-baseline.json").is_file()


def test_main_non_first_run_passes_no_improvement(*, tmp_path: Path) -> None:
    """Non-first run with kill rate == baseline does not update baseline."""
    import subprocess

    # killed=16/20 = 80% exactly at floor and == baseline; passes without improvement
    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=16, total=20)
    baseline = {"kill_rate_percent": 80.0, "mutants_surviving": 4, "mutants_total": 20}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    written = json.loads((tmp_path / ".mutmut-baseline.json").read_text())
    assert written["kill_rate_percent"] == pytest.approx(80.0)


def test_main_mutmut_run_fails(*, tmp_path: Path) -> None:
    """Mutmut run returning non-0/1 exit code fails check."""
    import subprocess

    fake = _make_fake_mutmut(tmp_path=tmp_path, killed=0, total=0, run_rc=2)
    baseline = {"kill_rate_percent": 0, "mutants_surviving": 0, "mutants_total": 0}
    (tmp_path / ".mutmut-baseline.json").write_text(json.dumps(baseline), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_CHECK_MUTATION_SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(fake)},
    )
    assert result.returncode == 1
