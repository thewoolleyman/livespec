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

Property names match
SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
semantic-property catalogue". Phase 7 item (d) per-prompt
regeneration cycles widen this registry alongside the catalogue
per the in-line widening rule (Plan §3543-3550).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

__all__: list[str] = ["ASSERTIONS"]


def _sub_specs_always_empty(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """`replayed_response.sub_specs` is always `[]` for the minimal template.

    Per SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/seed.md", the minimal
    template implements the v020 Q2 opt-out — sub_specs MUST be
    empty regardless of any pre-seed dialogue input.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    sub_specs = payload.get("sub_specs", [])
    if len(sub_specs) != 0:
        raise AssertionError(
            f"minimal-template seed replayed_response.sub_specs "
            f"MUST be empty per the v020 Q2 opt-out, but has "
            f"{len(sub_specs)} entries",
        )


def _single_specification_md_file(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """`replayed_response.files[]` is exactly one entry with path "SPECIFICATION.md".

    Per SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/seed.md", the minimal
    template ships a single-file SPECIFICATION.md output (per the
    template's `spec_root: "./"` + single-file positioning).
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    files = payload.get("files", [])
    if len(files) != 1:
        raise AssertionError(
            f"minimal-template seed replayed_response.files[] "
            f"MUST have exactly 1 entry, got {len(files)}",
        )
    path = files[0].get("path")
    if path != "SPECIFICATION.md":
        raise AssertionError(
            f"minimal-template seed replayed_response.files[0].path "
            f"MUST equal 'SPECIFICATION.md', got {path!r}",
        )


ASSERTIONS: dict[str, Callable[..., None]] = {
    "sub_specs_always_empty": _sub_specs_always_empty,
    "single_specification_md_file": _single_specification_md_file,
}
