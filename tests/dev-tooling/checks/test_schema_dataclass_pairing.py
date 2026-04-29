"""Outside-in test for `dev-tooling/checks/schema_dataclass_pairing.py`.

Per `python-skill-script-style-requirements.md` line 2083:

    AST (three-way walker per v013 M6): for every
    `schemas/*.schema.json`, verifies a paired dataclass at
    `schemas/dataclasses/<name>.py` (the `$id`-derived name) AND
    a paired validator at `validate/<name>.py` exists; every
    listed schema field matches the dataclass's Python type;
    vice versa in all three walks. Drift in any direction fails.

Cycle 48 pins ONE narrow violation per v032 D1
one-pattern-per-cycle: the **dataclass-without-schema**
direction. A `livespec/schemas/dataclasses/<name>.py` whose
corresponding `livespec/schemas/<name>.schema.json` does NOT
exist is rejected. The other two directions (schema-without-
dataclass, dataclass-without-validator) and field-by-field
type matching are deferred to subsequent cycles per v032 D1.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_DATACLASS_PAIRING = _REPO_ROOT / "dev-tooling" / "checks" / "schema_dataclass_pairing.py"


def test_schema_dataclass_pairing_rejects_dataclass_without_schema(*, tmp_path: Path) -> None:
    """A dataclass file with no paired schema is rejected.

    Fixture: `livespec/schemas/dataclasses/orphan.py` exists; no
    `livespec/schemas/orphan.schema.json`. The check must walk
    the dataclasses directory, observe the missing schema, exit
    non-zero, and surface the offending dataclass path.
    """
    schemas_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas"
    dataclasses_dir = schemas_dir / "dataclasses"
    dataclasses_dir.mkdir(parents=True)
    (dataclasses_dir / "orphan.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        '__all__: list[str] = ["Orphan"]\n'
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Orphan:\n"
        "    name: str\n",
        encoding="utf-8",
    )
    # Note: NO schemas/orphan.schema.json on purpose; that's the violation.

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"schema_dataclass_pairing should reject dataclass without schema; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/schemas/dataclasses/orphan.py"
    assert expected_path in combined, (
        f"schema_dataclass_pairing diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_schema_dataclass_pairing_accepts_dataclass_with_paired_schema(
    *,
    tmp_path: Path,
) -> None:
    """A dataclass with a paired schema file is accepted.

    Fixture: both `livespec/schemas/dataclasses/widget.py` and
    `livespec/schemas/widget.schema.json` exist. The check must
    walk the dataclasses tree, see the paired schema, and exit 0.
    """
    schemas_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec" / "schemas"
    dataclasses_dir = schemas_dir / "dataclasses"
    dataclasses_dir.mkdir(parents=True)
    (dataclasses_dir / "widget.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass\n"
        "\n"
        '__all__: list[str] = ["Widget"]\n'
        "\n"
        "\n"
        "@dataclass(frozen=True, kw_only=True, slots=True)\n"
        "class Widget:\n"
        "    name: str\n",
        encoding="utf-8",
    )
    (schemas_dir / "widget.schema.json").write_text(
        '{"$id": "widget", "type": "object"}\n',
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCHEMA_DATACLASS_PAIRING)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"schema_dataclass_pairing should accept dataclass with paired schema; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
