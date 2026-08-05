"""Edge-case tests for spec-governance default-block extraction."""

from __future__ import annotations

from livespec.spec_governance.default_block import documented_defaults

__all__: list[str] = []


def test_documented_defaults_ignores_braces_inside_escaped_string_values() -> None:
    text = (
        "{\n"
        "  // Optional \u2014 spec_governance: policy\n"
        '  //   "spec_governance": {\n'
        '  //     "pattern": "literal \\"{ not structural"\n'
        "  //   }\n"
        "  // Optional \u2014 implementation: next commented sibling block\n"
        '  //   "implementation": {\n'
        '  //     "plugin": "example"\n'
        "  //   }\n"
        "}\n"
    )

    assert documented_defaults(text=text) == {
        "pattern": 'literal "{ not structural',
    }
