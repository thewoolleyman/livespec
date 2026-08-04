"""Reusable checks for commented spec-governance safe-default blocks.

This module is shipped in the core plugin so consumer repositories can run the
installed `spec_governance.py --check-default-block <path>` surface from their
own check aggregates. That keeps the cross-repo read on the consumer side: the
consumer supplies its local `.livespec.jsonc`, while the running installed core
plugin supplies the manifest projection from its own package bytes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

from livespec.spec_governance.registry import ManifestRow

__all__: list[str] = [
    "BlockDrift",
    "BlockVerification",
    "documented_defaults",
    "verify_default_block",
]

_BLOCK_START = "// Optional \u2014 spec_governance:"
_BLOCK_END = "// Optional \u2014 credential_wrapper:"


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
    for line in lines[start_index:]:
        if line.strip().startswith(_BLOCK_END):
            return block
        block.append(line)
    return None


def _parse_commented_defaults(*, block: list[str]) -> dict[str, Any] | None:
    uncommented: list[str] = []
    for line in block:
        stripped = line.strip()
        if not stripped.startswith("//"):
            continue
        content = stripped.removeprefix("//").strip()
        if content.startswith("//"):
            continue
        if content.startswith(('"spec_governance"', "}", '"')):
            uncommented.append(content)
    if uncommented == []:
        return None
    parsed = cast(dict[str, object], json.loads("\n".join(["{", *uncommented, "}"])))
    block_value = parsed.get("spec_governance")
    if not isinstance(block_value, dict):
        return None
    return cast(dict[str, Any], block_value)
