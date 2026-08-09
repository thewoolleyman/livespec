"""spec_governance_manifest — runtime manifest resource loadability check."""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Any, cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402
from livespec_runtime.spec_governance import manifest_rows  # noqa: E402

__all__: list[str] = []

_MANIFEST_PATH = (
    Path(".claude-plugin")
    / "scripts"
    / "_vendor"
    / "livespec_runtime"
    / "api_configurable_keys.json"
)


def main() -> int:
    """Compare the runtime loader projection against its vendored resource."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("spec_governance_manifest")
    manifest_path = Path.cwd() / _MANIFEST_PATH
    if not manifest_path.is_file():
        log.error(
            "spec governance runtime manifest resource missing",
            check_id="spec-governance-manifest-missing",
            manifest_path=str(_MANIFEST_PATH),
        )
        return 1
    resource_rows = _manifest_rows(path=manifest_path)
    loaded_rows = [dataclasses.asdict(row) for row in manifest_rows()]
    if loaded_rows == resource_rows:
        return 0
    log.error(
        "spec governance runtime manifest loader/resource drift",
        check_id="spec-governance-manifest-drift",
        loaded_rows=loaded_rows,
        resource_rows=resource_rows,
    )
    return 1


def _manifest_rows(*, path: Path) -> list[dict[str, Any]]:
    parsed = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(parsed, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in cast(list[object], parsed):
        if isinstance(item, dict):
            rows.append(cast(dict[str, Any], item))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
