"""Tests for `dev-tooling/refresh_tenant_repos_registry.py` — the registry union.

The module under test is pure: it folds the four committed registries
(`.livespec.jsonc`'s `cross_repo_targets` and
`cross_repo_conformance_targets`, plus `.livespec-fleet-manifest.jsonc`'s
`fleet[]` and `adopters[]`) into one target set, and reports the two
conditions that must refuse a run before anything mutates — registries
that disagree about a repo, and a repo name that is not a single safe
path segment. Every case here is exercised against in-memory parsed
registry objects; no filesystem and no git are involved.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_registry.py"


def _load_module() -> ModuleType:
    """Import the registry helper by file path (`dev-tooling/` is not a package)."""
    assert _SCRIPT.is_file(), f"module under test is missing: {_SCRIPT}"
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_registry", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_target_set_is_the_union_of_all_four_registries() -> None:
    module = _load_module()

    resolution = module.resolve_targets(
        livespec_config={
            "cross_repo_targets": {
                "livespec": {
                    "github_url": "https://github.com/acme/livespec",
                    "local_clone": "/data/projects/livespec",
                    "default_branch": "master",
                },
                "planning-only": {"github_url": "https://github.com/acme/planning-only"},
            },
            "cross_repo_conformance_targets": {
                "livespec": {"github_url": "https://github.com/acme/livespec"},
                "conformance-only": {
                    "github_url": "https://github.com/acme/conformance-only",
                    "default_branch": "main",
                },
            },
        },
        fleet_manifest={
            "owner": "acme",
            "fleet": [{"repo": "livespec", "class": "core"}, {"repo": "fleet-only"}],
            "adopters": [{"repo": "adopter-only", "posture": "pinned"}],
        },
    )

    assert resolution.conflicts == ()
    assert [target.repo for target in resolution.targets] == [
        "adopter-only",
        "conformance-only",
        "fleet-only",
        "livespec",
        "planning-only",
    ]
    by_repo = {target.repo: target for target in resolution.targets}
    # A manifest-only entry derives its URL from the manifest `owner`.
    assert by_repo["fleet-only"].github_url == "https://github.com/acme/fleet-only"
    assert by_repo["fleet-only"].default_branch is None
    # A repo in several registries keeps the one default branch any of
    # them declared, rather than losing it to a later silent entry.
    assert by_repo["livespec"].default_branch == "master"
    assert by_repo["conformance-only"].default_branch == "main"
    assert by_repo["planning-only"].default_branch is None


def test_disagreeing_github_urls_are_a_conflict() -> None:
    module = _load_module()

    resolution = module.resolve_targets(
        livespec_config={
            "cross_repo_targets": {"widget": {"github_url": "https://github.com/acme/widget"}},
            "cross_repo_conformance_targets": {
                "widget": {"github_url": "https://github.com/other/widget"}
            },
        },
        fleet_manifest={"owner": "acme", "fleet": [], "adopters": []},
    )

    assert len(resolution.conflicts) == 1
    assert "disagree about the GitHub URL" in resolution.conflicts[0]


def test_disagreeing_default_branches_are_a_conflict() -> None:
    module = _load_module()

    resolution = module.resolve_targets(
        livespec_config={
            "cross_repo_targets": {
                "widget": {
                    "github_url": "https://github.com/acme/widget",
                    "default_branch": "master",
                }
            },
            "cross_repo_conformance_targets": {
                "widget": {
                    "github_url": "https://github.com/acme/widget",
                    "default_branch": "main",
                }
            },
        },
        fleet_manifest={"owner": "acme", "fleet": [], "adopters": []},
    )

    assert len(resolution.conflicts) == 1
    assert "disagree about the default branch" in resolution.conflicts[0]


@pytest.mark.parametrize(
    "unsafe",
    ["", ".", "..", "../escape", "nested/repo", "back\\slash", ".hidden", "-dash"],
)
def test_a_repo_name_that_is_not_a_single_safe_path_segment_is_a_conflict(*, unsafe: str) -> None:
    module = _load_module()

    resolution = module.resolve_targets(
        livespec_config={},
        fleet_manifest={"owner": "acme", "fleet": [{"repo": unsafe}], "adopters": []},
    )

    assert resolution.targets == ()
    assert len(resolution.conflicts) == 1
    assert "not a single safe path segment" in resolution.conflicts[0]
