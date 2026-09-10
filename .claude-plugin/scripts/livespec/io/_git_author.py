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
"""Git author-identity readers, re-exported through `io.git`.

Extracted from `io/git.py` to keep that file under the per-file
LLOC ceiling; the public seam stays `io.git.<name>` for every
consumer. Everything answering "who authored this" lives here
together — that cohesion, not the line count, is the seam — and
the distinction between the two low-level readers is the whole
point of the operator-author contract in
`SPECIFICATION/non-functional-requirements.md`:

- `get_effective_author` reads `git var GIT_AUTHOR_IDENT`, which
  is the identity Git will ACTUALLY write for a commit made now.
  Git resolves it from `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL`
  first, then repository, worktree, and global configuration,
  honouring `user.useConfigOnly`. Reading `git config user.email`
  cannot see the environment overrides, so a metadata surface
  built on the config read alone can record a canonical identity
  while the commit beside it carries a different one.
- `list_commit_authors` reads the authors of already-created
  commits over a revision range. That covers every creation path a
  pre-commit hook cannot observe — amend, rebase, cherry-pick,
  `--author`, and `commit-tree` — because whatever produced the
  object, the object records what it recorded.

`get_git_user` sits on top of the first reader: it is the
revision-metadata capture, and it refuses rather than record an
author the accompanying commit will not carry.

Each commit's full message travels with its identity because the
preserved-third-party-author declaration is a commit trailer; the
classifier needs both halves to decide whether a non-operator
author was declared.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess
from livespec.parse.git_author import GitIdentity, format_identity, parse_author_ident

__all__: list[str] = [
    "CommitAuthor",
    "get_effective_author",
    "get_git_user",
    "list_commit_authors",
]


# Field and record separators for the `git log --format` payload.
# ASCII unit/record separators cannot occur in a commit message, an
# author name, or an email, so a message containing newlines, tabs,
# or any punctuation still round-trips unambiguously.
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"

_LOG_FORMAT = f"%H{_FIELD_SEP}%an{_FIELD_SEP}%ae{_FIELD_SEP}%B{_RECORD_SEP}"


@dataclass(frozen=True, kw_only=True, slots=True)
class CommitAuthor:
    """One commit's object id, author identity, and full message."""

    sha: str
    identity: GitIdentity
    message: str


def get_effective_author(*, project_root: Path) -> IOResult[GitIdentity, LivespecError]:
    """Return the author identity Git would write for a commit made now.

    Composes `git -C <project_root> var GIT_AUTHOR_IDENT` and parses
    the resulting `Name <email> <unix-seconds> <tz>` ident line.

    Failure modes lifted to IOFailure(PreconditionError):
      - Git cannot resolve an identity at all (no configured
        `user.name`/`user.email` and no environment override, with
        `user.useConfigOnly` set): `git var` exits non-zero. This is
        the fail-closed case the contract requires — an absent
        identity MUST NOT resolve to a host-invented fallback.
      - The ident line does not parse (a shape this reader does not
        understand MUST NOT resolve to an identity it then compares).
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=["git", "-C", str(project_root), "var", "GIT_AUTHOR_IDENT"],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_result(parse_author_ident(raw=completed.stdout)).alt(
                lambda err: PreconditionError(f"git.get_effective_author: {err}"),
            )
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.get_effective_author: `git var GIT_AUTHOR_IDENT` exited "
                    f"{completed.returncode}; git cannot resolve an author identity "
                    f"({completed.stderr.strip()})",
                ),
            )
        ),
    )


def _parse_log_records(*, stdout: str) -> IOResult[tuple[CommitAuthor, ...], LivespecError]:
    """Split the `git log` payload into one CommitAuthor per record.

    Each record is `<sha> US <name> US <email> US <message> RS`.
    The trailing record separator leaves an empty final fragment,
    and a range containing no commits produces empty stdout; both
    yield an empty tuple rather than a malformed entry.
    """
    commits: list[CommitAuthor] = []
    for record in stdout.split(_RECORD_SEP):
        stripped = record.strip("\n")
        if not stripped:
            continue
        sha, name, email, message = stripped.split(_FIELD_SEP, maxsplit=3)
        commits.append(
            CommitAuthor(
                sha=sha,
                identity=GitIdentity(name=name, email=email),
                message=message,
            ),
        )
    return IOResult.from_value(tuple(commits))


def list_commit_authors(
    *,
    project_root: Path,
    rev_range: str,
) -> IOResult[tuple[CommitAuthor, ...], LivespecError]:
    """Return the author identity and message of every commit in `rev_range`.

    `rev_range` is any revision range `git log` accepts — the
    publication-time caller passes `<upstream>..HEAD` so the scan
    covers exactly the commits a push would introduce. A range
    that selects no commits yields an empty tuple on the IOSuccess
    track: an empty newly-introduced set is a real answer, not a
    precondition failure.

    Failure modes lifted to IOFailure(PreconditionError):
      - The range does not resolve (an unknown ref; a repository
        with no HEAD yet): `git log` exits non-zero.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "log",
            f"--format={_LOG_FORMAT}",
            rev_range,
        ],
    ).bind(
        lambda completed: (
            _parse_log_records(stdout=completed.stdout)
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_commit_authors: `git log {rev_range}` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )


def _read_configured_author() -> IOResult[GitIdentity, LivespecError]:
    """Read `git config user.name` + `user.email` as one identity.

    This is the CONFIGURED pair only. It is deliberately NOT the
    identity a commit would carry: an environment override wins
    over configuration, and this read cannot see one. It exists so
    `get_git_user` can compare the two and refuse to record
    metadata that disagrees with the commit beside it.

    An unset or empty value is emitted as-is (the empty string),
    so a half-configured repository surfaces as a disagreement
    against the effective identity rather than as a silent pass.
    """
    return run_subprocess(argv=["git", "config", "--get", "user.name"]).bind(
        lambda name_completed: run_subprocess(
            argv=["git", "config", "--get", "user.email"],
        ).map(
            lambda email_completed: GitIdentity(
                name=name_completed.stdout.strip(),
                email=email_completed.stdout.strip(),
            ),
        ),
    )


def get_git_user() -> IOResult[str, LivespecError]:
    """Return the author identity revision metadata MUST record.

    Returns IOSuccess(`"Name <email>"`) — the conventional Git
    author format the revision front-matter `author_human` field
    carries — resolved by the SAME effective-identity rule the Git
    commit path uses, per
    `SPECIFICATION/non-functional-requirements.md`.

    The resolution reads `git var GIT_AUTHOR_IDENT` (which folds in
    `GIT_AUTHOR_*`, repository/worktree configuration, and
    `user.useConfigOnly`) and compares it against the configured
    `user.name`/`user.email` pair. When the two DISAGREE the read
    fails with `PreconditionError` naming both pairs, rather than
    recording the configured identity while the commit that carries
    the revision file records the overridden one. That divergence is
    invisible to a config-only read, and a revision file attributing
    work to someone the commit does not is exactly the attribution
    defect the operator-author contract closes.

    Scoped to the surrounding repository (`git -C .`), so a caller
    isolates it by chdir as before.
    """
    here = Path()
    return get_effective_author(
        project_root=here
    ).bind(
        lambda effective: _read_configured_author().bind(
            lambda configured: (  # pyright: ignore[reportArgumentType]
                IOResult.from_value(format_identity(identity=effective))
                if configured == effective
                else IOResult.from_failure(
                    PreconditionError(
                        f"git.get_git_user: the identity git will write "
                        f"({format_identity(identity=effective)}) disagrees with the "
                        f"configured identity ({format_identity(identity=configured)}); "
                        f"revision metadata MUST NOT record an author the commit will "
                        f"not carry — clear the GIT_AUTHOR_NAME/GIT_AUTHOR_EMAIL "
                        f"override or correct `git config user.name`/`user.email`",
                    ),
                )
            ),
        ),
    )
