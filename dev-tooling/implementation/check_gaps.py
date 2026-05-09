"""check_gaps — validate implementation-gaps/current.json against its schema.

Per `SPECIFICATION/non-functional-requirements.md` §Contracts
§"Implementation-gap report shape", the gap report at
`implementation-gaps/current.json` MUST be machine-readable JSON
that validates against `implementation-gaps/current.schema.json`.

This check loads both files, runs JSON-Schema validation via the
vendored `fastjsonschema`, and surfaces every validation error
through structlog. Exit 0 on full conformance; exit 1 on any
violation (or when either file is missing).

Output discipline: per spec, `print` and `sys.stderr.write` are
banned in dev-tooling/**. Diagnostics flow through structlog
(JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path`
at module import time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import fastjsonschema  # noqa: E402  — vendor-path-aware import after sys.path insert.
import structlog  # noqa: E402  — same.

__all__: list[str] = []


_REPORT_PATH = Path("implementation-gaps") / "current.json"
_SCHEMA_PATH = Path("implementation-gaps") / "current.schema.json"


def _load_json(*, path: Path) -> dict[str, object] | None:
    """Read a JSON file. Returns the parsed object or None if the file is missing or malformed.

    `dict[str, object]` is the loose return type because both the schema
    and the report are top-level objects keyed by string. The caller
    tolerates either being None and reports the error itself.
    """
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> int:
    """Validate implementation-gaps/current.json against its schema.

    Steps:
    1. Configure structlog for JSON-on-stderr output (matching the
       existing dev-tooling/checks/* pattern).
    2. Load both files; surface a clean error if either is missing
       or malformed.
    3. Compile the schema into a validator function via
       fastjsonschema.compile.
    4. Run the validator. fastjsonschema raises
       fastjsonschema.JsonSchemaValueException with .message,
       .name, and .value attributes when the document is invalid.
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("check_gaps")

    schema = _load_json(path=_SCHEMA_PATH)
    if schema is None:
        log.error("schema missing or malformed", path=str(_SCHEMA_PATH))
        return 1

    report = _load_json(path=_REPORT_PATH)
    if report is None:
        log.error(
            "implementation-gap report missing or malformed",
            path=str(_REPORT_PATH),
            hint="run `just implementation::refresh-gaps` to (re)generate",
        )
        return 1

    try:
        validate = fastjsonschema.compile(schema)
    except fastjsonschema.JsonSchemaDefinitionException as exc:
        log.exception(
            "schema is itself invalid (definition exception)",
            path=str(_SCHEMA_PATH),
            message=str(exc),
        )
        return 1

    try:
        validate(report)
    except fastjsonschema.JsonSchemaValueException as exc:
        log.exception(
            "implementation-gap report failed schema validation",
            path=str(_REPORT_PATH),
            schema_path=str(_SCHEMA_PATH),
            field=exc.name,
            message=exc.message,
        )
        return 1

    log.info(
        "implementation-gap report conforms to schema",
        report=str(_REPORT_PATH),
        gap_count=len(report.get("gaps", [])) if isinstance(report.get("gaps"), list) else 0,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
