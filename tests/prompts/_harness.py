"""Prompt-QA harness shared by every per-template test module.

Per SPECIFICATION/contracts.md §"Prompt-QA harness contract"
(v014). The harness is a dedicated test-infrastructure module
(scope-distinct from the v014 N9 e2e tier at tests/e2e/) that
performs no LLM round-trip and no wrapper invocation. It loads
a fixture file, validates the fixture format, validates the
fixture's `replayed_response` against the named wire-contract
schema, and dispatches each name in the fixture's
`expected_semantic_properties` array to a per-template
`ASSERTIONS` dict supplied by the calling test module.

Coverage scope: this module lives under `tests/prompts/` which
is OUT of the unit-tier coverage source list per
SPECIFICATION/spec.md §"Testing approach" (v014); the per-file
100% line+branch gate does not extend here. The harness's
correctness is exercised functionally by the per-template
prompt-QA tests that consume it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import fastjsonschema

__all__: list[str] = ["assert_fixture"]


_HARNESS_DIR = Path(__file__).resolve().parent
_FIXTURE_SCHEMA_PATH = _HARNESS_DIR / "_fixture.schema.json"
_LIVESPEC_SCHEMAS_DIR = (
    _HARNESS_DIR.parents[1] / ".claude-plugin" / "scripts" / "livespec" / "schemas"
)


def _load_json(*, path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_fixture_format(*, fixture: dict[str, Any], fixture_path: Path) -> None:
    schema = _load_json(path=_FIXTURE_SCHEMA_PATH)
    validator = fastjsonschema.compile(schema)
    try:
        validator(fixture)
    except fastjsonschema.JsonSchemaValueException as exc:
        raise AssertionError(
            f"fixture {fixture_path} does not conform to " f"_fixture.schema.json: {exc}",
        ) from exc


def _validate_replayed_response(
    *,
    replayed_response: dict[str, Any],
    schema_id: str,
    expected_schema_valid: bool,
    fixture_path: Path,
) -> None:
    schema = _load_json(path=_LIVESPEC_SCHEMAS_DIR / schema_id)
    validator = fastjsonschema.compile(schema)
    if expected_schema_valid:
        try:
            validator(replayed_response)
        except fastjsonschema.JsonSchemaValueException as exc:
            raise AssertionError(
                f"replayed_response in {fixture_path} expected to "
                f"validate against {schema_id} but did not: {exc}",
            ) from exc
        return
    try:
        validator(replayed_response)
    except fastjsonschema.JsonSchemaValueException:
        return
    raise AssertionError(
        f"replayed_response in {fixture_path} expected to FAIL "
        f"{schema_id} validation (negative-test fixture) but it passed",
    )


def _dispatch_semantic_assertions(
    *,
    expected_semantic_properties: list[str],
    assertions: Mapping[str, Callable[..., None]],
    replayed_response: dict[str, Any],
    input_context: dict[str, Any],
    fixture_path: Path,
) -> None:
    for property_name in expected_semantic_properties:
        if property_name not in assertions:
            raise AssertionError(
                f"unknown property name '{property_name}' in "
                f"{fixture_path}: not registered in per-template "
                f"ASSERTIONS dict",
            )
        assertion = assertions[property_name]
        assertion(
            replayed_response=replayed_response,
            input_context=input_context,
        )


def assert_fixture(
    *,
    fixture_path: Path,
    assertions: Mapping[str, Callable[..., None]],
) -> None:
    """Validate a fixture and dispatch its semantic-property assertions.

    Behavior, in order:
      1. Load the fixture file and validate it against
         `_fixture.schema.json`. Failure -> AssertionError.
      2. When `expected_schema_valid` is true, validate
         `replayed_response` against the JSON Schema named by
         `schema_id`. Failure -> AssertionError.
      3. When `expected_schema_valid` is false, assert that schema
         validation FAILS (negative-test coverage).
      4. For each name in `expected_semantic_properties`, look up
         the function in the `assertions` Mapping and invoke it
         with `replayed_response` and `input_context` keyword
         arguments. Any raised AssertionError propagates.
    """
    fixture = _load_json(path=fixture_path)
    _validate_fixture_format(fixture=fixture, fixture_path=fixture_path)
    _validate_replayed_response(
        replayed_response=fixture["replayed_response"],
        schema_id=fixture["schema_id"],
        expected_schema_valid=fixture["expected_schema_valid"],
        fixture_path=fixture_path,
    )
    _dispatch_semantic_assertions(
        expected_semantic_properties=fixture["expected_semantic_properties"],
        assertions=assertions,
        replayed_response=fixture["replayed_response"],
        input_context=fixture["input_context"],
        fixture_path=fixture_path,
    )
