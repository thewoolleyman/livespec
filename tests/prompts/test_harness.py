"""Unit tests for `tests/prompts/_harness.py`.

Exercises every branch of the harness's behavior contract per
SPECIFICATION/contracts.md §"Prompt-QA harness contract" (v014):
fixture-format validation, schema-validity assertions in both
positive and negative-test cases, and per-template
semantic-property dispatch (registered, unregistered, assertion
failure).

Per-test fixtures are written into `tmp_path` so the suite stays
hermetic and tests/prompts/livespec/seed/ remains the canonical
prompt-QA case set (separate from these unit-test fixtures).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _harness import assert_fixture

__all__: list[str] = []


_VALID_REPLAYED_RESPONSE = {
    "template": "livespec",
    "intent": "Test intent",
    "files": [
        {"path": "SPECIFICATION/spec.md", "content": "# Spec\n"},
    ],
    "sub_specs": [],
}


def _write_fixture(*, tmp_path: Path, payload: dict[str, object]) -> Path:
    fixture_path = tmp_path / "case.json"
    fixture_path.write_text(json.dumps(payload), encoding="utf-8")
    return fixture_path


def test_assert_fixture_passes_with_valid_baseline(*, tmp_path: Path) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": True,
            "expected_semantic_properties": [],
        },
    )
    assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_rejects_malformed_fixture(*, tmp_path: Path) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": True,
        },
    )
    with pytest.raises(AssertionError, match="does not conform to"):
        assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_rejects_invalid_replayed_response(*, tmp_path: Path) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": {"template": "livespec"},
            "expected_schema_valid": True,
            "expected_semantic_properties": [],
        },
    )
    with pytest.raises(AssertionError, match="expected to validate"):
        assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_passes_negative_test(*, tmp_path: Path) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": {"template": "livespec"},
            "expected_schema_valid": False,
            "expected_semantic_properties": [],
        },
    )
    assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_rejects_unexpected_pass_negative_test(
    *,
    tmp_path: Path,
) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": False,
            "expected_semantic_properties": [],
        },
    )
    with pytest.raises(AssertionError, match="expected to FAIL"):
        assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_rejects_unknown_property_name(*, tmp_path: Path) -> None:
    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": True,
            "expected_semantic_properties": ["nonexistent_property"],
        },
    )
    with pytest.raises(AssertionError, match="unknown property name"):
        assert_fixture(fixture_path=fixture_path, assertions={})


def test_assert_fixture_invokes_registered_assertion(*, tmp_path: Path) -> None:
    invocations: list[tuple[object, object]] = []

    def _record_call(*, replayed_response: object, input_context: object) -> None:
        invocations.append((replayed_response, input_context))

    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {"hint": "ctx"},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": True,
            "expected_semantic_properties": ["recorded"],
        },
    )
    assert_fixture(
        fixture_path=fixture_path,
        assertions={"recorded": _record_call},
    )
    assert len(invocations) == 1
    assert invocations[0] == (_VALID_REPLAYED_RESPONSE, {"hint": "ctx"})


def test_assert_fixture_propagates_assertion_failure(*, tmp_path: Path) -> None:
    def _always_fail(*, replayed_response: object, input_context: object) -> None:
        del replayed_response, input_context
        raise AssertionError("intentional failure")

    fixture_path = _write_fixture(
        tmp_path=tmp_path,
        payload={
            "prompt_name": "seed",
            "schema_id": "seed_input.schema.json",
            "input_context": {},
            "replayed_response": _VALID_REPLAYED_RESPONSE,
            "expected_schema_valid": True,
            "expected_semantic_properties": ["always_fail"],
        },
    )
    with pytest.raises(AssertionError, match="intentional failure"):
        assert_fixture(
            fixture_path=fixture_path,
            assertions={"always_fail": _always_fail},
        )
