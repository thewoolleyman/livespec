"""Tests for livespec.parse.cross_repo.

Per the module's docstring: the pure shims wrap
`livespec_runtime.cross_repo.{parse_depends_on_entry,
parse_cross_repo_manifest}` with `Result`-track error handling so
consumer call sites stay raise-free.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from livespec.errors import ValidationError
from livespec.parse import cross_repo
from livespec_runtime.cross_repo.types import (
    BranchDependency,
    CrossRepoTarget,
    LocalDependency,
    PullRequestDependency,
    SiblingWorkItemDependency,
)
from returns.result import Failure, Success

__all__: list[str] = []


def test_parse_entry_local_success() -> None:
    """A `kind: local` dict parses into LocalDependency."""
    result = cross_repo.parse_entry(parsed={"kind": "local", "work_item_id": "li-abc"})
    assert result == Success(LocalDependency(work_item_id="li-abc"))


def test_parse_entry_sibling_success() -> None:
    """A `kind: sibling_work_item` dict parses into SiblingWorkItemDependency."""
    result = cross_repo.parse_entry(
        parsed={"kind": "sibling_work_item", "repo": "runtime", "work_item_id": "li-x"}
    )
    assert result == Success(SiblingWorkItemDependency(repo="runtime", work_item_id="li-x"))


def test_parse_entry_pull_request_success() -> None:
    """A `kind: pull_request` dict parses into PullRequestDependency."""
    result = cross_repo.parse_entry(parsed={"kind": "pull_request", "repo": "runtime", "number": 5})
    assert result == Success(PullRequestDependency(repo="runtime", number=5))


def test_parse_entry_branch_success() -> None:
    """A `kind: branch` dict parses into BranchDependency."""
    result = cross_repo.parse_entry(parsed={"kind": "branch", "repo": "runtime", "name": "feat/x"})
    assert result == Success(BranchDependency(repo="runtime", name="feat/x"))


def test_parse_entry_missing_kind_failure() -> None:
    """A dict without `kind` returns Failure(ValidationError(...))."""
    result = cross_repo.parse_entry(parsed={"work_item_id": "li-abc"})
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, ValidationError)
    assert "kind" in str(err)


def test_parse_entry_unknown_kind_failure() -> None:
    """A dict with unknown `kind` value returns Failure."""
    result = cross_repo.parse_entry(parsed={"kind": "bogus", "work_item_id": "x"})
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, ValidationError)
    assert "bogus" in str(err)


def test_parse_manifest_success() -> None:
    """A well-formed cross_repo_targets dict parses into a CrossRepoManifest."""
    result = cross_repo.parse_manifest(
        parsed={"runtime": {"github_url": "https://github.com/example/runtime"}}
    )
    assert isinstance(result, Success)
    manifest = result.unwrap()
    assert "runtime" in manifest.targets
    assert manifest.targets["runtime"] == CrossRepoTarget(
        github_url="https://github.com/example/runtime"
    )


def test_parse_manifest_missing_github_url_failure() -> None:
    """A target dict missing the REQUIRED `github_url` returns Failure."""
    result = cross_repo.parse_manifest(parsed={"runtime": {"local_clone": "/tmp/x"}})
    assert isinstance(result, Failure)
    err = result.failure()
    assert isinstance(err, ValidationError)


@given(
    work_item_id=st.text(
        alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
        min_size=1,
        max_size=20,
    ),
)
def test_parse_entry_local_roundtrip_property(*, work_item_id: str) -> None:
    """For any short lowercase string id, a `kind: local` dict parses to a matching LocalDependency.

    Property: the wrapper is a pure pass-through to the runtime's
    parser, so any input the runtime accepts MUST round-trip through
    the `Success(LocalDependency(...))` carrier with the same
    work_item_id. Hypothesis explores arbitrary string identifiers
    within the bounded envelope.
    """
    result = cross_repo.parse_entry(parsed={"kind": "local", "work_item_id": work_item_id})
    assert result == Success(LocalDependency(work_item_id=work_item_id))
