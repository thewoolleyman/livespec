"""Static-phase doctor check: bcp14_keyword_wellformedness.

Per Plan Phase 7 sub-step 7.b +: this check detects malformed BCP 14
(RFC 2119 + RFC 8174) normative keyword usage in spec-text-
bearing markdown files. The v1 minimum scope is the mixed-case
standalone-word rule (`Must`, `Should`, `May`, etc.). Sentence-
level case-inconsistency detection (lowercase `must` in normative
context) moves to the LLM-driven phase.

Applies to all spec-text-bearing trees (main + each sub-spec).
The check walks `<spec_root>/*.md` top-level files only — it
does NOT recurse into `history/`,
`proposed_changes/`, or `templates/` subtrees. This walk-set
semantic is the same as the `anchor-reference-resolution`
check's deliberately-narrow scope: per-version snapshots
inherit the live spec's well-formedness via the seed/revise
byte-identical write discipline.

Detection rules:
  - Mixed-case BCP 14 modal-verb keywords as standalone words
    flag as malformed: `Must`, `Should`, `May`, `Shall`. The
    rule is `\\b<keyword>\\b` so token-boundary non-keywords
    (`Mustang`, `Maybe`, etc.) do NOT trip.
  - The synonymous adjective forms (`Required`, `Recommended`,
    `Optional`) are NOT flagged at the static layer. They are
    common English words (column headers, descriptive prose,
    etc.) that risk significant false-positive rates without
    sentence-level context. Their case-discipline detection
    moves to the LLM-driven phase along with the broader case-
    inconsistency rules.
  - Full-uppercase forms (`MUST`, `SHALL NOT`) are well-formed
    and pass.
  - Full-lowercase forms (`must`, `should`) pass at the static
    layer (deferred to the LLM-driven phase).
  - The first violation found (lexicographically-sorted file,
    first matching line) is surfaced; the check short-circuits
    on the first hit so the user sees one offense at a time.
"""

from __future__ import annotations

import re
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "doctor-bcp14-keyword-wellformedness"

# The four RFC 2119 modal-verb keywords whose mixed-case
# standalone-word forms (capital first letter, lowercase
# remainder) flag as malformed. `MUST NOT`, `SHALL NOT`,
# `SHOULD NOT` decompose into their individual keywords for
# detection — flagging the leading `Must`/`Shall`/`Should` is
# sufficient to surface the violation. The synonymous adjective
# keywords (`Required`, `Recommended`, `Optional`) are NOT in
# this set: they are common English words that risk
# false-positives in column headers + descriptive prose; their
# case-discipline moves to the LLM-driven phase along with the
# broader case-inconsistency rules.
_MIXED_CASE_KEYWORDS: tuple[str, ...] = (
    "Must",
    "Shall",
    "Should",
    "May",
)

# Pre-compiled boundary-respecting alternation. `\b` enforces token
# boundaries so embedded forms (`Mustang`, `Maybe`, `Shallow`,
# `Bust`, `Required-fields`, etc.) do NOT match.
_MIXED_CASE_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(_MIXED_CASE_KEYWORDS) + r")\b",
)


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="BCP 14 normative keywords are well-formed",
        path=None,
        line=None,
        spec_root=str(ctx.spec_root),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
    keyword: str,
) -> Finding:
    """Construct a fail-status Finding naming the first offending keyword.

    The Finding's `path` field embeds the absolute file path so
    the user can locate the violation without re-scanning.
    `line_number` is 1-indexed per editor convention. `keyword`
    is the matched mixed-case form; the message instructs the
    user to use the uppercase form for normative usage.
    """
    relative_name = file_path.name
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{relative_name}:{line_number} mixed-case BCP 14 keyword "
            f"'{keyword}' (use uppercase '{keyword.upper()}' for "
            f"normative usage)"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=str(ctx.spec_root),
    )


def _scan_text_for_violation(
    *,
    text: str,
) -> tuple[int, str] | None:
    """Scan `text` for the first mixed-case BCP 14 keyword violation.

    Splits `text` into lines (preserving 1-indexed line numbers)
    and returns the first `(line_number, keyword)` pair where a
    standalone-word mixed-case keyword matches. Returns None if
    no violation is found. The first-violation short-circuit
    keeps the finding count manageable; the user fixes one
    offense, re-runs, and surfaces the next.
    """
    for line_index, line_text in enumerate(text.splitlines(), start=1):
        match = _MIXED_CASE_PATTERN.search(line_text)
        if match is not None:
            return (line_index, match.group(1))
    return None


def _list_top_level_md_files(
    *,
    spec_root: Path,
) -> IOResult[list[Path], LivespecError]:
    """List `<spec_root>/*.md` top-level files in sorted order.

    Per the v018 Q1 walk-set semantic: the check inspects only
    the top-level `*.md` files at `spec_root`. `fs.list_dir`
    yields every immediate child sorted by name; this helper
    filters to `.md` files and excludes directories. Returns an
    IOResult so the IO-track flows uniformly through `run`.
    """
    return fs.list_dir(path=spec_root).map(
        lambda children: [child for child in children if child.is_file() and child.suffix == ".md"],
    )


def _scan_one_file(
    *,
    ctx: DoctorContext,
    file_path: Path,
) -> IOResult[Finding | None, LivespecError]:
    """Scan one `.md` file for the first BCP14 violation.

    Reads the file via `fs.read_text` and applies
    `_scan_text_for_violation`. Returns:
      - IOSuccess(Finding(status='fail', ...)) when a violation
        is found (first match short-circuit);
      - IOSuccess(None) when the file is well-formed (caller
        continues to the next file).
    """
    return fs.read_text(path=file_path).map(
        lambda text: _build_finding_from_scan(
            ctx=ctx,
            file_path=file_path,
            text=text,
        ),
    )


def _build_finding_from_scan(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
) -> Finding | None:
    """Translate a scan result into a fail-Finding or None.

    Pure helper: maps the `_scan_text_for_violation` tuple
    output to the canonical fail-Finding shape, or None when
    the file is clean.
    """
    violation = _scan_text_for_violation(text=text)
    if violation is None:
        return None
    line_number, keyword = violation
    return _fail_finding(
        ctx=ctx,
        file_path=file_path,
        line_number=line_number,
        keyword=keyword,
    )


def _scan_files_for_first_violation(
    *,
    ctx: DoctorContext,
    files: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Scan files in sorted order; return the first violation Finding.

    Folds the per-file scan: each file's `_scan_one_file` yields
    IOSuccess(Finding | None). The accumulator carries the
    pass-Finding initially; the first file that produces a
    fail-Finding replaces it (short-circuit semantics — once a
    fail is in the accumulator, subsequent files are still
    visited but their results are ignored via the
    accumulator-precedence pattern). When every file is clean,
    the pass-Finding survives and is returned.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for file_path in files:
        accumulator = accumulator.bind(
            lambda current_finding, fp=file_path: _absorb_file_scan(
                ctx=ctx,
                current_finding=current_finding,
                file_path=fp,
            ),
        )
    return accumulator


def _absorb_file_scan(
    *,
    ctx: DoctorContext,
    current_finding: Finding,
    file_path: Path,
) -> IOResult[Finding, LivespecError]:
    """Merge one file's scan result into the running accumulator.

    Always reads the file and applies `_scan_one_file`; the
    accumulator-replacement rule preserves the first fail-
    Finding (i.e., once a fail is in the accumulator, a later
    file's fail does NOT overwrite it). A clean file leaves
    the accumulator unchanged.
    """
    return _scan_one_file(ctx=ctx, file_path=file_path).map(
        lambda maybe_finding: _select_first_finding(
            current_finding=current_finding,
            maybe_new_finding=maybe_finding,
        ),
    )


def _select_first_finding(
    *,
    current_finding: Finding,
    maybe_new_finding: Finding | None,
) -> Finding:
    """Choose between the running accumulator and a new scan result.

    First-violation precedence: if the accumulator already
    holds a fail-Finding, keep it. Otherwise, if the new scan
    yielded a fail-Finding, promote it. A clean new scan
    (None) leaves the accumulator unchanged.
    """
    if current_finding.status == "fail":
        return current_finding
    if maybe_new_finding is None:
        return current_finding
    return maybe_new_finding


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the bcp14-keyword-wellformedness check against `ctx`.

    Walks `<ctx.spec_root>/*.md` top-level files (sorted) and
    scans each for mixed-case BCP 14 keyword violations. On no
    violation yields IOSuccess(Finding(status='pass')); on first
    violation yields IOSuccess(Finding(status='fail', ...))
    naming the offending file + 1-indexed line + matched
    keyword. An empty spec_root (no `.md` files) is vacuously
    well-formed and passes.
    """
    return _list_top_level_md_files(spec_root=ctx.spec_root).bind(
        lambda files: _scan_files_for_first_violation(ctx=ctx, files=files),
    )
