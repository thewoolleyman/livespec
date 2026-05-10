"""refresh_gaps — author implementation-gaps/current.json from a static walk of the spec and repo.

Per `SPECIFICATION/non-functional-requirements.md` §Spec
§"Repo-local implementation workflow" + §"Implementation-gap
report shape", this script is the automation entry point for
the `refresh-gaps` skill. It reads the five `SPECIFICATION/`
files (computing each's git blob SHA1 fingerprint), runs a
hardcoded registry of gap-detection predicates against the
current repo state, assembles a JSON report against
`implementation-gaps/current.schema.json`, validates the
result, and writes it to `implementation-gaps/current.json`.

The static fields for each gap (id, area, severity, expected,
observed, evidence, etc.) live in `gap_blueprints.json`
alongside this file. The Python registry below maps each gap
id to its presence-predicate; main() composes the two halves
into the final report. New gaps are added by appending an
entry to the JSON file and registering a predicate in
`_PRESENCE_PREDICATES`.

Output discipline: per spec, `print` and `sys.stderr.write`
are banned in dev-tooling/**. Diagnostics flow through
structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to
`sys.path` at module import time alongside `fastjsonschema`
(used to validate the report against the schema before
writing).
"""

import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import uuid
from collections.abc import Callable
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import fastjsonschema  # noqa: E402  — vendor-path-aware import after sys.path insert.
import structlog  # noqa: E402  — same.

__all__: list[str] = []


_REPORT_PATH = Path("implementation-gaps") / "current.json"
_SCHEMA_PATH = Path("implementation-gaps") / "current.schema.json"
_BLUEPRINTS_PATH = Path(__file__).resolve().parent / "gap_blueprints.json"
_SPEC_DIR = Path("SPECIFICATION")
_SPEC_FILES: tuple[tuple[str, str], ...] = (
    ("spec_md", "spec.md"),
    ("contracts_md", "contracts.md"),
    ("constraints_md", "constraints.md"),
    ("scenarios_md", "scenarios.md"),
    ("non_functional_requirements_md", "non-functional-requirements.md"),
)
_SCOPES_INSPECTED: tuple[str, ...] = (
    "SPECIFICATION/",
    ".claude-plugin/",
    ".claude/skills/",
    "dev-tooling/implementation/",
    "implementation-gaps/",
    "tests/dev-tooling/",
    "justfile",
    "implementation.just",
    ".mise.toml",
    ".gitignore",
    ".beads/",
)
_SCOPE_LIVE_SYSTEM_REASON = (
    "livespec has no live system to probe (no DB / no edge functions); " "inspection is static-only"
)
_SCOPES_SKIPPED: tuple[tuple[str, str], ...] = (
    ("live-system runtime probes", _SCOPE_LIVE_SYSTEM_REASON),
)
_INSPECTION_METHOD = (
    "static — dev-tooling/implementation/refresh_gaps.py walked the repo "
    "via hardcoded gap-detection predicates"
)


def _git_blob_sha(*, path: Path) -> str:
    """Compute the git blob SHA1 of the file at `path` (pure-Python; no .git/ needed)."""
    content = path.read_bytes()
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content, usedforsecurity=False).hexdigest()


def _spec_sources(*, cwd: Path) -> dict[str, dict[str, str]]:
    """Build the spec_sources map, one entry per of the five spec files."""
    out: dict[str, dict[str, str]] = {}
    for key, filename in _SPEC_FILES:
        rel = _SPEC_DIR / filename
        out[key] = {
            "path": str(rel),
            "git_blob_sha": _git_blob_sha(path=cwd / rel),
        }
    return out


def _file_missing(rel: str) -> Callable[[Path], bool]:
    """Predicate factory: gap is present iff the file at `rel` does NOT exist."""
    return lambda cwd: not (cwd / rel).is_file()


def _files_missing(rels: tuple[str, ...]) -> Callable[[Path], bool]:
    """Predicate factory: gap is present iff ANY of the relative paths is missing."""
    return lambda cwd: any(not (cwd / rel).is_file() for rel in rels)


def _any_skill_has_manual_fallback(cwd: Path) -> bool:
    """Predicate: gap-0005 fires iff any SKILL.md still carries the manual-fallback section."""
    candidates = [
        cwd / ".claude" / "skills" / f"livespec-implementation-beads:{name}" / "SKILL.md"
        for name in ("refresh-gaps", "plan", "implement")
    ]
    candidates.extend(
        cwd / ".claude" / "plugins" / "livespec-implementation" / "skills" / name / "SKILL.md"
        for name in ("refresh-gaps", "plan", "implement")
    )
    for candidate in candidates:
        if candidate.is_file() and "Manual fallback (current state)" in candidate.read_text(
            encoding="utf-8",
        ):
            return True
    return False


def _beads_config_tracked(cwd: Path) -> bool:
    """Predicate: gap-0006 fires iff `.beads/config.yaml` is git-tracked AND not gitignored."""
    git = shutil.which("git")
    if git is None:
        return False
    try:
        result = subprocess.run(  # noqa: S603 — argv list, no shell.
            [git, "ls-files", ".beads/config.yaml"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0 or result.stdout.strip() == "":
        return False
    gitignore = cwd / ".gitignore"
    if gitignore.is_file():
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            if line.strip() == ".beads/config.yaml":
                return False
    return True


_PRESENCE_PREDICATES: dict[str, Callable[[Path], bool]] = {
    "gap-0001": _file_missing("dev-tooling/implementation/refresh_gaps.py"),
    "gap-0002": _file_missing("dev-tooling/implementation/plan.py"),
    "gap-0003": _file_missing("dev-tooling/implementation/implement.py"),
    "gap-0004": _files_missing(
        (
            "tests/dev-tooling/implementation/test_check_gaps.py",
            "tests/dev-tooling/implementation/test_check_gap_tracking.py",
        ),
    ),
    "gap-0005": _any_skill_has_manual_fallback,
    "gap-0006": _beads_config_tracked,
}


def _load_blueprints() -> list[dict[str, object]]:
    """Read and parse gap_blueprints.json, the static-fields source for each gap."""
    return json.loads(_BLUEPRINTS_PATH.read_text(encoding="utf-8"))


def _summary(*, gaps: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    """Aggregate by_area / by_severity / by_status counts for the gaps list."""
    by_area: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for entry in gaps:
        area = str(entry["area"])
        severity = str(entry["severity"])
        by_area[area] = by_area.get(area, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
    return {
        "by_area": by_area,
        "by_severity": by_severity,
        "by_status": {"open": len(gaps)},
    }


def _build_report(*, cwd: Path) -> dict[str, object]:
    """Assemble the full report object (pre-validation)."""
    blueprints = _load_blueprints()
    gaps: list[dict[str, object]] = []
    for blueprint in blueprints:
        gap_id = str(blueprint["id"])
        predicate = _PRESENCE_PREDICATES.get(gap_id)
        if predicate is None:
            continue
        if predicate(cwd):
            gaps.append(blueprint)
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "$schema": "./current.schema.json",
        "schema_version": 1,
        "generated_at": generated_at,
        "spec_sources": _spec_sources(cwd=cwd),
        "inspection": {
            "scopes_inspected": list(_SCOPES_INSPECTED),
            "scopes_skipped": [
                {"scope": scope, "reason": reason} for scope, reason in _SCOPES_SKIPPED
            ],
            "run_id": str(uuid.uuid4()),
            "inspection_method": _INSPECTION_METHOD,
        },
        "gaps": gaps,
        "summary": _summary(gaps=gaps),
    }


def main() -> int:
    """Author implementation-gaps/current.json from the current repo state."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("refresh_gaps")
    cwd = Path.cwd()

    for _key, filename in _SPEC_FILES:
        spec_file = cwd / _SPEC_DIR / filename
        if not spec_file.is_file():
            log.error("required SPECIFICATION/ file missing", path=str(spec_file))
            return 1

    schema_path = cwd / _SCHEMA_PATH
    if not schema_path.is_file():
        log.error("schema missing", path=str(schema_path))
        return 1
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.exception("schema is not valid JSON", path=str(schema_path), message=str(exc))
        return 1

    report = _build_report(cwd=cwd)

    try:
        validate = fastjsonschema.compile(schema)
        validate(report)
    except fastjsonschema.JsonSchemaDefinitionException as exc:
        log.exception("schema is itself invalid", path=str(schema_path), message=str(exc))
        return 1
    except fastjsonschema.JsonSchemaValueException as exc:
        log.exception(
            "generated report fails schema validation (refresh_gaps bug)",
            field=exc.name,
            message=exc.message,
        )
        return 1

    report_path = cwd / _REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    log.info(
        "implementation-gap report regenerated",
        path=str(report_path),
        gap_count=len(report["gaps"]) if isinstance(report["gaps"], list) else 0,
        run_id=report["inspection"]["run_id"] if isinstance(report["inspection"], dict) else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
