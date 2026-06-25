# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: wiring_completeness_cross_repo.

Per `SPECIFICATION/contracts.md`:

  A doctor invariant `wiring-completeness-cross-repo` MUST walk
  every registered sibling repo (per the `livespec-dev-tooling`,
  `livespec-runtime`, and `livespec-impl-*` registries declared
  in `.livespec.jsonc`'s `cross_repo_targets` block), read its
  `justfile`'s `check` recipe, compute the canonical-set
  difference, and fire `fail` on any aggregate lacking any
  canonical slug.

  The check MAY use a sibling's `local_clone` path when
  configured or fall back to a GitHub query against the
  sibling's default-branch `justfile`. The invariant covers
  the adversarial-drift case in which a consumer drops both a
  canonical slug AND `check-aggregate-completeness` from its
  aggregate in the same change — the in-repo gate cannot catch
  that combination (the gate is gone before it next runs), but
  the cross-repo doctor backstop can.

Cross-boundary mechanism:

  - Path A (preferred): the effective local-clone path is set and
    resolves to a git repository → read the justfile from the git
    database via `git -C <local_clone> show HEAD:justfile`. The
    "effective" local-clone path is the value returned by the
    `resolve_effective_local_clone` helper: the
    `LIVESPEC_SIBLING_CLONES_ROOT` env-var override (`<root>/<sibling-slug>`)
    when set, otherwise the manifest's
    `cross_repo_targets[<slug>].local_clone` field. CI sets the
    env var to a freshly-cloned siblings-root so the check passes
    on ephemeral GitHub Actions runners; local-dev usage leaves it
    unset and reads from `/data/projects/<sibling>` via the
    manifest. Either way the read uses `git show HEAD:justfile`,
    so the read is git-db-backed and works on bare clones (the
    primary-checkout commit-refuse hook supersedes the bare-flag
    mechanism but bare clones remain valid as siblings).
  - Path B (fallback): Path A fails (no effective local_clone, path
    is not a git repo, `justfile` absent at HEAD, etc.) → GitHub
    API query via `gh api repos/<owner>/<name>/contents/justfile?ref=<default_branch>`
    with base64-decoding of the returned `content` field.

The host repo itself (the entry whose `local_clone` resolves to
`project_root`) is skipped — the in-repo
`aggregate_completeness` gate covers that case at every
`just check` invocation. This check is the FLEET-WIDE backstop
against the host repo's siblings.

Canonical slug set comes from
`livespec_dev_tooling.canonical_checks.canonical_check_slugs()`
which is dynamically discovered from the
`livespec_dev_tooling.checks.<slug>` package directory at every
call — no second source of truth.

Pure helpers (URL parsing, justfile parsing, slug diffing,
manifest filtering, finding construction, gh-payload decoding)
live in the sibling module
`_wiring_completeness_cross_repo_helpers.py`; this file owns
only the IO-touching railway composition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static._wiring_completeness_cross_repo_helpers import (
    GithubRepoIdentity,
    build_aggregate_finding,
    decode_gh_contents_payload,
    filter_sibling_targets,
    interpret_justfile_text,
    make_finding,
    parse_owner_name_from_github_url,
    resolve_effective_local_clone,
)
from livespec.errors import LivespecError
from livespec.io import fs, proc
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-wiring-completeness-cross-repo")


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


def _evaluate_sibling(
    *,
    sibling_slug: str,
    target: dict[str, Any],
    canonical_slugs: tuple[str, ...],
) -> IOResult[list[tuple[str, str]], LivespecError]:
    """Compute (sibling, missing-slug) pairs for one sibling on the IO track."""
    return _resolve_sibling_justfile(sibling_slug=sibling_slug, target=target).bind(
        lambda justfile_text: IOResult.from_value(
            interpret_justfile_text(
                sibling_slug=sibling_slug,
                justfile_text=justfile_text,
                canonical_slugs=canonical_slugs,
            ),
        ),
    )


def _fold_pairs(
    *,
    accumulator: IOResult[list[tuple[str, str]], LivespecError],
    sibling: tuple[str, dict[str, Any]],
    canonical_slugs: tuple[str, ...],
) -> IOResult[list[tuple[str, str]], LivespecError]:
    """Fold one sibling's evaluation into the accumulator on the IO track."""
    sibling_slug, target = sibling
    return accumulator.bind(
        lambda acc: _evaluate_sibling(
            sibling_slug=sibling_slug,
            target=target,
            canonical_slugs=canonical_slugs,
        ).map(
            lambda pairs: acc + pairs,
        ),
    )


def _resolve_canonical_slugs() -> tuple[str, ...] | None:
    """Resolve the canonical-slug set, lazily importing its dev-tooling substrate.

    `livespec_dev_tooling.canonical_checks.canonical_check_slugs` is the
    single source of truth for the fleet-wide canonical-check set, but
    `livespec_dev_tooling` is a NON-bundled sibling package: it is
    importable under `uv` (dev/CI) yet absent under bare `python3` (the
    `python3 bin/doctor_static.py` plugin flow the revise wrapper spawns
    via `sys.executable`) and in the installed-plugin bundle. Importing it
    at module top-level therefore crashed the ENTIRE static phase with a
    `ModuleNotFoundError` in those contexts, silently bypassing every
    static check (li-rvdctr).

    This helper imports the slug accessor lazily inside a
    `try/except ModuleNotFoundError` and returns `None` when the substrate
    is unimportable — the caller degrades the fleet-wide cross-repo
    backstop to a `skipped` finding (rather than crashing the whole phase)
    in exactly those bundle / bare-python3 contexts where it cannot run.
    When the substrate IS present, it returns the resolved slug tuple and
    the check proceeds exactly as before.
    """
    try:
        from livespec_dev_tooling.canonical_checks import canonical_check_slugs
    except ModuleNotFoundError:
        return None
    return canonical_check_slugs()


def _evaluate_manifest(
    *,
    ctx: DoctorContext,
    cross_repo_targets: dict[str, Any],
) -> IOResult[Finding, LivespecError]:
    """Walk every non-host sibling, aggregate per-sibling drift, build Finding."""
    canonical_slugs = _resolve_canonical_slugs()
    if canonical_slugs is None:
        return IOSuccess(
            make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "wiring-completeness-cross-repo: livespec_dev_tooling is "
                    "not importable (cross-repo canonical-slug set "
                    "unavailable); check skipped"
                ),
            ),
        )
    sibling_targets = filter_sibling_targets(
        cross_repo_targets=cross_repo_targets, project_root=ctx.project_root
    )
    if not sibling_targets:
        return IOSuccess(
            make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "wiring-completeness-cross-repo: cross_repo_targets "
                    "contains no sibling entries (only the host repo or empty); "
                    "no siblings to walk"
                ),
            ),
        )
    initial: IOResult[list[tuple[str, str]], LivespecError] = IOResult.from_value([])
    aggregated = initial
    for sibling in sibling_targets:
        aggregated = _fold_pairs(
            accumulator=aggregated,
            sibling=sibling,
            canonical_slugs=canonical_slugs,
        )
    return aggregated.bind(
        lambda all_pairs: IOSuccess(
            build_aggregate_finding(ctx=ctx, all_pairs=all_pairs),
        ),
    )


def _evaluate(*, ctx: DoctorContext, parsed: Any) -> IOResult[Finding, LivespecError]:
    """Handle the .livespec.jsonc-parsed config; route to manifest walker."""
    if not isinstance(parsed, dict):
        return IOSuccess(
            make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "wiring-completeness-cross-repo: .livespec.jsonc root is "
                    "not an object; check skipped"
                ),
            ),
        )
    cross_repo_targets = parsed.get("cross_repo_targets")
    if not isinstance(cross_repo_targets, dict):
        return IOSuccess(
            make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "wiring-completeness-cross-repo: project carries no "
                    "`cross_repo_targets` block; check skipped"
                ),
            ),
        )
    return _evaluate_manifest(ctx=ctx, cross_repo_targets=cross_repo_targets)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run wiring-completeness-cross-repo against `ctx`.

    Composes read(.livespec.jsonc) → jsonc.loads → manifest walk →
    per-sibling justfile resolution → canonical-slug diff →
    aggregate Finding. Any IO failure on the config-read or
    config-parse path lashes into a skipped-status Finding so the
    orchestrator's stdout contract stays uniform.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        fs.read_text(path=config_path)
        .bind(
            lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
        )
        .bind(lambda parsed: _evaluate(ctx=ctx, parsed=parsed))
        .lash(
            lambda err: IOSuccess(
                make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"wiring-completeness-cross-repo: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
