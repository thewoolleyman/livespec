"""Tests for spec-governance commented default-block verification."""

from __future__ import annotations

from livespec.spec_governance.default_block import documented_defaults, verify_default_block
from livespec.spec_governance.registry import ManifestRow

__all__: list[str] = []


def test_documented_defaults_extracts_commented_block() -> None:
    assert documented_defaults(text=_source_text()) == {
        "mode": "safe",
        "reviewer": None,
    }


def test_documented_defaults_rejects_missing_or_unusable_blocks() -> None:
    assert documented_defaults(text="// Optional \u2014 credential_wrapper: next\n") is None
    assert (
        documented_defaults(
            text=(
                "// Optional \u2014 spec_governance: policy\n"
                "not a comment\n"
                "// Optional \u2014 credential_wrapper: next\n"
            )
        )
        is None
    )
    assert (
        documented_defaults(
            text=(
                "// Optional \u2014 spec_governance: policy\n"
                '//   "spec_governance": []\n'
                "// Optional \u2014 credential_wrapper: next\n"
            )
        )
        is None
    )
    assert (
        documented_defaults(
            text="\n".join(
                [
                    "// Optional \u2014 spec_governance: policy",
                    '//   "spec_governance": {}',
                    "",
                ]
            )
        )
        is None
    )


def test_verify_default_block_accepts_exact_manifest_defaults() -> None:
    verification = verify_default_block(text=_source_text(), manifest=_manifest())

    assert verification.drift is None
    assert verification.expected == {"mode": "safe", "reviewer": None}


def test_verify_default_block_reports_missing_extra_and_default_drift() -> None:
    verification = verify_default_block(
        text=_source_text().replace('"mode": "safe"', '"extra": "value"'),
        manifest=_manifest(),
    )

    assert verification.drift is not None
    assert verification.drift.missing == ["mode"]
    assert verification.drift.extra == ["extra"]
    assert verification.drift.default_drift == ["mode"]


def test_verify_default_block_reports_absent_block_as_missing_manifest_keys() -> None:
    verification = verify_default_block(
        text="// Optional \u2014 credential_wrapper: next\n",
        manifest=_manifest(),
    )

    assert verification.documented is None
    assert verification.drift is not None
    assert verification.drift.missing == ["mode", "reviewer"]


def _manifest() -> list[ManifestRow]:
    return [
        ManifestRow(
            key="mode",
            value_type="enum",
            safe_default="safe",
            per_proposal_override=None,
            allowed_values=[],
        ),
        ManifestRow(
            key="reviewer",
            value_type="string",
            safe_default=None,
            per_proposal_override=None,
            allowed_values=[],
        ),
    ]


def _source_text() -> str:
    return (
        "{\n"
        "  // Optional \u2014 spec_governance: policy\n"
        '  //   "spec_governance": {\n'
        '  //     "mode": "safe",\n'
        "  //     // description ignored\n"
        '  //     "reviewer": null\n'
        "  //   }\n"
        "  // Optional \u2014 credential_wrapper: next\n"
        "}\n"
    )
