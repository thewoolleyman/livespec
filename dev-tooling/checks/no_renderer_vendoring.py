"""no_renderer_vendoring — livespec vendors and depends on no diagram renderer.

Enforces `SPECIFICATION/constraints.md`:
livespec MUST NOT vendor rendering binaries or runtimes for any
diagram language (no bundled `plantuml.jar`, no Graphviz dependency,
no Mermaid CLI bundle) AND MUST NOT depend on any such renderer.
Mermaid — livespec's standard and default diagram format — renders
natively wherever markdown is viewed, so livespec needs no renderer at
all; an author needing a diagram type Mermaid lacks renders it OUTSIDE
livespec and commits the resulting image as an opaque asset.

The check scans the consuming repo at `cwd` on two surfaces:

1. `pyproject.toml` dependency declarations — any quoted dependency
   whose distribution name is (or begins with) a known renderer token
   fails (e.g. a `graphviz`, `pydot`, or `mermaid-cli` dependency).
2. `.claude-plugin/scripts/_vendor/` — any vendored entry whose name
   is (or begins with) a known renderer token fails (e.g. a vendored
   `plantuml/` tree, a `graphviz/` bundle, a `mermaid_cli/` package).

A clean tree exits 0; any renderer surfaced exits 1 with a structured
error naming the offender and the surface it was found on.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


# Known diagram-renderer distribution / bundle name tokens (lowercase).
# A dependency or vendored entry whose name equals a token, or begins
# with `<token>-` / `<token>_`, is a renderer and fails the check.
# Covers the spec's named renderers (PlantUML, Graphviz, Mermaid) plus
# their common Python distributions and CLI bundles; extend as new
# renderers appear.
_RENDERER_TOKENS: tuple[str, ...] = (
    "plantuml",
    "graphviz",
    "pygraphviz",
    "pydot",
    "mermaid",
    "mmdc",
    "blockdiag",
    "nomnoml",
    "kroki",
)

_PYPROJECT = Path("pyproject.toml")
_VENDOR_REL = Path(".claude-plugin") / "scripts" / "_vendor"

# A quoted dependency specifier opens with the distribution name: the
# run of name characters immediately after the opening quote (PEP 508
# names are `[A-Za-z0-9]` then `[A-Za-z0-9._-]*`). Comments (`# ...`)
# and bare prose never open with a quote, so they are not matched.
_QUOTED_NAME_RE = re.compile(r"""['"]([A-Za-z0-9][A-Za-z0-9._-]*)""")


def _renderer_token_for(*, name: str) -> str | None:
    """Return the renderer token `name` is, or starts with, else None."""
    lowered = name.lower()
    for token in _RENDERER_TOKENS:
        if lowered == token or lowered.startswith((token + "-", token + "_")):
            return token
    return None


def _pyproject_offenders(*, repo_root: Path) -> list[tuple[str, str]]:
    """(dependency-name, matched-token) pairs declared in pyproject.toml."""
    path = repo_root / _PYPROJECT
    if not path.is_file():
        return []
    offenders: list[tuple[str, str]] = []
    for name in _QUOTED_NAME_RE.findall(path.read_text(encoding="utf-8")):
        token = _renderer_token_for(name=name)
        if token is not None:
            offenders.append((name, token))
    return offenders


def _vendor_offenders(*, repo_root: Path) -> list[tuple[str, str]]:
    """(vendored-entry-name, matched-token) pairs under _vendor/."""
    vendor = repo_root / _VENDOR_REL
    if not vendor.is_dir():
        return []
    offenders: list[tuple[str, str]] = []
    for child in sorted(vendor.iterdir()):
        token = _renderer_token_for(name=child.name)
        if token is not None:
            offenders.append((child.name, token))
    return offenders


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("no_renderer_vendoring")
    cwd = Path.cwd()
    dep_offenders = _pyproject_offenders(repo_root=cwd)
    vendor_offenders = _vendor_offenders(repo_root=cwd)
    if not dep_offenders and not vendor_offenders:
        return 0
    for name, token in dep_offenders:
        log.error(
            "pyproject.toml declares a diagram-renderer dependency",
            check_id="no-renderer-vendoring-dependency",
            dependency=name,
            renderer=token,
        )
    for name, token in vendor_offenders:
        log.error(
            "a diagram renderer is vendored under .claude-plugin/scripts/_vendor/",
            check_id="no-renderer-vendoring-vendored",
            vendored_entry=name,
            renderer=token,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
