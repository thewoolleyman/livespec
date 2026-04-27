"""vendor_manifest: validate `.vendor.jsonc` schema-conformance.

Per python-skill-script-style-requirements.md canonical target list
line 1898:

    Validates `.vendor.jsonc` against a schema that forbids
    placeholder strings — every entry has a non-empty
    `upstream_url`, a non-empty `upstream_ref`, a parseable-ISO
    `vendored_at`, and the `shim: true` flag is present on
    `jsoncomment` (the v026 D1 hand-authored shim) and absent on
    every other entry (post-v027 D1 `typing_extensions` is
    upstream-sourced, NOT a shim).

Manifest shape:

    {
      "libraries": [
        {
          "name": "<lib>",
          "upstream_url": "<url>",
          "upstream_ref": "<tag-or-sha>",
          "vendored_at": "<ISO-8601 timestamp>",
          "shim": true   // present-and-true on jsoncomment only
        },
        ...
      ]
    }

Validations per entry:

1. `name` is a non-empty string.
2. `upstream_url` is a non-empty string.
3. `upstream_ref` is a non-empty string AND not a documented
   placeholder (e.g., the literal `"PLACEHOLDER"`).
4. `vendored_at` parses as ISO-8601 (per `datetime.fromisoformat`).
5. `shim` field: present-and-True iff `name == "jsoncomment"`;
   absent on every other entry.

Top-level keys other than `libraries` are tolerated (the JSONC
preamble may carry comments/metadata). Unknown per-entry keys
fail (additionalProperties: false intent).
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

__all__: list[str] = [
    "check_repo",
    "main",
]


log = logging.getLogger(__name__)

_VENDOR_PATH = Path(".vendor.jsonc")
_PLACEHOLDER = "PLACEHOLDER"
_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "upstream_url",
        "upstream_ref",
        "vendored_at",
    }
)
_OPTIONAL_FIELDS: frozenset[str] = frozenset({"shim"})
_SHIM_LIB_NAME = "jsoncomment"


def main() -> int:
    """Validate `.vendor.jsonc`; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures = check_repo(repo_root=repo_root)
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("vendor_manifest: %d violation(s)", len(failures))
        return 1
    return 0


def check_repo(*, repo_root: Path) -> list[str]:
    """Validate `.vendor.jsonc` at `repo_root`. Return list of violation messages."""
    path = repo_root / _VENDOR_PATH
    if not path.is_file():
        return [f"{path}: file does not exist"]
    text = path.read_text(encoding="utf-8")
    parsed = _parse_jsonc(text=text)
    if parsed is None:
        return [f"{path}: cannot parse as JSON-with-comments"]
    libraries = parsed.get("libraries")
    if not isinstance(libraries, list):
        return [f"{path}: missing or non-list `libraries` key"]
    violations: list[str] = []
    for index, entry in enumerate(libraries):
        prefix = f"{path}: libraries[{index}]"
        if not isinstance(entry, dict):
            violations.append(f"{prefix}: not an object")
            continue
        violations.extend(_validate_entry(prefix=prefix, entry=entry))
    return violations


def _validate_entry(*, prefix: str, entry: dict[str, object]) -> list[str]:
    violations: list[str] = []
    actual_keys = set(entry.keys())
    missing = _REQUIRED_FIELDS - actual_keys
    if missing:
        violations.append(f"{prefix}: missing required field(s) {sorted(missing)}")
    extra = actual_keys - (_REQUIRED_FIELDS | _OPTIONAL_FIELDS)
    if extra:
        violations.append(f"{prefix}: unknown field(s) {sorted(extra)}")
    name = entry.get("name")
    for field in ("name", "upstream_url", "upstream_ref"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"{prefix}.{field}: missing or empty string")
    if entry.get("upstream_ref") == _PLACEHOLDER:
        violations.append(f"{prefix}.upstream_ref: placeholder string still present")
    vendored_at = entry.get("vendored_at")
    if not _is_parseable_iso(value=vendored_at):
        violations.append(f"{prefix}.vendored_at: not a parseable ISO-8601 string")
    violations.extend(_validate_shim_field(prefix=prefix, entry=entry, name=name))
    return violations


def _validate_shim_field(
    *,
    prefix: str,
    entry: dict[str, object],
    name: object,
) -> list[str]:
    has_shim = "shim" in entry
    shim_value = entry.get("shim")
    if name == _SHIM_LIB_NAME:
        if not (has_shim and shim_value is True):
            return [f"{prefix}: jsoncomment must declare `shim: true`"]
        return []
    if has_shim:
        return [f"{prefix}: only jsoncomment may declare `shim`; found on `{name}`"]
    return []


def _is_parseable_iso(*, value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _parse_jsonc(*, text: str) -> dict[str, object] | None:
    """Strip line comments (whole-line `// ...`) + parse as JSON.

    Conservative stripping: only lines whose first non-whitespace
    content is `//` are treated as comments. Mid-line `//`
    occurrences (e.g., URL strings like `https://github.com/...`)
    are preserved. Block comments (`/* ... */`) are not supported
    by the manifest's authoring convention, so they're not
    stripped here.
    """
    import json

    stripped_lines: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("//"):
            stripped_lines.append("")
        else:
            stripped_lines.append(line)
    try:
        doc = json.loads("\n".join(stripped_lines))
    except json.JSONDecodeError:
        return None
    if not isinstance(doc, dict):
        return None
    return doc


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
