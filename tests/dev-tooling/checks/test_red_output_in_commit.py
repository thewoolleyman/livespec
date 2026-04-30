"""Outside-in test for `dev-tooling/checks/red_output_in_commit.py`.

Per Plan lines 1708-1712 (v032 D4):

    walks `git log --grep` against the v032-redo commit range
    and rejects any feature/bugfix commit lacking a `## Red
    output` fenced block in its body; activates as a hard
    `just check` gate at Phase 5 exit, **informational
    pre-Phase-5-exit**.

Phase 4 = pre-Phase-5-exit, so the check operates in
**informational mode**: it logs warnings for non-conforming
commits but always exits 0. The Phase 5 exit-criterion flips
this to hard-fail mode.

Cycle 56 pins the canonical violation pattern AND the
informational-mode exit-code semantics. The fixture creates a
disposable git repo with one redo-format commit lacking
`## Red output`; the test asserts that the warning surfaces
in stderr but exit code is 0 (Phase 4 informational mode).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_RED_OUTPUT_IN_COMMIT = _REPO_ROOT / "dev-tooling" / "checks" / "red_output_in_commit.py"


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


def test_red_output_in_commit_rejects_redo_commit_without_block_v033_hard_gate(
    *,
    tmp_path: Path,
) -> None:
    """A redo commit without `## Red output` exits non-zero (v033 D4 hard gate).

    Fixture: a fresh git repo with one redo-format commit
    (`phase-5: cycle 1 — foo`) whose body has NO `## Red
    output` block. Per v033 D4 the check is now a hard gate
    (the v032 D4 framing positioned the promotion at Phase-5-
    exit; v033 D5a moves the lefthook activation forward to
    v033-codification, which forces the hard-gate promotion to
    the same boundary). The check, run from this repo's cwd,
    must log an ERROR naming the offending sha and exit
    non-zero so lefthook rejects the commit.
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "file.txt"])
    _git(
        cwd=tmp_path,
        args=[
            "commit",
            "-m",
            "phase-5: cycle 1 — foo",
            "-m",
            "no red block in this body.",
        ],
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"red_output_in_commit v033 hard-gate mode must exit non-zero for missing block; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "Red output" in combined or "red_output" in combined, (
        f"red_output_in_commit must surface a diagnostic naming the missing `## Red output` block; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_output_in_commit_silent_when_block_present(*, tmp_path: Path) -> None:
    """A redo commit WITH a `## Red output` block produces no warning.

    Fixture: a fresh git repo with one redo-format commit whose
    body carries a `## Red output` heading. The check must walk
    the log, find the block, and emit no diagnostic for that
    commit. Exit 0 (Phase 4 informational mode and conformant
    commit both produce 0).
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "file.txt"])
    _git(
        cwd=tmp_path,
        args=[
            "commit",
            "-m",
            "phase-5: cycle 1 — foo",
            "-m",
            "Body prose.\n\n## Red output\n\n```\npytest red text\n```\n",
        ],
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_output_in_commit must exit 0 for conformant commit; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "missing `## Red output`" not in combined, (
        f"red_output_in_commit must not emit missing-block warning for conformant commit; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_output_in_commit_returns_empty_when_git_log_fails(*, tmp_path: Path) -> None:
    """A `git log` failure (e.g., not-a-git-repo cwd) returns an empty commit list.

    Per `_collect_redo_commits` line 58-59 guard: if the
    `git log` subprocess exits non-zero, the helper returns an
    empty list. The supervisor's loop then iterates zero commits,
    no offenders accumulate, and main() returns 0. Tested by
    invoking the check in a tmp_path that is NOT a git repo —
    git fails, the helper short-circuits to [], and the script
    exits 0 with no warnings.

    Drives line 59 (`return []` early-out) and the resulting
    no-offenders zero-exit path.
    """
    # tmp_path is a fresh tempdir, not a git repo. `git log` will
    # fail with "not a git repository" (returncode 128).
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_output_in_commit should exit 0 when git log fails (no commits to check); "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_output_in_commit_skips_non_redo_format_commits(*, tmp_path: Path) -> None:
    """A commit whose subject doesn't match the redo pattern is silently skipped.

    Per `_collect_redo_commits` line 73-74 guard: only commits
    whose first line matches `^phase-5: cycle <N> ` enter the
    offender-eligible set. Other commit subjects (`refactor: ...`,
    `chore: ...`, `phase-5: STATUS — ...`, etc.) are skipped
    without inspection.

    Fixture: a git repo with one non-redo-format commit (`chore:
    initial setup`). The check exits 0 because no commits are in
    scope. Drives line 74 (`continue` when subject doesn't match
    the redo pattern).
    """
    _git(cwd=tmp_path, args=["init", "-q"])
    _git(cwd=tmp_path, args=["config", "user.email", "test@example.com"])
    _git(cwd=tmp_path, args=["config", "user.name", "Test"])
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")
    _git(cwd=tmp_path, args=["add", "file.txt"])
    _git(
        cwd=tmp_path,
        args=["commit", "-m", "chore: initial setup", "-m", "no red block needed."],
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_RED_OUTPUT_IN_COMMIT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"red_output_in_commit must exit 0 for non-redo commits (out of scope); "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_red_output_in_commit_skips_chunks_with_empty_sha_or_message() -> None:
    """A chunk in the parsed git-log stream missing sha or body is silently skipped.

    Per `_collect_redo_commits` line 70-71 guard: the chunk-split
    on the `END_OF_COMMIT` sentinel can produce an entry whose
    sha or message is empty (e.g., a trailing chunk after the
    last sentinel). The guard skips those rather than reading
    `message.splitlines()[0]` on empty input. Tested by calling
    `_collect_redo_commits` (the module-private helper) directly
    via importlib — but this is awkward; instead we exercise it
    indirectly by seeding the `git log --format=...` output to
    contain an empty chunk via a no-op-only repo (one commit; the
    output's trailing-chunk artifact triggers the guard).

    Fixture: a fresh git repo with NO commits at all. `git log`
    exits non-zero (no commits) → returns [], then the helper's
    main path covers nothing further. Wait — that exercises the
    git-failure path, not the empty-sha guard. Drive line 71 by
    importing the module and calling the parser with hand-built
    output.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "red_output_in_commit_for_parser_test", str(_RED_OUTPUT_IN_COMMIT),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Patch subprocess.run to return controlled stdout that includes
    # a chunk whose body is empty after stripping (only the sentinel
    # remains). The split-on-sentinel produces an empty chunk; the
    # guard at line 70-71 skips it.
    import subprocess as _subprocess
    from typing import Any

    original_run = _subprocess.run

    def fake_run(*_args: Any, **_kwargs: Any) -> _subprocess.CompletedProcess[str]:
        # Three chunks. Chunk 1 has only-whitespace sha (one space)
        # -> body non-empty (just " "), partition produces ("", "", "")
        # because there's no \x00 in body; sha.strip() = "" and
        # message.strip() = "" — hits line 71's
        # `if not sha or not message: continue`. Chunk 2 is a
        # well-formed non-redo commit (filtered by line 74's
        # continue). Chunk 3 is empty (filtered by line 65's
        # `if not body: continue`). Coverage records line 71.
        stdout = (
            "  \x00END_OF_COMMIT\x00"
            "abc123\x00chore: setup\x00END_OF_COMMIT\x00"
            "\x00END_OF_COMMIT\x00"
        )
        return _subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")

    _subprocess.run = fake_run  # noqa: SLF001 — module-level patch for the test
    try:
        commits = module._collect_redo_commits(cwd=Path("/tmp"))
    finally:
        _subprocess.run = original_run
    # The non-redo commit (chore: setup) is filtered by line 74; the
    # empty-sha chunk is filtered by line 71. Result is empty.
    assert commits == [], f"expected no qualifying commits, got {commits!r}"


def test_red_output_in_commit_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Closes branches 35->38 (vendor-dir already in sys.path) and
    104->exit (__main__-else: imported, not run as a script).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "red_output_in_commit_for_import_test", str(_RED_OUTPUT_IN_COMMIT),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
