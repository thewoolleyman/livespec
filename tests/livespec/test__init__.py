"""Stub paired test for `livespec/__init__.py` per mirror-pairing rule.

The package's `__init__.py` configures structlog and binds the
per-invocation `run_id`. Both side-effects are exempt from
`check-global-writes` per style doc §"Bootstrap" and run at first
import. The verification this test owns: the module imports
cleanly and the per-invocation `run_id` is bound after import.
Logger-output behavior is exercised transitively by every other
test that imports `livespec.*`.
"""

from __future__ import annotations

import structlog

__all__: list[str] = []


def test_livespec_init_binds_run_id() -> None:
    """Importing `livespec` binds a non-empty `run_id` into structlog's contextvars."""
    import livespec  # noqa: F401 — import side-effect: configures structlog + binds run_id.

    bound = structlog.contextvars.get_contextvars()
    assert "run_id" in bound
    assert isinstance(bound["run_id"], str)
    assert len(bound["run_id"]) > 0
