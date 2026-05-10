"""Outside-in tests for `dev-tooling/implementation/check_gap_tracking.py`.

Per `SPECIFICATION/non-functional-requirements.md` §Constraints
§"Beads invariants" #2 ("Gap-id ↔ beads-label exactly-once
invariant"): every gap id appearing in
`implementation-gaps/current.json` MUST correspond to exactly
one beads issue across all statuses. Zero matches fails;
two-or-more matches fails; exactly one passes.

Two test families:

1. **End-to-end smoke tests** — invoke the script via
   `subprocess.run` against a `tmp_path` with a fake `bd`
   shell stub on PATH. The fake bd returns a configurable
   JSON payload, exercising the 0/1/2-match cases against the
   real subprocess plumbing.

2. **Branch-coverage unit tests** — import `check_gap_tracking`
   directly and call `main()` (or the helpers) with cwd
   scoped to `tmp_path` and `subprocess.run` monkeypatched to
   exercise error paths (missing report, malformed report,
   non-list gaps field, malformed gap entries, bd query
   failures, malformed bd JSON output, etc.).

The script defaults to `Path.cwd()` for its file lookups, so
all tests scope cwd via `monkeypatch.chdir` or
`subprocess.run(cwd=...)` to keep the live repo untouched.

The fake-bd stub installs at `tmp_path/bin/bd`; the test PATH
deliberately omits any directory that contains a real `mise`
binary so `_resolve_bd()` falls through to the bare `bd`
branch and finds the stub. Otherwise `mise exec -- bd ...`
would shell out to the real beads database.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK = _REPO_ROOT / "dev-tooling" / "implementation" / "check_gap_tracking.py"
_SCHEMA_SRC = _REPO_ROOT / "implementation-gaps" / "current.schema.json"


def _build_report(*, gaps: list[dict[str, object]]) -> dict[str, object]:
    """Assemble a schema-conforming report wrapper around the supplied gaps list.

    The check itself only reads `report["gaps"]`, so most surrounding fields
    could be omitted; we keep them schema-shaped for readability and to leave
    room for future changes that pull on additional fields.
    """
    return {
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
        "gaps": gaps,
        "summary": {
            "by_area": {},
            "by_severity": {},
            "by_status": {"open": len(gaps)},
        },
    }


def _make_gap_entry(*, gap_id: str) -> dict[str, object]:
    """Minimal gaps[] entry — every required Gap-schema field, deterministic content."""
    return {
        "id": gap_id,
        "area": "tests",
        "severity": "missing",
        "title": f"fixture gap {gap_id}",
        "spec_refs": ["non-functional-requirements.md#beads-invariants"],
        "expected": "fixture",
        "observed": "fixture",
        "evidence": ["fixture"],
        "evidence_kind": "absent",
        "destructive_to_fix": False,
        "destructive_reason": None,
        "fix_hint": "fixture",
        "depends_on": [],
    }


def _write_fixture(*, root: Path, gaps: list[dict[str, object]]) -> None:
    """Write `implementation-gaps/current.json` (and the sibling schema) under `root`."""
    gaps_dir = root / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.schema.json").write_text(
        _SCHEMA_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (gaps_dir / "current.json").write_text(
        json.dumps(_build_report(gaps=gaps)),
        encoding="utf-8",
    )


def _install_fake_bd(
    *,
    tmp_path: Path,
    stdout: str = "[]",
    returncode: int = 0,
) -> str:
    """Install a fake `bd` shell stub at `tmp_path/bin/bd`.

    Returns a PATH string suitable for `env=` injection that includes the
    fake-bd dir + the standard system bin dirs (so /bin/sh resolves) but
    deliberately excludes any directory that holds a real `mise` binary.
    `_resolve_bd()` therefore falls through to the bare `bd` branch and
    finds the stub.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bd_path = bin_dir / "bd"
    script = "#!/bin/sh\n" f"cat <<'STUB_EOF'\n{stdout}\nSTUB_EOF\n" f"exit {returncode}\n"
    _ = bd_path.write_text(script, encoding="utf-8")
    bd_path.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin"


def _run_subprocess(
    *,
    cwd: Path,
    env_path: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke check_gap_tracking.py under a controlled PATH; preserve other env."""
    env = {**os.environ, "PATH": env_path}
    return subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def check_module() -> Iterator[object]:
    """Import check_gap_tracking as a module for direct-call unit tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_gap_tracking", str(_CHECK))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_gap_tracking"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("check_gap_tracking", None)


def test_passes_when_every_gap_has_exactly_one_issue(*, tmp_path: Path) -> None:
    """Single-gap report + fake bd returning exactly one issue → exit 0."""
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0001")])
    env_path = _install_fake_bd(
        tmp_path=tmp_path,
        stdout=json.dumps([{"id": "li-aaa", "labels": ["gap-id:gap-0001"]}]),
    )
    result = _run_subprocess(cwd=tmp_path, env_path=env_path)
    assert (
        result.returncode == 0
    ), f"expected exit 0; got {result.returncode}, stderr={result.stderr!r}"
    assert "invariant holds" in result.stderr


def test_fails_when_gap_has_no_tracking_issue(*, tmp_path: Path) -> None:
    """Gap present in report but bd returns [] → exit 1."""
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0042")])
    env_path = _install_fake_bd(tmp_path=tmp_path, stdout="[]")
    result = _run_subprocess(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "no tracking beads issue" in result.stderr


def test_fails_when_gap_has_multiple_tracking_issues(*, tmp_path: Path) -> None:
    """Gap present in report and bd returns 2 issues → exit 1."""
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0042")])
    env_path = _install_fake_bd(
        tmp_path=tmp_path,
        stdout=json.dumps(
            [
                {"id": "li-aaa", "labels": ["gap-id:gap-0042"]},
                {"id": "li-bbb", "labels": ["gap-id:gap-0042"]},
            ],
        ),
    )
    result = _run_subprocess(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "multiple tracking beads issues" in result.stderr


def test_fails_when_bd_returns_non_zero(*, tmp_path: Path) -> None:
    """bd subprocess returns rc=1 → query treated as failed → exit 1."""
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0001")])
    env_path = _install_fake_bd(tmp_path=tmp_path, stdout="some error", returncode=1)
    result = _run_subprocess(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "bd query failed" in result.stderr


def test_passes_with_empty_gaps_list(*, tmp_path: Path) -> None:
    """An empty gaps list never asks bd anything → exit 0."""
    _write_fixture(root=tmp_path, gaps=[])
    env_path = _install_fake_bd(tmp_path=tmp_path)
    result = _run_subprocess(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0
    assert "invariant holds" in result.stderr


def test_fails_when_bd_unavailable(*, tmp_path: Path) -> None:
    """No bd anywhere on PATH → exit 1 with the bd-missing diagnostic.

    Both `mise` and `bd` must be absent from PATH for the bd-missing
    branch to fire. Standard `/usr/bin` and `/bin` carry a system
    `mise` on this host, so PATH must point at an empty fixture dir.
    """
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0001")])
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = {**os.environ, "PATH": str(empty_bin)}
    result = subprocess.run(
        [sys.executable, str(_CHECK)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1
    assert "bd not on PATH" in result.stderr


def test_main_warns_and_returns_zero_when_report_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """main() warns + returns 0 when implementation-gaps/current.json is absent."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: "/usr/bin/bd")
    assert check_module.main() == 0


def test_main_warns_and_returns_zero_when_report_malformed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """main() warns + returns 0 when current.json is not parseable JSON."""
    _write_fixture(root=tmp_path, gaps=[])
    (tmp_path / "implementation-gaps" / "current.json").write_text(
        "not json {",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: "/usr/bin/bd")
    assert check_module.main() == 0


def test_main_fails_when_gaps_field_is_not_a_list(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """main() returns 1 when report["gaps"] is not a JSON array."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text(
        json.dumps({"gaps": "not-a-list"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: "/usr/bin/bd")
    assert check_module.main() == 1


def test_main_fails_when_gap_entry_is_not_a_dict(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """main() returns 1 when a gaps[] element is a string instead of an object."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text(
        json.dumps({"gaps": ["not-a-dict"]}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: "/usr/bin/bd")
    assert check_module.main() == 1


def test_main_fails_when_gap_entry_id_missing_or_non_string(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """main() returns 1 when a gaps[] entry has no string id field."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text(
        json.dumps({"gaps": [{"id": 42}]}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: "/usr/bin/bd")
    assert check_module.main() == 1


def test_resolve_bd_prefers_mise_when_available(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_resolve_bd returns the mise-prefixed argv when mise is present on PATH."""
    monkeypatch.setattr(
        check_module.shutil,
        "which",
        lambda name: "/fake/mise" if name == "mise" else None,
    )
    argv = check_module._resolve_bd()  # noqa: SLF001
    assert argv == ["/fake/mise", "exec", "--", "bd"]


def test_resolve_bd_falls_back_to_bare_bd(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_resolve_bd returns bare-bd argv when mise is absent but bd is present."""
    monkeypatch.setattr(
        check_module.shutil,
        "which",
        lambda name: "/fake/bd" if name == "bd" else None,
    )
    argv = check_module._resolve_bd()  # noqa: SLF001
    assert argv == ["/fake/bd"]


def test_resolve_bd_returns_none_when_neither_present(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_resolve_bd returns None when neither mise nor bd is on PATH."""
    monkeypatch.setattr(check_module.shutil, "which", lambda _name: None)
    assert check_module._resolve_bd() is None  # noqa: SLF001


def test_bd_issues_with_label_handles_subprocess_error(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_bd_issues_with_label returns None when subprocess.run raises OSError."""

    def _raises(*_args: object, **_kwargs: object) -> object:
        raise OSError("simulated subprocess failure")

    monkeypatch.setattr(check_module.subprocess, "run", _raises)
    result = check_module._bd_issues_with_label(  # noqa: SLF001
        bd_argv=["bd"],
        label="gap-id:gap-0001",
    )
    assert result is None


def test_bd_issues_with_label_handles_malformed_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_bd_issues_with_label returns None when bd's stdout is not parseable JSON."""

    class _StubResult:
        returncode = 0
        stdout = "not json {"

    monkeypatch.setattr(check_module.subprocess, "run", lambda *_a, **_kw: _StubResult())
    result = check_module._bd_issues_with_label(  # noqa: SLF001
        bd_argv=["bd"],
        label="gap-id:gap-0001",
    )
    assert result is None


def test_bd_issues_with_label_handles_non_list_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_bd_issues_with_label returns None when bd's stdout parses to a non-list."""

    class _StubResult:
        returncode = 0
        stdout = json.dumps({"not": "a list"})

    monkeypatch.setattr(check_module.subprocess, "run", lambda *_a, **_kw: _StubResult())
    result = check_module._bd_issues_with_label(  # noqa: SLF001
        bd_argv=["bd"],
        label="gap-id:gap-0001",
    )
    assert result is None


def test_bd_issues_with_label_treats_empty_stdout_as_empty_list(
    *,
    monkeypatch: pytest.MonkeyPatch,
    check_module: object,
) -> None:
    """_bd_issues_with_label returns [] (a real result) when bd emits empty stdout."""

    class _StubResult:
        returncode = 0
        stdout = "   \n"

    monkeypatch.setattr(check_module.subprocess, "run", lambda *_a, **_kw: _StubResult())
    result = check_module._bd_issues_with_label(  # noqa: SLF001
        bd_argv=["bd"],
        label="gap-id:gap-0001",
    )
    assert result == []


def test_check_gap_tracking_module_importable_without_running_main() -> None:
    """The check_gap_tracking module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_gap_tracking_for_import_test",
        str(_CHECK),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
