"""Integration proof for the non-Driver Codex automatic-trust boundary.

The live reconciler belongs to the private ``vps-info`` host configuration, so this
test drives a fixture implementation of its contract-facing writer interface.  The
fixture models a host with the Codex Driver installed and makes the Driver, rather
than a writer-owned marketplace list, the authority on whether a plugin can be
release-verified.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import pytest

__all__: list[str] = []

pytestmark = pytest.mark.integration


_REPO_ROOT = Path(__file__).resolve().parents[2]
_HEADING = "## An automated non-Driver Codex hook-trust writer leaves release-verifiable plugins to the Driver"
_TEST_NODE_ID = (
    "tests.integration.test_non_driver_codex_hook_trust_writer."
    "test_fixture_automated_writer_defers_plugin_trust_to_the_installed_driver"
)


@dataclass(frozen=True, kw_only=True)
class _Hook:
    """One hook Codex reports as needing trust.

    A user-level hook has neither plugin nor marketplace.  A plugin hook always
    has a plugin name; it has no marketplace when its identity is incomplete.
    """

    key: str
    plugin: str | None = None
    marketplace: str | None = None


class _InstalledCodexDriver(Protocol):
    """The writer's narrow contract with the installed Codex Driver."""

    def can_release_verify(self, *, marketplace: str) -> bool:
        """Whether this Driver can release-verify the marketplace."""


class _CodexTrustRecords(Protocol):
    """The writer's narrow contract with Codex's host-level trust state."""

    def write(self, *, hook: _Hook) -> None:
        """Persist one hook's automatic-trust record."""


class _AutomatedHookTrustWriter(Protocol):
    """Contract-facing interface of an automatic non-Driver trust writer."""

    def reconcile(self, *, hooks: tuple[_Hook, ...]) -> None:
        """Trust every hook the contract permits this writer to trust."""


@dataclass(frozen=True, kw_only=True)
class _FixtureInstalledCodexDriver:
    """Fixture Driver installation; its decision is deliberately data-driven."""

    release_verifiable_marketplaces: frozenset[str]
    consultation_fails: bool = False

    def can_release_verify(self, *, marketplace: str) -> bool:
        if self.consultation_fails:
            raise RuntimeError("installed Driver release verification is unavailable")
        return marketplace in self.release_verifiable_marketplaces


@dataclass
class _MemoryTrustRecords:
    """Scratch Codex configuration receiving records from the fixture writer."""

    keys: set[str] = field(default_factory=set)

    def write(self, *, hook: _Hook) -> None:
        self.keys.add(hook.key)


@dataclass(frozen=True, kw_only=True)
class _FixtureAutomatedHookTrustWriter:
    """An automatically trusting writer that defers plugin decisions to the Driver."""

    driver: _InstalledCodexDriver
    records: _CodexTrustRecords
    trust_every_permitted_hook: bool = True

    def reconcile(self, *, hooks: tuple[_Hook, ...]) -> None:
        assert self.trust_every_permitted_hook
        for hook in hooks:
            if hook.plugin is None:
                self.records.write(hook=hook)
                continue
            if hook.marketplace is None:
                continue
            try:
                release_verifiable = self.driver.can_release_verify(marketplace=hook.marketplace)
            except RuntimeError:
                continue
            if not release_verifiable:
                self.records.write(hook=hook)


def _scenario_entry() -> dict[str, object]:
    coverage = json.loads(
        (_REPO_ROOT / "tests" / "heading-coverage.json").read_text(encoding="utf-8")
    )
    return next(entry for entry in coverage if entry.get("heading") == _HEADING)


def _debt_entries() -> list[dict[str, object]]:
    return json.loads(
        (_REPO_ROOT / "tests" / "heading-coverage-debt.json").read_text(encoding="utf-8")
    )


def test_fixture_automated_writer_defers_plugin_trust_to_the_installed_driver() -> None:
    """A non-Driver writer skips release-verifiable and unconsultable plugin hooks."""
    release_verified = (
        _Hook(
            key="livespec:pre-tool-use",
            plugin="livespec",
            marketplace="livespec-driver-codex",
        ),
        _Hook(
            key="livespec:session-start",
            plugin="livespec",
            marketplace="livespec-driver-codex",
        ),
    )
    third_party = _Hook(
        key="other:pre-tool-use", plugin="other", marketplace="third-party-marketplace"
    )
    user_hook = _Hook(key="user:pre-tool-use")
    records = _MemoryTrustRecords()
    writer: _AutomatedHookTrustWriter = _FixtureAutomatedHookTrustWriter(
        driver=_FixtureInstalledCodexDriver(
            release_verifiable_marketplaces=frozenset({"livespec-driver-codex"})
        ),
        records=records,
    )

    writer.reconcile(hooks=(*release_verified, third_party, user_hook))

    assert records.keys == {third_party.key, user_hook.key}
    assert not records.keys.intersection(hook.key for hook in release_verified)

    unconsultable_records = _MemoryTrustRecords()
    unconsultable_writer: _AutomatedHookTrustWriter = _FixtureAutomatedHookTrustWriter(
        driver=_FixtureInstalledCodexDriver(
            release_verifiable_marketplaces=frozenset({"livespec-driver-codex"}),
            consultation_fails=True,
        ),
        records=unconsultable_records,
    )

    unconsultable_writer.reconcile(hooks=(*release_verified, third_party, user_hook))

    assert unconsultable_records.keys == {user_hook.key}
    assert not unconsultable_records.keys.intersection(
        hook.key for hook in (*release_verified, third_party)
    )

    assert _scenario_entry()["test"] == _TEST_NODE_ID
    assert all(entry.get("heading") != _HEADING for entry in _debt_entries())
