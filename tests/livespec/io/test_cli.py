"""Tests for livespec.io.cli.

Per style doc §"CLI argument parsing seam": the io/cli facade
wraps argparse's parse-args call with `@impure_safe`, returning
`IOResult[Namespace, UsageError | HelpRequested]`. Construction
stays pure (commands/<cmd>.py:build_parser()); parsing is the
impure act that the io facade owns.
"""

from __future__ import annotations

import argparse

from returns.io import IOSuccess

from livespec.io import cli

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
