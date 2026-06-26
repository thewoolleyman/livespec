# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: no_spec_section_citation_in_code.

Per SPECIFICATION/constraints.md (the Reference discipline
section): source code MUST NOT cite spec sections via the
section-sign citation form (a section sign directly followed by a
double-quoted heading text). Source code MAY reference spec files
at the FILE level (file-level references survive heading renames),
but MUST NOT name specific headings within those files
(heading-level references rot silently on rename).

This check scans the project's source for the section-sign
citation marker appearing in a Python COMMENT or in a
module/class/function DOCSTRING. The same marker inside ANY OTHER
string literal is legitimate test data / regex / fixture content
and is IGNORED — only comments and docstrings carry the
heading-level citation the rule forbids.

Walk-set:
  - every `*.py` file under `ctx.project_root`, EXCLUDING any path
    that descends through a segment named `archive`, `_vendor`,
    `__pycache__`, `.git`, or `node_modules`, and EXCLUDING the
    spec tree (`ctx.spec_root`);
  - every `skills/<name>/SKILL.md` under `ctx.project_root` — a
    whole-file text scan, since Markdown has no comment/code
    distinction to discriminate against (core ships no skills, but
    the rule is implemented for governed projects that do).

For each `.py` file, `tokenize` surfaces COMMENT tokens and `ast`
surfaces module/class/function docstrings; the marker in either is
a violation. For each `SKILL.md`, any marker occurrence in the raw
text is a violation. The check short-circuits on the first match
in sorted path order, naming the file, the 1-indexed line, and the
offending text.
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-no-spec-section-citation-in-code")

# The forbidden marker: the section sign immediately followed by a
# double quote (the opening of a section-sign citation). The rule
# keys off this two-character prefix; the closing quote is not
# required for the violation to fire (a heading-level citation is
# the offense regardless of how it is terminated).
_SECTION_MARKER: str = '§"'

# Path segments whose presence anywhere in a file's path excludes
# it from the scan: vendored third-party code, byte-cache dirs,
# the git db, node deps, the project virtualenv (installed
# third-party packages are not project source), and frozen
# historical artifacts.
_EXCLUDED_SEGMENTS: frozenset[str] = frozenset(
    {"archive", "_vendor", "__pycache__", ".git", ".venv", "node_modules"},
)

# Top-level directories handed to `fs.list_tree`'s exclude set so
# the recursive walk never descends into them at all. The spec-root
# basename is added dynamically per `ctx`.
_EXCLUDED_TOP_LEVEL: frozenset[str] = frozenset(
    {"archive", ".git", ".venv", "node_modules"},
)


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Construct the canonical pass-status Finding for this check."""
    return Finding(
        check_id=SLUG,
        status="pass",
        message="no source comment or docstring cites a spec section via the section-sign form",
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _fail_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    line_number: int,
    offending: str,
) -> Finding:
    """Construct a fail-status Finding naming the offending citation.

    `line_number` is 1-indexed; `offending` is the literal text
    (the comment string, or a `<docstring>` / `<SKILL.md>` marker)
    that carries the forbidden section-sign citation.
    """
    return Finding(
        check_id=SLUG,
        status="fail",
        message=(
            f"{file_path.name}:{line_number} source cites a spec section "
            f"via the forbidden '§\"…\"' form ({offending}); reference the "
            f"spec FILE level instead — heading-level citations rot on rename"
        ),
        path=str(file_path),
        line=line_number,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _is_excluded(*, path: Path, spec_root: Path) -> bool:
    """Return True iff `path` falls under an excluded segment or the spec tree.

    A path is excluded when any of its segments is in
    `_EXCLUDED_SEGMENTS`, or when it lives inside `spec_root` (the
    spec tree is the domain of `no_cross_spec_reference`, not this
    code-side check).
    """
    if any(segment in _EXCLUDED_SEGMENTS for segment in path.parts):
        return True
    return spec_root in path.parents or path == spec_root


def _comment_violation(*, text: str) -> tuple[int, str] | None:
    """Find the first COMMENT token carrying the section marker, or None.

    Tokenizes `text` and returns `(1-indexed line, comment text)`
    for the first `#`-comment containing the section marker. A
    tokenizer error (e.g. a file that is not valid Python) yields
    None — such files are surfaced via the docstring path's own
    parse, and a genuinely unparseable source file carries no
    AST/token citation this check can localize.
    """
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT and _SECTION_MARKER in tok.string:
                return (tok.start[0], tok.string.strip())
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return None


def _docstring_violation(*, text: str) -> tuple[int, str] | None:
    """Find the first module/class/function docstring carrying the marker.

    Parses `text` to an AST and walks every module, class, and
    function node; the first whose docstring contains the section
    marker yields `(1-indexed line, "<docstring>")`. A `SyntaxError`
    (file is not valid Python) yields None.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(
            node,
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        ):
            docstring = ast.get_docstring(node, clean=False)
            if docstring is not None and _SECTION_MARKER in docstring:
                # `ast.get_docstring` returns non-None only when
                # `node.body[0]` is the docstring expression, so that
                # node's `lineno` is the docstring's source line.
                return (node.body[0].lineno, "<docstring>")
    return None


def _scan_python_text(*, text: str) -> tuple[int, str] | None:
    """Return the first comment-or-docstring marker violation in `text`.

    Comment hits and docstring hits are computed independently;
    the one with the smaller 1-indexed line number wins so the
    surfaced violation is the earliest in the file. Returns None
    when neither a comment nor a docstring cites a section.
    """
    comment_hit = _comment_violation(text=text)
    docstring_hit = _docstring_violation(text=text)
    if comment_hit is None:
        return docstring_hit
    if docstring_hit is None:
        return comment_hit
    return comment_hit if comment_hit[0] <= docstring_hit[0] else docstring_hit


def _scan_skill_text(*, text: str) -> tuple[int, str] | None:
    """Return the first raw marker violation in a SKILL.md whole-file scan.

    Markdown carries no comment/string distinction, so any
    occurrence of the section marker is a violation. Returns
    `(1-indexed line, line text)` for the first hit, or None.
    """
    for line_index, line_text in enumerate(text.splitlines(), start=1):
        if _SECTION_MARKER in line_text:
            return (line_index, line_text.strip())
    return None


def _is_skill_md(*, path: Path) -> bool:
    """Return True iff `path` is a `skills/<name>/SKILL.md` file.

    The whole-file Markdown scan applies only to skill-prose files
    nested directly under a `skills/<name>/` directory and named
    `SKILL.md`.
    """
    if path.name != "SKILL.md":
        return False
    parents = path.parts
    return "skills" in parents


def _scan_one_file(
    *,
    ctx: DoctorContext,
    file_path: Path,
) -> IOResult[Finding | None, LivespecError]:
    """Scan one walk-set file for the first section-citation violation.

    Reads the file via `fs.read_text` and dispatches on suffix:
    `.py` files run the comment+docstring scan; `SKILL.md` files
    run the whole-file Markdown scan. Yields IOSuccess(fail-Finding)
    on a hit, IOSuccess(None) when clean.
    """
    return fs.read_text(path=file_path).map(
        lambda text: _build_finding(ctx=ctx, file_path=file_path, text=text),
    )


def _build_finding(
    *,
    ctx: DoctorContext,
    file_path: Path,
    text: str,
) -> Finding | None:
    """Dispatch the per-suffix scan and translate a hit into a Finding."""
    if file_path.suffix == ".py":
        violation = _scan_python_text(text=text)
    else:
        violation = _scan_skill_text(text=text)
    if violation is None:
        return None
    line_number, offending = violation
    return _fail_finding(
        ctx=ctx,
        file_path=file_path,
        line_number=line_number,
        offending=offending,
    )


def _is_in_scan_set(*, path: Path, spec_root: Path) -> bool:
    """Return True iff `path` is a scannable `.py` or `skills/.../SKILL.md`."""
    if _is_excluded(path=path, spec_root=spec_root):
        return False
    if path.suffix == ".py":
        return True
    return _is_skill_md(path=path)


def _select_first(
    *,
    current: Finding,
    candidate: Finding | None,
) -> Finding:
    """First-violation precedence: keep an existing fail over a later one."""
    if current.status == "fail":
        return current
    if candidate is None:
        return current
    return candidate


def _fold_scan(
    *,
    ctx: DoctorContext,
    files: list[Path],
) -> IOResult[Finding, LivespecError]:
    """Fold the per-file scan into the first-violation Finding.

    The accumulator carries the pass-Finding initially; the first
    file producing a fail-Finding replaces it and subsequent files'
    results are ignored via the first-violation-precedence rule.
    """
    accumulator: IOResult[Finding, LivespecError] = IOSuccess(_pass_finding(ctx=ctx))
    for file_path in files:
        accumulator = accumulator.bind(
            lambda current, fp=file_path: _scan_one_file(ctx=ctx, file_path=fp).map(
                lambda candidate, c=current: _select_first(current=c, candidate=candidate),
            ),
        )
    return accumulator


def _walk_scan_set(*, ctx: DoctorContext) -> IOResult[list[Path], LivespecError]:
    """List every scannable file under `project_root` in sorted order.

    Uses `fs.list_tree` to enumerate the project tree (excluding the
    obvious top-level non-source dirs plus the spec-root basename),
    then filters to the `.py` / `SKILL.md` scan set with the
    per-segment exclusions applied.
    """
    exclude_top_level = _EXCLUDED_TOP_LEVEL | {ctx.spec_root.name}
    return fs.list_tree(
        root=ctx.project_root,
        exclude_top_level=frozenset(exclude_top_level),
    ).map(
        lambda files: [f for f in files if _is_in_scan_set(path=f, spec_root=ctx.spec_root)],
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the no-spec-section-citation-in-code check against `ctx`.

    Walks `project_root` for scannable `.py` and `skills/.../SKILL.md`
    files (excluding vendored, cached, archived, and spec-tree
    paths), then folds each file's comment/docstring (`.py`) or
    whole-file (`SKILL.md`) scan into a single first-violation
    Finding. On no violation yields IOSuccess(Finding(status='pass'));
    on the first section-sign citation yields
    IOSuccess(Finding(status='fail')) naming the file, 1-indexed
    line, and offending text.
    """
    return _walk_scan_set(ctx=ctx).bind(
        lambda files: _fold_scan(ctx=ctx, files=files),
    )
