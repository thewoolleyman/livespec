"""Outside-in test for `dev-tooling/checks/master_ci_green.py`.

Guard Layer 1 mechanical check that prevents the silent-red-master
pattern: master CI failed weeks ago, every PR merged onto red master
inherited the brokenness. The check ensures master CI is green at
every commit (graceful skip when `gh` is unavailable locally).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "master_ci_green.py"


def _run_check(*, cwd: Path, env_path: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the check script with cwd set to a path.

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


def test_gh_unavailable_skips_gracefully(*, tmp_path: Path) -> None:
    """No `gh` on PATH → exit 0 with a warning (local-dev tolerance)."""
    result = _run_check(cwd=tmp_path, env_path="")
    assert result.returncode == 0, (
        f"expected exit 0 when gh unavailable; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "gh CLI not on PATH" in result.stderr


def test_real_repo_passes(*, tmp_path: Path) -> None:  # noqa: ARG001
    """Run the check against the real repo cwd; expect exit 0.

    Master CI is green (we just verified after PR #4 merged). This
    test exercises the happy path. With `gh` unauthenticated the
    check still exits 0 (graceful skip). Either way: exit 0.
    """
    result = _run_check(cwd=_REPO_ROOT)
    assert result.returncode == 0, (
        f"expected exit 0 against real repo; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _install_fake_gh(*, tmp_path: Path, stdout: str = "[]", returncode: int = 0) -> str:
    """Install a fake `gh` shell stub at tmp_path/bin/gh, return PATH including it."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    gh_path = bin_dir / "gh"
    script = "#!/bin/sh\n" f"cat <<'STUB_EOF'\n{stdout}\nSTUB_EOF\n" f"exit {returncode}\n"
    _ = gh_path.write_text(script, encoding="utf-8")
    gh_path.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin"


def test_success_conclusion_passes(*, tmp_path: Path) -> None:
    """Latest CI is success → exit 0."""
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='[{"status": "completed", "conclusion": "success"}]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0


def test_failure_conclusion_fails(*, tmp_path: Path) -> None:
    """Latest CI is failure → exit 1 with error diagnostic."""
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='[{"status": "completed", "conclusion": "failure"}]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 1
    assert "master CI is red" in result.stderr


def test_pending_status_passes(*, tmp_path: Path) -> None:
    """Latest CI still in_progress → exit 0 with info log."""
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='[{"status": "in_progress", "conclusion": null}]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "still pending" in result.stderr


def test_unrecognized_conclusion_passes(*, tmp_path: Path) -> None:
    """Unrecognized conclusion → exit 0 with warning (non-blocking)."""
    fake_path = _install_fake_gh(
        tmp_path=tmp_path,
        stdout='[{"status": "completed", "conclusion": "neutral"}]',
    )
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "unrecognized conclusion" in result.stderr


def test_empty_runs_list_skips(*, tmp_path: Path) -> None:
    """No CI runs on master yet → exit 0 with warning."""
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout="[]")
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "no CI runs on master yet" in result.stderr


def test_gh_api_failure_skips_gracefully(*, tmp_path: Path) -> None:
    """gh available but API call fails → exit 0 with warning."""
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout="error", returncode=1)
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "gh api call failed" in result.stderr


def test_unexpected_payload_shape(*, tmp_path: Path) -> None:
    """gh returns non-list payload → exit 0 with warning."""
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout='{"not": "a list"}')
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "no CI runs on master yet" in result.stderr


def test_first_entry_not_dict(*, tmp_path: Path) -> None:
    """gh returns list but first entry isn't a dict → exit 0 with error log."""
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout='["not a dict"]')
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    assert "unexpected gh response shape" in result.stderr


def test_missing_status_and_conclusion(*, tmp_path: Path) -> None:
    """gh returns dict without status/conclusion fields → exit 0 with warning."""
    fake_path = _install_fake_gh(tmp_path=tmp_path, stdout="[{}]")
    result = _run_check(cwd=tmp_path, env_path=fake_path)
    assert result.returncode == 0
    # status is None (not in PENDING set) and conclusion is None
    # (not in GREEN or RED set), so falls through to "unrecognized" warning.
    assert "unrecognized conclusion" in result.stderr


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly via importlib (covers __name__ != "__main__" branch)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "master_ci_green_for_import_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_module_re_import_with_vendor_in_sys_path() -> None:
    """Re-importing when _VENDOR_DIR is already on sys.path covers the False branch."""
    import importlib.util

    spec1 = importlib.util.spec_from_file_location(
        "master_ci_green_first_import",
        str(_CHECK),
    )
    assert spec1 is not None and spec1.loader is not None
    module1 = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(module1)
    spec2 = importlib.util.spec_from_file_location(
        "master_ci_green_second_import",
        str(_CHECK),
    )
    assert spec2 is not None and spec2.loader is not None
    module2 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(module2)
    assert callable(module2.main)
