"""Outside-in tests for `dev-tooling/implementation/implement.py`.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow", `implement` drives the
verify-and-close half of the gap-tied issue lifecycle: it
re-runs `refresh-gaps`, hard-refuses to close any issue whose
`gap-id` still appears in `implementation-gaps/current.json`,
and on success closes the issue with the four mandatory audit
fields (gap id / evidence / run_id / timestamp).

Two test families:

1. **End-to-end smoke tests** — invoke the script via
   `subprocess.run` against a `tmp_path` with a fake `bd`
   shell stub. Confirms list-ready stdout shape, the
   verify-and-close happy path, and the hard-refusal exit code
   when the gap-id remains in current.json.

2. **Branch-coverage unit tests** — import `implement` directly
   and call `main()` / helpers with cwd scoped to `tmp_path`,
   `subprocess.run` monkeypatched on the `_implement_bd`
   helpers, and the refresh-gaps subprocess monkeypatched at
   the seam.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_IMPLEMENT = _REPO_ROOT / "dev-tooling" / "implementation" / "implement.py"
_SCHEMA_SRC = _REPO_ROOT / "implementation-gaps" / "current.schema.json"


def _make_gap_entry(*, gap_id: str, title: str = "fixture gap") -> dict[str, object]:
    return {
        "id": gap_id,
        "area": "tests",
        "severity": "missing",
        "title": title,
        "spec_refs": ["non-functional-requirements.md#repo-local-implementation-workflow"],
        "expected": "fixture",
        "observed": "fixture",
        "evidence": ["fixture"],
        "evidence_kind": "absent",
        "destructive_to_fix": False,
        "destructive_reason": None,
        "fix_hint": "fixture",
        "depends_on": [],
    }


def _build_report(
    *,
    gaps: list[dict[str, object]],
    run_id: str = "11111111-2222-4333-8444-555555555555",
    generated_at: str = "2026-05-10T12:00:00Z",
) -> dict[str, object]:
    return {
        "$schema": "./current.schema.json",
        "schema_version": 1,
        "generated_at": generated_at,
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
            "run_id": run_id,
            "inspection_method": "test fixture",
        },
        "gaps": gaps,
        "summary": {
            "by_area": {},
            "by_severity": {},
            "by_status": {"open": len(gaps)},
        },
    }


def _write_fixture(
    *,
    root: Path,
    gaps: list[dict[str, object]],
    run_id: str = "11111111-2222-4333-8444-555555555555",
    generated_at: str = "2026-05-10T12:00:00Z",
) -> None:
    gaps_dir = root / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.schema.json").write_text(
        _SCHEMA_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (gaps_dir / "current.json").write_text(
        json.dumps(_build_report(gaps=gaps, run_id=run_id, generated_at=generated_at)),
        encoding="utf-8",
    )


def _install_recording_fake_bd_with_refresh(
    *,
    tmp_path: Path,
    ready_response: list[dict[str, object]] | None = None,
) -> tuple[str, Path]:
    """Install a fake `bd` shim AND a no-op `refresh-gaps` shim on a controlled PATH.

    Returns (PATH-string, log-path). The fake bd handles three sub-commands:

    - `ready --json` → emits `json.dumps(ready_response or [])`.
    - `update ...` and `close ...` → emit `{}` and exit 0.
    - any other sub-command → emit `{}` and exit 0.

    The PATH also routes the `python3` invocation that implement.py uses
    to call `dev-tooling/implementation/refresh_gaps.py` to a stub that
    just exits 0 (the test pre-writes current.json itself, so no real
    refresh is needed). Every invocation appends one JSON line to the
    log file.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_path = tmp_path / "bd-invocations.log"
    bd_path = bin_dir / "bd"
    ready_json = json.dumps(ready_response if ready_response is not None else [])
    bd_script = f"""#!{sys.executable}
import json, sys
log_path = {str(log_path)!r}
with open(log_path, "a") as fp:
    fp.write(json.dumps(sys.argv[1:]) + "\\n")
argv = sys.argv[1:]
if not argv:
    sys.exit(0)
if argv[0] == "ready":
    sys.stdout.write({ready_json!r} + "\\n")
else:
    sys.stdout.write("{{}}\\n")
sys.exit(0)
"""
    _ = bd_path.write_text(bd_script, encoding="utf-8")
    bd_path.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin", log_path


def _empty_path(*, tmp_path: Path) -> str:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir(exist_ok=True)
    return str(empty_bin)


def _run(
    *,
    cwd: Path,
    env_path: str,
    args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": env_path}
    return subprocess.run(
        [sys.executable, str(_IMPLEMENT), *(args or [])],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def implement_module() -> Iterator[object]:
    """Import implement as a module for direct-call unit tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("implement", str(_IMPLEMENT))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["implement"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("implement", None)


def test_default_mode_emits_ready_issue_list(*, tmp_path: Path) -> None:
    """No args → bd ready --json passthrough as a JSON array."""
    env_path, _ = _install_recording_fake_bd_with_refresh(
        tmp_path=tmp_path,
        ready_response=[{"id": "li-aaa", "title": "ready issue"}],
    )
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    parsed = json.loads(result.stdout)
    assert parsed == [{"id": "li-aaa", "title": "ready issue"}]


def test_default_mode_emits_empty_array_when_no_ready(*, tmp_path: Path) -> None:
    """bd ready returns [] → stdout is `[]`; exit 0."""
    env_path, _ = _install_recording_fake_bd_with_refresh(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert json.loads(result.stdout) == []


def test_fails_when_bd_unavailable(*, tmp_path: Path) -> None:
    """No bd on PATH → exit 1 with the bd-missing diagnostic."""
    _write_fixture(root=tmp_path, gaps=[])
    env_path = _empty_path(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "bd not on PATH" in result.stderr


def test_main_close_mode_hard_refuses_when_gap_still_present(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close fails fast when the named gap is still present in current.json."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-9999")],
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_close_mode_succeeds_when_gap_absent(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close runs bd update + bd close when the gap-id is gone from current.json."""
    _write_fixture(
        root=tmp_path,
        gaps=[],  # empty — gap-9999 is NOT present, so closure is allowed
        run_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        generated_at="2026-05-10T13:00:00Z",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    captured: dict[str, object] = {}

    def _fake_update(
        *,
        bd_argv: list[str],  # noqa: ARG001
        li_id: str,
        notes: str,
    ) -> bool:
        captured["update_li"] = li_id
        captured["notes"] = notes
        return True

    def _fake_close(
        *,
        bd_argv: list[str],  # noqa: ARG001
        li_id: str,
        reason: str,
    ) -> bool:
        captured["close_li"] = li_id
        captured["reason"] = reason
        return True

    monkeypatch.setattr(implement_module, "_bd_update_with_audit", _fake_update)
    monkeypatch.setattr(implement_module, "_bd_close_issue", _fake_close)

    rc = implement_module.main(
        argv=[
            "--close",
            "li-aaa",
            "--gap",
            "gap-9999",
            "--evidence",
            "tests landed via PR #X",
        ],
    )
    assert rc == 0
    assert captured["update_li"] == "li-aaa"
    assert captured["close_li"] == "li-aaa"
    notes = str(captured["notes"])
    assert "Gap id: gap-9999" in notes
    assert "Evidence: tests landed via PR #X" in notes
    assert "Verification run_id: aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee" in notes
    assert "Verification timestamp: 2026-05-10T13:00:00Z" in notes


def test_main_close_mode_fails_when_refresh_gaps_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when refresh-gaps subprocess returns non-zero."""
    _write_fixture(root=tmp_path, gaps=[])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: False,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-0001", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_close_mode_fails_when_bd_update_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when bd update (audit notes + label) fails."""
    _write_fixture(root=tmp_path, gaps=[])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    monkeypatch.setattr(
        implement_module,
        "_bd_update_with_audit",
        lambda *, bd_argv, li_id, notes: False,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_close_mode_fails_when_bd_close_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when bd close fails."""
    _write_fixture(root=tmp_path, gaps=[])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    monkeypatch.setattr(
        implement_module,
        "_bd_update_with_audit",
        lambda *, bd_argv, li_id, notes: True,  # noqa: ARG005
    )
    monkeypatch.setattr(
        implement_module,
        "_bd_close_issue",
        lambda *, bd_argv, li_id, reason: False,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_close_mode_fails_when_report_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when current.json is missing after refresh-gaps."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_close_mode_fails_when_gaps_field_not_list(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when report.gaps is not a JSON array."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text(
        json.dumps({"gaps": "not-a-list", "inspection": {}, "generated_at": "x"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    rc = implement_module.main(
        argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
    )
    assert rc == 1


def test_main_default_fails_when_bd_ready_query_fails(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """Default mode exits 1 when bd ready --json returns failure."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_bd_ready_issues",
        lambda *, bd_argv: None,  # noqa: ARG005
    )
    assert implement_module.main(argv=[]) == 1


def test_run_refresh_gaps_returns_true_on_success(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_run_refresh_gaps returns True when the subprocess exits 0."""

    class _R:
        returncode = 0

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._run_refresh_gaps(cwd=tmp_path) is True  # noqa: SLF001


def test_run_refresh_gaps_returns_false_on_nonzero_rc(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_run_refresh_gaps returns False when the subprocess exits non-zero."""

    class _R:
        returncode = 1

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._run_refresh_gaps(cwd=tmp_path) is False  # noqa: SLF001


def test_run_refresh_gaps_returns_false_on_oserror(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_run_refresh_gaps returns False when subprocess.run raises OSError."""

    def _raises(*_a: object, **_kw: object) -> object:
        raise OSError("simulated subprocess failure")

    monkeypatch.setattr(implement_module.subprocess, "run", _raises)
    assert implement_module._run_refresh_gaps(cwd=tmp_path) is False  # noqa: SLF001


def test_bd_ready_issues_returns_none_on_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_ready_issues returns None when the bd subprocess returns non-zero."""

    class _R:
        returncode = 1
        stdout = ""

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._bd_ready_issues(bd_argv=["bd"]) is None  # noqa: SLF001


def test_bd_ready_issues_returns_empty_on_empty_stdout(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_ready_issues returns [] when bd emits empty stdout."""

    class _R:
        returncode = 0
        stdout = "  \n"

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._bd_ready_issues(bd_argv=["bd"]) == []  # noqa: SLF001


def test_bd_ready_issues_returns_none_on_malformed_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_ready_issues returns None when stdout isn't parseable JSON."""

    class _R:
        returncode = 0
        stdout = "not json {"

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._bd_ready_issues(bd_argv=["bd"]) is None  # noqa: SLF001


def test_bd_ready_issues_returns_none_on_non_list_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_ready_issues returns None when stdout parses to a non-list."""

    class _R:
        returncode = 0
        stdout = json.dumps({"not": "list"})

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert implement_module._bd_ready_issues(bd_argv=["bd"]) is None  # noqa: SLF001


def test_bd_update_with_audit_returns_true_on_success(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_update_with_audit returns True when bd update succeeds."""

    class _R:
        returncode = 0

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert (
        implement_module._bd_update_with_audit(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            notes="audit",
        )
        is True
    )


def test_bd_update_with_audit_returns_false_on_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_update_with_audit returns False when bd update fails."""

    class _R:
        returncode = 1

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert (
        implement_module._bd_update_with_audit(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            notes="audit",
        )
        is False
    )


def test_bd_update_with_audit_returns_false_on_oserror(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_update_with_audit returns False when subprocess.run raises OSError."""

    def _raises(*_a: object, **_kw: object) -> object:
        raise OSError("simulated")

    monkeypatch.setattr(implement_module.subprocess, "run", _raises)
    assert (
        implement_module._bd_update_with_audit(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            notes="audit",
        )
        is False
    )


def test_bd_close_issue_returns_true_on_success(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_close_issue returns True when bd close succeeds."""

    class _R:
        returncode = 0

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert (
        implement_module._bd_close_issue(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            reason="ok",
        )
        is True
    )


def test_bd_close_issue_returns_false_on_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_close_issue returns False when bd close fails."""

    class _R:
        returncode = 1

    monkeypatch.setattr(implement_module.subprocess, "run", lambda *_a, **_kw: _R())
    assert (
        implement_module._bd_close_issue(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            reason="ok",
        )
        is False
    )


def test_bd_close_issue_returns_false_on_oserror(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_close_issue returns False when subprocess.run raises OSError."""

    def _raises(*_a: object, **_kw: object) -> object:
        raise OSError("simulated")

    monkeypatch.setattr(implement_module.subprocess, "run", _raises)
    assert (
        implement_module._bd_close_issue(  # noqa: SLF001
            bd_argv=["bd"],
            li_id="li-x",
            reason="ok",
        )
        is False
    )


def test_resolve_bd_prefers_mise(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_resolve_bd returns the mise-prefixed argv when mise is available."""
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/fake/mise" if name == "mise" else None,
    )
    assert implement_module._resolve_bd() == ["/fake/mise", "exec", "--", "bd"]  # noqa: SLF001


def test_resolve_bd_falls_back_to_bare_bd(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_resolve_bd returns the bare-bd argv when only bd is available."""
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/fake/bd" if name == "bd" else None,
    )
    assert implement_module._resolve_bd() == ["/fake/bd"]  # noqa: SLF001


def test_resolve_bd_returns_none_when_neither_present(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_resolve_bd returns None when neither tool is on PATH."""
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert implement_module._resolve_bd() is None  # noqa: SLF001


def test_main_close_mode_fails_when_report_malformed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close exits 1 when current.json is unparseable JSON after refresh-gaps."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text("not json {", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        implement_module,
        "_run_refresh_gaps",
        lambda *, cwd: True,  # noqa: ARG005
    )
    assert (
        implement_module.main(
            argv=["--close", "li-aaa", "--gap", "gap-9999", "--evidence", "stub"],
        )
        == 1
    )


def test_bd_ready_issues_returns_none_on_oserror(
    *,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """_bd_ready_issues returns None when subprocess.run raises OSError."""

    def _raises(*_a: object, **_kw: object) -> object:
        raise OSError("simulated subprocess failure")

    monkeypatch.setattr(implement_module.subprocess, "run", _raises)
    assert implement_module._bd_ready_issues(bd_argv=["bd"]) is None  # noqa: SLF001


def test_verify_gap_absent_skips_non_dict_entries(
    *,
    implement_module: object,
) -> None:
    """_verify_gap_absent silently skips gaps entries that aren't dicts."""

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, *_a: object, **_kw: object) -> None: ...
        def error(self, *_a: object, **_kw: object) -> None: ...

    report = {"gaps": ["not-a-dict", {"id": "gap-other"}]}
    assert (
        implement_module._verify_gap_absent(  # noqa: SLF001
            gap_id="gap-target",
            report=report,
            log=_Log(),
        )
        is True
    )


def test_main_close_mode_fails_when_gap_or_evidence_missing(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    implement_module: object,
) -> None:
    """--close without --gap/--evidence exits 1 with the missing-args diagnostic."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    assert implement_module.main(argv=["--close", "li-aaa"]) == 1


def test_implement_module_importable_without_running_main() -> None:
    """The implement module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "implement_for_import_test",
        str(_IMPLEMENT),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)
