"""Tests for .claude-plugin/scripts/bin/_bootstrap.py.

Covers `_bootstrap.bootstrap()` per Phase 5 plan: both sides of the
`sys.version_info < (3, 10)` check are exercised via
`monkeypatch.setattr(sys, "version_info", ...)`. Pragma exclusions
on `bin/*.py` are forbidden by v011 K3, so branch coverage of the
exit-127 path is achieved exclusively through monkeypatching.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"
_BUNDLE_SCRIPTS = _BIN_DIR.parent
_BUNDLE_VENDOR = _BUNDLE_SCRIPTS / "_vendor"
_EXIT_CODE_VERSION_MISMATCH = 127


def _import_bootstrap() -> object:
    """Import `_bootstrap` fresh, ensuring `bin/` is on sys.path.

    Removes any stale module entry first so each test sees a clean
    import (the wrapper-coverage tests pre-populate
    sys.modules['_bootstrap'] with a stub; this helper replaces
    that stub with the real module under test).
    """
    if str(_BIN_DIR) not in sys.path:
        sys.path.insert(0, str(_BIN_DIR))
    sys.modules.pop("_bootstrap", None)
    return importlib.import_module("_bootstrap")


def test_bootstrap_exits_on_old_python(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """sys.version_info < (3, 10) raises SystemExit(127) with the canonical message."""
    bootstrap_module = _import_bootstrap()
    monkeypatch.setattr(sys, "version_info", (3, 9, 0, "final", 0))
    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert excinfo.value.code == _EXIT_CODE_VERSION_MISMATCH


def test_bootstrap_inserts_paths_when_missing(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """sys.version_info >= (3, 10) inserts the bundle scripts/ and _vendor/ paths into sys.path."""
    bootstrap_module = _import_bootstrap()
    fresh_path: list[str] = ["/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", fresh_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert str(_BUNDLE_SCRIPTS) in sys.path
    assert str(_BUNDLE_VENDOR) in sys.path


def test_bootstrap_skips_paths_already_present(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """When a bundle path is already in sys.path, bootstrap() does NOT duplicate it.

    Covers the False branch of `if path_str not in sys.path` so
    branch coverage of the loop body stays at 100%.
    """
    bootstrap_module = _import_bootstrap()
    seeded_path: list[str] = [str(_BUNDLE_SCRIPTS), str(_BUNDLE_VENDOR), "/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", seeded_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert sys.path.count(str(_BUNDLE_SCRIPTS)) == 1
    assert sys.path.count(str(_BUNDLE_VENDOR)) == 1
