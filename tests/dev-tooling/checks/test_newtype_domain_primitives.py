"""Outside-in test for `dev-tooling/checks/newtype_domain_primitives.py` — canonical field names use NewTypes.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-newtype-domain-primitives` row),
walks `schemas/dataclasses/*.py` and function signatures;
verifies field annotations matching canonical field names
(`check_id`, `run_id`, `topic`, `spec_root`, `schema_id`,
`template`, `author`/`author_human`/`author_llm`, `version_tag`)
use the corresponding `livespec/types.py` NewType
(`CheckId`, `RunId`, `TopicSlug`, `SpecRoot`, `SchemaId`,
`TemplateName`, `Author`, `VersionTag`). Note: `template_root`
is the resolved-directory `Path`, NOT `TemplateName`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NEWTYPE_DOMAIN_PRIMITIVES = _REPO_ROOT / "dev-tooling" / "checks" / "newtype_domain_primitives.py"


def test_newtype_domain_primitives_rejects_canonical_field_with_raw_type(
    *,
    tmp_path: Path,
) -> None:
    """A dataclass field named `check_id` annotated `str` (not `CheckId`) fails the check."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    check_id: str\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"newtype_domain_primitives should reject str-typed `check_id` field; "
        f"got returncode={result.returncode}"
    )
    combined = result.stdout + result.stderr
    assert "check_id" in combined, (
        f"diagnostic does not surface offending field `check_id`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_accepts_canonical_field_with_newtype(
    *,
    tmp_path: Path,
) -> None:
    """A `check_id: CheckId` field passes the check."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "from livespec.types import CheckId\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    check_id: CheckId\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should accept CheckId-typed `check_id`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_ignores_non_canonical_field_name(
    *,
    tmp_path: Path,
) -> None:
    """A field with a non-canonical name (e.g., `name: str`) is ignored."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    name: str\n"
        "    age: int\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should ignore non-canonical fields; "
        f"got returncode={result.returncode}"
    )


def test_newtype_domain_primitives_skips_class_body_methods_and_docstrings(
    *,
    tmp_path: Path,
) -> None:
    """Class-body statements that aren't AnnAssign are skipped.

    Closes the `if not (isinstance(stmt, AnnAssign) and ...):
    continue` branch. Fixture has a docstring, a method, and
    one valid AnnAssign so the class body has all three.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "from livespec.types import CheckId\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        '    """Class docstring is an Expr — not an AnnAssign."""\n'
        "\n"
        "    check_id: CheckId\n"
        "\n"
        "    def helper(self) -> int:\n"  # FunctionDef body stmt
        "        return 0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should skip non-AnnAssign body stmts; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_ignores_template_root(*, tmp_path: Path) -> None:
    """`template_root` is resolved-directory Path, NOT TemplateName.

    Per the canonical row note: the L8 mapping is
    field-name keyed and `template_root` doesn't match
    `template`. So `template_root: Path` is fine.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "from pathlib import Path\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    template_root: Path\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should ignore `template_root: Path`; "
        f"got returncode={result.returncode}"
    )


def test_newtype_domain_primitives_accepts_canonical_field_with_optional_newtype(
    *,
    tmp_path: Path,
) -> None:
    """A `author: Author | None` field passes the check.

    The `| None` only marks the field as optional; the inner
    type (`Author`) is the canonical NewType. The check peels
    `X | None` shapes (PEP 604 unions) before comparing.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "from livespec.types import Author\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    author: Author | None\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should accept `author: Author | None`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_accepts_canonical_field_with_optional_newtype_left_none(
    *,
    tmp_path: Path,
) -> None:
    """A `author: None | Author` field also passes (None on the left arm)."""
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "from livespec.types import Author\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    author: None | Author\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should accept `author: None | Author`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_rejects_optional_with_raw_type(
    *,
    tmp_path: Path,
) -> None:
    """A `author: str | None` (optional but raw str inner) fails the check.

    Asserts the peel logic doesn't accidentally pass `X | None`
    when X itself is wrong; only `Author | None` (correct inner)
    should pass.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    author: str | None\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"newtype_domain_primitives should reject `author: str | None`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "author" in combined, (
        f"diagnostic does not surface offending field `author`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_rejects_canonical_field_with_non_optional_union(
    *,
    tmp_path: Path,
) -> None:
    """A `check_id: str | int` (BinOp BitOr but neither arm is None Constant) falls through.

    Covers the branch where the optional-peel logic detects a
    `BinOp` with `BitOr` op but neither arm is a `None` literal —
    the rendered annotation flows to `ast.unparse` and rsplit
    rather than being peeled. Result: `str | int` ≠ `CheckId`, so
    the check rejects.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    package_dir.mkdir(parents=True)
    source = package_dir / "foo.py"
    source.write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        "__all__: list[str] = []\n"
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Foo:\n"
        "    check_id: str | int\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"newtype_domain_primitives should reject `check_id: str | int`; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should accept empty tree; "
        f"got returncode={result.returncode}"
    )


def test_newtype_domain_primitives_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "newtype_domain_primitives_for_import_test",
        str(_NEWTYPE_DOMAIN_PRIMITIVES),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
