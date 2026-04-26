"""Typed wrapper over vendored structlog (`Any` confined here).

Phase 2 placeholder. Real `get_logger`, `log_info`, `log_warning`,
`log_error` typed surfaces land alongside the first call site. The
`structlog.configure(...)` and `bind_contextvars(run_id=...)` calls
in `livespec/__init__.py` are the canonical configuration site;
everything else uses this facade.
"""

__all__: list[str] = []
