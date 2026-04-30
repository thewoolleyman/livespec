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


def test_revise_main_returns_zero_when_revise_file_readable(
    *,
    tmp_path: Path,
) -> None:
    """When --revise-json points at a readable file, main returns 0.

    Drives the Success arm of `_pattern_match_io_result`: the
    parse_argv -> fs.read_text composition reaches IOSuccess, the
    pattern-match falls into the Success(_) case, and the
    supervisor returns 0. Subsequent cycles append jsonc.loads,
    schema validation, and per-decision processing; once those
    land, this test will need a richer payload to reach success.
    """
    revise_path = tmp_path / "revise.json"
    _ = revise_path.write_text("{}", encoding="utf-8")
    exit_code = revise.main(argv=["--revise-json", str(revise_path)])
    assert exit_code == 0
