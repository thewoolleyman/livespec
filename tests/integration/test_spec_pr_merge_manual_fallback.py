"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "Error path — spec pull request cannot auto-merge"
end-to-end over the shipped `effective_spec_pr_merge` resolver and the
`awaits_manual_spec_pr_merge` attention predicate, driven over a REAL
on-disk `SPECIFICATION/history/vNNN/proposed_changes/<stem>.md` tree so
the resolver's own file glob, front-matter parse, and conservative fold
run as they do in production:

- An invalid policy value resolves to manual without raising — a
  proposal declaring an unknown `spec_pr_merge_policy` folds to `manual`
  and awaits human merge, even under a global `auto-on-green`.
- A registration-time floor blocks the set — one `manual` proposal among
  otherwise-auto proposals drives the whole conservative fold to
  `manual` (no auto-merge is armed for the set).
- A successfully-computed empty stem set is not an auto registration —
  an empty stem tuple resolves safely to `manual`.

POSITIVE CONTROL: a global `auto-on-green` with a proposal that carries
no override folds to `auto-on-green` and does NOT await manual merge,
proving the manual-fallback pins are not vacuously always-true.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.spec_governance.config import SpecGovernanceConfig
from livespec.spec_governance.spec_pr_merge import (
    awaits_manual_spec_pr_merge,
    effective_spec_pr_merge,
)

__all__: list[str] = []

pytestmark = pytest.mark.integration

_AUTO = SpecGovernanceConfig(spec_pr_merge="auto-on-green")


def _write_proposal(*, root: Path, stem: str, front_matter: str) -> None:
    proposal_dir = root / "SPECIFICATION" / "history" / "v001" / "proposed_changes"
    proposal_dir.mkdir(parents=True, exist_ok=True)
    _ = (proposal_dir / f"{stem}.md").write_text(
        f"---\ntopic: {stem}\n{front_matter}---\n\n## Proposal\n\nBody.\n",
        encoding="utf-8",
    )


def test_absent_override_under_global_auto_arms_auto_merge(*, tmp_path: Path) -> None:
    """POSITIVE CONTROL: a clean auto proposal does not await manual merge."""
    _write_proposal(root=tmp_path, stem="topic-a", front_matter="")

    policy = effective_spec_pr_merge(
        project_root=tmp_path, config=_AUTO, proposal_stems=("topic-a",)
    )

    assert policy.value == "auto-on-green"
    assert not awaits_manual_spec_pr_merge(policy=policy)


def test_invalid_override_resolves_to_manual_without_raising(*, tmp_path: Path) -> None:
    """An unknown override value folds to manual and awaits human merge."""
    _write_proposal(root=tmp_path, stem="topic-a", front_matter="spec_pr_merge_policy: robot\n")

    policy = effective_spec_pr_merge(
        project_root=tmp_path, config=_AUTO, proposal_stems=("topic-a",)
    )

    assert policy.value == "manual"
    assert policy.source == "proposal"
    assert awaits_manual_spec_pr_merge(policy=policy)


def test_one_manual_proposal_drives_the_whole_fold_to_manual(*, tmp_path: Path) -> None:
    """A single manual override blocks auto registration for the whole set."""
    _write_proposal(root=tmp_path, stem="topic-a", front_matter="")
    _write_proposal(root=tmp_path, stem="topic-b", front_matter="spec_pr_merge_policy: manual\n")

    policy = effective_spec_pr_merge(
        project_root=tmp_path, config=_AUTO, proposal_stems=("topic-a", "topic-b")
    )

    assert policy.value == "manual"
    assert awaits_manual_spec_pr_merge(policy=policy)


def test_empty_stem_set_resolves_safely_to_manual(*, tmp_path: Path) -> None:
    """A computed empty stem set is a safe manual, never an auto registration."""
    policy = effective_spec_pr_merge(project_root=tmp_path, config=_AUTO, proposal_stems=())

    assert policy.value == "manual"
    assert policy.source == "default"
    assert awaits_manual_spec_pr_merge(policy=policy)
