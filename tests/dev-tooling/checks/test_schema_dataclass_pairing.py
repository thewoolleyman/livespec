"""Outside-in test for `dev-tooling/checks/schema_dataclass_pairing.py` — schema→dataclass→validator triplet pairing.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-schema-dataclass-pairing` row), for
every `.claude-plugin/scripts/livespec/schemas/*.schema.json`,
the check verifies a paired dataclass at
`schemas/dataclasses/<name>.py` AND a paired validator at
`validate/<name>.py` exists.

Cycle 170 (minimum-viable) implements the file-presence
triplet check. Subsequent cycles add field-by-field type
verification (the v013 M6 three-way walker).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_DATACLASS_PAIRING = (
    _REPO_ROOT / "dev-tooling" / "checks" / "schema_dataclass_pairing.py"
)


def test_schema_dataclass_pairing_rejects_missing_dataclass(*, tmp_path: Path) -> None:
    """A schema file without a paired dataclass fails the check."""
    schemas_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "foo.schema.json").write_text("{}", encoding="utf-8")
    # Validator exists but not the dataclass.
    validate_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "validate"
    validate_dir.mkdir(parents=True)
    (validate_dir / "foo.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"schema_dataclass_pairing should reject missing dataclass; "
        f"got returncode={result.returncode}"
    )
    combined = result.stdout + result.stderr
    assert "foo" in combined, (
        f"diagnostic does not surface offending name `foo`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_schema_dataclass_pairing_rejects_missing_validator(*, tmp_path: Path) -> None:
    """A schema file without a paired validator fails the check."""
    schemas_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "foo.schema.json").write_text("{}", encoding="utf-8")
    # Dataclass exists but not the validator.
    dataclass_dir = (
        tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas" / "dataclasses"
    )
    dataclass_dir.mkdir(parents=True)
    (dataclass_dir / "foo.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"schema_dataclass_pairing should reject missing validator; "
        f"got returncode={result.returncode}"
    )


def test_schema_dataclass_pairing_accepts_complete_triplet(*, tmp_path: Path) -> None:
    """A schema with both paired dataclass and validator passes (exit 0)."""
    schemas_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "foo.schema.json").write_text("{}", encoding="utf-8")
    dataclass_dir = schemas_dir / "dataclasses"
    dataclass_dir.mkdir()
    (dataclass_dir / "foo.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )
    validate_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "validate"
    validate_dir.mkdir(parents=True)
    (validate_dir / "foo.py").write_text(
        "from __future__ import annotations\n__all__: list[str] = []\n",
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"schema_dataclass_pairing should accept complete triplet; "
        f"got returncode={result.returncode}"
    )


def test_schema_dataclass_pairing_accepts_empty_tree(*, tmp_path: Path) -> None:
    """An empty repo cwd passes (exit 0)."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"schema_dataclass_pairing should accept empty tree; "
        f"got returncode={result.returncode}"
    )


def test_schema_dataclass_pairing_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "schema_dataclass_pairing_for_import_test",
        str(_SCHEMA_DATACLASS_PAIRING),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
