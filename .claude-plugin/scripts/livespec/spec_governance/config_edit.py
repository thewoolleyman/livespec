"""JSONC text replacement helpers for spec-governance config edits."""

# livespec-lloc-soft-band-owner: livespec-dev-tooling-8o8e.25

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Result, Success

from livespec.errors import ValidationError
from livespec.parse import jsonc

__all__: list[str] = [
    "write_config_map_entry",
    "write_config_value",
]

_CONFIG_PATH = ".livespec.jsonc"


def write_config_value(
    *,
    project_root: Path,
    key: str,
    value: str | None,
) -> IOResult[Path, ValidationError]:
    """Set or clear one scalar spec_governance config value.

    Refuses on the FAILURE track rather than rewriting a config it could not
    read. `contracts.md` requires this CLI to "atomically replace only the
    selected value while PRESERVING UNRELATED JSONC KEYS/COMMENTS" — which is
    impossible when the existing block did not parse, so the honest outcome is a
    refusal rather than a destructive success.
    """
    config_path = project_root / _CONFIG_PATH
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else "{\n}\n"
    surgical = _replace_existing_scalar(text=text, key=key, value=value)
    if surgical is not None:
        return IOSuccess(
            _atomic_replace(project_root=project_root, path=config_path, updated=surgical)
        )
    existing = _extract_block(text=text)
    if isinstance(existing, Failure):
        return IOFailure(existing.failure())
    block = dict(existing.unwrap())
    if value is None:
        _ = block.pop(key, None)
    else:
        block[key] = value
    return _replace_config_block(
        project_root=project_root, path=config_path, text=text, block=block
    )


def write_config_map_entry(
    *,
    project_root: Path,
    map_key: str,
    entry_key: str,
    value: str | None,
) -> IOResult[Path, ValidationError]:
    """Set or clear one entry in a spec_governance config map.

    Same contract as `write_config_value`: an unreadable existing block refuses
    rather than being overwritten.
    """
    config_path = project_root / _CONFIG_PATH
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else "{\n}\n"
    existing = _extract_block(text=text)
    if isinstance(existing, Failure):
        return IOFailure(existing.failure())
    block = dict(existing.unwrap())
    raw_map = block.get(map_key)
    mapping = _string_map(value=raw_map)
    if value is None:
        _ = mapping.pop(entry_key, None)
    else:
        mapping[entry_key] = value
    if mapping:
        block[map_key] = dict(sorted(mapping.items()))
    else:
        _ = block.pop(map_key, None)
    return _replace_config_block(
        project_root=project_root, path=config_path, text=text, block=block
    )


def _extract_block(*, text: str) -> Result[dict[str, Any], ValidationError]:
    """The existing `spec_governance` block; `{}` on SUCCESS when there is none.

    ⛔ FOUR SITUATIONS USED TO COLLAPSE INTO `{}` HERE, and only one of them is an
    answer. An ABSENT block means "nothing is configured yet", and the caller is
    right to render a fresh one. A block that does NOT PARSE, one whose braces do
    not close, and one that is not an object are FAILURES — and folding them into
    an empty mapping made the caller believe there was nothing to preserve, so it
    rendered the single key being written and `_replace_existing_block` overwrote
    every sibling. The call then returned the SUCCESS spelling.

    ⚠️ THE TRIGGER WAS A COMMENT — the entire reason this file is `.jsonc`. Parsing
    is now done with `jsonc.loads`, exactly as the READ half in `config.py` already
    did, so a legitimately commented block is preserved rather than destroyed.
    """
    marker = '"spec_governance"'
    if marker not in text:
        return Success({})
    start = text.find(marker)
    brace = text.find("{", start)
    if brace < 0:
        return Failure(ValidationError("spec_governance block has no opening brace"))
    end = _matching_brace(text=text, start=brace)
    if end < 0:
        return Failure(ValidationError("spec_governance block is unterminated"))
    parsed_result = jsonc.loads(text=text[brace : end + 1])
    if isinstance(parsed_result, Failure):
        return Failure(ValidationError("spec_governance block does not parse as JSONC"))
    # No wrong-shape guard here on purpose: the slice always begins at `{` and ends
    # at its matching `}`, so `jsonc.loads` either yields a dict or fails above. A
    # guard for the impossible case would be a branch that reads as protection and
    # cannot execute — the defect `8o8e.19` was filed for.
    return Success(cast(dict[str, Any], parsed_result.unwrap()))


def _replace_config_block(
    *,
    project_root: Path,
    path: Path,
    text: str,
    block: dict[str, Any],
) -> IOResult[Path, ValidationError]:
    rendered = _render_block(block=block)
    marker = '"spec_governance"'
    if marker not in text:
        updated = _insert_block(text=text, rendered=rendered)
    else:
        updated = _replace_existing_block(text=text, rendered=rendered)
    return IOSuccess(_atomic_replace(project_root=project_root, path=path, updated=updated))


def _replace_existing_scalar(*, text: str, key: str, value: str | None) -> str | None:
    marker = '"spec_governance"'
    start = text.find(marker)
    if start < 0:
        return None
    brace = text.find("{", start)
    end = _matching_brace(text=text, start=brace)
    if brace < 0 or end < 0:
        return None
    encoded_key = re.escape(json.dumps(key))
    pattern = re.compile(
        rf'^[ \t]*{encoded_key}[ \t]*:[ \t]*(?P<value>"(?:\\.|[^"\\])*")'
        rf"(?P<comma>,?)[ \t]*(?://[^\n]*)?(?:\n|$)",
        flags=re.MULTILINE,
    )
    match = pattern.search(text, brace + 1, end)
    if match is None:
        return None
    if value is not None:
        value_start, value_end = match.span("value")
        return f"{text[:value_start]}{json.dumps(value)}{text[value_end:]}"
    return _remove_scalar_member(
        text=text,
        block_start=brace,
        match=match,
    )


def _remove_scalar_member(*, text: str, block_start: int, match: re.Match[str]) -> str:
    if match.group("comma"):
        return f"{text[: match.start()]}{text[match.end() :]}"
    prefix = text[: match.start()]
    prior_members = tuple(
        re.finditer(
            r'^[ \t]*"(?:\\.|[^"\\])*"[ \t]*:[ \t]*'
            r'"(?:\\.|[^"\\])*"(?P<comma>,)[ \t]*(?://[^\n]*)?(?:\n|$)',
            prefix[block_start + 1 :],
            flags=re.MULTILINE,
        )
    )
    if prior_members:
        comma = block_start + 1 + prior_members[-1].start("comma")
        prefix = f"{prefix[:comma]}{prefix[comma + 1:]}"
    return f"{prefix}{text[match.end() :]}"


def _atomic_replace(*, project_root: Path, path: Path, updated: str) -> Path:
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    _ = temp_path.write_text(updated, encoding="utf-8")
    _ = temp_path.replace(path)
    return path.relative_to(project_root)


def _string_map(*, value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, item in cast(dict[object, object], value).items():
        if isinstance(key, str) and isinstance(item, str):
            out[key] = item
    return out


def _replace_existing_block(*, text: str, rendered: str) -> str:
    marker = '"spec_governance"'
    start = text.find(marker)
    key_start = text.rfind("\n", 0, start) + 1
    # Reached only after `_extract_block` has parsed this same block, so the braces
    # are known to be present and balanced; re-guarding them here would be dead code.
    brace = text.find("{", start)
    end = _matching_brace(text=text, start=brace)
    replacement_start = key_start
    if "{" in text[key_start:start]:
        replacement_start = start
    line_end = end + 1
    trailing_comma = ""
    if line_end < len(text) and text[line_end] == ",":
        trailing_comma = ","
        line_end += 1
    return f"{text[:replacement_start]}{rendered}{trailing_comma}{text[line_end:]}"


def _render_block(*, block: dict[str, Any]) -> str:
    payload = json.dumps({"spec_governance": block}, indent=2, sort_keys=True)
    return "\n".join(payload.splitlines()[1:-1])


def _insert_block(*, text: str, rendered: str) -> str:
    stripped = text.rstrip()
    if stripped == "{":
        return f"{{\n{rendered}\n}}\n"
    if stripped.endswith("{"):
        return f"{stripped}\n{rendered}\n}}\n"
    insert_at = stripped.rfind("}")
    prefix = stripped[:insert_at].rstrip()
    comma = "," if not prefix.endswith("{") else ""
    return f"{prefix}{comma}\n{rendered}\n}}\n"


def _matching_brace(*, text: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1
