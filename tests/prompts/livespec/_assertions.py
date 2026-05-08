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
from pathlib import Path
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


_BCP14_KEYWORDS = ("MUST NOT", "SHOULD NOT", "MAY NOT", "MUST", "SHOULD", "MAY")


def _target_files_within_spec_target(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's `target_spec_files[]` paths are under `input_context.spec_target`.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/propose-change.md", findings
    referencing paths outside the spec target are malformed.
    """
    ctx = cast(dict[str, Any], input_context)
    payload = cast(dict[str, Any], replayed_response)
    spec_target: str = ctx.get("spec_target", "")
    findings = payload.get("findings", [])
    for finding in findings:
        for target in finding.get("target_spec_files", []):
            if not target.startswith(spec_target):
                raise AssertionError(
                    f"finding {finding.get('name')!r} target "
                    f"{target!r} is outside input_context.spec_target "
                    f"({spec_target!r})",
                )


def _bcp14_in_proposed_changes(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's `proposed_changes` prose contains a BCP14 keyword.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/propose-change.md", proposed-
    change prose SHOULD apply normative language so the resulting
    file flows into the spec under the same discipline.
    """
    del input_context
    payload = cast(dict[str, Any], replayed_response)
    findings = payload.get("findings", [])
    for finding in findings:
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

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/revise.md", emitted
    decisions MAY cover any subset of pending proposals (selective
    revise per SPECIFICATION/spec.md (v052) §"Sub-command lifecycle"
    revise lifecycle clause (h)). Extras — decisions whose topic is
    NOT in pending — indicate stale or typo'd topic references and
    are a bug.
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

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/revise.md". Schema
    validation enforces field presence + the enum; this assertion
    strengthens the rationale check (whitespace-only rationales
    fail).
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


def _findings_grounded_in_spec_target(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's `target_spec_files[]` paths exist in `input_context.current_spec_files[]`.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/critique.md", critique
    findings MUST reference files that exist in the target tree.
    """
    ctx = cast(dict[str, Any], input_context)
    payload = cast(dict[str, Any], replayed_response)
    current_files = set(ctx.get("current_spec_files", []))
    for finding in payload.get("findings", []):
        for target in finding.get("target_spec_files", []):
            if target not in current_files:
                raise AssertionError(
                    f"finding {finding.get('name')!r} target "
                    f"{target!r} is not in "
                    f"input_context.current_spec_files",
                )


def _prioritizes_ambiguity_over_style(
    *,
    replayed_response: object,
    input_context: object,
) -> None:
    """Every finding's `motivation` contains an ambiguity / contradiction lexicon term.

    Per SPECIFICATION/templates/livespec/contracts.md §"Per-prompt
    semantic-property catalogue → prompts/critique.md", the prompt
    SHOULD prioritize ambiguities + contradictions over wording-
    style suggestions. The lexicon match is heuristic; richer
    semantic checks live in the doctor LLM-driven subjective
    phase.
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
    "headings_derived_from_intent": _headings_derived_from_intent,
    "asks_v020_q2_question": _asks_v020_q2_question,
    "target_files_within_spec_target": _target_files_within_spec_target,
    "bcp14_in_proposed_changes": _bcp14_in_proposed_changes,
    "decisions_reference_pending_proposals": _decisions_reference_pending_proposals,
    "per_proposal_disposition_with_rationale": _per_proposal_disposition_with_rationale,
    "findings_grounded_in_spec_target": _findings_grounded_in_spec_target,
    "prioritizes_ambiguity_over_style": _prioritizes_ambiguity_over_style,
}
