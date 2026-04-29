"""livespec.commands.resolve_template — supervisor for `bin/resolve_template.py`.

v032 TDD redo cycle 19: smallest impl that drives the cycle-18
outside-in integration test to Green for the built-in `--template
livespec` / `--template minimal` path. Per PROPOSAL.md §"Template
resolution contract" lines 1424-1503:

1. Parse `--project-root <path>` (default `Path.cwd()`) and
   `--template <value>` (optional; v017 Q2 pre-seed flag).
2. When `--template` is `"livespec"` or `"minimal"`, resolve to
   the bundle's built-in path
   `<bundle-root>/specification-templates/<name>` where
   `<bundle-root>` = `Path(__file__).resolve().parents[3]` (per
   PROPOSAL.md lines 1473-1476: from
   `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
   parents[0]=commands/, parents[1]=livespec/, parents[2]=scripts/,
   parents[3]=.claude-plugin/).
3. Emit the resolved absolute POSIX path on stdout as exactly
   one line followed by `\\n` (PROPOSAL.md lines 1455-1459: stdout
   contract is frozen in v1).

`sys.stdout.write` is the sanctioned seam at supervisor scope per
python-skill-script-style-requirements.md §"Output channels"
lines 1749-1756 and `livespec/commands/CLAUDE.md`: "Supervisor
`main()` functions ... `sys.stdout.write` permitted for documented
stdout contracts: `HelpRequested.text`, the resolved-path
single-line output of `resolve_template`. The exemption is
per-`main()` only, not per-helper." No
`livespec/io/cli.py::write_stdout` helper authored — the style
rules name this exact case as one of the three designated
surfaces, so direct `sys.stdout.write` is the cleanest path.

Out of cycle-19 scope (deferred to subsequent cycles per the
outside-in walking direction, each driven by a specific
failure-path test):

- The `.livespec.jsonc` upward-walk path (when `--template` is
  NOT supplied; PROPOSAL.md lines 1437-1442 + 1488-1494). Will
  land when a default-flow test exercises it.
- The user-provided-path branch (when `--template` value is
  not a built-in name; PROPOSAL.md lines 1477-1484). Will land
  when a user-template test exercises it.
- `template.json` validation per PROPOSAL.md lines 1480-1484.
- Exit-3 paths per PROPOSAL.md lines 1488-1494.
- ROP plumbing (`@impure_safe`, `IOResult`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__: list[str] = ["main"]

_BUILTIN_TEMPLATES = frozenset({"livespec", "minimal"})


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="resolve-template", exit_on_error=False)
    parser.add_argument("--project-root", default=None, type=Path)
    parser.add_argument("--template", default=None)
    return parser


def _bundle_root() -> Path:
    """Compute `<bundle-root>` (.claude-plugin/) from this module's location.

    Per PROPOSAL.md lines 1473-1476: from
    `.claude-plugin/scripts/livespec/commands/resolve_template.py`,
    parents[3] is `.claude-plugin/`.
    """
    return Path(__file__).resolve().parents[3]


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:])
    template_value: str | None = args.template
    if template_value in _BUILTIN_TEMPLATES:
        resolved = _bundle_root() / "specification-templates" / template_value
        sys.stdout.write(f"{resolved}\n")
        return 0
    return 0
