"""Lockstep guard for the intent-preservation ratification (v159).

Per SPECIFICATION/spec.md, the "Intent preservation and design-record
authority" section binds the lifecycle operations operationally, and its
ratifying proposal (archived at
`SPECIFICATION/history/v159/proposed_changes/`) requires the operational
prose artifacts — `.claude-plugin/prose/critique.md` and
`.claude-plugin/prose/revise.md` — to be co-updated in the SAME revise
pass and to stay in lockstep with the ratified section thereafter. This
guard mechanically enforces that lockstep: the ratified section, its
scenario home, the reference-discipline carve-out, and both prose
artifacts' operational instructions must all be present together —
exactly the class of ratified-text-drifting-from-intent failure the
section exists to prevent.

Covers the `## Intent preservation and design-record authority`
(spec.md) and `## Conflicting ratified statements resolve toward the
cited design record` (scenarios.md) entries in
`tests/heading-coverage.json`. Marked integration-tier (the
`test_behavior_scenario_link` precedent): the assertions span five
artifacts across two component boundaries — the governed spec tree and
the shipped plugin's prose — so the invariant under test is
cross-component consistency, not a unit's behavior. The section's
LLM-behavioral clauses additionally land `clauses[]` scenario links via
the documented `behavior_scenario_link` warn-tier backlog per the
ratified proposal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

__all__: list[str] = []

pytestmark = [pytest.mark.integration]


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _REPO_ROOT / "SPECIFICATION" / "spec.md"
_SCENARIOS = _REPO_ROOT / "SPECIFICATION" / "scenarios.md"
_CONSTRAINTS = _REPO_ROOT / "SPECIFICATION" / "constraints.md"
_CRITIQUE_PROSE = _REPO_ROOT / ".claude-plugin" / "prose" / "critique.md"
_REVISE_PROSE = _REPO_ROOT / ".claude-plugin" / "prose" / "revise.md"

_SPEC_HEADING = "## Intent preservation and design-record authority"
_SCENARIOS_HEADING = "## Conflicting ratified statements resolve toward the cited design record"
_CARVE_OUT_HEADING = "### Design-record citations (authorized exception)"

# The four rule paragraphs the ratified section must carry, keyed on
# their bold lead-ins (the section's own structure, not a paraphrase).
_SPEC_RULE_MARKERS = (
    "**Rationale-and-citation requirement.**",
    "**The intent tiebreaker.**",
    "**Missing record is a maintainer finding.**",
    "**Operational reach.**",
)

# The load-bearing tiebreaker clause: recorded intent wins; the shipped
# implementation never does.
_TIEBREAKER_CLAUSE = "Consistency with the shipped implementation MUST NOT be the tiebreaker"

# The three Given/When/Then blocks the scenario H2 must carry.
_SCENARIO_TITLES = (
    "Scenario: Critique surfaces a conflict together with the design record's position",
    "Scenario: Revise does not ratify a resolution that contradicts a cited design record",
    "Scenario: A conflict with no reachable design record is escalated, never self-resolved",
)

# The carve-out's rewired prohibition sentences in constraints.md.
_CARVE_OUT_REWIRES = (
    "or — for design-record citations only — the authorized exception",
    "remain forbidden EXCEPT for design-record citations",
)

# The operational instructions each prose artifact must carry (the
# ratifying proposal's section-D edit signatures).
_CRITIQUE_INSTRUCTION = "state the cited design record's position on the conflict"
_REVISE_GATE_MARKER = "**Intent-preservation gate**"
_REVISE_DECISION_RECORD_NOTE = "name the departed-from record and the deliberate"


def _section(*, path: Path, heading: str) -> str:
    """The file's text from `heading` up to (not incl.) the next H2."""
    text = path.read_text(encoding="utf-8")
    start = text.find(heading)
    assert start != -1, f"{path.name} is missing the heading {heading!r}"
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_spec_section_carries_the_four_intent_preservation_rules() -> None:
    section = _section(path=_SPEC, heading=_SPEC_HEADING)
    missing = [marker for marker in _SPEC_RULE_MARKERS if marker not in section]
    assert not missing, (
        f"spec.md {_SPEC_HEADING!r} lost its rule paragraph(s) {missing!r}; "
        "the ratified section must carry all four intent-preservation rules"
    )
    assert _TIEBREAKER_CLAUSE in section, (
        "the ratified tiebreaker clause is gone from spec.md: recorded "
        "maintainer intent — never the shipped implementation — settles "
        "conflicts between ratified statements"
    )


def test_scenarios_section_carries_the_three_conflict_resolution_scenarios() -> None:
    section = _section(path=_SCENARIOS, heading=_SCENARIOS_HEADING)
    assert (
        "```gherkin" in section
    ), f"scenarios.md {_SCENARIOS_HEADING!r} must carry its Gherkin block"
    missing = [title for title in _SCENARIO_TITLES if title not in section]
    assert not missing, f"scenarios.md {_SCENARIOS_HEADING!r} lost scenario block(s) {missing!r}"


def test_constraints_carry_the_design_record_citation_carve_out() -> None:
    text = _CONSTRAINTS.read_text(encoding="utf-8")
    assert _CARVE_OUT_HEADING in text, (
        "constraints.md lost the design-record-citation carve-out subsection; "
        "without it the citation mandate and the reference-discipline "
        "prohibitions are conflicting ratified statements"
    )
    missing = [fragment for fragment in _CARVE_OUT_REWIRES if fragment not in text]
    assert not missing, (
        f"constraints.md lost the rewired prohibition sentence(s) {missing!r}; "
        "the carve-out must stay wired into both prohibition statements"
    )


def test_operational_prose_stays_in_lockstep_with_the_ratified_section() -> None:
    critique = _CRITIQUE_PROSE.read_text(encoding="utf-8")
    assert _CRITIQUE_INSTRUCTION in critique, (
        "prose/critique.md lost the conflict-surfacing instruction; critique "
        "must surface conflicts together with the cited design record's "
        "position (ratified co-update, section D of the v159 proposal)"
    )
    revise = _REVISE_PROSE.read_text(encoding="utf-8")
    assert _REVISE_GATE_MARKER in revise, (
        "prose/revise.md lost the intent-preservation gate bullet; revise "
        "must not ratify a resolution contradicting a cited design record "
        "without the maintainer's explicit acknowledgment"
    )
    assert _REVISE_DECISION_RECORD_NOTE in revise, (
        "prose/revise.md lost the decision-record acknowledgment note on the "
        "Decision and Rationale format bullet"
    )
