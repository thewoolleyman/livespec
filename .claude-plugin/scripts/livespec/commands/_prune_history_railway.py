"""File-shaping + skip-resolution railway stages for prune-history.

Extracted from `prune_history.py` at cycle 6.c.9 so the parent
file's LLOC stays under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py`. The split is purely
organizational; the behavior is identical to the inline original.

Stages: stdout-finding emitters (`_emit_*_finding`), the
`_resolve_skip` helper that implements the v012 spec.md
§"Pre-step skip control" 4-rule resolution matrix, and the
`_invoke_pre_step_doctor` helper (cycle 6.c.10) that fires
`bin/doctor_static.py` as a subprocess and folds fail-status
findings onto the IOFailure track.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs, proc
from livespec.parse import jsonc

__all__: list[str] = [
    "_build_pruned_history_marker",
    "_emit_no_op_finding",
    "_emit_pre_step_skipped_finding",
    "_emit_pruned_finding",
    "_find_max_version",
    "_invoke_pre_step_doctor",
    "_oldest_below_has_pruned_marker",
    "_resolve_skip",
    "_v_dirs_below_threshold",
]


_BIN_DIR = Path(__file__).resolve().parents[2] / "bin"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"


def _find_max_version(*, children: list[Path]) -> int:
    """Compute the highest `vNNN` integer suffix among directory children.

    Walks `children` looking for `vNNN` directories; tracks the
    maximum N found; returns 0 when no `vNNN` children are present.
    Non-directory entries and non-`v\\d+` names are skipped.
    """
    max_version = 0
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        max_version = max(max_version, int(suffix))
    return max_version


def _oldest_below_has_pruned_marker(*, children: list[Path], max_version: int) -> bool:
    """Whether the smallest-K v-directory (K < max_version) holds a PRUNED_HISTORY.json.

    Per v012 spec.md no-op short-circuit (ii): when the oldest
    surviving v-directory below the current max already carries a
    `PRUNED_HISTORY.json` marker, no full versions remain to prune
    below the prior marker. `children` is pre-sorted by
    `fs.list_dir`, so the FIRST eligible v-directory encountered
    IS the smallest-K; we return its marker presence directly.
    Returns False when no eligible v-directory exists below
    `max_version`.
    """
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        if version >= max_version:
            continue
        return (child / "PRUNED_HISTORY.json").is_file()
    return False


def _v_dirs_below_threshold(*, children: list[Path], max_version: int) -> list[Path]:
    """Return the list of `vK/` paths in `children` where K < max_version - 1.

    Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle"
    prune-history paragraph step (c): the wrapper deletes every
    `<spec-root>/history/vK/` where K < N-1. With N=4, that
    means K ∈ {1, 2} (v003 = v(N-1) is preserved at this cycle;
    its replacement-with-marker happens at 6.c.7). Pure helper
    so unit tests cover each filter branch without filesystem
    I/O. Mirrors `_find_max_version` and `_resolve_first`'s
    defensive guards (non-directory entries, non-`v`-prefixed
    names, `v<non-digits>` suffixes are all skipped).
    """
    threshold = max_version - 1
    paths: list[Path] = []
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        if version >= threshold:
            continue
        paths.append(child)
    return paths


def _build_pruned_history_marker(*, first: int, last: int) -> str:
    """Build the canonical `PRUNED_HISTORY.json` body per v012 spec.md step (d).

    The marker is exactly `{"pruned_range": [first, N-1]}` — no
    timestamps, git SHAs, or identity fields (no-metadata
    invariant; git commit metadata already provides that audit
    context). Pure helper so unit tests cover the JSON shape
    without filesystem I/O.
    """
    return json.dumps({"pruned_range": [first, last]})


def _emit_pruned_finding(*, first: int, last: int) -> None:
    """Write the canonical `prune-history-pruned` pass finding to stdout.

    Per v012 spec.md prune-history paragraph: the wrapper emits a
    single-finding JSON document to stdout describing the
    completed prune. The `commands/`-tree exemption in the
    `check-no-write-direct` allowlist permits this stdout-write.
    `first` and `last` are interpolated into the human-readable
    message; the structured payload preserves them as the
    canonical pruned-range pair.
    """
    payload = {
        "findings": [
            {
                "check_id": "prune-history-pruned",
                "status": "pass",
                "message": (
                    f"pruned v{first:03d}..v{last:03d} into v{last:03d}/PRUNED_HISTORY.json"
                ),
            },
        ],
    }
    _ = sys.stdout.write(json.dumps(payload) + "\n")


def _emit_no_op_finding() -> None:
    """Write the canonical prune-history-no-op skipped finding to stdout.

    Per v012 spec.md prune-history paragraph: the wrapper emits a
    single-finding `{"findings": [{"check_id": "prune-history-
    no-op", "status": "skipped", "message": "..."}]}` JSON document
    to stdout. The commands/-tree exemption in the
    `check-no-write-direct` allowlist permits this stdout-write.
    """
    payload = {
        "findings": [
            {
                "check_id": "prune-history-no-op",
                "status": "skipped",
                "message": (
                    "nothing to prune; oldest surviving history is " "already PRUNED_HISTORY.json"
                ),
            },
        ],
    }
    _ = sys.stdout.write(json.dumps(payload) + "\n")


def _emit_pre_step_skipped_finding() -> None:
    """Write the canonical pre-step-skipped finding to stdout.

    Per v012 spec.md §"Pre-step skip control": when the resolved
    skip value is True (either via the `--skip-pre-check` flag at
    cycle 6.c.8 or via the `.livespec.jsonc`
    `pre_step_skip_static_checks` config key at cycle 6.c.9), the
    wrapper MUST emit a single-finding `{"findings": [{"check_id":
    "pre-step-skipped", "status": "skipped", "message":
    "pre-step checks skipped by user config or
    --skip-pre-check"}]}` JSON document to stdout. The commands/-
    tree exemption in the `check-no-write-direct` allowlist
    permits this stdout-write.
    """
    payload = {
        "findings": [
            {
                "check_id": "pre-step-skipped",
                "status": "skipped",
                "message": ("pre-step checks skipped by user config " "or --skip-pre-check"),
            },
        ],
    }
    _ = sys.stdout.write(json.dumps(payload) + "\n")


def _resolve_skip_from_config_text(*, text: str) -> bool:
    """Parse `.livespec.jsonc` body and extract `pre_step_skip_static_checks`.

    Per v012 spec.md §"Pre-step skip control" rule (3): default is
    False when the key is absent. Malformed JSONC is treated as
    default-False defensively — `livespec_jsonc_valid` is the
    dedicated mechanism for surfacing malformed configs to the
    user; the prune-history wrapper's body-level concern is only
    the boolean skip resolution. `value_or({})` collapses the
    parse-failure track into an empty dict so the subsequent
    `.get(..., False)` consistently returns the default.
    """
    parsed: dict[str, object] = jsonc.loads(text=text).value_or({})
    raw = parsed.get("pre_step_skip_static_checks", False)
    return bool(raw)


def _resolve_skip(
    *,
    namespace: argparse.Namespace,
    project_root: Path,
) -> IOResult[bool, LivespecError]:
    """Resolve the effective skip value per v012 spec.md §"Pre-step skip control".

    Implements the 4-rule resolution matrix: (1) `--skip-pre-
    check` → True; (2) `--run-pre-check` → False (overrides
    config); (3) neither flag → read `.livespec.jsonc`
    `pre_step_skip_static_checks` (default False); (4) both
    flags is rejected upstream by argparse's mutually-exclusive
    group. Missing or malformed `.livespec.jsonc` defaults to
    False defensively. Returns IOResult so the railway can
    thread the decision through `_run_prune` without lifting
    out of the I/O monad.
    """
    if namespace.skip_pre_check:
        skip_true: bool = True
        return IOResult.from_value(skip_true)
    if namespace.run_pre_check:
        skip_false: bool = False
        return IOResult.from_value(skip_false)
    config_path = project_root / ".livespec.jsonc"
    if not config_path.is_file():
        skip_default: bool = False
        return IOResult.from_value(skip_default)
    return fs.read_text(path=config_path).map(
        lambda text: _resolve_skip_from_config_text(text=text),
    )


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decorator-lifted strict-JSON decode for the pre-step doctor stdout contract."""
    return json.loads(text)


def _fold_pre_step_doctor_completed_process(
    *,
    completed: subprocess.CompletedProcess[str],
) -> IOResult[None, LivespecError]:
    """Parse the pre-step doctor subprocess's stdout JSON; fold fail findings -> Failure.

    Mirror of the post-step fold in `_seed_railway_emits._fold_doctor_completed_process`,
    specialized to the pre-step contract: when one or more
    findings carry `status == "fail"`, the wrapper MUST short-
    circuit with `IOFailure(PreconditionError)` so the supervisor
    pattern-match lifts to exit 3 per PROPOSAL.md §"Sub-command
    lifecycle orchestration". The doctor's stdout is propagated
    intact via the helper's caller (the LLM-narration layer in
    SKILL.md prose surfaces the structured findings to the user;
    the wrapper does not add ad-hoc stderr text).
    """
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return IOResult.from_failure(
            PreconditionError(
                f"pre-step doctor stdout malformed JSON: {parsed.failure()}",
            ),
        )
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return IOResult.from_failure(
            PreconditionError("pre-step doctor stdout missing 'findings' key"),
        )
    findings_value = payload["findings"]
    if not isinstance(findings_value, list):
        return IOResult.from_failure(
            PreconditionError("pre-step doctor 'findings' is not a list"),
        )
    fail_count = sum(
        1
        for finding in findings_value
        if isinstance(finding, dict) and finding.get("status") == "fail"
    )
    if fail_count > 0:
        return IOResult.from_failure(
            PreconditionError(
                f"pre-step doctor reported {fail_count} fail-status finding(s)",
            ),
        )
    _ = sys.stdout.write(completed.stdout)
    return IOResult.from_value(None)


def _invoke_pre_step_doctor(*, project_root: Path) -> IOResult[None, LivespecError]:
    """Invoke `bin/doctor_static.py` as a subprocess; fold fail findings -> Failure.

    Per v012 SPECIFICATION/spec.md §"Sub-command lifecycle": when
    the resolved skip value is False, the prune-history wrapper
    MUST run the pre-step doctor static check before its action.
    Composition mechanism mirrors the post-step doctor invocation
    in `_seed_railway_emits._run_post_step_doctor` — `subprocess`
    is chosen over direct in-process import because the layered-
    architecture import-linter contract treats `livespec.commands`
    and `livespec.doctor` as independent siblings that cannot
    import each other.

    Forwards `--project-root <path>` to the subprocess so the
    doctor resolves the spec root from the same project root the
    prune-history wrapper resolved.
    """
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_pre_step_doctor_completed_process(completed=completed),
    )
