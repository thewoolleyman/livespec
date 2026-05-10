"""Outside-in tests for `dev-tooling/implementation/check_gaps.py`.

Per `SPECIFICATION/non-functional-requirements.md` §Contracts
§"Implementation-gap report shape", `check-gaps` validates that
`implementation-gaps/current.json` conforms to
`implementation-gaps/current.schema.json` via JSON Schema.
Exit 0 on full conformance; exit 1 on any violation (or when
either file is missing or malformed).

Two test families:

1. **End-to-end smoke tests** — invoke the script via
   `subprocess.run` against a minimal fixture under `tmp_path`.
   These confirm the script works as a standalone program (the
   canonical invocation surface — `just
   implementation::check-gaps`, the SKILL.md, direct `python3`
   calls).

2. **Branch-coverage unit tests** — import `check_gaps` directly
   and call `main()` with `monkeypatch.chdir(tmp_path)` to
   exercise every error path (missing schema / report,
   malformed JSON in either, schema-itself-invalid, report
   fails validation).

The script defaults to `Path.cwd()` for its file lookups, so all
tests scope cwd via `monkeypatch.chdir` or `subprocess.run(cwd=...)`
to keep the live repo untouched (per the project rule that
cwd-default tests MUST scope cwd explicitly).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_GAPS = _REPO_ROOT / "dev-tooling" / "implementation" / "check_gaps.py"
_SCHEMA_SRC = _REPO_ROOT / "implementation-gaps" / "current.schema.json"


def _build_minimal_fixture(*, root: Path) -> None:
    """Construct the minimum file layout check_gaps needs.

    Copies the live schema in so the report is validated against
    the real shape. The report defaults to a schema-conforming
    empty document; callers overwrite the file post-build to
    exercise error paths.
    """
    gaps_dir = root / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.schema.json").write_text(
        _SCHEMA_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    report = {
        "$schema": "./current.schema.json",
        "schema_version": 1,
        "generated_at": "2026-05-10T00:00:00Z",
        "spec_sources": {
            key: {
                "path": f"SPECIFICATION/{filename}",
                "git_blob_sha": "0" * 40,
            }
            for key, filename in (
                ("spec_md", "spec.md"),
                ("contracts_md", "contracts.md"),
                ("constraints_md", "constraints.md"),
                ("scenarios_md", "scenarios.md"),
                ("non_functional_requirements_md", "non-functional-requirements.md"),
            )
        },
        "inspection": {
            "scopes_inspected": ["SPECIFICATION/"],
            "scopes_skipped": [],
            "run_id": "00000000-0000-4000-8000-000000000000",
            "inspection_method": "test fixture",
        },
        "gaps": [],
        "summary": {
            "by_area": {},
            "by_severity": {},
            "by_status": {"open": 0},
        },
    }
    (gaps_dir / "current.json").write_text(json.dumps(report), encoding="utf-8")


@pytest.fixture
def check_gaps_module() -> Iterator[object]:
    """Import check_gaps as a module for direct-call unit tests.

    The module loads vendored deps (fastjsonschema, structlog) via
    sys.path manipulation at import time; calling main() in-process
    gives line+branch coverage that subprocess invocation cannot
    measure.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_gaps", str(_CHECK_GAPS))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_gaps"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("check_gaps", None)


def test_check_gaps_passes_on_minimal_valid_report(*, tmp_path: Path) -> None:
    """A schema-conforming empty report exits 0 with the conformance log."""
    _build_minimal_fixture(root=tmp_path)
    result = subprocess.run(
        [sys.executable, str(_CHECK_GAPS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"expected exit 0; got {result.returncode}, "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "conforms to schema" in result.stderr


def test_check_gaps_subprocess_fails_when_schema_missing(*, tmp_path: Path) -> None:
    """Removing the schema file produces exit 1 with the schema-missing diagnostic."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").unlink()
    result = subprocess.run(
        [sys.executable, str(_CHECK_GAPS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "schema missing or malformed" in result.stderr


def test_check_gaps_main_fails_when_report_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_gaps_module: object,
) -> None:
    """main() returns 1 when implementation-gaps/current.json is absent."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.json").unlink()
    monkeypatch.chdir(tmp_path)
    assert check_gaps_module.main() == 1


def test_check_gaps_main_fails_when_schema_malformed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_gaps_module: object,
) -> None:
    """main() returns 1 when the schema file is not parseable JSON."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").write_text(
        "this is not json {",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert check_gaps_module.main() == 1


def test_check_gaps_main_fails_when_report_malformed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_gaps_module: object,
) -> None:
    """main() returns 1 when the report file is not parseable JSON."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.json").write_text(
        "this is not json {",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert check_gaps_module.main() == 1


def test_check_gaps_main_fails_when_schema_definition_invalid(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_gaps_module: object,
) -> None:
    """main() returns 1 when the schema parses as JSON but is invalid as a JSON Schema."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").write_text(
        json.dumps({"type": "definitely-not-a-real-type"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert check_gaps_module.main() == 1


def test_check_gaps_main_fails_when_report_violates_schema(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_gaps_module: object,
) -> None:
    """main() returns 1 when the report parses but fails JSON-Schema validation.

    The schema pins `schema_version` to `const: 1`; rewriting it to 99
    forces a JsonSchemaValueException through the validator.
    """
    _build_minimal_fixture(root=tmp_path)
    report_path = tmp_path / "implementation-gaps" / "current.json"
    bad_report = json.loads(report_path.read_text(encoding="utf-8"))
    bad_report["schema_version"] = 99
    report_path.write_text(json.dumps(bad_report), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert check_gaps_module.main() == 1


def test_check_gaps_module_importable_without_running_main() -> None:
    """The check_gaps module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_gaps_for_import_test",
        str(_CHECK_GAPS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
