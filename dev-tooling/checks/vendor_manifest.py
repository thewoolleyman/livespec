"""vendor_manifest — `.vendor.jsonc` schema-conformance.

Per `python-skill-script-style-requirements.md` line 2096 +
PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md lines 1701-1707:

    Validates `.vendor.jsonc` against a schema that forbids
    placeholder strings — every entry has a non-empty
    `upstream_url`, a non-empty `upstream_ref`, a parseable-ISO
    `vendored_at`, and the `shim: true` flag is present on
    `jsoncomment` (the v026 D1 hand-authored shim) and absent
    on every other entry (post-v027 D1 `typing_extensions` is
    upstream-sourced, NOT a shim).

Cycle 55 pins ONE narrow violation pattern per v032 D1
one-pattern-per-cycle:

    A library entry whose `upstream_ref` is the literal
    placeholder string `"REPLACE_ME"` (or empty string).

The other validation modes (empty `upstream_url`, malformed
`vendored_at`, missing `shim: true` on `jsoncomment`,
spurious `shim: true` elsewhere) are deferred. The current
`.vendor.jsonc` carries concrete `upstream_ref` values for
all five entries plus the correct `shim: true` placement on
`jsoncomment`, so the rule passes today; the check catches
the next agent who lands a placeholder ref.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import jsoncomment  # noqa: E402  — vendor-path-aware import after sys.path insert.
import structlog  # noqa: E402

__all__: list[str] = []


_MANIFEST_PATH = Path(".vendor.jsonc")
_PLACEHOLDER = "REPLACE_ME"


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("vendor_manifest")
    cwd = Path.cwd()
    manifest_file = cwd / _MANIFEST_PATH
    if not manifest_file.is_file():
        return 0
    payload = jsoncomment.loads(manifest_file.read_text(encoding="utf-8"))
    libraries = cast("list[dict[str, object]]", payload.get("libraries", []))
    found_any = False
    for entry in libraries:
        name = entry.get("name")
        upstream_ref = entry.get("upstream_ref")
        if upstream_ref in (_PLACEHOLDER, ""):
            log.error(
                "library entry has placeholder/empty upstream_ref",
                path=str(manifest_file.relative_to(cwd)),
                name=name,
                upstream_ref=upstream_ref,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
