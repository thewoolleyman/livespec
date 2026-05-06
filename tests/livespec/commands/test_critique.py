"""Tests for livespec.commands.critique.

Per and Plan Phase 3
: critique is minimum-viable per v019 Q1 —
invokes propose_change internally with the `-critique`
reserve-suffix appended. Full LLM-driven critique flow lives at
SKILL.md prose level, not in the wrapper.
"""

from __future__ import annotations

from pathlib import Path

from livespec.commands import critique

__all__: list[str] = []


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
    exit 3 via err.exit_code per style doc §"Exit code contract".
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
    bind chaining; exit 4 per style doc §"Exit code contract".
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

     Per Plan Phase 3
    : critique delegates to propose_change with
     topic hint `<author>` plus the reserve-suffix `"-critique"`.
     Phase-3 minimum-viable scope: with `--author claude-opus-4-7`
     (already canonical), the resulting filename is
     `claude-opus-4-7-critique.md`. The body is the same one-
     proposal-section-per-finding shape as propose_change's
     output (per PROPOSAL.md, field-copy mapping).
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

    Per spec.md §"Author identifier resolution" step 2: with no
    `--author` flag, the env var `LIVESPEC_AUTHOR_LLM` is
    consulted before falling through to step 3 (payload author)
    or step 4 ("unknown-llm"). Asserts the resulting file lands
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

    Per spec.md §"Author identifier resolution" step 3: with no
    `--author` flag and no `LIVESPEC_AUTHOR_LLM` env var, the
    payload's top-level `author` field is consulted before
    falling through to "unknown-llm". Asserts the resulting file
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

    Per spec.md §"Author identifier resolution" step 1: `--author
    <id>` on the CLI takes precedence over `LIVESPEC_AUTHOR_LLM`
    (step 2) and the payload's `author` field (step 3). With all
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

    Per spec.md §"`critique` internal delegation": critique
    passes the un-slugged resolved-author stem as topic-hint AND
    the literal `"-critique"` as the reserve-suffix parameter to
    propose_change. propose_change's reserve-suffix
    canonicalization (v016 P3 / v017 Q1) truncates the
    non-suffix portion to `64 - len("-critique")` = 55 chars
    then re-appends the suffix, guaranteeing the suffix is
    preserved intact at the 64-char cap. With `--author` =
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
