"""Tests for `dev-tooling/refresh_tenant_repos_identity.py` — who a repo really is.

Two questions live in that module, and both are answered against the
FORGE rather than against the registry: where a registered `owner/repo`
has since been renamed or transferred TO, and what host plus
`owner/repo` an existing clone's `origin` actually names.

The `gh` cases run against a FAKE `gh` executable placed first on
`PATH` that records its argv, so a test asserts both the exact fields
the resolver asks GitHub for and what it does with the answer. The URL
cases need no process at all — parsing a remote URL is pure.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_identity.py"
_OWNER = "acme"
_REPO = "widget"

_FAKE_GH = """#!/usr/bin/env bash
set -uo pipefail
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
if [[ "${1:-} ${2:-}" == "auth status" ]]; then
    exit "${FAKE_GH_AUTH_EXIT:-0}"
fi
if [[ "${1:-} ${2:-}" == "repo view" ]]; then
    if [[ -n "${FAKE_GH_VIEW_JSON:-}" ]]; then
        printf '%s\\n' "$FAKE_GH_VIEW_JSON"
    else
        printf '{"nameWithOwner":"%s","defaultBranchRef":{"name":"%s"}}\\n' \
            "${FAKE_GH_NAME_WITH_OWNER:-$3}" "${FAKE_GH_DEFAULT_BRANCH:-master}"
    fi
    exit "${FAKE_GH_VIEW_EXIT:-0}"
fi
printf 'unexpected gh argv: %s\\n' "$*" >&2
exit 99
"""


def _load_module() -> ModuleType:
    """Import the identity resolver by file path (`dev-tooling/` is not a package)."""
    assert _SCRIPT.is_file(), f"{_SCRIPT} does not exist"
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_identity", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _install_fake_gh(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a recording fake `gh` first on PATH; return its argv log path."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_FAKE_GH, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IXUSR)
    log = tmp_path / "gh-argv.log"
    log.write_text("", encoding="utf-8")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_GH_LOG", str(log))
    return log


def test_canonical_identity_asks_github_for_both_fields_in_one_call(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One `gh repo view` supplies the canonical name AND the default branch."""
    module = _load_module()
    log = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    resolution = module.canonical_identity(owner=_OWNER, repo=_REPO)

    assert resolution.problem is None
    assert resolution.identity.name_with_owner == f"{_OWNER}/{_REPO}"
    assert resolution.identity.default_branch == "master"
    assert (
        log.read_text(encoding="utf-8").strip()
        == f"repo view {_OWNER}/{_REPO} --json nameWithOwner,defaultBranchRef"
    )


def test_canonical_identity_reports_the_repository_a_transfer_redirects_to(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registered owner/name that redirects resolves to the CANONICAL pair.

    This is the live `thewoolleyman/homelab` -> `mi-homelab/homelab`
    case: the registry still records the pre-transfer pair, GitHub keeps
    serving it by redirect, and only `nameWithOwner` locates the repo.
    """
    module = _load_module()
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_NAME_WITH_OWNER", "mi-homelab/homelab")

    resolution = module.canonical_identity(owner="thewoolleyman", repo="homelab")

    assert resolution.identity.name_with_owner == "mi-homelab/homelab"
    assert (
        module.https_url(name_with_owner=resolution.identity.name_with_owner)
        == "https://github.com/mi-homelab/homelab"
    )


def test_canonical_identity_reports_a_failing_gh_repo_view(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_VIEW_EXIT", "1")

    resolution = module.canonical_identity(owner=_OWNER, repo=_REPO)

    assert resolution.identity is None
    assert resolution.problem is not None
    assert resolution.problem.startswith(f"`gh repo view {_OWNER}/{_REPO}` failed")


def test_canonical_identity_reports_a_payload_carrying_no_name_with_owner(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without `nameWithOwner` there is no identity to clone or validate against."""
    module = _load_module()
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_VIEW_JSON", '{"nameWithOwner":null,"defaultBranchRef":null}')

    resolution = module.canonical_identity(owner=_OWNER, repo=_REPO)

    assert resolution.identity is None
    assert resolution.problem is not None
    assert "nameWithOwner" in resolution.problem


@pytest.mark.parametrize(
    "payload",
    [
        '{"nameWithOwner":"acme/widget","defaultBranchRef":null}',
        '{"nameWithOwner":"acme/widget","defaultBranchRef":{}}',
        '{"nameWithOwner":"acme/widget","defaultBranchRef":{"name":""}}',
    ],
)
def test_a_repository_with_no_branch_yet_resolves_no_default_branch(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: str
) -> None:
    """An empty repository has an identity but no default branch to land on."""
    module = _load_module()
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)
    monkeypatch.setenv("FAKE_GH_VIEW_JSON", payload)

    resolution = module.canonical_identity(owner=_OWNER, repo=_REPO)

    assert resolution.identity.name_with_owner == "acme/widget"
    assert resolution.identity.default_branch is None


def test_preflight_passes_an_authenticated_gh_and_names_both_ways_it_fails(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    _ = _install_fake_gh(tmp_path=tmp_path, monkeypatch=monkeypatch)

    assert module.preflight() is None

    monkeypatch.setenv("FAKE_GH_AUTH_EXIT", "1")
    unauthenticated = module.preflight()

    assert unauthenticated is not None
    assert unauthenticated.startswith("`gh auth status` failed")

    monkeypatch.setenv("PATH", "")

    assert module.preflight() == "`gh` is not on PATH"


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/acme/widget",
        "https://github.com/acme/widget.git",
        "https://github.com/acme/widget/",
        "https://github.com/ACME/Widget",
        "https://token@github.com/acme/widget.git",
        "ssh://git@github.com/acme/widget.git",
        "ssh://git@github.com:22/acme/widget.git",
        "git@github.com:acme/widget.git",
    ],
)
def test_parse_remote_url_collapses_every_form_naming_the_same_repository(*, url: str) -> None:
    module = _load_module()

    parsed = module.parse_remote_url(url=url)

    assert parsed.host == "github.com"
    assert parsed.slug == "acme/widget"


def test_parse_remote_url_reports_no_host_for_a_filesystem_remote(*, tmp_path: Path) -> None:
    """A local path names no host, so it can never satisfy a github.com check.

    This is the hole a tail-only comparison left open: `<tmp>/acme/widget`
    carries the very `owner/repo` tail the registry declares while being
    an entirely different repository.
    """
    module = _load_module()

    parsed = module.parse_remote_url(url=str(tmp_path / "acme" / "widget"))

    assert parsed.host == ""
    assert parsed.slug == "acme/widget"


def test_parse_remote_url_keeps_a_foreign_forge_distinguishable() -> None:
    module = _load_module()

    assert module.parse_remote_url(url="https://gitlab.com/acme/widget").host == "gitlab.com"
    assert module.parse_remote_url(url="git@gitlab.com:acme/widget.git").host == "gitlab.com"
