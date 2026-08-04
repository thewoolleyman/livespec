"""spec_governance_template - spec-governance defaults block agreement check.

The orchestrator-plugin copier template documents `spec_governance` as a
commented optional block in `.livespec.jsonc.jinja`. That block is intentionally
commented out so a generated repo arms no policy by default, but it still needs
to advertise every API-configurable key and its safe default. This check compares
the commented block against the shipped spec-governance manifest and fails when
the template omits a key or documents a different default.

The reusable consumer-side distribution home is the installed core plugin's
`spec_governance.py --check-default-block <path>` operation, because a governed
repo may read core's installed manifest while core and shared dev-tooling must
not read downstream consumers. This standalone check remains generic machinery
parameterized by paths so core's own template check can keep using the same
comparison without reaching into any sibling repository.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402

__all__: list[str] = []

_MANIFEST_PATH = (
    Path(".claude-plugin")
    / "scripts"
    / "livespec"
    / "spec_governance"
    / "api_configurable_keys.json"
)
_BLOCK_SOURCE_PATH = Path("templates") / "orchestrator-plugin" / ".livespec.jsonc.jinja"
_BLOCK_START = "// Optional \u2014 spec_governance:"
_BLOCK_END = "// Optional \u2014 credential_wrapper:"


class _ManifestRow(TypedDict):
    key: str
    value_type: Literal["enum", "map", "string"]
    safe_default: str | dict[str, str] | None
    per_proposal_override: str | None
    allowed_values: list[str]


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("spec_governance_template")


def _manifest_rows(*, manifest_path: Path) -> list[_ManifestRow]:
    parsed = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(parsed, list):
        return []
    rows: list[_ManifestRow] = []
    for item in cast(list[object], parsed):
        if isinstance(item, dict):
            rows.append(cast(_ManifestRow, item))
    return rows


def _comment_block(*, template_text: str) -> list[str] | None:
    lines = template_text.splitlines()
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip().startswith(_BLOCK_START):
            start_index = index
            break
    if start_index is None:
        return None
    block: list[str] = []
    for line in lines[start_index:]:
        if line.strip().startswith(_BLOCK_END):
            return block
        block.append(line)
    return None


def _documented_defaults(*, block: list[str]) -> dict[str, Any] | None:
    uncommented: list[str] = []
    for line in block:
        stripped = line.strip()
        if not stripped.startswith("//"):
            continue
        content = stripped.removeprefix("//").strip()
        if content.startswith("//"):
            continue
        if content.startswith(('"spec_governance"', "}", '"')):
            uncommented.append(content)
    if not uncommented:
        return None
    parsed = cast(object, json.loads("\n".join(["{", *uncommented, "}"])))
    parsed_dict = cast(dict[str, object], parsed)
    block_value = parsed_dict.get("spec_governance")
    if not isinstance(block_value, dict):
        return None
    return cast(dict[str, Any], block_value)


def _verify_block(
    *,
    cwd: Path,
    manifest_path: Path,
    block_source_path: Path,
    log: structlog.stdlib.BoundLogger,
) -> int:
    resolved_manifest_path = _resolve_path(cwd=cwd, path=manifest_path)
    resolved_block_source_path = _resolve_path(cwd=cwd, path=block_source_path)
    if not resolved_manifest_path.is_file() or not resolved_block_source_path.is_file():
        log.error(
            "spec-governance manifest/block-source files not found",
            check_id="spec-governance-template-missing-files",
            manifest_path=str(manifest_path),
            block_source_path=str(block_source_path),
            hint=(
                "Run from the livespec-core repo root, or pass explicit "
                "--manifest-path and --block-source paths."
            ),
        )
        return 1
    rows = _manifest_rows(manifest_path=resolved_manifest_path)
    block = _comment_block(template_text=resolved_block_source_path.read_text(encoding="utf-8"))
    documented = None if block is None else _documented_defaults(block=block)
    if documented is None:
        log.error(
            "commented spec_governance defaults block is absent or unparsable",
            check_id="spec-governance-template-block-invalid",
            path=str(block_source_path),
        )
        return 1
    expected = {row["key"]: row["safe_default"] for row in rows}
    if documented == expected:
        log.info(
            "commented spec_governance defaults block matches the manifest",
            check_id="spec-governance-template-ok",
            key_count=len(expected),
        )
        return 0
    log.error(
        "commented spec_governance defaults block has drifted from the manifest",
        check_id="spec-governance-template-drift",
        path=str(block_source_path),
        missing=sorted(set(expected) - set(documented)),
        extra=sorted(set(documented) - set(expected)),
        default_drift=sorted(
            key for key, value in expected.items() if documented.get(key) != value
        ),
        hint=(
            "Update the block source so the commented spec_governance block lists "
            "every manifest key at its safe default."
        ),
    )
    return 1


def _resolve_path(*, cwd: Path, path: Path) -> Path:
    return path if path.is_absolute() else cwd / path


def _parse_args(*, argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="spec_governance_template.py")
    _ = parser.add_argument("--manifest-path", default=str(_MANIFEST_PATH))
    _ = parser.add_argument("--block-source", default=str(_BLOCK_SOURCE_PATH))
    return parser.parse_args(argv)


def main() -> int:
    log = _configure_logger()
    namespace = _parse_args(argv=sys.argv[1:])
    return _verify_block(
        cwd=Path.cwd(),
        manifest_path=Path(str(namespace.manifest_path)),
        block_source_path=Path(str(namespace.block_source)),
        log=log,
    )


if __name__ == "__main__":
    raise SystemExit(main())
