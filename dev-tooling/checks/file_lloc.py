"""file_lloc: enforce per-file logical-line-of-code budget.

Per python-skill-script-style-requirements.md §"Complexity
thresholds" lines 1497-1499:

    File ≤ 200 logical lines (custom check at
    `<repo-root>/dev-tooling/checks/file_lloc.py`).

"Logical lines" here means the count of `tokenize.NEWLINE` tokens
emitted by the Python tokenizer for the file's source. A
`tokenize.NEWLINE` token is the END of a logical line of code:
each top-level statement, each function/class signature, each
return / assignment / call statement contributes one. Blank
lines, comment-only lines, and continuation lines (which emit
`tokenize.NL` instead) are NOT counted. Multi-line parenthesized
expressions count as one logical line. This matches how
`ruff PLR0915` and similar tools count function-body LLOC, just
applied at file scope.

Rationale for the budget: 200 logical lines is the empirical
breakpoint above which a single Python module starts hosting
multiple cohesive responsibilities. The rule forces extraction
to sibling helpers, splits long pipelines into separate
modules, and prevents agent-authored code from accreting
unbounded surface in any one file.

Scope: `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`.
Vendored libraries (`_vendor/` substring) and `__pycache__/`
are skipped.
"""

from __future__ import annotations

import logging
import sys
import tokenize
from pathlib import Path

__all__: list[str] = [
    "BUDGET",
    "check_file",
    "count_logical_lines",
    "main",
]


log = logging.getLogger(__name__)

BUDGET = 200

_SCOPE_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin/scripts/livespec"),
    Path(".claude-plugin/scripts/bin"),
    Path("dev-tooling"),
)
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"


def main() -> int:
    """Walk scoped trees; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            for v in check_file(path=path):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("file_lloc: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    try:
        n = count_logical_lines(path=path)
    except (SyntaxError, tokenize.TokenError) as e:
        return [f"tokenize error: {e}"]
    if n > BUDGET:
        return [f"{n} logical lines exceeds budget {BUDGET}"]
    return []


def count_logical_lines(*, path: Path) -> int:
    """Count `tokenize.NEWLINE` tokens emitted for `path`'s source."""
    with path.open("rb") as f:
        return sum(1 for tok in tokenize.tokenize(f.readline) if tok.type == tokenize.NEWLINE)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
