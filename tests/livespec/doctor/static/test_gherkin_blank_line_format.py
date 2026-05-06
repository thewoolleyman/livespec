"""Tests for livespec.doctor.static.gherkin_blank_line_format.

Per Plan Phase 7 sub-step 7.c + PROPOSAL.md §"`doctor` →
Static-phase checks": the `gherkin-blank-line-format` check
verifies that fenced ` ```gherkin ` blocks in spec-text-bearing
markdown files are surrounded by blank lines (one blank line
above the opening fence, one blank line below the closing
fence). Without proper spacing, GFM renderers and Gherkin
parsers produce inconsistent output.

Per `SPECIFICATION/templates/minimal/constraints.md`
§"Gherkin blank-line format check exemption": the check MUST
exempt `minimal`-rooted projects whose `SPECIFICATION.md` does
NOT contain any fenced ` ```gherkin ` blocks. The exemption
avoids false-positive failures for spec content that has no
scenario-style narrative. When `SPECIFICATION.md` does contain
gherkin blocks, the check applies normally.

Per v018 Q1: applies to all spec-text-bearing trees (main +
each sub-spec). For multi-file livespec-shape spec_roots, the
check walks `<spec_root>/*.md` top-level files only — it does
NOT recurse into `history/`, `proposed_changes/`, or
`templates/` subtrees (per the same walk-set semantic
established in `bcp14-keyword-wellformedness`). For minimal-
shape spec_roots (single-file `SPECIFICATION.md` at the spec
root), only `SPECIFICATION.md` is scanned.

Detection rules (v1 minimum scope per the deferred-items.md
`static-check-semantics` entry on `gherkin-blank-line-format`'s
fenced-block detection algorithm):
  - For every line opening a fenced ` ```gherkin ` block:
      - The line immediately before the opening fence MUST
        be blank, OR the opening fence MUST be the very first
        line of the file (start-of-file is implicit-blank-
        above).
      - The line immediately after the matching closing
        fence MUST be blank, OR the closing fence MUST be
        the last line of the file (end-of-file is
        implicit-blank-below).
  - The closing fence is the next line whose content is
    exactly ` ``` ` (three backticks, optional trailing
    whitespace).
  - The first violation found (lexicographically-sorted file,
    first matching line) is surfaced; the check short-
    circuits on the first hit so the user sees one offense
    at a time.

Cycle 7.c lands the Red→Green pair for this check.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import gherkin_blank_line_format
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_spec_root(*, spec_root: Path, files: dict[str, str]) -> None:
    """Materialize `files` (filename -> contents) at `spec_root`.

    Helper for the per-test fixtures: each test seeds the
    spec_root with a small set of `.md` files exercising one
    facet of the gherkin blank-line detection rule. The helper
    writes UTF-8 so the on-disk encoding matches the production
    `fs.read_text` UTF-8 convention.
    """
    spec_root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        _ = (spec_root / name).write_text(content, encoding="utf-8")


def test_run_returns_pass_when_gherkin_block_is_well_formed(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when fenced gherkin is well-formed.

    Pass-arm seed: a `scenarios.md` containing a fenced
    ` ```gherkin ` block preceded by a blank line and followed
    by a blank line. The canonical well-formed shape — one
    blank line above the opening fence, one blank line below
    the closing fence.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n"
                "\n"
                "## Happy-path\n"
                "\n"
                "```gherkin\n"
                "Scenario: foo\n"
                "  Given bar\n"
                "  When baz\n"
                "  Then qux\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_no_gherkin_blocks_present_in_livespec_shape(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when no fenced gherkin blocks exist.

    Pass-arm seed: a multi-file livespec-shape spec_root whose
    `*.md` files contain no fenced ` ```gherkin ` blocks. The
    rule is vacuously satisfied — there are no fences to
    surround. The check passes (it does NOT skip; the skip
    path is reserved for the minimal-rooted exemption).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": "# Spec\n\nThis document has no scenarios.\n",
            "constraints.md": "# Constraints\n\nDescriptive prose.\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_gherkin_block_is_at_start_of_file(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) treats start-of-file as an implicit blank line above the opening fence.

    Pass-arm seed: a `scenarios.md` whose very first line is
    the opening ` ```gherkin ` fence. There is no physical
    blank line above (the file begins with the fence); the
    rule treats start-of-file as implicit-blank-above so a
    fence at the start of the file passes.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "```gherkin\n" "Scenario: foo\n" "  Given bar\n" "```\n" "\n" "Trailing prose.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_when_gherkin_block_is_at_end_of_file(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) treats end-of-file as an implicit blank line below the closing fence.

    Pass-arm seed: a `scenarios.md` whose closing ` ``` ` is
    the very last line of the file (no trailing newline-only
    blank line). The rule treats end-of-file as implicit-
    blank-below so a closing fence at the last line passes.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n" "\n" "```gherkin\n" "Scenario: foo\n" "  Given bar\n" "```"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_when_text_touches_opening_fence(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) when prose touches the opening fence.

    Fail-arm seed: a `scenarios.md` where a heading line is
    immediately followed (no blank line) by the opening
    ` ```gherkin ` fence. Per the rule the line immediately
    above the opening fence MUST be blank or the fence MUST
    be the start-of-file. Neither holds here so the check
    yields a fail-Finding pointing at the offending fence line.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n"
                "## Happy-path\n"
                "```gherkin\n"
                "Scenario: foo\n"
                "  Given bar\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="fail",
        message=(
            "scenarios.md:3 fenced ```gherkin block opening fence "
            "is not preceded by a blank line"
        ),
        path=str(spec_root / "scenarios.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_when_text_touches_closing_fence(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) when prose touches the closing fence.

    Fail-arm seed: a `scenarios.md` where the closing ` ``` `
    is immediately followed (no blank line) by a prose line.
    Per the rule the line immediately below the closing
    fence MUST be blank or the closing fence MUST be the last
    line of the file. Neither holds here so the check yields a
    fail-Finding pointing at the offending closing-fence line.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n"
                "\n"
                "```gherkin\n"
                "Scenario: foo\n"
                "  Given bar\n"
                "```\n"
                "Trailing prose without a blank line above.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="fail",
        message=(
            "scenarios.md:6 fenced ```gherkin block closing fence "
            "is not followed by a blank line"
        ),
        path=str(spec_root / "scenarios.md"),
        line=6,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_first_violation_when_multiple_files_offend(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for the first offending file (sorted).

    Multi-file fixture: `contracts.md` is well-formed,
    `scenarios.md` carries a touching-prose violation. Files
    are walked in sorted order so the deterministic first
    violation is the one the check surfaces. This pins the
    multi-file walk behavior and the sorted-order
    discriminator.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": (
                "# Contracts\n"
                "\n"
                "```gherkin\n"
                "Scenario: well-formed\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
            "scenarios.md": (
                "# Scenarios\n"
                "## Heading-touching\n"
                "```gherkin\n"
                "Scenario: malformed\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="fail",
        message=(
            "scenarios.md:3 fenced ```gherkin block opening fence "
            "is not preceded by a blank line"
        ),
        path=str(spec_root / "scenarios.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_preserves_first_violation_when_later_file_also_offends(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) preserves the first-violation Finding when a later file also offends.

    First-violation-precedence fixture: BOTH `contracts.md`
    AND `scenarios.md` carry violations. Files are walked
    sorted; the first violation found (in `contracts.md`)
    MUST remain the surfaced Finding even though `scenarios.md`
    is scanned later. Pins the accumulator-precedence rule
    against the case where a naive last-write-wins fold would
    surface `scenarios.md`'s violation instead.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": (
                "# Contracts\n"
                "## Heading-touching\n"
                "```gherkin\n"
                "Scenario: first-violation\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
            "scenarios.md": (
                "# Scenarios\n"
                "## Heading-touching\n"
                "```gherkin\n"
                "Scenario: later-violation\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="fail",
        message=(
            "contracts.md:3 fenced ```gherkin block opening fence "
            "is not preceded by a blank line"
        ),
        path=str(spec_root / "contracts.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_only_walks_top_level_md_files(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) does NOT recurse into history/proposed_changes/templates subtrees.

    Per the `anchor-reference-resolution` walk-set semantic
    (PROPOSAL.md §"Static-phase checks"), the
    gherkin-blank-line-format check inspects only top-level
    `<spec_root>/*.md` files (livespec-shape) or only
    `<spec_root>/SPECIFICATION.md` (minimal-shape). A
    violation seeded inside `<spec_root>/history/v001/
    scenarios.md` MUST NOT trip the check (history snapshots
    are byte-identical copies that inherit the live spec's
    well-formedness via the seed/revise discipline).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n"
                "\n"
                "```gherkin\n"
                "Scenario: well-formed\n"
                "```\n"
                "\n"
                "Trailing prose.\n"
            ),
        },
    )
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    _ = (history_v001 / "scenarios.md").write_text(
        "# Scenarios\n## Heading-touching\n```gherkin\nScenario: foo\n```\n\nTrailing.\n",
        encoding="utf-8",
    )
    proposed_changes = spec_root / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "draft.md").write_text(
        "# Draft\n## Heading-touching\n```gherkin\nScenario: bar\n```\n\nTrailing.\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


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
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_skipped_for_minimal_shape_with_no_gherkin_blocks(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) emits status='skipped' for minimal-shape with no gherkin fences.

    Per `SPECIFICATION/templates/minimal/constraints.md`
    §"Gherkin blank-line format check exemption": when a
    spec_root carries a single-file `SPECIFICATION.md` (the
    minimal-template shape per the `spec_root: "./"`
    convention) AND `SPECIFICATION.md` does NOT contain any
    fenced ` ```gherkin ` blocks, the check MUST be skipped.
    The exemption avoids false-positive failures for spec
    content that has no scenario-style narrative.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root
    _ = (spec_root / "SPECIFICATION.md").write_text(
        "# My project\n\nThis is descriptive prose with no gherkin scenarios.\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="skipped",
        message=("minimal-shape spec_root has no fenced ```gherkin " "blocks — exemption applies"),
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_applies_normally_for_minimal_shape_with_gherkin_blocks(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) applies normally to minimal-shape WHEN gherkin blocks ARE present.

    Per `SPECIFICATION/templates/minimal/constraints.md`
    §"Gherkin blank-line format check exemption" final
    sentence: "When `SPECIFICATION.md` does contain gherkin
    blocks, the check MUST apply normally." This fixture
    seeds a minimal-shape spec_root whose `SPECIFICATION.md`
    contains a well-formed gherkin block; the check yields a
    pass-Finding (NOT skipped).
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
            "```gherkin\n"
            "Scenario: happy path\n"
            "  Given foo\n"
            "  Then bar\n"
            "```\n"
            "\n"
            "Trailing prose.\n"
        ),
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_for_minimal_shape_with_malformed_gherkin_block(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for malformed minimal-shape gherkin.

    Per `SPECIFICATION/templates/minimal/constraints.md`
    §"Gherkin blank-line format check exemption" final
    sentence: "When `SPECIFICATION.md` does contain gherkin
    blocks, the check MUST apply normally." This fixture
    seeds a minimal-shape spec_root whose `SPECIFICATION.md`
    has a heading touching the opening fence; the check
    yields a fail-Finding pointing at the offending fence
    line in `SPECIFICATION.md`.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root
    _ = (spec_root / "SPECIFICATION.md").write_text(
        (
            "# My project\n"
            "## Acceptance scenario\n"
            "```gherkin\n"
            "Scenario: heading-touching\n"
            "```\n"
            "\n"
            "Trailing prose.\n"
        ),
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="fail",
        message=(
            "SPECIFICATION.md:3 fenced ```gherkin block opening fence "
            "is not preceded by a blank line"
        ),
        path=str(spec_root / "SPECIFICATION.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_unmatched_gherkin_fence(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) tolerates an opening fence with no matching closing fence.

    Edge case: a malformed file with an opening ` ```gherkin `
    but no closing ` ``` `. The blank-line-around-fence rule
    cannot evaluate the closing-fence side without a closing
    fence; v1 minimum scope treats the unmatched opener as
    out-of-scope (the broader well-formedness of the markdown
    is the markdown parser's concern, not this check's). The
    check passes the opening-fence side check (preceded by a
    blank line) and does not flag the missing closer.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "scenarios.md": (
                "# Scenarios\n" "\n" "```gherkin\n" "Scenario: never closed\n" "  Given foo\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-gherkin-blank-line-format",
        status="pass",
        message="fenced gherkin blocks are surrounded by blank lines",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert gherkin_blank_line_format.run(ctx=ctx) == IOSuccess(expected)


def test_slug_is_doctor_gherkin_blank_line_format() -> None:
    """The module's `SLUG` constant is the canonical check_id.

    Pins the SLUG ↔ check_id mapping per the static/CLAUDE.md
    convention (slug `gherkin-blank-line-format` ↔ module
    filename `gherkin_blank_line_format.py` ↔ check_id
    `doctor-gherkin-blank-line-format`).
    """
    assert gherkin_blank_line_format.SLUG == "doctor-gherkin-blank-line-format"
