"""Outside-in tests for `dev-tooling/implementation/plan.py`.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow", `plan` manages the
beads issues that mirror current implementation gaps. The
script reads `implementation-gaps/current.json`, identifies
gap ids that lack a tracking beads issue (the "untracked"
set), surfaces them via stdout, and on demand calls
`bd create` + `bd dep add` to file each one.

Two test families:

1. **End-to-end smoke tests** — invoke the script via
   `subprocess.run` against a `tmp_path` with a fake `bd`
   shell stub that records every argv it sees. Confirms the
   list-mode JSON shape, the --create flow's bd argv
   sequence, and the --create-all batch behaviour.

2. **Branch-coverage unit tests** — import `plan` directly
   and call helpers / `main()` with cwd scoped to `tmp_path`
   and `subprocess.run` monkeypatched to exercise error
   paths (missing report, malformed report, bd unavailable,
   bd query failure, bd create failure, dep add failure).

The script defaults to `Path.cwd()` for its file lookups, so
all tests scope cwd via `monkeypatch.chdir` or
`subprocess.run(cwd=...)` to keep the live repo untouched.
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
_PLAN = _REPO_ROOT / "dev-tooling" / "implementation" / "plan.py"
_SCHEMA_SRC = _REPO_ROOT / "implementation-gaps" / "current.schema.json"


def _make_gap_entry(
    *,
    gap_id: str,
    title: str = "fixture gap",
    depends_on: list[str] | None = None,
) -> dict[str, object]:
    """Minimal Gap-schema-conforming entry used as a fixture."""
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
        "depends_on": depends_on if depends_on is not None else [],
    }


def _build_report(*, gaps: list[dict[str, object]]) -> dict[str, object]:
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


def _write_fixture(*, root: Path, gaps: list[dict[str, object]]) -> None:
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


def _install_recording_fake_bd(
    *,
    tmp_path: Path,
    label_responses: dict[str, list[dict[str, object]]] | None = None,
    create_id: str = "li-fake",
) -> tuple[str, Path]:
    """Install a label-aware fake `bd` shim that records every argv invocation.

    Returns (PATH-string, log-path). The fake is implemented in Python so it
    can parse `--label <X>` and return per-label responses (a shell stub
    cannot easily do that). Sub-commands handled:

    - `list --all --label <label> --json` → emits
      `json.dumps(label_responses.get(label, []))`. Default behaviour:
      every label maps to `[]` (no tracking issues anywhere).
    - `create ...` → emits `{"id": "<create_id>"}` so plan.py can parse
      the new issue id from `--json` stdout.
    - any other sub-command → emits `{}` and exits 0.

    Every invocation appends one line (argv joined by spaces) to the
    returned log path. Tests inspect the log to assert plan.py issued the
    expected bd calls in the expected order with the expected flags.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_path = tmp_path / "bd-invocations.log"
    responses_path = tmp_path / "bd-label-responses.json"
    responses_path.write_text(
        json.dumps(label_responses if label_responses is not None else {}),
        encoding="utf-8",
    )
    bd_path = bin_dir / "bd"
    script = f"""#!{sys.executable}
import json, os, sys
log_path = {str(log_path)!r}
responses_path = {str(responses_path)!r}
create_id = {create_id!r}
with open(log_path, "a") as fp:
    fp.write(json.dumps(sys.argv[1:]) + "\\n")
argv = sys.argv[1:]
if not argv:
    sys.exit(0)
sub = argv[0]
if sub == "list":
    label = ""
    for i, tok in enumerate(argv):
        if tok == "--label" and i + 1 < len(argv):
            label = argv[i + 1]
            break
    with open(responses_path) as fp:
        responses = json.load(fp)
    sys.stdout.write(json.dumps(responses.get(label, [])) + "\\n")
elif sub == "create":
    sys.stdout.write(json.dumps({{"id": create_id}}) + "\\n")
else:
    sys.stdout.write("{{}}\\n")
sys.exit(0)
"""
    _ = bd_path.write_text(script, encoding="utf-8")
    bd_path.chmod(0o755)
    return f"{bin_dir}:/usr/bin:/bin", log_path


def _empty_path(*, tmp_path: Path) -> str:
    """A PATH pointing only at an empty dir — neither mise nor bd resolvable."""
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
        [sys.executable, str(_PLAN), *(args or [])],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def plan_module() -> Iterator[object]:
    """Import plan as a module for direct-call unit tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("plan", str(_PLAN))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["plan"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("plan", None)


def test_list_mode_emits_empty_array_when_no_gaps(*, tmp_path: Path) -> None:
    """An empty gaps list → stdout is `[]`; exit 0."""
    _write_fixture(root=tmp_path, gaps=[])
    env_path, _ = _install_recording_fake_bd(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert json.loads(result.stdout) == []


def test_list_mode_emits_only_untracked_gaps(*, tmp_path: Path) -> None:
    """Gap that already has a tracking beads issue is omitted from the list."""
    _write_fixture(
        root=tmp_path,
        gaps=[
            _make_gap_entry(gap_id="gap-0010", title="already tracked"),
            _make_gap_entry(gap_id="gap-0011", title="not yet tracked"),
        ],
    )
    env_path, _ = _install_recording_fake_bd(
        tmp_path=tmp_path,
        label_responses={
            "gap-id:gap-0010": [{"id": "li-aaa", "labels": ["gap-id:gap-0010"]}],
        },
    )
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    parsed = json.loads(result.stdout)
    untracked_ids = [entry["id"] for entry in parsed]
    assert untracked_ids == ["gap-0011"]


def test_list_mode_skips_already_tracked_when_bd_returns_match(
    *,
    tmp_path: Path,
) -> None:
    """Single gap that's already tracked → empty list; exit 0."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-0010")],
    )
    env_path, _ = _install_recording_fake_bd(
        tmp_path=tmp_path,
        label_responses={
            "gap-id:gap-0010": [{"id": "li-aaa", "labels": ["gap-id:gap-0010"]}],
        },
    )
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


def test_create_mode_invokes_bd_create_with_gap_label(*, tmp_path: Path) -> None:
    """--create gap-NNNN runs `bd create` once with a `gap-id:gap-NNNN` label flag."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-0020", title="needs filing")],
    )
    env_path, log_path = _install_recording_fake_bd(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path, args=["--create", "gap-0020"])
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    log_contents = log_path.read_text(encoding="utf-8")
    invocations = [json.loads(line) for line in log_contents.splitlines() if line]
    create_invocations = [argv for argv in invocations if argv and argv[0] == "create"]
    assert len(create_invocations) == 1, f"expected exactly one bd create call; saw {invocations!r}"
    assert "gap-id:gap-0020" in create_invocations[0]


def test_create_mode_skips_already_tracked_gap(*, tmp_path: Path) -> None:
    """--create against an already-tracked gap is a no-op (no bd create call)."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-0030")],
    )
    env_path, log_path = _install_recording_fake_bd(
        tmp_path=tmp_path,
        label_responses={
            "gap-id:gap-0030": [{"id": "li-aaa", "labels": ["gap-id:gap-0030"]}],
        },
    )
    result = _run(cwd=tmp_path, env_path=env_path, args=["--create", "gap-0030"])
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    log_contents = log_path.read_text(encoding="utf-8")
    invocations = [json.loads(line) for line in log_contents.splitlines() if line]
    create_invocations = [argv for argv in invocations if argv and argv[0] == "create"]
    assert create_invocations == []


def test_create_mode_adds_dependency_edges(*, tmp_path: Path) -> None:
    """A gap whose depends_on names another tracked gap files a `bd dep add` edge."""
    _write_fixture(
        root=tmp_path,
        gaps=[
            _make_gap_entry(gap_id="gap-0040", title="dep already tracked"),
            _make_gap_entry(
                gap_id="gap-0041",
                title="depends on gap-0040",
                depends_on=["gap-0040"],
            ),
        ],
    )
    env_path, log_path = _install_recording_fake_bd(
        tmp_path=tmp_path,
        label_responses={
            "gap-id:gap-0040": [{"id": "li-existing", "labels": ["gap-id:gap-0040"]}],
        },
        create_id="li-newdep",
    )
    result = _run(cwd=tmp_path, env_path=env_path, args=["--create", "gap-0041"])
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    log_contents = log_path.read_text(encoding="utf-8")
    invocations = [json.loads(line) for line in log_contents.splitlines() if line]
    dep_invocations = [argv for argv in invocations if argv and argv[0] == "dep"]
    assert any(
        "li-newdep" in argv and "li-existing" in argv for argv in dep_invocations
    ), f"expected dep edge from li-newdep to li-existing; saw {dep_invocations!r}"


def test_create_all_creates_every_untracked_gap(*, tmp_path: Path) -> None:
    """--create-all calls bd create once per untracked gap."""
    _write_fixture(
        root=tmp_path,
        gaps=[
            _make_gap_entry(gap_id="gap-0050"),
            _make_gap_entry(gap_id="gap-0051"),
            _make_gap_entry(gap_id="gap-0052"),
        ],
    )
    env_path, log_path = _install_recording_fake_bd(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path, args=["--create-all"])
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    log_contents = log_path.read_text(encoding="utf-8")
    invocations = [json.loads(line) for line in log_contents.splitlines() if line]
    create_invocations = [argv for argv in invocations if argv and argv[0] == "create"]
    assert len(create_invocations) == 3, f"expected 3 bd create calls; saw {invocations!r}"


def test_fails_when_bd_unavailable(*, tmp_path: Path) -> None:
    """No bd or mise on PATH → exit 1 with bd-missing diagnostic."""
    _write_fixture(root=tmp_path, gaps=[_make_gap_entry(gap_id="gap-0060")])
    env_path = _empty_path(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "bd not on PATH" in result.stderr


def test_fails_when_report_missing(*, tmp_path: Path) -> None:
    """No current.json → exit 1 with report-missing diagnostic."""
    env_path, _ = _install_recording_fake_bd(tmp_path=tmp_path)
    result = _run(cwd=tmp_path, env_path=env_path)
    assert result.returncode == 1
    assert "report missing" in result.stderr or "current.json" in result.stderr


def test_main_fails_when_report_malformed(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """main() returns 1 when current.json is not parseable JSON."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text("not json {", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    assert plan_module.main(argv=[]) == 1


def test_main_fails_when_gaps_field_is_not_a_list(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """main() returns 1 when report.gaps is not a JSON array."""
    gaps_dir = tmp_path / "implementation-gaps"
    gaps_dir.mkdir(parents=True)
    (gaps_dir / "current.json").write_text(
        json.dumps({"gaps": "not-a-list"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    assert plan_module.main(argv=[]) == 1


def test_resolve_bd_prefers_mise(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_resolve_bd returns the mise-prefixed argv when mise is available."""
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/fake/mise" if name == "mise" else None,
    )
    assert plan_module._resolve_bd() == ["/fake/mise", "exec", "--", "bd"]  # noqa: SLF001


def test_resolve_bd_falls_back_to_bare_bd(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_resolve_bd returns the bare-bd argv when only bd is available."""
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: "/fake/bd" if name == "bd" else None,
    )
    assert plan_module._resolve_bd() == ["/fake/bd"]  # noqa: SLF001


def test_resolve_bd_returns_none_when_neither_present(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_resolve_bd returns None when neither tool is on PATH."""
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert plan_module._resolve_bd() is None  # noqa: SLF001


def test_main_fails_when_create_target_unknown(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """--create gap-XXXX where the gap id is NOT in current.json → exit 1."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-0070")],
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    assert plan_module.main(argv=["--create", "gap-9999"]) == 1


def test_plan_module_importable_without_running_main() -> None:
    """The plan module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("plan_for_import_test", str(_PLAN))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"


_PLAN_BD = _REPO_ROOT / "dev-tooling" / "implementation" / "_plan_bd.py"


@pytest.fixture
def plan_bd_module() -> Iterator[object]:
    """Import _plan_bd as a module for direct-call unit tests."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_plan_bd", str(_PLAN_BD))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_plan_bd"] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop("_plan_bd", None)


class _StubResult:
    """A stub mimicking subprocess.CompletedProcess[str] for monkeypatched runs."""

    def __init__(self, *, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


def test_run_bd_returns_none_on_oserror(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """_run_bd returns None when subprocess.run raises OSError."""

    def _raises(*_args: object, **_kwargs: object) -> object:
        raise OSError("simulated subprocess failure")

    monkeypatch.setattr(plan_bd_module.subprocess, "run", _raises)
    assert plan_bd_module._run_bd(bd_argv=["bd"], extra=["list"]) is None  # noqa: SLF001


def test_issues_with_label_returns_none_on_nonzero_rc(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """issues_with_label returns None when bd's returncode is non-zero."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=1, stdout=""),
    )
    assert plan_bd_module.issues_with_label(bd_argv=["bd"], label="gap-id:gap-0001") is None


def test_issues_with_label_returns_empty_on_empty_stdout(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """issues_with_label returns [] (a real result) when bd emits empty stdout."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout="   \n"),
    )
    assert plan_bd_module.issues_with_label(bd_argv=["bd"], label="x") == []


def test_issues_with_label_returns_none_on_malformed_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """issues_with_label returns None when bd's stdout is not parseable JSON."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout="not json {"),
    )
    assert plan_bd_module.issues_with_label(bd_argv=["bd"], label="x") is None


def test_issues_with_label_returns_none_on_non_list_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """issues_with_label returns None when bd's stdout parses to a non-list."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout=json.dumps({"not": "list"})),
    )
    assert plan_bd_module.issues_with_label(bd_argv=["bd"], label="x") is None


def test_create_gap_issue_returns_none_on_nonzero_rc(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """create_gap_issue returns None when bd create's returncode is non-zero."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=1, stdout=""),
    )
    gap = _make_gap_entry(gap_id="gap-0001")
    assert plan_bd_module.create_gap_issue(gap=gap, bd_argv=["bd"]) is None


def test_create_gap_issue_returns_none_on_malformed_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """create_gap_issue returns None when bd's stdout is not parseable JSON."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout="not json {"),
    )
    gap = _make_gap_entry(gap_id="gap-0001")
    assert plan_bd_module.create_gap_issue(gap=gap, bd_argv=["bd"]) is None


def test_create_gap_issue_returns_none_on_non_dict_json(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """create_gap_issue returns None when bd's stdout parses to a non-dict."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout=json.dumps(["not", "dict"])),
    )
    gap = _make_gap_entry(gap_id="gap-0001")
    assert plan_bd_module.create_gap_issue(gap=gap, bd_argv=["bd"]) is None


def test_create_gap_issue_returns_none_when_id_missing(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """create_gap_issue returns None when bd's response omits the id field."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=0, stdout=json.dumps({"no": "id"})),
    )
    gap = _make_gap_entry(gap_id="gap-0001")
    assert plan_bd_module.create_gap_issue(gap=gap, bd_argv=["bd"]) is None


def test_add_dep_edge_returns_false_on_nonzero_rc(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """add_dep_edge returns False when bd dep add returns non-zero."""
    monkeypatch.setattr(
        plan_bd_module.subprocess,
        "run",
        lambda *_a, **_kw: _StubResult(returncode=1, stdout=""),
    )
    assert (
        plan_bd_module.add_dep_edge(blocked_id="li-a", blocker_id="li-b", bd_argv=["bd"]) is False
    )


def test_existing_tracking_issue_returns_none_on_query_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_bd_module: object,
) -> None:
    """existing_tracking_issue returns None when issues_with_label fails."""
    monkeypatch.setattr(
        plan_bd_module,
        "issues_with_label",
        lambda *, bd_argv, label: None,  # noqa: ARG005
    )
    assert plan_bd_module.existing_tracking_issue(gap_id="gap-0001", bd_argv=["bd"]) is None


def test_untracked_gaps_skips_non_dict_entries(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_untracked_gaps silently skips entries that are not dicts."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: None,  # noqa: ARG005
    )
    result = plan_module._untracked_gaps(  # noqa: SLF001
        gaps=["not-a-dict", {"id": 42}, {"id": "gap-0001", "title": "ok"}],
        bd_argv=["bd"],
    )
    assert [entry["id"] for entry in result] == ["gap-0001"]


def test_process_create_target_returns_false_on_create_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_process_create_target returns False when bd create returns no id."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: None,  # noqa: ARG005
    )
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "create_gap_issue",
        lambda *, gap, bd_argv: None,  # noqa: ARG005
    )

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, *_a: object, **_kw: object) -> None: ...
        def error(self, *_a: object, **_kw: object) -> None: ...

    gap = _make_gap_entry(gap_id="gap-0001")
    assert (
        plan_module._process_create_target(  # noqa: SLF001
            gap=gap,
            bd_argv=["bd"],
            log=_Log(),
        )
        is False
    )


def test_wire_dep_edges_skips_predecessor_without_tracking_issue(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_wire_dep_edges logs a warning and continues when a predecessor isn't tracked."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: None,  # noqa: ARG005
    )
    warnings: list[str] = []

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, msg: str, **_kw: object) -> None:
            warnings.append(msg)

        def error(self, *_a: object, **_kw: object) -> None: ...

    ok = plan_module._wire_dep_edges(  # noqa: SLF001
        new_id="li-new",
        depends_on=["gap-missing", 42, "gap-other"],
        bd_argv=["bd"],
        log=_Log(),
        gap_id="gap-0001",
    )
    assert ok is True
    assert len(warnings) == 2


def test_wire_dep_edges_skips_predecessor_with_non_string_id(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_wire_dep_edges silently skips predecessors whose id field isn't a string."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: {"id": 42},  # noqa: ARG005
    )

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, *_a: object, **_kw: object) -> None: ...
        def error(self, *_a: object, **_kw: object) -> None: ...

    ok = plan_module._wire_dep_edges(  # noqa: SLF001
        new_id="li-new",
        depends_on=["gap-pred"],
        bd_argv=["bd"],
        log=_Log(),
        gap_id="gap-child",
    )
    assert ok is True


def test_wire_dep_edges_returns_false_on_dep_add_failure(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_wire_dep_edges returns False when bd dep add fails."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: {"id": "li-pred"},  # noqa: ARG005
    )
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "add_dep_edge",
        lambda *, blocked_id, blocker_id, bd_argv: False,  # noqa: ARG005
    )

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, *_a: object, **_kw: object) -> None: ...
        def error(self, *_a: object, **_kw: object) -> None: ...

    ok = plan_module._wire_dep_edges(  # noqa: SLF001
        new_id="li-new",
        depends_on=["gap-pred"],
        bd_argv=["bd"],
        log=_Log(),
        gap_id="gap-child",
    )
    assert ok is False


def test_process_create_target_returns_true_when_no_depends_on_list(
    *,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """When depends_on is missing or non-list, _process_create_target returns True after create."""
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: None,  # noqa: ARG005
    )
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "create_gap_issue",
        lambda *, gap, bd_argv: "li-new",  # noqa: ARG005
    )

    class _Log:
        def info(self, *_a: object, **_kw: object) -> None: ...
        def warning(self, *_a: object, **_kw: object) -> None: ...
        def error(self, *_a: object, **_kw: object) -> None: ...

    gap_no_deps = _make_gap_entry(gap_id="gap-0001")
    del gap_no_deps["depends_on"]  # exercise the non-list branch
    assert (
        plan_module._process_create_target(  # noqa: SLF001
            gap=gap_no_deps,
            bd_argv=["bd"],
            log=_Log(),
        )
        is True
    )


def test_run_create_mode_returns_one_on_failure(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    plan_module: object,
) -> None:
    """_run_create_mode returns 1 when at least one target fails to be processed."""
    _write_fixture(
        root=tmp_path,
        gaps=[_make_gap_entry(gap_id="gap-0001")],
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/bd")
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "existing_tracking_issue",
        lambda *, gap_id, bd_argv: None,  # noqa: ARG005
    )
    monkeypatch.setattr(
        plan_module._plan_bd,  # noqa: SLF001
        "create_gap_issue",
        lambda *, gap, bd_argv: None,  # noqa: ARG005  — simulate create failure
    )
    assert plan_module.main(argv=["--create", "gap-0001"]) == 1
