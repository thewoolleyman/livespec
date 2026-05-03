"""Tests for livespec.doctor.run_static.

Per PROPOSAL.md §"`doctor`" (line ~2468) and Plan Phase 3
(lines 1554-1616): run_static is the static-phase orchestrator.
It enumerates `(spec_root, template_name)` pairs, builds a
per-tree DoctorContext, and runs the applicable check subset
per the orchestrator-owned applicability table. Phase-3 minimum
subset registers 8 checks; the rest land at Phase 7.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.doctor import run_static

__all__: list[str] = []


def test_run_static_main_exists_and_returns_int(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/doctor/run_static.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Cycle 142 widened the orchestrator
    to actually exercise STATIC_CHECKS against the resolved
    project_root; calling with argv=[] hits the cwd-fallback
    branch via _resolve_project_root. monkeypatch.chdir(tmp_path)
    isolates that branch so checks don't read the actual repo
    tree (per the cycle 122 cleanup lesson). capsys silences
    the JSON payload the orchestrator writes to stdout.
    """
    monkeypatch.chdir(tmp_path)
    exit_code = run_static.main(argv=[])
    _ = capsys.readouterr()
    assert isinstance(exit_code, int)


def _seed_fully_valid_project(*, project_root: Path) -> Path:
    """Seed a project root with a fully-valid spec tree all 8 checks pass.

    Returns the spec_root. The fixture mirrors the post-seed
    output shape per PROPOSAL §"`seed`": .livespec.jsonc with
    a builtin template; <spec_root>/spec.md; proposed_changes/
    + history/ + history/v001/proposed_changes/{seed.md,
    seed-revision.md}.
    """
    project_root.mkdir(parents=True, exist_ok=True)
    config_text = '{\n  "template": "livespec"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    _ = (spec_root / "spec.md").write_text("# Spec\n", encoding="utf-8")
    (spec_root / "proposed_changes").mkdir()
    history_v001_pc = spec_root / "history" / "v001" / "proposed_changes"
    history_v001_pc.mkdir(parents=True)
    _ = (history_v001_pc / "seed.md").write_text("# seed\n", encoding="utf-8")
    _ = (history_v001_pc / "seed-revision.md").write_text(
        "# revision\n", encoding="utf-8",
    )
    return spec_root


def test_run_static_main_returns_zero_on_fully_valid_project(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """run_static.main returns exit 0 when every registered check passes.

    Drives the orchestrator's per-check dispatch pathway: it
    must build a DoctorContext from --project-root, iterate
    every member of STATIC_CHECKS, run each, and pattern-match
    the aggregated outcome. When every check produces
    IOSuccess(Finding(status='pass')) the supervisor returns 0
    per the doctor static-phase exit code contract (no findings
    => exit 0). capsys is consumed to keep the JSON payload
    out of the test's stdout (the next test asserts on its
    contents).
    """
    project_root = tmp_path / "project"
    _ = _seed_fully_valid_project(project_root=project_root)
    exit_code = run_static.main(argv=["--project-root", str(project_root)])
    _ = capsys.readouterr()
    assert exit_code == 0


def test_run_static_main_returns_usage_exit_code_on_unknown_flag() -> None:
    """run_static.main returns exit 2 when argparse rejects an unknown flag.

    Drives the parse-error branch of the supervisor's
    pattern-match: io/cli.parse_argv lifts argparse's
    SystemExit-on-unknown-flag into a Failure(UsageError),
    which the supervisor maps to err.exit_code = 2 per the
    style doc §"Exit code contract".
    """
    exit_code = run_static.main(argv=["--no-such-flag"])
    assert exit_code == 2


def test_run_static_main_emits_findings_json_to_stdout(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """run_static.main writes a `{"findings": [...]}` JSON payload to stdout.

    Per finding.schema.json + doctor_findings.schema.json: the
    orchestrator's stdout output is a single JSON object whose
    `findings` array carries one Finding entry per registered
    check. Asserts the payload contains all 8 Phase-3 minimum-
    subset check_ids when run against the fully-valid fixture.
    """
    project_root = tmp_path / "project"
    _ = _seed_fully_valid_project(project_root=project_root)
    _ = run_static.main(argv=["--project-root", str(project_root)])
    out = capsys.readouterr().out
    expected_check_ids = {
        "doctor-livespec-jsonc-valid",
        "doctor-template-exists",
        "doctor-template-files-present",
        "doctor-proposed-changes-and-history-dirs",
        "doctor-version-directories-complete",
        "doctor-version-contiguity",
        "doctor-revision-to-proposed-change-pairing",
        "doctor-proposed-change-topic-format",
    }
    for check_id in expected_check_ids:
        assert check_id in out, f"missing {check_id!r} in stdout"
