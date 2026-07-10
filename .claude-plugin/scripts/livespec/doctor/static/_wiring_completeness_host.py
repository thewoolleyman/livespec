"""Host-repo detection helpers for wiring completeness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.result import Success, safe

__all__: list[str] = ["is_host_repo"]


@safe(exceptions=(OSError,))
def _raw_path_resolve(*, path: Path) -> Path:
    """`@safe`-lifted call into pathlib.Path.resolve."""
    return path.resolve()


def is_host_repo(
    *,
    sibling_slug: str,
    target: dict[str, Any],
    project_root: Path,
    env: dict[str, str] | None = None,
) -> bool:
    """Return True when this target represents the same repo as `project_root`.

    Two-tier detection:

    1. **Slug-vs-basename match** (env-var-tolerant). When
       `sibling_slug` equals `project_root.name`, the target IS
       the host — regardless of any manifest `local_clone` value.
       This covers the CI case where the manifest's
       `local_clone: /data/projects/<repo>` doesn't exist on the
       runner, but the runner's checkout DOES sit at
       `/home/runner/work/<repo>/<repo>` whose basename matches
       the slug. Without this slug-keyed identity check, the host
       repo would be walked as a sibling in CI (resolving its
       effective path via the env-var override and failing because
       the CI workflow deliberately clones ONLY non-host siblings).

    2. **Path-comparison fallback** (local-dev). When the basename
       doesn't match, fall back to comparing the manifest's
       `local_clone` against `project_root`:
         - they resolve to the same path (host primary checkout case), OR
         - `project_root` resolves to a path under the manifest clone
           (the worktree-under-primary case — the doctor is being
           invoked from a secondary worktree of the primary checkout,
           e.g., `project_root=/repo/.claude/worktrees/li-X` and the
           manifest clone is `/repo`).

    Host detection uses the MANIFEST'S declared `local_clone` value
    (not the env-overridden effective path) — the manifest is the
    authoritative source-of-truth for which target names the host.
    (The `env` parameter is retained for signature symmetry with
    `resolve_effective_local_clone` but unused here — the basename
    tier doesn't read it, and the path tier deliberately uses the
    manifest value.)

    Path.resolve can raise OSError on filesystems with strict-symlink
    or permission-denied edge cases; the `@safe`-lifted helper
    converts the raise-path to a Result. A failed resolve (either
    side) yields False — the entry is treated as a non-host sibling.
    """
    _ = env  # env retained for signature symmetry with resolve_effective_local_clone
    if sibling_slug == project_root.name:
        return True
    local_clone_raw = target.get("local_clone")
    if not isinstance(local_clone_raw, str) or local_clone_raw == "":
        return False
    local_resolved = _raw_path_resolve(path=Path(local_clone_raw))
    project_resolved = _raw_path_resolve(path=project_root)
    if not isinstance(local_resolved, Success) or not isinstance(project_resolved, Success):
        return False
    local_path = local_resolved.unwrap()
    project_path = project_resolved.unwrap()
    if local_path == project_path:
        return True
    return local_path in project_path.parents
