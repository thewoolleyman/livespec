"""Shared fixtures for tests/livespec/validate/.

Provides one `*_validator` fixture per `livespec/schemas/<name>.schema.json`
file. Each fixture loads the schema from disk, compiles it through the
typed `compile_schema` facade, and returns the resulting `Validator`
ready for `make_validator(fast_validator=...)`.

Loading + compiling lives here (in conftest, supervisor-shaped) so that
the per-test files in this tree stay free of `livespec.io` imports per
the `tests/livespec/validate/CLAUDE.md` convention. The fixtures are
session-scoped because the compiled validator is a deterministic pure
artifact — Hypothesis's @given tests would otherwise trip
`HealthCheck.function_scoped_fixture`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import livespec.schemas
import pytest
from livespec.io.fastjsonschema_facade import Validator, compile_schema
from livespec.types import SchemaId

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

__all__: list[str] = []


_SCHEMAS_DIR = Path(livespec.schemas.__file__).parent


def _load_schema(*, filename: str) -> Mapping[str, Any]:
    return json.loads((_SCHEMAS_DIR / filename).read_text(encoding="utf-8"))


def _make_validator(*, filename: str) -> Validator:
    schema = _load_schema(filename=filename)
    return compile_schema(schema_id=SchemaId(filename), schema=schema)


@pytest.fixture(scope="session")
def doctor_findings_validator() -> Validator:
    return _make_validator(filename="doctor_findings.schema.json")


@pytest.fixture(scope="session")
def finding_validator() -> Validator:
    return _make_validator(filename="finding.schema.json")


@pytest.fixture(scope="session")
def livespec_config_validator() -> Validator:
    return _make_validator(filename="livespec_config.schema.json")


@pytest.fixture(scope="session")
def proposal_findings_validator() -> Validator:
    return _make_validator(filename="proposal_findings.schema.json")


@pytest.fixture(scope="session")
def proposed_change_front_matter_validator() -> Validator:
    return _make_validator(filename="proposed_change_front_matter.schema.json")


@pytest.fixture(scope="session")
def revise_input_validator() -> Validator:
    return _make_validator(filename="revise_input.schema.json")


@pytest.fixture(scope="session")
def revision_front_matter_validator() -> Validator:
    return _make_validator(filename="revision_front_matter.schema.json")


@pytest.fixture(scope="session")
def seed_input_validator() -> Validator:
    return _make_validator(filename="seed_input.schema.json")


@pytest.fixture(scope="session")
def sub_spec_payload_validator() -> Validator:
    return _make_validator(filename="sub_spec_payload.schema.json")


@pytest.fixture(scope="session")
def template_config_validator() -> Validator:
    return _make_validator(filename="template_config.schema.json")
