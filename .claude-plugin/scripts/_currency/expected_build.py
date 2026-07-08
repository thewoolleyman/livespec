"""Expected (pinned) plugin build resolution via the marketplace clone.

Resolves the build the marketplace currently serves by reading the HEAD of
the per-runtime marketplace clone. Stdlib-only (shells out to git).
"""

import subprocess
from pathlib import Path

from _currency.locate import (
    _MARKETPLACE_NAME,
    _SHA12_RE,
    _is_codex_installed_plugin_cache_path,
)

__all__ = ["_expected_build_id", "_git_rev_parse_head"]


def _expected_build_id(*, plugin_root: Path) -> str | None:
    if _is_codex_installed_plugin_cache_path(plugin_root=plugin_root):
        marketplace = Path.home() / ".codex" / ".tmp" / "marketplaces" / _MARKETPLACE_NAME
    else:
        marketplace = Path.home() / ".claude" / "plugins" / "marketplaces" / _MARKETPLACE_NAME
    return _git_rev_parse_head(repository=marketplace)


def _git_rev_parse_head(*, repository: Path) -> str | None:
    if not repository.exists():
        return None
    try:
        completed = subprocess.run(  # noqa: S603
            ["/usr/bin/git", "-C", str(repository), "rev-parse", "--short=12", "HEAD"],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    build_id = completed.stdout.strip().lower()
    if not _SHA12_RE.fullmatch(build_id):
        return None
    return build_id
