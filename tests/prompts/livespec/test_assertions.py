"""Unit tests for `tests/prompts/livespec/_assertions.py`.

Exercises every branch of the per-template assertion functions
that the prompt-QA harness dispatches per
`expected_semantic_properties`. The happy-path branches are
covered transitively by `tests/prompts/livespec/seed/baseline.json`
+ the harness; the `AssertionError` branches need explicit
coverage here per the per-file 100% line+branch gate.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

__all__: list[str] = []


_ASSERTIONS_PATH = Path(__file__).resolve().parent / "_assertions.py"
_SPEC = importlib.util.spec_from_file_location(
    "_livespec_template_assertions_for_unit_tests",
    _ASSERTIONS_PATH,
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"could not load {_ASSERTIONS_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ASSERTIONS = _MODULE.ASSERTIONS


_VALID_REPLAY = {
    "template": "livespec",
    "intent": "Test",
    "files": [
        {"path": "spec.md", "content": "# Title\n\n## Section\n\nbody\n"},
    ],
    "sub_specs": [],
}


def test_headings_derived_from_intent_passes_when_all_files_have_h1() -> None:
    assertion = ASSERTIONS["headings_derived_from_intent"]
    assertion(replayed_response=_VALID_REPLAY, input_context={})


def test_headings_derived_from_intent_rejects_missing_h1() -> None:
    payload = {
        "files": [
            {"path": "spec.md", "content": "## Section\n\nno H1 here\n"},
        ],
    }
    assertion = ASSERTIONS["headings_derived_from_intent"]
    with pytest.raises(AssertionError, match="missing `# ` H1 header"):
        assertion(replayed_response=payload, input_context={})


def test_asks_v020_q2_question_passes_when_ships_false_and_empty_sub_specs() -> None:
    assertion = ASSERTIONS["asks_v020_q2_question"]
    assertion(
        replayed_response={"sub_specs": []},
        input_context={"ships_own_templates": False},
    )


def test_asks_v020_q2_question_rejects_unexpected_sub_specs_when_ships_false() -> None:
    assertion = ASSERTIONS["asks_v020_q2_question"]
    with pytest.raises(AssertionError, match="ships_own_templates is false"):
        assertion(
            replayed_response={"sub_specs": [{"template_name": "x", "files": []}]},
            input_context={"ships_own_templates": False},
        )


def test_asks_v020_q2_question_passes_when_ships_true_and_counts_match() -> None:
    assertion = ASSERTIONS["asks_v020_q2_question"]
    assertion(
        replayed_response={
            "sub_specs": [
                {"template_name": "livespec", "files": []},
                {"template_name": "minimal", "files": []},
            ],
        },
        input_context={
            "ships_own_templates": True,
            "named_templates": ["livespec", "minimal"],
        },
    )


def test_asks_v020_q2_question_rejects_count_mismatch_when_ships_true() -> None:
    assertion = ASSERTIONS["asks_v020_q2_question"]
    with pytest.raises(AssertionError, match="ships_own_templates=true"):
        assertion(
            replayed_response={
                "sub_specs": [{"template_name": "livespec", "files": []}],
            },
            input_context={
                "ships_own_templates": True,
                "named_templates": ["livespec", "minimal"],
            },
        )


def test_target_files_within_spec_target_passes_when_all_paths_under_target() -> None:
    assertion = ASSERTIONS["target_files_within_spec_target"]
    assertion(
        replayed_response={
            "findings": [
                {
                    "name": "x",
                    "target_spec_files": ["SPECIFICATION/spec.md"],
                },
            ],
        },
        input_context={"spec_target": "SPECIFICATION/"},
    )


def test_target_files_within_spec_target_rejects_path_outside_target() -> None:
    assertion = ASSERTIONS["target_files_within_spec_target"]
    with pytest.raises(AssertionError, match="outside input_context.spec_target"):
        assertion(
            replayed_response={
                "findings": [
                    {
                        "name": "x",
                        "target_spec_files": ["other/dir/spec.md"],
                    },
                ],
            },
            input_context={"spec_target": "SPECIFICATION/"},
        )


def test_bcp14_in_proposed_changes_passes_when_keyword_present() -> None:
    assertion = ASSERTIONS["bcp14_in_proposed_changes"]
    assertion(
        replayed_response={
            "findings": [
                {
                    "name": "x",
                    "proposed_changes": "The system MUST emit X.",
                },
            ],
        },
        input_context={},
    )


def test_bcp14_in_proposed_changes_rejects_prose_without_keyword() -> None:
    assertion = ASSERTIONS["bcp14_in_proposed_changes"]
    with pytest.raises(AssertionError, match="lacks any BCP14 keyword"):
        assertion(
            replayed_response={
                "findings": [
                    {
                        "name": "x",
                        "proposed_changes": "The system emits X.",
                    },
                ],
            },
            input_context={},
        )


def test_decisions_reference_pending_proposals_passes_when_emitted_subset_of_pending() -> None:
    assertion = ASSERTIONS["decisions_reference_pending_proposals"]
    assertion(
        replayed_response={
            "decisions": [
                {"proposal_topic": "foo", "decision": "accept", "rationale": "ok"},
            ],
        },
        input_context={
            "pending_proposals": [
                "SPECIFICATION/proposed_changes/foo.md",
                "SPECIFICATION/proposed_changes/bar.md",
            ],
        },
    )


def test_decisions_reference_pending_proposals_rejects_extra_topic_not_in_pending() -> None:
    assertion = ASSERTIONS["decisions_reference_pending_proposals"]
    with pytest.raises(AssertionError, match="topics not in pending"):
        assertion(
            replayed_response={
                "decisions": [
                    {"proposal_topic": "foo", "decision": "accept", "rationale": "ok"},
                    {"proposal_topic": "baz", "decision": "reject", "rationale": "no"},
                ],
            },
            input_context={
                "pending_proposals": [
                    "SPECIFICATION/proposed_changes/foo.md",
                    "SPECIFICATION/proposed_changes/bar.md",
                ],
            },
        )


def test_per_proposal_disposition_with_rationale_passes_when_all_valid() -> None:
    assertion = ASSERTIONS["per_proposal_disposition_with_rationale"]
    assertion(
        replayed_response={
            "decisions": [
                {"proposal_topic": "x", "decision": "accept", "rationale": "ok"},
                {"proposal_topic": "y", "decision": "modify", "rationale": "tweak"},
                {"proposal_topic": "z", "decision": "reject", "rationale": "out of scope"},
            ],
        },
        input_context={},
    )


def test_per_proposal_disposition_with_rationale_rejects_unknown_decision() -> None:
    assertion = ASSERTIONS["per_proposal_disposition_with_rationale"]
    with pytest.raises(AssertionError, match="unexpected decision value"):
        assertion(
            replayed_response={
                "decisions": [
                    {"proposal_topic": "x", "decision": "skip", "rationale": "ok"},
                ],
            },
            input_context={},
        )


def test_per_proposal_disposition_with_rationale_rejects_empty_rationale() -> None:
    assertion = ASSERTIONS["per_proposal_disposition_with_rationale"]
    with pytest.raises(AssertionError, match="empty / whitespace-only rationale"):
        assertion(
            replayed_response={
                "decisions": [
                    {"proposal_topic": "x", "decision": "accept", "rationale": "   "},
                ],
            },
            input_context={},
        )


def test_findings_grounded_in_spec_target_passes_when_targets_match() -> None:
    assertion = ASSERTIONS["findings_grounded_in_spec_target"]
    assertion(
        replayed_response={
            "findings": [
                {
                    "name": "x",
                    "target_spec_files": ["SPECIFICATION/spec.md"],
                    "motivation": "ambiguous wording",
                },
            ],
        },
        input_context={
            "current_spec_files": ["SPECIFICATION/spec.md", "SPECIFICATION/contracts.md"],
        },
    )


def test_findings_grounded_in_spec_target_rejects_target_not_in_current_files() -> None:
    assertion = ASSERTIONS["findings_grounded_in_spec_target"]
    with pytest.raises(AssertionError, match="not in input_context.current_spec_files"):
        assertion(
            replayed_response={
                "findings": [
                    {
                        "name": "x",
                        "target_spec_files": ["SPECIFICATION/missing.md"],
                        "motivation": "contradiction",
                    },
                ],
            },
            input_context={"current_spec_files": ["SPECIFICATION/spec.md"]},
        )


def test_prioritizes_ambiguity_over_style_passes_when_lexicon_present() -> None:
    assertion = ASSERTIONS["prioritizes_ambiguity_over_style"]
    assertion(
        replayed_response={
            "findings": [
                {"name": "x", "motivation": "The CONTRADICTION between A and B."},
            ],
        },
        input_context={},
    )


def test_prioritizes_ambiguity_over_style_rejects_motivation_without_lexicon() -> None:
    assertion = ASSERTIONS["prioritizes_ambiguity_over_style"]
    with pytest.raises(AssertionError, match="ambiguity/contradiction lexicon"):
        assertion(
            replayed_response={
                "findings": [
                    {"name": "x", "motivation": "The wording could be smoother."},
                ],
            },
            input_context={},
        )
