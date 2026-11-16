"""A passing test leaves no tmp_path or tmp_path_factory files behind under this repo's pytest config.

Many files per suite run under pytest's basetemp exhausted a seat host's tmpfs inodes
(livespec-dev-tooling-jxhi63, 2026-11-16). The repository's `[tool.pytest.ini_options]`
retention keys and the tests/conftest.py fixtures must remove a passing test's directories,
including non-writable trees and `mktemp` directories."""

import ast
import os
from pathlib import Path

import pytest
import tomli

__all__: list[str] = []

pytest_plugins = ("pytester",)

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
_CONFTEST = Path(__file__).resolve().parent / "conftest.py"

_WRITER = """
def test_writes_files(tmp_path):
    for index in range(20):
        (tmp_path / f"retention_marker_{index}.txt").write_text("x")
"""


def test_a_passing_tests_tmp_path_files_are_removed(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    options = tomli.loads(_PYPROJECT.read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))
    ini_lines = ["[pytest]"] + [
        f"{key} = {options[key]}" for key in options if key.startswith("tmp_path_retention")
    ]
    pytester.makeini("\n".join(ini_lines))
    pytester.makepyfile(_WRITER)

    result = pytester.runpytest_inprocess("-p", "no:cacheprovider")

    result.assert_outcomes(passed=1)
    assert list(temproot.rglob("retention_marker_*.txt")) == []


def _removable_fixture_conftest() -> str:
    """The real `_tmp_path_stays_removable` fixture of tests/conftest.py, lifted into a conftest."""
    source = _CONFTEST.read_text(encoding="utf-8")
    fixture = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == "_tmp_path_stays_removable"
    )
    first_line = fixture.decorator_list[0].lineno
    body = "\n".join(source.splitlines()[first_line - 1 : fixture.end_lineno])
    header = "import os\nfrom collections.abc import Iterator\nfrom pathlib import Path\nimport pytest\n\n\n"
    return header + body + "\n"


_READONLY_WRITER = """
import os


def test_leaves_a_non_writable_tree(tmp_path):
    objects = tmp_path / "run-from" / ".git" / "objects" / "ab"
    objects.mkdir(parents=True)
    (objects / "retention_marker_object").write_text("x")
    (objects / "retention_marker_object").chmod(0o444)
    for directory in (objects, objects.parent, objects.parent.parent, objects.parent.parent.parent):
        directory.chmod(0o555)
"""


def test_a_passing_tests_non_writable_tree_is_removed(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    options = tomli.loads(_PYPROJECT.read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))
    ini_lines = ["[pytest]"] + [
        f"{key} = {options[key]}" for key in options if key.startswith("tmp_path_retention")
    ]
    pytester.makeini("\n".join(ini_lines))
    pytester.makeconftest(_removable_fixture_conftest())
    pytester.makepyfile(_READONLY_WRITER)

    result = pytester.runpytest_inprocess("-p", "no:cacheprovider")

    leftovers = [str(path) for path in temproot.rglob("retention_marker_object")]
    for directory, _subdirectories, _files in os.walk(temproot):
        Path(directory).chmod(0o755)
    result.assert_outcomes(passed=1)
    assert leftovers == []


_LIFTED = ("_CALL_REPORT", "pytest_runtest_makereport", "_make_removable", "_factory_dirs_removed")

_FACTORY_WRITER = """
def test_makes_factory_dirs(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("factory-marker")
    (scratch / "factory_marker_file.txt").write_text("x")
    guarded = tmp_path_factory.mktemp("factory-guarded") / "sub"
    guarded.mkdir()
    (guarded / "factory_marker_guarded.txt").write_text("x")
    guarded.chmod(0o555)
"""

_FAILING_FACTORY_WRITER = """
def test_makes_factory_dirs_then_fails(tmp_path_factory):
    scratch = tmp_path_factory.mktemp("factory-marker")
    (scratch / "factory_marker_kept.txt").write_text("x")
    assert False
"""


def _lifted_conftest() -> str:
    """The real factory-dir cleanup of tests/conftest.py, lifted into a conftest."""
    source = _CONFTEST.read_text(encoding="utf-8")
    lines = source.splitlines()
    chunks = []
    for node in ast.parse(source).body:
        name = (
            node.targets[0].id
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            else getattr(node, "name", None)
        )
        if name in _LIFTED:
            first = min(
                [node.lineno, *(item.lineno for item in getattr(node, "decorator_list", []))]
            )
            chunks.append("\n".join(lines[first - 1 : node.end_lineno]))
    header = "import os\nimport shutil\nfrom collections.abc import Generator, Iterator\nfrom pathlib import Path\nimport pytest\n\n\n"
    return header + "\n\n\n".join(chunks) + "\n"


def _run(
    *, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, writer: str
) -> tuple[pytest.RunResult, Path]:
    options = tomli.loads(_PYPROJECT.read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
    temproot = tmp_path / "temproot"
    temproot.mkdir()
    monkeypatch.setenv("PYTEST_DEBUG_TEMPROOT", str(temproot))
    ini_lines = ["[pytest]"] + [
        f"{key} = {options[key]}" for key in options if key.startswith("tmp_path_retention")
    ]
    pytester.makeini("\n".join(ini_lines))
    pytester.makeconftest(_lifted_conftest())
    pytester.makepyfile(writer)
    result = pytester.runpytest_inprocess("-p", "no:cacheprovider")
    return result, temproot


def _unlock(*, root: Path) -> None:
    for directory, _subdirectories, _files in os.walk(root):
        Path(directory).chmod(0o755)


def test_a_passing_tests_factory_dirs_are_removed(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, temproot = _run(
        pytester=pytester, monkeypatch=monkeypatch, tmp_path=tmp_path, writer=_FACTORY_WRITER
    )

    leftovers = [str(path) for path in temproot.rglob("factory_marker_*.txt")]
    _unlock(root=temproot)
    result.assert_outcomes(passed=1)
    assert leftovers == []


def test_a_failing_tests_factory_dirs_are_kept_for_diagnosis(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    result, temproot = _run(
        pytester=pytester,
        monkeypatch=monkeypatch,
        tmp_path=tmp_path,
        writer=_FAILING_FACTORY_WRITER,
    )

    kept = [path.name for path in temproot.rglob("factory_marker_kept.txt")]
    result.assert_outcomes(failed=1)
    assert kept == ["factory_marker_kept.txt"]
