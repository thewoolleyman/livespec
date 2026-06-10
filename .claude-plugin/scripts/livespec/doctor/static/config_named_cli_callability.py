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
"""Static-phase doctor check: config-named-cli-callability.

Per `SPECIFICATION/contracts.md` §"Doctor cross-boundary
invariants" → "`config-named-cli-callability`": for every CLI
named in `.livespec.jsonc` — spec-side per §"Spec-side CLI
contract" and orchestrator-side per §"Orchestrator CLI contract
— the three named CLIs" — the named entry MUST resolve and be
executable. A missing or non-executable resolution fires `fail`
naming the config key and value. The callability test is
zero-shape: the named CLI resolves and is executable; no probe
convention (no required `--version`, `--help`, or ping
subcommand) is part of this invariant.

Resolution semantics for each named argv's first entry:

- the literal `${CLAUDE_PLUGIN_ROOT}` substring expands to the
  `CLAUDE_PLUGIN_ROOT` env var when set, falling back to the
  running package's plugin root (the directory containing
  `scripts/`);
- an entry containing a path separator resolves as a filesystem
  path — relative paths anchor at the project root — and must
  be a file carrying the executable bit;
- a bare command name resolves via PATH lookup.

A missing or unparseable `.livespec.jsonc` yields `skipped`:
`livespec_jsonc_valid` owns that failure mode. A config that
parses but rejects schema validation yields `fail` — the named
CLIs cannot be read, which is itself a wiring failure.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Success

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc
from livespec.schemas.dataclasses.finding import Finding
from livespec.schemas.dataclasses.livespec_config import LivespecConfig
from livespec.types import CheckId, SpecRoot
from livespec.validate.livespec_config import validate_livespec_config

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-config-named-cli-callability")

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "livespec_config.schema.json"
_PLUGIN_ROOT_PLACEHOLDER = "${CLAUDE_PLUGIN_ROOT}"


def _make_finding(*, ctx: DoctorContext, status: str, message: str) -> Finding:
    """Construct this check's Finding with the canonical payload shape."""
    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _plugin_root() -> str:
    """Resolve the livespec plugin root for placeholder expansion.

    The `CLAUDE_PLUGIN_ROOT` env var wins when set (the Claude
    Code harness exports it for installed plugins). Otherwise
    derive it from this module's location: the package lives at
    `<plugin-root>/scripts/livespec/doctor/static/`, so four
    parents up is the plugin root.
    """
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_value:
        return env_value
    return str(Path(__file__).resolve().parents[4])


def _entry_is_callable(*, entry: str, project_root: Path) -> bool:
    """Decide whether one argv-leading entry resolves to an executable.

    Path-shaped entries (containing a separator) must be files
    carrying the executable bit, with relative paths anchored at
    the project root; bare command names resolve via PATH.
    """
    expanded = entry.replace(_PLUGIN_ROOT_PLACEHOLDER, _plugin_root())
    if os.sep in expanded:
        candidate = Path(expanded)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate.is_file() and os.access(candidate, os.X_OK)
    return shutil.which(expanded) is not None


def _named_clis(*, config: LivespecConfig) -> list[tuple[str, list[str]]]:
    """Enumerate every config-named CLI as (config key, argv) pairs.

    The seven spec-side CLIs are always named (core defaults
    materialize when the config omits them); the three
    orchestrator-side CLIs join the enumeration only when the
    optional orchestrator section is configured.
    """
    clis = config.spec_clis
    entries: list[tuple[str, list[str]]] = [
        ("spec_clis.seed", clis.seed),
        ("spec_clis.propose_change", clis.propose_change),
        ("spec_clis.revise", clis.revise),
        ("spec_clis.critique", clis.critique),
        ("spec_clis.doctor", clis.doctor),
        ("spec_clis.prune_history", clis.prune_history),
        ("spec_clis.next", clis.next),
    ]
    if config.orchestrator is not None:
        entries.extend(
            [
                ("orchestrator.spec_reader", config.orchestrator.spec_reader),
                ("orchestrator.gap_capture", config.orchestrator.gap_capture),
                ("orchestrator.drift_capture", config.orchestrator.drift_capture),
            ],
        )
    return entries


def _evaluate(
    *,
    ctx: DoctorContext,
    payload: dict[str, Any],
    schema: dict[str, Any],
) -> Finding:
    """Validate the parsed config and check every named CLI's callability.

    Schema rejection fires `fail` (the named CLIs cannot be
    read); otherwise each named argv's first entry must resolve
    to an executable, and any miss fires `fail` naming every
    offending config key and value.
    """
    validation = validate_livespec_config(payload=payload, schema=schema)
    if not isinstance(validation, Success):
        return _make_finding(
            ctx=ctx,
            status="fail",
            message=(
                "config does not validate against "
                f"livespec_config.schema.json: {validation.failure()}"
            ),
        )
    config = validation.unwrap()
    named = _named_clis(config=config)
    failures = [
        f"{key} = {argv!r} (entry {argv[0]!r} does not resolve to an executable)"
        for key, argv in named
        if not _entry_is_callable(entry=argv[0], project_root=ctx.project_root)
    ]
    if failures:
        return _make_finding(
            ctx=ctx,
            status="fail",
            message="config-named CLI not callable: " + "; ".join(failures),
        )
    return _make_finding(
        ctx=ctx,
        status="pass",
        message=f"all {len(named)} config-named CLIs resolve to executables",
    )


def _load_jsonc(*, path: Path) -> IOResult[Any, LivespecError]:
    """Read + parse one JSONC file onto the IOResult track."""
    return fs.read_text(path=path).bind(
        lambda text: IOResult.from_result(jsonc.loads(text=text)),  # pyright: ignore[reportArgumentType]
    )


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the config-named-cli-callability check against `ctx`.

    Reads `<ctx.project_root>/.livespec.jsonc` plus the packaged
    `livespec_config.schema.json` and evaluates callability per
    the module docstring. Missing/unparseable config recovers to
    a `skipped` Finding via `.lash` — `livespec_jsonc_valid`
    owns surfacing that failure mode as a `fail`.
    """
    config_path = ctx.project_root / ".livespec.jsonc"
    return (
        _load_jsonc(path=config_path)
        .bind(
            lambda payload: _load_jsonc(path=_SCHEMA_PATH).map(
                lambda schema: _evaluate(ctx=ctx, payload=payload, schema=schema),
            ),
        )
        .lash(
            lambda _err: IOSuccess(
                _make_finding(
                    ctx=ctx,
                    status="skipped",
                    message=(
                        "livespec config is missing or unparseable; "
                        "doctor-livespec-jsonc-valid owns that failure mode"
                    ),
                ),
            ),
        )
    )
