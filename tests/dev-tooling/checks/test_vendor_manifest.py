"""Outside-in test for `dev-tooling/checks/vendor_manifest.py`.

Per `python-skill-script-style-requirements.md` line 2096 +
PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md lines 1701-1707:

    Validates `.vendor.jsonc` against a schema that forbids
    placeholder strings — every entry has a non-empty
    `upstream_url`, a non-empty `upstream_ref`, a parseable-ISO
    `vendored_at`, and the `shim: true` flag is present on
    `jsoncomment` (the v026 D1 hand-authored shim) and absent
    on every other entry (post-v027 D1 `typing_extensions` is
    upstream-sourced, NOT a shim).

Cycle 55 pins ONE narrow violation per v032 D1
one-pattern-per-cycle: a manifest entry whose `upstream_ref`
is the placeholder string `"REPLACE_ME"` is rejected. Other
violation modes (empty `upstream_url`, malformed
`vendored_at`, missing/misplaced `shim: true`) are deferred.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENDOR_MANIFEST = _REPO_ROOT / "dev-tooling" / "checks" / "vendor_manifest.py"


def test_vendor_manifest_rejects_placeholder_upstream_ref(*, tmp_path: Path) -> None:
    """A manifest entry with placeholder upstream_ref is rejected.

    Fixture: `.vendor.jsonc` declares one library with
    `upstream_ref: "REPLACE_ME"`. The check must walk the
    manifest, observe the placeholder, exit non-zero, and
    surface the offending library name.
    """
    (tmp_path / ".vendor.jsonc").write_text(
        "{\n"
        '  "libraries": [\n'
        "    {\n"
        '      "name": "fakelib",\n'
        '      "upstream_url": "https://example.com/fakelib",\n'
        '      "upstream_ref": "REPLACE_ME",\n'
        '      "vendored_at": "2026-04-29T00:00:00Z"\n'
        "    }\n"
        "  ]\n"
        "}\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"vendor_manifest should reject placeholder upstream_ref; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "fakelib" in combined, (
        f"vendor_manifest diagnostic does not surface offending lib name 'fakelib'; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_vendor_manifest_accepts_non_placeholder_entries(*, tmp_path: Path) -> None:
    """A manifest with concrete upstream_ref values is accepted.

    Fixture: `.vendor.jsonc` declares two libs with real
    semver/tag values and parseable ISO `vendored_at`. The
    check must walk and exit 0.
    """
    (tmp_path / ".vendor.jsonc").write_text(
        "{\n"
        '  "libraries": [\n'
        "    {\n"
        '      "name": "structlog",\n'
        '      "upstream_url": "https://github.com/hynek/structlog",\n'
        '      "upstream_ref": "25.5.0",\n'
        '      "vendored_at": "2026-04-26T06:05:33Z"\n'
        "    }\n"
        "  ]\n"
        "}\n",
        encoding="utf-8",
    )

    # S603: argv is a fixed list (sys.executable + repo-controlled
    # script path); no untrusted shell input.
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_VENDOR_MANIFEST)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"vendor_manifest should accept manifest with concrete refs; "
        f"got returncode={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
