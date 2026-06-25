"""Outside-in test for `dev-tooling/checks/no_renderer_vendoring.py`.

Covers the two scan surfaces of the renderer-non-vendoring guard
(`SPECIFICATION/constraints.md` §"Renderer non-vendoring"): a
renderer declared as a `pyproject.toml` dependency and a renderer
vendored under `.claude-plugin/scripts/_vendor/` both fail; a clean
tree (and a bare tree with neither surface present) passes. The
fixtures exercise all three name-match shapes (exact token,
`token-` prefix, `token_` prefix) and the non-match path.

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
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "no_renderer_vendoring.py"


def _load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "no_renderer_vendoring_under_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pyproject(*, root: Path, deps: list[str]) -> None:
    body = "[dependency-groups]\ndev = [\n" + "".join(f'    "{d}",\n' for d in deps) + "]\n"
    _ = (root / "pyproject.toml").write_text(body, encoding="utf-8")


def _make_vendor_entries(*, root: Path, names: list[str]) -> None:
    vendor = root / ".claude-plugin" / "scripts" / "_vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    for name in names:
        (vendor / name).mkdir()


def test_clean_tree_passes(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_pyproject(root=tmp_path, deps=["structlog", "returns>=0.22"])
    _make_vendor_entries(root=tmp_path, names=["structlog", "returns"])
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0


def test_renderer_dependency_in_pyproject_fails(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # `graphviz` (exact token) + `mermaid-cli` (token- prefix).
    _write_pyproject(root=tmp_path, deps=["structlog", "graphviz>=0.20", "mermaid-cli==1.0"])
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 1
    combined = capsys.readouterr().err
    assert "no-renderer-vendoring-dependency" in combined
    assert "graphviz" in combined
    assert "mermaid-cli" in combined


def test_vendored_renderer_fails(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # `plantuml` (exact token) + `nomnoml_js` (token_ prefix); `structlog`
    # is the non-renderer entry that must NOT be flagged.
    _write_pyproject(root=tmp_path, deps=["structlog"])
    _make_vendor_entries(root=tmp_path, names=["structlog", "plantuml", "nomnoml_js"])
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 1
    combined = capsys.readouterr().err
    assert "no-renderer-vendoring-vendored" in combined
    assert "plantuml" in combined
    assert "nomnoml_js" in combined


def test_absent_pyproject_and_vendor_is_noop(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No pyproject.toml and no _vendor/ dir at all: nothing to scan.
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0
