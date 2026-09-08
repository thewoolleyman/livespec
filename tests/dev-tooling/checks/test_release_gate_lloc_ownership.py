"""Every soft-band file must declare an owning work-item, at per-commit time.

WHY THIS EXISTS. `check-no-lloc-soft-warnings` is two-tier by design: per-commit
it logs soft-band files at WARNING and exits 0, while the release context sets
`LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST` and rejects any soft-band file with
no owning marker. That gap armed a time bomb TWICE. The second time,
`revise.py` (227 LLOC) and `spec_pr_merge_policy.py` (230 LLOC) sat unmarked
while local `just check` stayed green, and EVERY livespec release from v0.34.2
through v0.37.0 published through a failing gate — five cuts — plus five
consecutive failed `Release readiness` canaries. Nothing blocked, because the
only tier that fails runs after the tag already exists.

This test closes the reporting gap without collapsing the two tiers. It asserts
ONLY the ownership half — enter the soft band if you must, but declare who owes
the refactor — so entering the band stays ergonomic while entering it
ANONYMOUSLY becomes a per-commit failure. The release tier keeps everything
else it checks (a marker naming a closed or nonexistent item, mutation testing,
the heading-coverage TODO registry), so it is still the stricter gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_dev_tooling.checks import no_lloc_soft_warnings

__all__: list[str] = []

pytestmark = [pytest.mark.integration]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FAIL_LEVER = "LIVESPEC_FAIL_IF_LLOC_SOFT_WARNINGS_EXIST"


def _parse_events(*, stderr: str) -> list[dict[str, object]]:
    """Decode the check's structlog lines into event dicts.

    Split out of `_release_tier_events` so its coverage does not depend on the
    repository currently CARRYING soft-band debt. While `revise.py` and
    `spec_pr_merge_policy.py` sat in the band this loop was exercised
    incidentally by the real tree; discharging both markers emptied the band and
    turned it into dead code. That is the correct end state for the repo, so the
    parsing is proven against a synthetic line instead — a test whose coverage
    evaporates once the debt it guards is paid is a test that punishes success.
    """
    events: list[dict[str, object]] = []
    for line in stderr.splitlines():
        loaded = json.loads(line)
        assert isinstance(loaded, dict)
        events.append(loaded)
    return events


def _release_tier_events(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[int, list[dict[str, object]]]:
    """Run the check in RELEASE tier and return its exit code plus its events."""
    monkeypatch.chdir(_REPO_ROOT)
    monkeypatch.setenv(_FAIL_LEVER, "true")
    return_code = no_lloc_soft_warnings.main()
    captured = capsys.readouterr()
    return return_code, _parse_events(stderr=captured.err)


def test_parse_events_decodes_one_diagnostic_per_line() -> None:
    """The decoder is proven independently of the tree's current debt."""
    stderr = '{"file": "a.py", "failing": true}\n{"file": "b.py", "failing": false}\n'
    events = _parse_events(stderr=stderr)
    assert [event["file"] for event in events] == ["a.py", "b.py"]
    assert [event["failing"] for event in events] == [True, False]


def test_parse_events_returns_empty_when_the_band_is_clean() -> None:
    """No diagnostics is the SUCCESS shape, not a parse failure."""
    assert _parse_events(stderr="") == []


def test_no_soft_band_file_lacks_an_owning_work_item(
    *,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unmarked soft-band file fails HERE, not at the tag push."""
    return_code, events = _release_tier_events(capsys=capsys, monkeypatch=monkeypatch)
    unowned = [event for event in events if event.get("failing") is True]
    assert unowned == [], (
        "soft-band file(s) with no `# livespec-lloc-soft-band-owner:` marker — "
        "these fail the release gate AFTER the tag is pushed, so declare an "
        f"owning work-item now: {unowned}"
    )
    assert return_code == 0
