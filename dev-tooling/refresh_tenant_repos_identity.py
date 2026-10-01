"""Who a registered repo really is — the `gh` calls that answer it, and URL parsing.

A registry records the owner and name a repo was adopted under. GitHub
keeps serving that pair after a RENAME or a TRANSFER by redirecting it,
so the registered pair NAMES the repository without LOCATING it. Only
`gh repo view --json nameWithOwner` locates it, and until that answer is
in hand there is no URL to clone from and no identity to validate an
existing clone's `origin` against. That is why every pass resolves the
canonical identity FIRST: the live `thewoolleyman/homelab` ->
`mi-homelab/homelab` transfer means a clone already carrying the
post-transfer URL would otherwise be reported as somebody else's
repository and preserved on every host, forever.

`gh` is the ONLY identity authority here — `gh repo view` for the
identity and `gh auth status` for the preflight. It is deliberately NOT
the clone transport: `gh repo clone <owner/repo>` picks its protocol from
gh's own `git_protocol` setting, which is `ssh` on the maintainer's Mac,
so a slug clone would go over SSH and need separate SSH auth — the very
problem the HTTPS fetch exists to remove. Cloning lives in
`refresh_tenant_repos_git` and addresses the canonical HTTPS URL built
here. No mapping is hardcoded and no
registry file is rewritten to record one — a redirect is a fact about the
forge, and reading it from the forge is what keeps the refresher correct
the next time one happens.

The URL side is pure and deliberately has TWO functions. `parse_remote_url`
DESCRIBES a remote — the host it names and its `owner/repo` tail — which is
what a report needs. `github_slug` DECIDES, and it is an allowlist rather
than a description: it recognizes exactly
`https://github.com/<owner>/<repo>[.git][/]`,
`ssh://git@github.com/<owner>/<repo>[.git]`, and
`git@github.com:<owner>/<repo>[.git]`, and answers None for everything
else. Describing is too weak to decide with, in two ways that both end in
an unrelated repository being refreshed: comparing the `owner/repo` tail
alone accepts another forge or a filesystem path whose last two segments
happen to match, and taking the LAST TWO segments of a longer path accepts
`https://github.com/extra/owner/repo` — while a scheme-only difference
accepts `file://github.com/owner/repo`. So the decider pins the scheme,
the host, the absence of any userinfo, and the exact segment count.

Following the `dev-tooling/` house style this module is standalone: it
shells out to `gh` through its own `subprocess.run` and imports nothing
from `.claude-plugin/scripts/livespec/`. No function raises on a failed
invocation — each returns the failure as data so the caller can preserve
one repo and carry on to the next.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import cast

__all__: list[str] = [
    "CanonicalIdentity",
    "IdentityResolution",
    "RemoteUrl",
    "canonical_identity",
    "github_slug",
    "https_url",
    "parse_remote_url",
    "preflight",
]

GITHUB_HOST = "github.com"
# Both fields come back from ONE `gh repo view`: the canonical
# `owner/repo` a redirect resolves to, and the branch to land on when no
# registry declared one.
_VIEW_FIELDS = "nameWithOwner,defaultBranchRef"
# The only three remote-URL shapes `github_slug` accepts. Each is matched
# as a literal PREFIX, so a userinfo prefix, a port, or a different
# scheme fails to match rather than being normalized away.
_HTTPS_PREFIX = f"https://{GITHUB_HOST}/"
_SSH_PREFIX = f"ssh://git@{GITHUB_HOST}/"
_SCP_PREFIX = f"git@{GITHUB_HOST}:"
# A GitHub repository path is exactly `<owner>/<repo>` — two segments.
# An extra one means a different URL that merely ENDS in the right pair.
_PATH_SEGMENTS = 2


@dataclass(frozen=True, kw_only=True)
class CanonicalIdentity:
    """Where a registered repo ACTUALLY lives, as GitHub itself reports it.

    `default_branch` is None for a repository that has no branches yet —
    an identity without a branch to land on, which the caller reports
    rather than guessing at.
    """

    name_with_owner: str
    default_branch: str | None


@dataclass(frozen=True, kw_only=True)
class IdentityResolution:
    """The canonical identity, or why `gh repo view` could not supply one.

    Exactly one field is set. `identity` being None is what stops a pass
    before it builds a clone URL or judges an `origin` against a guess.
    """

    identity: CanonicalIdentity | None
    problem: str | None


@dataclass(frozen=True, kw_only=True)
class RemoteUrl:
    """The host and `owner/repo` a git remote URL names, normalized for comparison.

    An EMPTY host means the URL named none — a filesystem path — which no
    github.com comparison can ever accept.
    """

    host: str
    slug: str


def _gh(*, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=False)


def preflight() -> str | None:
    """Why `gh` cannot be used, or None. Runs BEFORE any clone or fetch.

    Both legs matter: a missing binary and an unauthenticated one fail
    the same operations, and finding out mid-run would leave some repos
    refreshed and the rest reported as clone failures.
    """
    if shutil.which("gh") is None:
        return "`gh` is not on PATH"
    status = _gh(args=["auth", "status"])
    if status.returncode != 0:
        return f"`gh auth status` failed: {(status.stderr or status.stdout).strip()}"
    return None


def https_url(*, name_with_owner: str) -> str:
    """The HTTPS clone and fetch URL for a canonical `owner/repo`."""
    return f"https://{GITHUB_HOST}/{name_with_owner}"


def canonical_identity(*, owner: str, repo: str) -> IdentityResolution:
    """Ask GitHub where `owner/repo` actually lives and what its default branch is.

    One call answers both, and it runs before any clone and before any
    `origin` validation, so a redirected repository is cloned FROM — and
    judged AGAINST — the identity it redirects TO.
    """
    slug = f"{owner}/{repo}"
    view = _gh(args=["repo", "view", slug, "--json", _VIEW_FIELDS])
    if view.returncode != 0:
        detail = (view.stderr or view.stdout).strip()
        return IdentityResolution(identity=None, problem=f"`gh repo view {slug}` failed: {detail}")
    return _resolved(slug=slug, payload=view.stdout)


def _resolved(*, slug: str, payload: str) -> IdentityResolution:
    """Read `nameWithOwner` and `defaultBranchRef` out of a `gh repo view` payload."""
    fields = cast(dict[str, object], json.loads(payload))
    name_with_owner = fields.get("nameWithOwner")
    if not isinstance(name_with_owner, str) or not name_with_owner:
        return IdentityResolution(
            identity=None,
            problem=f"`gh repo view {slug}` reported no `nameWithOwner`",
        )
    return IdentityResolution(
        identity=CanonicalIdentity(
            name_with_owner=name_with_owner,
            default_branch=_default_branch(ref=fields.get("defaultBranchRef")),
        ),
        problem=None,
    )


def _default_branch(*, ref: object) -> str | None:
    """`defaultBranchRef.name`, or None for a repository with no branches yet."""
    if not isinstance(ref, dict):
        return None
    name = cast(dict[str, object], ref).get("name")
    if not isinstance(name, str) or not name:
        return None
    return name


def github_slug(*, url: str) -> str | None:
    """The `owner/repo` an EXACTLY-recognized github.com remote names, or None.

    An allowlist, not a parse. Only the three forms git itself writes for
    a GitHub remote are recognized, each with exactly two path segments;
    any other scheme, host, userinfo, port, or extra segment answers None
    and preserves the repository. See this module's docstring for the two
    concrete URLs a looser rule accepts.
    """
    trimmed = url.strip().removesuffix("/").removesuffix(".git")
    for prefix in (_HTTPS_PREFIX, _SSH_PREFIX, _SCP_PREFIX):
        if trimmed.startswith(prefix):
            return _exactly_two_segments(path=trimmed[len(prefix) :])
    return None


def _exactly_two_segments(*, path: str) -> str | None:
    """`owner/repo`, lowercased, when `path` is EXACTLY two non-empty segments."""
    segments = path.split("/")
    if len(segments) != _PATH_SEGMENTS or not all(segments):
        return None
    return path.lower()


def parse_remote_url(*, url: str) -> RemoteUrl:
    """Split a git remote URL into the HOST it names and its `owner/repo` tail.

    Collapses the forms that name the same repository — HTTPS with or
    without a `.git` suffix or a trailing slash, with or without a
    userinfo prefix, `ssh://git@host[:port]/owner/repo`, and the scp-like
    `git@host:owner/repo` — onto one comparable value. A plain filesystem
    path names no host and answers an empty one.
    """
    trimmed = url.strip().removesuffix("/").removesuffix(".git")
    _, separator, rest = trimmed.partition("://")
    if separator:
        authority, _, path = rest.partition("/")
    elif _is_scp_like(url=trimmed):
        authority, _, path = trimmed.partition(":")
    else:
        return RemoteUrl(host="", slug=_slug(path=trimmed))
    host = authority.rpartition("@")[2].partition(":")[0]
    return RemoteUrl(host=host.lower(), slug=_slug(path=path))


def _is_scp_like(*, url: str) -> bool:
    """Whether `url` is the scheme-less scp-like `[user@]host:owner/repo` form."""
    return "@" in url and ":" in url.rpartition("@")[2]


def _slug(*, path: str) -> str:
    """The lowercased `owner/repo` tail of a remote URL path."""
    return "/".join(path.split("/")[-2:]).lower()
