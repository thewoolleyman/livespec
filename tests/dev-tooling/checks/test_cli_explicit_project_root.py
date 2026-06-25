"""Outside-in test for `dev-tooling/checks/cli_explicit_project_root.py`.

Covers the explicit-project-root convention guard
(`SPECIFICATION/contracts.md` §"CLI shape conventions"): a spec-side
CLI module (one defining a `build_parser()` factory) passes when its
`build_parser` registers `--project-root` and fails when it does not;
a module with no `build_parser` is not a CLI and is skipped; an absent
package tree is a clean no-op.

The check reads `Path.cwd()`, so every test runs under
`monkeypatch.chdir(tmp_path)` to avoid polluting the real repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "cli_explicit_project_root.py"
_CMD_DIR = Path(".claude-plugin") / "scripts" / "livespec" / "commands"


def _load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "cli_explicit_project_root_under_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_module(*, root: Path, name: str, body: str) -> None:
    cmd_dir = root / _CMD_DIR
    cmd_dir.mkdir(parents=True, exist_ok=True)
    _ = (cmd_dir / f"{name}.py").write_text(body, encoding="utf-8")


_WITH_PROJECT_ROOT = (
    "import argparse\n\n\n"
    "def build_parser() -> argparse.ArgumentParser:\n"
    "    parser = argparse.ArgumentParser()\n"
    '    _ = parser.add_argument("--seed-json", required=True)\n'
    '    _ = parser.add_argument("--project-root", default=None)\n'
    "    return parser\n"
)
_NO_BUILD_PARSER = "def helper() -> int:\n    return 0\n"
_MISSING_PROJECT_ROOT = (
    "import argparse\n\n\n"
    "def build_parser() -> argparse.ArgumentParser:\n"
    "    parser = argparse.ArgumentParser()\n"
    '    _ = parser.add_argument("--findings-json", required=True)\n'
    "    return parser\n"
)


def test_passes_when_every_cli_has_project_root(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_module(root=tmp_path, name="seed", body=_WITH_PROJECT_ROOT)
    # A non-CLI helper module (no build_parser) must be skipped, not flagged.
    _write_module(root=tmp_path, name="_helper", body=_NO_BUILD_PARSER)
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0


def test_fails_when_a_cli_lacks_project_root(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_module(root=tmp_path, name="critique", body=_MISSING_PROJECT_ROOT)
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 1
    combined = capsys.readouterr().err
    assert "cli-explicit-project-root" in combined
    assert "critique.py" in combined


def test_absent_package_is_noop(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # No .claude-plugin/scripts/livespec/ tree at all: nothing to scan.
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0
