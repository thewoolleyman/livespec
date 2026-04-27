"""Tests for dev-tooling/checks/vendor_manifest.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHECKS_DIR = Path(__file__).resolve().parents[3] / "dev-tooling" / "checks"
sys.path.insert(0, str(_CHECKS_DIR))

import vendor_manifest  # noqa: E402

__all__: list[str] = []


def _write(*, repo: Path, content: str) -> None:
    (repo / ".vendor.jsonc").write_text(content, encoding="utf-8")


_GOOD = """// vendor manifest
{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/dry-python/returns",
      "upstream_ref": "0.25.0",
      "vendored_at": "2026-04-26T06:05:33Z"
    },
    {
      "name": "jsoncomment",
      "upstream_url": "https://pypi.org/project/jsoncomment/",
      "upstream_ref": "0.4.2",
      "vendored_at": "2026-04-26T06:05:33Z",
      "shim": true
    }
  ]
}"""

_MISSING_FIELD = """{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/x/y",
      "vendored_at": "2026-04-26T06:05:33Z"
    }
  ]
}"""

_PLACEHOLDER_REF = """{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/x/y",
      "upstream_ref": "PLACEHOLDER",
      "vendored_at": "2026-04-26T06:05:33Z"
    }
  ]
}"""

_BAD_TIMESTAMP = """{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/x/y",
      "upstream_ref": "0.25.0",
      "vendored_at": "not a real date"
    }
  ]
}"""

_SHIM_ON_NON_JSONCOMMENT = """{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/x/y",
      "upstream_ref": "0.25.0",
      "vendored_at": "2026-04-26T06:05:33Z",
      "shim": true
    }
  ]
}"""

_JSONCOMMENT_WITHOUT_SHIM = """{
  "libraries": [
    {
      "name": "jsoncomment",
      "upstream_url": "https://pypi.org/project/jsoncomment/",
      "upstream_ref": "0.4.2",
      "vendored_at": "2026-04-26T06:05:33Z"
    }
  ]
}"""

_UNKNOWN_FIELD = """{
  "libraries": [
    {
      "name": "returns",
      "upstream_url": "https://github.com/x/y",
      "upstream_ref": "0.25.0",
      "vendored_at": "2026-04-26T06:05:33Z",
      "extra": "junk"
    }
  ]
}"""


def test_good_manifest_passes(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_GOOD)
    assert vendor_manifest.check_repo(repo_root=tmp_path) == []


def test_missing_field_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_MISSING_FIELD)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("upstream_ref" in v for v in violations)


def test_placeholder_ref_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_PLACEHOLDER_REF)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("placeholder" in v for v in violations)


def test_bad_timestamp_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_BAD_TIMESTAMP)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("ISO-8601" in v for v in violations)


def test_shim_on_non_jsoncomment_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_SHIM_ON_NON_JSONCOMMENT)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("only jsoncomment" in v for v in violations)


def test_jsoncomment_without_shim_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_JSONCOMMENT_WITHOUT_SHIM)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("jsoncomment must declare `shim: true`" in v for v in violations)


def test_unknown_field_fails(*, tmp_path: Path) -> None:
    _write(repo=tmp_path, content=_UNKNOWN_FIELD)
    violations = vendor_manifest.check_repo(repo_root=tmp_path)
    assert any("unknown field" in v for v in violations)


def test_main_passes_against_real_repo(*, monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped .vendor.jsonc satisfies every rule."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(repo_root)
    assert vendor_manifest.main() == 0
