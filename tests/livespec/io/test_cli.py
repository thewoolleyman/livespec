"""Tests for livespec.io.cli.

Per style doc §"CLI argument parsing seam": the io/cli facade
wraps argparse's parse-args call with `@impure_safe`, returning
`IOResult[Namespace, UsageError | HelpRequested]`. Construction
stays pure (commands/<cmd>.py:build_parser()); parsing is the
impure act that the io facade owns.
"""

from __future__ import annotations

import argparse

from livespec.errors import UsageError
from livespec.io import cli
from returns.io import IOSuccess
from returns.result import Failure
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def test_cli_parse_argv_returns_iosuccess_on_valid_args() -> None:
    """`parse_argv` returns IOSuccess(Namespace(...)) when argparse accepts the args.

    Smallest behavior: a parser with one optional flag, valid
    argv, IOSuccess. Failure-track behavior (UsageError /
    HelpRequested) is driven by future cycles under consumer
    pressure.
    """
    parser = argparse.ArgumentParser(prog="t", exit_on_error=False)
    _ = parser.add_argument("--flag")
    result = cli.parse_argv(parser=parser, argv=["--flag", "value"])
    expected = argparse.Namespace(flag="value")
    assert result == IOSuccess(expected)


def test_cli_parse_argv_maps_argparse_error_to_usage_error() -> None:
    """argparse's ArgumentError lifts to IOFailure(UsageError(...)).

    Per style doc §"CLI argument parsing seam": parse_argv's
    failure track is `UsageError | HelpRequested`. With
    `exit_on_error=False`, argparse raises ArgumentError on
    type-conversion failures (the case this test pins); pre-
    detection of `-h`/`--help` and SystemExit-on-missing-
    required handling are driven by separate cycles.
    """
    parser = argparse.ArgumentParser(prog="t", exit_on_error=False)
    _ = parser.add_argument("--n", type=int)
    result = cli.parse_argv(parser=parser, argv=["--n", "notint"])
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(UsageError()):
            pass
        case _:
            raise AssertionError(f"expected IOFailure(UsageError), got {result!r}")


def test_cli_parse_argv_maps_missing_required_to_usage_error() -> None:
    """Missing required flag (argparse's SystemExit-via-error path) lifts to UsageError.

    `argparse.ArgumentParser(exit_on_error=False)` does not
    suppress SystemExit on missing-required-argument; argparse
    routes through `parser.error()` which calls `sys.exit(2)`.
    parse_argv MUST also catch that path so the supervisor sees
    a clean IOFailure(UsageError) instead of a propagated
    SystemExit (which would bypass the railway).
    """
    parser = argparse.ArgumentParser(prog="t", exit_on_error=False)
    _ = parser.add_argument("--required", required=True)
    result = cli.parse_argv(parser=parser, argv=[])
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Failure(UsageError()):
            pass
        case _:
            raise AssertionError(f"expected IOFailure(UsageError), got {result!r}")
