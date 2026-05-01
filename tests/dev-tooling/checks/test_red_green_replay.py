"""Outside-in test for `dev-tooling/checks/red_green_replay.py` — v034 D2-D3 replay-based TDD enforcement.

Per `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
§"Testing approach — Activation §v034 D2-D3 Red→Green replay
contract" and Plan §"Per-commit Red→Green replay discipline
(v034 D2-D3)", this hook gates `feat:`/`fix:` commits via the
amend pattern (Red-mode initial commit; Green-mode amend) and
exempts other Conventional Commit types (chore, docs, build,
ci, style, test, refactor, perf, revert).

Cycle 173 pins the first behavior: a `chore:` commit subject
is exempt from TDD enforcement; the hook reads the commit
message file (passed as argv[1] per the git commit-msg hook
contract) and exits 0 without running any test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_RED_GREEN_REPLAY = _REPO_ROOT / "dev-tooling" / "checks" / "red_green_replay.py"


def test_chore_commit_subject_exits_zero(*, tmp_path: Path) -> None:
    """A `chore:` commit subject is exempt from TDD enforcement; hook exits 0.

    Fixture: a tmp_path COMMIT_EDITMSG file containing
    `chore: codify v034`. The hook is invoked as a `commit-msg`
    git hook (the v034 D2-D3 design): argv[1] is the path to
    the commit message file. For non-`feat:`/`fix:` types the
    hook MUST exit 0 without running any test or computing any
    checksum.
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("chore: codify v034\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_green_replay should exit 0 for chore: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_feat_commit_subject_exits_nonzero(*, tmp_path: Path) -> None:
    """A `feat:` commit subject is NOT exempt; hook MUST exit non-zero.

    Fixture: a tmp_path COMMIT_EDITMSG file containing
    `feat: add new feature`. Per v034 D3, `feat:` and `fix:`
    types require Red→Green replay verification — Red mode
    (test staged + no impl + pytest fails) or Green mode
    (amend with impl + pytest passes). With nothing to verify
    (no git repo, no staged tree, no Red-trailer parent), the
    hook cannot complete verification and MUST reject the
    commit. This pins the type-discrimination contract:
    non-exempt subjects do not exit 0. Future cycles refine
    the rejection diagnostic + add the actual replay logic.
    """
    msg_path = tmp_path / "COMMIT_EDITMSG"
    msg_path.write_text("feat: add new feature\n", encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_GREEN_REPLAY), str(msg_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"red_green_replay should exit non-zero for feat: subject; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_green_replay_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Structural test mirroring the project convention (see e.g.
    `test_check_tools.py::test_check_tools_module_importable_without_running_main`):
    importing the module exercises the `if __name__ == "__main__":`
    False branch so per-file coverage hits 100% line+branch.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "red_green_replay_for_import_test", str(_RED_GREEN_REPLAY),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
