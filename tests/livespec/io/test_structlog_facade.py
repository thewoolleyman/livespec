"""Tests for livespec.io.structlog_facade."""

from __future__ import annotations

from typing import Any

from livespec.io import structlog_facade

__all__: list[str] = []


def test_get_logger_returns_typed_wrapper_that_forwards_error(
    *,
    monkeypatch: Any,
) -> None:
    """Facade loggers forward typed error calls to the underlying structlog logger."""
    events: list[tuple[str, str, dict[str, object]]] = []

    class FakeStructlogLogger:
        def error(self, event: str, **kwargs: object) -> None:
            events.append(("error", event, kwargs))

    def fake_get_logger(name: str) -> FakeStructlogLogger:
        events.append(("get_logger", name, {}))
        return FakeStructlogLogger()

    monkeypatch.setattr(structlog_facade.structlog, "get_logger", fake_get_logger)

    logger = structlog_facade.get_logger(name="livespec.test")
    logger.error(
        message="revise failed",
        error_type="PreconditionError",
        exit_code=3,
    )

    assert events == [
        ("get_logger", "livespec.test", {}),
        (
            "error",
            "revise failed",
            {"error_type": "PreconditionError", "exit_code": 3},
        ),
    ]


def test_configure_logging_delegates_structlog_configuration(
    *,
    monkeypatch: Any,
) -> None:
    """The package init configuration path is available through the facade."""
    calls: list[tuple[str, dict[str, object]]] = []
    wrapper_class = object()
    logger_factory = object()
    stream = object()

    def fake_make_filtering_bound_logger(log_level: int) -> object:
        calls.append(("make_filtering_bound_logger", {"log_level": log_level}))
        return wrapper_class

    def fake_print_logger_factory(*, file: object) -> object:
        calls.append(("PrintLoggerFactory", {"file": file}))
        return logger_factory

    def fake_configure(**kwargs: object) -> None:
        calls.append(("configure", kwargs))

    monkeypatch.setattr(
        structlog_facade.structlog,
        "make_filtering_bound_logger",
        fake_make_filtering_bound_logger,
    )
    monkeypatch.setattr(
        structlog_facade.structlog,
        "PrintLoggerFactory",
        fake_print_logger_factory,
    )
    monkeypatch.setattr(structlog_facade.structlog, "configure", fake_configure)

    structlog_facade.configure_logging(log_level=20, stream=stream)

    assert calls[-1] == (
        "configure",
        {
            "processors": [
                structlog_facade.structlog.contextvars.merge_contextvars,
                structlog_facade.structlog.processors.add_log_level,
                calls[-1][1]["processors"][2],
                calls[-1][1]["processors"][3],
            ],
            "wrapper_class": wrapper_class,
            "logger_factory": logger_factory,
            "cache_logger_on_first_use": True,
        },
    )


def test_bind_contextvars_delegates_to_structlog_contextvars(
    *,
    monkeypatch: Any,
) -> None:
    """The package init run_id binding path is available through the facade."""
    calls: list[dict[str, object]] = []

    def fake_bind_contextvars(**kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        structlog_facade.structlog.contextvars,
        "bind_contextvars",
        fake_bind_contextvars,
    )

    structlog_facade.bind_contextvars(run_id="run-123")

    assert calls == [{"run_id": "run-123"}]
