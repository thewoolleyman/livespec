"""canonical_slugs_projection — project + verify the canonical-slug template data file.

Per livespec/SPECIFICATION/contracts.md Template gate, the canonical check-slug set
that `templates/orchestrator-plugin/justfile.jinja` stamps MUST flow as a
committed STATIC DATA file — a release-time projection of
`livespec_dev_tooling.canonical_checks` (the single source of truth)
written to `templates/orchestrator-plugin/canonical-slugs.yml` — NOT computed
at render time by a copier `_jinja_extension`. The consumer
`copier update --vcs-ref=master` path reads only the committed data
file, so the canonical block renders import-free and correct (copier
clones the template to an ephemeral checkout with no PYTHONPATH
injection, where a render-time import of the dev-tooling module cannot
resolve).

This module is both the release-time PROJECTION writer and the
anti-drift VERIFY gate:

- **Verify mode (default, `python3 canonical_slugs_projection.py`).**
  Parses the committed `templates/orchestrator-plugin/canonical-slugs.yml`
  and asserts it equals `canonical_check_slugs()` in set AND order;
  exits non-zero with a structured drift diagnostic on any mismatch
  (missing file, missing slugs, extra slugs, or out-of-order). Wired
  into `just check` and CI so the projection can never silently drift
  from the source of truth.
- **Write mode (`--write`).** Regenerates the committed file from the
  source of truth; exits 0. Invoked by `just stamp-canonical-slugs`
  on the release path.

Data-file format: a YAML sequence of kebab-case `check-<slug>`
barewords, one per line (`- check-<slug>`), alphabetically sorted (the
source guarantees the ordering). The line-oriented `- <slug>` shape is
the single contract this module's writer, this module's parser, AND
`justfile.jinja`'s `{% include %}`-then-line-parse loop all agree on,
so no YAML library is needed on any path.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_YAML_REL = Path("templates") / "orchestrator-plugin" / "canonical-slugs.yml"
_HEADER_LINES: tuple[str, ...] = (
    "# Canonical check-slug aggregate — release-time projection of",
    "# livespec_dev_tooling.canonical_checks (the single source of truth).",
    "#",
    "# DO NOT hand-edit. Regenerate via `just stamp-canonical-slugs`; the",
    "# `check-canonical-slugs-projection` gate fails if this file drifts from",
    "# livespec_dev_tooling.canonical_checks.canonical_check_slugs().",
    "#",
    "# Consumed by templates/orchestrator-plugin/justfile.jinja as committed copier",
    "# template DATA so the canonical `check:` aggregate renders import-free on",
    "# both the smoke-check flow AND the consumer `copier update` flow. See",
    '# livespec/SPECIFICATION/contracts.md §"Shared code sync —',
    '# livespec-dev-tooling" → Template gate.',
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
    return structlog.get_logger("canonical_slugs_projection")


def _render_yaml(*, slugs: tuple[str, ...]) -> str:
    """Render the canonical-slug tuple as the committed data-file content.

    A YAML sequence of `- <slug>` lines under a fixed header comment,
    matching the line-oriented shape `justfile.jinja` and
    `_parse_committed_slugs` agree on.
    """
    lines = list(_HEADER_LINES)
    lines.extend(f"- {slug}" for slug in slugs)
    return "\n".join(lines) + "\n"


def _parse_committed_slugs(*, yaml_path: Path) -> tuple[str, ...]:
    """Parse the committed data file into a slug tuple, preserving file order.

    Reads the same line-oriented `- <slug>` shape `_render_yaml`
    emits: blank lines and `#`-comment lines are ignored; every other
    line is a YAML sequence item (`- <slug>`) whose `- ` prefix is
    stripped and whose remainder is the slug.
    """
    text = yaml_path.read_text(encoding="utf-8")
    slugs: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        slugs.append(line.removeprefix("- ").strip())
    return tuple(slugs)


def _canonical_slugs() -> tuple[str, ...]:
    from livespec_dev_tooling.canonical_checks import canonical_check_slugs

    return canonical_check_slugs()


def _write_projection(*, log: structlog.stdlib.BoundLogger, cwd: Path) -> int:
    slugs = _canonical_slugs()
    yaml_path = cwd / _YAML_REL
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    _ = yaml_path.write_text(_render_yaml(slugs=slugs), encoding="utf-8")
    log.info(
        "canonical-slugs projection written",
        check_id="canonical-slugs-projection-written",
        path=str(_YAML_REL),
        slug_count=len(slugs),
    )
    return 0


def _verify_projection(*, log: structlog.stdlib.BoundLogger, cwd: Path) -> int:
    yaml_path = cwd / _YAML_REL
    if not yaml_path.is_file():
        log.error(
            "committed canonical-slugs.yml not found",
            check_id="canonical-slugs-projection-missing-file",
            path=str(_YAML_REL),
            hint="Run `just stamp-canonical-slugs` from the livespec repo root.",
        )
        return 1
    expected = _canonical_slugs()
    committed = _parse_committed_slugs(yaml_path=yaml_path)
    if committed == expected:
        log.info(
            "canonical-slugs projection matches the source of truth",
            check_id="canonical-slugs-projection-ok",
            slug_count=len(expected),
        )
        return 0
    log.error(
        "committed canonical-slugs.yml has drifted from livespec_dev_tooling.canonical_checks",
        check_id="canonical-slugs-projection-drift",
        expected_count=len(expected),
        committed_count=len(committed),
        missing=sorted(set(expected) - set(committed)),
        extra=sorted(set(committed) - set(expected)),
        out_of_order=committed != tuple(sorted(committed)),
        hint="Run `just stamp-canonical-slugs` to regenerate the projection.",
    )
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="canonical-slugs-projection",
        description=(
            "Verify (default) or --write the committed "
            "templates/orchestrator-plugin/canonical-slugs.yml projection of "
            "livespec_dev_tooling.canonical_checks."
        ),
    )
    _ = parser.add_argument(
        "--write",
        action="store_true",
        help="Regenerate the committed canonical-slugs.yml from the source of truth.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    log = _configure_logger()
    cwd = Path.cwd()
    if args.write:
        return _write_projection(log=log, cwd=cwd)
    return _verify_projection(log=log, cwd=cwd)


if __name__ == "__main__":
    raise SystemExit(main())
