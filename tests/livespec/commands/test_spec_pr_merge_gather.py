"""Tests for the spec-PR observation gathering seam.

The two properties worth pinning are the short-circuit (a pull request that
misses the spec root must not be exposed to unrelated git or `gh` failures)
and the flag provenance (the rename-sensitive listing must run the shared
constant, never a locally re-spelled equivalent).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.commands._spec_pr_merge_gather import Observations, gather
from livespec.errors import LivespecError, PreconditionError
from livespec.io import gh, git
from livespec.spec_governance.pr_merge_derivation import LOCAL_DIFF_ARGS, ApiFile
from returns.io import IOResult
from returns.result import Failure, Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

_SPEC_ROOT = "SPECIFICATION"
_HISTORY_PATH = f"{_SPEC_ROOT}/history/v202/proposed_changes/some-topic.md"


def _gather(*, project_root: Path) -> IOResult[Observations, LivespecError]:
    return gather(
        project_root=project_root,
        spec_root=_SPEC_ROOT,
        base_sha="base",
        head_sha="head",
        repo="thewoolleyman/livespec",
        pull_request_number=2200,
    )


def _unwrap(*, result: IOResult[Observations, LivespecError]) -> Observations:
    unwrapped = unsafe_perform_io(result)
    match unwrapped:
        case Success(observations):
            return observations
        case _:
            raise AssertionError(f"expected IOSuccess(Observations), got {unwrapped!r}")


def test_untouched_spec_root_short_circuits_before_any_further_observation(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An unrelated `gh` outage must not block a pull request the gate ignores."""
    monkeypatch.setattr(
        git,
        "diff_name_only",
        lambda **_kwargs: IOResult.from_value(()),
    )
    monkeypatch.setattr(
        git,
        "merge_base",
        lambda **_kwargs: IOResult.from_failure(PreconditionError("must not be called")),
    )
    monkeypatch.setattr(
        gh,
        "list_pull_request_files",
        lambda **_kwargs: IOResult.from_failure(PreconditionError("must not be called")),
    )

    observations = _unwrap(result=_gather(project_root=tmp_path))

    assert observations == Observations(
        touched_spec_root=False,
        total_changed_files=0,
        local_paths=(),
        api_files=(),
    )


def test_touched_spec_root_gathers_every_observation(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The full observation set, with the API statuses carried through intact."""
    observed_diff_args: list[tuple[str, ...]] = []

    def fake_diff_name_only(
        *,
        diff_args: tuple[str, ...],
        pathspec: str | None = None,
        **_kwargs: object,
    ) -> IOResult[tuple[str, ...], LivespecError]:
        observed_diff_args.append(diff_args)
        if diff_args == LOCAL_DIFF_ARGS:
            return IOResult.from_value((_HISTORY_PATH,))
        if pathspec is None:
            return IOResult.from_value((_HISTORY_PATH, "README.md", "justfile"))
        return IOResult.from_value((_HISTORY_PATH,))

    monkeypatch.setattr(git, "diff_name_only", fake_diff_name_only)
    monkeypatch.setattr(
        git,
        "merge_base",
        lambda **_kwargs: IOResult.from_value("mergebase"),
    )
    monkeypatch.setattr(
        gh,
        "list_pull_request_files",
        lambda **_kwargs: IOResult.from_value(
            (gh.PullRequestFile(filename=_HISTORY_PATH, status="renamed"),),
        ),
    )

    observations = _unwrap(result=_gather(project_root=tmp_path))

    assert observations.touched_spec_root
    assert observations.total_changed_files == 3
    assert observations.local_paths == (_HISTORY_PATH,)
    assert observations.api_files == (ApiFile(filename=_HISTORY_PATH, status="renamed"),)
    assert LOCAL_DIFF_ARGS in observed_diff_args


def test_merge_base_failure_stays_on_the_failure_track(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A shallow checkout cannot be folded into an empty observation set."""
    monkeypatch.setattr(
        git,
        "diff_name_only",
        lambda **_kwargs: IOResult.from_value((_HISTORY_PATH,)),
    )
    monkeypatch.setattr(
        git,
        "merge_base",
        lambda **_kwargs: IOResult.from_failure(PreconditionError("git.merge_base: exited 128")),
    )

    unwrapped = unsafe_perform_io(_gather(project_root=tmp_path))

    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(f"expected IOFailure(PreconditionError), got {unwrapped!r}")


def test_hosting_api_failure_stays_on_the_failure_track(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A hosting-API error is derivation FAILURE, never an empty file listing."""
    monkeypatch.setattr(
        git,
        "diff_name_only",
        lambda **_kwargs: IOResult.from_value((_HISTORY_PATH,)),
    )
    monkeypatch.setattr(
        git,
        "merge_base",
        lambda **_kwargs: IOResult.from_value("mergebase"),
    )
    monkeypatch.setattr(
        gh,
        "list_pull_request_files",
        lambda **_kwargs: IOResult.from_failure(PreconditionError("gh: exited 1")),
    )

    unwrapped = unsafe_perform_io(_gather(project_root=tmp_path))

    match unwrapped:
        case Failure(PreconditionError()):
            pass
        case _:
            raise AssertionError(f"expected IOFailure(PreconditionError), got {unwrapped!r}")
