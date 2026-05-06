"""E2E happy-path test: seed → propose-change → critique → revise → doctor → prune-history.

Per SPECIFICATION/contracts.md §"E2E harness contract §"Test structure": the
happy path exercises the full user workflow against a tmp_path-scoped git repo
using the minimal template. Each wrapper step is followed by a git commit so
the out-of-band-edits doctor check sees HEAD-committed spec state.
"""

from __future__ import annotations

import subprocess  # documented integration-test usage
from pathlib import Path

import fake_claude
import pytest

__all__: list[str] = []


def _git(*, cwd: Path, args: list[str]) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
    )


def _git_init_and_configure(*, project_root: Path) -> None:
    _git(cwd=project_root, args=["init"])
    _git(cwd=project_root, args=["config", "user.email", "e2e-test@example.com"])
    _git(cwd=project_root, args=["config", "user.name", "E2E Test"])


def _git_add_all_and_commit(*, project_root: Path, message: str) -> None:
    _git(cwd=project_root, args=["add", "-A"])
    _git(cwd=project_root, args=["commit", "-m", message])


@pytest.mark.skipif(
    condition=False,
    reason="Runs in both mock and real tiers.",
)
def test_happy_path_minimal(*, tmp_path: Path) -> None:
    """Full happy-path round-trip: seed → propose-change → critique → revise → doctor → prune.

    PLR0915 noqa: same multi-step integration test rationale as
    tests/bin/test_phase3_round_trip.py — sequential steps share state
    via the tmp_path filesystem; extracting each step into a helper
    would obscure the round-trip reading order.
    """
    _git_init_and_configure(project_root=tmp_path)

    # Step 1: seed
    seed_result = fake_claude.seed(project_root=tmp_path, intent="E2E happy-path test project")
    assert seed_result.returncode == 0, (
        f"seed exited {seed_result.returncode}; "
        f"stdout={seed_result.stdout!r} stderr={seed_result.stderr!r}"
    )
    assert (tmp_path / "SPECIFICATION" / "spec.md").is_file()
    assert (tmp_path / ".livespec.jsonc").is_file()
    assert (tmp_path / "SPECIFICATION" / "proposed_changes" / "README.md").is_file()
    assert (tmp_path / "SPECIFICATION" / "history" / "v001").is_dir()
    _git_add_all_and_commit(project_root=tmp_path, message="seed")

    # Step 2: propose-change
    propose_result = fake_claude.propose_change(
        project_root=tmp_path,
        intent="Add a constraint that all changes MUST be reviewed",
        topic="review-constraint",
    )
    assert propose_result.returncode == 0, (
        f"propose-change exited {propose_result.returncode}; "
        f"stdout={propose_result.stdout!r} stderr={propose_result.stderr!r}"
    )
    assert (tmp_path / "SPECIFICATION" / "proposed_changes" / "review-constraint.md").is_file()

    # Step 3: critique
    critique_result = fake_claude.critique(
        project_root=tmp_path,
        intent="Review the pending proposal for ambiguities",
    )
    assert critique_result.returncode == 0, (
        f"critique exited {critique_result.returncode}; "
        f"stdout={critique_result.stdout!r} stderr={critique_result.stderr!r}"
    )
    critique_files = list((tmp_path / "SPECIFICATION" / "proposed_changes").glob("*-critique.md"))
    assert len(critique_files) == 1, "expected exactly one critique proposal"

    # Step 4: revise
    revise_result = fake_claude.revise(project_root=tmp_path)
    assert revise_result.returncode == 0, (
        f"revise exited {revise_result.returncode}; "
        f"stdout={revise_result.stdout!r} stderr={revise_result.stderr!r}"
    )
    assert (tmp_path / "SPECIFICATION" / "history" / "v002").is_dir()
    assert not (tmp_path / "SPECIFICATION" / "proposed_changes" / "review-constraint.md").exists()
    _git_add_all_and_commit(project_root=tmp_path, message="revise")

    # Step 5: doctor (static phase only; minimal template has no LLM-driven checks)
    doctor_result = fake_claude.doctor_static(project_root=tmp_path)
    assert doctor_result.returncode == 0, (
        f"doctor_static exited {doctor_result.returncode}; "
        f"stdout={doctor_result.stdout!r} stderr={doctor_result.stderr!r}"
    )

    # Step 6: prune-history (v001 + v002 exist → prunes v001)
    prune_result = fake_claude.prune_history(project_root=tmp_path)
    assert prune_result.returncode == 0, (
        f"prune-history exited {prune_result.returncode}; "
        f"stdout={prune_result.stdout!r} stderr={prune_result.stderr!r}"
    )
