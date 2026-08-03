"""JSONC text replacement helpers for spec-governance config edits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

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
) -> Path | str:
    """Set or clear one scalar spec_governance config value."""
    config_path = project_root / _CONFIG_PATH
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else "{\n}\n"
    block = dict(_extract_block(text=text))
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
) -> Path | str:
    """Set or clear one entry in a spec_governance config map."""
    config_path = project_root / _CONFIG_PATH
    text = config_path.read_text(encoding="utf-8") if config_path.exists() else "{\n}\n"
    block = dict(_extract_block(text=text))
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


def _extract_block(*, text: str) -> dict[str, Any]:
    marker = '"spec_governance"'
    if marker not in text:
        return {}
    start = text.find(marker)
    brace = text.find("{", start)
    if brace < 0:
        return {}
    end = _matching_brace(text=text, start=brace)
    if end < 0:
        return {}
    try:
        parsed = json.loads(text[brace : end + 1])
    except json.JSONDecodeError:
        return {}
    return cast(dict[str, Any], parsed) if isinstance(parsed, dict) else {}


def _replace_config_block(
    *,
    project_root: Path,
    path: Path,
    text: str,
    block: dict[str, Any],
) -> Path | str:
    rendered = _render_block(block=block)
    marker = '"spec_governance"'
    if marker not in text:
        updated = _insert_block(text=text, rendered=rendered)
    else:
        updated_or_error = _replace_existing_block(text=text, rendered=rendered)
        if updated_or_error.startswith("existing "):
            return updated_or_error
        updated = updated_or_error
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
    brace = text.find("{", start)
    end = _matching_brace(text=text, start=brace)
    if brace < 0 or end < 0:
        return "existing spec_governance block is malformed"
    line_end = end + 1
    if line_end < len(text) and text[line_end] == ",":
        line_end += 1
    return f"{text[:key_start]}{rendered}{text[line_end:]}"


def _render_block(*, block: dict[str, Any]) -> str:
    payload = json.dumps({"spec_governance": block}, indent=2, sort_keys=True)
    return ",\n".join(payload.splitlines()[1:-1])


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
