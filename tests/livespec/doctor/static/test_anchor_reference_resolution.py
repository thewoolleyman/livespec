"""Tests for livespec.doctor.static.anchor_reference_resolution.

Per Plan Phase 7 sub-step 7.d + PROPOSAL.md §"`doctor` →
Static-phase checks": the `anchor-reference-resolution` check
verifies that every Markdown intra-document anchor reference (a
link of the form `[text](#slug)`) resolves to an actual heading
in the same file via the GFM slug algorithm. This is the last of
four remaining doctor static checks landing at Phase 7 (alongside
`out-of-band-edits`, `bcp14-keyword-wellformedness`, and
`gherkin-blank-line-format`).

Per PROPOSAL.md §"Static-phase checks": "Anchors are generated
per GitHub-flavored Markdown (GFM) slug rules: the heading text
is lowercased; internal whitespace is replaced with single
hyphens; punctuation is stripped except `-` and `_`; multiple
consecutive hyphens collapse to one. Headings inside fenced code
blocks (` ``` ` or `~~~`) are NOT considered headings. Explicit
`{#custom-id}` syntax is NOT supported in v1."

Per v018 Q1: this check applies to all spec-text-bearing trees
(main + each sub-spec). The walk-set semantic matches the
sibling Phase-7 checks: livespec-shape spec_roots walk
`<spec_root>/*.md` top-level files only; minimal-shape
spec_roots scan only `<spec_root>/SPECIFICATION.md`. Cross-file
anchor references (`[text](other.md#slug)`) and external links
(`[text](https://example.com)`) are out of scope at the static
layer and pass silently — only intra-file anchors are
discriminated.

Detection rules (v1 minimum scope):
  - For every Markdown link `[text](#slug)` whose target starts
    with `#`, compute the set of valid slugs from every `#`/`##`/
    `###` etc. heading in the SAME file (excluding headings
    inside fenced code blocks). The reference resolves iff its
    `#`-stripped target is in that set.
  - Cross-file references (target containing `/` or starting
    with a non-`#` character before any `#`) are ignored.
  - The first violation found (lexicographically-sorted file,
    first matching reference) is surfaced; the check short-
    circuits on the first hit so the user sees one offense at
    a time.

Cycle 7.d lands the Red→Green pair for this check.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import anchor_reference_resolution
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_spec_root(*, spec_root: Path, files: dict[str, str]) -> None:
    """Materialize `files` (filename -> contents) at `spec_root`.

    Helper for the per-test fixtures: each test seeds the
    spec_root with a small set of `.md` files exercising one
    facet of the anchor-resolution rule. The helper writes UTF-8
    so the on-disk encoding matches the production
    `fs.read_text` UTF-8 convention.
    """
    spec_root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        _ = (spec_root / name).write_text(content, encoding="utf-8")


def test_run_returns_pass_when_anchor_reference_resolves(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when an anchor reference resolves.

    Pass-arm seed: a `spec.md` whose body contains a Markdown
    link `[link](#valid-slug)` AND a heading `## Valid slug`
    that produces the slug `valid-slug` per the GFM rule. The
    reference resolves to the heading; the check passes.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n" "\n" "## Valid slug\n" "\n" "See [link](#valid-slug) for details.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_no_anchor_references_present(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when no anchor references exist.

    Pass-arm seed: spec text with no Markdown anchor references
    at all (only headings + prose). The rule is vacuously
    satisfied — there are no references to resolve. The check
    passes.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Spec\n\nDescriptive prose with no anchor links.\n",
            "constraints.md": "# Constraints\n\nMore prose.\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_case_insensitive_heading_match(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) lowercases heading text per the GFM slug algorithm.

    Pass-arm seed: a heading `## Foo` whose GFM slug is `foo`
    (lowercased). A reference `[link](#foo)` resolves. Pins the
    case-folding step of the slug algorithm.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Top\n\n## Foo\n\nSee [link](#foo).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_punctuation_in_heading(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) strips punctuation per the GFM slug algorithm.

    Pass-arm seed: a heading `## Foo: Bar` whose GFM slug is
    `foo-bar` (the colon is stripped, the space becomes a
    hyphen). A reference `[link](#foo-bar)` resolves. Pins the
    punctuation-strip and whitespace-to-hyphen steps.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Top\n\n## Foo: Bar\n\nSee [link](#foo-bar).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_consecutive_hyphens_collapsed(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) collapses consecutive hyphens per the GFM slug algorithm.

    Pass-arm seed: a heading `## Foo -- Bar` whose GFM slug is
    `foo-bar` (the literal `-- ` collapses + the trailing hyphen
    around the space gives a single hyphen between `foo` and
    `bar`). Pins the consecutive-hyphen-collapse step.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Top\n\n## Foo -- Bar\n\nSee [link](#foo-bar).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_external_link(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) ignores external links (out of scope for the check).

    Pass-arm seed: spec text with an external `[link](https://
    example.com)` and no anchor references. External links are
    not anchor references — the rule does not engage. Pins the
    external-link-ignored branch.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Spec\n\nVisit [example](https://example.com).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_cross_file_anchor(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) ignores cross-file anchor references (out of scope).

    Pass-arm seed: spec text with a cross-file reference
    `[link](other.md#slug)`. The walk-set deferred-items.md
    entry restricts this check to intra-file resolution; cross-
    file references pass silently. Pins the cross-file-ignored
    branch.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Spec\n\nSee [link](other.md#slug).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_spec_root_has_no_md_files(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when no top-level .md files exist.

    Edge case: an empty spec_root (e.g., a freshly-created
    directory before seed materializes content) has no `.md`
    files to walk. The check yields a pass-Finding —
    vacuously well-formed. Pins the no-walk-target branch so
    the check doesn't crash on unseeded trees.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_root.mkdir()
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_when_anchor_reference_does_not_resolve(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) on a missing-target reference.

    Fail-arm seed: a `spec.md` whose body contains a Markdown
    link `[link](#missing-slug)` but NO heading whose GFM slug
    is `missing-slug`. The reference does not resolve; the
    check yields a fail-Finding pointing at the offending line.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n" "\n" "## Real heading\n" "\n" "See [link](#missing-slug) for details.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="fail",
        message=(
            "spec.md:5 anchor reference '#missing-slug' does not "
            "resolve to any heading in the same file"
        ),
        path=str(spec_root / "spec.md"),
        line=5,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_first_violation_when_multiple_files_offend(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for the first offending file (sorted).

    Multi-file fixture: `contracts.md` carries a broken anchor;
    `spec.md` is well-formed. Files are walked in sorted order
    so `contracts.md`'s violation is the surfaced one. Pins the
    multi-file walk + sorted-order discriminator.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": "# Contracts\n\nSee [link](#nope).\n",
            "spec.md": "# Spec\n\n## Real\n\nSee [link](#real).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="fail",
        message=(
            "contracts.md:3 anchor reference '#nope' does not "
            "resolve to any heading in the same file"
        ),
        path=str(spec_root / "contracts.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_preserves_first_violation_when_later_file_also_offends(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) preserves the first-violation Finding when a later file also offends.

    First-violation-precedence fixture: BOTH `contracts.md` AND
    `spec.md` carry violations. Files are walked sorted; the
    first violation found (in `contracts.md`) MUST remain the
    surfaced Finding even though `spec.md` is scanned later.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": "# Contracts\n\nSee [first](#first-broken).\n",
            "spec.md": "# Spec\n\nSee [later](#later-broken).\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="fail",
        message=(
            "contracts.md:3 anchor reference '#first-broken' does not "
            "resolve to any heading in the same file"
        ),
        path=str(spec_root / "contracts.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_only_walks_top_level_md_files(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) does NOT recurse into history/proposed_changes/templates subtrees.

    Per the v018 Q1 walk-set semantic shared with sibling
    Phase-7 checks, the anchor-reference-resolution check
    inspects only top-level `<spec_root>/*.md` files (livespec-
    shape) or only `<spec_root>/SPECIFICATION.md` (minimal-
    shape). A broken anchor seeded inside `<spec_root>/history/
    v001/spec.md` MUST NOT trip the check (history snapshots
    are byte-identical copies that inherit the live spec's
    well-formedness via the seed/revise discipline).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Spec\n\nDescriptive prose without anchors.\n",
        },
    )
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    _ = (history_v001 / "spec.md").write_text(
        "# Snapshot\n\nSee [broken](#nope).\n",
        encoding="utf-8",
    )
    proposed_changes = spec_root / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "draft.md").write_text(
        "# Draft\n\nSee [also-broken](#nope).\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_minimal_shape_with_resolving_anchor(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) walks only `SPECIFICATION.md` for minimal-shape spec_roots.

    Pass-arm seed: minimal-shape `spec_root` (carries
    `SPECIFICATION.md` directly at the spec_root per
    `spec_root: "./"`). The single-file walk picks up
    `SPECIFICATION.md`, finds a heading + a resolving anchor
    reference, and yields a pass-Finding.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root
    _ = (spec_root / "SPECIFICATION.md").write_text(
        (
            "# My project\n"
            "\n"
            "## Acceptance scenario\n"
            "\n"
            "See [link](#acceptance-scenario).\n"
        ),
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="pass",
        message="every anchor reference resolves to a heading in the same file",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_for_minimal_shape_with_broken_anchor(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) on minimal-shape broken anchor.

    Fail-arm seed: minimal-shape `spec_root` whose
    `SPECIFICATION.md` has a heading and a Markdown link whose
    target slug does NOT match any heading. The check yields a
    fail-Finding pointing at the offending line in
    `SPECIFICATION.md`.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root
    _ = (spec_root / "SPECIFICATION.md").write_text(
        ("# My project\n" "\n" "## Real heading\n" "\n" "See [broken](#missing).\n"),
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="fail",
        message=(
            "SPECIFICATION.md:5 anchor reference '#missing' does not "
            "resolve to any heading in the same file"
        ),
        path=str(spec_root / "SPECIFICATION.md"),
        line=5,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_when_heading_is_inside_fenced_code_block(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) does NOT treat fenced-block content as a heading.

    Fail-arm seed: spec text whose only `## Slug` heading-like
    line is inside a fenced ` ``` ` block. The reference
    `[link](#slug)` therefore does not resolve (the fence-
    enclosed line is a code line, not a markdown heading) and
    the check yields a fail-Finding. Pins the fenced-block
    exclusion rule.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": ("# Spec\n" "\n" "```\n" "## Slug\n" "```\n" "\n" "See [link](#slug).\n"),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-anchor-reference-resolution",
        status="fail",
        message=(
            "spec.md:7 anchor reference '#slug' does not " "resolve to any heading in the same file"
        ),
        path=str(spec_root / "spec.md"),
        line=7,
        spec_root=str(spec_root),
    )
    assert anchor_reference_resolution.run(ctx=ctx) == IOSuccess(expected)


def test_slug_is_doctor_anchor_reference_resolution() -> None:
    """The module's `SLUG` constant is the canonical check_id.

    Pins the SLUG ↔ check_id mapping per the static/CLAUDE.md
    convention (slug `anchor-reference-resolution` ↔ module
    filename `anchor_reference_resolution.py` ↔ check_id
    `doctor-anchor-reference-resolution`).
    """
    assert anchor_reference_resolution.SLUG == "doctor-anchor-reference-resolution"
