"""Outside-in test for `dev-tooling/checks/commit_pairs_source_and_test.py` — commit-pair gate.

Every commit modifying any `.claude-plugin/scripts/livespec/**`,
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
    return subprocess.run(
        ["git", *args],
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
    result = subprocess.run(
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


def test_commit_pairs_skips_when_head_has_unpaired_red_trailers(
    *,
    tmp_path: Path,
) -> None:
    """A staged source-only commit with HEAD carrying unpaired Red trailers passes the check.

    Per v034 D2-D3 amend-pattern coexistence (cycle 2.7): when
    HEAD's commit message contains `TDD-Red-Test-File-Checksum:`
    WITHOUT `TDD-Green-Verified-At:`, the next operation is
    structurally guaranteed to be `git commit --amend` adding the
    impl. During that amend, `git diff --cached --name-only`
    shows only the impl (the Red commit's test is in HEAD,
    unchanged). The check skips itself; pairing is enforced by
    v034 D3's replay hook at the commit-msg stage.

    Fixture: fresh git repo with HEAD's commit message carrying a
    Red trailer (mocking the Red commit's state). A
    source file is staged WITHOUT a test file. The check, invoked
    with `cwd=tmp_path`, detects HEAD's amend-pending state and
    exits 0 (skip).
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    # Baseline + a Red commit (its message carries the Red trailer).
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "README.md"])
    _git(cwd=tmp_path, args=["commit", "-m", "baseline"])
    test_dir = tmp_path / "tests" / "livespec" / "foo"
    test_dir.mkdir(parents=True)
    (test_dir / "test_bar.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_bar() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", "tests/livespec/foo/test_bar.py"])
    red_commit_message = (
        "feat: foo bar\n\nRed commit body.\n\n"
        "TDD-Red-Test: tests/livespec/foo/test_bar.py\n"
        "TDD-Red-Test-File-Checksum: sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
    )
    _git(cwd=tmp_path, args=["commit", "-m", red_commit_message])

    # Now stage an impl file (the Green amend's content).
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    (package_dir / "bar.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", ".claude-plugin/scripts/livespec/foo/bar.py"])

    # S603: argv is a fixed list (sys.executable + repo-controlled script path).
    result = subprocess.run(
        [sys.executable, str(_COMMIT_PAIRS_SOURCE_AND_TEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"commit_pairs should skip when HEAD has unpaired Red trailers; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_commit_pairs_applies_when_head_has_paired_red_and_green_trailers(
    *,
    tmp_path: Path,
) -> None:
    """A staged source-only commit with HEAD carrying Red+Green trailers fails the check.

    After a Green amend lands, HEAD carries BOTH `TDD-Red-*` and
    `TDD-Green-*` trailers — the "complete" state. The next
    commit isn't an amend; it's a fresh top-of-branch commit. The
    check resumes normal enforcement: source-without-paired-test
    is rejected.
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "README.md"])
    _git(cwd=tmp_path, args=["commit", "-m", "baseline"])
    test_dir = tmp_path / "tests" / "livespec" / "foo"
    test_dir.mkdir(parents=True)
    (test_dir / "test_bar.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n"
        "def test_bar() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", "tests/livespec/foo/test_bar.py"])
    paired_commit_message = (
        "feat: foo bar\n\nRed+Green pair body.\n\n"
        "TDD-Red-Test: tests/livespec/foo/test_bar.py\n"
        "TDD-Red-Test-File-Checksum: sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
        "TDD-Green-Verified-At: 2026-05-02T00:00:00Z\n"
    )
    _git(cwd=tmp_path, args=["commit", "-m", paired_commit_message])

    # Now stage a source-only change for a NEW commit (not an amend).
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "foo"
    package_dir.mkdir(parents=True)
    (package_dir / "bar.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\nx = 0\n",
        encoding="utf-8",
    )
    _git(cwd=tmp_path, args=["add", ".claude-plugin/scripts/livespec/foo/bar.py"])

    # S603: argv is a fixed list (sys.executable + repo-controlled script path).
    result = subprocess.run(
        [sys.executable, str(_COMMIT_PAIRS_SOURCE_AND_TEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"commit_pairs should reject source-only when HEAD has paired Red+Green trailers; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_commit_pairs_skips_on_empty_repo_with_no_head() -> None:
    """On a fresh repo with zero commits, the head-message lookup falls back gracefully.

    Drives the `result.returncode != 0` early-return in
    `_head_has_unpaired_red_trailers`: `git log -1`
    exits non-zero on a repo with no commits, the function
    returns False (no Red trailers), and the check applies its
    normal source-vs-test enforcement.

    Fixture: fresh git repo with NO commits AND no staged files
    in the source/test trees. The check exits 0 (no source
    changes = passes the existing source-vs-test logic).
    """
    import tempfile

    with tempfile.TemporaryDirectory() as raw_dir:
        empty_repo = Path(raw_dir)
        _git(cwd=empty_repo, args=["init", "-q"])
        _git(cwd=empty_repo, args=["config", "user.email", "test@example.com"])
        _git(cwd=empty_repo, args=["config", "user.name", "Test"])
        # Stage a non-source file so `_staged_files` has something
        # to enumerate but the source-tree filter returns an empty
        # list (no rejection).
        (empty_repo / "README.md").write_text("seed\n", encoding="utf-8")
        _git(cwd=empty_repo, args=["add", "README.md"])

        # S603: argv is a fixed list (sys.executable + repo-controlled
        # script path); no untrusted shell input.
        result = subprocess.run(
            [sys.executable, str(_COMMIT_PAIRS_SOURCE_AND_TEST)],
            cwd=str(empty_repo),
            capture_output=True,
            text=True,
            check=False,
        )

    assert result.returncode == 0, (
        f"commit_pairs should accept empty repo with no source changes; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_commit_pairs_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes two branch-coverage gaps in
    `commit_pairs_source_and_test.py`:
      - 100->exit: when the module is imported (not run as
        `python3 dev-tooling/checks/commit_pairs_source_and_test.py`),
        `__name__` is the module-qualified path, NOT `"__main__"`,
        so the `raise SystemExit(main())` line is skipped — the
        else-arm of `if __name__ == "__main__":` is taken.
      - 42->45: the `if str(_VENDOR_DIR) not in sys.path:` guard
        is taken on second import (the test runner already added
        _VENDOR_DIR via pytest's pythonpath config), so the body
        (`sys.path.insert(...)`) is skipped — the
        already-present branch is exercised.

    Pins the invocation contract that this script is BOTH usable
    as a CLI (`python3 dev-tooling/checks/commit_pairs_source_and_test.py`)
    AND importable for testing without running its main(). Tests
    of the rejection / accept cases above invoke via subprocess to
    pin the CLI path; this test pins the import path.
    """
    import importlib.util

    module_path = (
        Path(__file__).resolve().parents[3]
        / "dev-tooling"
        / "checks"
        / "commit_pairs_source_and_test.py"
    )
    spec = importlib.util.spec_from_file_location(
        "commit_pairs_source_and_test_for_import_test",
        str(module_path),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"


def test_commit_pairs_accepts_staged_source_with_staged_test(*, tmp_path: Path) -> None:
    """A staged source change paired with a staged tests/ change passes the check.

    Pass-case companion to the rejection test. Fixture: fresh git
    repo with one baseline commit. A source file under
    `.claude-plugin/scripts/livespec/foo/bar.py` AND a paired
    test under `tests/livespec/foo/test_bar.py` are co-staged. The
    check, invoked with `cwd=tmp_path`, inspects the staged state,
    finds both a source-tree file AND a tests/-tree file in the
    same commit, and exits 0 (success).

    Drives the success-path return on (`return 0`) and
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
    result = subprocess.run(
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
