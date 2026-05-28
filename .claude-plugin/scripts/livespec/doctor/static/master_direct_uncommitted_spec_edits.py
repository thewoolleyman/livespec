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
"""Static-phase doctor check: master_direct_uncommitted_spec_edits.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → §"`master-direct-uncommitted-spec-edits`":

  Every worktree (primary or secondary, per
  `git worktree list --porcelain`) whose HEAD points at the
  default branch MUST NOT carry uncommitted modifications under
  `<spec-root>/`. The check enumerates every worktree, identifies
  the subset whose HEAD is the default branch (typically
  `master`), and for each invokes `git status --porcelain`
  scoped to `<spec-root>/`. Any non-empty output fires `warn`
  (NOT `fail`, consistent with the v079 prose at
  `non-functional-requirements.md:746` — "a `warn` finding") with
  corrective-action narration that names the offending worktree
  path, names the modified files, and directs the user to either
  commit-into-a-feature-branch (`git checkout -b <branch>` then
  commit) per the workflow discipline, OR to discard the edits
  (`git checkout -- <files>`) if they were unintentional.

  The check covers the secondary-worktree-on-master bypass that
  the sibling `primary-checkout-commit-refuse-hook-installed`
  invariant cannot physically prevent (the commit-refuse hook
  fires only when `git rev-parse --show-toplevel` equals the
  configured primary path; secondary worktrees on master pass
  that comparison and proceed to commit, so a
  `git worktree add /path master` + edit + commit at the
  secondary worktree bypasses the hook).

  Committed-and-then-discovered violations (the user committed
  on master and now the commit needs to be moved) are out of
  scope here; the existing `out-of-band-edits` check surfaces
  those via the snapshot-mismatch invariant.

Skip conditions (Finding.status='skipped'):
  - `project_root` is not a git working tree (`is_git_repo`
    returns False), OR
  - any IO precondition lifts on the railway (lashed into a
    skipped finding so the orchestrator's stdout contract stays
    uniform).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-master-direct-uncommitted-spec-edits")


def _pass(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a pass-status Finding."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _skipped(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a skipped-status Finding."""
    return Finding(
        check_id=SLUG,
        status="skipped",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _warn(*, ctx: DoctorContext, message: str) -> Finding:
    """Build a warn-status Finding (v074 status enum)."""
    return Finding(
        check_id=SLUG,
        status="warn",
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _extract_status_path(*, status_line: str) -> str:
    """Return the path component of one `git status --porcelain` line.

    The porcelain v1 format is `XY <path>` where `XY` is the
    fixed 2-char status field and `<path>` is the worktree-
    relative path. The first 3 characters (`XY` plus separator
    space) are sliced off; the remainder is returned as-is. For
    rename entries (`R  old -> new`) the entire remainder is
    returned verbatim — this check surfaces the literal porcelain
    line content to the user, so rename arrows are preserved.
    """
    return status_line[3:]


def _format_worktree_violation(*, worktree_path: Path, status_lines: tuple[str, ...]) -> str:
    """Render one worktree's violation summary for the warn message.

    Lists the worktree path followed by each modified file path.
    """
    paths = sorted(_extract_status_path(status_line=line) for line in status_lines)
    paths_joined = ", ".join(paths)
    return f"{worktree_path}: {paths_joined}"


def _evaluate(
    *,
    ctx: DoctorContext,
    default_branch: str,
    violations: tuple[tuple[Path, tuple[str, ...]], ...],
    worktrees_on_default_count: int,
) -> Finding:
    """Build the pass-or-warn Finding from the per-worktree status results.

    `violations` is a tuple of `(worktree_path, status_lines)`
    pairs for every worktree on the default branch whose
    `git status --porcelain <spec-root>/` produced at least one
    line. An empty `violations` tuple yields a pass.
    """
    if not violations:
        return _pass(
            ctx=ctx,
            message=(
                f"master-direct-uncommitted-spec-edits: no worktrees on "
                f"`{default_branch}` carry uncommitted spec-tree edits "
                f"({worktrees_on_default_count} worktree(s) on `{default_branch}` "
                f"scanned)"
            ),
        )
    summaries = "; ".join(
        _format_worktree_violation(worktree_path=path, status_lines=lines)
        for path, lines in violations
    )
    return _warn(
        ctx=ctx,
        message=(
            f"master-direct-uncommitted-spec-edits: "
            f"{len(violations)} worktree(s) on `{default_branch}` carry "
            f"uncommitted spec-tree edits: {summaries}. Corrective action: "
            f"either move the edits to a feature branch "
            f"(`git checkout -b <branch>` then commit), or discard them "
            f"(`git checkout -- <files>`)."
        ),
    )


def _collect_violation(
    *,
    project_root: Path,
    worktree_path: Path,
    spec_rel: Path,
) -> IOResult[tuple[Path, tuple[str, ...]] | None, LivespecError]:
    """Run `git status --porcelain` for `worktree_path/spec_rel` and lift the result.

    Returns IOSuccess(None) when the per-worktree status produces
    zero porcelain lines (no violation for this worktree).
    Returns IOSuccess((worktree_path, status_lines)) when the
    status produces at least one line (violation; non-empty
    tuple). Per-worktree spec-root resolution uses
    `worktree_path / spec_rel` so the check works uniformly for
    primary and secondary worktrees; `project_root` is unused in
    the per-worktree invocation (the `-C` flag pins git to the
    worktree).
    """
    _ = project_root
    return io_git.list_status_porcelain(
        project_root=worktree_path,
        pathspec=spec_rel,
    ).map(
        lambda lines: (worktree_path, lines) if lines else None,
    )


def _collect_all_violations(
    *,
    project_root: Path,
    worktrees_on_default: tuple[io_git.Worktree, ...],
    spec_rel: Path,
    accumulated: tuple[tuple[Path, tuple[str, ...]], ...] = (),
) -> IOResult[tuple[tuple[Path, tuple[str, ...]], ...], LivespecError]:
    """Sequentially collect per-worktree status results into one tuple.

    Walks `worktrees_on_default` head-first, recursing on the
    tail with the head's result appended (when non-None) to
    `accumulated`. An IOFailure anywhere short-circuits the chain
    via `.bind`'s standard short-circuit semantics. Empty input
    yields IOSuccess(accumulated).
    """
    if not worktrees_on_default:
        return IOResult.from_value(accumulated)
    head, *tail = worktrees_on_default
    return _collect_violation(
        project_root=project_root,
        worktree_path=head.path,
        spec_rel=spec_rel,
    ).bind(
        lambda result: _collect_all_violations(
            project_root=project_root,
            worktrees_on_default=tuple(tail),
            spec_rel=spec_rel,
            accumulated=(*accumulated, result) if result is not None else accumulated,
        ),
    )


def _on_repo(
    *,
    ctx: DoctorContext,
) -> IOResult[Finding, LivespecError]:
    """Run the check given that `project_root` is a git working tree.

    Composes get_default_branch_name → list_worktrees → filter
    by branch == default → per-worktree status → _evaluate. The
    spec-root path is relativized against `project_root` once
    (so the check fails fast if `spec_root` is not under
    `project_root`, which would be a configuration bug, not a
    domain error — raised as ValueError from `relative_to`).
    """
    project_root = ctx.project_root
    spec_rel = ctx.spec_root.relative_to(project_root)
    return io_git.get_default_branch_name(project_root=project_root).bind(
        lambda default_branch: io_git.list_worktrees(
            project_root=project_root,
        ).bind(
            lambda worktrees: _collect_all_violations(
                project_root=project_root,
                worktrees_on_default=tuple(wt for wt in worktrees if wt.branch == default_branch),
                spec_rel=spec_rel,
            ).map(
                lambda violations: _evaluate(
                    ctx=ctx,
                    default_branch=default_branch,
                    violations=violations,
                    worktrees_on_default_count=sum(
                        1 for wt in worktrees if wt.branch == default_branch
                    ),
                ),
            ),
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run master-direct-uncommitted-spec-edits against `ctx`.

    Composes is_git_repo → _on_repo. Any failure on the IO track
    is lashed into a skipped-status Finding so the orchestrator's
    stdout contract stays uniform; non-git project_roots surface
    a skipped finding rather than an IOFailure.
    """
    project_root = ctx.project_root
    return (
        io_git.is_git_repo(project_root=project_root)
        .bind(
            lambda is_repo: (
                _on_repo(ctx=ctx)
                if is_repo
                else IOResult.from_value(
                    _skipped(
                        ctx=ctx,
                        message=(
                            "master-direct-uncommitted-spec-edits: project_root "
                            "is not a git working tree; check skipped"
                        ),
                    ),
                )
            ),
        )
        .lash(
            lambda err: IOSuccess(
                _skipped(
                    ctx=ctx,
                    message=(
                        f"master-direct-uncommitted-spec-edits: precondition "
                        f"not met ({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
