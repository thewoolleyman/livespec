"""Pure derivation of the spec pull-request merge-policy decision.

This module carries the derivation that `SPECIFICATION/non-functional-
requirements.md` requires to exist in exactly ONE implementation every caller
executes, under its shared-CI-logic contract. It performs no I/O: a caller
supplies the already-gathered git and hosting-API observations, and receives
the decision plus the stems it derived.

Two rules here decided wrongly in production and are therefore expressed as
module constants rather than as caller-side flags, so a caller cannot drift
from them silently:

`LOCAL_DIFF_ARGS` suppresses git's rename detection, and
`API_ACCEPTED_STATUSES` accepts the hosting API's move statuses. A ratifying
pull request MOVES the proposal out of `<spec-root>/proposed_changes/` into
`<spec-root>/history/vNNN/proposed_changes/`; git scores that `R100` and the
API reports `renamed`. An added-only filter on BOTH sources therefore missed
the stem and AGREED it had missed it — which the dual-source hardening cannot
catch, because by construction it detects only SOURCE-level divergence.

The asymmetry is deliberate. Widening BOTH sides to detect renames would make
a move that one implementation scores as a rename and the other as
add-plus-delete DISAGREE, resolving derivation FAILURE and hard-blocking
routine ratifications. Taking the heuristic OUT of the comparison on the local
side, while accepting move statuses on the API side, makes both yield the
DESTINATION path however either implementation scores the move.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

__all__: list[str] = [
    "API_ACCEPTED_STATUSES",
    "LOCAL_DIFF_ARGS",
    "ApiFile",
    "Derivation",
    "Outcome",
    "accepted_api_paths",
    "derive",
    "stem_paths",
    "stems_from_paths",
]

Outcome = Literal["auto", "blocked", "governed"]

LOCAL_DIFF_ARGS: tuple[str, ...] = ("--no-renames", "--name-only", "--diff-filter=A")
API_ACCEPTED_STATUSES: frozenset[str] = frozenset({"added", "renamed", "copied"})

_MARKDOWN_SUFFIX = ".md"
_REVISION_SUFFIX = "-revision.md"


@dataclass(frozen=True, kw_only=True, slots=True)
class ApiFile:
    """One changed file as the hosting API reports it."""

    filename: str
    status: str


@dataclass(frozen=True, kw_only=True, slots=True)
class Derivation:
    """The derived decision, the stems it rests on, and the reason to surface."""

    outcome: Outcome
    stems: tuple[str, ...]
    reason: str


def _stem_pattern(*, spec_root: str) -> re.Pattern[str]:
    """Match an archived proposed-change under the main spec root or a sub-spec."""
    root = re.escape(spec_root)
    return re.compile(rf"^{root}/(?:templates/[^/]+/)?history/[^/]+/proposed_changes/[^/]+\.md$")


def accepted_api_paths(*, files: tuple[ApiFile, ...]) -> tuple[str, ...]:
    """Keep the filenames whose status denotes a file arriving at that path."""
    return tuple(entry.filename for entry in files if entry.status in API_ACCEPTED_STATUSES)


def stem_paths(*, paths: tuple[str, ...], spec_root: str) -> tuple[str, ...]:
    """Select archived proposal paths, dropping their `-revision` companions."""
    pattern = _stem_pattern(spec_root=spec_root)
    selected = [
        path
        for path in paths
        if pattern.match(path) is not None and not path.endswith(_REVISION_SUFFIX)
    ]
    return tuple(sorted(selected))


def stems_from_paths(*, paths: tuple[str, ...]) -> tuple[str, ...]:
    """Reduce each path to the proposal stem the control CLI expects."""
    return tuple(path.rsplit("/", 1)[-1].removesuffix(_MARKDOWN_SUFFIX) for path in paths)


def derive(
    *,
    spec_root: str,
    touched_spec_root: bool,
    total_changed_files: int,
    local_paths: tuple[str, ...],
    api_files: tuple[ApiFile, ...],
) -> Derivation:
    """Decide whether the pull request is governed, falls through, or blocks.

    `local_paths` MUST come from a git invocation carrying `LOCAL_DIFF_ARGS`,
    and `api_files` MUST be the hosting API's full changed-file listing with
    statuses intact — this function applies the status filter itself so the
    accepted set cannot drift from the comparison it feeds.
    """
    if not touched_spec_root:
        return Derivation(
            outcome="auto",
            stems=(),
            reason="pull request does not touch the spec root; spec_pr_merge does not apply",
        )
    if total_changed_files == 0:
        return Derivation(
            outcome="blocked",
            stems=(),
            reason=(
                "derivation FAILURE: entirely-empty computed diff, which is "
                "impossible for a genuine pull request"
            ),
        )
    local_stem_paths = stem_paths(paths=local_paths, spec_root=spec_root)
    api_stem_paths = stem_paths(paths=accepted_api_paths(files=api_files), spec_root=spec_root)
    if local_stem_paths != api_stem_paths:
        return Derivation(
            outcome="blocked",
            stems=(),
            reason="derivation FAILURE: local-git and hosting-API derivations disagree",
        )
    if not local_stem_paths:
        return Derivation(
            outcome="auto",
            stems=(),
            reason=(
                "KNOWN-EMPTY: touches the spec root but ratifies no proposal; "
                "falls through to the non-spec eligibility gates unchanged"
            ),
        )
    return Derivation(
        outcome="governed",
        stems=stems_from_paths(paths=local_stem_paths),
        reason="ratifies one or more proposals; the pull-request effective policy governs",
    )
