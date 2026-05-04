"""Tests for livespec.commands.propose_change.

Per PROPOSAL.md §"`propose-change`" (line ~2134) and Plan
Phase 3 (lines 1505-1523), propose-change is the second
sub-command authored under TDD. Phase-3 minimum-viable scope:
validate the inbound `--findings-json <path>` payload against
proposal_findings.schema.json, compose a proposed-change file
from the findings, write it to
`<spec-target>/proposed_changes/<topic>.md`. Topic-canonical-
ization is OUT OF SCOPE for Phase 3.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.commands import propose_change

__all__: list[str] = []


def _write_valid_findings_payload(*, tmp_path: Path) -> Path:
    """Helper: write a schema-valid proposal-findings payload to tmp_path.

    Used by success-arm tests to satisfy the parse_argv ->
    read_text -> jsonc.loads -> validate_proposal_findings
    chain so the railway reaches the file-write stage.
    """
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


def test_propose_change_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/propose_change.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = propose_change.main(argv=["--findings-json", "/tmp/x.json", "topic"])
    assert isinstance(exit_code, int)


def test_propose_change_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing required args (UsageError) returns exit code 2.

    Per PROPOSAL.md §"`propose-change`" lines 2149-2155: the
    wrapper requires `--findings-json <path>` plus a positional
    `<topic>`. Drives the first real railway-composition behavior
    by threading argv through io/cli.parse_argv and pattern-
    matching the IOFailure(UsageError) onto err.exit_code.
    """
    exit_code = propose_change.main(argv=[])
    assert exit_code == 2


def test_propose_change_main_returns_precondition_exit_code_on_missing_findings_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --findings-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to the supervisor's pattern-match, which lifts to
    exit 3 via err.exit_code per style doc §"Exit code contract".
    """
    missing = tmp_path / "no-such-findings.json"
    exit_code = propose_change.main(argv=["--findings-json", str(missing), "topic"])
    assert exit_code == 3


def test_propose_change_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) bubbles
    via bind chaining; exit 4 per style doc §"Exit code
    contract".
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = propose_change.main(argv=["--findings-json", str(payload), "topic"])
    assert exit_code == 4


def test_propose_change_main_writes_proposed_change_file_on_success(
    *,
    tmp_path: Path,
) -> None:
    """Successful propose-change writes `<spec-target>/proposed_changes/<topic>.md`.

    Per PROPOSAL.md §"`propose-change`" lines 2145-2148: the
    wrapper creates a proposed-change file containing one or
    more `## Proposal: <name>` sections. With --spec-target
    explicit, the target is `<spec-target>/proposed_changes/
    <topic>.md`. The body composes from the findings array via
    the field-copy mapping in PROPOSAL.md lines 2232-2242.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    _ = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "demo-topic",
        ],
    )
    out = spec_target / "proposed_changes" / "demo-topic.md"
    assert out.exists(), f"expected {out} to be written"
    text = out.read_text(encoding="utf-8")
    assert "## Proposal: Sample finding" in text
    assert "Demo summary." in text
    assert "Demo motivation." in text
    assert "Demo changes prose." in text


def test_propose_change_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives the railway widening to include schema validation:
    parse_argv -> read_text -> jsonc.loads -> validate against
    proposal_findings.schema.json. The payload `{}` is valid
    JSON so jsonc.loads succeeds; it then trips schema
    validation (missing required `findings` array) which
    returns Failure(ValidationError) and lifts to exit 4.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = propose_change.main(argv=["--findings-json", str(payload), "topic"])
    assert exit_code == 4


def test_propose_change_canonicalizes_topic_lowercase_and_hyphens(
    *,
    tmp_path: Path,
) -> None:
    """Inbound topic with uppercase + spaces canonicalizes to slug filename.

    Per SPECIFICATION/spec.md "Topic canonicalization (v015 O3)": the
    wrapper canonicalizes the inbound topic before filename selection
    via lowercase -> non-[a-z0-9]-runs-to-hyphen -> strip-edges ->
    truncate-64. Drives the canonicalization helper into propose_change
    and proves the canonical form is what lands on disk.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "Foo Bar!!",
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "foo-bar.md"
    assert out.exists(), f"expected canonicalized {out} to be written"


def test_propose_change_main_returns_usage_exit_code_on_empty_after_canonicalization(
    *,
    tmp_path: Path,
) -> None:
    """Topic that canonicalizes to empty string returns exit 2 (UsageError).

    Per SPECIFICATION/spec.md "Topic canonicalization (v015 O3)": "If the
    result is empty, the wrapper exits 2 with `UsageError`." A topic of
    only non-[a-z0-9] characters (e.g. `"!!!"`) canonicalizes through
    the regex to a string of hyphens, which strip("-") empties; the
    empty result short-circuits to IOFailure(UsageError) on the railway.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "!!!",
        ],
    )
    assert exit_code == 2


def test_propose_change_appends_reserve_suffix_to_canonical_topic(
    *,
    tmp_path: Path,
) -> None:
    """`--reserve-suffix critique` produces `<canonical-hint>-critique.md`.

    Per SPECIFICATION/spec.md "Reserve-suffix canonicalization (v016 P3 /
    v017 Q1)" and the deferred-items.md "Reserve-suffix topic
    canonicalization" algorithm: when the flag is supplied, the wrapper
    canonicalizes the hint, canonicalizes the suffix, and re-appends the
    canonical suffix verbatim. Drives `--reserve-suffix` parser wiring
    and the new branch of `_canonicalize_topic`.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "--reserve-suffix=-critique",
            "Foo Bar",
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "foo-bar-critique.md"
    assert out.exists(), f"expected {out} to be written"


def test_propose_change_with_reserve_suffix_strips_pre_attached_suffix(
    *,
    tmp_path: Path,
) -> None:
    """A topic hint pre-ending with the reserve suffix is not duplicated.

    Per the v016 P3 algorithm step 3: "If <canonical-hint> already ends
    in <canonical-suffix>, strip the trailing suffix from
    <canonical-hint> before truncation." Drives the endswith branch
    of the reserve-suffix path.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "--reserve-suffix=-critique",
            "Claude Opus 4.7-critique",
        ],
    )
    assert exit_code == 0
    out = spec_target / "proposed_changes" / "claude-opus-4-7-critique.md"
    assert out.exists(), f"expected pre-attached-suffix-stripped {out} to be written"


def test_propose_change_with_reserve_suffix_truncates_to_sixty_four_chars(
    *,
    tmp_path: Path,
) -> None:
    """Long hint + reserve suffix yields a result of at most 64 chars.

    Per the v016 P3 algorithm step 4: "Truncate the resulting non-suffix
    portion to `64 - len(<canonical-suffix>)` characters; strip
    trailing hyphens left behind by the truncation." With suffix
    `-critique` (9 chars), the non-suffix budget is 55 chars; the
    composed result is exactly 64 chars and ends with `-critique`.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    long_hint = "An unusually long author identifier that keeps going and going past fifty"
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "--reserve-suffix=-critique",
            long_hint,
        ],
    )
    assert exit_code == 0
    written = list((spec_target / "proposed_changes").iterdir())
    assert len(written) == 1
    out = written[0]
    stem = out.stem
    assert len(stem) <= 64
    assert stem.endswith("-critique")
    assert stem == "an-unusually-long-author-identifier-that-keeps-going-an-critique"


def test_propose_change_with_reserve_suffix_returns_usage_on_empty_hint(
    *,
    tmp_path: Path,
) -> None:
    """Empty-after-canonicalization hint with reserve-suffix exits 2.

    Per the v016 P3 algorithm: when the truncated non-suffix portion
    is empty, the resulting filename would consist only of the
    reserve-suffix and would not anchor to a meaningful artifact name;
    the wrapper short-circuits to UsageError on the railway. Drives the
    `if not truncated_hint` branch of the reserve-suffix path.
    """
    spec_target = tmp_path / "spec-root"
    spec_target.mkdir()
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    exit_code = propose_change.main(
        argv=[
            "--findings-json",
            str(payload_path),
            "--spec-target",
            str(spec_target),
            "--reserve-suffix=-critique",
            "!!!",
        ],
    )
    assert exit_code == 2


def test_propose_change_main_defaults_spec_target_to_cwd_specification_when_no_flags(
    *,
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    """Without --spec-target or --project-root, falls back to `cwd()/SPECIFICATION`.

    Per PROPOSAL.md §"Wrapper CLI surface" lines 349-356 + Plan
    Phase 3: when neither --spec-target nor --project-root is
    supplied, project_root defaults to Path.cwd() and the spec
    target derives as `<cwd>/SPECIFICATION`. Drives
    `_resolve_spec_target`'s cwd-fallback branch (line 145:
    `Path.cwd() if namespace.project_root is None`) — the
    last uncovered code path in the file. Uses monkeypatch to
    chdir into tmp_path so the cwd-read at the supervisor edge
    points at a writable, deterministic root rather than the
    test runner's invocation cwd.
    """
    import pytest

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    project_root = tmp_path / "proj"
    (project_root / "SPECIFICATION").mkdir(parents=True)
    payload_path = _write_valid_findings_payload(tmp_path=tmp_path)
    monkeypatch.chdir(project_root)
    exit_code = propose_change.main(
        argv=["--findings-json", str(payload_path), "demo-topic"],
    )
    assert exit_code == 0
    out = project_root / "SPECIFICATION" / "proposed_changes" / "demo-topic.md"
    assert out.exists(), f"expected {out} to be written"
