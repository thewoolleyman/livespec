"""Registration tests for the host and deploy repositories in the fleet manifest.

The fleet's provisioning model lives in per-host and per-deploy repositories
(`.ai/gitops-deployment-discipline.md` section "Where the fleet's provisioning
model lives"). Each of them owes its own `.ai/gitops-deployment*.md` layer map
under `SPECIFICATION/contracts.md` section "Fleet agent-instruction core", and
that obligation only binds a repository the fleet manifest declares — so the
seven repositories are registered as adopters in
`.livespec-fleet-manifest.jsonc`.

Registration deliberately precedes wiring: a declared-but-unwired adopter is
meant to surface as a fleet-conformance finding rather than stay invisible
(`.ai/adding-an-adopter.md`). What this file asserts is therefore the
REGISTRATION only — the entry, the comment that explains it to a reader, and
that every manifest consumer livespec itself ships still reads the file.

The consumer test is the reason this file exists at all. Livespec parses this
one manifest three different ways, and only one of them is the vendored JSONC
parser; the other two are hand-rolled comment strippers in a maintainer script
and in the activity-report generator. A registration that lands fine under the
vendored parser can still break a hand-rolled one — the activity generator, for
instance, refuses outright when the manifest declares more repositories than it
has chart colours, which is a limit the manifest itself has no way to announce.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest
from livespec.parse.jsonc import loads

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _REPO_ROOT / ".livespec-fleet-manifest.jsonc"
_LIVESPEC_CONFIG = _REPO_ROOT / ".livespec.jsonc"
_ACTIVITY_GENERATOR = _REPO_ROOT / "docs" / "activity" / "update-activity.sh"

# The registration this file guards: every repository that owns a piece of the
# fleet's provisioning model, with the role each one plays. The role is the word
# the entry's own comment must use, so a reader of the manifest learns why the
# repository is governed without leaving the file.
_HOST_AND_DEPLOY_ADOPTERS: tuple[tuple[str, str], ...] = (
    ("vps-info", "host repository"),
    ("poweredge-xubuntu-info", "host repository"),
    ("gmktec-xubuntu-info", "host repository"),
    ("hp-xubuntu-info", "host repository"),
    ("fabro-hosts", "deploy repository"),
    ("otel-collector", "deploy repository"),
    ("local-llm", "deploy repository"),
)

_REGISTRATION_DATE = "2026-10-19"
_DEFERRAL_PHRASE = "installation prompt"

_EXPECTED_PROFILE: list[str] = ["baseline", "orchestrator-plugin"]
_EXPECTED_POSTURE = "released"


def _manifest_text() -> str:
    return _MANIFEST.read_text(encoding="utf-8")


def _manifest() -> dict[str, object]:
    value = loads(text=_manifest_text()).unwrap()
    assert isinstance(value, dict)
    return value


def _load_registry_module() -> ModuleType:
    """Import the refresher's registry union by path (`dev-tooling/` is no package)."""
    script = _REPO_ROOT / "dev-tooling" / "refresh_tenant_repos_registry.py"
    assert script.is_file(), f"manifest consumer is missing: {script}"
    spec = importlib.util.spec_from_file_location("refresh_tenant_repos_registry", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _adopters() -> list[dict[str, object]]:
    adopters = _manifest()["adopters"]
    assert isinstance(adopters, list)
    return [entry for entry in adopters if isinstance(entry, dict)]


def _entry_for(*, repo: str) -> dict[str, object]:
    matches = [entry for entry in _adopters() if entry.get("repo") == repo]
    assert (
        len(matches) == 1
    ), f"{repo!r} MUST appear exactly once in the manifest's adopters array; found {len(matches)}"
    return matches[0]


def _preceding_comment_block(*, repo: str) -> str:
    """The contiguous run of whole-line `//` comments above `repo`'s entry.

    Reads the raw bytes rather than a parsed object, because the comment is
    exactly what every JSONC parser discards.
    """
    lines = _manifest_text().splitlines()
    entry_indexes = [
        index
        for index, line in enumerate(lines)
        if f'"repo": "{repo}"' in line and line.lstrip().startswith("{")
    ]
    assert len(entry_indexes) == 1, f"expected one manifest entry line for {repo!r}"
    block: list[str] = []
    index = entry_indexes[0] - 1
    while index >= 0 and lines[index].lstrip().startswith("//"):
        block.append(lines[index].lstrip().removeprefix("//").strip())
        index -= 1
    return " ".join(reversed(block))


def _strip_whole_line_comments_then_trailing_commas(*, raw: str) -> dict[str, object]:
    """The `fleet-runner-inventory.py` strategy: drop `//` lines, then commas."""
    text = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("//"))
    value = json.loads(re.sub(r",(\s*[}\]])", r"\1", text))
    assert isinstance(value, dict)
    return value


def _substitute_whole_line_comments(*, raw: str) -> dict[str, object]:
    """The activity generator's strategy: blank every whole-line `//`."""
    value = json.loads(re.sub(r"^\s*//.*$", "", raw, flags=re.MULTILINE))
    assert isinstance(value, dict)
    return value


def _activity_generator_colour_count() -> int:
    """How many chart colours the activity generator declares.

    The generator is a bash wrapper around an inlined Python program, so its
    `COLORS` tuple is read out of the file text rather than imported.
    """
    text = _ACTIVITY_GENERATOR.read_text(encoding="utf-8")
    match = re.search(r"^COLORS = \((?P<body>.*?)^\)$", text, flags=re.MULTILINE | re.DOTALL)
    assert match is not None, f"{_ACTIVITY_GENERATOR} no longer declares a COLORS tuple"
    return len(re.findall(r'"#[0-9A-Fa-f]{6}"', match.group("body")))


@pytest.mark.parametrize(("repo", "role"), _HOST_AND_DEPLOY_ADOPTERS)
def test_host_and_deploy_repository_is_a_released_orchestrator_plugin_adopter(
    *,
    repo: str,
    role: str,
) -> None:
    """Each of the seven is one adopter entry on the shared profile and posture.

    `orchestrator-plugin` is what lets the factory carry per-repo work in the
    adopter; `released` is the homelab precedent, which tracks the moving
    livespec release channel. `role` is unused here — it is the comment test's
    expectation, and the shared parametrization keeps the two in one place.
    """
    assert role
    entry = _entry_for(repo=repo)
    assert (
        entry.get("profile") == _EXPECTED_PROFILE
    ), f"{repo!r} MUST declare profile {_EXPECTED_PROFILE}; found {entry.get('profile')!r}"
    assert (
        entry.get("posture") == _EXPECTED_POSTURE
    ), f"{repo!r} MUST declare posture {_EXPECTED_POSTURE!r}; found {entry.get('posture')!r}"


@pytest.mark.parametrize(("repo", "role"), _HOST_AND_DEPLOY_ADOPTERS)
def test_host_and_deploy_repository_entry_carries_its_registration_comment(
    *,
    repo: str,
    role: str,
) -> None:
    """The comment above each entry explains the registration to a reader.

    Three facts, because each answers a question the entry itself cannot: what
    the repository is for, when it was declared, and why it is not yet wired.
    """
    block = _preceding_comment_block(repo=repo)
    assert role in block, f"{repo!r}'s comment MUST name its role as a {role}; got: {block!r}"
    assert (
        _REGISTRATION_DATE in block
    ), f"{repo!r}'s comment MUST carry its registration date {_REGISTRATION_DATE}; got: {block!r}"
    assert _DEFERRAL_PHRASE in block, (
        f"{repo!r}'s comment MUST defer its onboarding wiring to the adopter-side "
        f"{_DEFERRAL_PHRASE}; got: {block!r}"
    )


def test_every_livespec_manifest_parser_reads_the_registered_repositories() -> None:
    """All three parse strategies livespec ships recover all seven entries.

    The hand-rolled strippers only tolerate WHOLE-LINE comments, so a trailing
    `//` beside an entry would pass the vendored parser and corrupt the other
    two. Asserting all three over the live file is what catches that.
    """
    raw = _manifest_text()
    expected = {repo for repo, _ in _HOST_AND_DEPLOY_ADOPTERS}
    for parsed in (
        _manifest(),
        _strip_whole_line_comments_then_trailing_commas(raw=raw),
        _substitute_whole_line_comments(raw=raw),
    ):
        adopters = parsed["adopters"]
        assert isinstance(adopters, list)
        declared = {
            entry["repo"] for entry in adopters if isinstance(entry, dict) and "repo" in entry
        }
        assert expected <= declared, f"parser lost {sorted(expected - declared)}"


def test_refresh_tenant_repos_resolves_every_registered_repository() -> None:
    """The registry union accepts the new entries and reports no conflict.

    `resolve_targets` is the refusal surface the repo refresher runs before it
    touches anything: a name that is not one safe path segment, or a repo two
    registries disagree about, refuses the whole pass. Running it over the live
    registries proves the registration cannot refuse a maintainer's refresh.
    """
    registry = _load_registry_module()
    config_parsed = loads(text=_LIVESPEC_CONFIG.read_text(encoding="utf-8")).unwrap()
    assert isinstance(config_parsed, dict)
    resolution = registry.resolve_targets(
        livespec_config=config_parsed,
        fleet_manifest=_manifest(),
    )
    assert resolution.conflicts == ()
    resolved = {target.repo for target in resolution.targets}
    for repo, _ in _HOST_AND_DEPLOY_ADOPTERS:
        assert repo in resolved, f"{repo!r} MUST resolve to a refresh target"


def test_activity_generator_has_a_colour_for_every_manifest_repository() -> None:
    """The activity report refuses a manifest wider than its chart palette.

    The generator exits rather than reuse a colour, so its palette is a hard
    ceiling on fleet-plus-adopter membership that nothing else in the repo
    announces. Every registration has to widen it.
    """
    manifest = _manifest()
    fleet = manifest["fleet"]
    adopters = manifest["adopters"]
    assert isinstance(fleet, list) and isinstance(adopters, list)
    declared = len(fleet) + len(adopters)
    colours = _activity_generator_colour_count()
    assert declared <= colours, (
        f"the manifest declares {declared} repositories but the activity generator "
        f"has only {colours} chart colours; it would refuse to run"
    )
