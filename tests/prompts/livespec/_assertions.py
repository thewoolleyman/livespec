"""Per-template semantic-property assertion registry for `livespec`.

Maps each property name from a fixture's
`expected_semantic_properties` array to a function that
asserts the property holds for the fixture's `replayed_response`.
Per SPECIFICATION/contracts.md §"Prompt-QA harness contract"
(v014), the registry is populated via explicit imports per the
static-enumeration discipline (no `glob+importlib` dynamic
discovery). Each assertion function MUST accept keyword-only
arguments `*, replayed_response: object, input_context: object`
and raise `AssertionError` on any property violation.

Property names match
SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
semantic-property catalogue". Phase 7 item (c) per-prompt
regeneration cycles widen this registry alongside the catalogue
per the in-line widening rule (Plan §3543-3550); fixtures
`expected_semantic_properties` lists land in the same revise
commit as their matching assertion functions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

__all__: list[str] = ["ASSERTIONS"]


def _headings_derived_from_intent(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every file in `replayed_response.files[]` has an `# ` H1 header.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/seed.md", each spec file's
    top-level heading MUST be `#` (level 1) reflecting the seed intent.
    The structural assertion verifies the H1 is present; semantic
    intent-derivation is a fuzzier check left to the LLM-driven
    subjective phase of doctor.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    files = payload.get("files", [])
    for entry in files:
        path = entry["path"]
        content = entry["content"]
        first_line = content.lstrip().split("\n", 1)[0]
        if not first_line.startswith("# "):
            raise AssertionError(
                f"file {path} missing `# ` H1 header (first non-blank " f"line was {first_line!r})",
            )


def _asks_v020_q2_question(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """`replayed_response.sub_specs[]` reflects the v020 Q2 dialogue answer.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/seed.md", when the input
    context's `ships_own_templates` is true (with `named_templates`
    listing N entries), the replayed response's `sub_specs` array
    MUST carry exactly N entries; otherwise the array MUST be empty.
    """
    ctx = cast(dict[str, Any], input_context)
    payload = cast(dict[str, Any], replayed_response)
    ships = ctx.get("ships_own_templates", False)
    sub_specs = payload.get("sub_specs", [])
    if ships:
        named = ctx.get("named_templates", [])
        if len(sub_specs) != len(named):
            raise AssertionError(
                f"input_context.ships_own_templates=true with "
                f"named_templates={named!r} but "
                f"replayed_response.sub_specs has {len(sub_specs)} "
                f"entries (expected {len(named)})",
            )
    elif len(sub_specs) != 0:
        raise AssertionError(
            f"input_context.ships_own_templates is false/absent "
            f"but replayed_response.sub_specs has "
            f"{len(sub_specs)} entries (expected 0)",
        )


ASSERTIONS: dict[str, Callable[..., None]] = {
    "headings_derived_from_intent": _headings_derived_from_intent,
    "asks_v020_q2_question": _asks_v020_q2_question,
}
