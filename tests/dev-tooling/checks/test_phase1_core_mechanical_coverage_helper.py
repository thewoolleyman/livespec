"""Coverage for the Phase-1 mechanical regression-test helper."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []

_TEST_MODULE = Path(__file__).with_name("test_phase1_core_mechanical_coverage.py")


def _load_phase1_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "phase1_core_mechanical_coverage_for_test",
        _TEST_MODULE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fake_main() -> int:
    json.dump({"newly_covered": False, "file": "ignored.py"}, sys.stderr)
    _ = sys.stderr.write("\n")
    json.dump({"newly_covered": True, "file": "example.py"}, sys.stderr)
    return 0


def test_newly_covered_events_parses_warning_lines(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_phase1_module()
    fake_check = ModuleType("fake_check")
    fake_check.__dict__["main"] = _fake_main

    events = module._newly_covered_events(  # noqa: SLF001
        check_module=fake_check,
        capsys=capsys,
        monkeypatch=monkeypatch,
    )

    assert events == [{"newly_covered": True, "file": "example.py"}]
