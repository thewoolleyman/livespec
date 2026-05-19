"""Next sub-command supervisor.

Per `SPECIFICATION/contracts.md` §"`/livespec-core:next`
spec-side thin-transport skill" + §"Wrapper CLI surface": a
pure-function-of-file-state ranker over the spec-side queue
state. Reads `<spec-target>/proposed_changes/` (count of
in-flight proposals + oldest `created_at` from each proposal's
restricted-YAML front-matter) and `<spec-target>/history/`
(count of `vNNN/` version directories), and emits a
`next_output.schema.json`-conforming JSON payload on stdout
with `{action, reason, urgency}`. No LLM in the ranking path;
no impl-side store reads (cross-side composition is the
project-local orchestration layer's job per `spec.md` §"Three-
layer orchestration architecture").

Ranking heuristic (MVP — doctor-cache integration deferred to a
follow-on once the cache format is formalized via propose-
change):

- Non-empty Proposed Changes queue → action=`revise`. Urgency
  rolls up via two axes (queue depth and oldest-proposal age):
  count ≥ 3 OR oldest ≥ 7 days → `high`; count == 2 OR oldest
  ≥ 1 day → `medium`; otherwise `low`. The two axes are OR-ed
  so either a deep queue OR a long-stale single proposal lifts
  urgency.
- Empty queue AND ≥ `_PRUNE_HISTORY_THRESHOLD` unpruned history
  versions → action=`prune-history`, urgency=`low`. The threshold
  is set conservatively so the recommendation surfaces only when
  history accretion is substantial.
- Empty queue AND short history → action=`none`, urgency=`low`.

`build_parser()` is the pure argparse factory per style doc
§"CLI argument parsing seam"; `main()` is the supervisor that
threads argv through the railway and pattern-matches the final
IOResult to derive the exit code + emit the JSON payload on
stdout (per `commands/CLAUDE.md` exception list: supervisor
`main()` functions are the only place outside `bin/` and
`livespec/doctor/run_static.py` where `sys.stdout.write` is
permitted).
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult, IOSuccess
from returns.result import Failure, Result, Success, safe
from returns.unsafe import unsafe_perform_io
from typing_extensions import assert_never

from livespec.errors import LivespecError, PreconditionError, ValidationError
from livespec.io import cli, fs
from livespec.parse import front_matter, jsonc
from livespec.schemas.dataclasses.next_output import NextOutput
from livespec.validate import next_output as validate_next_output_module

__all__: list[str] = ["build_parser", "main"]


_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
_NEXT_OUTPUT_SCHEMA_PATH = _SCHEMAS_DIR / "next_output.schema.json"
_PROPOSED_CHANGES_README = "README.md"
_HIGH_URGENCY_COUNT_THRESHOLD = 3
_MEDIUM_URGENCY_COUNT_THRESHOLD = 2
_HIGH_URGENCY_AGE_DAYS = 7.0
_MEDIUM_URGENCY_AGE_DAYS = 1.0
_PRUNE_HISTORY_THRESHOLD = 20


def build_parser() -> argparse.ArgumentParser:
    """Construct the next argparse parser without parsing.

    Per `SPECIFICATION/contracts.md` §"Wrapper CLI surface":
    `--project-root <path>` (default `Path.cwd()`) and
    `--spec-target <path>` (defaults to
    `<project-root>/SPECIFICATION/` when omitted).
    `exit_on_error=False` lets argparse signal errors via
    `argparse.ArgumentError` rather than `SystemExit`, per style
    doc §"CLI argument parsing seam".
    """
    parser = argparse.ArgumentParser(prog="next", exit_on_error=False)
    _ = parser.add_argument("--project-root", default=None)
    _ = parser.add_argument("--spec-target", default=None)
    return parser


def _resolve_project_root(*, namespace: argparse.Namespace) -> Path:
    """Resolve --project-root to a Path, defaulting to Path.cwd()."""
    if namespace.project_root is None:
        return Path.cwd()
    return Path(namespace.project_root)


def _resolve_spec_target(*, namespace: argparse.Namespace, project_root: Path) -> Path:
    """Resolve --spec-target to a Path; default <project-root>/SPECIFICATION/.

    The default applies when --spec-target is omitted per the
    `next` row of the §"Wrapper CLI surface" table.
    """
    if namespace.spec_target is None:
        return project_root / "SPECIFICATION"
    return Path(namespace.spec_target)


def _proposal_paths(*, spec_target: Path) -> IOResult[list[Path], LivespecError]:
    """List `<spec-target>/proposed_changes/*.md` excluding the README.

    Sorted lexicographically (via `fs.list_dir`) for deterministic
    iteration order. The skill-owned `proposed_changes/README.md`
    is excluded per `SPECIFICATION/spec.md` §"Sub-command lifecycle"
    revise clause (a) — the README is not an in-flight proposal.
    """
    return fs.list_dir(path=spec_target / "proposed_changes").map(
        lambda entries: [
            entry
            for entry in entries
            if entry.is_file() and entry.suffix == ".md" and entry.name != _PROPOSED_CHANGES_README
        ],
    )


def _front_matter_to_io(
    *,
    text: str,
    path: Path,
) -> IOResult[dict[str, Any], LivespecError]:
    """Lift `parse_front_matter` from Result to IOResult and remap errors.

    The pure front_matter parser returns `ValidationError` (exit
    4 — wire-format violation). For the next ranker, a malformed
    proposal in the spec tree is a project-state precondition
    failure (the spec tree contains an unparseable file); the
    remap to `PreconditionError` lifts the exit code from 4 → 3
    per the §"Lifecycle exit-code table" semantics.
    """
    parse_result = front_matter.parse_front_matter(text=text)
    match parse_result:
        case Success(payload):
            return IOSuccess(payload)
        case Failure(ValidationError() as ve):
            return IOResult.from_failure(
                PreconditionError(f"next: malformed proposal front-matter at {path}: {ve}"),
            )
        case _:
            assert_never(parse_result)


def _proposal_created_at(*, path: Path) -> IOResult[str, LivespecError]:
    """Read a proposal file and return its `created_at` ISO timestamp string.

    Composes fs.read_text -> front_matter parse, then coerces
    the `created_at` field to `str` via `str(... or "")`. A
    missing key or `null` value becomes the empty string, which
    downstream `_parse_iso_age_days` rejects via its canonical-
    `Z`-suffix gate — yielding the same `PreconditionError`
    exit-3 channel that malformed YAML front-matter takes. The
    coercion folds the missing-key / wrong-type / unparseable-
    ISO failure modes into a single branch.
    """
    return (
        fs.read_text(path=path)
        .bind(lambda text: _front_matter_to_io(text=text, path=path))
        .map(lambda fm: str(fm.get("created_at") or ""))
    )


@safe(exceptions=(ValueError,))
def _raw_fromisoformat(*, normalized: str) -> datetime.datetime:
    """Decorator-lifted call into `datetime.fromisoformat`.

    `@safe` from returns lifts the ValueError that
    fromisoformat raises on a malformed input into the Result
    track without an explicit `try/except` in livespec/** —
    keeping the no-except-outside-io invariant intact.
    """
    return datetime.datetime.fromisoformat(normalized)


def _parse_iso_age_days(*, created_at: str, now: datetime.datetime) -> Result[float, LivespecError]:
    """Compute the age in days between `created_at` (ISO 8601) and `now`.

    Accepts the canonical `YYYY-MM-DDTHH:MM:SSZ` shape per
    `proposed_change_front_matter.schema.json`'s `date-time`
    format. The trailing `Z` is stripped and `+00:00` is
    appended before `datetime.fromisoformat` (stdlib 3.10 does
    not accept the `Z` suffix directly). Empty / missing
    `created_at` values arrive here as `""`, which fails the
    ISO parse and surfaces as `Failure(PreconditionError)` —
    the same exit-3 channel as a malformed YAML front-matter.
    """
    base = created_at.rstrip("Z")
    normalized = f"{base}+00:00"
    return (
        _raw_fromisoformat(normalized=normalized)
        .alt(
            lambda exc: PreconditionError(f"next: unparseable created_at {created_at!r}: {exc}"),
        )
        .map(
            lambda parsed: (now - parsed).total_seconds() / 86400.0,
        )
    )


def _collect_oldest_age_days(
    *,
    created_ats: list[str],
    now: datetime.datetime,
) -> Result[float | None, LivespecError]:
    """Compute the maximum age-days across all proposal `created_at` values.

    Returns `Success(None)` when the input list is empty (no
    proposals → no oldest age). Aggregates per-proposal age
    Results via accumulator-style `.bind` so the first failure
    short-circuits and surfaces as `Failure(PreconditionError)`
    — the supervisor maps that to exit 3 per the §"Lifecycle
    exit-code table".
    """
    if not created_ats:
        return Success(None)
    aggregate: Result[list[float], LivespecError] = Success([])
    for created_at in created_ats:
        aggregate = aggregate.bind(
            lambda ages, c=created_at: _parse_iso_age_days(created_at=c, now=now).map(
                lambda age, _ages=ages: [*_ages, age],
            ),
        )
    return aggregate.map(max)


def _history_version_count(*, spec_target: Path) -> IOResult[int, LivespecError]:
    """Count `<spec-target>/history/v*/` directories.

    The ranker treats every `v*`-named child as a version
    directory; pruned-marker directories (containing
    `PRUNED_HISTORY.json`) still count toward the unpruned-
    against-threshold comparison — the marker is the previous
    floor and the surviving versions sit above it. The MVP
    ranker uses raw count; a future widening MAY subtract the
    pruned-marker contribution.
    """
    return fs.list_dir(path=spec_target / "history").map(
        lambda entries: sum(
            1 for entry in entries if entry.is_dir() and entry.name.startswith("v")
        ),
    )


def _rank_revise(
    *,
    proposal_count: int,
    oldest_age_days: float | None,
) -> NextOutput:
    """Construct the `action=revise` NextOutput with urgency-bucket logic.

    Two axes feed urgency: queue depth and oldest-proposal age.
    `high` when either axis trips the high threshold; `medium`
    when either trips the medium threshold; otherwise `low`.
    The two axes are OR-ed so a deep queue lifts urgency even
    when each proposal is fresh, and a single stale proposal
    lifts urgency even when the queue is otherwise shallow.
    """
    if proposal_count >= _HIGH_URGENCY_COUNT_THRESHOLD or (
        oldest_age_days is not None and oldest_age_days >= _HIGH_URGENCY_AGE_DAYS
    ):
        urgency = "high"
    elif proposal_count >= _MEDIUM_URGENCY_COUNT_THRESHOLD or (
        oldest_age_days is not None and oldest_age_days >= _MEDIUM_URGENCY_AGE_DAYS
    ):
        urgency = "medium"
    else:
        urgency = "low"
    age_phrase = (
        f"oldest is ~{oldest_age_days:.1f} days old"
        if oldest_age_days is not None
        else "age unknown"
    )
    reason = f"{proposal_count} proposed change(s) pending; {age_phrase}"
    return NextOutput(action="revise", reason=reason, urgency=urgency)


def _rank(
    *,
    proposal_count: int,
    oldest_age_days: float | None,
    history_version_count: int,
) -> NextOutput:
    """Pure ranker — compose a NextOutput from the three input counts.

    Dispatch order matches the heuristic in the module docstring:
    revise (queue) wins; prune-history (history accretion) is the
    fallback when the queue is empty; none is the
    nothing-pressing terminal.
    """
    if proposal_count >= 1:
        return _rank_revise(proposal_count=proposal_count, oldest_age_days=oldest_age_days)
    if history_version_count >= _PRUNE_HISTORY_THRESHOLD:
        return NextOutput(
            action="prune-history",
            reason=f"{history_version_count} unpruned history versions; consider pruning",
            urgency="low",
        )
    return NextOutput(action="none", reason="No pending spec-side work", urgency="low")


def _now_utc() -> datetime.datetime:
    """Return the current time in UTC with tzinfo set.

    Wrapped for monkeypatch-replacement in tests that want a
    deterministic clock.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def _validate_and_serialize(*, output: NextOutput) -> IOResult[str, LivespecError]:
    """Validate the NextOutput against the schema and serialize to JSON.

    Round-trips the dataclass through `next_output.schema.json`
    via the validator factory so a drift between the dataclass
    fields and the schema enum/required constraints surfaces as
    a `ValidationError` (exit 4) before the supervisor writes a
    malformed payload to stdout.
    """
    return (
        fs.read_text(path=_NEXT_OUTPUT_SCHEMA_PATH)
        .bind(lambda text: IOResult.from_result(jsonc.loads(text=text)))
        .bind(
            lambda schema_dict: IOResult.from_result(
                validate_next_output_module.validate_next_output(
                    payload={
                        "action": output.action,
                        "reason": output.reason,
                        "urgency": output.urgency,
                    },
                    schema=schema_dict,
                ),
            ),
        )
        .map(
            lambda validated: json.dumps(
                {
                    "action": validated.action,
                    "reason": validated.reason,
                    "urgency": validated.urgency,
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
        )
    )


def _collect_proposal_created_ats(
    *,
    paths: list[Path],
) -> IOResult[list[str], LivespecError]:
    """Read each proposal file and return its `created_at` value.

    Aggregates per-proposal IOResults via short-circuiting:
    the first failure halts iteration and propagates to the
    supervisor's pattern-match. Equivalent in spirit to
    `Fold.collect` but spelled out to keep the type annotations
    legible.
    """
    out: list[str] = []
    for path in paths:
        result = _proposal_created_at(path=path)
        unwrapped = unsafe_perform_io(result)
        match unwrapped:
            case Success(value):
                out.append(value)
            case Failure(LivespecError()):
                return result.map(lambda _value, _out=out: _out)
            case _:
                assert_never(unwrapped)
    return IOSuccess(out)


def _verify_spec_target(*, spec_target: Path) -> IOResult[Path, LivespecError]:
    """Confirm the spec target directory exists; lift to PreconditionError otherwise.

    Without this guard, `_proposal_paths` and
    `_history_version_count` would each surface an opaque
    `fs.list_dir` precondition error. Checking the spec-target
    root once up front emits a clearer diagnostic naming the
    missing target.
    """
    if not spec_target.is_dir():
        return IOResult.from_failure(
            PreconditionError(
                f"next: --spec-target does not exist or is not a directory: {spec_target}"
            ),
        )
    return IOSuccess(spec_target)


def _rank_pipeline(*, spec_target: Path) -> IOResult[NextOutput, LivespecError]:
    """Compose the file-state reads into a NextOutput.

    Sequence: verify spec target → list proposal paths → read
    each proposal's `created_at` → count history versions →
    compute oldest age → pure rank.
    """
    return (
        _verify_spec_target(spec_target=spec_target)
        .bind(lambda _path: _proposal_paths(spec_target=spec_target))
        .bind(
            lambda paths: _collect_proposal_created_ats(paths=paths).bind(
                lambda created_ats: _history_version_count(spec_target=spec_target).bind(
                    lambda history_count: IOResult.from_result(
                        _collect_oldest_age_days(
                            created_ats=created_ats,
                            now=_now_utc(),
                        ).map(
                            lambda oldest_age_days: _rank(
                                proposal_count=len(created_ats),
                                oldest_age_days=oldest_age_days,
                                history_version_count=history_count,
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def _emit_payload(*, payload: str) -> IOResult[str, LivespecError]:
    """Write the JSON payload + newline to stdout per the wire contract."""
    sys.stdout.write(f"{payload}\n")
    return IOSuccess(payload)


def main(*, argv: list[str] | None = None) -> int:
    """Next supervisor entry point. Returns the exit code.

    Threads argv through parse_argv → resolve spec-target →
    file-state reads → rank → schema-validate → JSON-serialize →
    stdout emit. Failure(LivespecError) lifts via err.exit_code;
    Success exits 0 after the JSON payload + trailing newline
    is written.
    """
    resolved_argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    parse_result = cli.parse_argv(parser=parser, argv=resolved_argv)
    railway: IOResult[str, LivespecError] = parse_result.bind(
        lambda namespace: _rank_pipeline(
            spec_target=_resolve_spec_target(
                namespace=namespace,
                project_root=_resolve_project_root(namespace=namespace),
            ),
        ).bind(lambda output: _validate_and_serialize(output=output)),
    ).bind(lambda payload: _emit_payload(payload=payload))
    unwrapped = unsafe_perform_io(railway)
    match unwrapped:
        case Success(_):
            return 0
        case Failure(LivespecError() as err):
            return err.exit_code
        case _:
            assert_never(unwrapped)
