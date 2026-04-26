"""livespec package: configures structlog and binds the per-invocation run_id.

This module runs at first-import time. Each `bin/*.py` shebang wrapper
imports `livespec.commands.<cmd>` (or `livespec.doctor.run_static`),
which transitively imports `livespec`, triggering this configuration.
One configuration per process; each wrapper invocation is its own
process.

The structlog config emits JSON to stderr with the standard fields
documented in python-skill-script-style-requirements.md §"Logging":
`timestamp` (ISO 8601 UTC), `level`, `logger`, `message`, `run_id`
(uuid4 bound here), plus arbitrary kwargs from the call site. Level is
controlled by `LIVESPEC_LOG_LEVEL` env var (default `WARNING`); the
`-v` / `-vv` CLI flag override is layered on at supervisor scope.

The two side-effecting calls below (`structlog.configure`,
`bind_contextvars`) are exempt from `check-global-writes` per the
style doc §"Bootstrap" — they configure third-party library state,
not livespec module-level state.
"""
import logging
import os
import sys
import uuid

import structlog

__all__: list[str] = []


def _resolve_log_level() -> int:
    name = os.environ.get("LIVESPEC_LOG_LEVEL", "WARNING").upper()
    return getattr(logging, name, logging.WARNING)


structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(_resolve_log_level()),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)
structlog.contextvars.bind_contextvars(run_id=str(uuid.uuid4()))
