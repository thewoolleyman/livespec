"""vendor_update — re-vendor an upstream-sourced library into `_vendor/`.

Per `SPECIFICATION/constraints.md` §"Vendoring procedure": re-vendoring
of upstream-sourced libs MUST go through `just vendor-update <lib>` —
the only blessed mutation path. The recipe fetches the upstream ref
recorded in `.vendor.jsonc`, copies the library's source tree under
`_vendor/<lib>/`, preserves `LICENSE` (when upstream ships one), and
updates the entry's `vendored_at` timestamp.

This is a maintainer-only mutating tool, invoked via
`just vendor-update <lib>` (NOT part of `just check`). Shim entries
(`shim: true` in `.vendor.jsonc`) are NOT re-vendored — they are
livespec-authored and edited in place via the normal propose-change
cycle.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path` at
module import time.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

_VENDOR_DIR = Path(__file__).resolve().parent.parent / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import jsoncomment  # noqa: E402  — vendor-path-aware import after sys.path insert.
import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_MANIFEST_FILENAME = ".vendor.jsonc"
_LICENSE_FILENAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING")
_EXIT_PRECONDITION = 3


def _find_entry(*, libraries: list[dict[str, Any]], lib_name: str) -> dict[str, Any] | None:
    for entry in libraries:
        if entry.get("name") == lib_name:
            return entry
    return None


def _shallow_clone(
    *, upstream_url: str, upstream_ref: str, dest: Path, log: structlog.stdlib.BoundLogger
) -> None:
    log.info("cloning upstream", upstream_url=upstream_url, upstream_ref=upstream_ref)
    _ = subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", upstream_ref, upstream_url, str(dest)],
        check=True,
    )


def _copy_package_tree(*, clone_root: Path, lib_name: str, vendor_dest: Path) -> bytes | None:
    """Replace `vendor_dest` with the upstream package tree.

    Returns the bytes of any pre-existing `vendor_dest/LICENSE` so the
    caller can restore it when upstream ships no canonical LICENSE
    file (per `SPECIFICATION/constraints.md` §'Lib admission policy':
    every vendored lib's `LICENSE` file MUST be preserved at
    `_vendor/<lib>/LICENSE`).
    """
    src = clone_root / lib_name
    if not src.is_dir():
        raise SystemExit(_EXIT_PRECONDITION)
    preserved_license: bytes | None = None
    existing_license = vendor_dest / "LICENSE"
    if existing_license.is_file():
        preserved_license = existing_license.read_bytes()
    if vendor_dest.is_dir():
        shutil.rmtree(vendor_dest)
    vendor_dest.mkdir(parents=True)
    for item in src.iterdir():
        if item.name == "__pycache__":
            continue
        if item.is_dir():
            _ = shutil.copytree(item, vendor_dest / item.name)
        else:
            _ = shutil.copy2(item, vendor_dest / item.name)
    return preserved_license


def _copy_license(
    *,
    clone_root: Path,
    vendor_dest: Path,
    preserved_license: bytes | None,
    log: structlog.stdlib.BoundLogger,
) -> bool:
    for license_name in _LICENSE_FILENAMES:
        candidate = clone_root / license_name
        if candidate.is_file():
            _ = shutil.copy2(candidate, vendor_dest / "LICENSE")
            return True
    if preserved_license is not None:
        _ = (vendor_dest / "LICENSE").write_bytes(preserved_license)
        message_restored = (
            f"upstream ships no LICENSE file; restored pre-existing "
            f"_vendor/{vendor_dest.name}/LICENSE (per SPECIFICATION/"
            f"constraints.md 'Lib admission policy' the maintainer-authored "
            f"attribution LICENSE is the source of record for this lib)"
        )
        log.warning(message_restored)
        return False
    message_missing = (
        f"upstream ships no LICENSE file at any canonical filename and "
        f"no pre-existing _vendor/{vendor_dest.name}/LICENSE was found; "
        f"maintainer must author one per SPECIFICATION/constraints.md "
        f"'Lib admission policy'"
    )
    log.warning(message_missing)
    return False


def _rewrite_vendored_at(*, manifest_path: Path, lib_name: str, now_iso: str) -> None:
    text = manifest_path.read_text(encoding="utf-8")
    parsed = cast(dict[str, Any], jsoncomment.loads(text))
    libraries = cast(list[dict[str, Any]], parsed["libraries"])
    entry = _find_entry(libraries=libraries, lib_name=lib_name)
    if entry is None:
        raise SystemExit(_EXIT_PRECONDITION)
    old_vendored_at = cast(str, entry["vendored_at"])
    upstream_url = cast(str, entry["upstream_url"])
    upstream_ref = cast(str, entry["upstream_ref"])
    # In-place targeted rewrite (preserves comments + formatting) of the
    # JSON object's `vendored_at` field for this entry only.
    needle = (
        f'"name": "{lib_name}",\n      "upstream_url": '
        f'"{upstream_url}",\n      "upstream_ref": '
        f'"{upstream_ref}",\n      "vendored_at": "{old_vendored_at}"'
    )
    replacement = (
        f'"name": "{lib_name}",\n      "upstream_url": '
        f'"{upstream_url}",\n      "upstream_ref": '
        f'"{upstream_ref}",\n      "vendored_at": "{now_iso}"'
    )
    if needle not in text:
        raise SystemExit(_EXIT_PRECONDITION)
    _ = manifest_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")


def _vendor_update(*, lib_name: str, log: structlog.stdlib.BoundLogger) -> int:
    cwd = Path.cwd()
    manifest_path = cwd / _MANIFEST_FILENAME
    if not manifest_path.is_file():
        log.error("manifest not found", path=str(manifest_path))
        return _EXIT_PRECONDITION
    parsed = cast(dict[str, Any], jsoncomment.loads(manifest_path.read_text(encoding="utf-8")))
    libraries_raw = parsed.get("libraries")
    if not isinstance(libraries_raw, list):
        log.error("manifest missing top-level `libraries` array")
        return _EXIT_PRECONDITION
    libraries = cast(list[dict[str, Any]], libraries_raw)
    entry = _find_entry(libraries=libraries, lib_name=lib_name)
    if entry is None:
        log.error("no `.vendor.jsonc` entry for lib", lib_name=lib_name)
        return _EXIT_PRECONDITION
    if entry.get("shim") is True:
        message_shim = (
            "lib is a shim; shims are NOT re-vendored "
            "(per SPECIFICATION/constraints.md 'Vendoring procedure')"
        )
        log.error(message_shim, lib_name=lib_name)
        return _EXIT_PRECONDITION
    upstream_url = cast(str, entry["upstream_url"])
    upstream_ref = cast(str, entry["upstream_ref"])
    vendor_dest = cwd / ".claude-plugin" / "scripts" / "_vendor" / lib_name
    with tempfile.TemporaryDirectory(prefix="livespec-vendor-") as tmp_str:
        clone_root = Path(tmp_str) / "clone"
        _shallow_clone(
            upstream_url=upstream_url, upstream_ref=upstream_ref, dest=clone_root, log=log
        )
        preserved_license = _copy_package_tree(
            clone_root=clone_root, lib_name=lib_name, vendor_dest=vendor_dest
        )
        _ = _copy_license(
            clone_root=clone_root,
            vendor_dest=vendor_dest,
            preserved_license=preserved_license,
            log=log,
        )
    now_iso = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _rewrite_vendored_at(manifest_path=manifest_path, lib_name=lib_name, now_iso=now_iso)
    log.info(
        "vendor-update completed",
        lib_name=lib_name,
        upstream_ref=upstream_ref,
        vendored_at=now_iso,
    )
    return 0


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("vendor_update")
    parser = argparse.ArgumentParser(prog="vendor_update", add_help=True)
    _ = parser.add_argument("lib", help="vendored library slug (matches `.vendor.jsonc` `name`)")
    namespace = parser.parse_args()
    lib_name = str(namespace.lib)
    return _vendor_update(lib_name=lib_name, log=log)


if __name__ == "__main__":
    raise SystemExit(main())
