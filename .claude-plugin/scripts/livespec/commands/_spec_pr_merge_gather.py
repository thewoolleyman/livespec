# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library, same rationale as `livespec.io.git`:
# bind chains lose flow-narrowing through pyright strict mode.
"""Gather the git and hosting-API observations the spec-PR derivation folds.

This is the impure half of the spec pull-request merge-policy gate; the pure
half is `livespec.spec_governance.pr_merge_derivation`. Splitting them is what
makes the rules that decided wrongly in production testable without a runner.

The observation set is gathered from TWO TREES, and the split is deliberate:
the CONSUMER's checkout supplies the data (full git history for the merge-base,
`.livespec.jsonc`, and the spec tree) while `livespec`'s own checkout supplies
the executable. `project_root` names the former.

A pull request that does not touch the spec root SHORT-CIRCUITS before any
further observation. That is not an optimisation: gathering the merge-base and
the hosting-API listing for such a pull request would let an unrelated git or
`gh` failure resolve BLOCKED on a change the gate does not govern at all,
which would silently narrow auto-merge for every non-spec pull request.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io import gh, git
from livespec.spec_governance.pr_merge_derivation import LOCAL_DIFF_ARGS, ApiFile

__all__: list[str] = ["Observations", "gather"]

# The plain listing flags for the two observations that are counts or
# membership tests rather than the rename-sensitive stem derivation. The
# rename-sensitive invocation uses `LOCAL_DIFF_ARGS` instead, unaltered.
_NAME_ONLY: tuple[str, ...] = ("--name-only",)


@dataclass(frozen=True, kw_only=True, slots=True)
class Observations:
    """Everything the pure derivation needs, and nothing it does not."""

    touched_spec_root: bool
    total_changed_files: int
    local_paths: tuple[str, ...]
    api_files: tuple[ApiFile, ...]


_UNTOUCHED = Observations(
    touched_spec_root=False,
    total_changed_files=0,
    local_paths=(),
    api_files=(),
)


def gather(
    *,
    project_root: Path,
    spec_root: str,
    base_sha: str,
    head_sha: str,
    repo: str,
    pull_request_number: int,
) -> IOResult[Observations, LivespecError]:
    """Observe the pull request, short-circuiting when it misses the spec root.

    Every failure stays on the IOFailure track so the supervisor can resolve it
    as derivation FAILURE. Nothing here folds an error into an empty result —
    that conflation is the defect this module exists to make unrepresentable.
    """
    return git.diff_name_only(
        project_root=project_root,
        base_ref=base_sha,
        head_ref=head_sha,
        diff_args=_NAME_ONLY,
        pathspec=spec_root,
    ).bind(
        lambda touched: (
            _gather_touched(
                project_root=project_root,
                spec_root=spec_root,
                base_sha=base_sha,
                head_sha=head_sha,
                repo=repo,
                pull_request_number=pull_request_number,
            )
            if touched
            else IOResult.from_value(_UNTOUCHED)
        ),
    )


def _gather_touched(
    *,
    project_root: Path,
    spec_root: str,
    base_sha: str,
    head_sha: str,
    repo: str,
    pull_request_number: int,
) -> IOResult[Observations, LivespecError]:
    """Observe a pull request already known to touch the spec root."""
    return git.merge_base(
        project_root=project_root,
        base_ref=base_sha,
        head_ref=head_sha,
    ).bind(
        lambda base: _gather_from_merge_base(
            project_root=project_root,
            spec_root=spec_root,
            merge_base_sha=base,
            head_sha=head_sha,
            repo=repo,
            pull_request_number=pull_request_number,
        ),
    )


def _gather_from_merge_base(
    *,
    project_root: Path,
    spec_root: str,
    merge_base_sha: str,
    head_sha: str,
    repo: str,
    pull_request_number: int,
) -> IOResult[Observations, LivespecError]:
    """Compose the three remaining observations off a resolved merge-base."""
    return git.diff_name_only(
        project_root=project_root,
        base_ref=merge_base_sha,
        head_ref=head_sha,
        diff_args=_NAME_ONLY,
    ).bind(
        lambda all_paths: git.diff_name_only(
            project_root=project_root,
            base_ref=merge_base_sha,
            head_ref=head_sha,
            diff_args=LOCAL_DIFF_ARGS,
            pathspec=spec_root,
        ).bind(
            lambda local_paths: gh.list_pull_request_files(
                project_root=project_root,
                repo=repo,
                pull_request_number=pull_request_number,
            ).map(
                lambda api_files: Observations(
                    touched_spec_root=True,
                    total_changed_files=len(all_paths),
                    local_paths=local_paths,
                    api_files=tuple(
                        ApiFile(filename=entry.filename, status=entry.status) for entry in api_files
                    ),
                ),
            ),
        ),
    )
