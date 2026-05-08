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
from pathlib import Path
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


_BCP14_KEYWORDS = ("MUST NOT", "SHOULD NOT", "MAY NOT", "MUST", "SHOULD", "MAY")


def _target_is_single_specification_md(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's target_spec_files equals exactly ["SPECIFICATION.md"].

    Per SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/propose-change.md", the
    minimal template's single-file output means every finding
    targets exactly the single SPECIFICATION.md path.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    for finding in payload.get("findings", []):
        targets = finding.get("target_spec_files", [])
        if targets != ["SPECIFICATION.md"]:
            raise AssertionError(
                f"finding {finding.get('name')!r} target_spec_files "
                f"MUST equal ['SPECIFICATION.md'], got {targets!r}",
            )


def _bcp14_in_proposed_changes(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's proposed_changes prose contains a BCP14 keyword.

    Per SPECIFICATION/templates/minimal/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/propose-change.md".
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    for finding in payload.get("findings", []):
        prose: str = finding.get("proposed_changes", "")
        if not any(keyword in prose for keyword in _BCP14_KEYWORDS):
            raise AssertionError(
                f"finding {finding.get('name')!r} proposed_changes "
                f"prose lacks any BCP14 keyword "
                f"({_BCP14_KEYWORDS!r})",
            )


_DECISION_VALUES = ("accept", "modify", "reject")


def _decisions_reference_pending_proposals(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every `replayed_response.decisions[].proposal_topic` references an actually-pending proposal.

    Same shape as livespec-template `_decisions_reference_pending_proposals`;
    per-template registry independence per v014 fixture pattern.
    """
    ctx = cast(dict[str, Any], input_context)
    payload = cast(dict[str, Any], replayed_response)
    pending = ctx.get("pending_proposals", [])
    pending_topics = {Path(p).stem for p in pending}
    decisions = payload.get("decisions", [])
    emitted_topics = {d.get("proposal_topic", "") for d in decisions}
    extras = emitted_topics - pending_topics
    if extras:
        raise AssertionError(
            f"replayed_response.decisions[] topics not in pending "
            f"proposals: {sorted(extras)!r}",
        )


def _per_proposal_disposition_with_rationale(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every decision has `decision` in {accept, modify, reject} + non-empty `rationale`.

    Same shape as livespec-template
    `_per_proposal_disposition_with_rationale`.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    for decision in payload.get("decisions", []):
        topic = decision.get("proposal_topic", "<unknown>")
        if decision.get("decision") not in _DECISION_VALUES:
            raise AssertionError(
                f"decision for topic {topic!r} has unexpected "
                f"decision value {decision.get('decision')!r}",
            )
        rationale: str = decision.get("rationale", "")
        if not rationale.strip():
            raise AssertionError(
                f"decision for topic {topic!r} has empty / " f"whitespace-only rationale",
            )


_AMBIGUITY_LEXICON = (
    "ambiguity",
    "ambiguous",
    "contradiction",
    "contradicts",
    "contradictory",
    "unclear",
    "inconsistent",
    "inconsistency",
    "silent",
    "undefined",
)


def _prioritizes_ambiguity_over_style(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's `motivation` contains an ambiguity / contradiction lexicon term.

    Same shape as livespec-template `_prioritizes_ambiguity_over_style`.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    for finding in payload.get("findings", []):
        motivation: str = finding.get("motivation", "").lower()
        if not any(keyword in motivation for keyword in _AMBIGUITY_LEXICON):
            raise AssertionError(
                f"finding {finding.get('name')!r} motivation "
                f"prose contains no ambiguity/contradiction "
                f"lexicon keyword ({_AMBIGUITY_LEXICON!r})",
            )


ASSERTIONS: dict[str, Callable[..., None]] = {
    "sub_specs_always_empty": _sub_specs_always_empty,
    "single_specification_md_file": _single_specification_md_file,
    "target_is_single_specification_md": _target_is_single_specification_md,
    "bcp14_in_proposed_changes": _bcp14_in_proposed_changes,
    "decisions_reference_pending_proposals": _decisions_reference_pending_proposals,
    "per_proposal_disposition_with_rationale": _per_proposal_disposition_with_rationale,
    "prioritizes_ambiguity_over_style": _prioritizes_ambiguity_over_style,
}
