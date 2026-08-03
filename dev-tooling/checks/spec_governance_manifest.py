"""spec_governance_manifest — registry/manifest completeness check."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402

__all__: list[str] = []

_REGISTRY_PATH = Path(".claude-plugin") / "scripts" / "livespec" / "spec_governance" / "registry.py"
_MANIFEST_PATH = (
    Path(".claude-plugin")
    / "scripts"
    / "livespec"
    / "spec_governance"
    / "api_configurable_keys.json"
)


def main() -> int:
    """Compare registry ConfigKey rows against the committed manifest."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("spec_governance_manifest")
    cwd = Path.cwd()
    registry_path = cwd / _REGISTRY_PATH
    manifest_path = cwd / _MANIFEST_PATH
    if not registry_path.is_file() and not manifest_path.is_file():
        return 0
    registry_rows = _registry_rows(path=registry_path)
    manifest_rows = _manifest_rows(path=manifest_path)
    if registry_rows == manifest_rows:
        return 0
    log.error(
        "spec governance registry/manifest drift",
        registry_rows=registry_rows,
        manifest_rows=manifest_rows,
    )
    return 1


def _registry_rows(*, path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node=node) == "ConfigKey":
            row: dict[str, Any] = {}
            for keyword in node.keywords:
                if keyword.arg is not None:
                    row[keyword.arg] = ast.literal_eval(keyword.value)
            if "key" not in row:
                continue
            rows.append(
                {
                    "key": row["key"],
                    "value_type": row["value_type"],
                    "safe_default": row["safe_default"],
                    "per_proposal_override": row["per_proposal_override"],
                    "allowed_values": row["allowed_values"],
                },
            )
    return rows


def _manifest_rows(*, path: Path) -> list[dict[str, Any]]:
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(parsed, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in cast(list[object], parsed):
        if isinstance(item, dict):
            rows.append(cast(dict[str, Any], item))
    return rows


def _call_name(*, node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
