"""Regression coverage for the livespec-2j46re Phase-1 mechanical slice."""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType

import pytest
from livespec_dev_tooling.checks import all_declared, global_writes, keyword_only_args

__all__: list[str] = []

pytestmark = [pytest.mark.integration]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECKS = (
    all_declared,
    keyword_only_args,
    global_writes,
)


def _newly_covered_events(
    *,
    check_module: ModuleType,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict[str, object]]:
    monkeypatch.chdir(_REPO_ROOT)
    return_code = check_module.main()
    captured = capsys.readouterr()
    assert return_code == 0, captured.err
    events: list[dict[str, object]] = []
    for line in captured.err.splitlines():
        loaded = json.loads(line)
        assert isinstance(loaded, dict)
        if loaded.get("newly_covered") is True:
            events.append(loaded)
    return events


@pytest.mark.parametrize("check_module", _CHECKS)
def test_phase1_core_mechanical_slice_has_no_newly_covered_warns(
    *,
    check_module: ModuleType,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        _newly_covered_events(
            check_module=check_module,
            capsys=capsys,
            monkeypatch=monkeypatch,
        )
        == []
    )
