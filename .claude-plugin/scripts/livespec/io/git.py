"""Git boundary facade.

Per style doc §"Skill layout — `io/`": the io/ layer is
the impure boundary; every operation that touches git lives here
under `@impure_safe` so the railway flows through `IOResult`.
The git facade exposes `get_git_user` returning the conventional
`"Name <email>"` author string from local git config, used by
`livespec.commands.revise.main` (and `seed.main`'s revision-auto-
capture path) to populate the revision-file `author_human`
front-matter field per PROPOSAL.md §"Revision file format" and `revision_front_matter.schema.json`.

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
"""

from __future__ import annotations

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io.proc import run_subprocess

__all__: list[str] = ["get_git_user"]


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
    this to the `"unknown"` fallback per PROPOSAL.md §"Revision
    file format" + the PreconditionError lift
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
