# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""Justfile resolution helpers for wiring completeness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult

from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    GithubRepoIdentity,
    decode_gh_contents_payload,
    parse_owner_name_from_github_url,
    resolve_effective_local_clone,
)
from livespec.errors import LivespecError
from livespec.io import proc

__all__: list[str] = ["_resolve_sibling_justfile"]


def _read_justfile_from_local_clone(
    *,
    local_clone: Path,
) -> IOResult[str | None, LivespecError]:
    """Read `<local_clone>`'s justfile from the git database at HEAD.

    Uses `git -C <local_clone> show HEAD:justfile` rather than a
    direct filesystem read. The git db is the canonical source of
    truth for the cross-repo invariant — the working tree may lag
    HEAD on any of the configurations the check accepts (bare
    clones, shallow clones, normal working-tree clones with
    uncommitted local edits).

    Returns `IOSuccess(<text>)` on the happy path (git show
    succeeds, stdout is the justfile body). Returns
    `IOSuccess(None)` on any non-zero exit — covering all three
    documented failure modes:

      - `local_clone` exists but isn't a git directory (no `.git`
        and not a bare repo): `git -C` exits 128 with `fatal: not
        a git repository`.
      - `HEAD:justfile` doesn't exist (deleted from master or
        never present): `git show` exits 128 with `fatal: path
        'justfile' does not exist in 'HEAD'`.
      - Any other git failure (e.g., corrupted repo): non-zero
        exit lifts to `IOSuccess(None)`.

    `None` is the signal to the caller that Path A failed; the
    railway then falls through to the GitHub-API Path B. Any
    OSError from the proc seam (e.g., `git` binary itself
    missing) lifts to IOFailure(PreconditionError) and is
    handled by the outer `.lash(...)` in `run()`.
    """
    argv = [
        "git",
        "-C",
        str(local_clone),
        "show",
        "HEAD:justfile",
    ]
    return proc.run_subprocess(argv=argv, cwd=None).map(
        lambda completed: (completed.stdout if completed.returncode == 0 else None),
    )


def _fetch_justfile_from_github(
    *,
    identity: GithubRepoIdentity,
    default_branch: str,
) -> IOResult[str | None, LivespecError]:
    """Fetch `<repo>/justfile` at `default_branch` via the GitHub API.

    Uses `gh api --method GET repos/<owner>/<name>/contents/justfile
    -f ref=<branch>` and base64-decodes the returned `content`
    field. Returns `IOSuccess(<text>)` on the happy path,
    `IOSuccess(None)` on any non-zero exit (gh not authenticated,
    repo private, network down, justfile absent in repo).
    """
    argv = [
        "gh",
        "api",
        f"repos/{identity.owner}/{identity.name}/contents/justfile",
        # `--method GET` is load-bearing: `gh api` flips its default
        # method to POST whenever a `-f` field flag is present, and
        # POST on the contents endpoint is the create-file call
        # (answers 404 on this read). The contents endpoint stays at
        # argv[2] — the position consumers index on.
        "--method",
        "GET",
        "-f",
        f"ref={default_branch}",
    ]
    return proc.run_subprocess(argv=argv, cwd=None).bind(
        lambda completed: (
            IOResult.from_value(decode_gh_contents_payload(stdout=completed.stdout))
            if completed.returncode == 0
            else IOResult.from_value(None)
        ),
    )


def _resolve_via_github(
    *,
    target: dict[str, Any],
) -> IOResult[str | None, LivespecError]:
    """Resolve a sibling's justfile via the GitHub Contents API (Path B)."""
    github_url = target.get("github_url")
    if not isinstance(github_url, str):
        return IOResult.from_value(None)
    identity = parse_owner_name_from_github_url(github_url=github_url)
    if identity is None:
        return IOResult.from_value(None)
    default_branch_raw = target.get("default_branch", "master")
    default_branch = default_branch_raw if isinstance(default_branch_raw, str) else "master"
    return _fetch_justfile_from_github(identity=identity, default_branch=default_branch)


def _resolve_sibling_justfile(
    *,
    sibling_slug: str,
    target: dict[str, Any],
) -> IOResult[str | None, LivespecError]:
    """Resolve a single sibling's justfile text via local-clone-then-GitHub.

    Returns `IOSuccess(<text>)` when the justfile was successfully
    read by either path; `IOSuccess(None)` when neither path
    succeeded.

    Path A: `git -C <local_clone> show HEAD:justfile`. The effective
    `local_clone` is resolved via
    `resolve_effective_local_clone` so the
    `LIVESPEC_SIBLING_CLONES_ROOT` env-var override is honored (the
    CI workflow clones siblings to a fresh root and points the
    check at it via the env var). A non-zero git exit (no .git, no
    HEAD, missing justfile, corrupted repo) yields
    `IOSuccess(None)` and the railway falls through to Path B
    below.

    Path B: `gh api repos/<owner>/<name>/contents/justfile?ref=<branch>`
    with base64-decoding.
    """
    effective_local_clone = resolve_effective_local_clone(
        sibling_slug=sibling_slug,
        target=target,
    )
    if effective_local_clone is not None:
        local_clone = Path(effective_local_clone)
        return _read_justfile_from_local_clone(local_clone=local_clone).bind(
            lambda local_text: (
                IOResult.from_value(local_text)
                if local_text is not None
                else _resolve_via_github(target=target)
            ),
        )
    return _resolve_via_github(target=target)
