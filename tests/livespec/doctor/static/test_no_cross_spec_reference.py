"""Tests for livespec.doctor.static.no_cross_spec_reference.

The `no-cross-spec-reference` check verifies that every
section-sign citation in a `SPECIFICATION/<file>.md` resolves
either inside the same spec tree (same-tree) or against the
`external_references` allowlist declared in `.livespec.jsonc`.
Anything else — a citation naming sibling-repo content, an
implementation-tree path, or a stale heading — fires `fail`.

Per SPECIFICATION/constraints.md (the Reference discipline
section): the citation form is a section sign directly followed
by a double-quoted heading, optionally preceded by a `<file>.md`
prefix. Same-file anchor references (Markdown `#slug` links)
remain governed by `doctor-anchor-reference-resolution`.

The walk-set semantic mirrors the sibling
`anchor_reference_resolution` check: livespec-shape spec_roots
walk `<spec_root>/*.md` top-level files only; minimal-shape
spec_roots scan only `<spec_root>/SPECIFICATION.md`. Citations
whose section sign falls inside a fenced code block or an inline
code span are illustrative syntax and are skipped; the check
short-circuits on the first violation in sorted file order.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec.context import DoctorContext
from livespec.doctor.static import no_cross_spec_reference
from livespec.errors import PreconditionError
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []

# A section-sign citation marker assembled at runtime so this test
# module carries no literal section-sign-plus-quote sequence in a
# comment or docstring (the sibling
# `no_spec_section_citation_in_code` check forbids that in source);
# the marker living in a string literal is legitimate test data.
_MARKER = "§" + '"'


def _json(value: str) -> str:
    """Return a JSON string literal for `value` (double-quoted, escaped)."""
    return json.dumps(value)


def _cite(*, heading: str, file_prefix: str | None = None) -> str:
    """Build a section-sign citation, optionally with a file prefix."""
    body = _MARKER + heading + '"'
    if file_prefix is None:
        return body
    return f"{file_prefix} {body}"


def _seed_spec_root(*, spec_root: Path, files: dict[str, str]) -> None:
    """Materialize `files` (filename -> contents) at `spec_root`."""
    spec_root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        _ = (spec_root / name).write_text(content, encoding="utf-8")


def _write_config(*, project_root: Path, body: str) -> None:
    """Write a `.livespec.jsonc` with `body` at `project_root`."""
    _ = (project_root / ".livespec.jsonc").write_text(body, encoding="utf-8")


def _project(*, tmp_path: Path) -> tuple[Path, Path]:
    """Create a `project/SPECIFICATION` pair and return both paths."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    return (project_root, spec_root)


def _pass_finding(*, spec_root: Path) -> Finding:
    """The canonical pass-Finding for the given spec_root."""
    return Finding(
        check_id="doctor-no-cross-spec-reference",
        status="pass",
        message=(
            "every section citation resolves same-tree or via the " "external_references allowlist"
        ),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )


def _run_and_unwrap(*, ctx: DoctorContext) -> Finding:
    """Run the check and unwrap the IOResult to a Finding."""
    return unsafe_perform_io(no_cross_spec_reference.run(ctx=ctx)).unwrap()


def test_run_passes_when_no_citations_present(*, tmp_path: Path) -> None:
    """run(ctx) passes when no spec file carries a section-sign citation."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": "# Spec\n\nPlain prose with no citation.\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_passes_for_bare_same_tree_citation(*, tmp_path: Path) -> None:
    """run(ctx) passes a bare citation whose heading exists somewhere in-tree.

    The citation lives in `spec.md` but its target heading lives in
    `contracts.md`; the union-of-all-headings resolution accepts it.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Template manifest")
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": f"# Spec\n\nSee {citation} for the manifest.\n",
            "contracts.md": "# Contracts\n\n## Template manifest\n\nbody\n",
        },
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_passes_for_file_prefixed_same_tree_citation(*, tmp_path: Path) -> None:
    """run(ctx) passes a file-prefixed citation when the sibling has the heading."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Wire contract", file_prefix="contracts.md")
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": f"# Spec\n\nPer {citation}.\n",
            "contracts.md": "# Contracts\n\n## Wire contract\n\nbody\n",
        },
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_passes_for_allowlisted_bare_citation(*, tmp_path: Path) -> None:
    """run(ctx) passes a bare citation whose heading is an allowlist heading."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Sibling discovery")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation} in the sibling.\n"},
    )
    allow = _cite(heading="Sibling discovery", file_prefix="SPECIFICATION/contracts.md")
    _write_config(
        project_root=project_root,
        body='{"external_references": {"sib": [' + _json(allow) + "]}}",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_passes_for_allowlisted_file_prefixed_citation(*, tmp_path: Path) -> None:
    """run(ctx) passes a file-prefixed cross-tree citation that is allowlisted.

    The citation names a sibling-repo path (which contains a
    separator so it is not same-tree); the allowlist entry's
    basename-plus-heading form matches, so it passes.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(
        heading="Shared check inventory",
        file_prefix="livespec-x/SPECIFICATION/contracts.md",
    )
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation} upstream.\n"},
    )
    allow = _cite(
        heading="Shared check inventory",
        file_prefix="SPECIFICATION/contracts.md",
    )
    _write_config(
        project_root=project_root,
        body='{"external_references": {"livespec-x": [' + _json(allow) + "]}}",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_uses_sibling_clones_root_for_cross_repo_heading_validation(
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The cross-repo heading read honors the shared CI clones-root override."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    clones_root = tmp_path / "clones"
    sibling_root = clones_root / "repo-a"
    sibling_spec_root = sibling_root / "SPECIFICATION"
    citation = _cite(
        heading="Shared heading",
        file_prefix="repo-a/SPECIFICATION/contracts.md",
    )
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation} upstream.\n"},
    )
    _seed_spec_root(
        spec_root=sibling_spec_root,
        files={"contracts.md": "# Contracts\n\n## Shared heading\n\nupstream\n"},
    )
    allow = _cite(
        heading="Shared heading",
        file_prefix="SPECIFICATION/contracts.md",
    )
    _write_config(
        project_root=project_root,
        body=(
            '{"external_references": {"repo-a": ['
            + _json(allow)
            + ']}, "cross_repo_targets": {"repo-a": {"local_clone": '
            + _json(str(tmp_path / "stale-manifest-path"))
            + "}}}"
        ),
    )
    monkeypatch.setenv("LIVESPEC_SIBLING_CLONES_ROOT", str(clones_root))
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_fails_when_repo_qualified_citation_heading_is_absent_in_cited_repo(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) resolves a repo-qualified citation against that repo's headings.

    The local tree deliberately carries the same heading text, so a
    heading-only or basename-only resolution would pass. The cited
    sibling clone lacks that heading, so the repo-qualified citation
    must fail instead.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    sibling_root = tmp_path / "livespec"
    sibling_spec_root = sibling_root / "SPECIFICATION"
    citation = _cite(
        heading="Collision heading",
        file_prefix="livespec/SPECIFICATION/contracts.md",
    )
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": f"# Spec\n\nPer {citation} upstream.\n",
            "contracts.md": "# Contracts\n\n## Collision heading\n\nlocal only\n",
        },
    )
    _seed_spec_root(
        spec_root=sibling_spec_root,
        files={"contracts.md": "# Contracts\n\n## Different heading\n\nupstream\n"},
    )
    allow = _cite(
        heading="Collision heading",
        file_prefix="SPECIFICATION/contracts.md",
    )
    _write_config(
        project_root=project_root,
        body=(
            '{"external_references": {"livespec": ['
            + _json(allow)
            + ']}, "cross_repo_targets": {"livespec": {"local_clone": '
            + _json(str(sibling_root))
            + "}}}"
        ),
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-no-cross-spec-reference",
        status="fail",
        message=(
            f"spec.md:3 section citation '{citation}' does not resolve to a "
            f"heading in the same SPECIFICATION/ tree and is not allowlisted; "
            f"add '{citation}' under an external_references repo key in "
            f".livespec.jsonc to allow it"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(expected)


def test_run_fails_when_repo_qualified_citation_matches_different_repo_allowlist(
    *,
    tmp_path: Path,
) -> None:
    """A repo-qualified citation must match the same allowlist repo key."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    sibling_a_root = tmp_path / "repo-a"
    sibling_a_spec_root = sibling_a_root / "SPECIFICATION"
    citation = _cite(
        heading="Shared heading",
        file_prefix="repo-b/SPECIFICATION/contracts.md",
    )
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation} upstream.\n"},
    )
    _seed_spec_root(
        spec_root=sibling_a_spec_root,
        files={"contracts.md": "# Contracts\n\n## Shared heading\n\nupstream\n"},
    )
    allow = _cite(
        heading="Shared heading",
        file_prefix="SPECIFICATION/contracts.md",
    )
    _write_config(
        project_root=project_root,
        body=(
            '{"external_references": {"repo-a": ['
            + _json(allow)
            + ']}, "cross_repo_targets": {"repo-a": {"local_clone": '
            + _json(str(sibling_a_root))
            + "}}}"
        ),
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-no-cross-spec-reference",
        status="fail",
        message=(
            f"spec.md:3 section citation '{citation}' does not resolve to a "
            f"heading in the same SPECIFICATION/ tree and is not allowlisted; "
            f"add '{citation}' under an external_references repo key in "
            f".livespec.jsonc to allow it"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(expected)


def test_run_fails_for_unresolved_bare_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails a bare citation whose heading exists nowhere in-tree."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Nonexistent heading")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation} elsewhere.\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    suggested = _cite(heading="Nonexistent heading", file_prefix="SPECIFICATION/<file>.md")
    expected = Finding(
        check_id="doctor-no-cross-spec-reference",
        status="fail",
        message=(
            f"spec.md:3 section citation '{citation}' does not resolve to a "
            f"heading in the same SPECIFICATION/ tree and is not allowlisted; "
            f"add '{suggested}' under an external_references repo key in "
            f".livespec.jsonc to allow it"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(expected)


def test_run_fails_for_cross_tree_path_prefixed_citation(*, tmp_path: Path) -> None:
    """run(ctx) fails a `<repo>/path.md` citation that is not allowlisted.

    The file prefix contains a separator, so it can never resolve
    same-tree; with no allowlist entry it fails, and the suggested
    entry echoes the offending file-prefixed citation verbatim.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(
        heading="DependsOnEntry union",
        file_prefix="sibling/SPECIFICATION/contracts.md",
    )
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation}.\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-no-cross-spec-reference",
        status="fail",
        message=(
            f"spec.md:3 section citation '{citation}' does not resolve to a "
            f"heading in the same SPECIFICATION/ tree and is not allowlisted; "
            f"add '{citation}' under an external_references repo key in "
            f".livespec.jsonc to allow it"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(expected)


def test_run_fails_for_file_prefix_naming_absent_sibling(*, tmp_path: Path) -> None:
    """run(ctx) fails a `<name>.md` citation when `<name>.md` is not present.

    The file prefix is a bare sibling name (no separator) but no such
    file is in the walk-set, so `headings_by_file.get` returns None
    and the citation does not resolve same-tree.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Whatever", file_prefix="ghost.md")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation}.\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"
    assert finding.path == str(spec_root / "spec.md")
    assert "Whatever" in finding.message


def test_run_skips_citation_inside_inline_code_span(*, tmp_path: Path) -> None:
    """run(ctx) ignores a citation whose section sign is inside a backtick span.

    The illustrative citation lives inside a backtick code span, so
    it is NOT a citation even though its heading is unresolved.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Unresolved")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nThe `{citation}` form is illustrative.\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_resolves_citation_with_inner_backtick_heading(*, tmp_path: Path) -> None:
    """run(ctx) still resolves a real citation whose heading has a backtick span.

    Only the section sign's position is tested against inline-code
    ranges; a citation whose section sign is OUTSIDE backticks but
    whose quoted heading contains a backtick fragment resolves
    against the matching heading.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="`/livespec:next` binding")
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": f"# Spec\n\nPer {citation}.\n",
            "contracts.md": "# Contracts\n\n## `/livespec:next` binding\n\nbody\n",
        },
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_skips_citation_inside_fenced_code_block(*, tmp_path: Path) -> None:
    """run(ctx) ignores a citation inside a fenced code block.

    The unresolved citation lives inside a ` ``` ` fence and the
    heading-collection skips fenced headings too, so the block is
    entirely out of scope and the check passes.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Unresolved inside fence")
    body = "# Spec\n\n```\n" + citation + "\n```\n\nprose\n"
    _seed_spec_root(spec_root=spec_root, files={"spec.md": body})
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_minimal_shape_passes(*, tmp_path: Path) -> None:
    """run(ctx) scans only SPECIFICATION.md in a minimal-shape spec_root."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root
    citation = _cite(heading="Acceptance scenario")
    _ = (spec_root / "SPECIFICATION.md").write_text(
        f"# Proj\n\n## Acceptance scenario\n\nPer {citation}.\n",
        encoding="utf-8",
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_passes_when_spec_root_empty(*, tmp_path: Path) -> None:
    """run(ctx) passes (vacuously) when the spec_root has no .md files."""
    project_root, spec_root = _project(tmp_path=tmp_path)
    spec_root.mkdir()
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_recovers_when_config_missing(*, tmp_path: Path) -> None:
    """run(ctx) degrades to an empty allowlist when .livespec.jsonc is absent.

    With no config file, the allowlist load fails and `.lash`
    recovers to an empty allowlist; a same-tree citation still
    resolves, so the check passes.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Local")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\n## Local\n\nPer {citation}.\n"},
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    assert no_cross_spec_reference.run(ctx=ctx) == IOSuccess(
        _pass_finding(spec_root=spec_root),
    )


def test_run_with_non_dict_config_yields_empty_allowlist(*, tmp_path: Path) -> None:
    """run(ctx) treats a non-dict parsed config as no allowlist.

    A `.livespec.jsonc` whose top-level value is a JSON array parses
    fine but has no `external_references` key; `_config_allowlist_value`
    returns None, so a cross-tree citation fails for lack of an
    allowlist.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    citation = _cite(heading="Outside")
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": f"# Spec\n\nPer {citation}.\n"},
    )
    _write_config(project_root=project_root, body="[1, 2, 3]")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.status == "fail"


def test_flatten_allowlist_tolerates_malformed_shapes() -> None:
    """_flatten_allowlist ignores non-dict blocks, non-list and non-str values.

    Exercises each defensive branch: a non-dict `external_references`,
    a value that is not a list, a list entry that is not a string,
    and a well-formed entry whose heading is collected.
    """
    (
        none_strings,
        none_headings,
        none_by_repo,
    ) = no_cross_spec_reference._flatten_allowlist(  # noqa: SLF001
        external_references=None,
    )
    assert none_strings == set()
    assert none_headings == set()
    assert none_by_repo == {}

    good = _cite(heading="Good heading", file_prefix="contracts.md")
    strings, headings, by_repo = no_cross_spec_reference._flatten_allowlist(  # noqa: SLF001
        external_references={
            "repo-a": "not-a-list",
            "repo-b": [42, good],
        },
    )
    assert strings == {good}
    assert headings == {"Good heading"}
    assert by_repo == {"repo-b": {good}}


def test_flatten_allowlist_entry_without_citation_contributes_no_heading() -> None:
    """A malformed allowlist string with no citation adds to strings, not headings."""
    strings, headings, by_repo = no_cross_spec_reference._flatten_allowlist(  # noqa: SLF001
        external_references={"repo": ["no citation here"]},
    )
    assert strings == {"no citation here"}
    assert headings == set()
    assert by_repo == {"repo": {"no citation here"}}


def test_allowlist_match_skips_entries_without_file_prefix() -> None:
    """_allowlist_match ignores allowlist entries lacking a file prefix.

    A bare allowlist entry (heading only) contributes its heading to
    `entry_headings` but cannot satisfy a file-prefixed citation's
    basename comparison; the function falls through to False.
    """
    bare_entry = _cite(heading="Bare entry")
    matched = no_cross_spec_reference._allowlist_match(  # noqa: SLF001
        file_prefix="contracts.md",
        heading="Different heading",
        entry_strings={bare_entry},
        entry_headings={"Bare entry"},
    )
    assert matched is False


def test_allowlist_match_skips_entries_with_no_citation_shape() -> None:
    """_allowlist_match ignores allowlist strings that carry no citation.

    An allowlist string with no section-sign citation yields no regex
    match, so the entry is skipped during file-prefixed comparison.
    """
    matched = no_cross_spec_reference._allowlist_match(  # noqa: SLF001
        file_prefix="contracts.md",
        heading="Some heading",
        entry_strings={"garbage with no citation"},
        entry_headings=set(),
    )
    assert matched is False


def test_allowlist_match_falls_through_non_matching_file_entry() -> None:
    """_allowlist_match returns False when a file-prefixed entry does not match.

    The single allowlist entry IS a well-formed file-prefixed
    citation, but to a DIFFERENT file/heading than the citation under
    test; the loop iterates past it and returns False (the
    file-prefixed precision the bare path deliberately lacks).
    """
    other_entry = _cite(heading="Other heading", file_prefix="contracts.md")
    matched = no_cross_spec_reference._allowlist_match(  # noqa: SLF001
        file_prefix="spec.md",
        heading="Wanted heading",
        entry_strings={other_entry},
        entry_headings={"Other heading"},
    )
    assert matched is False


def test_run_fails_on_first_offending_file_in_sorted_order(*, tmp_path: Path) -> None:
    """run(ctx) surfaces the first violation in sorted file order.

    `contracts.md` sorts before `spec.md`; both carry an unresolved
    citation, but the `contracts.md` one is the surfaced Finding.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    first = _cite(heading="First broken")
    second = _cite(heading="Second broken")
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": f"# Contracts\n\nPer {first}.\n",
            "spec.md": f"# Spec\n\nPer {second}.\n",
        },
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    finding = _run_and_unwrap(ctx=ctx)
    assert finding.path == str(spec_root / "contracts.md")
    assert "First broken" in finding.message


def test_run_propagates_read_failure(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run(ctx) keeps a spec-file read failure on the IOResult failure track.

    When a walk-set file cannot be read, `_read_all_texts` short-
    circuits onto the failure track and `run` surfaces the
    PreconditionError rather than a Finding.
    """
    project_root, spec_root = _project(tmp_path=tmp_path)
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": "# Spec\n\nprose\n"},
    )
    _write_config(project_root=project_root, body="{}")
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)

    def _boom(*, path: Path) -> IOFailure[PreconditionError]:
        return IOFailure(PreconditionError(f"read denied: {path}"))

    monkeypatch.setattr(no_cross_spec_reference.fs, "read_text", _boom)
    result = no_cross_spec_reference.run(ctx=ctx)
    assert isinstance(result, IOFailure)


def test_slug_is_doctor_no_cross_spec_reference() -> None:
    """The module's SLUG constant is the canonical check_id."""
    assert no_cross_spec_reference.SLUG == "doctor-no-cross-spec-reference"
