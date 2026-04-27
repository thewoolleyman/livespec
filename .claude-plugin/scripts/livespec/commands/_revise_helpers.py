"""Sibling helpers for `commands/revise.py`.

Extracted from `revise.py` at Phase 4 sub-step 14b so the
supervisor module stays under the 200-logical-line budget enforced
by `dev-tooling/checks/file_lloc.py`. The functions here own:

- The `.livespec.jsonc` upward-walk + parse + schema-validate
  chain that resolves the default `--spec-target` (PROPOSAL
  §"revise" lines 2380-2389).
- The `<topic>-revision.md` rendering per PROPOSAL §"Revision
  file format" lines 3027-3050.
- The recursive `_walk_writes` for `resulting_files` updates.

The leading underscore on the module name keeps the helpers as
package-private. Public names are re-exported via `__all__`.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from returns.io import IOFailure, IOResult, IOSuccess
from returns.result import Failure, Success
from typing_extensions import assert_never

from livespec.errors import LivespecError
from livespec.io.fastjsonschema_facade import compile_schema
from livespec.io.fs import find_upward, mkdir_p, read_text, write_text
from livespec.parse.jsonc import parse as parse_jsonc
from livespec.schemas.dataclasses.revise_input import ProposalDecision
from livespec.types import Author, TemplateName
from livespec.validate import livespec_config as validate_livespec_config

__all__: list[str] = [
    "AUTHOR_FALLBACK",
    "LIVESPEC_JSONC",
    "VNNN_RE",
    "compute_next_vnnn",
    "now_iso",
    "render_revision",
    "resolve_default_spec_target",
    "spec_root_for_template",
    "walk_writes",
]


LIVESPEC_JSONC = ".livespec.jsonc"
AUTHOR_FALLBACK = "unknown-llm"
VNNN_RE = re.compile(r"^v(\d+)$")


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_next_vnnn(*, entries: list[Path]) -> str:
    max_n = 0
    for entry in entries:
        m = VNNN_RE.match(entry.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"v{max_n + 1:03d}"


def spec_root_for_template(*, template: TemplateName, project_root: Path) -> Path:
    """Phase 3 minimum-viable mapping (matches seed.py + propose_change.py)."""
    if template == "minimal":
        return project_root
    return project_root / "SPECIFICATION"


def resolve_default_spec_target(*, project_root: Path) -> IOResult[Path, LivespecError]:
    """Walk upward for `.livespec.jsonc`; parse + schema-validate; map template→spec root."""
    return (
        find_upward(start=project_root, name=LIVESPEC_JSONC)
        .bind(lambda jsonc_path: read_text(path=jsonc_path))
        .bind(_parse_and_validate_jsonc)
        .map(
            lambda config: spec_root_for_template(
                template=config.template,
                project_root=project_root,
            ),
        )
    )


def _parse_and_validate_jsonc(text: str) -> IOResult[Any, LivespecError]:
    parsed = parse_jsonc(text=text)
    match parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(jsonc_dict):
            return read_text(path=_schema_path()).bind(
                lambda schema_text: _validate_jsonc(
                    schema_text=schema_text,
                    jsonc_dict=jsonc_dict,
                ),
            )
        case _:
            assert_never(parsed)


def _validate_jsonc(
    *,
    schema_text: str,
    jsonc_dict: dict[str, Any],
) -> IOResult[Any, LivespecError]:
    schema_parsed = parse_jsonc(text=schema_text)
    match schema_parsed:
        case Failure(err):
            return IOFailure(err)
        case Success(schema_dict):
            fast_validator = compile_schema(
                schema_id="livespec_config.schema.json",
                schema=schema_dict,
            )
            validator = validate_livespec_config.make_validator(
                fast_validator=fast_validator,
            )
            validated = validator(payload=jsonc_dict)
            match validated:
                case Failure(err):
                    return IOFailure(err)
                case Success(config):
                    return IOSuccess(config)
                case _:
                    assert_never(validated)
        case _:
            assert_never(schema_parsed)


def _schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas" / "livespec_config.schema.json"


def render_revision(
    *,
    decision: ProposalDecision,
    timestamp: str,
    git_user: str,
    author_llm: Author,
) -> str:
    """Render <topic>-revision.md per PROPOSAL §"Revision file format" lines 3027-3050."""
    body_sections = f"## Decision and Rationale\n\n{decision.rationale}\n"
    if decision.decision == "modify" and decision.modifications is not None:
        body_sections += f"\n## Modifications\n\n{decision.modifications}\n"
    if decision.decision in ("accept", "modify") and decision.resulting_files:
        files_block = "\n".join(f"- {rf.path}" for rf in decision.resulting_files)
        body_sections += f"\n## Resulting Changes\n\n{files_block}\n"
    return (
        f"---\n"
        f"proposal: {decision.proposal_topic}.md\n"
        f"decision: {decision.decision}\n"
        f"revised_at: {timestamp}\n"
        f"author_human: {git_user}\n"
        f"author_llm: {author_llm}\n"
        f"---\n"
        f"\n"
        f"{body_sections}"
    )


def walk_writes(
    *,
    targets: list[tuple[Path, str]],
    index: int,
) -> IOResult[None, LivespecError]:
    """Sequentially mkdir parent + write each (path, content) target."""
    if index >= len(targets):
        return IOSuccess(None)
    path, content = targets[index]
    return (
        mkdir_p(path=path.parent)
        .bind(
            lambda _: write_text(path=path, content=content),
        )
        .bind(
            lambda _: walk_writes(targets=targets, index=index + 1),
        )
    )
