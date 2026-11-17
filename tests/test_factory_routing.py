"""Regression test for the committed factory-routing configuration.

Covers ``## Factory routing`` in
``SPECIFICATION/non-functional-requirements.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

from livespec.parse import jsonc
from returns.result import Success

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _REPO_ROOT / ".livespec.jsonc"
_HEADING_COVERAGE_PATH = _REPO_ROOT / "tests" / "heading-coverage.json"
_TEST_NODE = (
    "tests.test_factory_routing.test_committed_factories_are_registry_backed_and_name_no_machine"
)


def test_committed_factories_are_registry_backed_and_name_no_machine() -> None:
    """Each committed factory routes through the registry, not a named host."""
    parsed = jsonc.loads(text=_CONFIG_PATH.read_text(encoding="utf-8"))
    match parsed:
        case Success(payload):
            factories = payload["livespec-orchestrator-beads-fabro"]["dispatcher"]["factories"]
        case _:
            raise AssertionError(f"expected committed config to parse, got {parsed!r}")

    assert all(factory.get("registry") is True for factory in factories.values())
    assert all(
        factory.get("server") is None and factory.get("docker_host") is None
        for factory in factories.values()
    )

    coverage = json.loads(_HEADING_COVERAGE_PATH.read_text(encoding="utf-8"))
    factory_routing = next(
        entry
        for entry in coverage
        if entry["heading"] == "## Factory routing"
        and entry["spec_file"] == "non-functional-requirements.md"
    )
    assert factory_routing["test"] == _TEST_NODE
