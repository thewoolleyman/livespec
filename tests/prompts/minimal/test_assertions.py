"""Unit tests for `tests/prompts/minimal/_assertions.py`.

Mirrors `tests/prompts/livespec/test_assertions.py`'s pattern:
loads the per-template `_assertions.py` via importlib with a
unique sys.modules name + unit-tests every branch of each
registered function (happy-path + AssertionError paths).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

__all__: list[str] = []


_ASSERTIONS_PATH = Path(__file__).resolve().parent / "_assertions.py"
_SPEC = importlib.util.spec_from_file_location(
    "_minimal_template_assertions_for_unit_tests",
    _ASSERTIONS_PATH,
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"could not load {_ASSERTIONS_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ASSERTIONS = _MODULE.ASSERTIONS


def test_sub_specs_always_empty_passes_when_empty() -> None:
    assertion = ASSERTIONS["sub_specs_always_empty"]
    assertion(replayed_response={"sub_specs": []}, input_context={})


def test_sub_specs_always_empty_rejects_non_empty() -> None:
    assertion = ASSERTIONS["sub_specs_always_empty"]
    with pytest.raises(AssertionError, match="MUST be empty"):
        assertion(
            replayed_response={"sub_specs": [{"template_name": "x", "files": []}]},
            input_context={},
        )


def test_single_specification_md_file_passes_when_one_correct_entry() -> None:
    assertion = ASSERTIONS["single_specification_md_file"]
    assertion(
        replayed_response={
            "files": [{"path": "SPECIFICATION.md", "content": "# x\n"}],
        },
        input_context={},
    )


def test_single_specification_md_file_rejects_zero_files() -> None:
    assertion = ASSERTIONS["single_specification_md_file"]
    with pytest.raises(AssertionError, match="exactly 1 entry"):
        assertion(replayed_response={"files": []}, input_context={})


def test_single_specification_md_file_rejects_multiple_files() -> None:
    assertion = ASSERTIONS["single_specification_md_file"]
    with pytest.raises(AssertionError, match="exactly 1 entry"):
        assertion(
            replayed_response={
                "files": [
                    {"path": "SPECIFICATION.md", "content": "x"},
                    {"path": "EXTRA.md", "content": "y"},
                ],
            },
            input_context={},
        )


def test_single_specification_md_file_rejects_wrong_path() -> None:
    assertion = ASSERTIONS["single_specification_md_file"]
    with pytest.raises(AssertionError, match="MUST equal 'SPECIFICATION.md'"):
        assertion(
            replayed_response={
                "files": [{"path": "WRONG.md", "content": "x"}],
            },
            input_context={},
        )


def test_target_is_single_specification_md_passes_when_exact() -> None:
    assertion = ASSERTIONS["target_is_single_specification_md"]
    assertion(
        replayed_response={
            "findings": [{"name": "x", "target_spec_files": ["SPECIFICATION.md"]}],
        },
        input_context={},
    )


def test_target_is_single_specification_md_rejects_extra_file() -> None:
    assertion = ASSERTIONS["target_is_single_specification_md"]
    with pytest.raises(AssertionError, match=r"MUST equal \['SPECIFICATION.md'\]"):
        assertion(
            replayed_response={
                "findings": [
                    {
                        "name": "x",
                        "target_spec_files": ["SPECIFICATION.md", "EXTRA.md"],
                    },
                ],
            },
            input_context={},
        )


def test_bcp14_in_proposed_changes_passes_when_keyword_present() -> None:
    assertion = ASSERTIONS["bcp14_in_proposed_changes"]
    assertion(
        replayed_response={
            "findings": [{"name": "x", "proposed_changes": "The system MUST X."}],
        },
        input_context={},
    )


def test_bcp14_in_proposed_changes_rejects_no_keyword() -> None:
    assertion = ASSERTIONS["bcp14_in_proposed_changes"]
    with pytest.raises(AssertionError, match="lacks any BCP14 keyword"):
        assertion(
            replayed_response={
                "findings": [{"name": "x", "proposed_changes": "Just prose."}],
            },
            input_context={},
        )


def test_decisions_reference_pending_proposals_passes_when_emitted_in_pending() -> None:
    assertion = ASSERTIONS["decisions_reference_pending_proposals"]
    assertion(
        replayed_response={
            "decisions": [
                {"proposal_topic": "foo", "decision": "accept", "rationale": "ok"},
            ],
        },
        input_context={"pending_proposals": ["proposed_changes/foo.md"]},
    )


def test_decisions_reference_pending_proposals_rejects_extra_not_in_pending() -> None:
    assertion = ASSERTIONS["decisions_reference_pending_proposals"]
    with pytest.raises(AssertionError, match="topics not in pending"):
        assertion(
            replayed_response={
                "decisions": [
                    {"proposal_topic": "baz", "decision": "reject", "rationale": "no"},
                ],
            },
            input_context={"pending_proposals": ["proposed_changes/foo.md"]},
        )


def test_per_proposal_disposition_with_rationale_passes_when_valid() -> None:
    assertion = ASSERTIONS["per_proposal_disposition_with_rationale"]
    assertion(
        replayed_response={
            "decisions": [
                {"proposal_topic": "x", "decision": "accept", "rationale": "ok"},
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
                    {"proposal_topic": "x", "decision": "accept", "rationale": "  "},
                ],
            },
            input_context={},
        )


def test_prioritizes_ambiguity_over_style_passes_when_lexicon_present() -> None:
    assertion = ASSERTIONS["prioritizes_ambiguity_over_style"]
    assertion(
        replayed_response={
            "findings": [{"name": "x", "motivation": "The CONTRADICTION between A and B."}],
        },
        input_context={},
    )


def test_prioritizes_ambiguity_over_style_rejects_motivation_without_lexicon() -> None:
    assertion = ASSERTIONS["prioritizes_ambiguity_over_style"]
    with pytest.raises(AssertionError, match="ambiguity/contradiction lexicon"):
        assertion(
            replayed_response={
                "findings": [{"name": "x", "motivation": "Just polish the wording."}],
            },
            input_context={},
        )
