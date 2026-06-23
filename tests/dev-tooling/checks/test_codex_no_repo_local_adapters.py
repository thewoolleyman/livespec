"""Outside-in test for `dev-tooling/checks/codex_no_repo_local_adapters.py`.

Core's v129 spec retired the repo-local Codex adapter model. The check is the
absence/retirement guard: it FAILS if any `.agents/skills/livespec-*` adapter
directory has been re-added, and PASSES when the tree is absent or carries no
`livespec-*` child.

The check reads `Path.cwd()`, so every test runs under
`monkeypatch.chdir(tmp_path)` to avoid polluting or colliding with the real
repository.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "codex_no_repo_local_adapters.py"


def _load_check() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "codex_no_repo_local_adapters_under_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_repo_local_adapter(*, root: Path, name: str) -> None:
    skill_dir = root / ".agents" / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: A re-added repo-local Codex adapter.\n"
        "---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )


def test_passes_when_no_repo_local_adapters(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An absent `.agents/skills/` tree satisfies the retirement guard."""
    (tmp_path / ".agents" / "plugins").mkdir(parents=True)
    (tmp_path / ".agents" / "plugins" / "marketplace.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0


def test_passes_when_skills_dir_has_no_livespec_adapter(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `.agents/skills/` tree with no `livespec-*` child still passes."""
    other = tmp_path / ".agents" / "skills" / "some-other-skill"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("# unrelated\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 0


def test_fails_when_repo_local_adapter_present(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A re-added `.agents/skills/livespec-*` adapter trips the guard."""
    _write_repo_local_adapter(root=tmp_path, name="livespec-foo")
    monkeypatch.chdir(tmp_path)

    module = _load_check()

    assert module.main() == 1
    combined = capsys.readouterr().err
    assert "livespec-foo" in combined
    assert "codex-no-repo-local-adapters" in combined


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    module = _load_check()

    assert callable(module.main), "main should be importable without invocation"
