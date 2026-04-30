"""Tests for livespec.commands.seed.

The seed sub-command is the Phase 3 outermost rail per the
briefing's outside-in walking direction. Cycles drive its
behavior step-by-step from the supervisor entrypoint
(`main(argv)`) inward.
"""

from __future__ import annotations

from pathlib import Path

from livespec.commands import seed

__all__: list[str] = []


def test_seed_main_exists_and_returns_int() -> None:
    """The supervisor entry point exists and returns an int exit code.

    Smallest possible cycle: drives livespec/commands/seed.py
    into existence with the canonical `main(*, argv) -> int`
    supervisor signature. Subsequent cycles widen the body
    behavior-by-behavior.
    """
    exit_code = seed.main(argv=["--seed-json", "/tmp/x.json"])
    assert isinstance(exit_code, int)


def test_seed_main_returns_usage_exit_code_on_missing_required_flag() -> None:
    """Missing --seed-json (UsageError) returns exit code 2.

    Threads argv through io/cli.parse_argv and pattern-matches
    the IOFailure(UsageError) onto its err.exit_code per style
    doc §"Exit code contract". Drives seed.main's first real
    railway-composition behavior.
    """
    exit_code = seed.main(argv=[])
    assert exit_code == 2


def test_seed_main_returns_precondition_exit_code_on_missing_seed_json_path(
    *,
    tmp_path: Path,
) -> None:
    """Missing --seed-json file (PreconditionError) returns exit code 3.

    Composes parse_argv -> fs.read_text on the railway. The
    fs.read_text failure (FileNotFoundError -> PreconditionError)
    bubbles to seed.main's pattern-match, which lifts to exit 3
    via err.exit_code per style doc §"Exit code contract".
    """
    missing = tmp_path / "no-such-payload.json"
    exit_code = seed.main(argv=["--seed-json", str(missing)])
    assert exit_code == 3


def test_seed_main_returns_validation_exit_code_on_malformed_payload(
    *,
    tmp_path: Path,
) -> None:
    """Malformed JSONC payload (ValidationError) returns exit code 4.

    Composes parse_argv -> fs.read_text -> jsonc.loads on the
    railway. The pure parse-failure (ValidationError) reaches
    seed.main's pattern-match through bind chaining; exit 4
    per style doc §"Exit code contract".
    """
    payload = tmp_path / "bad.json"
    _ = payload.write_text("{not json}", encoding="utf-8")
    exit_code = seed.main(argv=["--seed-json", str(payload)])
    assert exit_code == 4


def test_seed_main_returns_validation_exit_code_on_schema_violation(
    *,
    tmp_path: Path,
) -> None:
    """Schema-violation payload (well-formed JSON, missing fields) returns exit 4.

    Drives seed.main's railway widening to include schema
    validation: parse_argv -> read_text -> jsonc.loads ->
    validate_seed_input. The payload `{}` is valid JSON so
    jsonc.loads succeeds; it then trips schema validation
    (missing required `template`/`intent`/`files`/`sub_specs`)
    which returns Failure(ValidationError) and lifts to exit 4.
    """
    payload = tmp_path / "empty.json"
    _ = payload.write_text("{}", encoding="utf-8")
    exit_code = seed.main(argv=["--seed-json", str(payload)])
    assert exit_code == 4


def test_seed_build_parser_accepts_seed_json_flag() -> None:
    """The pure argparse factory accepts `--seed-json <path>` and binds it.

    Per PROPOSAL.md §"`seed`" lines 1937-1942 (`bin/seed.py
    --seed-json <path>` is the sole wrapper entry point) and
    style doc §"CLI argument parsing seam" (commands/<cmd>.py
    exposes a pure `build_parser() -> ArgumentParser` factory
    that constructs but does NOT parse). Constructing-only lets
    us introspect the parser shape without effectful invocation.
    """
    parser = seed.build_parser()
    namespace = parser.parse_args(["--seed-json", "/tmp/payload.json"])
    assert namespace.seed_json == "/tmp/payload.json"
