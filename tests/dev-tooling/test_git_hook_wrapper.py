"""Outside-in test for `dev-tooling/git-hook-wrapper.sh` — v033 D5a Option-3 hook wrapper.

The lefthook-generated pre-commit hook tries to find `lefthook` on
PATH or in node_modules, neither of which works for livespec's
mise-pinned setup unless mise activation has fired in the current
shell. Zsh sessions without a `~/.zshrc` mise-activate line (e.g.,
Claude Code's default Bash tool which uses zsh) silently no-op the
hook with "Can't find lefthook in PATH". v033 D5a Option-3
addresses the gap by shipping a small repo-tracked wrapper that
`just bootstrap` installs as `.git/hooks/{pre-commit,pre-push}`
in place of the vanilla lefthook-generated scripts.

The wrapper's behavioral contract:

- Determines the hook name from `basename "$0"` so a single
  wrapper file serves both `pre-commit` and `pre-push` (and
  any future hook) — `just bootstrap` copies the same script
  to multiple hook paths.
- Invokes `mise exec lefthook -- lefthook run <hook-name>
  <args>` so lefthook is reached via mise's pinned-version
  resolution regardless of the user's shell config or PATH.
- Forwards `$@` (the args git passes to the hook, typically
  empty for pre-commit but populated for pre-push) verbatim.

Cycle 61 pins the dispatch contract: when the wrapper is
invoked under the name `pre-commit` with two trailing
arguments, it must `exec` `mise` with the canonical argv
`["mise", "exec", "lefthook", "--", "lefthook", "run",
"pre-commit", <arg1>, <arg2>]`.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_GIT_HOOK_WRAPPER = _REPO_ROOT / "dev-tooling" / "git-hook-wrapper.sh"


def test_git_hook_wrapper_dispatches_to_mise_with_basename_hook_name(*, tmp_path: Path) -> None:
    """Wrapper invoked as `pre-commit` forwards to `mise exec lefthook -- lefthook run pre-commit <args>`.

    The fixture sets up a synthetic PATH with a fake `mise`
    binary that records its full argv to a log file, then
    invokes `./pre-commit foo bar` (the wrapper renamed to
    `pre-commit` so the basename detection fires). The
    recorded argv must match the canonical dispatch:
    `mise exec lefthook -- lefthook run pre-commit foo bar`.
    Failure here means the wrapper isn't using basename to
    determine the hook name OR isn't passing args through
    correctly OR isn't invoking mise as the resolution
    mechanism.
    """
    fake_path_dir = tmp_path / "fake_path"
    fake_path_dir.mkdir()
    argv_log = tmp_path / "mise_argv.log"
    fake_mise = fake_path_dir / "mise"
    fake_mise.write_text(
        "#!/bin/sh\n" f'printf "%s\\n" "$@" > "{argv_log}"\n' "exit 0\n",
        encoding="utf-8",
    )
    fake_mise.chmod(fake_mise.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    pre_commit_path = tmp_path / "pre-commit"
    shutil.copy(_GIT_HOOK_WRAPPER, pre_commit_path)
    pre_commit_path.chmod(
        pre_commit_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )

    env = dict(os.environ)
    env["PATH"] = f"{fake_path_dir}{os.pathsep}{env.get('PATH', '')}"

    # S603: argv is a fixed list (literal wrapper path + literal
    # arg strings); no untrusted shell input.
    result = subprocess.run(
        [str(pre_commit_path), "foo", "bar"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, (
        f"git-hook-wrapper invocation failed; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert argv_log.is_file(), (
        f"fake mise was not invoked; argv log file does not exist; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    recorded_argv = argv_log.read_text(encoding="utf-8").splitlines()
    expected_argv = [
        "exec",
        "lefthook",
        "--",
        "lefthook",
        "run",
        "--no-auto-install",
        "pre-commit",
        "foo",
        "bar",
    ]
    assert recorded_argv == expected_argv, (
        f"git-hook-wrapper did not dispatch with canonical argv; "
        f"expected={expected_argv!r} got={recorded_argv!r}"
    )
