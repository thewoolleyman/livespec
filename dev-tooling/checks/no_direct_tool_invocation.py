"""no_direct_tool_invocation: enforce just-only invocation surfaces.

Per python-skill-script-style-requirements.md canonical target list
line 1899:

    grep: lefthook.yml and .github/workflows/*.yml only invoke
    `just <target>`.

The rule keeps `just` as the single source of truth for every
dev-tooling invocation. CI YAML and pre-commit YAML both
delegate via `just <target>`; direct invocations of `ruff`,
`pyright`, `pytest`, `mutmut`, `lint-imports`, etc. in `run:`
lines are forbidden.

Implementation: line-oriented grep (per the canonical-list
description) over `lefthook.yml` + `.github/workflows/*.yml`.
For each line, strip the trailing comment (`#` onward), then
flag any whole-word occurrence of a forbidden tool name.
Comments themselves are exempt — the rule is about commands,
not documentation.

Forbidden tool tokens (whole-word match, case-sensitive):

    ruff, pyright, pytest, mutmut, mypy, black, isort,
    flake8, lint-imports

Permitted invocation prefixes (the `just` fan-out, plus
documented setup steps):

    just, uv, mise, lefthook, python3 (only when the path
    points at a dev-tooling/checks/ script, but we don't
    need to permit it in YAML — the canonical pattern is
    `just check-<slug>`)

Note: `python3` is NOT forbidden because it's how
`dev-tooling/checks/<name>.py` scripts are invoked from
`justfile`, but YAML files should not invoke them directly.
We only check the YAML invocation surfaces, not the
`justfile`.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

__all__: list[str] = [
    "FORBIDDEN_TOOLS",
    "check_file",
    "main",
]


log = logging.getLogger(__name__)

_LEFTHOOK_PATH = Path("lefthook.yml")
_WORKFLOWS_DIR = Path(".github/workflows")

FORBIDDEN_TOOLS: frozenset[str] = frozenset(
    {
        "ruff",
        "pyright",
        "pytest",
        "mutmut",
        "mypy",
        "black",
        "isort",
        "flake8",
        "lint-imports",
    }
)


def main() -> int:
    """Walk YAML invocation surfaces; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    targets: list[Path] = []
    lefthook = repo_root / _LEFTHOOK_PATH
    if lefthook.is_file():
        targets.append(lefthook)
    workflows = repo_root / _WORKFLOWS_DIR
    if workflows.is_dir():
        targets.extend(sorted(workflows.glob("*.yml")))
        targets.extend(sorted(workflows.glob("*.yaml")))
    for path in targets:
        for v in check_file(path=path):
            failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("no_direct_tool_invocation: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    violations: list[str] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = _strip_comment(line=raw)
        for tool in sorted(FORBIDDEN_TOOLS):
            if _matches_word(text=stripped, word=tool):
                violations.append(
                    f"line {lineno}: direct invocation of `{tool}` forbidden — "
                    f"delegate via `just <target>`",
                )
    return violations


def _strip_comment(*, line: str) -> str:
    """Return `line` with the trailing `# ...` comment stripped.

    Naïve substring split on `#`; YAML strings rarely contain `#`
    in practice, and the rule only matters for un-quoted command
    text. Quoted-string false-positives are accepted as a
    grep-level limitation.
    """
    idx = line.find("#")
    return line[:idx] if idx != -1 else line


def _matches_word(*, text: str, word: str) -> bool:
    """True iff `word` appears in `text` with word-boundary delimiters."""
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text) is not None


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
