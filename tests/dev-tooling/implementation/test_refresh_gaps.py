"""Outside-in tests for `dev-tooling/implementation/refresh_gaps.py`.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow" + §"Implementation-gap
report shape", `refresh-gaps` produces
`implementation-gaps/current.json` from a static walk of the
spec + repo. The output MUST validate against
`implementation-gaps/current.schema.json`, with a fresh
`run_id` per invocation.

Two test families:

1. **End-to-end smoke tests** — invoke the script via
   `subprocess.run` against a minimal fixture under
   `tmp_path`. These confirm the script works as a standalone
   program (the canonical invocation surface — `just
   implementation::refresh-gaps`, the SKILL.md, direct
   `python3` calls).

2. **Branch-coverage unit tests** — import `refresh_gaps`
   directly and call `main()` (or its helpers) with
   `monkeypatch.chdir(tmp_path)` and other monkeypatches to
   exercise error paths (missing spec file, missing schema,
   malformed schema, gap-0005 / gap-0006 predicate variants,
   blueprint-vs-predicate-registry mismatch).

The script defaults to `Path.cwd()` for repo-root discovery,
so all tests scope cwd via `monkeypatch.chdir` or
`subprocess.run(cwd=...)` to keep the live repo untouched
(per the project rule that cwd-default tests MUST scope cwd
explicitly).
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
_REFRESH_GAPS = _REPO_ROOT / "dev-tooling" / "implementation" / "refresh_gaps.py"
_SCHEMA_SRC = _REPO_ROOT / "implementation-gaps" / "current.schema.json"
_VENDOR_SRC = _REPO_ROOT / ".claude-plugin" / "scripts" / "_vendor"

_SPEC_FILES = (
    "spec.md",
    "contracts.md",
    "constraints.md",
    "scenarios.md",
    "non-functional-requirements.md",
)


def _build_minimal_fixture(*, root: Path) -> None:
    """Construct a minimal repo-shape under root.

    The fixture has just enough for the script's happy path:
    SPECIFICATION/ with the five spec files, the
    implementation-gaps/ schema copy, and a vendored copy of
    structlog + fastjsonschema reachable via the script's
    vendor-path import (resolved relative to the SCRIPT's path,
    not cwd, so no symlink is needed in the fixture).
    """
    spec_dir = root / "SPECIFICATION"
    spec_dir.mkdir(parents=True)
    for name in _SPEC_FILES:
        (spec_dir / name).write_text(f"# {name}\n\nstub for tests\n", encoding="utf-8")

    gaps_dir = root / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.schema.json").write_text(
        _SCHEMA_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


@pytest.fixture
def refresh_gaps_module() -> Iterator[object]:
    """Import refresh_gaps as a module for direct-call unit tests.

    The module loads vendored deps via sys.path manipulation at
    import time; calling main() and helpers in-process gives
    line+branch coverage that subprocess invocation cannot
    measure (pytest-cov's pth-installed startup hook works for
    children but not as deeply as direct import).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("refresh_gaps", str(_REFRESH_GAPS))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["refresh_gaps"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("refresh_gaps", None)


def test_refresh_gaps_writes_schema_valid_report(*, tmp_path: Path) -> None:
    """Running refresh_gaps via subprocess in a minimal repo emits a schema-valid current.json (exit 0)."""
    _build_minimal_fixture(root=tmp_path)

    result = subprocess.run(
        [sys.executable, str(_REFRESH_GAPS)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"refresh_gaps should exit 0 on minimal repo; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    report_path = tmp_path / "implementation-gaps" / "current.json"
    assert report_path.is_file(), "refresh_gaps did not write current.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    for top_level_field in (
        "schema_version",
        "generated_at",
        "spec_sources",
        "inspection",
        "gaps",
        "summary",
    ):
        assert top_level_field in report, (
            f"report missing required top-level field {top_level_field!r}; "
            f"got keys {sorted(report.keys())!r}"
        )

    assert report["schema_version"] == 1
    for spec_key in (
        "spec_md",
        "contracts_md",
        "constraints_md",
        "scenarios_md",
        "non_functional_requirements_md",
    ):
        entry = report["spec_sources"][spec_key]
        assert "path" in entry and "git_blob_sha" in entry
        assert len(entry["git_blob_sha"]) == 40

    run_id = report["inspection"]["run_id"]
    assert len(run_id) == 36 and run_id.count("-") == 4


def test_refresh_gaps_run_id_changes_per_invocation(*, tmp_path: Path) -> None:
    """Two consecutive subprocess runs produce different run_id values (UUID4 freshness)."""
    _build_minimal_fixture(root=tmp_path)

    def _run_and_read_run_id() -> str:
        result = subprocess.run(
            [sys.executable, str(_REFRESH_GAPS)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            check=False,
        )
        assert (
            result.returncode == 0
        ), f"refresh_gaps should exit 0; got {result.returncode} stderr={result.stderr!r}"
        report = json.loads(
            (tmp_path / "implementation-gaps" / "current.json").read_text(encoding="utf-8"),
        )
        return report["inspection"]["run_id"]

    first = _run_and_read_run_id()
    second = _run_and_read_run_id()
    assert first != second, f"run_id should differ between invocations; got {first} twice"


def test_refresh_gaps_main_returns_zero_on_minimal_repo(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """Direct main() call returns 0 on a minimal repo (covers main()'s happy path)."""
    _build_minimal_fixture(root=tmp_path)
    monkeypatch.chdir(tmp_path)
    assert refresh_gaps_module.main() == 0
    assert (tmp_path / "implementation-gaps" / "current.json").is_file()


def test_refresh_gaps_main_errors_on_missing_spec_file(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """main() returns 1 when a SPECIFICATION/ file is absent."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "SPECIFICATION" / "spec.md").unlink()
    monkeypatch.chdir(tmp_path)
    assert refresh_gaps_module.main() == 1


def test_refresh_gaps_main_errors_on_missing_schema(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """main() returns 1 when implementation-gaps/current.schema.json is absent."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").unlink()
    monkeypatch.chdir(tmp_path)
    assert refresh_gaps_module.main() == 1


def test_refresh_gaps_main_errors_on_malformed_schema(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """main() returns 1 when the schema file is not valid JSON."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").write_text(
        "this is not json {",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert refresh_gaps_module.main() == 1


def test_refresh_gaps_main_errors_on_invalid_schema_definition(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """main() returns 1 when the schema is parseable JSON but invalid as a JSON Schema."""
    _build_minimal_fixture(root=tmp_path)
    (tmp_path / "implementation-gaps" / "current.schema.json").write_text(
        json.dumps({"type": "definitely-not-a-real-type"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert refresh_gaps_module.main() == 1


def test_refresh_gaps_main_errors_when_report_fails_validation(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """main() returns 1 when the produced report fails the schema (refresh_gaps own bug guard).

    Forced by monkeypatching `_build_report` to return a structurally-invalid
    object (e.g., schema_version 99 — the schema pins it to const 1).
    """
    _build_minimal_fixture(root=tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        refresh_gaps_module,
        "_build_report",
        lambda *, cwd: {"schema_version": 99, "wrong_shape": True},  # noqa: ARG005
    )
    assert refresh_gaps_module.main() == 1


def test_refresh_gaps_skips_blueprint_with_unmapped_predicate(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """`_build_report` skips any blueprint whose id has no entry in `_PRESENCE_PREDICATES`."""
    _build_minimal_fixture(root=tmp_path)
    monkeypatch.chdir(tmp_path)
    fake = {"id": "gap-9999", "area": "spec", "severity": "drift"}
    monkeypatch.setattr(refresh_gaps_module, "_load_blueprints", lambda: [fake])
    report = refresh_gaps_module._build_report(cwd=tmp_path)  # noqa: SLF001
    assert report["gaps"] == []


def test_skill_manual_fallback_predicate_fires_when_present(
    *,
    tmp_path: Path,
    refresh_gaps_module: object,
) -> None:
    """gap-0005 predicate returns True when any SKILL.md file carries the manual-fallback section."""
    skill_dir = tmp_path / ".claude" / "skills" / "livespec-implementation-beads:refresh-gaps"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# refresh-gaps\n\n## Manual fallback (current state)\n\nRun by hand.\n",
        encoding="utf-8",
    )
    assert refresh_gaps_module._any_skill_has_manual_fallback(tmp_path) is True  # noqa: SLF001


def test_skill_manual_fallback_predicate_silent_on_clean_skills(
    *,
    tmp_path: Path,
    refresh_gaps_module: object,
) -> None:
    """gap-0005 predicate returns False when no SKILL.md has the manual-fallback section."""
    skill_dir = tmp_path / ".claude" / "skills" / "livespec-implementation-beads:plan"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# plan\n\nNo fallback section.\n", encoding="utf-8")
    assert refresh_gaps_module._any_skill_has_manual_fallback(tmp_path) is False  # noqa: SLF001


def test_beads_config_predicate_silent_when_git_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """gap-0006 predicate returns False when git is not available on PATH."""
    monkeypatch.setattr(refresh_gaps_module.shutil, "which", lambda _name: None)
    assert refresh_gaps_module._beads_config_tracked(tmp_path) is False  # noqa: SLF001


def test_beads_config_predicate_silent_on_subprocess_error(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """gap-0006 predicate returns False when the `git ls-files` subprocess raises OSError."""

    def _raises(*_args: object, **_kwargs: object) -> object:
        raise OSError("simulated git failure")

    monkeypatch.setattr(refresh_gaps_module.shutil, "which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(refresh_gaps_module.subprocess, "run", _raises)
    assert refresh_gaps_module._beads_config_tracked(tmp_path) is False  # noqa: SLF001


def test_beads_config_predicate_fires_when_tracked_and_not_gitignored(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """gap-0006 predicate returns True when git ls-files reports the file AND .gitignore omits it."""

    class _StubResult:
        returncode = 0
        stdout = ".beads/config.yaml\n"

    monkeypatch.setattr(refresh_gaps_module.shutil, "which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        refresh_gaps_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(),
    )
    (tmp_path / ".gitignore").write_text("# unrelated comment\nnode_modules/\n", encoding="utf-8")
    assert refresh_gaps_module._beads_config_tracked(tmp_path) is True  # noqa: SLF001


def test_beads_config_predicate_fires_when_no_gitignore_file(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """gap-0006 predicate returns True when there is no .gitignore at all (covers 153→157 arc)."""

    class _StubResult:
        returncode = 0
        stdout = ".beads/config.yaml\n"

    monkeypatch.setattr(refresh_gaps_module.shutil, "which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        refresh_gaps_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(),
    )
    assert refresh_gaps_module._beads_config_tracked(tmp_path) is True  # noqa: SLF001


def test_beads_config_predicate_silent_when_gitignored(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    refresh_gaps_module: object,
) -> None:
    """gap-0006 predicate returns False when .gitignore lists `.beads/config.yaml`."""

    class _StubResult:
        returncode = 0
        stdout = ".beads/config.yaml\n"

    monkeypatch.setattr(refresh_gaps_module.shutil, "which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        refresh_gaps_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(),
    )
    (tmp_path / ".gitignore").write_text(".beads/config.yaml\n", encoding="utf-8")
    assert refresh_gaps_module._beads_config_tracked(tmp_path) is False  # noqa: SLF001


def testrefresh_gaps_module_importable_without_running_main() -> None:
    """The refresh_gaps module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "refresh_gaps_for_import_test",
        str(_REFRESH_GAPS),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
