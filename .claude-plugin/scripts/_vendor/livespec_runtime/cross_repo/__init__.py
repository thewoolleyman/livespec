"""livespec_runtime.cross_repo — cross-repo work-item dependency resolution.

Implements the cross-repo dependency awareness contract from
livespec/SPECIFICATION/contracts.md v072 §"Cross-repo dependency
awareness" (landed by work-item li-e7h6ki under parent epic li-6d2wpj;
impl landed by li-aclzfe at v0.2.0).

Public surface lives in the sub-modules; consumers import directly
from them rather than the package namespace:

- `livespec_runtime.cross_repo.types` — typed `DependsOnEntry` union
  (LocalDependency / SiblingWorkItemDependency / PullRequestDependency
  / BranchDependency) discriminated on `Literal[...] kind`; the
  `CrossRepoManifest` / `CrossRepoTarget` view of the
  `cross_repo_targets` block; the `RefStatus` enum; and the
  `parse_*` dict-to-typed boundary helpers.
- `livespec_runtime.cross_repo.errors` — `CrossRepoSchemaError`, the
  single domain error raised by the parser helpers.
- `livespec_runtime.cross_repo.providers.github` — the `gh` CLI
  subprocess dispatch surface (PR state, branch existence,
  branch-merged-into-default).
- `livespec_runtime.cross_repo.retry` — 3-attempt 1s/2s/4s
  exponential backoff used by the resolve-walker.
- `livespec_runtime.cross_repo.resolve` — `resolve_ref`, the
  exhaustive walker that maps any `DependsOnEntry` to a `RefStatus`.

The package namespace itself stays empty (`__all__: list[str] = []`)
to keep the import contract explicit at the sub-module level; this
matches the discipline applied throughout livespec-core.
"""

__all__: list[str] = []
