"""argparse boundary facade.

Per style doc §"CLI argument parsing seam": construction lives
in `commands/<cmd>.py:build_parser()` (pure factory); parsing
lives here under `@impure_safe`. `parse_argv` returns
`IOResult[Namespace, UsageError | HelpRequested]` once those
failure-track classes are pulled in by consumer pressure.

Cycle 67 lands the success path only — IOSuccess(Namespace) on
valid argv. Subsequent cycles drive UsageError on argparse
errors and HelpRequested on `-h`/`--help`.
"""

from __future__ import annotations

import argparse

from returns.io import impure_safe

__all__: list[str] = ["parse_argv"]


@impure_safe(exceptions=(argparse.ArgumentError,))
def parse_argv(
    *,
    parser: argparse.ArgumentParser,
    argv: list[str],
) -> argparse.Namespace:
    """Parse argv against parser, lifting argparse errors onto IOResult.

    `@impure_safe` converts the explicit `ArgumentError` raise
    path (only possible because `build_parser` sets
    `exit_on_error=False`) into a Failure carrying the raw
    exception; subsequent cycles will `.alt(...)` that into a
    `UsageError` per the canonical pattern in
    `livespec/parse/jsonc.py`.
    """
    return parser.parse_args(argv)
