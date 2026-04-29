"""Outside-in test for `dev-tooling/checks/no_direct_tool_invocation.py`.

Per `python-skill-script-style-requirements.md` line 2097 and
PROPOSAL.md §"Dev tooling and task runner":

    grep: `lefthook.yml` and `.github/workflows/*.yml` only
    invoke `just <target>` (no direct `ruff` / `pyright` /
    `pytest` / `python3` / `mutmut` / `lint-imports`
    invocations).

Cycle 52 pins the canonical violation: a `run:` line in
`lefthook.yml` or any `.github/workflows/*.yml` that invokes
`pytest` directly is rejected. The other banned-tool words
(`ruff`, `pyright`, `python3`, `mutmut`, `lint-imports`) are
recognized too — they all share one banlist.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NO_DIRECT_TOOL_INVOCATION = (
    _REPO_ROOT / "dev-tooling" / "checks" / "no_direct_tool_invocation.py"
)


def test_no_direct_tool_invocation_rejects_lefthook_pytest_run(*, tmp_path: Path) -> None:
    """A `lefthook.yml` invoking `pytest` directly is rejected.

    Fixture: `lefthook.yml` declares a pre-commit hook with
    `run: pytest`. The check must walk lefthook.yml + the
    workflows tree, observe the banned word, exit non-zero,
    and surface the offending file.
    """
    (tmp_path / "lefthook.yml").write_text(
        "pre-commit:\n"
        "  commands:\n"
        "    check:\n"
        "      run: pytest\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_DIRECT_TOOL_INVOCATION)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"no_direct_tool_invocation should reject `run: pytest` in lefthook.yml; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = "lefthook.yml"
    assert expected_path in combined, (
        f"no_direct_tool_invocation diagnostic does not surface offending file "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_direct_tool_invocation_accepts_just_targets_only(*, tmp_path: Path) -> None:
    """A `lefthook.yml` whose `run:` lines only invoke `just <target>` is accepted.

    Fixture: lefthook.yml + a workflow file both delegate
    exclusively to `just check`. The check must walk and exit 0.
    """
    (tmp_path / "lefthook.yml").write_text(
        "pre-commit:\n"
        "  commands:\n"
        "    check:\n"
        "      run: just check\n",
        encoding="utf-8",
    )
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text(
        "name: CI\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - run: just check\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NO_DIRECT_TOOL_INVOCATION)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"no_direct_tool_invocation should accept `run: just check` lines; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
