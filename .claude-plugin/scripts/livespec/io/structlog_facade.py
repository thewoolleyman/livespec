"""Typed wrapper over vendored structlog (`Any` confined here).

`io/` hosts typed facades over vendored libraries whose surface
types are not strict-pyright-clean. The vendored `structlog`
library returns `Any`-typed `BoundLogger` instances from
`get_logger()` and accepts arbitrary keyword arguments on each
log method. This facade narrows the surface to a typed `Logger`
Protocol with explicit method signatures.

`structlog.configure(...)` and `bind_contextvars(run_id=...)`
already happened once per process in `livespec/__init__.py`.
This module provides only the typed accessor; it does not
re-configure.

Style rules (style doc §"Structured logging"):
- Kwargs only — `log.error("parse failed", path=str(p))`. Never
  f-strings in messages; the message is a stable literal.
- Errors include structured fields — pass `LivespecError`
  subclass name and structured context as kwargs, not bare
  `str(exc)`.
- stdout is reserved (per `check-no-write-direct`); structlog
  writes JSON to stderr.

The kwargs-only call-site discipline is enforced separately by
ruff `LOG`/`G` categories (flake8-logging / flake8-logging-format)
on the call sites; the facade just provides the typed surface.
"""
from __future__ import annotations

from typing import Protocol, cast

import structlog

__all__: list[str] = [
    "Logger",
    "get_logger",
]


class Logger(Protocol):
    """Typed surface for a structlog `BoundLogger`.

    Each method takes a stable literal `message` plus arbitrary
    keyword arguments that become structured fields on the emitted
    JSON line. Levels are filtered by the
    `make_filtering_bound_logger(_resolve_log_level())` wrapper
    configured in `livespec/__init__.py`.

    `Protocol` declares the structural shape — any object with
    matching method signatures satisfies the protocol at runtime
    via duck typing; pyright type-checks structurally at
    construction sites. The Logger Protocol does NOT inherit
    `runtime_checkable`; structural conformance is a static check.
    """

    def debug(self, message: str, **kwargs: object) -> None:
        """Log at DEBUG level (typically suppressed by default)."""

    def info(self, message: str, **kwargs: object) -> None:
        """Log at INFO level."""

    def warning(self, message: str, **kwargs: object) -> None:
        """Log at WARNING level (the default minimum)."""

    def error(self, message: str, **kwargs: object) -> None:
        """Log at ERROR level."""

    def critical(self, message: str, **kwargs: object) -> None:
        """Log at CRITICAL level."""


def get_logger(name: str) -> Logger:
    """Return a typed `Logger` bound to `name` (typically `__name__`).

    Thin wrapper over `structlog.get_logger(name)` that casts the
    `Any`-typed `BoundLogger` to the `Logger` Protocol so callers
    see typed method signatures.
    """
    return cast("Logger", structlog.get_logger(name))
