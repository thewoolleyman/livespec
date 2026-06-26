"""Tests for livespec.doctor.static.agents_ai_reference_resolution.

The `agents-ai-reference-resolution` check verifies referential
integrity of the agent-instruction surface: every CONCRETE
`.ai/<topic>.md` path that any `AGENTS.md` under the project root
references MUST resolve to an existing file, relative to that
`AGENTS.md`'s own directory. An `AGENTS.md` that references zero
concrete `.ai/` files passes; the convention's angle-bracketed
placeholder `.ai/<topic>.md` is NOT a concrete reference and a
`.ai` that is the tail of a larger token (e.g. `foo.ai/x.md`) is
not one either.

Per the Fleet agent-instruction core contract in
SPECIFICATION/contracts.md, this is a cross-boundary invariant over
the project's agent-instruction surface, not the spec tree. The walk
excludes `archive`, `_vendor`, `__pycache__`, `.git`, `.venv`,
`node_modules`, and the spec tree; the check short-circuits on the
first unresolved reference in sorted `AGENTS.md` order.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import agents_ai_reference_resolution as mod
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


def _ctx(*, tmp_path: Path) -> DoctorContext:
    """Build a DoctorContext rooted at `tmp_path`."""
    return DoctorContext(project_root=tmp_path, spec_root=tmp_path / "SPECIFICATION")


def _pass_finding(*, tmp_path: Path) -> Finding:
    """The canonical pass-Finding for a `tmp_path`-rooted context."""
    return Finding(
        check_id="doctor-agents-ai-reference-resolution",
        status="pass",
        message="every AGENTS.md-referenced .ai/<topic>.md path resolves to an existing file",
        path=None,
        line=None,
        spec_root=str(tmp_path / "SPECIFICATION"),
    )


def _run_and_unwrap(*, ctx: DoctorContext) -> Finding:
    """Run the check and unwrap the IOResult to a Finding."""
    return unsafe_perform_io(mod.run(ctx=ctx)).unwrap()


def test_run_passes_when_reference_resolves(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) passes when a referenced `.ai/<topic>.md` file exists."""
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "AGENTS.md").write_text("See `.ai/foo.md`.\n", encoding="utf-8")
    ai_dir = tmp_path / ".ai"
    ai_dir.mkdir()
    _ = (ai_dir / "foo.md").write_text("topic detail\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_fails_on_dangling_reference(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) fails when a referenced `.ai/<topic>.md` file is missing."""
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "AGENTS.md").write_text("Refs `.ai/missing.md` here.\n", encoding="utf-8")
    finding = _run_and_unwrap(ctx=_ctx(tmp_path=tmp_path))
    assert finding.status == "fail"
    assert finding.path == str(tmp_path / "AGENTS.md")
    assert finding.line == 1
    assert "AGENTS.md:1" in finding.message
    assert ".ai/missing.md" in finding.message


def test_run_resolves_reference_relative_to_nested_agents_dir(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) resolves a nested `AGENTS.md`'s reference against its own dir."""
    monkeypatch.chdir(tmp_path)
    sub = tmp_path / "sub"
    sub.mkdir()
    _ = (sub / "AGENTS.md").write_text("See `.ai/x.md`.\n", encoding="utf-8")
    nested_ai = sub / ".ai"
    nested_ai.mkdir()
    _ = (nested_ai / "x.md").write_text("nested detail\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_ignores_placeholder_and_tail_token(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) treats the angle-bracket placeholder and a tail token as non-refs.

    `.ai/<topic>.md` (angle brackets excluded by the grammar) and
    `foo.ai/x.md` (a `.ai` that is the tail of a larger token, rejected
    by the negative lookbehind) are NOT concrete references, so an
    AGENTS.md carrying only these passes.
    """
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "AGENTS.md").write_text(
        "The `.ai/<topic>.md` placeholder and a foo.ai/x.md tail token.\n",
        encoding="utf-8",
    )
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_ignores_dangling_reference_in_archive(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) does NOT scan `AGENTS.md` files under a top-level `archive/`."""
    monkeypatch.chdir(tmp_path)
    archive = tmp_path / "archive"
    archive.mkdir()
    _ = (archive / "AGENTS.md").write_text("Refs `.ai/missing.md`.\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_ignores_dangling_reference_under_excluded_segment(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) excludes an `AGENTS.md` nested under a `_vendor` segment.

    `_vendor` is not a top-level exclusion, so the walk reaches it, but
    `_is_excluded` drops it from the candidate `AGENTS.md` set — its
    dangling reference does not trip the check.
    """
    monkeypatch.chdir(tmp_path)
    vendor = tmp_path / "scripts" / "_vendor"
    vendor.mkdir(parents=True)
    _ = (vendor / "AGENTS.md").write_text("Refs `.ai/missing.md`.\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_surfaces_first_unresolved_in_sorted_order(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) surfaces the first unresolved reference in sorted `AGENTS.md` order.

    `a/AGENTS.md` sorts before `b/AGENTS.md`; both dangle, but the
    `a/AGENTS.md` Finding is the surfaced one (first-violation
    precedence).
    """
    monkeypatch.chdir(tmp_path)
    dir_a = tmp_path / "a"
    dir_a.mkdir()
    _ = (dir_a / "AGENTS.md").write_text("Refs `.ai/missing.md`.\n", encoding="utf-8")
    dir_b = tmp_path / "b"
    dir_b.mkdir()
    _ = (dir_b / "AGENTS.md").write_text("Refs `.ai/missing.md`.\n", encoding="utf-8")
    finding = _run_and_unwrap(ctx=_ctx(tmp_path=tmp_path))
    assert finding.status == "fail"
    assert finding.path == str(dir_a / "AGENTS.md")
    assert "a/AGENTS.md" in finding.message


def test_run_passes_when_no_agents_md_present(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) passes when the project root carries no `AGENTS.md` at all."""
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "notes.txt").write_text("not an agents file\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_passes_when_agents_md_has_zero_references(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) passes when an `AGENTS.md` carries no `.ai/` references."""
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "AGENTS.md").write_text("# Orientation\n\nplain prose\n", encoding="utf-8")
    assert mod.run(ctx=_ctx(tmp_path=tmp_path)) == IOSuccess(_pass_finding(tmp_path=tmp_path))


def test_run_propagates_read_failure(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) keeps a file-read failure on the IOResult failure track."""
    monkeypatch.chdir(tmp_path)
    _ = (tmp_path / "AGENTS.md").write_text("Refs `.ai/foo.md`.\n", encoding="utf-8")

    def _boom(*, path: Path) -> IOFailure[PreconditionError]:
        return IOFailure(PreconditionError(f"read denied: {path}"))

    monkeypatch.setattr(mod.fs, "read_text", _boom)
    result = mod.run(ctx=_ctx(tmp_path=tmp_path))
    assert isinstance(result, IOFailure)


def test_iter_ai_references_yields_only_concrete_references() -> None:
    """_iter_ai_references yields concrete `.ai/<topic>.md` refs with line numbers.

    The placeholder and tail-token lines yield nothing; the concrete
    reference on line 3 is the only match.
    """
    text = (
        "The `.ai/<topic>.md` placeholder.\n"
        "A foo.ai/x.md tail token.\n"
        "A real `.ai/agent-disciplines.md` reference.\n"
    )
    refs = list(mod._iter_ai_references(text=text))  # noqa: SLF001
    assert refs == [(3, ".ai/agent-disciplines.md")]


def test_is_excluded_matches_excluded_segment() -> None:
    """_is_excluded returns True when a path segment is in the excluded set."""
    spec_root = Path("/proj/SPECIFICATION")
    excluded = mod._is_excluded(  # noqa: SLF001
        path=Path("/proj/scripts/_vendor/AGENTS.md"),
        spec_root=spec_root,
    )
    assert excluded is True


def test_is_excluded_matches_path_under_spec_root() -> None:
    """_is_excluded returns True when the path lives inside the spec tree."""
    spec_root = Path("/proj/SPECIFICATION")
    excluded = mod._is_excluded(  # noqa: SLF001
        path=Path("/proj/SPECIFICATION/AGENTS.md"),
        spec_root=spec_root,
    )
    assert excluded is True


def test_is_excluded_matches_path_equal_to_spec_root() -> None:
    """_is_excluded returns True when the path IS the spec_root itself."""
    spec_root = Path("/proj/SPECIFICATION")
    assert mod._is_excluded(path=spec_root, spec_root=spec_root) is True  # noqa: SLF001


def test_is_excluded_false_for_ordinary_path() -> None:
    """_is_excluded returns False for a plain in-scope project path."""
    spec_root = Path("/proj/SPECIFICATION")
    excluded = mod._is_excluded(  # noqa: SLF001
        path=Path("/proj/templates/impl-plugin/AGENTS.md"),
        spec_root=spec_root,
    )
    assert excluded is False


def test_slug_is_doctor_agents_ai_reference_resolution() -> None:
    """The module's SLUG constant is the canonical check_id."""
    assert mod.SLUG == "doctor-agents-ai-reference-resolution"
