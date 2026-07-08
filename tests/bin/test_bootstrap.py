"""Tests for .claude-plugin/scripts/bin/_bootstrap.py.

Covers `_bootstrap.bootstrap()`: the `sys.version_info < (3, 10)`
check (both branches, via `monkeypatch.setattr`), the sys.path
insertion, and the wiring that delegates the plugin-currency gate to
the sibling `_currency` package and acts on the returned
`CurrencyVerdict` (writes the message, raises SystemExit). The
currency LOGIC itself is covered under `tests/_currency/`.

Pragma exclusions on `bin/*.py` are forbidden by the coverage-
thresholds spec, so branch coverage of the exit-127 path is achieved
exclusively through monkeypatching.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import _currency
import pytest

__all__: list[str] = []


_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"
_BUNDLE_SCRIPTS = _BIN_DIR.parent
_BUNDLE_VENDOR = _BUNDLE_SCRIPTS / "_vendor"
_EXIT_CODE_VERSION_MISMATCH = 127
_EXIT_CODE_STALE_PLUGIN = 78


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

    Covers the False branch of `if entry_str not in sys.path` so
    branch coverage of `_insert_sys_path` stays at 100%.
    """
    bootstrap_module = _import_bootstrap()
    seeded_path: list[str] = [str(_BUNDLE_SCRIPTS), str(_BUNDLE_VENDOR), "/usr/lib/python3.10"]
    monkeypatch.setattr(sys, "path", seeded_path)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert sys.path.count(str(_BUNDLE_SCRIPTS)) == 1
    assert sys.path.count(str(_BUNDLE_VENDOR)) == 1


def _stub_verdict_bootstrap(
    *, monkeypatch: pytest.MonkeyPatch, verdict: _currency.CurrencyVerdict
) -> object:
    """Import `_bootstrap` with `_currency.verify_currency` stubbed to `verdict`."""
    bootstrap_module = _import_bootstrap()
    monkeypatch.setattr(sys, "path", ["/usr/lib/python3.10"])
    monkeypatch.setattr(sys, "version_info", (3, 12, 0, "final", 0))
    monkeypatch.setattr(_currency, "verify_currency", lambda: verdict)
    return bootstrap_module


def test_bootstrap_writes_message_and_hard_fails_on_stale_verdict(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hard-fail verdict makes bootstrap write the message and raise SystemExit(78)."""
    verdict = _currency.CurrencyVerdict(
        message="stale-message\n", hard_fail=True, gate_sensitive=False
    )
    bootstrap_module = _stub_verdict_bootstrap(monkeypatch=monkeypatch, verdict=verdict)
    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert excinfo.value.code == _EXIT_CODE_STALE_PLUGIN
    assert "stale-message" in capsys.readouterr().err


def test_bootstrap_writes_checkout_message_without_exiting(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-failing verdict with a message writes it and proceeds to set up sys.path."""
    verdict = _currency.CurrencyVerdict(
        message="checkout-message\n", hard_fail=False, gate_sensitive=False
    )
    bootstrap_module = _stub_verdict_bootstrap(monkeypatch=monkeypatch, verdict=verdict)
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert "checkout-message" in capsys.readouterr().err
    assert str(_BUNDLE_VENDOR) in sys.path


def test_bootstrap_gate_sensitive_verdict_warns_by_default_and_fails_under_gate(
    *, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gate-sensitive verdict proceeds by default and hard-fails when the gate is `fail`."""
    verdict = _currency.CurrencyVerdict(
        message="unknown-message\n", hard_fail=False, gate_sensitive=True
    )
    bootstrap_module = _stub_verdict_bootstrap(monkeypatch=monkeypatch, verdict=verdict)
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert str(_BUNDLE_VENDOR) in sys.path

    monkeypatch.setenv("LIVESPEC_CURRENCY_GATE", "fail")
    with pytest.raises(SystemExit) as excinfo:
        bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert excinfo.value.code == _EXIT_CODE_STALE_PLUGIN


def test_bootstrap_proceeds_silently_on_current_verdict(
    *, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A silent verdict (no message) writes nothing and completes sys.path setup."""
    verdict = _currency.CurrencyVerdict(message=None, hard_fail=False, gate_sensitive=False)
    bootstrap_module = _stub_verdict_bootstrap(monkeypatch=monkeypatch, verdict=verdict)
    bootstrap_module.bootstrap()  # type: ignore[attr-defined]
    assert capsys.readouterr().err == ""
    assert str(_BUNDLE_SCRIPTS) in sys.path
    assert str(_BUNDLE_VENDOR) in sys.path
