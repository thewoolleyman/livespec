"""Tests for livespec.commands.critique.

Per PROPOSAL.md §"`critique`" (line ~2280) and Plan Phase 3
(lines 1524-1532): critique is minimum-viable per v019 Q1 —
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

    Per PROPOSAL.md §"`critique`" (lines 2287-2293): the wrapper
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


def test_critique_main_returns_zero_when_findings_file_readable(
    *,
    tmp_path: Path,
) -> None:
    """When --findings-json points at a readable, valid payload, main returns 0.

    Drives the Success arm of `_pattern_match_io_result`: the
    parse_argv -> fs.read_text -> jsonc.loads composition reaches
    IOSuccess, the pattern-match falls into the Success(_) case,
    and the supervisor returns 0. Subsequent cycles append schema
    validation and propose_change-delegation.
    """
    findings_path = tmp_path / "findings.json"
    _ = findings_path.write_text("{}", encoding="utf-8")
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
