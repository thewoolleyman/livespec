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
"""Shared work-item provider seam for the cross-boundary doctor checks.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants": the six work-item integrity checks
(`no-orphan-dependency`, `no-stalled-epic`, `no-duplicate-gap-id`,
`no-stale-gap-tied`, `depends_on-ref-wellformedness`,
`unresolved-spec-commitment`) acquire their work-item data by
invoking the ACTIVE impl-plugin's `list-work-items` thin-transport
wrapper — NOT by a direct JSONL file read. This is plugin-agnostic:
it works for `livespec-impl-plaintext` (a JSONL store) AND for
`livespec-impl-beads` (a Dolt-server tenant) and any future
backend, because every impl-plugin exposes the same
`list-work-items --filter all --json` machine surface emitting a
top-level JSON ARRAY of materialized work-item views (per the
§"Thin-transport skills" required surface).

Wrapper resolution + connection. The active wrapper's absolute path
is read from the `LIVESPEC_IMPL_LIST_WORK_ITEMS` env var (resolved
once by `run_static.py` into `DoctorContext.work_items_provider`).
The backend-specific connection the wrapper needs (e.g. beads'
`BEADS_DOLT_PASSWORD`, `LIVESPEC_BD_PATH`, and the `.beads/`
pointer files read from cwd) is supplied by the CALLER's
environment; this seam runs the wrapper as a subprocess inheriting
that env, from `cwd=ctx.project_root`.

Three-state outcome (no CI regression). The helper returns one of:

- `ProviderUnset` — `ctx.work_items_provider is None` (the env var
  was unset). The check surfaces a `skipped` Finding: "no live
  work-item provider configured". This preserves the hermetic-CI
  behavior (where the env var is unset) so the checks do not
  regress to spurious failures.
- `ProviderUnreachable` — the wrapper invocation failed to connect
  (executable absent → OSError, nonzero exit, or non-array JSON on
  stdout). The check surfaces a `skipped` Finding: "work-item store
  unreachable". A genuine wrapper CONNECTION failure is a skip, NOT
  a fail; only actual invariant violations are `fail`.
- `WorkItemsIndex` — success. Carries `index: dict[str, dict[str,
  Any]]`, the latest-record-per-`id` materialization the checks
  apply their invariant LOGIC against (unchanged from the prior
  direct-JSONL `_materialize_records` shape).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Success, safe
from typing_extensions import assert_never

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import proc

__all__: list[str] = [
    "PROVIDER_ENV_VAR",
    "ProviderOutcome",
    "ProviderUnreachable",
    "ProviderUnset",
    "WorkItemsIndex",
    "load_work_items_index",
    "resolve_provider_path",
    "skip_message",
]


PROVIDER_ENV_VAR: str = "LIVESPEC_IMPL_LIST_WORK_ITEMS"


@dataclass(frozen=True, kw_only=True, slots=True)
class ProviderUnset:
    """No live work-item provider is configured (env var unset)."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ProviderUnreachable:
    """The configured provider could not be reached (connection failure)."""

    detail: str


@dataclass(frozen=True, kw_only=True, slots=True)
class WorkItemsIndex:
    """Materialized latest-record-per-id index of work-items."""

    index: dict[str, dict[str, Any]]


ProviderOutcome = ProviderUnset | ProviderUnreachable | WorkItemsIndex


def skip_message(*, slug_prefix: str, outcome: ProviderUnset | ProviderUnreachable) -> str:
    """Render the standardized skip-reason narration for a check's Finding.

    `slug_prefix` is the check's human-readable slug (e.g.
    `"no-duplicate-gap-id"`). `ProviderUnset` → "no live work-item
    provider configured" (the `LIVESPEC_IMPL_LIST_WORK_ITEMS` env var
    is unset — the hermetic-CI default). `ProviderUnreachable` →
    "work-item store unreachable" plus the connection-failure detail.
    Both are `skipped`, never `fail`.
    """
    match outcome:
        case ProviderUnset():
            return (
                f"{slug_prefix}: no live work-item provider configured "
                f"(set {PROVIDER_ENV_VAR} to the active impl-plugin's "
                f"list-work-items wrapper to enforce); check skipped"
            )
        case ProviderUnreachable(detail=detail):
            return f"{slug_prefix}: work-item store unreachable ({detail}); check skipped"
        case _:
            assert_never(outcome)


def resolve_provider_path(*, env: dict[str, str] | None = None) -> Path | None:
    """Return the active impl-plugin's `list-work-items` wrapper path, or None.

    Reads `LIVESPEC_IMPL_LIST_WORK_ITEMS` from `env` (defaulting to
    the process environment). An unset OR empty value yields None —
    the caller threads that None into `DoctorContext.work_items_provider`
    and each check then surfaces a `skipped` Finding. `env` is
    injectable to keep `run_static.py`'s resolution testable without
    monkeypatching the process environment.
    """
    effective_env = os.environ if env is None else env
    raw = effective_env.get(PROVIDER_ENV_VAR, "")
    if raw == "":
        return None
    return Path(raw)


@safe(exceptions=(json.JSONDecodeError,))
def _raw_json_loads(*, stdout: str) -> Any:
    """`@safe`-lifted call into stdlib json.loads."""
    return json.loads(stdout)


def _materialize_from_array(*, parsed: Any) -> dict[str, dict[str, Any]] | None:
    """Build the latest-record-per-id index from a JSON array of views.

    Returns None when the parsed payload is not a top-level array —
    that shape means the wrapper did not emit the contracted
    `list-work-items --json` surface (treated as unreachable by the
    caller). Array entries that are not dicts, or that lack a string
    `id`, contribute nothing (last-record-per-id wins, matching the
    materialize semantics every impl-plugin store applies).
    """
    if not isinstance(parsed, list):
        return None
    index: dict[str, dict[str, Any]] = {}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        item_id = entry.get("id")
        if not isinstance(item_id, str):
            continue
        index[item_id] = entry
    return index


def _interpret_completed(
    *,
    returncode: int,
    stdout: str,
) -> ProviderOutcome:
    """Map a finished subprocess to a ProviderOutcome.

    A nonzero exit means the wrapper ran but could not satisfy the
    query (no live server, no creds, etc.) → `ProviderUnreachable`.
    A zero exit whose stdout is not valid JSON, or is valid JSON but
    not a top-level array, is also `ProviderUnreachable` (the
    contracted surface was not produced). Otherwise the array
    materializes into a `WorkItemsIndex`.
    """
    if returncode != 0:
        return ProviderUnreachable(
            detail=f"wrapper exited {returncode}",
        )
    parsed_result = _raw_json_loads(stdout=stdout)
    if not isinstance(parsed_result, Success):
        return ProviderUnreachable(detail="wrapper stdout is not valid JSON")
    index = _materialize_from_array(parsed=parsed_result.unwrap())
    if index is None:
        return ProviderUnreachable(detail="wrapper stdout is not a top-level JSON array")
    return WorkItemsIndex(index=index)


def load_work_items_index(*, ctx: DoctorContext) -> IOResult[ProviderOutcome, LivespecError]:
    """Acquire work-items via the active impl-plugin's list-work-items wrapper.

    Returns `IOSuccess(ProviderUnset)` immediately when
    `ctx.work_items_provider is None`. Otherwise invokes the wrapper
    as `python3 <provider> --project-root <project_root> --filter
    all --json` from `cwd=ctx.project_root`, inheriting the caller's
    environment (so the backend's connection prerequisites flow
    through). An OSError at the subprocess boundary (e.g.
    FileNotFoundError when the wrapper path does not exist) is lashed
    into `IOSuccess(ProviderUnreachable)` — a connection-class
    failure is a skip, never a fail. A finished subprocess is
    interpreted by `_interpret_completed`.
    """
    provider = ctx.work_items_provider
    if provider is None:
        unset: ProviderOutcome = ProviderUnset()
        return IOSuccess(unset)
    argv = [
        "python3",
        str(provider),
        "--project-root",
        str(ctx.project_root),
        "--filter",
        "all",
        "--json",
    ]
    return (
        proc.run_subprocess(argv=argv, cwd=ctx.project_root)
        .map(
            lambda completed: _interpret_completed(
                returncode=completed.returncode,
                stdout=completed.stdout,
            ),
        )
        .lash(lambda err: _unreachable_io(detail=f"wrapper invocation failed: {err}"))
    )


def _unreachable_io(*, detail: str) -> IOResult[ProviderOutcome, LivespecError]:
    """Lift a `ProviderUnreachable` onto the IO success track (typed as ProviderOutcome).

    The explicit `ProviderOutcome` return annotation lets pyright unify
    the `.lash` recovery branch with the function's declared
    `IOResult[ProviderOutcome, LivespecError]` signature (the narrow
    `IOSuccess[ProviderUnreachable]` inferred from an inline lambda
    does not unify through the returns library's HKT `lash`).
    """
    outcome: ProviderOutcome = ProviderUnreachable(detail=detail)
    return IOSuccess(outcome)
