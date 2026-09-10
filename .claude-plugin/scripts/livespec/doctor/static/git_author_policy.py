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
"""Static-phase doctor check: git-author-policy.

Per `SPECIFICATION/contracts.md` and
`SPECIFICATION/non-functional-requirements.md`: a project that
declares `git_author` in `.livespec.jsonc` MUST attribute every
operator-owned commit it introduces to the declared operator pair
byte-for-byte. The only permitted exceptions are a commit of
exclusively mechanical output authored by an exact declared
`mechanical_authors` pair, and a genuine third-party import that
declares itself preserved via the `Livespec-Preserved-Author`
trailer naming its own author.

The check inspects the commits this branch would INTRODUCE — the
range from the default branch's remote tip to HEAD — rather than
the pending-commit identity alone. That scope is what makes it
cover the creation paths a hook cannot observe: amend, Red→Green
replay, rebase, cherry-pick, an explicit `--author`, a stale
`GIT_AUTHOR_*` environment, and `commit-tree`. Whatever produced
the object, the object records the author it recorded, so reading
the objects catches every path uniformly and refuses publication
before the push. The pending-identity rule itself is shared with
the revision-metadata capture through
`livespec.parse.git_author`, so the two surfaces cannot diverge.

Status derivation:

- `skipped` when `.livespec.jsonc` is missing or unparseable
  (`livespec-jsonc-valid` owns that failure mode), when the project
  declares no `git_author` (it has not opted in, and core imposes
  no identity on it), when the project is not a git working tree,
  or when the default branch's remote tip cannot be resolved so
  there is no range to scan. Each skip names its reason.
- `fail` when the config does not validate — a malformed or
  incomplete `git_author` declaration cannot be enforced, and the
  contract requires that to fail rather than to silently disarm —
  or when any introduced commit's author is a conflict.
- `pass` otherwise, naming the range and the number of commits
  scanned, so an empty range reads as "nothing to introduce"
  rather than as an unqualified endorsement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Success

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.io import git as io_git
from livespec.parse import jsonc
from livespec.parse.git_author import (
    GitIdentity,
    classify_identity,
    format_identity,
    parse_preserved_author,
)
from livespec.schemas.dataclasses.finding import Finding
from livespec.schemas.dataclasses.livespec_config import GitAuthorPolicy
from livespec.types import CheckId, SpecRoot
from livespec.validate.livespec_config import validate_livespec_config

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-git-author-policy")

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "livespec_config.schema.json"


def _make_finding(*, ctx: DoctorContext, status: str, message: str) -> Finding:
    """Construct this check's Finding with the canonical payload shape."""
    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _load_jsonc(*, path: Path) -> IOResult[Any, LivespecError]:
    """Read + parse one JSONC file onto the IOResult track."""
    return fs.read_text(path=path).bind(
        lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
    )


def _declared_identities(
    *,
    policy: GitAuthorPolicy,
) -> tuple[GitIdentity, tuple[GitIdentity, ...]]:
    """Split the declaration into the operator pair and the mechanical set."""
    operator = GitIdentity(name=policy.operator_name, email=policy.operator_email)
    mechanical = tuple(
        GitIdentity(name=entry.name, email=entry.email) for entry in policy.mechanical_authors
    )
    return operator, mechanical


def _conflicts(
    *,
    commits: tuple[io_git.CommitAuthor, ...],
    policy: GitAuthorPolicy,
) -> tuple[str, ...]:
    """Return one diagnostic per commit whose author the policy rejects.

    A commit's own message supplies the preserved-third-party
    declaration, so each commit is classified against the policy
    plus its own trailer.
    """
    operator, mechanical = _declared_identities(policy=policy)
    offenders: list[str] = []
    for commit in commits:
        verdict = classify_identity(
            identity=commit.identity,
            operator=operator,
            mechanical=mechanical,
            preserved=parse_preserved_author(message=commit.message),
        )
        if verdict.classification == "conflict":
            offenders.append(
                f"{commit.sha} authored by {format_identity(identity=commit.identity)}"
            )
    return tuple(offenders)


def _evaluate_range(
    *,
    ctx: DoctorContext,
    policy: GitAuthorPolicy,
    rev_range: str,
    commits: tuple[io_git.CommitAuthor, ...],
) -> Finding:
    """Build the pass-or-fail Finding for one scanned range."""
    operator, _mechanical = _declared_identities(policy=policy)
    offenders = _conflicts(commits=commits, policy=policy)
    if not offenders:
        return _make_finding(
            ctx=ctx,
            status="pass",
            message=(
                f"git-author-policy: all {len(commits)} commit(s) introduced by "
                f"`{rev_range}` carry a declared author "
                f"(operator {format_identity(identity=operator)})"
            ),
        )
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"git-author-policy: {len(offenders)} commit(s) introduced by "
            f"`{rev_range}` carry an undeclared author: {'; '.join(offenders)}. "
            f"Corrective action: re-author them as "
            f"{format_identity(identity=operator)}, declare the pair under "
            f"`git_author.mechanical_authors` if the commit is exclusively "
            f"mechanical output, or add a `Livespec-Preserved-Author` trailer "
            f"naming that author if the commit is a genuine third-party import."
        ),
    )


def _scan_range(
    *,
    ctx: DoctorContext,
    policy: GitAuthorPolicy,
    rev_range: str,
) -> IOResult[Finding, LivespecError]:
    """Classify every commit `rev_range` selects."""
    return io_git.list_commit_authors(
        project_root=ctx.project_root,
        rev_range=rev_range,
    ).map(
        lambda commits: _evaluate_range(
            ctx=ctx,
            policy=policy,
            rev_range=rev_range,
            commits=commits,
        ),
    )


def _scan(*, ctx: DoctorContext, policy: GitAuthorPolicy) -> IOResult[Finding, LivespecError]:
    """Resolve the newly-introduced range and classify every commit in it.

    The range runs from the default branch's REMOTE tip to HEAD, so
    it holds exactly the commits a push would introduce. On the
    default branch itself the range is empty and the check passes
    with a zero count — a push that introduces no commit has nothing
    to refuse, and the message says so rather than reporting a bare
    pass.
    """
    return io_git.get_default_branch_name(project_root=ctx.project_root).bind(
        lambda default_branch: _scan_range(
            ctx=ctx,
            policy=policy,
            rev_range=f"origin/{default_branch}..HEAD",
        ),
    )


def _on_config(
    *,
    ctx: DoctorContext,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> IOResult[Finding, LivespecError]:
    """Validate the config, then scan when the project has opted in."""
    validation = validate_livespec_config(payload=payload, schema=schema)
    if not isinstance(validation, Success):
        return IOResult.from_value(
            _make_finding(
                ctx=ctx,
                status="fail",
                message=(
                    "git-author-policy: config does not validate against "
                    f"livespec_config.schema.json, so a `git_author` declaration "
                    f"cannot be read or enforced: {validation.failure()}"
                ),
            ),
        )
    policy = validation.unwrap().git_author
    if policy is None:
        return IOResult.from_value(
            _make_finding(
                ctx=ctx,
                status="skipped",
                message=(
                    "git-author-policy: `.livespec.jsonc` declares no `git_author`; "
                    "the project has not opted into operator-author enforcement"
                ),
            ),
        )
    return io_git.is_git_repo(project_root=ctx.project_root).bind(
        lambda is_repo: (
            _scan(ctx=ctx, policy=policy)
            if is_repo
            else IOResult.from_value(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        "git-author-policy: project_root is not a git working tree; "
                        "there are no commits to classify"
                    ),
                ),
            )
        ),
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the git-author-policy check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc` plus the packaged
    `livespec_config.schema.json`, then evaluates per the module
    docstring. A missing or unparseable config, and an unresolvable
    default-branch remote tip, both recover to a `skipped` Finding
    via `.lash` so the orchestrator's stdout contract stays uniform.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        _load_jsonc(path=config_path)
        .bind(
            lambda payload: _load_jsonc(path=_SCHEMA_PATH).bind(
                lambda schema: _on_config(ctx=ctx, payload=payload, schema=schema),
            ),
        )
        .lash(
            lambda err: IOSuccess(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        f"git-author-policy: precondition not met "
                        f"({err.__class__.__name__}); check skipped"
                    ),
                ),
            ),
        )
    )
