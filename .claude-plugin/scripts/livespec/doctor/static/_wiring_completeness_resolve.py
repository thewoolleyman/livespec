# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""Justfile resolution helpers for wiring completeness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple

from returns.io import IOResult

from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    GithubRepoIdentity,
    decode_gh_contents_payload,
    parse_owner_name_from_github_url,
    resolve_effective_local_clone,
)
from livespec.errors import LivespecError
from livespec.io import proc

__all__: list[str] = ["ResolvedCheckSource", "_resolve_sibling_check_source"]


_INVENTORY_PATH = "check-targets.txt"
_JUSTFILE_PATH = "justfile"


class ResolvedCheckSource(NamedTuple):
    """A sibling's selected aggregate source and its committed text."""

    kind: str
    text: str


def _read_file_from_local_clone(
    *,
    local_clone: Path,
    repo_path: str,
) -> IOResult[str | None, LivespecError]:
    """Read a sibling file from the local clone's git database at HEAD.

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
      - `HEAD:<repo_path>` doesn't exist (deleted from master or
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
        f"HEAD:{repo_path}",
    ]
    return proc.run_subprocess(argv=argv, cwd=None).map(
        lambda completed: (completed.stdout if completed.returncode == 0 else None),
    )


def _fetch_file_from_github(
    *,
    identity: GithubRepoIdentity,
    default_branch: str,
    repo_path: str,
) -> IOResult[str | None, LivespecError]:
    """Fetch a sibling file at `default_branch` via the GitHub API.

    Uses `gh api --method GET repos/<owner>/<name>/contents/justfile
    -f ref=<branch>` and base64-decodes the returned `content`
    field. Returns `IOSuccess(<text>)` on the happy path,
    `IOSuccess(None)` on any non-zero exit (gh not authenticated,
    repo private, network down, justfile absent in repo).
    """
    argv = [
        "gh",
        "api",
        f"repos/{identity.owner}/{identity.name}/contents/{repo_path}",
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
) -> IOResult[ResolvedCheckSource | None, LivespecError]:
    """Resolve inventory-first aggregate wiring via GitHub (Path B)."""
    github_url = target.get("github_url")
    if not isinstance(github_url, str):
        return IOResult.from_value(None)
    identity = parse_owner_name_from_github_url(github_url=github_url)
    if identity is None:
        return IOResult.from_value(None)
    default_branch_raw = target.get("default_branch", "master")
    default_branch = default_branch_raw if isinstance(default_branch_raw, str) else "master"
    return _fetch_file_from_github(
        identity=identity,
        default_branch=default_branch,
        repo_path=_INVENTORY_PATH,
    ).bind(
        lambda inventory_text: (
            IOResult.from_value(ResolvedCheckSource("inventory", inventory_text))
            if inventory_text is not None
            else _fetch_file_from_github(
                identity=identity,
                default_branch=default_branch,
                repo_path=_JUSTFILE_PATH,
            ).map(
                lambda justfile_text: (
                    ResolvedCheckSource("justfile", justfile_text)
                    if justfile_text is not None
                    else None
                ),
            )
        ),
    )


def _resolve_sibling_check_source(
    *,
    sibling_slug: str,
    target: dict[str, Any],
) -> IOResult[ResolvedCheckSource | None, LivespecError]:
    """Resolve a sibling's inventory-first aggregate source over both paths.

    `check-targets.txt` takes precedence whenever present, matching
    the producer's own completeness checks. A missing inventory
    falls back to the existing `targets=(...)` justfile source.

    Path A reads `HEAD:check-targets.txt`, then `HEAD:justfile`. The effective
    `local_clone` is resolved via
    `resolve_effective_local_clone` so the
    `LIVESPEC_SIBLING_CLONES_ROOT` env-var override is honored (the
    CI workflow clones siblings to a fresh root and points the
    check at it via the env var). A non-zero git exit (no .git, no
    HEAD, missing justfile, corrupted repo) yields
    `IOSuccess(None)` and the railway falls through to Path B
    below.

    Path B repeats the same precedence through the GitHub Contents API.
    """
    effective_local_clone = resolve_effective_local_clone(
        sibling_slug=sibling_slug,
        target=target,
    )
    if effective_local_clone is not None:
        local_clone = Path(effective_local_clone)
        return _read_file_from_local_clone(
            local_clone=local_clone,
            repo_path=_INVENTORY_PATH,
        ).bind(
            lambda inventory_text: (
                IOResult.from_value(ResolvedCheckSource("inventory", inventory_text))
                if inventory_text is not None
                else _read_file_from_local_clone(
                    local_clone=local_clone,
                    repo_path=_JUSTFILE_PATH,
                ).bind(
                    lambda justfile_text: (
                        IOResult.from_value(ResolvedCheckSource("justfile", justfile_text))
                        if justfile_text is not None
                        else _resolve_via_github(target=target)
                    ),
                )
            ),
        )
    return _resolve_via_github(target=target)
