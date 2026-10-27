"""Regression coverage for the Red-mode pre-commit aggregate.

The Red commit may follow an earlier implementation commit on the same branch.
In that shape the no-argument incremental coverage target discovers the earlier
implementation change through ``origin/master...HEAD`` and would run the
intentionally failing staged test. This test uses a small Git repository and a
``just`` stand-in to assert that the Red branch skips that target before the
child aggregate runs, while the Green-amend branch retains its narrower skip.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(*, argv: list[str], cwd: Path, environ: dict[str, str] | None = None) -> None:
    """Run one fixed fixture command and require it to succeed."""
    result = subprocess.run(argv, cwd=cwd, env=environ, check=False, capture_output=True, text=True)
    assert result.returncode == 0, (
        "fixture command failed: "
        + repr(argv)
        + "\nstdout:\n"
        + result.stdout
        + "\nstderr:\n"
        + result.stderr
    )


def _write_fake_just(*, directory: Path) -> None:
    """Write the child aggregate stand-in that demands the required Red skip."""
    fake = directory / "just"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$1" == check && " $SKIP_TARGETS " == *" check-check-coverage-incremental "* ]]; then\n'
        "    exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)


def test_red_mode_skips_incremental_coverage_after_an_earlier_impl_change(
    *, tmp_path: Path
) -> None:
    """A staged failing test may Red-commit after an implementation branch change."""
    just = shutil.which("just")
    assert just is not None, "the test requires the repository's just executable"
    repository = tmp_path / "repository"
    repository.mkdir()
    _run(argv=["git", "init", "--initial-branch=master"], cwd=repository)
    _run(argv=["git", "config", "user.name", "Test User"], cwd=repository)
    _run(argv=["git", "config", "user.email", "test@example.invalid"], cwd=repository)
    (repository / "justfile").write_text(
        (_REPO_ROOT / "justfile").read_text(encoding="utf-8"), encoding="utf-8"
    )
    _run(argv=["git", "add", "justfile"], cwd=repository)
    _run(argv=["git", "commit", "-m", "initial"], cwd=repository)
    _run(argv=["git", "update-ref", "refs/remotes/origin/master", "HEAD"], cwd=repository)

    implementation = repository / ".claude-plugin/scripts/livespec/example.py"
    implementation.parent.mkdir(parents=True)
    implementation.write_text("VALUE = 1\n", encoding="utf-8")
    _run(argv=["git", "add", str(implementation.relative_to(repository))], cwd=repository)
    _run(argv=["git", "commit", "-m", "implementation"], cwd=repository)

    staged_test = repository / "tests/test_red_mode.py"
    staged_test.parent.mkdir()
    staged_test.write_text(
        "def test_intentionally_red() -> None:\n    assert False\n", encoding="utf-8"
    )
    _run(argv=["git", "add", str(staged_test.relative_to(repository))], cwd=repository)

    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    _write_fake_just(directory=bin_directory)
    environ = dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"])
    _run(argv=[just, "check-pre-commit"], cwd=repository, environ=environ)
