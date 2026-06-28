"""Tests for livespec.doctor.static.no_spec_section_citation_in_code.

The `no-spec-section-citation-in-code` check verifies that no
source comment or docstring cites a spec SECTION via the
section-sign citation form. A section-sign citation inside any
other string literal (test data, regex, fixtures) is legitimate
and ignored; only Python COMMENT tokens, module/class/function
DOCSTRINGS, and `skills/<name>/SKILL.md` whole-file text are
scanned.

Per SPECIFICATION/constraints.md (the Reference discipline
section): source code MAY reference spec files at the FILE level
(stable across heading renames) but MUST NOT name specific
headings within those files. The walk-set is every `*.py` under
`ctx.project_root` (excluding `archive`, `_vendor`, `__pycache__`,
`.git`, `node_modules`, and the spec tree) plus every
`skills/<name>/SKILL.md`; the check short-circuits on the first
violation in sorted path order.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_spec_section_citation_in_code as mod
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

# The forbidden marker assembled at runtime so this test module
# carries no literal section-sign-plus-quote in a comment or
# docstring (the check under test forbids that). The marker living
# in a string literal is the very thing the check must IGNORE.
_MARKER = "§" + '"'


def _cite(*, heading: str) -> str:
    """Build a section-sign citation wrapping `heading`."""
    return _MARKER + heading + '"'


def _project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Create a `project/SPECIFICATION` pair and return both paths."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    return (project_root, spec_root)


def _ctx(*, tmp_path: Path) -> tuple[DoctorContext, Path, Path]:
    """Build a DoctorContext over a fresh project tree."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    return (
        DoctorContext(project_root=project_root, spec_root=spec_root),
        project_root,
        spec_root,
    )


def _pass_finding(*, spec_root: Path) -> Finding:
    """The canonical pass-Finding for the given spec_root."""
    return Finding(
        check_id="doctor-no-spec-section-citation-in-code",
        status="pass",
        message=(
            "no source comment or docstring cites a spec section via the " "section-sign form"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def _run_and_unwrap(*, ctx: DoctorContext) -> Finding:
    """Run the check and unwrap the IOResult to a Finding."""
    return unsafe_perform_io(mod.run(ctx=ctx)).unwrap()


def test_run_passes_when_no_source_cites_a_section(*, tmp_path: Path) -> None:
    """run(ctx) passes when no comment/docstring/skill text cites a section."""
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    _ = (project_root / "mod.py").write_text(
        '"""Clean module docstring."""\n\n\nx = 1  # plain comment\n',
        encoding="utf-8",
    )
    assert mod.run(ctx=ctx) == IOSuccess(_pass_finding(spec_root=spec_root))


def test_run_ignores_section_marker_in_string_literal(*, tmp_path: Path) -> None:
    """run(ctx) ignores a section marker that appears in a string literal.

    The marker is legitimate test data / regex when it lives in a
    plain string assignment — only comments and docstrings carry the
    forbidden citation.
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    source = "marker = " + repr(_cite(heading="Some heading")) + "\n"
    _ = (project_root / "mod.py").write_text(source, encoding="utf-8")
    assert mod.run(ctx=ctx) == IOSuccess(_pass_finding(spec_root=spec_root))


def test_run_fails_on_comment_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails when a Python comment cites a spec section."""
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    comment = "# Per " + _cite(heading="Wire contract")
    source = "x = 1\n" + comment + "\n"
    py_path = project_root / "mod.py"
    _ = py_path.write_text(source, encoding="utf-8")
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.path == str(py_path)
    assert finding.line == 2
    assert "mod.py:2" in finding.message


def test_run_fails_on_docstring_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails when a module docstring cites a spec section."""
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    docstring = '"""Module that cites ' + _cite(heading="Heading") + '."""\n'
    py_path = project_root / "mod.py"
    _ = py_path.write_text(docstring + "x = 1\n", encoding="utf-8")
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.line == 1
    assert "<docstring>" in finding.message


def test_run_fails_on_function_docstring_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails when a function docstring cites a spec section.

    Exercises the function-node branch of the docstring walk (the
    module docstring is clean; the citation is in the function body's
    docstring on a later line).
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    source = (
        '"""Clean module docstring."""\n'
        "\n"
        "\n"
        "def f() -> None:\n"
        '    """Cites ' + _cite(heading="Inner") + '."""\n'
        "    return None\n"
    )
    py_path = project_root / "mod.py"
    _ = py_path.write_text(source, encoding="utf-8")
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.line == 5


def test_run_fails_on_skill_md_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails when a skills/<name>/SKILL.md cites a spec section.

    The whole-file Markdown scan flags any marker occurrence; the
    citation here is on the third line.
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    skill_dir = project_root / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    _ = skill_path.write_text(
        "# Demo\n\nPer " + _cite(heading="A heading") + " here.\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.path == str(skill_path)
    assert finding.line == 3


def test_run_fails_on_rust_comment_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails when a Rust source comment cites a spec section."""
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    rust_dir = project_root / "crates" / "demo" / "src"
    rust_dir.mkdir(parents=True)
    rust_path = rust_dir / "lib.rs"
    _ = rust_path.write_text(
        "pub fn demo() {}\n// Per " + _cite(heading="Rust wire") + "\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.path == str(rust_path)
    assert finding.line == 2


def test_run_ignores_section_marker_in_excluded_segments(*, tmp_path: Path) -> None:
    """run(ctx) does NOT scan paths under excluded segments.

    A `_vendor`-nested module whose comment cites a section MUST NOT
    trip the check (vendored third-party code is out of scope).
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    vendor = project_root / "scripts" / "_vendor"
    vendor.mkdir(parents=True)
    _ = (vendor / "lib.py").write_text(
        "# Per " + _cite(heading="Ignored") + "\n",
        encoding="utf-8",
    )
    assert mod.run(ctx=ctx) == IOSuccess(_pass_finding(spec_root=spec_root))


def test_run_ignores_section_marker_in_spec_tree(*, tmp_path: Path) -> None:
    """run(ctx) does NOT scan `.py` files inside the spec tree.

    The spec tree is `no_cross_spec_reference`'s domain; a `.py` file
    that somehow lives under `SPECIFICATION/` is excluded here.
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    _ = (spec_root / "helper.py").write_text(
        "# Per " + _cite(heading="SpecSide") + "\n",
        encoding="utf-8",
    )
    assert mod.run(ctx=ctx) == IOSuccess(_pass_finding(spec_root=spec_root))


def test_run_ignores_non_skill_markdown(*, tmp_path: Path) -> None:
    """run(ctx) ignores Markdown that is not a `skills/<name>/SKILL.md`.

    A top-level `README.md` carrying the marker is out of scope — the
    Markdown whole-file scan applies only to skill-prose files.
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    _ = (project_root / "README.md").write_text(
        "Per " + _cite(heading="Doc") + "\n",
        encoding="utf-8",
    )
    assert mod.run(ctx=ctx) == IOSuccess(_pass_finding(spec_root=spec_root))


def test_run_surfaces_first_violation_in_sorted_order(*, tmp_path: Path) -> None:
    """run(ctx) surfaces the first violation in sorted path order.

    `a.py` sorts before `b.py`; both cite a section, but the `a.py`
    Finding is the surfaced one (first-violation precedence).
    """
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    _ = (project_root / "a.py").write_text(
        "# Per " + _cite(heading="First") + "\n",
        encoding="utf-8",
    )
    _ = (project_root / "b.py").write_text(
        "# Per " + _cite(heading="Second") + "\n",
        encoding="utf-8",
    )
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.path == str(project_root / "a.py")


def test_run_propagates_read_failure(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) keeps a file-read failure on the IOResult failure track."""
    ctx, project_root, spec_root = _ctx(tmp_path=tmp_path)
    _ = (project_root / "mod.py").write_text("x = 1\n", encoding="utf-8")

    def _boom(*, path: Path) -> IOFailure[PreconditionError]:
        return IOFailure(PreconditionError(f"read denied: {path}"))

    monkeypatch.setattr(mod.fs, "read_text", _boom)
    result = mod.run(ctx=ctx)
    assert isinstance(result, IOFailure)


def test_comment_violation_returns_none_on_unparseable_python() -> None:
    """_comment_violation returns None when the source cannot be tokenized.

    Unbalanced delimiters raise a TokenError mid-iteration, which the
    helper catches and reports as "no comment violation".
    """
    assert mod._comment_violation(text="x = (\n") is None  # noqa: SLF001


def test_docstring_violation_returns_none_on_syntax_error() -> None:
    """_docstring_violation returns None when the source is not valid Python."""
    assert mod._docstring_violation(text="def (:\n") is None  # noqa: SLF001


def test_scan_python_text_prefers_earlier_docstring_over_comment() -> None:
    """_scan_python_text picks the earlier of a docstring vs comment hit.

    Both a module docstring (line 1) and a comment (line 2) cite a
    section; the docstring is earlier, so it wins.
    """
    source = (
        '"""Cites ' + _cite(heading="DocFirst") + '."""\n'
        "x = 1  # Per " + _cite(heading="CommentSecond") + "\n"
    )
    hit = mod._scan_python_text(text=source)  # noqa: SLF001
    assert hit is not None
    line_number, offending = hit
    assert line_number == 1
    assert offending == "<docstring>"


def test_scan_python_text_prefers_earlier_comment_over_docstring() -> None:
    """_scan_python_text picks an earlier comment over a later docstring.

    A comment on line 1 cites a section; a function docstring on a
    later line also cites one. The earlier comment wins.
    """
    source = (
        "# Per " + _cite(heading="CommentFirst") + "\n"
        "def f() -> None:\n"
        '    """Cites ' + _cite(heading="DocLater") + '."""\n'
        "    return None\n"
    )
    hit = mod._scan_python_text(text=source)  # noqa: SLF001
    assert hit is not None
    line_number, _offending = hit
    assert line_number == 1


def test_scan_python_text_returns_none_when_clean() -> None:
    """_scan_python_text returns None when neither comment nor docstring cites."""
    assert mod._scan_python_text(text='"""Clean."""\nx = 1  # ok\n') is None  # noqa: SLF001


def test_scan_skill_text_returns_none_when_clean() -> None:
    """_scan_skill_text returns None when no line carries the marker."""
    assert mod._scan_skill_text(text="# Title\n\nplain prose\n") is None  # noqa: SLF001


def test_is_skill_md_rejects_non_skill_filename() -> None:
    """_is_skill_md returns False for a file that is not named SKILL.md."""
    assert mod._is_skill_md(path=Path("skills/demo/notes.md")) is False  # noqa: SLF001


def test_is_skill_md_rejects_skill_md_outside_skills_dir() -> None:
    """_is_skill_md returns False for a SKILL.md not under a `skills/` dir."""
    assert mod._is_skill_md(path=Path("docs/SKILL.md")) is False  # noqa: SLF001


def test_is_skill_md_accepts_nested_skill_file() -> None:
    """_is_skill_md returns True for `skills/<name>/SKILL.md`."""
    assert mod._is_skill_md(path=Path("skills/demo/SKILL.md")) is True  # noqa: SLF001


def test_is_excluded_matches_path_equal_to_spec_root() -> None:
    """_is_excluded returns True when the path IS the spec_root itself."""
    spec_root = Path("/proj/SPECIFICATION")
    assert mod._is_excluded(path=spec_root, spec_root=spec_root) is True  # noqa: SLF001


def test_is_excluded_false_for_ordinary_source_path() -> None:
    """_is_excluded returns False for a plain in-scope source path."""
    spec_root = Path("/proj/SPECIFICATION")
    excluded = mod._is_excluded(  # noqa: SLF001
        path=Path("/proj/scripts/mod.py"),
        spec_root=spec_root,
    )
    assert excluded is False


def test_is_in_scan_set_rejects_unrelated_extension() -> None:
    """_is_in_scan_set returns False for a non-.py, non-SKILL.md file."""
    spec_root = Path("/proj/SPECIFICATION")
    in_set = mod._is_in_scan_set(path=Path("/proj/data.txt"), spec_root=spec_root)  # noqa: SLF001
    assert in_set is False


def test_slug_is_doctor_no_spec_section_citation_in_code() -> None:
    """The module's SLUG constant is the canonical check_id."""
    assert mod.SLUG == "doctor-no-spec-section-citation-in-code"
