"""spec_governance_template - template/manifest agreement check.

The orchestrator-plugin copier template documents `spec_governance` as a
commented optional block in `.livespec.jsonc.jinja`. That block is intentionally
commented out so a generated repo arms no policy by default, but it still needs
to advertise every API-configurable key and its safe default. This check compares
the commented block against the shipped spec-governance manifest and fails when
the template omits a key or documents a different default.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal, TypedDict, cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402

__all__: list[str] = []

_MANIFEST_PATH = (
    Path(".claude-plugin")
    / "scripts"
    / "livespec"
    / "spec_governance"
    / "api_configurable_keys.json"
)
_TEMPLATE_PATH = Path("templates") / "orchestrator-plugin" / ".livespec.jsonc.jinja"
_BLOCK_START = "// Optional \u2014 spec_governance:"
_BLOCK_END = "// Optional \u2014 credential_wrapper:"


class _ManifestRow(TypedDict):
    key: str
    value_type: Literal["enum", "map", "string"]
    safe_default: str | dict[str, str] | None
    per_proposal_override: str | None
    allowed_values: list[str]


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("spec_governance_template")


def _manifest_rows(*, manifest_path: Path) -> list[_ManifestRow]:
    parsed = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(parsed, list):
        return []
    rows: list[_ManifestRow] = []
    for item in cast(list[object], parsed):
        if isinstance(item, dict):
            rows.append(cast(_ManifestRow, item))
    return rows


def _comment_block(*, template_text: str) -> list[str] | None:
    lines = template_text.splitlines()
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


def _documented_defaults(*, block: list[str]) -> dict[str, object] | None:
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
    if not uncommented:
        return None
    parsed = cast(object, json.loads("\n".join(["{", *uncommented, "}"])))
    parsed_dict = cast(dict[str, object], parsed)
    block_value = parsed_dict.get("spec_governance")
    if not isinstance(block_value, dict):
        return None
    return cast(dict[str, object], block_value)


def _verify_template(*, cwd: Path, log: structlog.stdlib.BoundLogger) -> int:
    manifest_path = cwd / _MANIFEST_PATH
    template_path = cwd / _TEMPLATE_PATH
    if not manifest_path.is_file() or not template_path.is_file():
        log.error(
            "spec-governance manifest/template files not found",
            check_id="spec-governance-template-missing-files",
            manifest_path=str(_MANIFEST_PATH),
            template_path=str(_TEMPLATE_PATH),
            hint="Run from the livespec-core repo root.",
        )
        return 1
    rows = _manifest_rows(manifest_path=manifest_path)
    block = _comment_block(template_text=template_path.read_text(encoding="utf-8"))
    documented = None if block is None else _documented_defaults(block=block)
    if documented is None:
        log.error(
            "commented spec_governance template block is absent or unparsable",
            check_id="spec-governance-template-block-invalid",
            path=str(_TEMPLATE_PATH),
        )
        return 1
    expected = {row["key"]: row["safe_default"] for row in rows}
    if documented == expected:
        log.info(
            "commented spec_governance template block matches the manifest",
            check_id="spec-governance-template-ok",
            key_count=len(expected),
        )
        return 0
    log.error(
        "commented spec_governance template block has drifted from the manifest",
        check_id="spec-governance-template-drift",
        path=str(_TEMPLATE_PATH),
        missing=sorted(set(expected) - set(documented)),
        extra=sorted(set(documented) - set(expected)),
        default_drift=sorted(
            key for key, value in expected.items() if documented.get(key) != value
        ),
        hint=(
            "Update templates/orchestrator-plugin/.livespec.jsonc.jinja so the "
            "commented spec_governance block lists every manifest key at its safe default."
        ),
    )
    return 1


def main() -> int:
    log = _configure_logger()
    return _verify_template(cwd=Path.cwd(), log=log)


if __name__ == "__main__":
    raise SystemExit(main())
