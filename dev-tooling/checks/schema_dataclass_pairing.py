"""schema_dataclass_pairing — schema → dataclass → validator triplet pairing.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-schema-dataclass-pairing` row), for
every `.claude-plugin/scripts/livespec/schemas/*.schema.json`,
verifies a paired dataclass at
`schemas/dataclasses/<name>.py` AND a paired validator at
`validate/<name>.py` exists.

Cycle 170 (minimum-viable) implements the file-presence
triplet check. Subsequent cycles add field-by-field type
verification (the v013 M6 three-way walker that verifies
every listed schema field matches the dataclass's Python
type and vice versa).

Output discipline: per spec lines 1738-1762, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_SCHEMAS_DIR = Path(".claude-plugin") / "scripts" / "livespec" / "schemas"
_DATACLASSES_DIR = (
    Path(".claude-plugin") / "scripts" / "livespec" / "schemas" / "dataclasses"
)
_VALIDATE_DIR = Path(".claude-plugin") / "scripts" / "livespec" / "validate"
_SCHEMA_SUFFIX = ".schema.json"


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("schema_dataclass_pairing")
    cwd = Path.cwd()
    schemas_root = cwd / _SCHEMAS_DIR
    if not schemas_root.is_dir():
        return 0
    issues: list[tuple[str, str, str]] = []
    for schema_path in sorted(schemas_root.glob(f"*{_SCHEMA_SUFFIX}")):
        name = schema_path.name[: -len(_SCHEMA_SUFFIX)]
        expected_dataclass = cwd / _DATACLASSES_DIR / f"{name}.py"
        expected_validator = cwd / _VALIDATE_DIR / f"{name}.py"
        if not expected_dataclass.is_file():
            issues.append(
                (name, "dataclass", str(expected_dataclass.relative_to(cwd))),
            )
        if not expected_validator.is_file():
            issues.append(
                (name, "validator", str(expected_validator.relative_to(cwd))),
            )
    if issues:
        for name, kind, expected_path in issues:
            log.error(
                "schema missing paired %s",
                kind,
                schema_name=name,
                missing_kind=kind,
                expected_path=expected_path,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
