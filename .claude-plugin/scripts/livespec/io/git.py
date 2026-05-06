"""Git boundary facade.

Per style doc §"Skill layout — `io/`": the io/ layer is
the impure boundary; every operation that touches git lives here
under `@impure_safe` so the railway flows through `IOResult`.
The git facade exposes `get_git_user` returning the conventional
`"Name <email>"` author string from local git config, used by
`livespec.commands.revise.main` (and `seed.main`'s revision-auto-
capture path) to populate the revision-file `author_human`
front-matter field and `revision_front_matter.schema.json`.

Cycle 5.c.1 lands the smallest viable surface: the happy path
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

Phase 7 sub-step 7.a.i adds `is_git_repo` + `show_at_head`. The
former composes on top of `run_subprocess` (text-mode capture is
fine — only the returncode matters). The latter needs binary
stdout capture (text mode would corrupt non-UTF-8 bytes), so it
uses a dedicated `@impure_safe` raw helper with
`subprocess.run(..., stdout=PIPE)` returning bytes.

Phase 7 sub-step 7.a.iv (redo) adds `list_at_head`. It enumerates
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
from pathlib import Path

from returns.io import IOResult, impure_safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io.proc import run_subprocess

__all__: list[str] = ["get_git_user", "is_git_repo", "list_at_head", "show_at_head"]


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

    Cycle 5.c.1 happy-path-only: when either git config value is
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
