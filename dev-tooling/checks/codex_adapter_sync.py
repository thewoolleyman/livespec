"""codex_adapter_sync — keep Codex adapters thin over core prose and wrappers.

Validates the committed project-local `.agents/skills/livespec-*` adapters:
they must keep namespaced Codex frontmatter, reference existing core prose,
reference the expected wrapper when wrapper-backed, and avoid copied core
operation prose sections.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics flow
through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at module
import time.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TypeAlias

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []

_SKILLS_DIR = Path(".agents") / "skills"
_PROSE_DIR = Path(".claude-plugin") / "prose"
_WRAPPERS_DIR = Path(".claude-plugin") / "scripts" / "bin"
_COPIED_SECTION_MARKERS = (
    "## Steps",
    "## Failure handling",
    "## Post-CLI",
    "## Inputs",
    "## Output schema",
)
_MIN_FRONTMATTER_LINES = 3


ExpectedAdapter: TypeAlias = tuple[str, str, str | None]


_EXPECTED_ADAPTERS: tuple[ExpectedAdapter, ...] = (
    ("livespec-help", "help", None),
    ("livespec-next", "next", str(_WRAPPERS_DIR / "next.py")),
    ("livespec-doctor", "doctor", str(_WRAPPERS_DIR / "doctor_static.py")),
)


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("codex_adapter_sync")


def _frontmatter(*, text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if len(lines) < _MIN_FRONTMATTER_LINES or lines[0] != "---":  # pragma: no cover
        return None
    try:
        closing = lines[1:].index("---") + 1
    except ValueError:  # pragma: no cover
        return None
    parsed: dict[str, str] = {}
    for line in lines[1:closing]:
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip("'\"")
    return parsed


def _adapter_name(*, adapter: ExpectedAdapter) -> str:
    return adapter[0]


def _adapter_wrapper(*, adapter: ExpectedAdapter) -> str | None:
    return adapter[2]


def _adapter_prose(*, adapter: ExpectedAdapter) -> str:
    return str(_PROSE_DIR / f"{adapter[1]}.md")


def _adapter_skill_path(*, adapter: ExpectedAdapter) -> Path:
    return _SKILLS_DIR / _adapter_name(adapter=adapter) / "SKILL.md"


def _actual_livespec_skill_names(*, cwd: Path) -> set[str]:
    skills_root = cwd / _SKILLS_DIR
    if not skills_root.is_dir():
        return set()  # pragma: no cover - expected adapters fail immediately after this.
    return {
        child.name
        for child in skills_root.iterdir()
        if child.is_dir() and child.name.startswith("livespec-")
    }


def _has_copied_core_prose(*, text: str) -> str | None:
    for marker in _COPIED_SECTION_MARKERS:
        if marker in text:
            return marker
    return None


def _check_frontmatter(
    *,
    log: structlog.stdlib.BoundLogger,
    adapter_name: str,
    adapter_skill_path: Path,
    text: str,
) -> int:
    frontmatter = _frontmatter(text=text)
    if frontmatter is None:  # pragma: no cover - defensive malformed-frontmatter path.
        log.error(
            "Codex adapter missing YAML frontmatter",
            check_id="codex-adapter-sync",
            adapter=adapter_name,
            path=str(adapter_skill_path),
        )
        return 1
    if frontmatter.get("name") == adapter_name and frontmatter.get("description"):
        return 0
    log.error(
        "Codex adapter frontmatter drift",
        check_id="codex-adapter-sync",
        adapter=adapter_name,
        path=str(adapter_skill_path),
        expected_name=adapter_name,
        actual_name=frontmatter.get("name"),
        description_present=bool(frontmatter.get("description")),
    )
    return 1


def _check_prose_reference(
    *,
    log: structlog.stdlib.BoundLogger,
    cwd: Path,
    adapter_name: str,
    adapter_skill_path: Path,
    adapter_prose: str,
    text: str,
) -> int:
    prose_path = cwd / adapter_prose
    if adapter_prose in text and prose_path.is_file():
        return 0
    log.error(
        "Codex adapter prose reference drift",
        check_id="codex-adapter-sync",
        adapter=adapter_name,
        path=str(adapter_skill_path),
        expected_prose=adapter_prose,
        prose_exists=prose_path.is_file(),
    )
    return 1


def _check_wrapper_reference(
    *,
    log: structlog.stdlib.BoundLogger,
    cwd: Path,
    adapter_name: str,
    adapter_skill_path: Path,
    adapter_wrapper: str | None,
    text: str,
) -> int:
    if adapter_wrapper is None:
        return 0

    wrapper_path = cwd / adapter_wrapper
    if adapter_wrapper in text and wrapper_path.is_file():
        return 0
    log.error(
        "Codex adapter wrapper reference drift",
        check_id="codex-adapter-sync",
        adapter=adapter_name,
        path=str(adapter_skill_path),
        expected_wrapper=adapter_wrapper,
        wrapper_exists=wrapper_path.is_file(),
    )
    return 1


def _check_no_copied_core_prose(
    *,
    log: structlog.stdlib.BoundLogger,
    adapter_name: str,
    adapter_skill_path: Path,
    text: str,
) -> int:
    copied_marker = _has_copied_core_prose(text=text)
    if copied_marker is None:
        return 0
    log.error(
        "Codex adapter appears to contain copied core prose",
        check_id="codex-adapter-sync",
        adapter=adapter_name,
        path=str(adapter_skill_path),
        matched=copied_marker,
    )
    return 1


def _check_adapter(
    *,
    log: structlog.stdlib.BoundLogger,
    cwd: Path,
    adapter: ExpectedAdapter,
) -> int:
    issues = 0
    adapter_name = _adapter_name(adapter=adapter)
    adapter_skill_path = _adapter_skill_path(adapter=adapter)
    skill_path = cwd / adapter_skill_path
    if not skill_path.is_file():
        log.error(
            "missing Codex adapter",
            check_id="codex-adapter-sync",
            adapter=adapter_name,
            expected_path=str(adapter_skill_path),
        )
        return 1

    text = skill_path.read_text(encoding="utf-8")
    adapter_prose = _adapter_prose(adapter=adapter)
    adapter_wrapper = _adapter_wrapper(adapter=adapter)
    issues += _check_frontmatter(
        log=log,
        adapter_name=adapter_name,
        adapter_skill_path=adapter_skill_path,
        text=text,
    )
    issues += _check_prose_reference(
        log=log,
        cwd=cwd,
        adapter_name=adapter_name,
        adapter_skill_path=adapter_skill_path,
        adapter_prose=adapter_prose,
        text=text,
    )
    issues += _check_wrapper_reference(
        log=log,
        cwd=cwd,
        adapter_name=adapter_name,
        adapter_skill_path=adapter_skill_path,
        adapter_wrapper=adapter_wrapper,
        text=text,
    )
    issues += _check_no_copied_core_prose(
        log=log,
        adapter_name=adapter_name,
        adapter_skill_path=adapter_skill_path,
        text=text,
    )

    return issues


def main() -> int:
    log = _configure_logger()
    cwd = Path.cwd()
    issues = 0
    expected_names = {_adapter_name(adapter=adapter) for adapter in _EXPECTED_ADAPTERS}
    actual_names = _actual_livespec_skill_names(cwd=cwd)

    for unexpected in sorted(actual_names - expected_names):
        log.error(
            "unexpected livespec Codex adapter",
            check_id="codex-adapter-sync",
            adapter=unexpected,
            hint="only read-only livespec Codex adapters are currently allowed",
        )
        issues += 1

    for adapter in _EXPECTED_ADAPTERS:
        issues += _check_adapter(log=log, cwd=cwd, adapter=adapter)

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
