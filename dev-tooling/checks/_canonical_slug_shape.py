"""_canonical_slug_shape — read `canonical_check_slugs()` under EITHER return shape.

`livespec_dev_tooling.canonical_checks.canonical_check_slugs` is scheduled to
convert from a bare `tuple[str, ...]` to an `IOResult[tuple[str, ...], …]`
(`livespec-dev-tooling-vzwa`). It reaches the filesystem transitively through
`_discover_slugs` → `pkgutil.iter_modules`, so ratified livespec v179 member 1
reaches it and the Result-return rule applies.

**THIS MODULE LANDS BEFORE THAT CONVERSION, DELIBERATELY, AND IT IS WHY.** The
auto-merge pin-bump fan-out delivers a dev-tooling change to this repo within
minutes with nobody deciding, so a consumer that only understands the OLD shape
breaks on the bump and a consumer that only understands the NEW shape breaks on a
REVERT. Reading both makes the pin free to move in either direction — the property
a sequenced fix would not have. Precedent and cost:
`livespec-dev-tooling-dx8l`, which turned a sibling's master RED.

## ⛔ THE FAILURE MODE THIS EXISTS TO PREVENT IS NOT AN EXCEPTION

`dx8l`'s consumer did `if manifest is None`. Against a `Result` that test is
permanently False, so the guard did not FAIL — **it silently STOPPED BEING A
GUARD**, and control flowed on into attribute access. Measured on the vendored
copy, `bool(IOFailure(...))` is **True** and an `IOFailure` carries no `.unwrap()`
success value. So every intuitive guard is wrong here:

    if value:              # WRONG — an IOFailure is TRUTHY
    if value is None:      # WRONG — an IOFailure is not None
    if not value:          # WRONG — same, inverted

**The discrimination is on TYPE, explicitly, and nothing else.** A bare `tuple` is
today's pin; anything else is asked whether it is an `IOSuccess`.

## WHY `returns` IS IMPORTED LAZILY

The sibling consumer of this same function
(`doctor/static/wiring_completeness_cross_repo.py`) runs under BARE `python3`,
where neither `livespec_dev_tooling` nor `returns` is importable. This module runs
under `uv`, so it could import eagerly — but the lazy import keeps ONE reading of
the shape question across both environments, and in an environment without
`returns` the value can only ever have been the tuple the first branch already
returned.
"""

from __future__ import annotations

from typing import cast

__all__: list[str] = ["slugs_from_either_shape"]


def slugs_from_either_shape(*, value: object) -> tuple[str, ...] | None:
    """The slug tuple from a bare tuple OR an `IOResult`; None when unavailable.

    Returns None — never a partial or empty tuple — when the value is a failure
    track, because an EMPTY slug tuple is exactly the fail-open this conversion
    exists to remove: every consumer reads "no canonical checks" as a PASS. A
    caller that receives None MUST skip or fail, never proceed with `()`.
    """
    if isinstance(value, tuple):
        # Today's pin. `tuple(...)` re-wraps so a caller cannot mutate a shared
        # object, and `str(...)` per element makes the annotation honest at
        # runtime rather than only to the type checker.
        return tuple(str(slug) for slug in cast("tuple[object, ...]", value))
    from returns.io import IOResult, IOSuccess
    from returns.unsafe import unsafe_perform_io

    if not isinstance(value, IOSuccess):
        return None
    # `unsafe_perform_io` is NOT ceremony: `IOResult.unwrap()` returns `IO[T]`,
    # and `tuple(IO(("a","b")))` SUCCEEDS — yielding a one-element tuple holding
    # the IO container. Every slug comparison downstream would then miss, and
    # nothing would raise. Same trap, same spelling, as `#841`.
    typed = cast("IOResult[tuple[object, ...], object]", value)
    return tuple(str(slug) for slug in unsafe_perform_io(typed.unwrap()))
