"""Pre-write validation helpers for `livespec.commands.revise`.

Per `SPECIFICATION/spec.md` §"Sub-command lifecycle":

- **Path-relativity guard**: rejects `resulting_files[].path`
  values that are absolute or that begin with the spec-target's
  basename followed by `/`. UsageError (exit 2).
- **Require-existing-target rule**: rejects
  `resulting_files[].path` values whose resolved target does
  not exist as a regular file. PreconditionError (exit 3).

Both validations fire AFTER schema validation but BEFORE any
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

__all__: list[str] = []


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


def _validate_resulting_files(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
) -> IOResult[RevisionInput, LivespecError]:
    """Compose path-relativity guard then target-existence check.

    Sequential validation: path-relativity (UsageError, exit 2)
    fires first; target-existence (PreconditionError, exit 3)
    fires second. Both validate every `resulting_files[]` entry
    across all accept/modify decisions; reject decisions are
    not validated.
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
        .map(lambda _value: revise_input)
    )
