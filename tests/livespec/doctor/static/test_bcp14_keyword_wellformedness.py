"""Tests for livespec.doctor.static.bcp14_keyword_wellformedness.

Per Plan Phase 7 sub-step 7.b +: the `bcp14-keyword-wellformedness` check
detects malformed BCP 14 (RFC 2119 + RFC 8174) normative keyword
usage in spec-text-bearing markdown files. This is one of four
remaining doctor static checks landing at Phase 7 (alongside
`out-of-band-edits`, `gherkin-blank-line-format`, and
`anchor-reference-resolution`).

Per `bcp14-keyword-
wellformedness`: the check detects mixed-case BCP 14 keywords
appearing as standalone words (`Must`, `Should`, `May`, etc.).
The deferred `static-check-semantics` entry in
`deferred-items.md` reserves the precise enumeration; the v1
minimum scope authored here is the mixed-case standalone-word
rule. Sentence-level context-dependent checks (lowercase `must`
in normative passages) move to the LLM-driven phase per.

Per v018 Q1: this check applies to all spec-text-bearing trees
(main + each sub-spec). The check walks `<spec_root>/*.md`
top-level files only — it does NOT recurse into `history/`,
`proposed_changes/`, or `templates/` subtrees (those are
covered by their own checks; the per-version snapshots inherit
the well-formedness via the seed/revise byte-identical write
discipline).

Detection rules (v1 minimum scope):
  - Mixed-case BCP 14 modal-verb keywords as standalone words:
    `Must`, `Should`, `May`, `Shall` (capitalized first letter,
    lowercase remainder) flag as malformed.
  - Synonymous adjective keywords (`Required`, `Recommended`,
    `Optional`) are NOT flagged by the static check. They are
    common English words (column headers like
    `| Required flags |`, descriptive prose like `Deployment
    is Recommended`) that risk significant false-positive
    rates without sentence-level context. Their case-
    discipline detection moves to the LLM-driven phase per.
  - Token-boundary respecting: `Mustang`, `Bust`, `Maybe`,
    `Shallow` etc. do NOT trip the rule (must be a complete
    word per `\\b<keyword>\\b`).
  - Full-uppercase forms (`MUST`, `SHALL NOT`) are well-formed
    and do not trip.
  - Full-lowercase forms (`must`, `should`) are NOT detected
    by the static check (deferred to the LLM-driven phase);
    spec text using lowercase `must` in descriptive prose
    passes.
  - Non-keyword embedded uppercase words (`GitHub MUST
    validate`) leave the `MUST` intact and the `GitHub`
    untouched — the rule only flags the BCP 14 keywords
    themselves.

Cycle 7.b lands the Red→Green pair for this check.
"""

from __future__ import annotations

from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import bcp14_keyword_wellformedness
from livespec.schemas.dataclasses.finding import Finding
from returns.io import IOSuccess

__all__: list[str] = []


def _seed_spec_root(*, spec_root: Path, files: dict[str, str]) -> None:
    """Materialize `files` (filename -> contents) at `spec_root`.

    Helper for the per-test fixtures: each test seeds the
    spec_root with a small set of `.md` files exercising one
    facet of the BCP14 detection rule. The helper writes UTF-8
    so the on-disk encoding matches the production
    `fs.read_text` UTF-8 convention.
    """
    spec_root.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        _ = (spec_root / name).write_text(content, encoding="utf-8")


def test_run_returns_pass_for_well_formed_uppercase_keywords(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when keywords are well-formed.

    Pass-arm seed: the spec text uses BCP 14 keywords in their
    canonical uppercase form (`MUST`, `MUST NOT`, `SHALL`,
    `SHOULD`, `MAY`). No mixed-case standalone-word violations
    are present, so the check yields a pass-Finding for the
    tree.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n\n"
                "The wrapper MUST validate the input. "
                "Implementations MUST NOT mutate the payload. "
                "Callers SHOULD prefer the typed surface. "
                "The skill MAY emit a warning. "
                "The orchestrator SHALL exit 0 on success.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_text_without_normative_keywords(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when no BCP 14 keywords appear.

    Pass-arm seed: the spec text is descriptive prose with no
    BCP 14 keywords at all. The check yields a pass-Finding —
    absence of normative keywords is not a violation.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n\n"
                "This document describes the system architecture.\n"
                "The components interact via typed messages.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_lowercase_non_normative_usage(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) when keywords are full-lowercase.

    Pass-arm seed: the spec text uses lowercase `must`/`should`/
    `may` in non-normative descriptive prose. Sentence-level
    case-inconsistency detection is deferred to the LLM-driven
    phase; the static check passes on full-lowercase usage because
    RFC 2119 keywords are normative ONLY when uppercase.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n\n"
                "Logging this should help debugging.\n"
                "The component may emit traces if configured.\n"
                "Operators must understand the rollback procedure.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_token_boundary_non_keyword_words(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(pass-Finding) for token-boundary non-keywords.

    Token-boundary edge case: `Mustang`, `Maybe`, `Shallow`,
    `Bust`, `Shouldering`, `Recommended-fields` are NOT BCP 14
    keywords — the leading capital letter happens to start a
    different word. The check uses `\\b<keyword>\\b` boundaries
    so these strings do NOT trip the mixed-case rule.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "spec.md": (
                "# Spec\n\n"
                "Mustang heritage; Maybe later; Shallow depth; "
                "Bust statue; Shouldering responsibility.\n"
            ),
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_for_mixed_case_must(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for mixed-case `Must`.

    Fail-arm seed: the spec text contains a standalone-word
    `Must` (capital M, lowercase rest) in a clearly normative
    context. Per
    `bcp14-keyword-wellformedness`: mixed-case BCP 14 keywords
    as standalone words are malformed. The check yields a
    fail-Finding naming the offending file and line.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_text = "# Spec\n" "\n" "The wrapper Must validate the input.\n"
    _seed_spec_root(spec_root=spec_root, files={"spec.md": spec_text})
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="fail",
        message=(
            "spec.md:3 mixed-case BCP 14 keyword 'Must' "
            "(use uppercase 'MUST' for normative usage)"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_for_mixed_case_should(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for mixed-case `Should`.

    Fail-arm seed: pinning a second mixed-case keyword (`Should`)
    to confirm the keyword set is enumerated correctly. The
    check yields the canonical fail-Finding shape pointing at
    the offending file + line.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_text = "# Spec\n\nCallers Should prefer the typed surface.\n"
    _seed_spec_root(spec_root=spec_root, files={"spec.md": spec_text})
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="fail",
        message=(
            "spec.md:3 mixed-case BCP 14 keyword 'Should' "
            "(use uppercase 'SHOULD' for normative usage)"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_first_violation_when_multiple_files_offend(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for the first offending file.

    Multi-file fixture: `contracts.md` is well-formed,
    `spec.md` has a mixed-case `May`. Files are walked in
    sorted order so the deterministic first violation is the
    one the check surfaces. This pins the multi-file walk
    behavior and the sorted-order discriminator.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": "# Contracts\n\nThe API MUST be stable.\n",
            "spec.md": "# Spec\n\nClients May retry on failure.\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="fail",
        message=(
            "spec.md:3 mixed-case BCP 14 keyword 'May' " "(use uppercase 'MAY' for normative usage)"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_preserves_first_violation_when_later_file_also_offends(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) preserves the first-violation Finding when a later file also offends.

    First-violation-precedence fixture: BOTH `contracts.md`
    AND `spec.md` carry mixed-case BCP 14 violations
    (`Should` and `Must`). Files are walked sorted; the first
    violation found (in `contracts.md`) MUST remain the
    surfaced Finding even though `spec.md` is scanned later.
    Pins the accumulator-precedence rule against the case
    where a naive last-write-wins fold would surface
    `spec.md`'s violation instead.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={
            "contracts.md": "# Contracts\n\nThe API Should be stable.\n",
            "spec.md": "# Spec\n\nClients Must retry on failure.\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="fail",
        message=(
            "contracts.md:3 mixed-case BCP 14 keyword 'Should' "
            "(use uppercase 'SHOULD' for normative usage)"
        ),
        path=str(spec_root / "contracts.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_only_walks_top_level_md_files(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) does NOT recurse into history/proposed_changes/templates subtrees.

    Per the `anchor-reference-resolution` walk-set semantic
    (, generalized to every
    doctor static check that walks `<spec-root>/`), the BCP14
    check inspects only top-level `<spec_root>/*.md` files. A
    `Must`-violation seeded inside `<spec_root>/history/v001/
    spec.md` MUST NOT trip the check (history snapshots are
    byte-identical copies that inherit the live spec's
    well-formedness via the seed/revise discipline).
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    _seed_spec_root(
        spec_root=spec_root,
        files={"spec.md": "# Spec\n\nThe API MUST be stable.\n"},
    )
    history_v001 = spec_root / "history" / "v001"
    history_v001.mkdir(parents=True)
    _ = (history_v001 / "spec.md").write_text(
        "# Spec\n\nThe API Must be stable.\n",
        encoding="utf-8",
    )
    proposed_changes = spec_root / "proposed_changes"
    proposed_changes.mkdir()
    _ = (proposed_changes / "draft.md").write_text(
        "# Draft\n\nClients Should retry.\n",
        encoding="utf-8",
    )
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


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
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_fail_for_mixed_case_shall(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) returns IOSuccess(fail-Finding) for mixed-case `Shall`.

    Fail-arm seed: pins the fourth modal-verb keyword (`Shall`)
    so every member of the v1 detection set has a paired fail-
    arm test. The four-keyword set (Must/Should/May/Shall) is
    the v1 minimum scope; the synonymous adjective keywords
    (Required/Recommended/Optional) are deferred to the LLM-
    driven phase to avoid common-English-word false-positives
    in column headers and descriptive prose.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_text = "# Spec\n\nThe orchestrator Shall exit zero on success.\n"
    _seed_spec_root(spec_root=spec_root, files={"spec.md": spec_text})
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="fail",
        message=(
            "spec.md:3 mixed-case BCP 14 keyword 'Shall' "
            "(use uppercase 'SHALL' for normative usage)"
        ),
        path=str(spec_root / "spec.md"),
        line=3,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_returns_pass_for_mixed_case_required_in_table_header(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) does NOT flag `Required` in column-header / descriptive prose use.

    The synonymous adjective keywords (`Required`, `Recommended`,
    `Optional`) are common English words. The v1 static check
    scope deliberately excludes them to avoid false-positives
    in column headers (`| Required flags |`), descriptive prose
    (`Deployment is Recommended for production`), etc. Their
    case-discipline detection lives in the LLM-driven phase.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    spec_root = project_root / "SPECIFICATION"
    spec_text = (
        "# Spec\n\n"
        "| Sub-command | Required flags | Optional flags |\n"
        "Deployment is Recommended for production.\n"
    )
    _seed_spec_root(spec_root=spec_root, files={"spec.md": spec_text})
    ctx = DoctorContext(project_root=project_root, spec_root=spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_run_passes_for_minimal_template_sub_spec_layout(
    *,
    tmp_path: Path,
) -> None:
    """run(ctx) handles the minimal sub-spec layout (well-formed text).

    Per v018 Q1: this check applies to sub-spec trees too. The
    minimal sub-spec under `<main_spec_root>/templates/minimal/`
    uses the multi-file livespec layout per
    SPECIFICATION/templates/minimal/constraints.md
    §"Single-file end-user output" final paragraph; this
    fixture mirrors that layout and asserts the check passes
    when the sub-spec text is well-formed.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()
    main_spec_root = project_root / "SPECIFICATION"
    sub_spec_root = main_spec_root / "templates" / "minimal"
    _seed_spec_root(
        spec_root=sub_spec_root,
        files={
            "spec.md": "# Sub-spec\n\nProjects MUST adopt this layout.\n",
            "constraints.md": "# Constraints\n\nSub-trees SHOULD inherit.\n",
        },
    )
    ctx = DoctorContext(project_root=project_root, spec_root=sub_spec_root)
    expected = Finding(
        check_id="doctor-bcp14-keyword-wellformedness",
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(sub_spec_root),
    )
    assert bcp14_keyword_wellformedness.run(ctx=ctx) == IOSuccess(expected)


def test_slug_is_doctor_bcp14_keyword_wellformedness() -> None:
    """The module's `SLUG` constant is the canonical check_id.

    Pins the SLUG ↔ check_id mapping per the static/CLAUDE.md
    convention (slug `bcp14-keyword-wellformedness` ↔ module
    filename `bcp14_keyword_wellformedness.py` ↔ check_id
    `doctor-bcp14-keyword-wellformedness`).
    """
    assert bcp14_keyword_wellformedness.SLUG == "doctor-bcp14-keyword-wellformedness"
