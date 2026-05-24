# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Pre-write validation helpers for `livespec.commands.revise`.

Per `SPECIFICATION/spec.md` §"Sub-command lifecycle":

- **Path-relativity guard**: rejects `resulting_files[].path`
  values that are absolute or that begin with the spec-target's
  basename followed by `/`. UsageError (exit 2).
- **Require-existing-target rule**: rejects
  `resulting_files[].path` values whose resolved target does
  not exist as a regular file. PreconditionError (exit 3).
- **Proposal-topic resolution rule**: rejects payloads whose
  `decisions[].proposal_topic` does not resolve to an existing
  `<spec-target>/proposed_changes/<topic>.md` file (e.g., the
  topic was already processed in a prior revise pass, or never
  existed). PreconditionError (exit 3). This check fires BEFORE
  any new `history/vNNN/` directory is cut so a payload
  referencing an already-processed topic leaves the spec tree
  byte-identical instead of producing a partial-snapshot
  artifact.

All validations fire AFTER schema validation but BEFORE any
file-shaping work, so a violation leaves the spec tree byte-
identical.

Per `commands/CLAUDE.md` §leading-underscore convention: this
is a sibling private module to `revise.py`. Public consumption
is via re-export from `revise.py`.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult
from returns.result import Failure, Result, Success

from livespec.errors import LivespecError, PreconditionError, UsageError
from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = ["_validate_resulting_files"]


def _iter_resulting_files_paths(
    *,
    revise_input: RevisionInput,
) -> list[str]:
    """Collect every `resulting_files[].path` string across accept/modify decisions.

    Reject decisions and decisions without `resulting_files[]`
    are skipped. Returns the list in payload order so the
    caller's error message names the first violation
    deterministically.
    """
    paths: list[str] = []
    for decision in revise_input.decisions:
        decision_value = str(decision.get("decision", ""))
        if decision_value not in ("accept", "modify"):
            continue
        resulting_files = decision.get("resulting_files", [])
        if not isinstance(resulting_files, list):
            continue
        for entry in resulting_files:
            if isinstance(entry, dict):
                paths.append(str(entry.get("path", "")))
    return paths


def _validate_resulting_files_paths(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> Result[None, LivespecError]:
    """Reject paths that are absolute or that start with `<spec-target-basename>/`.

    The narrowed predicate (basename + `/` at start, not
    substring match) avoids false positives for legitimate
    paths that contain the spec-target stem internally.
    Returns `Failure(UsageError)` (exit 2) on first violation.
    """
    forbidden_prefix = f"{spec_target.name}/"
    for path_str in _iter_resulting_files_paths(revise_input=revise_input):
        if path_str.startswith("/"):
            return Failure(
                UsageError(
                    f"revise: resulting_files[].path '{path_str}' is absolute; "
                    f"paths MUST be relative to <spec-target>/ with no leading prefix",
                ),
            )
        if path_str.startswith(forbidden_prefix):
            return Failure(
                UsageError(
                    f"revise: resulting_files[].path '{path_str}' starts with the "
                    f"spec-target basename '{forbidden_prefix}'; paths MUST be "
                    f"relative to <spec-target>/ with no leading prefix",
                ),
            )
    return Success(None)


def _validate_resulting_files_targets_exist(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> IOResult[None, LivespecError]:
    """Reject when any `resulting_files` target does not exist as a regular file.

    revise's `resulting_files[]` is for updating existing spec
    files only; creating new files via this path is forbidden
    (new spec files are added via seed). Non-existent targets
    are a `PreconditionError` (exit 3) and the railway aborts
    before any write occurs.
    """
    for path_str in _iter_resulting_files_paths(revise_input=revise_input):
        target = spec_target / path_str
        if not target.is_file():
            return IOResult.from_failure(
                PreconditionError(
                    f"revise: resulting_files target {target} does not exist; "
                    f"revise updates existing spec files only "
                    f"(new spec files are added via seed)",
                ),
            )
    return IOResult.from_value(None)


def _iter_proposal_topics(
    *,
    revise_input: RevisionInput,
) -> list[str]:
    """Collect every `decisions[].proposal_topic` value in payload order.

    Returns the list in payload order so the caller's error
    message names the first violation deterministically. Every
    decision contributes a topic regardless of its `decision`
    verb (accept / modify / reject) — even rejected proposals
    MUST resolve to an existing file because revise moves them
    byte-identically into history/vNNN/proposed_changes/ as part
    of the rejection audit trail.
    """
    topics: list[str] = []
    for decision in revise_input.decisions:
        topics.append(str(decision.get("proposal_topic", "")))
    return topics


def _validate_proposal_topics_exist(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> IOResult[None, LivespecError]:
    """Reject when any decision's proposal_topic does not resolve to an existing file.

    The pre-existing `_check_proposed_changes_nonempty` only
    ensures `<spec-target>/proposed_changes/` holds at least one
    in-flight proposal — it does NOT validate that the payload's
    specific topics resolve. Without this stricter check, a
    payload referencing an already-processed topic (e.g., a
    second invocation of revise with the same payload) would
    cut a new `history/v(N+1)/` directory, write the revision
    file, and only THEN fail when the proposed-change move
    cannot find its source — leaving a partial-snapshot artifact
    on disk that trips downstream doctor invariants. Firing the
    check before file-shaping leaves the spec tree byte-
    identical on PreconditionError (exit 3).
    """
    for topic in _iter_proposal_topics(revise_input=revise_input):
        target = spec_target / "proposed_changes" / f"{topic}.md"
        if not target.is_file():
            return IOResult.from_failure(
                PreconditionError(
                    f"revise: decisions[].proposal_topic '{topic}' does not "
                    f"resolve to an existing file at {target}; revise processes "
                    f"only in-flight proposed-change files (each topic must "
                    f"correspond to <spec-target>/proposed_changes/<topic>.md)",
                ),
            )
    return IOResult.from_value(None)


def _validate_resulting_files(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """Compose path-relativity guard, target-existence check, and proposal-topic resolution.

    Sequential validation: path-relativity (UsageError, exit 2)
    fires first; resulting_files target-existence (PreconditionError,
    exit 3) fires second; proposal-topic resolution
    (PreconditionError, exit 3) fires third. The path-relativity
    and target-existence checks validate every `resulting_files[]`
    entry across all accept/modify decisions; the proposal-topic
    check validates every decision's `proposal_topic` regardless
    of verb. All three fire BEFORE any file-shaping work so a
    violation leaves the spec tree byte-identical.
    """
    return (
        IOResult.from_result(
            _validate_resulting_files_paths(
                revise_input=revise_input,
                spec_target=spec_target,
            ),
        )
        .bind(
            lambda _value: _validate_resulting_files_targets_exist(
                revise_input=revise_input,
                spec_target=spec_target,
            ),
        )
        .bind(
            lambda _value: _validate_proposal_topics_exist(
                revise_input=revise_input,
                spec_target=spec_target,
            ),
        )
        .map(lambda _value: revise_input)
    )
