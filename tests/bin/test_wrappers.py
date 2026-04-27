"""Meta-test: every shebang wrapper conforms to the 6-statement shape.

Independent of `dev-tooling/checks/wrapper_shape.py` (which exists
to gate `just check-wrapper-shape`); this test asserts the shape
from the test-suite side per Phase 5 plan line 1540-1541, ensuring
any future wrapper added to `.claude-plugin/scripts/bin/` is caught
by `just check-tests` even before `just check-wrapper-shape` runs.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

__all__: list[str] = []


_BIN_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "bin"
_EXEMPT_FILES = frozenset({"_bootstrap.py"})
_SHEBANG = "#!/usr/bin/env python3"
_POST_DOCSTRING_STMT_COUNT = 4


def _wrappers() -> list[Path]:
    return sorted(p for p in _BIN_DIR.glob("*.py") if p.name not in _EXEMPT_FILES)


@pytest.mark.parametrize("wrapper", _wrappers(), ids=lambda p: p.name)
def test_wrapper_has_canonical_shebang(*, wrapper: Path) -> None:
    """Statement 1: `#!/usr/bin/env python3`."""
    first_line = wrapper.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == _SHEBANG


@pytest.mark.parametrize("wrapper", _wrappers(), ids=lambda p: p.name)
def test_wrapper_has_module_docstring(*, wrapper: Path) -> None:
    """Statement 2: a module docstring."""
    tree = ast.parse(wrapper.read_text(encoding="utf-8"), filename=str(wrapper))
    assert tree.body, f"{wrapper.name}: empty body"
    docstring_node = tree.body[0]
    assert isinstance(docstring_node, ast.Expr)
    assert isinstance(docstring_node.value, ast.Constant)
    assert isinstance(docstring_node.value.value, str)


@pytest.mark.parametrize("wrapper", _wrappers(), ids=lambda p: p.name)
def test_wrapper_has_four_post_docstring_statements(*, wrapper: Path) -> None:
    """Statements 3-6: import bootstrap; bootstrap(); import main; raise SystemExit(main())."""
    tree = ast.parse(wrapper.read_text(encoding="utf-8"), filename=str(wrapper))
    body = tree.body[1:]  # skip the docstring
    assert len(body) == _POST_DOCSTRING_STMT_COUNT, (
        f"{wrapper.name}: expected {_POST_DOCSTRING_STMT_COUNT} post-docstring statements, "
        f"got {len(body)}"
    )


@pytest.mark.parametrize("wrapper", _wrappers(), ids=lambda p: p.name)
def test_wrapper_imports_bootstrap_then_calls_then_imports_main_then_raises(
    *, wrapper: Path
) -> None:
    """Statements 3-6 in order: from _bootstrap import bootstrap; bootstrap();
    from livespec.<...> import main; raise SystemExit(main())."""
    tree = ast.parse(wrapper.read_text(encoding="utf-8"), filename=str(wrapper))
    stmt_3, stmt_4, stmt_5, stmt_6 = tree.body[1:]

    assert isinstance(stmt_3, ast.ImportFrom)
    assert stmt_3.module == "_bootstrap"
    assert [alias.name for alias in stmt_3.names] == ["bootstrap"]

    assert isinstance(stmt_4, ast.Expr)
    assert isinstance(stmt_4.value, ast.Call)
    assert isinstance(stmt_4.value.func, ast.Name)
    assert stmt_4.value.func.id == "bootstrap"
    assert not stmt_4.value.args
    assert not stmt_4.value.keywords

    assert isinstance(stmt_5, ast.ImportFrom)
    assert stmt_5.module is not None
    assert stmt_5.module.startswith("livespec.")
    assert [alias.name for alias in stmt_5.names] == ["main"]

    assert isinstance(stmt_6, ast.Raise)
    assert isinstance(stmt_6.exc, ast.Call)
    assert isinstance(stmt_6.exc.func, ast.Name)
    assert stmt_6.exc.func.id == "SystemExit"
    assert len(stmt_6.exc.args) == 1
    inner = stmt_6.exc.args[0]
    assert isinstance(inner, ast.Call)
    assert isinstance(inner.func, ast.Name)
    assert inner.func.id == "main"


def test_at_least_one_wrapper_present() -> None:
    """Sanity guard: tests/bin/test_wrappers.py is meaningful only when wrappers exist."""
    assert _wrappers(), f"no wrappers found under {_BIN_DIR}"


def test_module_imported_under_pytest() -> None:
    """The pytest module is imported (covers the import statement at module top)."""
    assert "pytest" in sys.modules
