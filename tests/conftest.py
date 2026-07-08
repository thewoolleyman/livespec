"""Top-level pytest conftest — autouse env scrubbing for inherited vars.

When the test suite runs under a git pre-commit hook (lefthook),
git exports `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, etc.,
pointing at the surrounding repository's git directory. Tests that
invoke `subprocess.run(["git", ...], cwd=tmp_path)` without
explicitly scrubbing those env vars will silently operate on the
surrounding repo (because `git init` with `GIT_DIR` set
re-initializes the GIT_DIR target rather than the cwd, and
subsequent commits go to the surrounding repo's refs).

The autouse fixture below scrubs the inherited GIT_* vars from
`os.environ` for the duration of every test, so subprocess git
calls inherit a clean environment and operate on the
tmp_path-scoped `.git` they create themselves.

Per-test-file `_scrub_git_env` helpers (in many existing tests)
remain as documentation + defense-in-depth and continue to work
unchanged — `monkeypatch.delenv` is idempotent when the var has
already been removed by this fixture.

The second autouse fixture (`_isolate_structlog_stream`) keeps
livespec's cached structlog logger bound to the live per-test
stderr; see its docstring for the closed-file flake it defends
against.
"""

from __future__ import annotations

import logging
import os
import sys

import pytest

__all__: list[str] = []


_GIT_ENV_PASSTHROUGH_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_LITERAL_PATHSPECS",
    "GIT_PREFIX",
)

_LIVESPEC_ENV_PASSTHROUGH_VARS: tuple[str, ...] = ("LIVESPEC_CURRENCY_GATE",)


@pytest.fixture(autouse=True)
def _scrub_inherited_git_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove inherited ambient env vars for every test."""
    for var in _GIT_ENV_PASSTHROUGH_VARS:
        monkeypatch.delenv(var, raising=False)
    for var in _LIVESPEC_ENV_PASSTHROUGH_VARS:
        monkeypatch.setenv(var, "warn")


def _resolve_log_level() -> int:
    """Mirror `livespec.__init__._resolve_log_level` for the test rebind."""
    name = os.environ.get("LIVESPEC_LOG_LEVEL", "WARNING").upper()
    return getattr(logging, name, logging.WARNING)


@pytest.fixture(autouse=True)
def _isolate_structlog_stream() -> None:
    """Rebind livespec's cached structlog logger to the live per-test stderr.

    `livespec.io.structlog_facade.configure_logging` builds structlog with
    `PrintLoggerFactory(file=stream)` + `cache_logger_on_first_use=True`. In
    PRODUCTION each `bin/*.py` invocation is its own process — one
    configuration, one stderr — so caching the underlying `PrintLogger` is
    correct. In the TEST process the package is imported once and the
    module-level logger proxy (currently `livespec.commands.revise._log`, the
    only persistent one) is cached process-wide: the first error-path `main()`
    call FREEZES it against whichever `sys.stderr` the factory captured at
    import time. Under `pytest -n auto` that captured stream can be a prior
    test's pytest capture object, which is closed at that test's teardown — so
    a later `main()` that error-logs writes to a closed file and raises
    `ValueError: I/O operation on closed file`, reddening the suite
    intermittently (e.g. `test_revise_main_exists_and_returns_int` and
    `test_revise_main_returns_usage_exit_code_on_missing_required_flag`).

    This fixture makes each test a faithful analog of a fresh production
    process: it re-establishes the livespec structlog configuration bound to
    THIS test's live `sys.stderr`, then clears every cached module-level
    facade-logger proxy so none survives across tests bound to a stale stream.
    Each re-created proxy re-freezes lazily against the freshly-bound factory
    on its next use. Production behavior (`structlog_facade.py`) is unchanged.
    """
    from livespec.io import structlog_facade

    structlog_facade.configure_logging(log_level=_resolve_log_level(), stream=sys.stderr)
    for module in list(sys.modules.values()):
        if not getattr(module, "__name__", "").startswith("livespec"):
            continue
        for attr_name, attr_value in list(vars(module).items()):
            if isinstance(attr_value, structlog_facade.Logger):
                setattr(module, attr_name, structlog_facade.get_logger(name=module.__name__))
