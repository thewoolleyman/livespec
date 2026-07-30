"""Unit test for `_canonical_slug_shape` — the dual-shape read of canonical_check_slugs.

`livespec-dev-tooling-vzwa` converts `canonical_check_slugs()` from a bare
`tuple[str, ...]` to an `IOResult`. This consumer-side reader lands FIRST so the pin
is free to move in EITHER direction, per `.ai/ci-gate-discipline.md` step 3 and the
cost recorded on `livespec-dev-tooling-dx8l`.

**BOTH SHAPES ARE EXERCISED, because wiring for a shape nothing exercises is how the
silent pass ships.** The load-bearing assertion is not "it returned something" — it
is that an `IOSuccess` unwraps **TO ITS VALUE**, since asserting the call merely
succeeded is exactly what the `dx8l` bug also satisfied.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
if str(_CHECKS_DIR) not in sys.path:
    sys.path.insert(0, str(_CHECKS_DIR))

from _canonical_slug_shape import slugs_from_either_shape  # noqa: E402

__all__: list[str] = []

_SLUGS = ("check-alpha", "check-beta")


def test_a_bare_tuple_is_read_unchanged() -> None:
    """Today's pin: a bare tuple passes through as the slug set."""
    assert slugs_from_either_shape(value=_SLUGS) == _SLUGS


def test_an_empty_bare_tuple_stays_empty_rather_than_becoming_none() -> None:
    """An empty tuple is NOT re-read as unavailable.

    Today's `canonical_check_slugs()` returns `()` on a missing package directory —
    the very fail-open `vzwa` removes — and this reader must not paper over it by
    silently converting it to None. Under the OLD pin an empty tuple is what the
    substrate actually said, and the caller's existing behavior is preserved
    unchanged. Only the NEW shape's failure track maps to None.
    """
    assert slugs_from_either_shape(value=()) == ()


def test_an_io_success_unwraps_to_its_value() -> None:
    """Post-conversion: the LOAD-BEARING assertion.

    Not "it returned something" — that is what the `dx8l` bug also satisfied. This
    pins that the actual slug strings come back, which is what fails if a caller
    reaches for `.unwrap()` without `unsafe_perform_io` and gets an `IO` container.
    """
    from returns.io import IOSuccess

    assert slugs_from_either_shape(value=IOSuccess(_SLUGS)) == _SLUGS


def test_an_io_failure_is_unavailable_not_an_empty_slug_set() -> None:
    """A failure track maps to None, NEVER to `()`.

    `()` would be read by every consumer as "this repo has no canonical checks",
    which PASSES — the exact fail-open `vzwa` exists to remove, reintroduced one
    level up in the consumer.
    """
    from returns.io import IOFailure

    assert slugs_from_either_shape(value=IOFailure("checks package unreadable")) is None


def test_a_failure_is_truthy_so_a_boolean_guard_would_not_have_worked() -> None:
    """The `dx8l` trap, pinned as a property rather than trusted as a memory.

    `bool(IOFailure(...))` is **True** and it is not None, so `if value:`,
    `if not value:` and `if value is None:` are ALL wrong discriminators. This test
    exists so that a later editor who simplifies the reader to a boolean check sees
    a red test naming the reason, rather than shipping a guard that has silently
    stopped guarding.
    """
    from returns.io import IOFailure

    failure = IOFailure("checks package unreadable")
    assert bool(failure) is True
    assert failure is not None
    assert slugs_from_either_shape(value=failure) is None


def test_an_unrecognized_shape_is_unavailable_rather_than_assumed() -> None:
    """Doubt maps to None — the strict direction for a slug set."""
    assert slugs_from_either_shape(value="check-alpha") is None
    assert slugs_from_either_shape(value=None) is None
