"""codex_no_repo_local_adapters — guard the retired repo-local Codex adapters.

Core's v129 spec RETIRED the repo-local Codex adapter model: this repository
ships NO project-local `.agents/skills/livespec-*` adapter directories. The
eight `/livespec:*` operations now ship from the distributed
`livespec-driver-codex` plugin, which resolves CORE's prose and wrappers at
runtime — it MUST NOT point at a repo-local `.agents/skills/*` tree or require
that tree to exist.

This check is the absence/retirement guard. It walks `.agents/skills/` at cwd
and FAILS if any `livespec-*` adapter directory has been re-added:

- `.agents/skills/` does not exist → PASS.
- `.agents/skills/` exists but contains no `livespec-*` child directory → PASS.
- any `livespec-*` child directory exists → FAIL, one structured error per
  offending directory.

It runs even on doc-only commits because a re-added `SKILL.md` is a markdown
change.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics flow
through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at module
import time.
"""

from __future__ import annotations

import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []

_SKILLS_DIR = Path(".agents") / "skills"
_RETIRED_PREFIX = "livespec-"


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("codex_no_repo_local_adapters")


def _repo_local_adapter_dirs(*, cwd: Path) -> list[Path]:
    skills_root = cwd / _SKILLS_DIR
    if not skills_root.is_dir():
        return []
    return sorted(
        child
        for child in skills_root.iterdir()
        if child.is_dir() and child.name.startswith(_RETIRED_PREFIX)
    )


def main() -> int:
    log = _configure_logger()
    cwd = Path.cwd()
    offenders = _repo_local_adapter_dirs(cwd=cwd)

    for offender in offenders:
        log.error(
            "repo-local Codex adapter is retired and must not exist",
            check_id="codex-no-repo-local-adapters",
            path=str(offender.relative_to(cwd)),
            hint=(
                "core's v129 spec retired the repo-local Codex adapter model; "
                "the /livespec:* operations ship from the distributed "
                "livespec-driver-codex plugin, not from .agents/skills/livespec-*"
            ),
        )

    return 1 if offenders else 0


if __name__ == "__main__":
    raise SystemExit(main())
