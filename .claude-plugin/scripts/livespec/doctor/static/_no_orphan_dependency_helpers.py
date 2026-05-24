"""Private helpers for `no_orphan_dependency`.

Extracts the depends_on walking + resolve_ref dispatch from the
parent module so the public check wrapper stays below the 250-LLOC
hard ceiling enforced by `dev-tooling/checks/file_lloc.py`. The
split is purely an LLOC-budget concern; the public surface is
re-exported through `no_orphan_dependency.py`.

Resolve_ref dispatch (added v072 phase 2): every typed dict entry
flows through `livespec_runtime.cross_repo.resolve_ref`, which
dispatches LocalDependency to the in-store lookup and non-local
kinds to the gh-CLI provider. Per
`SPECIFICATION/contracts.md` §"`no-orphan-dependency`": for local
kinds, a missing id fires `fail`; for non-local kinds, `fail`
fires only when `resolve_ref` returns `unknown` AND the entry's
`repo` is configured in `cross_repo_targets`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    BranchDependency,
    CrossRepoManifest,
    DependsOnEntry,
    LocalDependency,
    PullRequestDependency,
    RefStatus,
    SiblingWorkItemDependency,
)
from returns.result import Success
from typing_extensions import assert_never

from livespec.parse import cross_repo as cross_repo_parse

__all__: list[str] = [
    "extract_manifest",
    "find_orphans",
]


def _orphan(*, item_id: str, dep_id: str, kind: str) -> tuple[str, str]:
    """Format the (item_id, dep_label) pair used in the fail narration."""
    return (item_id, f"{dep_id} (kind={kind})")


def _local_status(*, work_item_id: str, index: dict[str, dict[str, Any]]) -> RefStatus:
    """Return the RefStatus for a same-repo work-item id, scanning the materialized index."""
    record = index.get(work_item_id)
    if record is None:
        return RefStatus.UNKNOWN
    if record.get("status") == "closed":
        return RefStatus.CLOSED
    return RefStatus.OPEN


def _make_local_lookup(
    *,
    index: dict[str, dict[str, Any]],
) -> Callable[[str], RefStatus]:
    """Wire `resolve_ref`'s local_status_lookup against the materialized index."""
    return lambda work_item_id: _local_status(work_item_id=work_item_id, index=index)


_NonLocalDependency: TypeAlias = (
    SiblingWorkItemDependency | PullRequestDependency | BranchDependency
)


def _describe_non_local(*, entry: _NonLocalDependency) -> str:
    """Format a non-local typed entry as a compact human-readable label."""
    match entry:
        case SiblingWorkItemDependency(repo=repo, work_item_id=work_item_id):
            return f"{repo}#{work_item_id}"
        case PullRequestDependency(repo=repo, number=number):
            return f"{repo}#PR{number}"
        case BranchDependency(repo=repo, name=name):
            return f"{repo}@{name}"
        case _:
            assert_never(entry)


def _resolve_and_check(
    *,
    item_id: str,
    entry: DependsOnEntry,
    record_status: str,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> tuple[str, str] | None:
    """Dispatch a typed entry through resolve_ref and interpret the RefStatus."""
    status = resolve_ref(
        entry=entry,
        manifest=manifest,
        local_status_lookup=_make_local_lookup(index=index),
    )
    if status != RefStatus.UNKNOWN:
        return None
    if isinstance(entry, LocalDependency):
        return _orphan(item_id=item_id, dep_id=entry.work_item_id, kind="local")
    if record_status == "closed":
        return None
    if entry.repo not in manifest.targets:
        return None
    return _orphan(
        item_id=item_id,
        dep_id=_describe_non_local(entry=entry),
        kind=f"{entry.kind} (unresolved by runtime)",
    )


def _check_str_entry(
    *,
    item_id: str,
    record_status: str,
    raw: str,
    index: dict[str, dict[str, Any]],
) -> tuple[str, str] | None:
    """Handle a legacy bare-string entry — fail for open records, tolerate closed."""
    if record_status != "closed":
        return _orphan(item_id=item_id, dep_id=raw, kind="bare-string (data-migration pending)")
    if raw not in index:
        return _orphan(item_id=item_id, dep_id=raw, kind="local-legacy")
    return None


def _check_dict_entry(
    *,
    item_id: str,
    record_status: str,
    raw: dict[str, Any],
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> tuple[str, str] | None:
    """Handle a typed-dict entry: parse, then dispatch through resolve_ref."""
    parsed_result = cross_repo_parse.parse_entry(parsed=raw)
    if not isinstance(parsed_result, Success):
        if record_status == "closed":
            return None
        return _orphan(item_id=item_id, dep_id=str(raw), kind="schema-error")
    entry = parsed_result.unwrap()
    return _resolve_and_check(
        item_id=item_id,
        entry=entry,
        record_status=record_status,
        index=index,
        manifest=manifest,
    )


def _check_raw(
    *,
    item_id: str,
    record_status: str,
    raw: Any,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> tuple[str, str] | None:
    """Dispatch on raw entry shape (str / dict / other)."""
    if isinstance(raw, str):
        return _check_str_entry(item_id=item_id, record_status=record_status, raw=raw, index=index)
    if isinstance(raw, dict):
        return _check_dict_entry(
            item_id=item_id,
            record_status=record_status,
            raw=raw,
            index=index,
            manifest=manifest,
        )
    if record_status == "closed":
        return None
    return _orphan(item_id=item_id, dep_id=str(raw), kind="malformed (non-dict)")


def find_orphans(
    *,
    index: dict[str, dict[str, Any]],
    manifest: CrossRepoManifest,
) -> list[tuple[str, str]]:
    """Walk every record's depends_on; return sorted orphan pairs."""
    orphans: list[tuple[str, str]] = []
    for item_id, record in index.items():
        deps = record.get("depends_on")
        if not isinstance(deps, list):
            continue
        status_value = record.get("status")
        record_status = status_value if isinstance(status_value, str) else ""
        for raw in deps:
            orphan = _check_raw(
                item_id=item_id,
                record_status=record_status,
                raw=raw,
                index=index,
                manifest=manifest,
            )
            if orphan is not None:
                orphans.append(orphan)
    return sorted(orphans)


def extract_manifest(*, config: dict[str, Any]) -> CrossRepoManifest:
    """Parse the `cross_repo_targets` block out of `.livespec.jsonc`.

    Returns an empty manifest when the block is absent or malformed —
    the malformed-block surface is the `depends_on-ref-wellformedness`
    invariant's domain, not this check's.
    """
    raw_block = config.get("cross_repo_targets")
    if not isinstance(raw_block, dict):
        return CrossRepoManifest(targets={})
    parsed_result = cross_repo_parse.parse_manifest(parsed=raw_block)
    if not isinstance(parsed_result, Success):
        return CrossRepoManifest(targets={})
    return parsed_result.unwrap()
