"""Tests for the pure spec pull-request merge-policy derivation.

The behaviour under test is the part of the spec-PR merge gate that decided
wrongly in production twice, so each case names the failure it pins down
rather than merely asserting a return value.
"""

from __future__ import annotations

from livespec.spec_governance.pr_merge_derivation import (
    API_ACCEPTED_STATUSES,
    LOCAL_DIFF_ARGS,
    ApiFile,
    accepted_api_paths,
    derive,
    stem_paths,
    stems_from_paths,
)

SPEC_ROOT = "SPECIFICATION"


def test_local_diff_args_suppress_rename_detection() -> None:
    """The local side MUST pass --no-renames.

    A ratifying pull request MOVES the proposal; git scores that R100. With
    rename detection on, the move is not an addition and the stem is missed.
    """
    assert "--no-renames" in LOCAL_DIFF_ARGS
    assert "--diff-filter=A" in LOCAL_DIFF_ARGS


def test_api_accepted_statuses_include_rename_and_copy() -> None:
    """The API side MUST accept renamed and copied, not added alone.

    The hosting API reports the same move as `renamed`, so an added-only
    filter missed it. Both sides must yield the destination path.
    """
    assert frozenset({"added", "renamed", "copied"}) == API_ACCEPTED_STATUSES


def test_accepted_api_paths_keeps_move_statuses_and_drops_others() -> None:
    files = (
        ApiFile(filename="a.md", status="added"),
        ApiFile(filename="b.md", status="renamed"),
        ApiFile(filename="c.md", status="copied"),
        ApiFile(filename="d.md", status="modified"),
        ApiFile(filename="e.md", status="removed"),
    )
    assert accepted_api_paths(files=files) == ("a.md", "b.md", "c.md")


def test_stem_paths_matches_main_and_sub_spec_roots() -> None:
    paths = (
        f"{SPEC_ROOT}/history/v202/proposed_changes/topic-b.md",
        f"{SPEC_ROOT}/templates/livespec/history/v003/proposed_changes/topic-a.md",
        f"{SPEC_ROOT}/proposed_changes/pending.md",
        f"{SPEC_ROOT}/spec.md",
        "README.md",
    )
    assert stem_paths(paths=paths, spec_root=SPEC_ROOT) == (
        f"{SPEC_ROOT}/history/v202/proposed_changes/topic-b.md",
        f"{SPEC_ROOT}/templates/livespec/history/v003/proposed_changes/topic-a.md",
    )


def test_stem_paths_strips_revision_companions() -> None:
    """A ratification writes BOTH files; only the proposal names a stem."""
    paths = (
        f"{SPEC_ROOT}/history/v202/proposed_changes/topic.md",
        f"{SPEC_ROOT}/history/v202/proposed_changes/topic-revision.md",
    )
    assert stem_paths(paths=paths, spec_root=SPEC_ROOT) == (
        f"{SPEC_ROOT}/history/v202/proposed_changes/topic.md",
    )


def test_stems_from_paths_takes_basename_without_suffix() -> None:
    paths = (f"{SPEC_ROOT}/history/v202/proposed_changes/some-topic.md",)
    assert stems_from_paths(paths=paths) == ("some-topic",)


def test_untouched_spec_root_falls_through_to_auto() -> None:
    result = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=False,
        total_changed_files=7,
        local_paths=(),
        api_files=(),
    )
    assert result.outcome == "auto"
    assert result.stems == ()


def test_entirely_empty_diff_is_failure_not_known_empty() -> None:
    """Zero changed files IN TOTAL is impossible for a real pull request.

    Treating it as known-empty would auto-merge on a broken diff computation.
    """
    result = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=True,
        total_changed_files=0,
        local_paths=(),
        api_files=(),
    )
    assert result.outcome == "blocked"


def test_ratifying_rename_is_derived_by_both_sources() -> None:
    """The production shape: a move, seen as an add locally and a rename via API."""
    path = f"{SPEC_ROOT}/history/v202/proposed_changes/some-topic.md"
    result = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=True,
        total_changed_files=9,
        local_paths=(path, f"{SPEC_ROOT}/history/v202/proposed_changes/some-topic-revision.md"),
        api_files=(
            ApiFile(filename=path, status="renamed"),
            ApiFile(
                filename=f"{SPEC_ROOT}/history/v202/proposed_changes/some-topic-revision.md",
                status="added",
            ),
        ),
    )
    assert result.outcome == "governed"
    assert result.stems == ("some-topic",)


def test_source_disagreement_blocks() -> None:
    """Dual-source hardening: divergence is failure, never a silent empty set."""
    result = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=True,
        total_changed_files=4,
        local_paths=(f"{SPEC_ROOT}/history/v202/proposed_changes/only-local.md",),
        api_files=(),
    )
    assert result.outcome == "blocked"


def test_known_empty_touches_spec_root_but_ratifies_nothing() -> None:
    """A plain propose-change filing: falls through unchanged, NOT a fold."""
    path = f"{SPEC_ROOT}/proposed_changes/newly-filed.md"
    result = derive(
        spec_root=SPEC_ROOT,
        touched_spec_root=True,
        total_changed_files=1,
        local_paths=(path,),
        api_files=(ApiFile(filename=path, status="added"),),
    )
    assert result.outcome == "auto"
    assert result.stems == ()
