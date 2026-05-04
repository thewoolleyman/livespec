"""Body-composition helpers for `livespec.commands.revise`.

Per `commands/CLAUDE.md` § leading-underscore convention: this is
a sibling private module to `revise.py`. Its public API (the
underscore-prefixed names re-exported from revise.py) is consumed
only by `revise.main`'s railway and (transitively, via re-export)
the paired test surface at `tests/livespec/commands/test_revise.py`.

Cycle 5.c.2 extracted the helpers from `revise.py` to keep the
supervisor file under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py` (per `SPECIFICATION/constraints.md`
§"File LLOC ceiling"). This precedent matches
`dev-tooling/checks/_red_green_replay_modes.py` which extracted
the heavy mode handlers from `red_green_replay.py` for the same
LLOC reason.

The helpers are pure-Python compose-and-format functions: no I/O,
no side effects, no railway. Their callers (revise.main + the
fold-style accumulator in `_write_and_move_per_decision`) thread
the inputs (decision dicts, resolved author identifiers,
revised_at timestamp) into them and use the returned strings as
file-content payloads.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import datetime, timezone

from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = []


def _resolve_author(
    *,
    namespace: argparse.Namespace,
    payload: RevisionInput,
    env_lookup: Callable[[str], str | None],
) -> str:
    """Resolve the author identifier per spec.md "Author identifier resolution".

    Four-step precedence: `--author <id>` (CLI) > `LIVESPEC_AUTHOR_LLM`
    (env) > `payload.author` (LLM self-declaration) > literal
    `"unknown-llm"` fallback. The first non-empty value in this
    order wins. Body identical to `propose_change._resolve_author`
    and `critique._resolve_author` per the established DRY-violation-
    accepted convention between private module-internal helpers
    (cross-module calls into private helpers would violate the
    module-private boundary per `commands/CLAUDE.md`).
    """
    if namespace.author:
        return str(namespace.author)
    env_value = env_lookup("LIVESPEC_AUTHOR_LLM")
    if env_value:
        return env_value
    if payload.author:
        return payload.author
    return "unknown-llm"


def _now_utc_iso8601() -> str:
    """Format the current UTC time as ISO-8601 seconds for `revised_at`.

    Matches `propose_change.main`'s `created_at` shape:
    `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`.
    Computed once per `revise` invocation in `main` and threaded
    through to every per-decision `_compose_revision_body` call
    so all revisions in a single `revise` cut carry the same
    `revised_at` stamp.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compose_revision_body(
    *,
    decision: dict[str, object],
    author_human: str,
    author_llm: str,
    revised_at: str,
) -> str:
    """Compose the `<stem>-revision.md` body from a decision dict.

    Per `SPECIFICATION/spec.md` §"Proposed-change and revision file
    formats" §"Revision file format" + `revision_front_matter.schema.json`:
    YAML front-matter with 5 keys (proposal, decision, revised_at,
    author_human, author_llm) plus per-decision-type sections:
    `## Decision and Rationale` always; `## Modifications` when
    `decision: modify`; `## Resulting Changes` when `decision:
    accept` or `modify`; `## Rejection Notes` when `decision:
    reject` (the rejection-flow audit-trail richness Plan Phase 7
    mandates).
    """
    topic = str(decision.get("proposal_topic", ""))
    decision_value = str(decision.get("decision", ""))
    rationale = str(decision.get("rationale", ""))
    sections: list[str] = [
        "---\n"
        f"proposal: {topic}.md\n"
        f"decision: {decision_value}\n"
        f"revised_at: {revised_at}\n"
        f"author_human: {author_human}\n"
        f"author_llm: {author_llm}\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        f"{rationale}\n",
    ]
    if decision_value == "modify":
        modifications = str(decision.get("modifications", ""))
        sections.append(f"\n## Modifications\n\n{modifications}\n")
    if decision_value in ("accept", "modify"):
        sections.append(_compose_resulting_changes_section(decision=decision))
    if decision_value == "reject":
        sections.append(
            "\n## Rejection Notes\n\n"
            'Rejection rationale captured in §"Decision and Rationale" above. '
            "Future re-proposal would need to address that critique.\n",
        )
    return "".join(sections)


def _compose_resulting_changes_section(*, decision: dict[str, object]) -> str:
    """Compose the `## Resulting Changes` section from `resulting_files`.

    Lists the spec-file paths the decision touches as a Markdown
    bullet list. Per the schema, `resulting_files[]` is optional;
    when absent or non-list, the section emits the literal
    `(none)` so the heading still appears (the heading's presence
    signals that this is a working-spec-mutating decision per
    spec.md §"Revision file format" item (4)).
    """
    resulting_files = decision.get("resulting_files", [])
    files_lines: list[str] = []
    if isinstance(resulting_files, list):
        for entry in resulting_files:
            if isinstance(entry, dict):
                path_value = str(entry.get("path", ""))
                files_lines.append(f"- {path_value}")
    files_text = "\n".join(files_lines) if files_lines else "(none)"
    return f"\n## Resulting Changes\n\n{files_text}\n"
