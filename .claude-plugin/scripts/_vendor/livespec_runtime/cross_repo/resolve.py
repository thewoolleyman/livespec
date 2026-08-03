"""`resolve_ref` — exhaustive live-walk dependency resolution.

Per livespec/SPECIFICATION/contracts.md v072: no cache; tolerate partial
visibility; for each `DependsOnEntry` variant, walk every extant view
the runtime can access and return a `RefStatus`.

Environment-aware:

- `LocalDependency` is always resolved against the active impl-plugin's
  work-items store. The caller passes `local_status_lookup` so the
  runtime stays agnostic of impl-plugin storage layouts.
- `SiblingWorkItemDependency`, `PullRequestDependency`, and
  `BranchDependency` resolutions walk the GitHub-queryable view via
  `gh`. The optional `sibling_status_lookup` bridges to an impl-plugin's
  local-clone parser when configured; absent that, sibling work-item
  resolution returns `UNKNOWN`.
- Missing `local_clone` is NOT an error; partial visibility is the
  rule, and the resolver degrades to `UNKNOWN` rather than raising.
- `gh` CLI failures translate to `UNKNOWN` after retry exhaustion via
  the sibling `retry.retry_with_backoff` wrapper.

Resolution semantics:

- PR `state == "OPEN"` → `RefStatus.OPEN`.
- PR `state` in `{"MERGED", "CLOSED"}` → `RefStatus.CLOSED`.
- Branch absent from remote → `RefStatus.CLOSED` (assumes
  deleted-after-merge; the impl-plugin's branch hygiene MUST delete
  feature branches on merge for this to be correct).
- Branch present on remote + reachable from default branch → `CLOSED`.
- Branch present on remote + NOT reachable from default → `OPEN`.
- Any retry exhaustion → `UNKNOWN` (consumer's ranker handles
  unknowns per its own policy; livespec-core's doctor surfaces a
  `warn` finding by default).
"""

from collections.abc import Callable

from returns.io import IOFailure, IOResult
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec_runtime.cross_repo.providers import github as gh_provider
from livespec_runtime.cross_repo.retry import RetryExhausted, retry_with_backoff
from livespec_runtime.cross_repo.types import (
    BranchDependency,
    CrossRepoManifest,
    DependsOnEntry,
    LocalDependency,
    PullRequestDependency,
    RefStatus,
    SiblingWorkItemDependency,
)

__all__: list[str] = ["resolve_ref"]


def resolve_ref(
    *,
    entry: DependsOnEntry,
    manifest: CrossRepoManifest,
    local_status_lookup: Callable[[str], RefStatus],
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> RefStatus:
    """Return the entry's resolved `RefStatus`.

    `local_status_lookup(work_item_id)` returns the current-repo
    work-item's status; the caller wires this against the active
    impl-plugin's list-work-items output.

    `sibling_status_lookup(repo, work_item_id)` is OPTIONAL. When
    provided, it resolves `SiblingWorkItemDependency` entries via
    the impl-plugin's local-clone parser. When absent, sibling
    work-item resolution returns `RefStatus.UNKNOWN` (v1 ships no
    runtime-side local-clone JSONL parser).
    """
    match entry:
        case LocalDependency(work_item_id=work_item_id):
            return local_status_lookup(work_item_id)
        case SiblingWorkItemDependency(repo=repo, work_item_id=work_item_id):
            return _resolve_sibling_work_item(
                repo=repo,
                work_item_id=work_item_id,
                manifest=manifest,
                sibling_status_lookup=sibling_status_lookup,
            )
        case PullRequestDependency(repo=repo, number=number):
            return _resolve_pull_request(repo=repo, number=number, manifest=manifest)
        case BranchDependency(repo=repo, name=name):
            return _resolve_branch(repo=repo, name=name, manifest=manifest)
        case _:
            assert_never(entry)


def _resolve_sibling_work_item(
    *,
    repo: str,
    work_item_id: str,
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None,
) -> RefStatus:
    if repo not in manifest.targets:
        return RefStatus.UNKNOWN
    if sibling_status_lookup is None:
        return RefStatus.UNKNOWN
    return sibling_status_lookup(repo, work_item_id)


def _resolve_pull_request(
    *,
    repo: str,
    number: int,
    manifest: CrossRepoManifest,
) -> RefStatus:
    target = manifest.targets.get(repo)
    if target is None:
        return RefStatus.UNKNOWN
    answered = retry_with_backoff(
        fn=lambda: gh_provider.query_pull_request_state(
            github_url=target.github_url,
            number=number,
        ),
    )
    if isinstance(answered, IOFailure):
        return RefStatus.UNKNOWN
    state = unsafe_perform_io(answered.unwrap())
    if state in ("MERGED", "CLOSED"):
        return RefStatus.CLOSED
    return RefStatus.OPEN


def _resolve_branch(
    *,
    repo: str,
    name: str,
    manifest: CrossRepoManifest,
) -> RefStatus:
    target = manifest.targets.get(repo)
    if target is None:
        return RefStatus.UNKNOWN
    probed = retry_with_backoff(
        fn=lambda: gh_provider.branch_exists_on_remote(
            github_url=target.github_url,
            name=name,
        ),
    )
    exists = _answer(outcome=probed)
    if exists is None:
        return RefStatus.UNKNOWN
    if not exists:
        return RefStatus.CLOSED
    compared = retry_with_backoff(
        fn=lambda: gh_provider.branch_merged_into_default(
            github_url=target.github_url,
            name=name,
            default_branch=target.default_branch,
        ),
    )
    merged = _answer(outcome=compared)
    if merged is None:
        return RefStatus.UNKNOWN
    return RefStatus.CLOSED if merged else RefStatus.OPEN


def _answer(*, outcome: IOResult[bool, RetryExhausted]) -> bool | None:
    """The boolean a probe settled on, or `None` when it never settled.

    ⛔ THIS `bool | None` IS A LEGITIMATE ABSENCE, NOT THE `T | None`
    THIS SEAM REMOVED. `retry_with_backoff` used to return `T | None`
    where `None` stood in for a FAILURE that carried no reason. Here the
    failure has already been reported with its reason on the railway,
    and `None` means only "no answer" — the exact thing the domain
    models as `RefStatus.UNKNOWN` one line up.
    """
    if isinstance(outcome, IOFailure):
        return None
    return unsafe_perform_io(outcome.unwrap())
