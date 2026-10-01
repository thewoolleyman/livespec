"""Registry union + refusal conditions for `refresh_tenant_repos`.

The repo set the refresher operates on is the UNION of four committed
registries, two per file:

  - `.livespec.jsonc` `cross_repo_targets` — the planning registry;
  - `.livespec.jsonc` `cross_repo_conformance_targets` — the narrower
    code-conformance registry;
  - `.livespec-fleet-manifest.jsonc` `fleet[].repo` — fleet membership;
  - `.livespec-fleet-manifest.jsonc` `adopters[].repo` — governed
    adopters.

The two mapping registries DECLARE a `github_url` (and optionally a
`default_branch`); the two manifest arrays declare only a repo name, so
their GitHub URL is DERIVED from the manifest's `owner`. A repo named by
several registries merges into one target, and the merge is where both
refusal conditions live: registries that DISAGREE about a repo's GitHub
URL or default branch, and a repo name that is not a single safe path
segment (so a name can never escape the peer root it gets joined onto).
Each surfaces as a conflict the caller refuses on BEFORE any mutation,
rather than as a mid-run failure with some repos already touched.

`local_clone` is deliberately IGNORED. The refresher places every repo
as a peer of the primary checkout it is run from, so a registry's
recorded clone path is not an input to where anything lands.

This module is PURE — it takes already-parsed registry objects and
performs no I/O — so the whole refusal surface is exercisable without a
filesystem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

__all__: list[str] = ["RepoTarget", "TargetResolution", "resolve_targets"]

# A repo name is joined onto the peer root, so it must be ONE path
# segment carrying no traversal and no separator: a leading
# alphanumeric followed by alphanumerics, dots, underscores, or
# hyphens. This rejects "", ".", "..", "a/b", "a\\b", an absolute
# "/etc", and any leading-dot or leading-hyphen name.
_SAFE_SEGMENT = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


@dataclass(frozen=True, kw_only=True)
class RepoTarget:
    """One repo the refresher will clone or refresh.

    `default_branch` is None when no registry declared one; the caller
    then asks GitHub for the repository's own default branch.
    """

    repo: str
    owner: str
    github_url: str
    default_branch: str | None


@dataclass(frozen=True, kw_only=True)
class TargetResolution:
    """The merged target set plus every refusal reason found while merging."""

    targets: tuple[RepoTarget, ...]
    conflicts: tuple[str, ...]


def _from_mapping(*, block: object, owner: str) -> list[RepoTarget]:
    """Targets from a `{repo: {github_url, default_branch}}` registry block."""
    rows = cast(dict[str, dict[str, str]], block)
    return [
        RepoTarget(
            repo=repo,
            owner=owner,
            github_url=entry["github_url"],
            default_branch=entry.get("default_branch"),
        )
        for repo, entry in rows.items()
    ]


def _from_array(*, block: object, owner: str) -> list[RepoTarget]:
    """Targets from a `[{repo: ...}]` manifest block, URL derived from `owner`."""
    rows = cast(list[dict[str, str]], block)
    return [
        RepoTarget(
            repo=row["repo"],
            owner=owner,
            github_url=f"https://github.com/{owner}/{row['repo']}",
            default_branch=None,
        )
        for row in rows
    ]


def _conflict(*, existing: RepoTarget, incoming: RepoTarget) -> str | None:
    """Why two declarations of the same repo cannot be merged, or None."""
    if existing.github_url != incoming.github_url:
        return (
            f"{incoming.repo}: registries disagree about the GitHub URL "
            f"({existing.github_url} vs {incoming.github_url})"
        )
    if (
        existing.default_branch is not None
        and incoming.default_branch is not None
        and existing.default_branch != incoming.default_branch
    ):
        return (
            f"{incoming.repo}: registries disagree about the default branch "
            f"({existing.default_branch} vs {incoming.default_branch})"
        )
    return None


def resolve_targets(*, livespec_config: object, fleet_manifest: object) -> TargetResolution:
    """Merge all four registries into one repo-name-sorted target set.

    Every conflict is collected rather than returned on the first
    failure, so one run reports the whole set of refusals the maintainer
    has to resolve.
    """
    config = cast(dict[str, object], livespec_config)
    manifest = cast(dict[str, object], fleet_manifest)
    owner = cast(str, manifest["owner"])
    declared = [
        *_from_mapping(block=config.get("cross_repo_targets", {}), owner=owner),
        *_from_mapping(block=config.get("cross_repo_conformance_targets", {}), owner=owner),
        *_from_array(block=manifest.get("fleet", []), owner=owner),
        *_from_array(block=manifest.get("adopters", []), owner=owner),
    ]
    merged: dict[str, RepoTarget] = {}
    conflicts: list[str] = []
    for target in declared:
        if _SAFE_SEGMENT.match(target.repo) is None:
            conflicts.append(f"{target.repo!r}: not a single safe path segment")
            continue
        existing = merged.get(target.repo)
        if existing is None:
            merged[target.repo] = target
            continue
        conflict = _conflict(existing=existing, incoming=target)
        if conflict is not None:
            conflicts.append(conflict)
            continue
        merged[target.repo] = RepoTarget(
            repo=target.repo,
            owner=owner,
            github_url=target.github_url,
            default_branch=existing.default_branch or target.default_branch,
        )
    return TargetResolution(
        targets=tuple(merged[name] for name in sorted(merged)),
        conflicts=tuple(dict.fromkeys(conflicts)),
    )
