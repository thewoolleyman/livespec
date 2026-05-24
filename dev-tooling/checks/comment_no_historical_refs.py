"""comment_no_historical_refs — ban historical-bookkeeping references in source comments.

Enforces SPECIFICATION/non-functional-requirements.md §"Comment
discipline" Rule 2 — comments in first-party trees MUST NOT cite
version markers, decision-id markers, phase-numbering markers,
cycle-numbering markers, or commit-reference phrases. The audit
trail of decisions lives in the spec history tree, the version-
control log, and the per-revision proposed-change files; duplicating
those references in source-file comments creates bit-rot risk and
reader-archeology cost.

Walks the in-scope trees (`.claude-plugin/scripts/livespec/`,
`.claude-plugin/scripts/bin/`, `dev-tooling/`, `tests/`) for `.py`
files — applies the spec's reference regex against AST docstrings
and `#`-comment tokens only, so string literals and code identifiers
are not in scope. Walks the in-scope text files (`justfile`,
`lefthook.yml`, `.github/workflows/*.yml`) line-by-line — for each
line, applies the regex against any text after the first `#`.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import ast
import re
import sys
import tokenize
from pathlib import Path
from typing import cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_PYTHON_TARGET_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
    Path("tests"),
)
_TEXT_TARGET_FILES: tuple[Path, ...] = (
    Path("justfile"),
    Path("lefthook.yml"),
)
_WORKFLOWS_DIR: Path = Path(".github") / "workflows"
_EXEMPT_MARKERS: tuple[str, ...] = ("_vendor",)

_HISTORICAL_REF_RE = re.compile(
    r"(?i)\b("
    r"v\d{3}\s*[A-Z]\d"
    r"|per v\d{3}"
    r"|phase\s+\d+"
    r"|cycle\s+\d+"
    r"|this commit"
    r"|the previous (commit|PR)"
    r")\b",
)

_AST_DOCSTRING_HOSTS = ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
_REMINDER = (
    "Comments MUST NOT cite version numbers, decision IDs, phase numbers, "
    "cycle numbers, or commit references — the audit trail lives in "
    "SPECIFICATION/history/, git log, and replay-hook trailers."
)


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("comment_no_historical_refs")


def _is_exempt(*, path: Path) -> bool:
    return any(marker in path.parts for marker in _EXEMPT_MARKERS)


def _python_docstring_hits(*, source: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, _AST_DOCSTRING_HOSTS):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring is None:
            continue
        first = cast(ast.Expr, node.body[0])
        for line_idx, line_text in enumerate(docstring.splitlines()):
            for match in _HISTORICAL_REF_RE.finditer(line_text):
                hits.append((first.lineno + line_idx, match.group(0)))
    return hits


def _python_comment_hits(*, source: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    tokens = list(tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__))
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        for match in _HISTORICAL_REF_RE.finditer(tok.string):
            hits.append((tok.start[0], match.group(0)))
    return hits


def _scan_python_file(*, path: Path) -> list[tuple[int, str]]:
    source = path.read_text(encoding="utf-8")
    return _python_docstring_hits(source=source) + _python_comment_hits(source=source)


def _scan_text_file(*, path: Path) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    source = path.read_text(encoding="utf-8")
    for line_idx, line in enumerate(source.splitlines(), start=1):
        hash_idx = line.find("#")
        if hash_idx < 0:
            continue
        comment = line[hash_idx:]
        for match in _HISTORICAL_REF_RE.finditer(comment):
            hits.append((line_idx, match.group(0)))
    return hits


def _walk_python_targets(*, cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for target in _PYTHON_TARGET_DIRS:
        target_root = cwd / target
        if not target_root.is_dir():
            continue
        for path in sorted(target_root.rglob("*.py")):
            if _is_exempt(path=path):
                continue
            paths.append(path)
    return paths


def _walk_text_targets(*, cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for rel in _TEXT_TARGET_FILES:
        candidate = cwd / rel
        if candidate.is_file() and not _is_exempt(path=candidate):
            paths.append(candidate)
    workflows_root = cwd / _WORKFLOWS_DIR
    if workflows_root.is_dir():
        paths.extend(sorted(workflows_root.glob("*.yml")))
    return paths


def _emit_hits(
    *,
    log: structlog.stdlib.BoundLogger,
    path: Path,
    cwd: Path,
    hits: list[tuple[int, str]],
) -> int:
    for lineno, matched in hits:
        log.error(
            "historical-bookkeeping reference in comment or docstring",
            check_id="comment-no-historical-ref",
            path=str(path.relative_to(cwd)),
            lineno=lineno,
            matched=matched,
            hint=_REMINDER,
        )
    return len(hits)


def main() -> int:
    log = _configure_logger()
    cwd = Path.cwd()
    offenders = 0
    for path in _walk_python_targets(cwd=cwd):
        offenders += _emit_hits(log=log, path=path, cwd=cwd, hits=_scan_python_file(path=path))
    for path in _walk_text_targets(cwd=cwd):
        offenders += _emit_hits(log=log, path=path, cwd=cwd, hits=_scan_text_file(path=path))
    if offenders:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
