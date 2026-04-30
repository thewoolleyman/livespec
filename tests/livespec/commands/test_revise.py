"""Tests for livespec.commands.revise.

Per PROPOSAL.md §"`revise`" (line ~2335) and Plan Phase 3
(lines 1533-1553): revise is minimum-viable per v019 Q1 —
validate `--revise-json` payload, process per-proposal
`decisions[]` in payload order, write paired
`<stem>-revision.md`, move processed proposed-change files into
`history/vNNN/proposed_changes/`, cut new `history/vNNN/`.
"""

from __future__ import annotations

from pathlib import Path

from livespec.commands import revise

__all__: list[str] = []


def test_revise_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/revise.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature.
    """
    exit_code = revise.main(argv=["--revise-json", "/tmp/x.json"])
    assert isinstance(exit_code, int)


def test_revise_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing required `--revise-json <path>` returns exit code 2.

    Per PROPOSAL.md §"`revise`" lines 2375-2410: the wrapper
    requires `--revise-json <path>` (plus optional `--author
    <id>`, `--spec-target <path>`, `--project-root <path>`).
    Drives the first real railway-composition behavior by
    threading argv through io/cli.parse_argv and pattern-matching
    the IOFailure(UsageError) onto err.exit_code (= 2).
    """
    exit_code = revise.main(argv=[])
    assert exit_code == 2


def test_revise_main_returns_precondition_exit_code_on_missing_revise_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --revise-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to the supervisor's pattern-match, which lifts to
    exit 3 via err.exit_code per style doc §"Exit code contract".
    Mirrors propose_change/critique's same railway stage.
    """
    missing = tmp_path / "no-such-revise.json"
    exit_code = revise.main(argv=["--revise-json", str(missing)])
    assert exit_code == 3


def _write_valid_revise_payload(*, tmp_path: Path) -> Path:
    """Helper: write a schema-valid revise-input payload to tmp_path.

    Mirrors propose_change/critique helpers: the payload conforms
    to revise_input.schema.json with one reject-decision so the
    railway can reach the Success arm without needing the
    accept/modify file-shaping branches yet.
    """
    import json

    payload_dict = {
        "decisions": [
            {
                "proposal_topic": "demo",
                "decision": "reject",
                "rationale": "Demo rejection rationale.",
            },
        ],
    }
    payload_path = tmp_path / "revise.json"
    _ = payload_path.write_text(json.dumps(payload_dict), encoding="utf-8")
    return payload_path


def test_revise_main_returns_zero_when_revise_file_readable(
    *,
    tmp_path: Path,
) -> None:
    """When --revise-json points at a schema-valid payload, main returns 0.

    Drives the Success arm of `_pattern_match_io_result`: the
    parse_argv -> fs.read_text -> jsonc.loads -> validate
    composition reaches IOSuccess, the pattern-match falls into
    the Success(_) case, and the supervisor returns 0. Subsequent
    cycles append per-decision processing.
    """
    revise_path = _write_valid_revise_payload(tmp_path=tmp_path)
    exit_code = revise.main(argv=["--revise-json", str(revise_path)])
    assert exit_code == 0


def test_revise_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) bubbles via
    bind chaining; exit 4 per style doc §"Exit code contract".
    Mirrors critique's cycle-120 stage.
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = revise.main(argv=["--revise-json", str(payload)])
    assert exit_code == 4


def test_revise_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives the railway widening to include schema validation
    against revise_input.schema.json. The payload `{}` is valid
    JSON so jsonc.loads succeeds; it then trips schema validation
    (missing required `decisions` array) which returns
    Failure(ValidationError) and lifts to exit 4. Mirrors
    critique's cycle-121 stage.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = revise.main(argv=["--revise-json", str(payload)])
    assert exit_code == 4
