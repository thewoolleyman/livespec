"""Pure Result-wrapping shims over `livespec_runtime.cross_repo` parsers.

The runtime library raises `CrossRepoSchemaError` directly when a
typed-union dict fails validation; livespec's no-raise-outside-io
discipline forbids try/except at consumer sites. These shims use
the canonical `@safe(exceptions=(...))` + `.alt(...)` pattern (see
`livespec.parse.jsonc` for the precedent) to convert the
runtime's raise-path into `Failure(ValidationError(...))`.

Two surface functions:

- `parse_entry` — wraps `parse_depends_on_entry` for a single
  typed-dict `depends_on` entry.
- `parse_manifest` — wraps `parse_cross_repo_manifest` for a
  `cross_repo_targets` block.

Both are pure (no I/O); the dict argument MUST be JSON-loadable
shape (typically the materialized result of `jsonc.loads`).
"""

from __future__ import annotations

from typing import Any

from livespec_runtime.cross_repo.errors import CrossRepoSchemaError
from livespec_runtime.cross_repo.types import (
    CrossRepoManifest,
    DependsOnEntry,
    parse_cross_repo_manifest,
    parse_depends_on_entry,
)
from returns.result import Result, safe

from livespec.errors import ValidationError

__all__: list[str] = ["parse_entry", "parse_manifest"]


@safe(exceptions=(CrossRepoSchemaError,))
def _raw_parse_entry(*, parsed: dict[str, Any]) -> DependsOnEntry:
    """`@safe`-lifted call into the runtime's typed-entry parser."""
    return parse_depends_on_entry(parsed=parsed)


def parse_entry(*, parsed: dict[str, Any]) -> Result[DependsOnEntry, ValidationError]:
    """Parse a typed-dict depends_on entry.

    Returns `Success(<typed-entry>)` on a valid kind-discriminated
    dict; `Failure(ValidationError(...))` when the dict is missing
    `kind`, carries an unknown `kind`, or omits per-kind required
    fields.
    """
    return _raw_parse_entry(parsed=parsed).alt(
        lambda exc: ValidationError(f"cross_repo depends_on entry: {exc.detail}"),
    )


@safe(exceptions=(CrossRepoSchemaError,))
def _raw_parse_manifest(*, parsed: dict[str, Any]) -> CrossRepoManifest:
    """`@safe`-lifted call into the runtime's cross_repo_targets parser."""
    return parse_cross_repo_manifest(parsed=parsed)


def parse_manifest(*, parsed: dict[str, Any]) -> Result[CrossRepoManifest, ValidationError]:
    """Parse the `cross_repo_targets` block.

    Returns `Success(<manifest>)` on a valid dict mapping repo slugs
    to target objects each with the REQUIRED `github_url` field;
    `Failure(ValidationError(...))` otherwise.
    """
    return _raw_parse_manifest(parsed=parsed).alt(
        lambda exc: ValidationError(f"cross_repo_targets manifest: {exc.detail}"),
    )
