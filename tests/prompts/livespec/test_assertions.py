"""Unit tests for `tests/prompts/livespec/_assertions.py`.

Exercises every branch of the per-template assertion functions
that the prompt-QA harness dispatches per
`expected_semantic_properties`. The happy-path branches are
covered transitively by `tests/prompts/livespec/seed/baseline.json`
+ the harness; the `AssertionError` branches need explicit
coverage here per the per-file 100% line+branch gate.
"""

from __future__ import annotations

import pytest
from _assertions import ASSERTIONS

__all__: list[str] = []


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
