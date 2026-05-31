"""Consumer wiring for the canonical CLI end-to-end harness.

Per SPECIFICATION/contracts.md §"CLI end-to-end harness contract", the
harness itself is the single canonical implementation that ships from
`livespec-dev-tooling` (`livespec_dev_tooling.testing.cli_e2e`); this repo
is a CONSUMER (contract requirement 6). This module wires the imported
`test_workflow_full_round_trip` entry point into livespec's pytest
collection, parametrized over the known impl plugin(s) (requirement 2).

What runs in the `mock` tier (LIVESPEC_E2E_HARNESS=mock, in `just check`):

- REAL structural skill discovery (`discover_skills` walks
  `.claude-plugin/skills/*/SKILL.md` and reads the slash prefix from
  `plugin.json`'s `name` — the in-repo plugin directory IS the source of
  truth, requirement 3);
- REAL per-skill fixture loading from `tests/e2e-cli/fixtures/<skill>/`
  (requirement 4);
- the REAL fail-closed time-bomb coverage gate (requirement 5);
- only the `claude -p` subprocess is mocked, via an injected deterministic
  runner that materializes each fixture's `expected_files`.

The `real` tier (LIVESPEC_E2E_HARNESS=real, NOT in `just check`) drives the
actual `claude` binary against the live API; it is exercised by the
dedicated CI job, not the default aggregate.

The red-baseline test at the bottom proves the coverage gate fails CLOSED
when a discovered skill lacks a fixture (requirement 5), then the
happy-path test proves it passes once every discovered skill is fixtured.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_dev_tooling.testing import cli_e2e
from livespec_dev_tooling.testing.cli_e2e import (
    CliResult,
    CoverageGateError,
    HarnessConfig,
)

__all__: list[str] = []


# The canonical entry point is named `test_workflow_full_round_trip` (fixed
# by the contract's consumer import path). Importing that bare `test_*` name
# into a pytest module would make pytest try to COLLECT it as a test with a
# missing `config` fixture — so we alias it under a non-`test_`-prefixed
# name here and call it from our own thin wrapper test.
_run_full_round_trip = cli_e2e.test_workflow_full_round_trip


# The repo root is three levels up from this file:
# <root>/tests/e2e-cli/test_cli_e2e.py
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PLUGIN_SOURCE = _REPO_ROOT / ".claude-plugin"
_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"

# The known impl plugin(s) the harness is parametrized over (contract
# requirement 2). livespec-core discovers only the FIXED spec-side
# `livespec` plugin; each impl-plugin repo owns its own tests/e2e-cli/
# consumer obligation (requirement 7) and discovers its own skills paired
# with livespec. The id is carried through `HarnessConfig.impl_plugin_id`
# so the parameter is exercised end-to-end even when the impl-side skill
# set is not discovered in this repo's run.
_KNOWN_IMPL_PLUGINS: tuple[str, ...] = ("livespec-impl-plaintext",)


class _FakeCliRunner:
    """Deterministic `claude -p` seam — the one mocked boundary.

    Records every turn and, per a per-prompt recipe, materializes the files
    a real `claude -p` run of that skill's slash command would create.
    Discovery, fixture loading, the coverage gate, and orchestration all run
    for real against the on-disk fixtures tree; only this subprocess seam is
    canned (per the harness's injected-runner design).
    """

    def __init__(self, *, creates: dict[str, tuple[str, ...]]) -> None:
        self._creates = creates
        self.turns: list[dict[str, object]] = []

    def run(
        self,
        *,
        prompt: str,
        home: Path,
        cwd: Path,
        resume_session_id: str | None,
    ) -> CliResult:
        self.turns.append(
            {
                "prompt": prompt,
                "home": str(home),
                "cwd": str(cwd),
                "resume": resume_session_id,
            }
        )
        for rel in self._creates.get(prompt, ()):
            target = cwd / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            _ = target.write_text("created by fake claude\n", encoding="utf-8")
        return CliResult(exit_code=0, stdout="", stderr="", session_id=None)


def _harness_config(*, impl_plugin_id: str, fixtures_root: Path) -> HarnessConfig:
    """Build a HarnessConfig pointing discovery at the in-repo plugin source."""
    return HarnessConfig(
        impl_plugin_id=impl_plugin_id,
        marketplace="thewoolleyman/livespec",
        enabled_plugins=("livespec@livespec", f"{impl_plugin_id}@{impl_plugin_id}"),
        plugin_install_dirs=(_PLUGIN_SOURCE,),
        fixtures_root=fixtures_root,
        install_command="/plugin install livespec@livespec",
    )


def _expected_files_for(*, fixtures_root: Path) -> dict[str, tuple[str, ...]]:
    """Load each fixture's prompt → its expected_files, for the fake runner.

    Reuses the harness's own fixture loader so the prompt strings the fake
    keys on are byte-identical to what the orchestrator passes through.
    """
    fixtures = cli_e2e.discover_fixtures(fixtures_root=fixtures_root)
    return {fx.prompt: fx.expected_files for fx in fixtures.values()}


@pytest.mark.parametrize("impl_plugin_id", _KNOWN_IMPL_PLUGINS)
def test_cli_e2e_full_round_trip_mock_tier(*, impl_plugin_id: str, tmp_path: Path) -> None:
    """The imported harness drives every discovered /livespec:* skill.

    Mock tier: real discovery against the in-repo `.claude-plugin/` source,
    real fixture loading, the real fail-closed coverage gate, and a
    deterministic injected runner that materializes each fixture's expected
    files. Asserts the full round-trip passes and that every spec-side skill
    was discovered and fixtured.
    """
    config = _harness_config(impl_plugin_id=impl_plugin_id, fixtures_root=_FIXTURES_ROOT)
    creates = _expected_files_for(fixtures_root=_FIXTURES_ROOT)
    # The install command creates nothing; every skill prompt materializes
    # its fixture's expected files under the tmp project root.
    runner = _FakeCliRunner(creates=creates)
    result = _run_full_round_trip(
        config=config,
        home=tmp_path / "home",
        project_root=tmp_path / "project",
        injected_runner=runner,
    )
    # Every spec-side skill is discovered and fixtured.
    assert set(result.discovered_skills) == {
        "seed",
        "propose-change",
        "critique",
        "revise",
        "doctor",
        "prune-history",
        "next",
        "help",
    }
    assert set(result.fixtured_skills) == set(result.discovered_skills)
    assert result.passed is True


def test_cli_e2e_coverage_gate_fails_closed_on_missing_fixture(*, tmp_path: Path) -> None:
    """Red baseline: a discovered skill with no fixture trips the gate.

    Proves the time-bomb coverage gate fails CLOSED (contract requirement
    5): when the in-repo plugin exposes a skill that has no fixture
    directory and is not exempt, the harness raises `CoverageGateError`
    BEFORE running any skill turn. This is the deliberate red-baseline for
    the gate — the happy-path test above is the green counterpart once every
    discovered skill is fixtured.
    """
    # A plugin exposing one extra skill (`brand-new`) beyond the fixtured
    # set, modelling a freshly-added skill that nobody wrote a fixture for.
    plugin_dir = tmp_path / "plugin"
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    _ = (plugin_dir / "plugin.json").write_text(json.dumps({"name": "livespec"}), encoding="utf-8")
    for skill in ("seed", "brand-new"):
        sd = skills_dir / skill
        sd.mkdir()
        _ = (sd / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
    # Fixtures exist for `seed` only — `brand-new` is uncovered.
    fixtures_root = tmp_path / "fixtures"
    seed_fx = fixtures_root / "seed"
    seed_fx.mkdir(parents=True)
    _ = (seed_fx / "prompt.md").write_text("/livespec:seed\n", encoding="utf-8")

    config = HarnessConfig(
        impl_plugin_id="livespec-impl-plaintext",
        marketplace="thewoolleyman/livespec",
        enabled_plugins=("livespec@livespec",),
        plugin_install_dirs=(plugin_dir,),
        fixtures_root=fixtures_root,
    )
    runner = _FakeCliRunner(creates={})
    with pytest.raises(CoverageGateError, match="brand-new"):
        _ = _run_full_round_trip(
            config=config,
            home=tmp_path / "home",
            project_root=tmp_path / "project",
            injected_runner=runner,
        )
    # Fail-closed BEFORE any skill turn ran.
    assert runner.turns == []
