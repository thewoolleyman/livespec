"""Tests for dev-tooling/checks/wrapper_shape.py.

Covers BOTH pass and fail cases per Phase 4 plan line 1452-1453.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add dev-tooling/checks to sys.path so the check module imports cleanly.
_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import wrapper_shape  # noqa: E402  -- after sys.path setup

__all__: list[str] = []


_VALID_WRAPPER = (
    "#!/usr/bin/env python3\n"
    '"""Shebang wrapper for example."""\n'
    "from _bootstrap import bootstrap\n"
    "bootstrap()\n"
    "from livespec.commands.example import main\n"
    "\n"
    "raise SystemExit(main())\n"
)


def test_valid_wrapper_passes(*, tmp_path: Path) -> None:
    """A correctly-shaped wrapper produces no violations."""
    wrapper = tmp_path / "example.py"
    wrapper.write_text(_VALID_WRAPPER, encoding="utf-8")
    violations = wrapper_shape.check_file(path=wrapper)
    assert violations == []


def test_missing_shebang_fails(*, tmp_path: Path) -> None:
    """A file without the canonical shebang produces a shebang violation."""
    bad_text = _VALID_WRAPPER.replace("#!/usr/bin/env python3", "#!/bin/bash")
    wrapper = tmp_path / "bad_shebang.py"
    wrapper.write_text(bad_text, encoding="utf-8")
    violations = wrapper_shape.check_file(path=wrapper)
    assert len(violations) == 1
    assert "must be" in violations[0]


def test_missing_docstring_fails(*, tmp_path: Path) -> None:
    """A file without a docstring as statement 2 produces a docstring violation."""
    bad_text = (
        "#!/usr/bin/env python3\n"
        "from _bootstrap import bootstrap\n"
        "bootstrap()\n"
        "from livespec.commands.example import main\n"
        "raise SystemExit(main())\n"
    )
    wrapper = tmp_path / "no_docstring.py"
    wrapper.write_text(bad_text, encoding="utf-8")
    violations = wrapper_shape.check_file(path=wrapper)
    assert any("docstring" in v for v in violations)


def test_wrong_statement_order_fails(*, tmp_path: Path) -> None:
    """A file with a non-canonical statement order surfaces violations."""
    bad_text = (
        "#!/usr/bin/env python3\n"
        '"""Shebang wrapper for example."""\n'
        "from livespec.commands.example import main\n"  # wrong: should be _bootstrap
        "bootstrap()\n"
        "from _bootstrap import bootstrap\n"
        "raise SystemExit(main())\n"
    )
    wrapper = tmp_path / "wrong_order.py"
    wrapper.write_text(bad_text, encoding="utf-8")
    violations = wrapper_shape.check_file(path=wrapper)
    assert len(violations) > 0


def test_extra_statement_fails(*, tmp_path: Path) -> None:
    """A file with an extra statement (e.g., a stray print) surfaces a count violation."""
    bad_text = (
        "#!/usr/bin/env python3\n"
        '"""Shebang wrapper for example."""\n'
        "from _bootstrap import bootstrap\n"
        "bootstrap()\n"
        "from livespec.commands.example import main\n"
        "raise SystemExit(main())\n"
        "x = 1  # stray statement\n"
    )
    wrapper = tmp_path / "extra_stmt.py"
    wrapper.write_text(bad_text, encoding="utf-8")
    violations = wrapper_shape.check_file(path=wrapper)
    assert any("post-docstring statements" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped bin/*.py wrappers all conform — main() exits 0."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert wrapper_shape.main() == 0
