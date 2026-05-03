"""Emission + post-step doctor railway stages for the `seed` sub-command.

Extracted from `seed.py` at cycle 4e so the parent file's LLOC
stays under the 200-line ceiling. The split is purely
organizational; the behavior is identical to the inline
original. Companion to `_seed_railway_writes.py`.

Stages: seed proposed-change, seed revision, skill-owned
proposed_changes/README.md, post-step doctor invocation +
finding-fold.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

from returns.io import IOResult
from returns.result import Success, safe

from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs, proc
from livespec.schemas.dataclasses.seed_input import SeedInput

__all__: list[str] = [
    "_emit_seed_proposed_change",
    "_emit_seed_revision",
    "_emit_skill_owned_proposed_changes_readme",
    "_run_post_step_doctor",
]


# Path-shape minima — duplicated from seed.py / _seed_railway_writes.py
# so this module is self-contained.
_MIN_PARTS_MAIN_SPEC: int = 2

_BIN_DIR = Path(__file__).resolve().parents[2] / "bin"
_DOCTOR_STATIC_WRAPPER = _BIN_DIR / "doctor_static.py"


_PROPOSED_CHANGES_README_TEXT = (
    "# Proposed Changes\n"
    "\n"
    "This directory holds in-flight proposed changes to the\n"
    "specification. Each file is named `<topic>.md` and contains\n"
    "one or more `## Proposal: <name>` sections with target\n"
    "specification files, summary, motivation, and proposed\n"
    "changes (prose or unified diff). Files are processed by\n"
    "`livespec revise` in creation-time order (YAML `created_at`\n"
    "front-matter field) and moved into\n"
    "`../history/vNNN/proposed_changes/` when revised. After a\n"
    "successful `revise`, this directory is empty.\n"
)


def _emit_seed_proposed_change(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Auto-emit `<spec-root>/history/v001/proposed_changes/seed.md`."""
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    target_files_block = "\n".join(f"- {entry['path']}" for entry in seed_input.files)
    body = (
        "---\n"
        "topic: seed\n"
        "author: livespec-seed\n"
        "---\n"
        "\n"
        "## Proposal: seed\n"
        "\n"
        "### Target specification files\n"
        "\n"
        f"{target_files_block}\n"
        "\n"
        "### Summary\n"
        "\n"
        "Initial seed of the specification from user-provided intent.\n"
        "\n"
        "### Motivation\n"
        "\n"
        f"{seed_input.intent}\n"
        "\n"
        "### Proposed Changes\n"
        "\n"
        f"{seed_input.intent}\n"
    )
    target = project_root / spec_root_name / "history" / "v001" / "proposed_changes" / "seed.md"
    return fs.write_text(path=target, text=body).map(lambda _: seed_input)


def _emit_seed_revision(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Auto-emit `<spec-root>/history/v001/proposed_changes/seed-revision.md`."""
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    resulting_changes = "\n".join(f"- {entry['path']}" for entry in seed_input.files)
    body = (
        "---\n"
        "proposal: seed.md\n"
        "decision: accept\n"
        "author_llm: livespec-seed\n"
        "author_human: unknown\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        "auto-accepted during seed\n"
        "\n"
        "## Resulting Changes\n"
        "\n"
        f"{resulting_changes}\n"
    )
    target = (
        project_root / spec_root_name / "history" / "v001" / "proposed_changes" / "seed-revision.md"
    )
    return fs.write_text(path=target, text=body).map(lambda _: seed_input)


def _emit_skill_owned_proposed_changes_readme(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Write `<spec-root>/proposed_changes/README.md` (skill-owned dir marker)."""
    if not seed_input.files:
        return IOResult.from_value(seed_input)
    first_path = Path(seed_input.files[0]["path"])
    if len(first_path.parts) < _MIN_PARTS_MAIN_SPEC:
        return IOResult.from_value(seed_input)
    spec_root_name = first_path.parts[0]
    proposed_changes_readme = project_root / spec_root_name / "proposed_changes" / "README.md"
    return fs.write_text(
        path=proposed_changes_readme,
        text=_PROPOSED_CHANGES_README_TEXT,
    ).map(lambda _: seed_input)


@safe(exceptions=(ValueError,))
def _safe_json_loads(*, text: str) -> Any:
    """Decorator-lifted strict-JSON decode for doctor's stdout contract."""
    return _json.loads(text)


def _fold_doctor_completed_process(
    *,
    seed_input: SeedInput,
    completed: Any,
) -> IOResult[SeedInput, LivespecError]:
    """Parse the doctor subprocess's stdout JSON; fold fail findings -> Failure."""
    parsed = _safe_json_loads(text=completed.stdout)
    if not isinstance(parsed, Success):
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor stdout malformed JSON: {parsed.failure()}",
            ),
        )
    payload = parsed.unwrap()
    if not isinstance(payload, dict) or "findings" not in payload:
        return IOResult.from_failure(
            PreconditionError("post-step doctor stdout missing 'findings' key"),
        )
    findings_value = payload["findings"]
    if not isinstance(findings_value, list):
        return IOResult.from_failure(
            PreconditionError("post-step doctor 'findings' is not a list"),
        )
    fail_count = sum(
        1
        for finding in findings_value
        if isinstance(finding, dict) and finding.get("status") == "fail"
    )
    if fail_count > 0:
        return IOResult.from_failure(
            PreconditionError(
                f"post-step doctor reported {fail_count} fail-status finding(s)",
            ),
        )
    return IOResult.from_value(seed_input)


def _run_post_step_doctor(
    *,
    seed_input: SeedInput,
    project_root: Path,
) -> IOResult[SeedInput, LivespecError]:
    """Invoke `bin/doctor_static.py` as a subprocess; fold fail findings -> Failure."""
    return proc.run_subprocess(
        argv=[
            sys.executable,
            str(_DOCTOR_STATIC_WRAPPER),
            "--project-root",
            str(project_root),
        ],
    ).bind(
        lambda completed: _fold_doctor_completed_process(
            seed_input=seed_input,
            completed=completed,
        ),
    )
