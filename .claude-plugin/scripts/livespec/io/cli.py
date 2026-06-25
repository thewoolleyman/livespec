# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""argparse boundary facade.

Per style doc: construction lives in `commands/<cmd>.py:build_parser()`
(pure factory); parsing
lives here under `@impure_safe`. `parse_argv` returns
`IOResult[Namespace, UsageError | HelpRequested]` once those
failure-track classes are pulled in by consumer pressure.

Cycles 67-68 land the success path + UsageError mapping for
argparse's ArgumentError-class failures (type-conversion). The
SystemExit case (missing required flags / unknown flags) is
covered by a separate cycle since `exit_on_error=False` does
not suppress those paths in stdlib argparse. HelpRequested
(`-h`/`--help`) lands when the supervisor needs it.
"""

from __future__ import annotations

import argparse

from returns.io import IOResult, impure_safe

from livespec.errors import HelpRequestedError, UsageError

__all__: list[str] = ["parse_argv"]


@impure_safe(exceptions=(argparse.ArgumentError, SystemExit))  # pyright: ignore[reportArgumentType]
def _raw_parse_argv(
    *,
    parser: argparse.ArgumentParser,
    argv: list[str],
) -> argparse.Namespace:
    """Decorator-lifted call into argparse. The IOFailure carries the
    raw ArgumentError or SystemExit; `parse_argv` maps both to
    UsageError via .alt.

    Why catch SystemExit: stdlib argparse's `exit_on_error=False`
    only suppresses ArgumentError-class failures (type
    conversion). Missing-required-arg and unknown-flag both
    route through `parser.error()` -> `parser.exit()` ->
    `sys.exit(2)`, which `exit_on_error=False` does NOT
    intercept (Python issue 41255). Catching SystemExit here
    keeps the railway intact.
    """
    return parser.parse_args(argv)


def parse_argv(
    *,
    parser: argparse.ArgumentParser,
    argv: list[str],
) -> IOResult[argparse.Namespace, HelpRequestedError | UsageError]:
    """Parse argv, lifting argparse errors onto the IOResult track.

    `@impure_safe` converts the explicit `ArgumentError` raise
    path (only possible because `build_parser` sets
    `exit_on_error=False`) into an IOFailure carrying the raw
    exception; `.alt(...)` then maps that to a UsageError per
    the canonical pattern in `livespec/parse/jsonc.py`.
    """
    return _raw_parse_argv(parser=parser, argv=argv).alt(_map_parse_error)


def _map_parse_error(exc: argparse.ArgumentError | SystemExit) -> HelpRequestedError | UsageError:
    """Map argparse's exception-shaped exits to domain errors."""
    if isinstance(exc, SystemExit) and exc.code == 0:
        return HelpRequestedError("argparse: help requested")
    return UsageError(f"argparse: {exc}")
