"""Outside-in test for `dev-tooling/checks/vendor_manifest.py` — `.vendor.jsonc` schema validation.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-vendor-manifest` row), `.vendor.
jsonc` is validated against a schema that forbids placeholder
strings: every entry has a non-empty `upstream_url`, a
non-empty `upstream_ref`, a parseable-ISO `vendored_at`, and
the `shim: true` flag is present on the canonical hand-
authored shim entry (`jsoncomment` per v026 D1) and absent on
every other entry.

Cycle 162 implements the structural validation of
`.vendor.jsonc`'s placeholder-and-shim discipline.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENDOR_MANIFEST = _REPO_ROOT / "dev-tooling" / "checks" / "vendor_manifest.py"


def test_vendor_manifest_rejects_empty_upstream_ref(*, tmp_path: Path) -> None:
    """A `.vendor.jsonc` entry with empty `upstream_ref` fails the check.

    Fixture: a manifest with one entry whose `upstream_ref` is
    the empty string. The check must parse the file, detect
    the violation, exit non-zero, and surface the offending
    entry name.
    """
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "https://github.com/dry-python/returns",'
        '"upstream_ref": "",'
        '"vendored_at": "2026-04-26T06:05:33Z"}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject empty upstream_ref; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "returns" in combined, (
        f"vendor_manifest diagnostic does not surface offending entry name `returns`; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_rejects_unparseable_vendored_at(*, tmp_path: Path) -> None:
    """A `.vendor.jsonc` entry with malformed `vendored_at` fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "https://example.com/returns",'
        '"upstream_ref": "0.25.0",'
        '"vendored_at": "not-an-iso-timestamp"}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject unparseable vendored_at; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_rejects_shim_on_non_canonical_entry(*, tmp_path: Path) -> None:
    """A `shim: true` flag on an entry other than `jsoncomment` fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "https://example.com/returns",'
        '"upstream_ref": "0.25.0",'
        '"vendored_at": "2026-04-26T06:05:33Z",'
        '"shim": true}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject shim flag on non-canonical entry; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_rejects_canonical_shim_without_flag(*, tmp_path: Path) -> None:
    """A `jsoncomment` entry MISSING the `shim: true` flag fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "jsoncomment",'
        '"upstream_url": "https://pypi.org/project/jsoncomment/",'
        '"upstream_ref": "0.4.2",'
        '"vendored_at": "2026-04-26T06:05:33Z"}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject jsoncomment without shim:true; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_rejects_empty_upstream_url(*, tmp_path: Path) -> None:
    """An entry with empty `upstream_url` fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "",'
        '"upstream_ref": "0.25.0",'
        '"vendored_at": "2026-04-26T06:05:33Z"}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject empty upstream_url; "
        f"got returncode={result.returncode}"
    )


def test_vendor_manifest_rejects_missing_vendored_at_field(*, tmp_path: Path) -> None:
    """An entry with no `vendored_at` field at all fails the check.

    Closes the early-return False branch of `_is_iso_parseable`
    when value is None (not a string).
    """
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "https://example.com/returns",'
        '"upstream_ref": "0.25.0"}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject missing vendored_at; "
        f"got returncode={result.returncode}"
    )


def test_vendor_manifest_rejects_missing_libraries_array(*, tmp_path: Path) -> None:
    """A manifest without a top-level `libraries` array fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text('{"other_key": []}', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject manifest without `libraries`; "
        f"got returncode={result.returncode}"
    )


def test_vendor_manifest_rejects_non_dict_library_entry(*, tmp_path: Path) -> None:
    """A library entry that's not a dict (e.g., a string) fails the check."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ["bogus_string_entry"]}', encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject non-dict entry; "
        f"got returncode={result.returncode}"
    )


def test_vendor_manifest_accepts_canonical_manifest(*, tmp_path: Path) -> None:
    """A manifest mirroring the real `.vendor.jsonc` shape passes (exit 0)."""
    manifest = tmp_path / ".vendor.jsonc"
    manifest.write_text(
        '{"libraries": ['
        '{"name": "returns",'
        '"upstream_url": "https://github.com/dry-python/returns",'
        '"upstream_ref": "0.25.0",'
        '"vendored_at": "2026-04-26T06:05:33Z"},'
        '{"name": "jsoncomment",'
        '"upstream_url": "https://pypi.org/project/jsoncomment/",'
        '"upstream_ref": "0.4.2",'
        '"vendored_at": "2026-04-26T06:05:33Z",'
        '"shim": true}'
        "]}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"vendor_manifest should accept canonical manifest with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_accepts_missing_manifest_file(*, tmp_path: Path) -> None:
    """A repo cwd without `.vendor.jsonc` passes the check (exit 0).

    Closes the `if not manifest_path.is_file():` early-return
    branch — the check exits silently when no manifest
    exists.
    """
    result = subprocess.run(
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"vendor_manifest should accept missing manifest with exit 0; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_module_importable_without_running_main() -> None:
    """The check module imports cleanly without invoking main()."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "vendor_manifest_for_import_test", str(_VENDOR_MANIFEST),
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main), "main should be importable without invocation"
