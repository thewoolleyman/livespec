"""schema_dataclass_pairing — three-way schema/dataclass/validator pairing (v013 M6).

Per `python-skill-script-style-requirements.md` line 2083:

    AST (three-way walker per v013 M6): for every
    `schemas/*.schema.json`, verifies a paired dataclass at
    `schemas/dataclasses/<name>.py` (the `$id`-derived name) AND
    a paired validator at `validate/<name>.py` exists; every
    listed schema field matches the dataclass's Python type;
    vice versa in all three walks. Drift in any direction fails.

Cycle 48 pins ONE narrow violation pattern per v032 D1
one-pattern-per-cycle: the **dataclass-without-schema** drift
direction. A `livespec/schemas/dataclasses/<name>.py` (any name
other than `__init__.py`) whose corresponding
`livespec/schemas/<name>.schema.json` does NOT exist is
rejected. The other two drift directions
(schema-without-dataclass, dataclass-without-validator) and
field-by-field type matching are deferred to subsequent cycles
per v032 D1.

The current repo's only dataclass file is `finding.py` paired
with `finding.schema.json`; the rule passes today and catches
the next agent who lands a dataclass file without its companion
schema.
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
_DATACLASSES_DIR = _SCHEMAS_DIR / "dataclasses"
_INIT_FILENAME = "__init__.py"


def _iter_dataclass_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.glob("*.py") if p.is_file() and p.name != _INIT_FILENAME)


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
    dataclasses_root = cwd / _DATACLASSES_DIR
    schemas_root = cwd / _SCHEMAS_DIR
    if not dataclasses_root.is_dir():
        return 0
    found_any = False
    for dataclass_file in _iter_dataclass_files(root=dataclasses_root):
        stem = dataclass_file.stem
        expected_schema = schemas_root / f"{stem}.schema.json"
        if not expected_schema.is_file():
            log.error(
                "dataclass file has no paired schema",
                path=str(dataclass_file.relative_to(cwd)),
                expected_schema=str(expected_schema.relative_to(cwd)),
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
