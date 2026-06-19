"""Outside-in test for `dev-tooling/checks/codex_adapter_sync.py`.

The check keeps project-local Codex adapters thin over livespec core prose and
wrappers. It validates adapter names, YAML frontmatter, core prose references,
wrapper references, and rejects copied operation-prose sections.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "checks" / "codex_adapter_sync.py"


def _run(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _write_core_files(*, root: Path) -> None:
    prose = root / ".claude-plugin" / "prose"
    prose.mkdir(parents=True)
    for name in ("help", "next", "doctor"):
        (prose / f"{name}.md").write_text(f"# {name}\n\nCore prose.\n", encoding="utf-8")
    wrappers = root / ".claude-plugin" / "scripts" / "bin"
    wrappers.mkdir(parents=True)
    for name in ("next.py", "doctor_static.py"):
        (wrappers / name).write_text("#!/usr/bin/env python3\n", encoding="utf-8")


def _write_adapter(
    *,
    root: Path,
    name: str,
    operation: str,
    wrapper: str | None,
    body_extra: str = "",
) -> None:
    skill_dir = root / ".agents" / "skills" / name
    skill_dir.mkdir(parents=True)
    wrapper_step = (
        "4. Do not invoke a wrapper CLI; the core help prose defines this operation as narration-only.\n"
        if wrapper is None
        else f"4. When the prose calls for the CLI, invoke `{wrapper}` from this repository.\n"
    )
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: Use when the user invokes `/livespec:{operation}`.\n"
        "---\n\n"
        f"# {name}\n\n"
        "This is a Codex runtime adapter for livespec.\n\n"
        "When this skill is triggered:\n\n"
        "1. Resolve the repository root as the current working tree.\n"
        f"2. Read `.claude-plugin/prose/{operation}.md` completely.\n"
        "3. Follow that prose exactly for behavior, routing, failure handling, and user-facing output.\n"
        f"{wrapper_step}"
        "5. Do not copy, summarize as a substitute for, or restate operation behavior from the prose in this adapter.\n"
        f"{body_extra}",
        encoding="utf-8",
    )


def _write_complete_adapter_fixture(*, root: Path) -> None:
    _write_core_files(root=root)
    _write_adapter(root=root, name="livespec-help", operation="help", wrapper=None)
    _write_adapter(
        root=root,
        name="livespec-next",
        operation="next",
        wrapper=".claude-plugin/scripts/bin/next.py",
    )
    _write_adapter(
        root=root,
        name="livespec-doctor",
        operation="doctor",
        wrapper=".claude-plugin/scripts/bin/doctor_static.py",
    )


def test_accepts_complete_adapter_set(*, tmp_path: Path) -> None:
    """The expected read-only adapter set passes when all references resolve."""
    _write_complete_adapter_fixture(root=tmp_path)

    result = _run(cwd=tmp_path)

    assert result.returncode == 0, (
        f"complete adapter fixture should pass; returncode={result.returncode} "
        f"stderr={result.stderr!r}"
    )


def test_rejects_missing_expected_adapter(*, tmp_path: Path) -> None:
    """All three read-only adapter files are required."""
    _write_complete_adapter_fixture(root=tmp_path)
    (tmp_path / ".agents" / "skills" / "livespec-next" / "SKILL.md").unlink()

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "livespec-next" in combined


def test_rejects_frontmatter_name_mismatch(*, tmp_path: Path) -> None:
    """Codex YAML frontmatter name must match the namespaced adapter directory."""
    _write_complete_adapter_fixture(root=tmp_path)
    skill = tmp_path / ".agents" / "skills" / "livespec-help" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace("name: livespec-help", "name: help"),
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "frontmatter" in combined
    assert "livespec-help" in combined


def test_rejects_missing_core_prose_reference(*, tmp_path: Path) -> None:
    """Every adapter must reference its existing core prose file."""
    _write_complete_adapter_fixture(root=tmp_path)
    (tmp_path / ".claude-plugin" / "prose" / "next.md").unlink()

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert ".claude-plugin/prose/next.md" in combined


def test_rejects_missing_wrapper_reference(*, tmp_path: Path) -> None:
    """Wrapper-backed adapters must name the expected core wrapper."""
    _write_complete_adapter_fixture(root=tmp_path)
    skill = tmp_path / ".agents" / "skills" / "livespec-doctor" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            ".claude-plugin/scripts/bin/doctor_static.py",
            ".claude-plugin/scripts/bin/doctor.py",
        ),
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert ".claude-plugin/scripts/bin/doctor_static.py" in combined


def test_rejects_copied_core_section_heading(*, tmp_path: Path) -> None:
    """Adapters must not copy operation-prose sections like `## Steps`."""
    _write_complete_adapter_fixture(root=tmp_path)
    skill = tmp_path / ".agents" / "skills" / "livespec-help" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8") + "\n## Steps\n\nCopied operation detail.\n",
        encoding="utf-8",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "copied" in combined
    assert "livespec-help" in combined


def test_rejects_unexpected_livespec_adapter(*, tmp_path: Path) -> None:
    """Mutating livespec adapters stay out until the read-only surface is guarded."""
    _write_complete_adapter_fixture(root=tmp_path)
    _write_adapter(
        root=tmp_path,
        name="livespec-revise",
        operation="revise",
        wrapper=".claude-plugin/scripts/bin/revise.py",
    )

    result = _run(cwd=tmp_path)

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "livespec-revise" in combined


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "codex_adapter_sync_for_import_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
