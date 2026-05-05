"""File-shaping + skip-resolution railway stages for prune-history.

Extracted from `prune_history.py` at cycle 6.c.9 so the parent
file's LLOC stays under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py`. The split is purely
organizational; the behavior is identical to the inline original.

Stages: stdout-finding emitters (`_emit_*_finding`) and the
`_resolve_skip` helper that implements the v012 spec.md
§"Pre-step skip control" 4-rule resolution matrix.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from returns.io import IOResult

from livespec.errors import LivespecError
from livespec.io import fs
from livespec.parse import jsonc

__all__: list[str] = [
    "_emit_no_op_finding",
    "_emit_pre_step_skipped_finding",
    "_emit_pruned_finding",
    "_resolve_skip",
]


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
