"""Outside-in test for `dev-tooling/checks/newtype_domain_primitives.py`.

Per `python-skill-script-style-requirements.md` §"Domain primitives via
`NewType`" (lines 962-1010) and the canonical-target table line 2090:

    AST: walks `schemas/dataclasses/*.py` and function signatures;
    verifies field annotations matching canonical field names use
    the corresponding `livespec/types.py` NewType. Field-name
    keyed mapping table (lines 975-984): `check_id`→`CheckId`,
    `run_id`→`RunId`, `topic`→`TopicSlug`, `spec_root`→`SpecRoot`,
    `schema_id`→`SchemaId`, `template`→`TemplateName`,
    `author`/`author_human`/`author_llm`→`Author`,
    `version_tag`→`VersionTag`. Note that `template_root` is the
    resolved-directory `Path` and uses raw `Path`, NOT
    `TemplateName` — the L8 mapping is field-name keyed, and
    `template_root` doesn't match `template`.

Cycle 49 pins ONE narrow violation per v032 D1
one-pattern-per-cycle: a function-signature parameter named
`run_id` annotated with anything other than `RunId`. The other
seven canonical field-name → NewType mappings, and the
dataclass-field walk, are deferred to subsequent cycles.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_NEWTYPE_DOMAIN_PRIMITIVES = _REPO_ROOT / "dev-tooling" / "checks" / "newtype_domain_primitives.py"


def test_newtype_domain_primitives_rejects_run_id_annotated_str(*, tmp_path: Path) -> None:
    """A function param named `run_id` annotated `str` (not `RunId`) is rejected.

    Fixture: `livespec/correlate.py` defines a function with a
    keyword-only parameter `run_id: str`. The check must walk
    the livespec tree, detect the wrong-NewType param annotation,
    exit non-zero, and surface the offending module path.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "correlate.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        '__all__: list[str] = ["correlate"]\n'
        "\n"
        "\n"
        "def correlate(*, run_id: str) -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"newtype_domain_primitives should reject run_id: str (expected RunId); "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    expected_path = ".claude-plugin/scripts/livespec/correlate.py"
    assert expected_path in combined, (
        f"newtype_domain_primitives diagnostic does not surface offending path "
        f"`{expected_path}`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_newtype_domain_primitives_accepts_run_id_annotated_runid(
    *,
    tmp_path: Path,
) -> None:
    """A function param `run_id: RunId` is accepted.

    Fixture: `livespec/correlate.py` defines a function with
    parameter `run_id: RunId`. The check walks, observes the
    canonical NewType, and exits 0.
    """
    package_dir = tmp_path / ".claude-plugin" / "scripts" / "livespec"
    package_dir.mkdir(parents=True)
    (package_dir / "correlate.py").write_text(
        "from __future__ import annotations\n"
        "\n"
        "from livespec.types import RunId\n"
        "\n"
        '__all__: list[str] = ["correlate"]\n'
        "\n"
        "\n"
        "def correlate(*, run_id: RunId) -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_NEWTYPE_DOMAIN_PRIMITIVES)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"newtype_domain_primitives should accept run_id: RunId; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
