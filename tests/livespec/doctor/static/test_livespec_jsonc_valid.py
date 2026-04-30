"""Tests for livespec.doctor.static.livespec_jsonc_valid.

Per Plan Phase 3 line 1596-1602 + PROPOSAL.md §"`doctor` →
Static-phase checks": this is the first of the eight Phase-3
minimum-subset doctor checks. It asserts that the project's
`.livespec.jsonc` config file exists and parses as valid JSONC
(comments stripped via the vendored jsoncomment shim).

Outside-in seam: the check is the consumer that drives the
`Finding` dataclass and `DoctorContext` dataclass into
existence simultaneously. Subsequent cycles widen the check
(rejection arm + missing-file arm) and drive additional
checks under the same DoctorContext shape.

Per static/CLAUDE.md, each check exports
`run(ctx) -> IOResult[Finding, E]`. The success arm yields
`IOSuccess(Finding(check_id="doctor-livespec-jsonc-valid",
status="pass", message="<...>", path=None, line=None,
spec_root=<spec_root-as-string>))`; later cycles add the
failure arms (missing config -> IOSuccess(status="fail"),
malformed JSONC -> IOSuccess(status="fail")).
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOSuccess

from livespec.context import DoctorContext
from livespec.doctor.static import livespec_jsonc_valid
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = []


def test_livespec_jsonc_valid_run_returns_pass_for_valid_config(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for a well-formed config.

    Seeds a project root with a minimal valid `.livespec.jsonc`
    (a single `template` field and a JSONC `//` comment to
    exercise the comment-stripping path), constructs a
    DoctorContext pointing at the project's main spec_root,
    and asserts the returned IOResult is an IOSuccess wrapping
    a Finding with status='pass' + the canonical check_id.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_text = '// minimal livespec config\n{\n  "template": "livespec"\n}\n'
    _ = (project_root / ".livespec.jsonc").write_text(config_text, encoding="utf-8")
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-livespec-jsonc-valid",
        status="pass",
        message="livespec config parses as valid JSONC",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert livespec_jsonc_valid.run(ctx=ctx) == IOSuccess(expected)


def test_livespec_jsonc_valid_run_returns_fail_for_missing_config(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) when .livespec.jsonc is absent.

    Drives the failure arm: when the project root has no
    `.livespec.jsonc`, the check's railway sees fs.read_text
    return Failure(PreconditionError); the check maps that to
    a fail-status Finding (rather than letting the IOFailure
    bubble) so the orchestrator can render it as a structured
    finding rather than a check-process error. This is the
    "check ran and detected a violation" path per
    finding.schema.json's status enum description.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    result = livespec_jsonc_valid.run(ctx=ctx)
    config_path_str = str(project_root / ".livespec.jsonc")
    expected = Finding(
        check_id="doctor-livespec-jsonc-valid",
        status="fail",
        message="livespec config file is missing or unreadable",
        path=config_path_str,
        line=None,
        spec_root=str(spec_root),
    )
    assert result == IOSuccess(expected)
