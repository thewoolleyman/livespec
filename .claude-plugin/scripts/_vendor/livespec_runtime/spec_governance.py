"""Runtime spec-governance manifest and default-block checks.

This module is upstream of livespec core. It carries the manifest and the
commented-defaults block verifier so core and consumer repositories can call one
shared implementation without reaching into plugin-local scripts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, TypeAlias, cast

from returns.result import Failure, Result, Success

__all__: list[str] = [
    "BlockDrift",
    "BlockVerification",
    "ConfigValueType",
    "ManifestRow",
    "UnterminatedGovernanceBlockError",
    "documented_defaults",
    "manifest_rows",
    "verify_default_block",
    "verify_livespec_jsonc_default_block",
]

ConfigValueType: TypeAlias = str
ManifestSafeDefault: TypeAlias = str | int | dict[str, str] | None

_BLOCK_START = "// Optional — spec_governance:"
_MANIFEST_RESOURCE = "api_configurable_keys.json"


@dataclass(frozen=True, kw_only=True, slots=True)
class ManifestRow:
    """Wire projection of one registry row."""

    key: str
    value_type: ConfigValueType
    safe_default: ManifestSafeDefault
    per_proposal_override: str | None
    allowed_values: list[str]


@dataclass(frozen=True, kw_only=True, slots=True)
class BlockDrift:
    """Differences between a documented block and the manifest defaults."""

    missing: list[str]
    extra: list[str]
    default_drift: list[str]


@dataclass(frozen=True, kw_only=True, slots=True)
class BlockVerification:
    """Result of comparing one source file's default block to the manifest."""

    documented: dict[str, Any] | None
    expected: dict[str, Any]
    drift: BlockDrift | None


class UnterminatedGovernanceBlockError(Exception):
    """Raised when a `spec_governance` comment block opens but never balances."""

    def __init__(self) -> None:
        super().__init__("unterminated spec_governance comment block")


def manifest_rows() -> list[ManifestRow]:
    """Load the hosted spec-governance API-key manifest."""
    raw = json.loads(
        files("livespec_runtime").joinpath(_MANIFEST_RESOURCE).read_text(encoding="utf-8")
    )
    return [_manifest_row(raw=row) for row in cast(list[dict[str, object]], raw)]


def documented_defaults(*, text: str) -> dict[str, Any] | None:
    """Extract the commented `spec_governance` object from one source file."""
    block = _comment_block(text=text)
    return None if block is None else _parse_commented_defaults(block=block)


def verify_default_block(
    *,
    text: str,
    manifest: list[ManifestRow],
) -> BlockVerification:
    """Compare one commented defaults block against manifest safe defaults."""
    documented = documented_defaults(text=text)
    expected = {row.key: row.safe_default for row in manifest}
    if documented is None:
        return BlockVerification(
            documented=None,
            expected=expected,
            drift=BlockDrift(
                missing=sorted(expected),
                extra=[],
                default_drift=[],
            ),
        )
    drift = BlockDrift(
        missing=sorted(set(expected) - set(documented)),
        extra=sorted(set(documented) - set(expected)),
        default_drift=sorted(
            key for key, value in expected.items() if documented.get(key) != value
        ),
    )
    if drift.missing == [] and drift.extra == [] and drift.default_drift == []:
        return BlockVerification(documented=documented, expected=expected, drift=None)
    return BlockVerification(documented=documented, expected=expected, drift=drift)


def verify_livespec_jsonc_default_block(
    *,
    path: Path,
) -> Result[dict[str, Any], str]:
    """Verify one `.livespec.jsonc` file against the hosted manifest."""
    if not path.is_file():
        message = ": ".join(
            (
                "spec-governance-default-block-missing-source",
                f"default-block source not found: {path}",
            )
        )
        return Failure(message)
    verification = verify_default_block(
        text=path.read_text(encoding="utf-8"),
        manifest=manifest_rows(),
    )
    if verification.drift is None:
        return Success(
            {
                "check_id": "spec-governance-default-block-ok",
                "path": str(path),
                "key_count": len(verification.expected),
            }
        )
    return Failure(_default_block_drift_message(path=path, drift=verification.drift))


def _manifest_row(*, raw: dict[str, object]) -> ManifestRow:
    return ManifestRow(
        key=str(raw["key"]),
        value_type=str(raw["value_type"]),
        safe_default=cast(ManifestSafeDefault, raw["safe_default"]),
        per_proposal_override=(
            None if raw["per_proposal_override"] is None else str(raw["per_proposal_override"])
        ),
        allowed_values=[str(value) for value in cast(list[object], raw["allowed_values"])],
    )


def _comment_block(*, text: str) -> list[str] | None:
    lines = text.splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip().startswith(_BLOCK_START):
            start_index = index
            break
    if start_index is None:
        return None
    block: list[str] = []
    balance = 0
    object_started = False
    for line in lines[start_index:]:
        block.append(line)
        content = _comment_content(line=line)
        if content is None:
            continue
        if not object_started and not content.startswith('"spec_governance"'):
            continue
        object_started = True
        balance += _brace_delta(text=content)
        if balance <= 0:
            return block
    raise UnterminatedGovernanceBlockError


def _comment_content(*, line: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith("//"):
        return None
    content = stripped.removeprefix("//").strip()
    if content.startswith("//"):
        return None
    return content


def _brace_delta(*, text: str) -> int:
    delta = 0
    in_string = False
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = in_string
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            delta += 1
        if char == "}":
            delta -= 1
    return delta


def _parse_commented_defaults(*, block: list[str]) -> dict[str, Any] | None:
    uncommented: list[str] = []
    for line in block:
        content = _comment_content(line=line)
        if content is None:
            continue
        if content.startswith(('"spec_governance"', "}", '"')):
            uncommented.append(content)
    parsed = cast(dict[str, object], json.loads("\n".join(["{", *uncommented, "}"])))
    block_value = parsed.get("spec_governance")
    if not isinstance(block_value, dict):
        return None
    if block_value == {}:
        return None
    return cast(dict[str, Any], block_value)


def _default_block_drift_message(*, path: Path, drift: BlockDrift) -> str:
    payload = {
        "check_id": "spec-governance-default-block-drift",
        "path": str(path),
        "missing": drift.missing,
        "extra": drift.extra,
        "default_drift": drift.default_drift,
        "hint": (
            "Update the commented spec_governance block so it lists every "
            "installed core manifest key at its safe default, or run with no "
            "block if this repo does not intentionally carry the documentation."
        ),
    }
    return json.dumps(payload, sort_keys=True)
