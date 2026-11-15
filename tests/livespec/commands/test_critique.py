"""Tests for livespec.commands.critique.

Critique is minimum-viable: it invokes propose_change internally
with the `-critique` reserve-suffix appended. Full LLM-driven
critique flow lives at SKILL.md prose level, not in the wrapper.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from livespec.commands import critique
from livespec.errors import LivespecError
from livespec.io import proc
from returns.io import IOResult

__all__: list[str] = []


_DoctorRun = IOResult[subprocess.CompletedProcess[str], LivespecError]


@pytest.fixture(autouse=True)
def lifecycle_doctor_calls(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Answer the delegated propose-change's doctor runs with a passing document.

    critique delegates to propose_change, which wraps its write in the
    pre-/post-step doctor static lifecycle. The fixtures here build bare
    `SPECIFICATION/` trees the real doctor would reject, so doctor runs
    are faked and recorded (the railway spawns no other subprocess).
    """
    calls: list[list[str]] = []

    def _run(*, argv: list[str], cwd: Path | None = None) -> _DoctorRun:
        del cwd
        calls.append(argv)
        return IOResult.from_value(
            subprocess.CompletedProcess(
                args=argv,
                returncode=0,
                stdout='{"findings": []}',
                stderr="",
            ),
        )

    monkeypatch.setattr(proc, "run_subprocess", _run)
    return calls


def test_critique_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/critique.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = critique.main(argv=["--findings-json", "/tmp/x.json"])
    assert isinstance(exit_code, int)


def test_critique_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing required `--findings-json <path>` returns exit code 2.

    Per: the wrapper
    requires `--findings-json <path>` (plus optional `--author
    <id>`, `--spec-target <path>`, `--project-root <path>`).
    Drives the first real railway-composition behavior by
    threading argv through io/cli.parse_argv and pattern-matching
    the IOFailure(UsageError) onto err.exit_code (= 2).
    """
    exit_code = critique.main(argv=[])
    assert exit_code == 2


def test_critique_main_returns_precondition_exit_code_on_missing_findings_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --findings-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to the supervisor's pattern-match, which lifts to
    exit 3 via err.exit_code per style doc.
    Mirrors propose_change's test for the same railway stage.
    """
    missing = tmp_path / "no-such-findings.json"
    exit_code = critique.main(argv=["--findings-json", str(missing)])
    assert exit_code == 3


def _write_valid_findings_payload(*, tmp_path: Path) -> Path:
    """Helper: write a schema-valid proposal-findings payload to tmp_path.

    Mirrors the helper in `tests/livespec/commands/test_propose_change.py`
    so critique's schema-validation success-arm test can drive the
    railway through the schema-validation stage to IOSuccess.
    """
    import json

    payload_dict = {
        "findings": [
            {
                "name": "Sample finding",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Demo summary.",
                "motivation": "Demo motivation.",
                "proposed_changes": "Demo changes prose.",
            },
        ],
    }
    payload_path = tmp_path / "findings.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    return payload_path


def test_critique_main_returns_zero_when_findings_file_readable(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """When --findings-json points at a schema-valid payload, main returns 0.

    Drives the Success arm of the supervisor's pattern-match: the
    parse_argv -> fs.read_text -> jsonc.loads -> validate
    composition reaches IOSuccess, the supervisor enters the
    Success arm, the propose_change-delegation runs with
    cwd-default project_root, and the supervisor returns 0.

    Uses monkeypatch.chdir(tmp_path) to make the cwd-fallback
    path writable + isolated; without it, propose_change's
    `Path.cwd()` default would write into the repo root's
    `SPECIFICATION/proposed_changes/` and leak across test runs.
    `monkeypatch.delenv` removes any user-shell
    `LIVESPEC_AUTHOR_LLM` so the resolved author falls through to
    the documented Phase-7 precedence chain deterministically.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    (tmp_path / "SPECIFICATION").mkdir()
    findings_path = _write_valid_findings_payload(tmp_path=tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    exit_code = critique.main(argv=["--findings-json", str(findings_path)])
    assert exit_code == 0


def test_critique_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) bubbles via
    bind chaining; exit 4 per style doc.
    Mirrors propose_change's same railway stage.
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = critique.main(argv=["--findings-json", str(payload)])
    assert exit_code == 4


def test_critique_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives the railway widening to include schema validation
    against proposal_findings.schema.json. The payload `{}` is
    valid JSON so jsonc.loads succeeds; it then trips schema
    validation (missing required `findings` array) which returns
    Failure(ValidationError) and lifts to exit 4. Mirrors
    propose_change's same railway stage.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = critique.main(argv=["--findings-json", str(payload)])
    assert exit_code == 4


def test_critique_main_writes_proposed_change_with_critique_suffix(
    *,
    tmp_path: Path,
) -> None:
    """Successful critique writes `<spec-target>/proposed_changes/<author>-critique.md`.

    Critique delegates to propose_change with topic hint `<author>`
    plus the reserve-suffix `"-critique"`. With
    `--author claude-opus-4-7` (already canonical), the resulting
    filename is
     `claude-opus-4-7-critique.md`. The body is the same one-
     proposal-section-per-finding shape as propose_change's
     output (field-copy mapping).
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--author",
            "claude-opus-4-7",
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "claude-opus-4-7-critique.md"
    assert out.exists(), f"expected {out} to be written"
    text = out.read_text(encoding="utf-8")
    assert "## Proposal: Sample finding" in text
    assert "Demo summary." in text


def test_critique_main_propagates_project_root_to_delegated_propose_change(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """When --project-root is provided, critique forwards it to propose_change.

    Drives the `--project-root` branch of the delegated-argv
    construction. With no --spec-target, propose_change derives
    the spec target as `<project-root>/SPECIFICATION/`, so the
    output file lands at
    `<project-root>/SPECIFICATION/proposed_changes/unknown-llm-critique.md`.
    No --author argv passed, env unset, payload omits author, so
    the documented fallback "unknown-llm" is used.
    `monkeypatch.delenv` removes any user-shell
    `LIVESPEC_AUTHOR_LLM` so the assertion against
    `unknown-llm-critique.md` is deterministic post-widening.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    project_root = tmp_path / "proj"
    (project_root / "SPECIFICATION").mkdir(parents=True)
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--project-root",
            str(project_root),
        ],
    )
    assert exit_code == 0
    out = project_root / "SPECIFICATION" / "proposed_changes" / "unknown-llm-critique.md"
    assert out.exists(), f"expected {out} to be written"


def _write_findings_with_author(*, tmp_path: Path, author: str) -> Path:
    """Helper: write a schema-valid payload that includes a top-level `author`.

    The schema permits an optional file-level `author` LLM
    self-declaration (per `proposal_findings.schema.json`).
    Used by the payload-precedence test.
    """
    import json

    payload_dict = {
        "author": author,
        "findings": [
            {
                "name": "Sample finding",
                "target_spec_files": ["SPECIFICATION/spec.md"],
                "summary": "Demo summary.",
                "motivation": "Demo motivation.",
                "proposed_changes": "Demo changes prose.",
            },
        ],
    }
    payload_path = tmp_path / "findings.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    return payload_path


def test_critique_main_resolves_author_via_env_var_when_no_cli_or_payload(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """LIVESPEC_AUTHOR_LLM env var resolves when no --author and no payload author.

    Per spec.md: with no `--author` flag, the env var
    `LIVESPEC_AUTHOR_LLM` is consulted before falling through
    to the next resolution step (payload author) or the
    final fallback ("unknown-llm"). Asserts the resulting file lands
    at `<spec-target>/proposed_changes/env-author-critique.md`,
    which only happens when critique threads env-lookup through
    its `_resolve_author` helper.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setenv("LIVESPEC_AUTHOR_LLM", "env-author")
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "env-author-critique.md"
    assert out.exists(), f"expected {out} to be written"


def test_critique_main_resolves_author_via_payload_when_no_cli_or_env(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """Payload-level `author` resolves when no --author and no env var.

    Per spec.md: with no `--author` flag and no `LIVESPEC_AUTHOR_LLM`
    env var, the payload's top-level `author` field is consulted
    before falling through to "unknown-llm". Asserts the resulting file
    lands at `<spec-target>/proposed_changes/payload-author-critique.md`,
    which only happens when critique threads the validated
    payload through its `_resolve_author` helper.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_findings_with_author(tmp_path=tmp_path, author="payload-author")
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "payload-author-critique.md"
    assert out.exists(), f"expected {out} to be written"


def test_critique_main_cli_author_wins_over_env_and_payload(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """CLI --author wins over both env var and payload author.

    Per spec.md: `--author <id>` on the CLI takes precedence over
    `LIVESPEC_AUTHOR_LLM` and the payload's `author` field. With all
    three sources set, the resulting filename must be derived
    from the CLI value.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setenv("LIVESPEC_AUTHOR_LLM", "env-author")
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_findings_with_author(tmp_path=tmp_path, author="payload-author")
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--author",
            "cli-author",
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "cli-author-critique.md"
    assert out.exists(), f"expected {out} to be written"


def test_critique_main_truncates_long_author_stem_preserving_critique_suffix(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """A 70-char author stem composes via reserve-suffix to a 64-char canonical filename.

    Per spec.md: critique passes the un-slugged resolved-author stem
    as topic-hint AND
    the literal `"-critique"` as the reserve-suffix parameter to
    propose_change. propose_change's reserve-suffix
    canonicalization truncates the non-suffix portion to
    `64 - len("-critique")` = 55 chars then re-appends the
    suffix, guaranteeing the suffix is preserved intact at the
    64-char cap. With `--author` =
    70 'a' chars (already canonical), the post-widening
    filename is `("a" * 55) + "-critique.md"` (64-char stem +
    .md). The pre-widening pre-attached-then-truncate path
    would produce `("a" * 64) + ".md"` (suffix clipped), so this
    test fails before the green amend and passes after.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    long_author = "a" * 70
    exit_code = critique.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--author",
            long_author,
            "--spec-target",
            str(spec_target),
        ],
    )
    assert exit_code == 0
    expected_stem = "a" * 55
    out = spec_target / "proposed_changes" / f"{expected_stem}-critique.md"
    assert out.exists(), f"expected {out} to be written"


def test_critique_module_declares_hkt_erosion_pragma() -> None:
    """`commands/critique.py` carries the file-level HKT-erosion pyright pragma.

    Per li-xxjopf Step 3e: the returns-library bind chains that
    compose the critique supervisor's railway lose flow-narrowing
    through pyright's strict mode, surfacing as
    reportUnknownMemberType / reportUnknownVariableType /
    reportUnknownArgumentType diagnostics on most bind / map
    / unsafe_perform_io call sites. The file-level pragma
    suppresses the three HKT-related categories;
    reportArgumentType stays ON globally so non-HKT firings
    still surface. This contract test pins the pragma so a
    future reformatter / accidental top-comment edit / mass
    rewrite that drops it surfaces immediately rather than
    silently re-introducing the ~19 pyright errors at the
    next `just check-types` run.
    """
    import inspect

    from livespec.commands import critique as critique_command

    source = inspect.getsource(critique_command)
    assert source.startswith(
        "# pyright: reportUnknownMemberType=none, "
        "reportUnknownVariableType=none, "
        "reportUnknownArgumentType=none\n",
    ), "commands/critique.py must declare the HKT-erosion pragma as its first line"


def _critique_lifecycle_argv(*, tmp_path: Path, extra: list[str]) -> list[str]:
    """Argv for a critique run rooted at tmp_path, plus extra pre-check flags."""
    (tmp_path / "SPECIFICATION").mkdir(exist_ok=True)
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    return [
        "--findings-json",
        str(payload_path),
        "--project-root",
        str(tmp_path),
        "--author",
        "demo-llm",
        *extra,
    ]


def _critique_output(*, tmp_path: Path) -> Path:
    return tmp_path / "SPECIFICATION" / "proposed_changes" / "demo-llm-critique.md"


def _write_skip_config(*, tmp_path: Path, skip: bool) -> None:
    import json

    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps({"pre_step_skip_static_checks": skip}),
        encoding="utf-8",
    )


_SKIPPED_DOCUMENT = (
    '{"findings": [{"check_id": "pre-step-skipped", "status": "skipped", '
    '"message": "pre-step checks skipped by user config or --skip-pre-check"}]}\n'
)


def test_critique_runs_pre_step_doctor_before_write_and_post_step_after(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Neither flag, no config: doctor static runs before AND after the one write.

    Per contracts.md (pre-step skip control) and spec.md
    (sub-command lifecycle): critique has both pre-step and post-step
    doctor static, run against the resolved project root.
    """
    output_present_at_call: list[bool] = []

    def _run(*, argv: list[str], cwd: Path | None = None) -> _DoctorRun:
        del cwd
        assert argv[-2:] == ["--project-root", str(tmp_path)]
        output_present_at_call.append(_critique_output(tmp_path=tmp_path).is_file())
        return IOResult.from_value(
            subprocess.CompletedProcess(args=argv, returncode=0, stdout='{"findings": []}'),
        )

    monkeypatch.setattr(proc, "run_subprocess", _run)
    exit_code = critique.main(argv=_critique_lifecycle_argv(tmp_path=tmp_path, extra=[]))
    assert exit_code == 0
    assert output_present_at_call == [False, True]


def test_critique_skip_pre_check_emits_skipped_finding_and_runs_only_post_step(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    lifecycle_doctor_calls: list[list[str]],
) -> None:
    """`--skip-pre-check` emits the single pre-step-skipped finding; post-step still runs."""
    exit_code = critique.main(
        argv=_critique_lifecycle_argv(tmp_path=tmp_path, extra=["--skip-pre-check"]),
    )
    assert exit_code == 0
    assert capsys.readouterr().out == _SKIPPED_DOCUMENT
    assert len(lifecycle_doctor_calls) == 1
    assert _critique_output(tmp_path=tmp_path).is_file()


def test_critique_config_key_true_skips_pre_step(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    lifecycle_doctor_calls: list[list[str]],
) -> None:
    """Neither flag: `pre_step_skip_static_checks: true` skips the pre-step."""
    _write_skip_config(tmp_path=tmp_path, skip=True)
    exit_code = critique.main(argv=_critique_lifecycle_argv(tmp_path=tmp_path, extra=[]))
    assert exit_code == 0
    assert capsys.readouterr().out == _SKIPPED_DOCUMENT
    assert len(lifecycle_doctor_calls) == 1


def test_critique_run_pre_check_overrides_config_key_true(
    *,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    lifecycle_doctor_calls: list[list[str]],
) -> None:
    """`--run-pre-check` forces the pre-step even when config says skip."""
    _write_skip_config(tmp_path=tmp_path, skip=True)
    exit_code = critique.main(
        argv=_critique_lifecycle_argv(tmp_path=tmp_path, extra=["--run-pre-check"]),
    )
    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert len(lifecycle_doctor_calls) == 2


def test_critique_rejects_both_pre_check_flags_with_usage_exit(
    *,
    tmp_path: Path,
    lifecycle_doctor_calls: list[list[str]],
) -> None:
    """Both flags together are an argparse usage error: exit 2, nothing runs."""
    exit_code = critique.main(
        argv=_critique_lifecycle_argv(
            tmp_path=tmp_path,
            extra=["--skip-pre-check", "--run-pre-check"],
        ),
    )
    assert exit_code == 2
    assert lifecycle_doctor_calls == []
    assert list((tmp_path / "SPECIFICATION").iterdir()) == []


def test_critique_pre_step_doctor_fail_aborts_before_write(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fail finding from the pre-step doctor exits 3 and writes nothing."""

    def _failing(*, argv: list[str], cwd: Path | None = None) -> _DoctorRun:
        del cwd
        return IOResult.from_value(
            subprocess.CompletedProcess(
                args=argv,
                returncode=3,
                stdout='{"findings": [{"check_id": "x", "status": "fail", "message": "m"}]}',
            ),
        )

    monkeypatch.setattr(proc, "run_subprocess", _failing)
    exit_code = critique.main(argv=_critique_lifecycle_argv(tmp_path=tmp_path, extra=[]))
    assert exit_code == 3
    assert list((tmp_path / "SPECIFICATION").iterdir()) == []
