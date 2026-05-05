"""Per-template semantic-property assertion registry for `minimal`.

Maps each property name from a fixture's
`expected_semantic_properties` array to a function that
asserts the property holds for the fixture's `replayed_response`.
Per SPECIFICATION/contracts.md §"Prompt-QA harness contract"
(v014), the registry is populated via explicit imports per the
static-enumeration discipline (no `glob+importlib` dynamic
discovery). Each assertion function MUST accept keyword-only
arguments `*, replayed_response: object, input_context: object`
and raise `AssertionError` on any property violation.

Bootstrap-minimum scope: the registry starts empty and widens
in Phase 7 sub-step (f) per-prompt cycles + the Phase 7 items
(d) per-prompt regeneration cycles. The semantic properties are
codified in SPECIFICATION/templates/minimal/contracts.md
§"Per-prompt semantic-property catalogue".
"""

from __future__ import annotations

from collections.abc import Callable

__all__: list[str] = ["ASSERTIONS"]


ASSERTIONS: dict[str, Callable[..., None]] = {}
