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

Per `SPECIFICATION/contracts.md`:

  Every worktree (primary or secondary, per
  `git worktree list --porcelain`) whose HEAD points at the
  default branch MUST NOT carry uncommitted modifications under
  `<spec-root>/` or under `plan/`. The check enumerates every
  worktree, identifies the subset whose HEAD is the default
  branch (typically `master`), and for each invokes
  `git status --porcelain` scoped to those two path prefixes,
  each resolved relative to that worktree's own root. Any
  non-empty output fires `warn` (NOT `fail`, consistent with the
  v079 prose — "a `warn` finding") with corrective-action
  narration that names the offending worktree path, names the
  modified files under each class respectively, and directs the
  user to commit-into-a-feature-branch per the workflow
  discipline.

  The narration is ASYMMETRIC by path class, and this is
  contract, not style: for `<spec-root>/` paths it MAY
  additionally offer discarding unintentional edits
  (`git checkout -- <files>`); for `plan/` paths it MUST NOT —
  "a plan-thread handoff is the durable record of a planning
  thread and an uncommitted one is frequently the ONLY copy, so
  a discard suggestion against it risks destroying the very
  artifact the finding exists to protect."

  The `plan/` scope was added by spec v170, after a session's
  first `check-doctor-static` run reported `pass` while the very
  worktree it scanned held a plan handoff carrying 153
  unversioned lines.

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
  scope here. For `<spec-root>/` paths the existing
  `out-of-band-edits` check surfaces those via the
  snapshot-mismatch invariant. For `plan/` paths there is
  deliberately NO after-the-fact doctor surface, and none is
  needed: `out-of-band-edits` compares committed spec state
  against `history/vNNN/` snapshots, which capture only files
  under the spec root, so it is structurally incapable of seeing
  `plan/` — and a COMMITTED plan file is already durable in git,
  so the orphaned-uncommitted-file risk this invariant targets
  does not arise for it.

Skip conditions (Finding.status='skipped'):
  - `project_root` is not a git working tree (`is_git_repo`
    returns False), OR
  - any IO precondition lifts on the railway (lashed into a
    skipped finding so the orchestrator's stdout contract stays
    uniform).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import git as io_git
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-master-direct-uncommitted-spec-edits")

# The `plan/` path prefix is project-root-relative by contract, exactly as
# `<spec-root>/` is, and is resolved against each worktree's OWN root rather
# than the invoking checkout's. It is a fixed convention rather than config:
# `plan/` is already first-class to the check suite (`check-plan-thread-anchor-
# declared`, `check-plan-thread-epic-parity`).
_PLAN_REL = Path("plan")


@dataclass(frozen=True, kw_only=True)
class Violation:
    """One default-branch worktree's uncommitted edits, split by path class.

    The two classes are carried SEPARATELY rather than merged into
    one path list because they are governed by different
    corrective-action rules — discard MAY be offered for
    `<spec-root>/` and MUST NOT be offered for `plan/` — so a
    merged list could not render the narration correctly.
    At least one of the two tuples is non-empty for any
    `Violation` that gets constructed.
    """

    worktree_path: Path
    spec_lines: tuple[str, ...]
    plan_lines: tuple[str, ...]


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


def _format_class_paths(*, label: str, status_lines: tuple[str, ...]) -> str:
    """Render one path class's modified files as `<label>: a, b, c`."""
    paths = sorted(_extract_status_path(status_line=line) for line in status_lines)
    return f"{label}: {', '.join(paths)}"


def _format_worktree_violation(*, violation: Violation) -> str:
    """Render one worktree's violation summary for the warn message.

    Lists the worktree path followed by each modified file path,
    grouped under its path class (`spec:` / `plan:`) so the reader
    can tell which corrective action applies to which file — the
    two classes are governed by DIFFERENT narration rules (see
    `_corrective_action`), so an unlabelled flat list would leave
    the discard offer ambiguous about which files it covers.
    A class contributes nothing when it has no modified files.
    """
    parts = [
        _format_class_paths(label=label, status_lines=lines)
        for label, lines in (("spec", violation.spec_lines), ("plan", violation.plan_lines))
        if lines
    ]
    return f"{violation.worktree_path}: {'; '.join(parts)}"


def _corrective_action(*, violations: tuple[Violation, ...]) -> str:
    """Build the corrective-action narration, asymmetric by path class.

    Per `SPECIFICATION/contracts.md`
    §`master-direct-uncommitted-spec-edits` item 3: the commit
    path is always offered; the discard option MAY be offered for
    `<spec-root>/` paths but MUST NOT be offered for `plan/`
    paths, because a plan-thread handoff is the durable record of
    a planning thread and an uncommitted one is frequently the
    ONLY copy — a discard suggestion against it risks destroying
    the very artifact the finding exists to protect.

    So the discard clause is emitted only when a `<spec-root>/`
    path is actually implicated, and is explicitly SCOPED to that
    class rather than left bare; and whenever a `plan/` path is
    implicated the narration carries the explicit prohibition, so
    a reader holding both classes at once cannot read the discard
    offer as covering the handoff.
    """
    has_spec = any(v.spec_lines for v in violations)
    has_plan = any(v.plan_lines for v in violations)
    action = "Corrective action: move the edits to a feature branch and commit them there."
    if has_spec:
        action += (
            " Unintentional `<spec-root>/` edits MAY instead be discarded "
            "(`git checkout -- <files>`)."
        )
    if has_plan:
        action += (
            " NEVER discard `plan/` edits: an uncommitted handoff is frequently "
            "the only copy of a planning thread."
        )
    return action


def _evaluate(
    *,
    ctx: DoctorContext,
    default_branch: str,
    violations: tuple[Violation, ...],
    worktrees_on_default_count: int,
) -> Finding:
    """Build the pass-or-warn Finding from the per-worktree status results.

    `violations` holds one entry per worktree on the default
    branch whose `git status --porcelain` produced at least one
    line under `<spec-root>/` or under `plan/`. An empty
    `violations` tuple yields a pass.
    """
    if not violations:
        return _pass(
            ctx=ctx,
            message=(
                f"master-direct-uncommitted-spec-edits: no worktrees on "
                f"`{default_branch}` carry uncommitted spec-tree or `plan/` edits "
                f"({worktrees_on_default_count} worktree(s) on `{default_branch}` "
                f"scanned)"
            ),
        )
    summaries = "; ".join(
        _format_worktree_violation(violation=violation) for violation in violations
    )
    return _warn(
        ctx=ctx,
        message=(
            f"master-direct-uncommitted-spec-edits: "
            f"{len(violations)} worktree(s) on `{default_branch}` carry "
            f"uncommitted spec-tree or `plan/` edits: {summaries}. "
            f"{_corrective_action(violations=violations)}"
        ),
    )


def _collect_violation(
    *,
    worktree_path: Path,
    spec_rel: Path,
) -> IOResult[Violation | None, LivespecError]:
    """Run `git status --porcelain` for both path classes and lift the result.

    Returns IOSuccess(None) when BOTH classes produce zero
    porcelain lines (no violation for this worktree), else
    IOSuccess(Violation) carrying each class's lines separately.

    Both pathspecs resolve against `worktree_path` — not against
    the invoking checkout — so the check works uniformly for
    primary and secondary worktrees; the `-C` flag pins git to the
    worktree. A worktree with no `plan/` directory is not a
    special case: `git status --porcelain -- plan/` exits 0 with
    empty output when the pathspec matches nothing.
    """
    return io_git.list_status_porcelain(
        project_root=worktree_path,
        pathspec=spec_rel,
    ).bind(
        lambda spec_lines: io_git.list_status_porcelain(
            project_root=worktree_path,
            pathspec=_PLAN_REL,
        ).map(
            lambda plan_lines: (
                Violation(
                    worktree_path=worktree_path,
                    spec_lines=spec_lines,
                    plan_lines=plan_lines,
                )
                if (spec_lines or plan_lines)
                else None
            ),
        ),
    )


def _collect_all_violations(
    *,
    worktrees_on_default: tuple[io_git.Worktree, ...],
    spec_rel: Path,
    accumulated: tuple[Violation, ...] = (),
) -> IOResult[tuple[Violation, ...], LivespecError]:
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
        worktree_path=head.path,
        spec_rel=spec_rel,
    ).bind(
        lambda result: _collect_all_violations(
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
