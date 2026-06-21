"""Tests for livespec.doctor.static.config_named_cli_callability.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → "`config-named-cli-callability`": for every CLI
named in `.livespec.jsonc` — spec-side per §"Spec-side CLI
contract" and orchestrator-side per §"Orchestrator CLI contract
— the three named CLIs" — the named entry MUST resolve and be
executable. A missing or non-executable resolution fires `fail`
naming the config key and value. The callability test is
zero-shape: no probe convention (no required `--version`,
`--help`, or ping subcommand).

The check reads `<project_root>/.livespec.jsonc`, validates it
against `livespec_config.schema.json` (so the seven spec-side
defaults materialize), and resolves each named argv's first
entry: a bare command name resolves via PATH lookup; an entry
containing a path separator resolves as a filesystem path
(relative paths anchored at the project root) that must exist
and carry the executable bit. The literal `${CLAUDE_PLUGIN_ROOT}`
placeholder expands to the env var when set, falling back to the
running package's plugin root.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import config_named_cli_callability
from livespec.schemas.dataclasses.finding import Finding
from returns.result import Success
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _run_check(*, project_root: Path) -> Finding:
    """Run the check against `project_root` and unwrap the Finding."""
    ctx = DoctorContext(
        project_root=project_root,
        spec_root=project_root / "SPECIFICATION",
    )
    io_result = config_named_cli_callability.run(ctx=ctx)
    unwrapped = unsafe_perform_io(io_result)
    match unwrapped:
        case Success(finding):
            return finding
        case _:
            msg = f"expected Success(Finding), got {unwrapped}"
            raise AssertionError(msg)


def _write_config(*, project_root: Path, payload: dict[str, object]) -> None:
    """Write `payload` as `<project_root>/.livespec.jsonc`."""
    project_root.mkdir(parents=True, exist_ok=True)
    _ = (project_root / ".livespec.jsonc").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _write_executable(*, path: Path) -> Path:
    """Create an executable stub script at `path` and return it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_registered_in_static_checks_for_main_trees_only() -> None:
    """The check is registered in STATIC_CHECKS and excluded from sub-spec trees.

    `.livespec.jsonc` is a project-root concern (like
    `livespec_jsonc_valid` + `template_exists`), so the check
    runs once per invocation against the main tree only.
    """
    from livespec.doctor.static import APPLICABILITY_BY_TREE_KIND, STATIC_CHECKS

    assert config_named_cli_callability in STATIC_CHECKS
    assert config_named_cli_callability not in APPLICABILITY_BY_TREE_KIND["sub_spec"]


def test_passes_on_default_config(*, tmp_path: Path) -> None:
    """A minimal config passes: every spec-side default argv leads with python3.

    Core's reference defaults are `["python3", "${CLAUDE_PLUGIN_ROOT}/
    scripts/bin/<wrapper>.py"]`; the callable ENTRY is argv[0]
    (`python3`), which resolves via PATH on every supported
    platform per `constraints.md`.
    """
    project_root = tmp_path / "project"
    _write_config(project_root=project_root, payload={"template": "livespec"})
    finding = _run_check(project_root=project_root)
    assert finding.status == "pass", f"expected pass, got {finding}"
    assert finding.check_id == "doctor-config-named-cli-callability"


def test_fails_naming_key_and_value_when_spec_cli_entry_is_missing(
    *,
    tmp_path: Path,
) -> None:
    """A spec-side CLI whose argv[0] path does not exist fires fail.

    Per the contract: "A missing or non-executable resolution
    fires `fail` naming the config key and value."
    """
    project_root = tmp_path / "project"
    _write_config(
        project_root=project_root,
        payload={"spec_clis": {"doctor": ["/nonexistent/custom-doctor", "--json"]}},
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "fail", f"expected fail, got {finding}"
    assert "spec_clis.doctor" in finding.message
    assert "/nonexistent/custom-doctor" in finding.message


def test_fails_when_orchestrator_cli_is_not_executable(*, tmp_path: Path) -> None:
    """An orchestrator CLI resolving to a non-executable file fires fail."""
    project_root = tmp_path / "project"
    executable = _write_executable(path=project_root / "tools" / "ok-cli")
    non_executable = project_root / "tools" / "not-executable"
    _ = non_executable.write_text("plain text\n", encoding="utf-8")
    _write_config(
        project_root=project_root,
        payload={
            "orchestrator": {
                "name": "livespec-orchestrator-beads-fabro",
                "spec_reader": [str(executable)],
                "gap_capture": [str(executable)],
                "drift_capture": [str(non_executable)],
            },
        },
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "fail", f"expected fail, got {finding}"
    assert "orchestrator.drift_capture" in finding.message
    assert str(non_executable) in finding.message
    assert "orchestrator.spec_reader" not in finding.message


def test_passes_when_orchestrator_clis_resolve(*, tmp_path: Path) -> None:
    """A complete orchestrator section with executable CLIs passes."""
    project_root = tmp_path / "project"
    executable = _write_executable(path=project_root / "tools" / "impl-cli")
    _write_config(
        project_root=project_root,
        payload={
            "orchestrator": {
                "name": "livespec-orchestrator-beads-fabro",
                "spec_reader": [str(executable), "spec-reader"],
                "gap_capture": [str(executable), "gap-capture"],
                "drift_capture": [str(executable), "drift-capture"],
            },
        },
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "pass", f"expected pass, got {finding}"


def test_resolves_relative_path_entries_against_project_root(
    *,
    tmp_path: Path,
) -> None:
    """A path-shaped argv[0] without a leading slash anchors at the project root."""
    project_root = tmp_path / "project"
    _ = _write_executable(path=project_root / "tools" / "local-doctor")
    _write_config(
        project_root=project_root,
        payload={"spec_clis": {"doctor": ["tools/local-doctor"]}},
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "pass", f"expected pass, got {finding}"


def test_expands_claude_plugin_root_placeholder_from_env(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`${CLAUDE_PLUGIN_ROOT}` in argv[0] expands to the env var when set."""
    project_root = tmp_path / "project"
    plugin_root = tmp_path / "plugroot"
    _ = _write_executable(path=plugin_root / "scripts" / "bin" / "custom-cli")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin_root))
    _write_config(
        project_root=project_root,
        payload={
            "spec_clis": {"critique": ["${CLAUDE_PLUGIN_ROOT}/scripts/bin/custom-cli"]},
        },
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "pass", f"expected pass, got {finding}"


def test_expands_claude_plugin_root_placeholder_from_package_when_env_unset(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the env var unset, the placeholder falls back to the package's plugin root.

    The running package lives at `<plugin-root>/scripts/livespec/`,
    so the fallback resolves `${CLAUDE_PLUGIN_ROOT}/scripts/bin/
    critique.py` to this repo's real (executable) wrapper.
    """
    project_root = tmp_path / "project"
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    _write_config(
        project_root=project_root,
        payload={
            "spec_clis": {"critique": ["${CLAUDE_PLUGIN_ROOT}/scripts/bin/critique.py"]},
        },
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "pass", f"expected pass, got {finding}"


def test_skipped_when_config_is_missing(*, tmp_path: Path) -> None:
    """A missing `.livespec.jsonc` yields skipped (livespec-jsonc-valid owns that fail)."""
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True)
    finding = _run_check(project_root=project_root)
    assert finding.status == "skipped", f"expected skipped, got {finding}"


def test_fails_when_config_rejects_schema_validation(*, tmp_path: Path) -> None:
    """A config whose named-CLI shape violates the schema fires fail.

    An empty argv has no entry to resolve — the schema's
    `minItems: 1` rejection IS the callability failure here, so
    the check fires `fail` (not skipped) naming the validation
    diagnostic.
    """
    project_root = tmp_path / "project"
    _write_config(
        project_root=project_root,
        payload={"spec_clis": {"seed": []}},
    )
    finding = _run_check(project_root=project_root)
    assert finding.status == "fail", f"expected fail, got {finding}"
    assert "livespec_config" in finding.message
