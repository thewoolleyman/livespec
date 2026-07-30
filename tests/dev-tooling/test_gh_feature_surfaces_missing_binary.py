"""Coverage companion for `dev-tooling/gh_feature_surfaces.py` missing-binary handling."""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "gh_feature_surfaces.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gh_feature_surfaces", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_fake_gh(*, tmp_path: Path, body: str) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(body, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)
    return bin_dir


def test_fails_when_gh_is_not_on_path(*, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setenv("PATH", "")

    assert module.main() == 1


def test_fails_when_update_branch_help_falls_back_to_pr_help(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    bin_dir = _write_fake_gh(
        tmp_path=tmp_path,
        body="""#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == "pr checks --json name --help" ]]; then
  exit 0
fi
if [[ "$*" == "pr update-branch --help" ]]; then
  printf 'USAGE\n  gh pr <command> [flags]\n'
  exit 0
fi
printf 'unexpected gh argv: %s\n' "$*" >&2
exit 99
""",
    )
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

    assert module.main() == 1
