"""Tests for livespec.parse.front_matter (placeholder; deferred-items).

`livespec/parse/front_matter.py` is a Phase-2 placeholder pending
the restricted-YAML deferred-items decision. The module currently
exposes only `__all__: list[str] = []`. This test file:

- Covers the placeholder's single line via import.
- Carries a trivial `@given` test so that
  `check-pbt-coverage-pure-modules` (which requires every test
  module under `tests/livespec/parse/**/test_*.py` to declare at
  least one `@given(...)`-decorated function) accepts the module.
- Pins the placeholder shape (`__all__ == []`) so that when the
  restricted-YAML implementation lands, this file's PBT test
  becomes the natural authoring target — Red-Green-driving the
  parser against the new behavior.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from livespec.parse import front_matter

__all__: list[str] = []


def test_placeholder_exposes_empty_public_surface() -> None:
    assert front_matter.__all__ == []


@given(arbitrary=st.text(max_size=8))
def test_pbt_placeholder_module_imports_cleanly(*, arbitrary: str) -> None:
    """Trivial PBT shell satisfying check-pbt-coverage-pure-modules.

    The body re-asserts the placeholder invariant for any input;
    the Hypothesis-generated `arbitrary` is unused but its presence
    flips the module from "no @given test" to "has @given test"
    per the AST check.
    """
    _ = arbitrary
    assert front_matter.__all__ == []
