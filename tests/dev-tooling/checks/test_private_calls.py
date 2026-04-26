"""Tests for dev-tooling/checks/private_calls.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import private_calls  # noqa: E402

__all__: list[str] = []


_PUBLIC_IMPORT = '"""docstring"""\nfrom os import path\n'
_DUNDER_IMPORT = '"""docstring"""\nfrom __future__ import annotations\n'
_PRIVATE_IMPORT = '"""docstring"""\nfrom livespec.io.fs import _internal_helper\n'
_PRIVATE_PATH_TRAVERSAL = '"""docstring"""\nimport livespec.io._private_module\n'
_BOOTSTRAP_IMPORT = '"""docstring"""\nfrom _bootstrap import bootstrap\n'

_RELATIVE_LIVESPEC = Path(".claude-plugin/scripts/livespec/io/fs.py")
_RELATIVE_BIN_WRAPPER = Path(".claude-plugin/scripts/bin/seed.py")
_RELATIVE_NON_BIN = Path(".claude-plugin/scripts/livespec/commands/seed.py")


def test_public_import_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_PUBLIC_IMPORT, encoding="utf-8")
    assert private_calls.check_file(path=target, relative=_RELATIVE_LIVESPEC) == []


def test_dunder_import_passes(*, tmp_path: Path) -> None:
    """Dunder imports (e.g., __future__) are not 'private' — passes."""
    target = tmp_path / "module.py"
    target.write_text(_DUNDER_IMPORT, encoding="utf-8")
    assert private_calls.check_file(path=target, relative=_RELATIVE_LIVESPEC) == []


def test_private_import_fails(*, tmp_path: Path) -> None:
    """Cross-module import of a single-underscore-prefixed name fails."""
    target = tmp_path / "module.py"
    target.write_text(_PRIVATE_IMPORT, encoding="utf-8")
    violations = private_calls.check_file(path=target, relative=_RELATIVE_LIVESPEC)
    assert len(violations) == 1
    assert "_internal_helper" in violations[0]


def test_private_path_traversal_fails(*, tmp_path: Path) -> None:
    """`import livespec.io._private_module` flags the _-prefixed segment."""
    target = tmp_path / "module.py"
    target.write_text(_PRIVATE_PATH_TRAVERSAL, encoding="utf-8")
    violations = private_calls.check_file(path=target, relative=_RELATIVE_LIVESPEC)
    assert len(violations) == 1
    assert "_private_module" in violations[0]


def test_bootstrap_import_passes_anywhere(*, tmp_path: Path) -> None:
    """`from _bootstrap import bootstrap` passes — the imported NAME (`bootstrap`)
    is public; the rule targets _-prefixed FUNCTION names, not _-prefixed MODULE
    names. The bin-wrapper exemption is defensive belt-and-suspenders for the
    one canonical use site."""
    target = tmp_path / "anywhere.py"
    target.write_text(_BOOTSTRAP_IMPORT, encoding="utf-8")
    assert private_calls.check_file(path=target, relative=_RELATIVE_BIN_WRAPPER) == []
    assert private_calls.check_file(path=target, relative=_RELATIVE_NON_BIN) == []


def test_private_function_from_private_module_fails(*, tmp_path: Path) -> None:
    """`from _bootstrap import _internal` flags the imported _-prefixed name."""
    target = tmp_path / "double_private.py"
    target.write_text(
        '"""docstring"""\nfrom _bootstrap import _internal\n',
        encoding="utf-8",
    )
    violations = private_calls.check_file(path=target, relative=_RELATIVE_NON_BIN)
    assert len(violations) == 1
    assert "_internal" in violations[0]


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert private_calls.main() == 0
