"""Regression coverage for the Red-mode pre-commit aggregate.

The Red commit may follow an earlier implementation commit on the same branch.
In that shape the no-argument incremental coverage target discovers the earlier
implementation change through ``origin/master...HEAD`` and would run the
intentionally failing staged test. This test uses a small Git repository and a
``just`` stand-in to assert that the Red branch skips that target before the
child aggregate runs, while the Green-amend branch retains its narrower skip.

The same fixture covers the staged-file pre-check at the head of the recipe:
it runs before the aggregate whenever Python files are staged, a refusal stops
the recipe before the aggregate starts, and a doc-only commit never runs it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRECHECK_MODULE = "livespec_dev_tooling.workflow_checks.staged_precheck"
_DELEGATE_MODULE = "livespec_dev_tooling.pre_commit_delegate"


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


def _write_recording_fakes(
    *, directory: Path, log: Path, uv_status: int, just_program: str
) -> None:
    """Write `uv` and `just` stand-ins that append their argv to one shared call log."""
    uv = directory / "uv"
    uv.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "uv $*" >> "{log}"\n'
        f'if [[ "$*" == "run python -m {_DELEGATE_MODULE} run" ]]; then\n'
        "    exit 75\n"
        "fi\n"
        f"exit {uv_status}\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)
    just = directory / "just"
    just.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "just $*" >> "{log}"\n'
        'if [[ "$1" == "check-pre-commit-local" ]]; then\n'
        f'    exec "{just_program}" "$@"\n'
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    just.chmod(0o755)


def _new_repository(*, tmp_path: Path) -> Path:
    """Create a scratch repository holding only this repository's justfile."""
    repository = tmp_path / "repository"
    repository.mkdir()
    _run(argv=["git", "init", "--initial-branch=master"], cwd=repository)
    _run(argv=["git", "config", "user.name", "Test User"], cwd=repository)
    _run(argv=["git", "config", "user.email", "test@example.invalid"], cwd=repository)
    (repository / "justfile").write_text(
        (_REPO_ROOT / "justfile").read_text(encoding="utf-8"), encoding="utf-8"
    )
    scripts = repository / "dev-tooling"
    scripts.mkdir()
    for name in ("check-pre-commit.sh", "check-pre-commit-gated-tree.sh"):
        shutil.copy(_REPO_ROOT / "dev-tooling" / name, scripts / name)
    _run(argv=["git", "add", "justfile"], cwd=repository)
    _run(argv=["git", "commit", "-m", "initial"], cwd=repository)
    _run(argv=["git", "update-ref", "refs/remotes/origin/master", "HEAD"], cwd=repository)
    return repository


def _check_pre_commit_calls(
    *, tmp_path: Path, staged_name: str, uv_status: int
) -> tuple[int, list[str]]:
    """Stage one file, run `just check-pre-commit`, and return its status and call log."""
    just = shutil.which("just")
    assert just is not None, "the test requires the repository's just executable"
    repository = _new_repository(tmp_path=tmp_path)
    staged = repository / staged_name
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text("VALUE = 1\n", encoding="utf-8")
    _run(argv=["git", "add", staged_name], cwd=repository)
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    log = tmp_path / "calls.log"
    log.write_text("", encoding="utf-8")
    _write_recording_fakes(
        directory=bin_directory,
        log=log,
        uv_status=uv_status,
        just_program=just,
    )
    environ = dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"])
    result = subprocess.run(
        [just, "check-pre-commit"],
        cwd=repository,
        env=environ,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, log.read_text(encoding="utf-8").splitlines()


def test_red_mode_skips_incremental_coverage_after_an_earlier_impl_change(
    *, tmp_path: Path
) -> None:
    """A staged failing test may Red-commit after an implementation branch change."""
    just = shutil.which("just")
    assert just is not None, "the test requires the repository's just executable"
    repository = _new_repository(tmp_path=tmp_path)

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
    fake_uv = bin_directory / "uv"
    fake_uv.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_uv.chmod(0o755)
    environ = dict(os.environ, PATH=str(bin_directory) + os.pathsep + os.environ["PATH"])
    _run(argv=[just, "check-pre-commit"], cwd=repository, environ=environ)


def test_staged_python_runs_the_precheck_before_the_aggregate(*, tmp_path: Path) -> None:
    """A staged `.py` file runs the staged-file pre-check ahead of the aggregate."""
    status, calls = _check_pre_commit_calls(
        tmp_path=tmp_path, staged_name="tests/test_example.py", uv_status=0
    )
    assert status == 0
    assert calls == [
        f"uv run python -m {_DELEGATE_MODULE} run",
        "just check-pre-commit-local",
        f"uv run python -m {_PRECHECK_MODULE}",
        "just check",
    ]


def test_a_precheck_refusal_stops_the_recipe_before_the_aggregate(*, tmp_path: Path) -> None:
    """A pre-check refusal exits non-zero and the aggregate never starts."""
    status, calls = _check_pre_commit_calls(
        tmp_path=tmp_path, staged_name="tests/test_example.py", uv_status=4
    )
    assert status == 4
    assert calls == [
        f"uv run python -m {_DELEGATE_MODULE} run",
        "just check-pre-commit-local",
        f"uv run python -m {_PRECHECK_MODULE}",
    ]


def test_a_doc_only_commit_never_runs_the_precheck(*, tmp_path: Path) -> None:
    """With zero `.py` files staged the recipe skips the pre-check entirely."""
    status, calls = _check_pre_commit_calls(tmp_path=tmp_path, staged_name="notes.md", uv_status=4)
    assert status == 0
    assert calls == [
        f"uv run python -m {_DELEGATE_MODULE} run",
        "just check-pre-commit-local",
        "just check-pre-commit-doc-only",
    ]
