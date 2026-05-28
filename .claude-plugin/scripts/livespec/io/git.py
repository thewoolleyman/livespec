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
"""Git boundary facade.

Per style doc §"Skill layout — `io/`": the io/ layer is
the impure boundary; every operation that touches git lives here
under `@impure_safe` so the railway flows through `IOResult`.
The git facade exposes `get_git_user` returning the conventional
`"Name <email>"` author string from local git config, used by
`livespec.commands.revise.main` (and `seed.main`'s revision-auto-
capture path) to populate the revision-file `author_human`
front-matter field and `revision_front_matter.schema.json`.

lands the smallest viable surface: the happy path
where both `git config --get user.name` and
`git config --get user.email` return non-empty values. Subsequent
cycles widen the unset/missing-git fallbacks (the `"unknown"`
literal when git is available but either value is unset;
PreconditionError when the git binary itself is missing entirely)
under typed Failure carriers as consumer pressure forces them.

The composition mechanism is `livespec.io.proc.run_subprocess`
rather than a direct `subprocess.run` import: every git operation
flows through the typed subprocess seam at proc, keeping the
single OSError → PreconditionError mapping in one place per the
io/ layer's "exception-to-LivespecError mapping is the io/
boundary's responsibility" rule.

 sub-step 7.a.i adds `is_git_repo` + `show_at_head`. The
former composes on top of `run_subprocess` (text-mode capture is
fine — only the returncode matters). The latter needs binary
stdout capture (text mode would corrupt non-UTF-8 bytes), so it
uses a dedicated `@impure_safe` raw helper with
`subprocess.run(..., stdout=PIPE)` returning bytes.

 sub-step 7.a.iv (redo) adds `list_at_head`. It enumerates
immediate file basenames at HEAD under a given repo-relative
directory via `git ls-tree HEAD <dir>/`, parsing the canonical
`<mode> SP <type> SP <object-id> TAB <name>` shape and filtering
to type=blob entries. Empty subtree + missing subtree both return
IOSuccess(()) (git's ls-tree does not distinguish them); the
no-HEAD-yet case lifts to IOFailure via the same @impure_safe
exception widening as `_raw_show_at_head`.
"""

from __future__ import annotations

import subprocess  # subprocess is the documented io/ surface (style doc)
from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResult, impure_safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess


@dataclass(frozen=True, kw_only=True, slots=True)
class Worktree:
    """A single entry in `git worktree list --porcelain` output.

    `path` is the absolute worktree directory; `branch` is the
    short branch name (e.g., `master`) when the worktree is on a
    branch, or `None` when the worktree is in detached-HEAD
    state. The primary (main) worktree is the first entry in
    porcelain order; consumers MUST exclude it from cleanup
    enumeration via the `is_primary` flag.
    """

    path: Path
    branch: str | None
    is_primary: bool


__all__: list[str] = [
    "Worktree",
    "get_default_branch_name",
    "get_git_user",
    "is_git_repo",
    "list_at_head",
    "list_merged_branches",
    "list_status_porcelain",
    "list_worktrees",
    "show_at_head",
]


# Column index of the type field (`blob`, `tree`, `commit`) in the
# whitespace-split prefix of a `git ls-tree` line. Each line has the
# canonical shape `<mode> SP <type> SP <object-id> TAB <name>`; the
# prefix split yields three tokens with type at index 1.
_LS_TREE_TYPE_COLUMN_INDEX: int = 1


def get_git_user() -> IOResult[str, LivespecError]:
    """Read `git config user.name` + `user.email` and combine them.

    Returns IOSuccess(`"Name <email>"`) when both git config
    values are set and non-empty in the surrounding repository's
    local config. The composition: read user.name via the proc
    facade, bind the user.email read on top, map the two
    captured stdouts into the conventional Git author format.

    happy-path-only: when either git config value is
    unset (returncode != 0) or empty (whitespace-only stdout),
    the literal substring is emitted as-is. Later cycles widen
    this to the `"unknown"` fallback + the PreconditionError lift
    when the git binary is missing.
    """
    return run_subprocess(argv=["git", "config", "--get", "user.name"]).bind(
        lambda name_completed: run_subprocess(
            argv=["git", "config", "--get", "user.email"],
        ).map(
            lambda email_completed: (
                f"{name_completed.stdout.strip()} <{email_completed.stdout.strip()}>"
            ),
        ),
    )


def is_git_repo(*, project_root: Path) -> IOResult[bool, LivespecError]:
    """Return IOSuccess(True/False) for whether `project_root` is in a git tree.

    Composes on top of `run_subprocess` with
    `git -C <project_root> rev-parse --is-inside-work-tree`. The
    `-C` flag scopes the operation to `project_root` without
    requiring the caller (or the test) to chdir; the impure
    `run_subprocess` seam already handles OSError → PreconditionError
    if the `git` binary itself is missing.

    Returns IOSuccess(True) on returncode 0 (rev-parse succeeded;
    project_root is inside a working tree). Returns IOSuccess(False)
    on returncode != 0 (rev-parse exited `fatal: not a git
    repository`; project_root is NOT inside a working tree). The
    non-repo case is an EXPECTED business outcome — the doctor's
    out-of-band-edits static check folds it into "skip the
    out-of-band check, the project isn't versioned." The
    IOFailure track stays reserved for genuinely unexpected
    errors (e.g., the `git` binary itself missing entirely; that
    surfaces as PreconditionError via the proc seam).
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "rev-parse",
            "--is-inside-work-tree",
        ],
    ).map(lambda completed: completed.returncode == 0)


@impure_safe(exceptions=(OSError, subprocess.SubprocessError))
def _raw_show_at_head(*, project_root: Path, repo_relative_path: Path) -> bytes:
    """Decorator-lifted call into `git -C <project_root> show HEAD:<path>`.

    Binary stdout capture (no `text=True`, no `encoding=`) so the
    raw bytes round-trip byte-identically — the doctor's
    out-of-band-edits check byte-compares the HEAD blob against
    the working-tree blob, and a text-mode decode would corrupt
    embedded NULs and bytes outside UTF-8. Non-zero exit codes
    (path missing at HEAD; repo has no HEAD yet) raise
    `subprocess.CalledProcessError` via `check=True`; the
    decorator widens its caught-exception tuple to include
    `subprocess.SubprocessError` (CalledProcessError's parent)
    so the failure lifts to IOFailure rather than propagating
    as an unhandled exception. OSError (e.g., the `git` binary
    itself missing) lifts via the same decorator.
    """
    # S603/S607: argv is a fixed list of literals + caller-controlled paths;
    # `git` is the documented io/git boundary binary, mirrored from proc.py
    # which suppresses S603 for the same reason. capture_output=True with
    # text=None (default) returns bytes — the binary contract this seam pins.
    completed = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "-C",
            str(project_root),
            "show",
            f"HEAD:{repo_relative_path}",
        ],
        capture_output=True,
        check=True,
    )
    return completed.stdout


@impure_safe(exceptions=(OSError, subprocess.SubprocessError))
def _raw_list_at_head(
    *,
    project_root: Path,
    repo_relative_dir: Path,
) -> tuple[str, ...]:
    """Decorator-lifted call into `git -C <project_root> ls-tree HEAD <dir>/`.

    Captures stdout as text (the parsed output is mode + type +
    object-id + name on each line, all ASCII; text-mode is the
    appropriate decode here even though `show_at_head` uses
    binary mode for blob bodies). Filters lines whose type
    column is `blob` and returns only the basename column.
    Subtrees (type=tree) are excluded — the doctor's HEAD-active
    enumeration is files-only.

    Non-zero exit codes (repo has no HEAD yet) raise
    `subprocess.CalledProcessError` via `check=True`; the
    decorator widens its caught-exception tuple to include
    `subprocess.SubprocessError` (CalledProcessError's parent)
    so the failure lifts to IOFailure. OSError (e.g., the `git`
    binary itself missing) lifts via the same decorator.

    The trailing `/` on `<repo_relative_dir>` matches the
    `git ls-tree` "directory listing" syntax: without it the
    command treats the path as a single tree object reference
    rather than enumerating immediate children. A missing-at-HEAD
    directory yields exit 0 with empty stdout (NOT a failure);
    the empty-result and missing-result cases are
    indistinguishable by ls-tree and both surface as
    IOSuccess(()) at the public seam.
    """
    # S603/S607: argv is a fixed list of literals + caller-controlled paths;
    # `git` is the documented io/git boundary binary, mirrored from
    # `_raw_show_at_head`.
    completed = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "-C",
            str(project_root),
            "ls-tree",
            "HEAD",
            f"{repo_relative_dir}/",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    names: list[str] = []
    for line in completed.stdout.splitlines():
        # Each ls-tree line has the canonical shape:
        #   <mode> SP <type> SP <object-id> TAB <name>
        # where <type> is one of `blob` / `tree` / `commit`. Split
        # on TAB once to isolate the name column; split the
        # prefix on whitespace to recover the type column. Filter
        # to blobs so subtrees are excluded. Git's output format
        # is stable across versions — a well-formed `ls-tree`
        # invocation always produces this shape — so the parse
        # is straight-line (no defensive empty-line / short-prefix
        # branches; a malformed line would surface as an
        # IndexError bug rather than a domain error).
        prefix, _sep, raw_name = line.partition("\t")
        if prefix.split()[_LS_TREE_TYPE_COLUMN_INDEX] != "blob":
            continue
        # `git ls-tree HEAD <dir>/` returns the path-from-repo-
        # root in the name column (e.g. `SPECIFICATION/alpha.md`);
        # the basename is what callers need. Use `Path` to extract
        # the basename portably (handles trailing slashes and
        # nested-segment names uniformly across platforms).
        names.append(Path(raw_name).name)
    return tuple(names)


def list_at_head(
    *,
    project_root: Path,
    repo_relative_dir: Path,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return the immediate file basenames at HEAD under `repo_relative_dir`.

    The doctor's out-of-band-edits check uses this primitive to
    iterate over HEAD-committed spec files for the
    active-vs-history-vN comparison. Subtrees and
    files nested inside subtrees are excluded — the comparison
    is a top-level-files question.

    Failure modes lifted to IOFailure(PreconditionError):
      - Repo has no HEAD yet (zero commits since `git init`):
        `git ls-tree HEAD <dir>/` exits non-zero
        (CalledProcessError → PreconditionError).
      - The `git` binary itself missing: `OSError` →
        PreconditionError via `@impure_safe`.

    Empty-result cases (both stay on the IOSuccess track with
    an empty tuple — `git ls-tree` does not distinguish these
    two shapes):
      - Dir at HEAD with only subdir children (no immediate
        file children).
      - Dir not at HEAD at all (never added to any commit).
        `git ls-tree HEAD <dir>/` exits 0 with empty stdout
        for an unknown subtree path. The doctor folds this
        into "no files at HEAD under spec_root" — the
        comparison is a no-op when no HEAD baseline exists.
    """
    return _raw_list_at_head(
        project_root=project_root,
        repo_relative_dir=repo_relative_dir,
    ).alt(
        lambda exc: PreconditionError(f"git.list_at_head: {exc}"),
    )


_ORIGIN_PREFIX: str = "origin/"


def get_default_branch_name(*, project_root: Path) -> IOResult[str, LivespecError]:
    """Return the repo's default branch name (e.g., `master` or `main`).

    Reads `git symbolic-ref --short refs/remotes/origin/HEAD`,
    which returns `origin/<default>` when the remote's HEAD has
    been recorded locally (the canonical case for clones). The
    `origin/` prefix is stripped before returning. Returns the
    stripped name on the IOSuccess track.

    Failure modes lifted to IOFailure(PreconditionError):
      - `origin/HEAD` is not set locally (returncode != 0). This
        happens on bare-init repos with no remote, or on clones
        that never set the symbolic-ref. The doctor's
        no-stale-merged-branch check folds this into a `skipped`
        finding rather than treating it as an invariant violation.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "symbolic-ref",
            "--short",
            "refs/remotes/origin/HEAD",
        ],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(completed.stdout.strip().removeprefix(_ORIGIN_PREFIX))
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.get_default_branch_name: "
                    f"`git symbolic-ref refs/remotes/origin/HEAD` exited "
                    f"{completed.returncode}; default branch undetermined",
                ),
            )
        ),
    )


def list_merged_branches(
    *,
    project_root: Path,
    into_ref: str,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return local branch names whose tips are reachable from `into_ref`.

    Composes `git -C <project_root> for-each-ref --format='%(refname:short)'
    --merged refs/heads/<into_ref> refs/heads`. The result is a
    tuple of local-branch short-names (one per line, in
    for-each-ref's lexicographic order); INCLUDES `into_ref`
    itself (a branch is trivially reachable from itself), so
    callers MUST filter it out before reporting cleanup
    candidates.

    Failure modes lifted to IOFailure(PreconditionError):
      - `into_ref` does not exist as a local branch (returncode
        != 0). The doctor's no-stale-merged-branch check folds
        this into a `skipped` finding.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "for-each-ref",
            "--format=%(refname:short)",
            "--merged",
            f"refs/heads/{into_ref}",
            "refs/heads",
        ],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(
                tuple(line for line in completed.stdout.splitlines() if line.strip()),
            )
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_merged_branches: "
                    f"`git for-each-ref --merged refs/heads/{into_ref}` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )


_REFS_HEADS_PREFIX: str = "refs/heads/"


def _parse_worktree_porcelain(*, text: str) -> tuple[Worktree, ...]:
    """Parse `git worktree list --porcelain` text into Worktree records.

    Porcelain format: records separated by blank lines; each
    record is a sequence of `<key> <value>` lines. The first
    record is the primary worktree (per `git-worktree(1)`); we
    set `is_primary=True` for it and `False` for the rest.
    Unrecognized record lines (`bare`, `detached`, `locked`,
    `prunable`, etc.) are tolerated — only `worktree` and
    `branch` lines influence the parsed value.
    """
    records: list[Worktree] = []
    current_path: Path | None = None
    current_branch: str | None = None
    blocks = text.split("\n\n")
    for index, block in enumerate(blocks):
        for line in block.splitlines():
            key, _sep, value = line.partition(" ")
            if key == "worktree":
                current_path = Path(value)
            elif key == "branch":
                current_branch = value.removeprefix(_REFS_HEADS_PREFIX)
        if current_path is not None:
            records.append(
                Worktree(
                    path=current_path,
                    branch=current_branch,
                    is_primary=(index == 0),
                ),
            )
        current_path = None
        current_branch = None
    return tuple(records)


def list_worktrees(
    *,
    project_root: Path,
) -> IOResult[tuple[Worktree, ...], LivespecError]:
    """Return the list of git worktrees attached to `project_root`'s repo.

    Composes `git -C <project_root> worktree list --porcelain`
    and parses the output into Worktree records. The first
    record is the primary worktree; subsequent records are
    secondary worktrees that the doctor's no-stale-worktree
    invariant considers for cleanup candidacy.

    Failure modes lifted to IOFailure(PreconditionError):
      - `git worktree list` exits non-zero (e.g., not a git
        working tree). The doctor folds this into a skipped
        finding.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    return run_subprocess(
        argv=[
            "git",
            "-C",
            str(project_root),
            "worktree",
            "list",
            "--porcelain",
        ],
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(_parse_worktree_porcelain(text=completed.stdout))
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_worktrees: "
                    f"`git worktree list --porcelain` exited "
                    f"{completed.returncode}",
                ),
            )
        ),
    )


def show_at_head(
    *,
    project_root: Path,
    repo_relative_path: Path,
) -> IOResult[bytes, LivespecError]:
    """Return raw bytes of `repo_relative_path` at HEAD on the IO track.

    `git show HEAD:<path>` requires `<path>` to be repo-root-
    relative; for livespec the project_root IS the repo root, so
    the caller passes the spec-file path relative to project_root.
    The bytes are returned raw — no decode, no normalization —
    so the doctor's out-of-band-edits check can byte-compare
    against the working tree without corrupting embedded NULs or
    non-UTF-8 content.

    Failure modes lifted to IOFailure(PreconditionError):
      - Path not at HEAD: `git show` exits 128 with
        `fatal: path 'X' does not exist in 'HEAD'`
        (CalledProcessError → PreconditionError).
      - Repo has no HEAD yet (zero commits since `git init`):
        `git show` exits 128 with
        `fatal: ambiguous argument 'HEAD'`
        (CalledProcessError → PreconditionError).
      - The `git` binary itself missing: `OSError` →
        PreconditionError via `@impure_safe` on
        `_raw_show_at_head`.

    The helper's `@impure_safe` widens its caught-exception
    tuple to include `subprocess.SubprocessError` (the parent of
    `CalledProcessError`) so the non-zero-exit failure lifts
    onto the IOFailure track rather than escaping as an
    unhandled exception.
    """
    return _raw_show_at_head(
        project_root=project_root,
        repo_relative_path=repo_relative_path,
    ).alt(
        lambda exc: PreconditionError(f"git.show_at_head: {exc}"),
    )


def list_status_porcelain(
    *,
    project_root: Path,
    pathspec: Path,
) -> IOResult[tuple[str, ...], LivespecError]:
    """Return `git status --porcelain` lines scoped to `pathspec`.

    Composes `git -C <project_root> status --porcelain -- <pathspec>`.
    Each line of the captured stdout (without trailing newline) is
    one tuple entry. Empty stdout yields an empty tuple. The
    porcelain v1 format is one line per modified/untracked entry,
    with a fixed 2-char status field, a space, and the path
    relative to the worktree root.

    The `--` separator is included so `pathspec` is unambiguously
    treated as a path even if it begins with a dash or matches a
    flag. The caller is responsible for ensuring `pathspec`
    resolves under the worktree at `project_root` (e.g., by
    relativizing the spec-root path against the worktree root
    before invocation).

    Failure modes lifted to IOFailure(PreconditionError):
      - `git status` exits non-zero (e.g., not a git working
        tree). The doctor's
        master-direct-uncommitted-spec-edits check folds this
        into a skipped finding via its `is_git_repo` gate.
      - The `git` binary itself missing: lifts via the proc seam.
    """
    argv = ["git", "-C", str(project_root), "status", "--porcelain", "--", str(pathspec)]
    return run_subprocess(
        argv=argv
    ).bind(
        lambda completed: (  # pyright: ignore[reportArgumentType]
            IOResult.from_value(tuple(line for line in completed.stdout.splitlines() if line))
            if completed.returncode == 0
            else IOResult.from_failure(
                PreconditionError(
                    f"git.list_status_porcelain: `git status --porcelain -- {pathspec}` "
                    f"exited {completed.returncode}",
                ),
            )
        ),
    )
