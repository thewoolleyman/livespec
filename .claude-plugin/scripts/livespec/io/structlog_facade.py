"""Typed facade for the vendored structlog package."""

from __future__ import annotations

from typing import Any, TextIO, cast

import structlog

__all__: list[str] = [
    "Logger",
    "bind_contextvars",
    "configure_logging",
    "debug",
    "error",
    "get_logger",
    "info",
    "structlog",
    "warning",
]


class Logger:
    """Typed wrapper around a structlog bound logger."""

    def __init__(self, *, logger: Any) -> None:
        self._logger = logger

    def debug(self, *, message: str, **kwargs: object) -> None:  # pragma: no cover
        self._logger.debug(message, **kwargs)

    def info(self, *, message: str, **kwargs: object) -> None:  # pragma: no cover
        self._logger.info(message, **kwargs)

    def warning(self, *, message: str, **kwargs: object) -> None:  # pragma: no cover
        self._logger.warning(message, **kwargs)

    def error(self, *, message: str, **kwargs: object) -> None:
        self._logger.error(message, **kwargs)


def configure_logging(*, log_level: int, stream: object) -> None:
    """Configure structlog's process-wide JSON logger."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=cast(TextIO, stream)),
        cache_logger_on_first_use=True,
    )


def bind_contextvars(*, run_id: str) -> None:
    """Bind per-invocation context fields into structlog contextvars."""
    _ = structlog.contextvars.bind_contextvars(run_id=run_id)


def get_logger(*, name: str) -> Logger:
    """Return a typed logger wrapper for `name`."""
    return Logger(logger=structlog.get_logger(name))


def debug(*, message: str, **kwargs: object) -> None:  # pragma: no cover
    """Emit a DEBUG-level event on the package logger."""
    get_logger(name="livespec").debug(message=message, **kwargs)


def info(*, message: str, **kwargs: object) -> None:  # pragma: no cover
    """Emit an INFO-level event on the package logger."""
    get_logger(name="livespec").info(message=message, **kwargs)


def warning(*, message: str, **kwargs: object) -> None:  # pragma: no cover
    """Emit a WARNING-level event on the package logger."""
    get_logger(name="livespec").warning(message=message, **kwargs)


def error(*, message: str, **kwargs: object) -> None:  # pragma: no cover
    """Emit an ERROR-level event on the package logger."""
    get_logger(name="livespec").error(message=message, **kwargs)
