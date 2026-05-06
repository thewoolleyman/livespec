"""Tests for livespec.doctor.run_static.

Per and Plan Phase 3
: run_static is the static-phase orchestrator.
It enumerates `(spec_root, template_name)` pairs, builds a
per-tree DoctorContext, and runs the applicable check subset
per the orchestrator-owned applicability table. Phase-3 minimum
subset registers 8 checks; the rest land at Phase 7.
"""

from __future__ import annotations

import json
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
    output shape: .livespec.jsonc with
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
        "# revision\n",
        encoding="utf-8",
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
        "doctor-bcp14-keyword-wellformedness",
        "doctor-gherkin-blank-line-format",
        "doctor-anchor-reference-resolution",
        "doctor-out-of-band-edits",
    }
    for check_id in expected_check_ids:
        assert check_id in out, f"missing {check_id!r} in stdout"


def _seed_sub_spec_tree(*, sub_spec_root: Path) -> None:
    """Seed `sub_spec_root` with the sub-spec layout the 6 sub-spec checks need.

    Sub-spec trees skip the project-root-only checks
    (`livespec_jsonc_valid` + `template_exists`) per
    APPLICABILITY_BY_TREE_KIND['sub_spec'] (Plan Phase 6 +
    static/__init__.py cycle 143). The 6 remaining checks need
    `<sub_spec_root>/{spec.md, proposed_changes/, history/v001/
    proposed_changes/}` plus the skill-owned `history/README.md`
    that v037 D1's cycle (ii) Red→Green established as the
    valid-and-skipped non-version sibling.
    """
    sub_spec_root.mkdir(parents=True, exist_ok=True)
    _ = (sub_spec_root / "spec.md").write_text("# Sub-spec\n", encoding="utf-8")
    (sub_spec_root / "proposed_changes").mkdir()
    history_path = sub_spec_root / "history"
    history_path.mkdir()
    _ = (history_path / "README.md").write_text(
        "Skill-owned directory description.\n",
        encoding="utf-8",
    )
    (history_path / "v001" / "proposed_changes").mkdir(parents=True)


def test_run_static_main_emits_per_tree_findings_for_sub_specs(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """run_static.main enumerates main + sub-spec trees in one invocation.

    Per Plan §"Phase 6" exit criterion ("/livespec:doctor's
    static phase runs cleanly against every spec tree — one
    wrapper invocation, exit 0 overall, with per-tree findings
    emitted and all marked pass"): a project that ships
    `<spec_root>/templates/<name>/` sub-spec trees must drive
    the orchestrator to enumerate every (main + sub-spec) tree,
    apply the appropriate APPLICABILITY_BY_TREE_KIND subset to
    each, and emit per-tree findings tagged with their
    `spec_root` field. Asserts: (a) exit 0; (b) main tree's 8
    Phase-3-minimum findings are emitted with the main
    spec_root; (c) each sub-spec's 6 sub-spec-applicable
    findings are emitted with the sub-spec spec_root; (d) every
    finding's status is 'pass'.
    """
    project_root = tmp_path / "project"
    main_spec_root = _seed_fully_valid_project(project_root=project_root)
    livespec_sub = main_spec_root / "templates" / "livespec"
    minimal_sub = main_spec_root / "templates" / "minimal"
    _seed_sub_spec_tree(sub_spec_root=livespec_sub)
    _seed_sub_spec_tree(sub_spec_root=minimal_sub)
    exit_code = run_static.main(argv=["--project-root", str(project_root)])
    out = capsys.readouterr().out
    assert exit_code == 0, f"expected exit 0, got {exit_code}; stdout: {out}"
    main_check_ids = {
        "doctor-livespec-jsonc-valid",
        "doctor-template-exists",
        "doctor-template-files-present",
        "doctor-proposed-changes-and-history-dirs",
        "doctor-version-directories-complete",
        "doctor-version-contiguity",
        "doctor-revision-to-proposed-change-pairing",
        "doctor-proposed-change-topic-format",
        "doctor-bcp14-keyword-wellformedness",
        "doctor-gherkin-blank-line-format",
        "doctor-anchor-reference-resolution",
        "doctor-out-of-band-edits",
    }
    sub_spec_check_ids = {
        "doctor-template-files-present",
        "doctor-proposed-changes-and-history-dirs",
        "doctor-version-directories-complete",
        "doctor-version-contiguity",
        "doctor-revision-to-proposed-change-pairing",
        "doctor-proposed-change-topic-format",
        "doctor-bcp14-keyword-wellformedness",
        "doctor-gherkin-blank-line-format",
        "doctor-anchor-reference-resolution",
        "doctor-out-of-band-edits",
    }
    payload = json.loads(out)
    findings = payload["findings"]
    findings_by_spec_root: dict[str, set[str]] = {}
    for finding in findings:
        # The out-of-band-edits check returns "skipped" when the
        # spec_root is not inside a git working tree; the tmp_path
        # fixtures here are NOT initialized as git repos, so the
        # skip is the correct outcome (: "skip the out-of-band check, the project isn't
        # versioned"). The exit-code derivation treats skipped
        # as pass, so this does not break the exit-0 invariant.
        if finding["check_id"] == "doctor-out-of-band-edits":
            assert (
                finding["status"] == "skipped"
            ), f"expected skipped for out-of-band-edits in non-git fixture; got {finding}"
        else:
            assert finding["status"] == "pass", f"non-pass finding: {finding}"
        findings_by_spec_root.setdefault(finding["spec_root"], set()).add(
            finding["check_id"],
        )
    assert findings_by_spec_root.get(str(main_spec_root)) == main_check_ids
    assert findings_by_spec_root.get(str(livespec_sub)) == sub_spec_check_ids
    assert findings_by_spec_root.get(str(minimal_sub)) == sub_spec_check_ids
