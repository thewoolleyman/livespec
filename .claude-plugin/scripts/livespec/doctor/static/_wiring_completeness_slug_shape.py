"""Interpret canonical-check slug values across the fleet's pin transition.

This small boundary stays separate from the general cross-repo helpers so adding
compatibility logic cannot push that already substantial module over its LLOC gate.
"""

from __future__ import annotations

from typing import cast

__all__: list[str] = ["slugs_from_either_shape"]


def slugs_from_either_shape(*, value: object) -> tuple[str, ...] | None:
    """Read a bare tuple or successful ``IOResult``; return None if unavailable.

    ``canonical_check_slugs`` is converting from ``tuple[str, ...]`` to
    ``IOResult``. Supporting both shapes keeps this check correct across staggered
    fleet pin bumps and a possible revert.

    The discrimination must be on type: ``bool(IOFailure(...))`` is true. A failure
    also maps to None, never ``()``, because callers interpret None as unavailable
    and an empty tuple as an authoritative empty canonical-check set.

    This cannot share ``dev-tooling/checks/_canonical_slug_shape.py``: the plugin
    imports under bare ``python3``, where neither ``livespec_dev_tooling`` nor
    ``returns`` is guaranteed to be importable. The lazy import preserves that flow.
    """
    if isinstance(value, tuple):
        return tuple(str(slug) for slug in cast("tuple[object, ...]", value))
    try:
        from returns.io import IOSuccess
        from returns.unsafe import unsafe_perform_io
    except ModuleNotFoundError:  # pragma: no cover — bare-python3 plugin flow.
        return None
    if not isinstance(value, IOSuccess):
        return None
    # ``IOResult.unwrap()`` returns ``IO[T]``; performing that IO is load-bearing.
    success = cast("IOSuccess[tuple[object, ...]]", value)
    unwrapped = unsafe_perform_io(success.unwrap())
    return tuple(str(slug) for slug in unwrapped)
