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

from pathlib import Path

from livespec.commands import propose_change

__all__: list[str] = []


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
