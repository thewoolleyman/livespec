"""CLI parsing wrappers (`@impure_safe`, `exit_on_error=False`).

argparse is the sole CLI parser, and it lives here in `io/`.
Rationale (per style doc §"CLI argument parsing seam"):

- `ArgumentParser.parse_args()` calls `sys.exit` on usage errors
  and on `-h`/`--help`. The 6-statement shebang-wrapper shape
  has no room for an exit-trapping wrapper, and
  `check-supervisor-discipline` forbids `SystemExit` outside
  `bin/*.py`.
- Routing argparse through the `io/` impure boundary keeps the
  ROP railway intact: usage errors flow as `IOFailure(UsageError)`
  on the failure track; `-h`/`--help` flows as
  `IOFailure(HelpRequested(text=...))` — also a failure-track
  payload but pattern-matched into an exit-0 success path by the
  supervisor (see style doc §"Structural pattern matching →
  HelpRequested example").

`exit_on_error=False` (Python 3.9+) makes `parse_args` raise
`argparse.ArgumentError` on usage errors instead of calling
`sys.exit(2)`. `--help` still calls `sys.exit(0)` even with
`exit_on_error=False`, so we detect `-h`/`--help` explicitly
before invoking `parse_args` and short-circuit with
`HelpRequested` carrying `parser.format_help()`.

The pure parser factories `build_parser() -> ArgumentParser` live
in `livespec/commands/<cmd>.py` (verified by
`check-build-parser-purity`). This module's job is the impure
invocation; parser construction stays pure.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence

from returns.io import impure_safe

from livespec.errors import HelpRequested, UsageError

__all__: list[str] = [
    "parse_args",
]


@impure_safe(exceptions=(HelpRequested, UsageError))
def parse_args(
    *,
    parser: argparse.ArgumentParser,
    argv: Sequence[str],
) -> argparse.Namespace:
    """Run `parser.parse_args(argv)` through the impure boundary.

    `parser` MUST have been constructed with `exit_on_error=False`
    by the caller's pure `build_parser()` factory; this function
    asserts that invariant. Returns:

    - `IOSuccess(Namespace)` on successful parse.
    - `IOFailure(HelpRequested(text=parser.format_help()))` when
      `-h` or `--help` appears anywhere in `argv` (detected before
      `parse_args` runs to avoid argparse's implicit `sys.exit(0)`).
    - `IOFailure(UsageError(<argparse message>))` on any usage
      failure (unrecognized flag, missing required arg, type
      coercion failure, mutually-exclusive violation, etc.).
    """
    if parser.exit_on_error:
        raise UsageError(
            "build_parser() must construct ArgumentParser with exit_on_error=False",
        )
    if any(token in {"-h", "--help"} for token in argv):
        raise HelpRequested(text=parser.format_help())
    try:
        return parser.parse_args(list(argv))
    except argparse.ArgumentError as e:
        raise UsageError(str(e)) from e
    except argparse.ArgumentTypeError as e:
        raise UsageError(str(e)) from e
