"""Outside-in test for `dev-tooling/checks/branch_protection_alignment.py`.

Guard Layer 1 mechanical check that prevents the v039-D1-style
drift between `.github/workflows/ci.yml`'s job matrix and master
branch protection's required-checks list.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "branch_protection_alignment.py"


def _run_check(*, cwd: Path, env_path: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the check script with cwd set to tmp_path (or any path).

    Preserves the parent env (incl. COVERAGE_PROCESS_START) so pytest-cov's
    subprocess auto-init works; overrides only PATH when env_path is given.
    """
    env = {**os.environ, "PATH": env_path} if env_path is not None else None
    return subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_missing_ci_yml_fails(*, tmp_path: Path) -> None:
    """Empty cwd → ci.yml missing → exit 1."""
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 1, (
        f"expected exit 1 on missing ci.yml; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "ci.yml missing" in result.stderr


def test_empty_matrix_fails(*, tmp_path: Path) -> None:
    """ci.yml exists but has no parseable matrix → exit 1."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    _ = (workflows / "ci.yml").write_text("name: CI\non: push\n", encoding="utf-8")
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 1, (
        f"expected exit 1 on empty matrix; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "matrix.target" in result.stderr


def test_gh_unavailable_skips_gracefully(*, tmp_path: Path) -> None:
    """No `gh` on PATH → exit 0 with a warning (local-dev tolerance)."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    ci_yml = textwrap.dedent("""\
        name: CI
        on: push
        jobs:
          check:
            strategy:
              matrix:
                target:
                  - check-foo
                  - check-bar
            runs-on: ubuntu-latest
        """)
    _ = (workflows / "ci.yml").write_text(ci_yml, encoding="utf-8")
    # Empty PATH → gh CLI not found by shutil.which.
    result = _run_check(cwd=tmp_path, env_path="")
    assert result.returncode == 0, (
        f"expected exit 0 when gh unavailable; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "gh CLI not on PATH" in result.stderr


def test_real_repo_passes(*, tmp_path: Path) -> None:  # noqa: ARG001
    """Run the check against the real repo cwd; expect exit 0.

    Authenticated `gh` produces either pass (no missing-from-ci.yml)
    or warning-only output. With `gh` unauthenticated, the check
    still exits 0 (graceful skip). Either way: exit 0.
    """
    result = _run_check(cwd=_REPO_ROOT)
    assert result.returncode == 0, (
        f"expected exit 0 against real repo; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _setup_repo_with_ci_yml(*, tmp_path: Path, matrix_targets: list[str]) -> None:
    """Write a synthetic ci.yml with the given matrix.target list."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    target_lines = "\n".join(f"          - {t}" for t in matrix_targets)
    ci_yml = (
        "name: CI\n"
        "on: push\n"
        "jobs:\n"
        "  check:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        target:\n"
        f"{target_lines}\n"
        "    runs-on: ubuntu-latest\n"
    )
    _ = (workflows / "ci.yml").write_text(ci_yml, encoding="utf-8")


def _install_fake_gh(*, tmp_path: Path, stdout: str = "[]", returncode: int = 0) -> str:
    """Install a fake `gh` shell stub at tmp_path/bin/gh, return PATH including it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh_path = bin_dir / "gh"
    script = "#!/bin/sh\n" f"cat <<'STUB_EOF'\n{stdout}\nSTUB_EOF\n" f"exit {returncode}\n"
    _ = gh_path.write_text(script, encoding="utf-8")
    gh_path.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin"


def test_required_missing_from_ci_yml_fails(*, tmp_path: Path) -> None:
    """Required check absent from ci.yml matrix → exit 1."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo"])
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='["check-foo", "check-missing"]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 1, (
        f"expected exit 1 when required check missing from ci.yml; "
        f"got {result.returncode}, stderr={result.stderr!r}"
    )
    assert "check-missing" in result.stderr
    assert "required check has no matching ci.yml job" in result.stderr


def test_aligned_lists_pass(*, tmp_path: Path) -> None:
    """Required list and ci.yml matrix match exactly → exit 0, no warnings."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo", "check-bar"])
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='["check-foo", "check-bar"]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "required check has no matching" not in result.stderr


def test_blank_and_comment_lines_in_matrix_are_skipped(*, tmp_path: Path) -> None:
    """Blank lines and `# comment` lines within the matrix target bullets are skipped.

    Exercises the in-bullet-list `continue` branch in
    `_parse_ci_matrix` so an author may insert blank lines or
    comments to group jobs without breaking the parser.
    """
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    ci_yml = (
        "name: CI\n"
        "on: push\n"
        "jobs:\n"
        "  check:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        target:\n"
        "          # a comment line\n"
        "          - check-foo\n"
        "\n"
        "          - check-bar\n"
        "    runs-on: ubuntu-latest\n"
    )
    _ = (workflows / "ci.yml").write_text(ci_yml, encoding="utf-8")
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='["check-foo", "check-bar"]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0, (
        f"expected exit 0 with blank/comment lines in matrix; "
        f"got {result.returncode}, stderr={result.stderr!r}"
    )
    assert "required check has no matching" not in result.stderr


def test_extra_ci_job_warns(*, tmp_path: Path) -> None:
    """ci.yml has a job not in required list → exit 0 with warning."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo", "check-extra"])
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='["check-foo"]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "check-extra" in result.stderr
    assert "not in branch-protection required list" in result.stderr


def test_gh_api_failure_skips_gracefully(*, tmp_path: Path) -> None:
    """gh available but API call fails → exit 0 with warning."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo"])
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout="error", returncode=1)
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "gh api call failed" in result.stderr


def test_unexpected_payload_shape(*, tmp_path: Path) -> None:
    """gh returns non-list payload → exit 0 with error log (no enforcement)."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo"])
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout='{"not": "a list"}')
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "unexpected gh api response shape" in result.stderr


def test_payload_with_non_string_entries(*, tmp_path: Path) -> None:
    """gh list contains non-string entries → silently skip them (covers the False branch)."""
    _setup_repo_with_ci_yml(tmp_path=tmp_path, matrix_targets=["check-foo"])
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='["check-foo", 42, null, "check-bar"]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    # Only "check-foo" and "check-bar" are extracted as required;
    # ci.yml has only "check-foo", so "check-bar" is missing → exit 1.
    assert result.returncode == 1
    assert "check-bar" in result.stderr


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly via importlib (covers __name__ != "__main__" branch)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "branch_protection_alignment_for_import_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_module_re_import_with_vendor_in_sys_path() -> None:
    """Re-importing the module when _VENDOR_DIR is already on sys.path covers the False branch."""
    import importlib.util

    # First import — primes sys.path with _VENDOR_DIR (True branch of the guard).
    spec1 = importlib.util.spec_from_file_location(
        "branch_protection_alignment_first_import",
        str(_CHECK),
    )
    assert spec1 is not None and spec1.loader is not None
    module1 = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(module1)
    # Second import — _VENDOR_DIR is already on sys.path, exercises the False branch.
    spec2 = importlib.util.spec_from_file_location(
        "branch_protection_alignment_second_import",
        str(_CHECK),
    )
    assert spec2 is not None and spec2.loader is not None
    module2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(module2)
    assert callable(module2.main)
