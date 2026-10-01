"""refresh_tenant_repos — clone or refresh every registered fleet + adopter repo.

The fleet spans many sibling repositories, and most cross-repo work needs
all of them present, current, and on their default branch as PEERS of the
livespec primary checkout. Doing that by hand is a dozen `cd`s and a
dozen chances to clobber work in progress. This tool does it in one pass,
deterministically, with no LLM involved.

WHICH REPOS. The union of the four committed registries, resolved by
`refresh_tenant_repos_registry` — `.livespec.jsonc`'s
`cross_repo_targets` and `cross_repo_conformance_targets`, plus
`.livespec-fleet-manifest.jsonc`'s `fleet[]` and `adopters[]`.

WHERE THEY LAND. `<peer-root>/<repo>`, where the peer root is the
directory CONTAINING the primary checkout — derived through
`--git-common-dir`, so the answer is the same whether the tool runs from
the primary checkout or from a linked worktree. The directory NAME is
always the REGISTERED repo name, even when the repository has since been
renamed on GitHub: the peer layout is the maintainer's, not the forge's.
A registry's `local_clone` path is deliberately not consulted.

WHICH IDENTITY. Every pass resolves the repo's CANONICAL identity from
GitHub first, via `refresh_tenant_repos_identity`, before it builds a
clone URL or judges an existing `origin`. A registry records the pair a
repo was adopted under, and a rename or transfer leaves that pair as a
redirect — so taking it as the repo's address reports the post-transfer
clone as somebody else's repository and preserves it on every host.

THE SAFETY POSTURE IS PRESERVE-BY-DEFAULT, and the ordering is the whole
design. Two conditions refuse the run OUTRIGHT with exit 2, before any
clone or fetch: a `gh` that is missing or unauthenticated, and a registry
set that disagrees with itself or names a repo that is not a single safe
path segment. Past that, each repo is handled independently: a missing
one is cloned, landed on its configured default branch, and proved clean
before it counts as done; an existing one is refreshed only after it
proves to be this repo's own primary checkout, on github.com, with a
clean tree and nothing unpushed. Anything else — including an inspection
that could not be trusted because git exited non-zero — is left EXACTLY
as found and reported with the cleanup commands its particular state
calls for. The fetch happens BEFORE the unpushed and divergence
decisions precisely so those decisions read refs updated in the same run.

EXIT CODES. 0 every repo cloned or refreshed; 1 at least one preserved or
failed; 2 refused before touching anything.

This is a maintainer ACTION tool invoked via `just refresh-tenant-repos`,
not a member of `just check`. Output discipline per spec: `print` and
`sys.stderr.write` are banned in `dev-tooling/**`, so diagnostics flow
through structlog as JSON on stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

_DEV_TOOLING_DIR = Path(__file__).resolve().parent
if str(_DEV_TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_TOOLING_DIR))

import jsoncomment  # noqa: E402  — path-aware import after sys.path insert.
import structlog  # noqa: E402  — path-aware import after sys.path insert.
from refresh_tenant_repos_git import primary_checkout  # noqa: E402
from refresh_tenant_repos_identity import preflight  # noqa: E402
from refresh_tenant_repos_pass import process_target  # noqa: E402
from refresh_tenant_repos_registry import resolve_targets  # noqa: E402

__all__: list[str] = ["main", "refresh_tenant_repos"]

_CONFIG_NAME = ".livespec.jsonc"
_MANIFEST_NAME = ".livespec-fleet-manifest.jsonc"


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("refresh_tenant_repos")


def _parse_jsonc(*, path: Path) -> object:
    return jsoncomment.loads(path.read_text(encoding="utf-8"))


def refresh_tenant_repos(*, project_root: Path) -> int:
    """Clone or refresh every registered repo as a peer of `project_root`'s primary.

    Returns 0 when every target was cloned or refreshed, 1 when at least
    one was preserved or failed, and 2 when the run refused before
    touching anything.
    """
    log = _configure_logger()
    resolution = resolve_targets(
        livespec_config=_parse_jsonc(path=project_root / _CONFIG_NAME),
        fleet_manifest=_parse_jsonc(path=project_root / _MANIFEST_NAME),
    )
    if resolution.conflicts:
        for conflict in resolution.conflicts:
            log.error("refusing to mutate anything: registry conflict", issue=conflict)
        return 2
    gh_problem = preflight()
    if gh_problem is not None:
        log.error("refusing to clone or fetch anything", issue=gh_problem)
        return 2
    primary = primary_checkout(project_root=project_root)
    if primary is None:
        log.error("project root is not inside a git repository", path=str(project_root))
        return 2
    peer_root = primary.parent
    preserved: list[str] = []
    for target in resolution.targets:
        if process_target(target=target, peer_root=peer_root, log=log) is not None:
            preserved.append(target.repo)
    log.info(
        "refresh complete",
        peer_root=str(peer_root),
        targets=[target.repo for target in resolution.targets],
        preserved=preserved,
    )
    return 1 if preserved else 0


def main(*, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="refresh_tenant_repos", add_help=True)
    _ = parser.add_argument(
        "--project-root",
        default=str(Path.cwd()),
        help="the livespec checkout whose registries name the repo set (default: cwd)",
    )
    namespace = parser.parse_args(argv)
    return refresh_tenant_repos(project_root=Path(str(namespace.project_root)).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
