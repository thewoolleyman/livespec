"""Outside-in test for `dev-tooling/checks/commit_pairs_source_and_test.py` — v033 D3 commit-pair gate.

Per the v033 D3 revision file at `brainstorming/approach-2-nlspec-
based/history/v033/proposed_changes/critique-fix-v032-revision.md`,
every commit modifying any `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, or `<repo-root>/dev-tooling/
checks/**` source file MUST also modify a `tests/**` file in the
same commit. Lefthook pre-commit gate, NOT in `just check`
aggregate.

Pre-commit hooks run BEFORE the commit lands and inspect the
STAGED state. The check therefore reads `git diff --cached
--name-only` (or equivalent) to enumerate files staged for the
imminent commit, applies the source-file filter, and verifies
the test-file co-staging.

Cycle 1 pins the bare rejection: a synthetic git repo with a
staged `.claude-plugin/scripts/livespec/foo/bar.py` change but
NO staged `tests/**` change makes the check exit non-zero with
the offending source path surfaced. Subsequent cycles will
pin the carve-outs (refactor: prefix, ## Type: lines, config-
only filenames, deletion-only) and the accept case (source +
test co-staged).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMIT_PAIRS_SOURCE_AND_TEST = (
    _REPO_ROOT / "dev-tooling" / "checks" / "commit_pairs_source_and_test.py"
)


def _git(*, cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    # S603/S607: argv is a fixed list (literal git binary + repo-controlled
    # args); bare `git` is the canonical invocation per system PATH;
    # no untrusted shell input.
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        env={"HOME": str(cwd), "GIT_CONFIG_GLOBAL": "/dev/null", "PATH": "/usr/bin:/bin"},
    )


def test_commit_pairs_rejects_staged_source_without_staged_test(*, tmp_path: Path) -> None:
    """A staged `livespec/foo/bar.py` with no staged tests/ change fails the check.

    Fixture: a fresh git repo with one baseline commit (so HEAD
    exists). A `livespec/foo/bar.py` source file is created and
    staged for the next commit. NO `tests/**` file is staged.
    The check, invoked with `cwd=tmp_path`, inspects the staged
    state, detects a source-file change without a paired
    test-file change, exits non-zero, and surfaces the offending
    source path in its diagnostic.
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    # Baseline commit so HEAD exists.
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "README.md"])
    _git(cwd=tmp_path, args=["commit", "-m", "baseline"])

    # Stage a source file change without staging any tests.
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    source = package_dir / "bar.py"
    source.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", ".claude-plugin/scripts/livespec/foo/bar.py"])

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_COMMIT_PAIRS_SOURCE_AND_TEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"commit_pairs_source_and_test should reject staged source without staged test "
        f"with non-zero exit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_token = ".claude-plugin/scripts/livespec/foo/bar.py"
    assert expected_token in combined, (
        f"commit_pairs_source_and_test diagnostic does not surface offending source path "
        f"`{expected_token}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_commit_pairs_accepts_staged_source_with_staged_test(*, tmp_path: Path) -> None:
    """A staged source change paired with a staged tests/ change passes the check.

    Pass-case companion to the rejection test. Fixture: fresh git
    repo with one baseline commit. A source file under
    `.claude-plugin/scripts/livespec/foo/bar.py` AND a paired
    test under `tests/livespec/foo/test_bar.py` are co-staged. The
    check, invoked with `cwd=tmp_path`, inspects the staged state,
    finds both a source-tree file AND a tests/-tree file in the
    same commit, and exits 0 (success).

    Drives the success-path return on line 97 (`return 0`) and
    closes the load-bearing branch coverage gap: only the
    rejection arm has been exercised; the accept arm has been
    silently unreachable from the test suite.
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "README.md"])
    _git(cwd=tmp_path, args=["commit", "-m", "baseline"])

    # Stage source AND test together — the canonical Red→Green
    # pair pattern this gate is designed to enforce.
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    source = package_dir / "bar.py"
    source.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
        encoding="utf-8",
    )
    test_dir = tmp_path / "tests" / "livespec" / "foo"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_bar.py"
    test_file.write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_bar() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", ".claude-plugin/scripts/livespec/foo/bar.py"])
    _git(cwd=tmp_path, args=["add", "tests/livespec/foo/test_bar.py"])

    # S603: argv is a fixed list (sys.executable + repo-controlled script path).
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_COMMIT_PAIRS_SOURCE_AND_TEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"commit_pairs_source_and_test should accept staged source + paired test "
        f"with exit 0; got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
