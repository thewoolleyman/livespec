"""Typed `DependsOnEntry` union + `CrossRepoManifest` + `RefStatus`.

Per livespec/SPECIFICATION/contracts.md v072.

The four variant dataclasses (`LocalDependency`,
`SiblingWorkItemDependency`, `PullRequestDependency`,
`BranchDependency`) are discriminated on a `Literal[...]`-typed
`kind` field so pyright narrows union members on `match
entry.kind: ...` dispatch in consumer code.

The two `parse_*` helpers are the JSON-to-typed boundary: they
validate the dict-shape and emit a typed instance, or raise
`CrossRepoSchemaError` on schema deviation. The `parse_*` boundary
lives here (not at the consumer site) so every consumer sees the
same typed shape regardless of how the dict was sourced (JSONL
work-items file, `.livespec.jsonc` config, harness fixture).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Literal, TypeAlias

from typing_extensions import assert_never

from livespec_runtime.cross_repo.errors import CrossRepoSchemaError

__all__: list[str] = [
    "BranchDependency",
    "CrossRepoManifest",
    "CrossRepoTarget",
    "DependsOnEntry",
    "LocalDependency",
    "PullRequestDependency",
    "RefStatus",
    "SiblingWorkItemDependency",
    "parse_cross_repo_manifest",
    "parse_depends_on_entry",
]


DependsOnKind: TypeAlias = Literal["local", "sibling_work_item", "pull_request", "branch"]


@dataclass(frozen=True, slots=True, kw_only=True)
class RefStatus:
    """The resolved state of a `DependsOnEntry`.

    `OPEN`   — the dependency is still in-flight (target work-item /
               PR / branch is not yet closed-or-merged).
    `CLOSED` — the dependency has resolved (target work-item is
               status==closed; PR is MERGED or CLOSED; branch is
               merged into default).
    `UNKNOWN` — the runtime could not derive a definitive answer
               (missing local clone, GitHub query failed after retry
               exhaustion, impl-plugin surface absent).
    """

    value: Literal["open", "closed", "unknown"]

    OPEN: ClassVar["RefStatus"]
    CLOSED: ClassVar["RefStatus"]
    UNKNOWN: ClassVar["RefStatus"]


RefStatus.OPEN = RefStatus(value="open")
RefStatus.CLOSED = RefStatus(value="closed")
RefStatus.UNKNOWN = RefStatus(value="unknown")


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalDependency:
    """A same-repo work-item dependency.

    Resolved against the active impl-plugin's local work-items store
    (no cross-repo walk).
    """

    work_item_id: str
    kind: Literal["local"] = "local"


@dataclass(frozen=True, slots=True, kw_only=True)
class SiblingWorkItemDependency:
    """A work-item in a configured sibling repo.

    `repo` MUST match a key in `.livespec.jsonc`'s `cross_repo_targets`
    block. Resolved via the caller-supplied `sibling_status_lookup`
    callback passed to `resolve_ref`. When the callback is absent or
    `repo` is not in the manifest, `resolve_ref` returns
    `RefStatus.UNKNOWN` (v1 ships no runtime-side sibling-walking
    surface; consumers wire local-clone reading through the callback).
    """

    repo: str
    work_item_id: str
    kind: Literal["sibling_work_item"] = "sibling_work_item"


@dataclass(frozen=True, slots=True, kw_only=True)
class PullRequestDependency:
    """A specific GitHub pull request.

    Resolved via `gh pr view <number> --repo <github_url>`. Closed
    iff `state == "MERGED"` OR `state == "CLOSED"` (resolved either
    way unblocks the dependent work-item; the consumer's ranker
    decides whether closed-but-unmerged warrants a different urgency).
    """

    repo: str
    number: int
    kind: Literal["pull_request"] = "pull_request"


@dataclass(frozen=True, slots=True, kw_only=True)
class BranchDependency:
    """A specific GitHub branch.

    `name` MUST be the branch name without the `refs/heads/` prefix.
    Resolved via `gh api` against the remote: a missing branch resolves
    to `CLOSED` (assumes deleted-after-merge), a present branch is
    further checked against the default branch with `gh api compare`
    to derive merged-vs-unmerged.
    """

    repo: str
    name: str
    kind: Literal["branch"] = "branch"


DependsOnEntry: TypeAlias = (
    LocalDependency | SiblingWorkItemDependency | PullRequestDependency | BranchDependency
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CrossRepoTarget:
    """A single entry in `.livespec.jsonc`'s `cross_repo_targets` block.

    `github_url`     — REQUIRED; canonical `https://github.com/<owner>/<name>`
                       URL. Trailing `.git` and/or trailing `/` are
                       accepted (the provider's `_split_owner_name`
                       strips both). Any other shape (ssh, git-protocol,
                       bare owner/name, non-github host) raises
                       `NonCanonicalGithubUrlError` at the provider
                       boundary.
    `local_clone`    — OPTIONAL; filesystem path to a local clone. Held
                       on the typed manifest for consumer use (e.g.,
                       routing a `sibling_status_lookup` callback to a
                       local JSONL reader); the v1 runtime surface does
                       NOT read local clones directly.
    `default_branch` — OPTIONAL; defaults to "master". The repo's default
                       branch name used for "branch merged into default"
                       derivations.
    """

    github_url: str
    local_clone: Path | None = None
    default_branch: str = "master"


@dataclass(frozen=True, slots=True, kw_only=True)
class CrossRepoManifest:
    """In-memory view of the `.livespec.jsonc` `cross_repo_targets` block.

    The mapping keys are short repo slugs (used as the `repo` field
    in every typed `depends_on` entry). The block is OPTIONAL at the
    top level — projects with no cross-repo dependencies pass an empty
    mapping.
    """

    targets: dict[str, CrossRepoTarget]


def parse_depends_on_entry(*, parsed: dict[str, Any]) -> DependsOnEntry:
    """Parse a dict-shaped depends_on entry into a typed variant.

    Raises `CrossRepoSchemaError` with a descriptive `detail` when:
    - the `kind` field is missing,
    - the `kind` value is not one of the four enumerated variants,
    - a per-kind required field is missing.

    The function does NOT validate the surrounding work-item record;
    that responsibility stays with the impl-plugin's store layer.
    """
    if "kind" not in parsed:
        raise CrossRepoSchemaError(
            detail="depends_on entry missing required field 'kind'",
        )
    kind_raw = parsed["kind"]
    if kind_raw not in ("local", "sibling_work_item", "pull_request", "branch"):
        raise CrossRepoSchemaError(
            detail=(
                f"depends_on entry has unknown kind {kind_raw!r}; "
                f"expected one of: local, sibling_work_item, pull_request, branch"
            ),
        )
    kind: DependsOnKind = kind_raw
    match kind:
        case "local":
            return _parse_local(parsed=parsed)
        case "sibling_work_item":
            return _parse_sibling_work_item(parsed=parsed)
        case "pull_request":
            return _parse_pull_request(parsed=parsed)
        case "branch":
            return _parse_branch(parsed=parsed)
        case _:
            assert_never(kind)


def parse_cross_repo_manifest(*, parsed: dict[str, Any]) -> CrossRepoManifest:
    """Parse a dict-shaped cross_repo_targets block into a typed manifest.

    Raises `CrossRepoSchemaError` when any target entry is missing its
    required `github_url` field. Optional fields (`local_clone`,
    `default_branch`) fall back to dataclass defaults when absent.
    """
    targets: dict[str, CrossRepoTarget] = {}
    for slug, target_dict in parsed.items():
        targets[slug] = _parse_cross_repo_target(slug=slug, parsed=target_dict)
    return CrossRepoManifest(targets=targets)


def _parse_local(*, parsed: dict[str, Any]) -> LocalDependency:
    _require_field(parsed=parsed, field="work_item_id", kind_label="local")
    return LocalDependency(work_item_id=parsed["work_item_id"])


def _parse_sibling_work_item(*, parsed: dict[str, Any]) -> SiblingWorkItemDependency:
    _require_field(parsed=parsed, field="repo", kind_label="sibling_work_item")
    _require_field(parsed=parsed, field="work_item_id", kind_label="sibling_work_item")
    return SiblingWorkItemDependency(
        repo=parsed["repo"],
        work_item_id=parsed["work_item_id"],
    )


def _parse_pull_request(*, parsed: dict[str, Any]) -> PullRequestDependency:
    _require_field(parsed=parsed, field="repo", kind_label="pull_request")
    _require_field(parsed=parsed, field="number", kind_label="pull_request")
    return PullRequestDependency(repo=parsed["repo"], number=parsed["number"])


def _parse_branch(*, parsed: dict[str, Any]) -> BranchDependency:
    _require_field(parsed=parsed, field="repo", kind_label="branch")
    _require_field(parsed=parsed, field="name", kind_label="branch")
    return BranchDependency(repo=parsed["repo"], name=parsed["name"])


def _parse_cross_repo_target(*, slug: str, parsed: dict[str, Any]) -> CrossRepoTarget:
    if "github_url" not in parsed:
        raise CrossRepoSchemaError(
            detail=f"cross_repo_targets[{slug!r}] missing required field 'github_url'",
        )
    local_clone_raw = parsed.get("local_clone")
    local_clone = None if local_clone_raw is None else Path(local_clone_raw)
    default_branch = parsed.get("default_branch", "master")
    return CrossRepoTarget(
        github_url=parsed["github_url"],
        local_clone=local_clone,
        default_branch=default_branch,
    )


def _require_field(*, parsed: dict[str, Any], field: str, kind_label: str) -> None:
    if field not in parsed:
        raise CrossRepoSchemaError(
            detail=(
                f"depends_on entry of kind {kind_label!r} " f"missing required field {field!r}"
            ),
        )
