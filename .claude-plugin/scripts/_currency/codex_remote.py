"""Codex marketplace config parse + remote-ref-tip resolution (stdlib-only).

The Codex plugin-currency axis is LOCAL provenance versus the REMOTE ref
tip. Codex auto-upgrades the marketplace clone at session start, so the
`last_revision` recorded in `~/.codex/config.toml`'s `[marketplaces.<name>]`
section is the running build (the SHA Codex last pulled the clone to), and
the tip of the tracked `ref` on the remote is the expected build. This
module reads that config section with a targeted line parse — no TOML
library, because `tomllib` is 3.11+ while the gate targets 3.10+ — and
resolves the remote tip with a short-timeout `git ls-remote`. Stdlib-only,
like the rest of `_currency`; every unresolved input maps to None so the
verdict degrades to unknown (soft-warn) rather than crashing.
"""

import re
import subprocess
from pathlib import Path

from _currency.locate import _MARKETPLACE_NAME, _SHA12_RE

__all__: list[str] = [
    "_codex_config_marketplace_section",
    "_codex_last_revision_build_id",
    "_codex_remote_ref_build_id",
    "_first_ls_remote_sha",
    "_git_ls_remote_tip",
    "_normalize_build_id",
]

_LS_REMOTE_TIMEOUT_SECONDS = 5
_LS_REMOTE_MIN_FIELDS = 2
_SECTION_HEADER_RE = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
_KEY_VALUE_RE = re.compile(r'^\s*(?P<key>[A-Za-z0-9_.-]+)\s*=\s*"(?P<value>[^"]*)"\s*$')


def _normalize_build_id(*, value: str) -> str | None:
    build_id = value.strip()[:12].lower()
    if not _SHA12_RE.fullmatch(build_id):
        return None
    return build_id


def _codex_config_marketplace_section(*, marketplace: str) -> dict[str, str] | None:
    config_path = Path.home() / ".codex" / "config.toml"
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError:
        return None
    target = f"marketplaces.{marketplace}"
    found = False
    in_section = False
    section: dict[str, str] = {}
    for line in raw.splitlines():
        header = _SECTION_HEADER_RE.match(line)
        if header is not None:
            in_section = header.group("name").strip() == target
            found = found or in_section
            continue
        if in_section:
            pair = _KEY_VALUE_RE.match(line)
            if pair is not None:
                section[pair.group("key")] = pair.group("value")
    return section if found else None


def _codex_last_revision_build_id() -> str | None:
    section = _codex_config_marketplace_section(marketplace=_MARKETPLACE_NAME)
    if section is None:
        return None
    last_revision = section.get("last_revision")
    if last_revision is None:
        return None
    return _normalize_build_id(value=last_revision)


def _codex_remote_ref_build_id() -> str | None:
    section = _codex_config_marketplace_section(marketplace=_MARKETPLACE_NAME)
    if section is None:
        return None
    ref = section.get("ref")
    if not ref:
        return None
    marketplace_clone = Path.home() / ".codex" / ".tmp" / "marketplaces" / _MARKETPLACE_NAME
    return _git_ls_remote_tip(repository=marketplace_clone, ref=ref)


def _git_ls_remote_tip(*, repository: Path, ref: str) -> str | None:
    if not repository.exists():
        return None
    try:
        completed = subprocess.run(  # noqa: S603
            ["/usr/bin/git", "-C", str(repository), "ls-remote", "origin", ref],
            capture_output=True,
            check=False,
            text=True,
            timeout=_LS_REMOTE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return _first_ls_remote_sha(output=completed.stdout)


def _first_ls_remote_sha(*, output: str) -> str | None:
    fallback: str | None = None
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < _LS_REMOTE_MIN_FIELDS:
            continue
        sha, refname = parts[0], parts[1]
        if refname.endswith("^{}"):
            return _normalize_build_id(value=sha)
        if fallback is None:
            fallback = sha
    if fallback is None:
        return None
    return _normalize_build_id(value=fallback)
