"""Tests for dev-tooling/checks/comment_line_anchors.

The check bans line-number anchors (the `[Ll]ines?\\s+\\d+...`
pattern) in Python docstrings and `#` comments. Such anchors
silently rot on any edit to the referenced file: a single
inserted paragraph above shifts every downstream reference
without any compiler / linter / test signal. Comments should
explain WHY (non-obvious constraints, hidden invariants,
surprising behavior) — not WHAT (already obvious from
well-named identifiers + signatures). Cross-references to specs
or other code should use section names or symbol names only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_CHECK_PATH = (
    Path(__file__).resolve().parents[3] / "dev-tooling" / "checks" / "comment_line_anchors.py"
)


def _run_check(*, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_CHECK_PATH)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _scaffold_target_dirs(*, root: Path) -> Path:
    target = root / ".claude-plugin" / "scripts" / "livespec"
    target.mkdir(parents=True)
    return target


def test_passes_on_clean_docstrings(*, tmp_path: Path) -> None:
    """Fixture with no line-number anchors → exit 0, empty stderr."""
    target = _scaffold_target_dirs(root=tmp_path)
    _ = (target / "clean.py").write_text(
        '"""A clean module docstring with no anchors."""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_fails_on_line_anchor_in_docstring(*, tmp_path: Path) -> None:
    """Fixture with a multi-line anchor in a docstring → exit non-zero."""
    target = _scaffold_target_dirs(root=tmp_path)
    _ = (target / "polluted.py").write_text(
        '"""Per spec.md lines 100-200, this module exists."""\n'
        "\n"
        "from __future__ import annotations\n"
        "\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    assert "polluted.py" in result.stderr


def test_fails_on_line_anchor_in_comment(*, tmp_path: Path) -> None:
    """Fixture with a single-line anchor in a `#` comment → exit non-zero."""
    target = _scaffold_target_dirs(root=tmp_path)
    _ = (target / "polluted.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "# Per spec.md line 42, this constant exists.\n"
        "_K = 1\n"
        "\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    assert "polluted.py" in result.stderr


def test_passes_when_anchor_is_in_string_literal(*, tmp_path: Path) -> None:
    """Fixture with an anchor inside a non-docstring string literal → exit 0.

    String literals are not comments. The check must scope to
    docstrings + `#` comments only.
    """
    target = _scaffold_target_dirs(root=tmp_path)
    _ = (target / "literal.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '_LABEL = "line 42 of the upstream file"\n'
        "\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_skips_vendored_library_files(*, tmp_path: Path) -> None:
    """Anchors inside `_vendor/` are out of scope."""
    vendor_dir = tmp_path / ".claude-plugin" / "scripts" / "_vendor" / "upstream"
    vendor_dir.mkdir(parents=True)
    _ = (vendor_dir / "shipped.py").write_text(
        '"""Per upstream README lines 100-200, this lib is vendored."""\n'
        "\n"
        "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main().

    Required to exercise the false arms of (a) the vendor
    `sys.path` guard at module-load time and (b) the
    `if __name__ == "__main__"` guard at the bottom — both
    untaken under subprocess invocation. Mirrors the pattern in
    `test_no_todo_registry_module_importable_without_running_main`.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "comment_line_anchors_for_import_test",
        str(_CHECK_PATH),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"


def test_failure_output_includes_why_not_what_reminder(*, tmp_path: Path) -> None:
    """The failure diagnostic must include a WHY-not-WHAT reminder.

    Per the user's directive: when the check fails, the output
    should remind the author that comments should explain WHY
    (non-obvious constraints, hidden invariants), not WHAT
    (already obvious from well-named identifiers).
    """
    target = _scaffold_target_dirs(root=tmp_path)
    _ = (target / "polluted.py").write_text(
        '"""Per spec.md lines 100-200, this module exists."""\n' "\n" "__all__: list[str] = []\n",
        encoding="utf-8",
    )
    result = _run_check(cwd=tmp_path)
    assert result.returncode != 0
    assert "WHY" in result.stderr
    assert "WHAT" in result.stderr
