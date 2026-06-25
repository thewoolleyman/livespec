"""Outside-in test for `dev-tooling/checks/behavior_scenario_link.py`.

Covers the severity lever (`LIVESPEC_BEHAVIOR_SCENARIO_LINK`):
warn-mode is non-blocking (exit 0) while still surfacing unlinked
clauses; fail-mode blocks (exit 1) on any unlinked clause. Also
covers the link-resolution rules: a clause linked to a LIVE
`scenarios.md` H2 section is satisfied; a link to a stale/typo'd
scenario name does NOT count; the `## ` prefix is optional.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

__all__: list[str] = []

# Every test in this module drives the check OUT-OF-PROCESS via
# `subprocess.run`, so the whole module is integration-tier. The
# marker declares that tier honestly (registered in
# pyproject.toml `[tool.pytest.ini_options].markers`) and is what
# `check-heading-coverage` AST-detects to satisfy the scenarios.md
# integration-tier requirement for `## Behavior clause lacking a
# scenario link is surfaced` in `tests/heading-coverage.json`.
pytestmark = [pytest.mark.integration]


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "behavior_scenario_link.py"

# A spec.md with exactly one behavior clause; its gap-id is derived
# the same way the check derives it, so the test stays independent
# of the absolute id value.
_SPEC_MD = "# Top\n\n## Section A\n\nEvery reader MUST validate the input.\n"
_SCENARIOS_MD = "# Scenarios\n\n## Happy path\n\nGiven a reader When input Then validated.\n"


def _gap_id_for_clause() -> str:
    """Derive the gap-id the check will compute for the lone clause."""
    loader = importlib.util.spec_from_file_location(
        "spec_clauses_for_test",
        _REPO_ROOT / "dev-tooling" / "spec_clauses.py",
    )
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    sys.modules[loader.name] = module
    loader.loader.exec_module(module)
    return module.derive_gap_id(
        spec_file="spec.md",
        heading_path="Top > Section A",
        rule_text="Every reader MUST validate the input.",
    )


def _write_spec(*, root: Path, coverage: list[dict[str, object]]) -> None:
    spec = root / "SPECIFICATION"
    spec.mkdir(parents=True, exist_ok=True)
    _ = (spec / "spec.md").write_text(_SPEC_MD, encoding="utf-8")
    _ = (spec / "scenarios.md").write_text(_SCENARIOS_MD, encoding="utf-8")
    tests_dir = root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    _ = (tests_dir / "heading-coverage.json").write_text(json.dumps(coverage), encoding="utf-8")


def _run(*, cwd: Path, mode: str | None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if mode is None:
        _ = env.pop("LIVESPEC_BEHAVIOR_SCENARIO_LINK", None)
    else:
        env["LIVESPEC_BEHAVIOR_SCENARIO_LINK"] = mode
    return subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_warn_mode_is_non_blocking_but_surfaces_unlinked(tmp_path: Path) -> None:
    _write_spec(root=tmp_path, coverage=[])
    result = _run(cwd=tmp_path, mode=None)  # default is warn
    assert result.returncode == 0, f"warn mode must not block; stderr={result.stderr!r}"
    assert "behavior-scenario-link-unlinked" in result.stderr
    assert "behavior-scenario-link-summary" in result.stderr


def test_fail_mode_blocks_on_unlinked(tmp_path: Path) -> None:
    _write_spec(root=tmp_path, coverage=[])
    result = _run(cwd=tmp_path, mode="fail")
    assert result.returncode == 1, f"fail mode must block; stderr={result.stderr!r}"
    assert "behavior-scenario-link-unlinked" in result.stderr


def test_linked_clause_passes_in_both_modes(tmp_path: Path) -> None:
    coverage: list[dict[str, object]] = [
        {
            "heading": "## Section A",
            "spec_root": "SPECIFICATION",
            "spec_file": "spec.md",
            "test": "tests.e2e.test_x.test_y",
            "clauses": [{"gap_id": _gap_id_for_clause(), "scenario": "Happy path"}],
        }
    ]
    _write_spec(root=tmp_path, coverage=coverage)
    warn = _run(cwd=tmp_path, mode="warn")
    fail = _run(cwd=tmp_path, mode="fail")
    assert warn.returncode == 0
    assert fail.returncode == 0, f"linked clause must pass in fail mode; stderr={fail.stderr!r}"
    assert "behavior-scenario-link-unlinked" not in fail.stderr


def test_h2_prefix_is_optional_in_link(tmp_path: Path) -> None:
    # The scenario value carries the full `## ` H2 form here.
    coverage: list[dict[str, object]] = [
        {
            "heading": "## Section A",
            "spec_root": "SPECIFICATION",
            "spec_file": "spec.md",
            "test": "tests.e2e.test_x.test_y",
            "clauses": [{"gap_id": _gap_id_for_clause(), "scenario": "## Happy path"}],
        }
    ]
    _write_spec(root=tmp_path, coverage=coverage)
    result = _run(cwd=tmp_path, mode="fail")
    assert result.returncode == 0, f"## prefix must resolve; stderr={result.stderr!r}"


def test_stale_scenario_link_does_not_count(tmp_path: Path) -> None:
    # The link points at a scenario name that is NOT a live H2 section.
    coverage: list[dict[str, object]] = [
        {
            "heading": "## Section A",
            "spec_root": "SPECIFICATION",
            "spec_file": "spec.md",
            "test": "tests.e2e.test_x.test_y",
            "clauses": [{"gap_id": _gap_id_for_clause(), "scenario": "Nonexistent scenario"}],
        }
    ]
    _write_spec(root=tmp_path, coverage=coverage)
    result = _run(cwd=tmp_path, mode="fail")
    assert result.returncode == 1, "a stale scenario link must not satisfy the guardrail"
    assert "behavior-scenario-link-unlinked" in result.stderr


def test_no_specification_dir_is_a_noop(tmp_path: Path) -> None:
    result = _run(cwd=tmp_path, mode="fail")
    assert result.returncode == 0, "absent SPECIFICATION/ must be a clean no-op"


def test_unrecognized_mode_defaults_to_warn(tmp_path: Path) -> None:
    _write_spec(root=tmp_path, coverage=[])
    result = _run(cwd=tmp_path, mode="bogus")
    assert result.returncode == 0, "an unrecognized lever value must default to warn"
    assert "behavior-scenario-link-unlinked" in result.stderr


def _write_spec_raw(*, root: Path, coverage_json: str | None) -> None:
    """Write the spec fixture with a RAW (possibly malformed) coverage map.

    `coverage_json` is the literal `tests/heading-coverage.json`
    body; `None` omits the file entirely (the absent-coverage-file
    branch). This bypasses `_write_spec`'s typed `coverage` param so
    the defensive parse branches can be exercised.
    """
    spec = root / "SPECIFICATION"
    spec.mkdir(parents=True, exist_ok=True)
    _ = (spec / "spec.md").write_text(_SPEC_MD, encoding="utf-8")
    _ = (spec / "scenarios.md").write_text(_SCENARIOS_MD, encoding="utf-8")
    if coverage_json is not None:
        tests_dir = root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        _ = (tests_dir / "heading-coverage.json").write_text(coverage_json, encoding="utf-8")


def test_absent_coverage_file_surfaces_all_clauses(tmp_path: Path) -> None:
    # No tests/heading-coverage.json at all: every clause is unlinked.
    _write_spec_raw(root=tmp_path, coverage_json=None)
    result = _run(cwd=tmp_path, mode="warn")
    assert result.returncode == 0
    assert "behavior-scenario-link-unlinked" in result.stderr


def test_malformed_coverage_shapes_are_skipped_not_crashed(tmp_path: Path) -> None:
    # Exercises every defensive skip branch in _linked_gap_ids:
    #   top-level not a list; entry not a dict; clauses not a list;
    #   a clause not a dict; gap_id/scenario not strings.
    # None of these should crash; all leave the lone clause unlinked.
    malformed_shapes = [
        '{"not": "a list"}',
        '["entry-is-a-string"]',
        '[{"clauses": "not-a-list"}]',
        '[{"clauses": ["clause-is-a-string"]}]',
        '[{"clauses": [{"gap_id": 1, "scenario": 2}]}]',
    ]
    for raw in malformed_shapes:
        _write_spec_raw(root=tmp_path, coverage_json=raw)
        result = _run(cwd=tmp_path, mode="fail")
        assert result.returncode == 1, f"malformed map must leave clause unlinked; raw={raw!r}"
        assert "behavior-scenario-link-unlinked" in result.stderr
