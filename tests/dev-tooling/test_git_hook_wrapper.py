"""Outside-in test for the impl-plugin template's `git-hook-wrapper.sh`.

The repo's OWN commit-refuse hook body is no longer a vendored file: it is
installed from-package by `just install-commit-refuse-hooks` (REUSING
`livespec_dev_tooling.install_commit_refuse_hooks.CANONICAL_HOOK_BODY`, the
SINGLE source), and that installer plus the body's runtime behavior — mise
dispatch, hook-name-from-basename, arg-forwarding, structural refuse,
worktree delegation, and the `livespec.sandboxExempt` exemption — are
covered in livespec-dev-tooling's `test_install_commit_refuse_hooks.py`
(which runs the actual installed body via `sh`). So the former
dev-tooling-copy dispatch test here is retired as redundant (convergence
zs22.7.9.1).

What REMAINS a vendored copy — until convergence slice zs22.7.9.3 deletes it
together with the template's bootstrap/install conversion + dev-tooling pin
bump — is the impl-plugin template's
`templates/impl-plugin/dev-tooling/git-hook-wrapper.sh`, copier-copied into
scaffolded repos. This test locks the load-bearing `unset GIT_DIR …`
ordering for that remaining template copy until then.

When git fires a commit hook inside a worktree it injects
`GIT_DIR=.git/worktrees/<name>` (plus `GIT_INDEX_FILE`, `GIT_WORK_TREE`,
`GIT_PREFIX`) into the hook environment. The wrapper delegates to `mise exec
lefthook -- lefthook run …`; lefthook run with `GIT_DIR` pointing at a
worktree gitdir misreads the repo as bare and writes `core.bare=true` into
the shared `.git/config`, corrupting every checkout that shares it (root
cause li-iroguc). The fix unsets those vars on their own line immediately
BEFORE the `lefthook run` exec, so lefthook detects the repo from cwd.
"""

from __future__ import annotations

from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_GIT_HOOK_WRAPPER = (
    _REPO_ROOT / "templates" / "impl-plugin" / "dev-tooling" / "git-hook-wrapper.sh"
)


@pytest.mark.parametrize("wrapper_path", [_TEMPLATE_GIT_HOOK_WRAPPER], ids=["template"])
def test_git_hook_wrapper_unsets_git_dir_env_before_lefthook(*, wrapper_path: Path) -> None:
    """Template wrapper clears git-injected GIT_DIR env before invoking lefthook (core.bare-flip fix).

    The wrapper MUST carry the `unset GIT_DIR GIT_INDEX_FILE
    GIT_WORK_TREE GIT_PREFIX` line, and it MUST appear BEFORE the
    `lefthook run` exec. Failure here means the template wrapper lost the
    unset (regressing the core.bare flip) or moved it after the exec.
    """
    text = wrapper_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    unset_line_indices = [
        i
        for i, line in enumerate(lines)
        if line.strip() == "unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX"
    ]
    assert unset_line_indices, (
        f"{wrapper_path} is missing the "
        f"'unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX' line; "
        f"without it lefthook (run with the git-injected GIT_DIR) writes "
        f"core.bare=true to the shared config (li-iroguc)."
    )

    lefthook_exec_indices = [
        i for i, line in enumerate(lines) if "lefthook run --no-auto-install" in line
    ]
    assert lefthook_exec_indices, (
        f"{wrapper_path} is missing the 'lefthook run --no-auto-install' exec line; "
        f"the wrapper's dispatch contract is broken."
    )

    assert min(unset_line_indices) < min(lefthook_exec_indices), (
        f"{wrapper_path} has the unset line AFTER the 'lefthook run' exec line; "
        f"it must come BEFORE so the env is cleared before lefthook resolves the repo. "
        f"unset at line {min(unset_line_indices) + 1}, "
        f"lefthook exec at line {min(lefthook_exec_indices) + 1}."
    )
