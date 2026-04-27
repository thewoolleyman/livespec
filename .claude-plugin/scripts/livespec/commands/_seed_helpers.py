"""Sibling helpers for `commands/seed.py` (auto-capture cluster).

Extracted from `seed.py` at Phase 4 sub-step 14a so the supervisor
module stays under the 200-logical-line budget enforced by
`dev-tooling/checks/file_lloc.py`. The functions here own the
PROPOSAL §"Auto-capture during seed" obligations: writing the
canonical `seed.md` proposed-change and the paired
`seed-revision.md` under the main spec's `history/v001/proposed_changes/`.

The leading underscore on the module name keeps the helpers as
package-private (no `livespec.commands._seed_helpers` import
outside this directory). Public names are re-exported via
`__all__` for use from `seed.SeedPipeline`.

`get_git_user`'s `IOFailure` (e.g., git is absent or the user
config is incomplete) is caught at the call-site in
`seed.SeedPipeline._write_seed_auto_capture` via `.lash`, which
falls back to `GIT_USER_UNKNOWN` per PROPOSAL §"Git user
fallback".
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io.fs import write_text
from livespec.schemas.dataclasses.seed_input import SeedInput

__all__: list[str] = [
    "now_iso",
    "write_seed_pair",
]


_SEED_AUTHOR = "livespec-seed"
_SEED_TOPIC = "seed"


def now_iso() -> str:
    """UTC ISO-8601 to seconds (no microseconds), with Z suffix."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_seed_pair(
    *,
    payload: SeedInput,
    pc_dir: Path,
    timestamp: str,
    git_user: str,
) -> IOResult[None, LivespecError]:
    """Render + write the seed.md / seed-revision.md pair under `pc_dir`."""
    seed_md_content = _render_seed_md(payload=payload, timestamp=timestamp)
    seed_revision_content = _render_seed_revision_md(
        payload=payload,
        timestamp=timestamp,
        git_user=git_user,
    )
    return write_text(path=pc_dir / "seed.md", content=seed_md_content).bind(
        lambda _: write_text(path=pc_dir / "seed-revision.md", content=seed_revision_content),
    )


def _render_seed_md(*, payload: SeedInput, timestamp: str) -> str:
    targets_block = "\n".join(f"- {entry.path}" for entry in payload.files)
    return (
        f"---\n"
        f"topic: {_SEED_TOPIC}\n"
        f"author: {_SEED_AUTHOR}\n"
        f"created_at: {timestamp}\n"
        f"---\n"
        f"\n"
        f"## Proposal: seed\n"
        f"\n"
        f"### Target specification files\n"
        f"\n"
        f"{targets_block}\n"
        f"\n"
        f"### Summary\n"
        f"\n"
        f"Initial seed of the specification from user-provided intent.\n"
        f"\n"
        f"### Motivation\n"
        f"\n"
        f"{payload.intent}\n"
        f"\n"
        f"### Proposed Changes\n"
        f"\n"
        f"{payload.intent}\n"
    )


def _render_seed_revision_md(
    *,
    payload: SeedInput,
    timestamp: str,
    git_user: str,
) -> str:
    resulting_files_block = "\n".join(f"- {entry.path}" for entry in payload.files)
    return (
        f"---\n"
        f"proposal: seed.md\n"
        f"decision: accept\n"
        f"revised_at: {timestamp}\n"
        f"author_human: {git_user}\n"
        f"author_llm: {_SEED_AUTHOR}\n"
        f"---\n"
        f"\n"
        f"## Decision and Rationale\n"
        f"\n"
        f"Auto-accepted during seed.\n"
        f"\n"
        f"## Resulting Changes\n"
        f"\n"
        f"{resulting_files_block}\n"
    )
