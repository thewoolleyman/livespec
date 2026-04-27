"""Tests for dev-tooling/checks/no_write_direct.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import no_write_direct  # noqa: E402

__all__: list[str] = []


_NO_WRITE = '"""docstring"""\n__all__: list[str] = []\n'

_HELPER_WITH_WRITE = (
    '"""docstring"""\nimport sys\ndef helper() -> None:\n    sys.stdout.write("hi")\n'
)

_MAIN_WITH_WRITE = (
    '"""docstring"""\n'
    "import sys\n"
    "def main() -> int:\n"
    '    sys.stdout.write("hi")\n'
    "    return 0\n"
)

_NESTED_HELPER_WITH_WRITE = (
    '"""docstring"""\n'
    "import sys\n"
    "def main() -> int:\n"
    "    def nested_helper() -> None:\n"
    '        sys.stdout.write("hi")\n'
    "    nested_helper()\n"
    "    return 0\n"
)

_RELATIVE_COMMAND = Path(".claude-plugin/scripts/livespec/commands/example.py")
_RELATIVE_NON_COMMAND = Path(".claude-plugin/scripts/livespec/io/fs.py")
_RELATIVE_BOOTSTRAP = Path(".claude-plugin/scripts/bin/_bootstrap.py")
_RELATIVE_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")


def test_no_write_passes(*, tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text(_NO_WRITE, encoding="utf-8")
    assert no_write_direct.check_file(path=target, relative=_RELATIVE_NON_COMMAND) == []


def test_helper_with_write_in_command_fails(*, tmp_path: Path) -> None:
    """sys.stdout.write inside a non-main helper of a commands/ file is forbidden."""
    target = tmp_path / "command_helper.py"
    target.write_text(_HELPER_WITH_WRITE, encoding="utf-8")
    violations = no_write_direct.check_file(path=target, relative=_RELATIVE_COMMAND)
    assert len(violations) == 1
    assert "sys.stdout.write()" in violations[0]


def test_main_with_write_in_command_passes(*, tmp_path: Path) -> None:
    """sys.stdout.write inside def main() of a commands/ file is exempted."""
    target = tmp_path / "command_main.py"
    target.write_text(_MAIN_WITH_WRITE, encoding="utf-8")
    assert no_write_direct.check_file(path=target, relative=_RELATIVE_COMMAND) == []


def test_main_with_write_in_run_static_passes(*, tmp_path: Path) -> None:
    """sys.stdout.write inside def main() of run_static.py is exempted."""
    target = tmp_path / "run_static.py"
    target.write_text(_MAIN_WITH_WRITE, encoding="utf-8")
    assert no_write_direct.check_file(path=target, relative=_RELATIVE_RUN_STATIC) == []


def test_main_with_write_in_non_command_fails(*, tmp_path: Path) -> None:
    """sys.stdout.write inside def main() of a NON-commands file is still forbidden."""
    target = tmp_path / "io_main.py"
    target.write_text(_MAIN_WITH_WRITE, encoding="utf-8")
    violations = no_write_direct.check_file(path=target, relative=_RELATIVE_NON_COMMAND)
    assert len(violations) == 1


def test_nested_helper_inside_main_passes(*, tmp_path: Path) -> None:
    """A nested closure inside `main()` is part of main's lexical scope and stays exempt.

    The style-doc rule "exemption is per-supervisor, NOT per-helper"
    targets module-top-level helper `def`s — the kind that show up
    in the AST as siblings of `main()`. Nested `def`s (closures
    declared INSIDE main()) are part of main's body lexically and
    inherit the exemption; they're a normal Python idiom for
    factoring a chunk of main's logic without exposing a separate
    module-level helper.
    """
    target = tmp_path / "nested.py"
    target.write_text(_NESTED_HELPER_WITH_WRITE, encoding="utf-8")
    assert no_write_direct.check_file(path=target, relative=_RELATIVE_COMMAND) == []


def test_bootstrap_passes_unconditionally(*, tmp_path: Path) -> None:
    """bin/_bootstrap.py is fully exempted — its sys.stderr.write is permitted."""
    target = tmp_path / "_bootstrap.py"
    target.write_text(_HELPER_WITH_WRITE, encoding="utf-8")
    assert no_write_direct.check_file(path=target, relative=_RELATIVE_BOOTSTRAP) == []


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """Post-Phase-4 sub-step 4 supervisor refactor: shipped code conforms."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert no_write_direct.main() == 0
