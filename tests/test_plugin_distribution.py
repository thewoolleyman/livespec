"""Rule test for SPECIFICATION/contracts.md §"Plugin distribution".

Asserts the on-disk plugin-bundle artifacts match the live spec's
plugin-distribution contract:

- `.claude-plugin/marketplace.json` exists at the repo-root path
  the spec mandates.
- Marketplace name = `livespec`; single plugin entry name = `livespec`;
  source = `.` (same directory as the marketplace catalog).
- `marketplace.json`'s plugin description duplicates `plugin.json`'s
  description verbatim (the SoT rule: `plugin.json` wins, marketplace
  duplicates manually for v1).
- The seven `/livespec:*` slash commands the spec enumerates each have
  a corresponding SKILL.md under `.claude-plugin/skills/<name>/SKILL.md`.
- The `.claude/skills` symlink is NOT present (its presence would cause
  Claude Code to discover the plugin's skills as PROJECT-level without
  the `livespec:` namespace prefix, which the spec mandates the plugin
  exposes).

Paired with the `## Plugin distribution` heading registered in
`tests/heading-coverage.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PLUGIN_DIR = _REPO_ROOT / ".claude-plugin"
_MARKETPLACE_JSON = _PLUGIN_DIR / "marketplace.json"
_PLUGIN_JSON = _PLUGIN_DIR / "plugin.json"
_SKILLS_DIR = _PLUGIN_DIR / "skills"
_CLAUDE_SKILLS_SYMLINK = _REPO_ROOT / ".claude" / "skills"

_SLASH_COMMANDS_PER_SPEC: tuple[str, ...] = (
    "seed",
    "propose-change",
    "critique",
    "revise",
    "doctor",
    "prune-history",
    "help",
)


def test_marketplace_json_exists_at_spec_path() -> None:
    """marketplace.json lives at .claude-plugin/marketplace.json (repo root)."""
    assert _MARKETPLACE_JSON.is_file(), (
        f'SPECIFICATION/contracts.md §"Plugin distribution" requires '
        f"marketplace.json at {_MARKETPLACE_JSON.relative_to(_REPO_ROOT)}; "
        f"file not found."
    )


def test_marketplace_json_is_valid_json() -> None:
    """marketplace.json parses cleanly as JSON."""
    text = _MARKETPLACE_JSON.read_text(encoding="utf-8")
    _ = json.loads(text)


def test_marketplace_name_is_livespec() -> None:
    """Marketplace top-level `name` field equals `livespec` per the spec."""
    data = json.loads(_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "livespec", (
        f"SPECIFICATION/contracts.md §\"Plugin distribution\" mandates "
        f"marketplace name 'livespec'; got {data['name']!r}."
    )


def test_marketplace_lists_single_livespec_plugin() -> None:
    """Marketplace `plugins[]` has exactly one entry, named `livespec`, source `.`."""
    data = json.loads(_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data["plugins"]
    assert len(plugins) == 1, (
        f'SPECIFICATION/contracts.md §"Plugin distribution" mandates a single plugin '
        f"in the marketplace; got {len(plugins)} entries."
    )
    entry = plugins[0]
    assert entry["name"] == "livespec", f"plugin name MUST be 'livespec'; got {entry['name']!r}."
    assert entry["source"] == ".", (
        f"plugin source MUST be '.' (same directory as marketplace.json); "
        f"got {entry['source']!r}."
    )


def test_marketplace_description_duplicates_plugin_json() -> None:
    """marketplace.json's plugin description = plugin.json's description verbatim.

    Per the v049 §"Plugin distribution" SoT rule: `plugin.json.description`
    is authoritative; `marketplace.json` duplicates it manually for v1.
    """
    marketplace = json.loads(_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugin = json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))
    marketplace_desc = marketplace["plugins"][0]["description"]
    plugin_desc = plugin["description"]
    assert marketplace_desc == plugin_desc, (
        f"marketplace.json plugin description does NOT match plugin.json "
        f"description; the v1 SoT rule requires verbatim duplication.\n"
        f"plugin.json:    {plugin_desc!r}\n"
        f"marketplace.json: {marketplace_desc!r}"
    )


@pytest.mark.parametrize("command", _SLASH_COMMANDS_PER_SPEC)
def test_skill_md_exists_for_each_slash_command(*, command: str) -> None:
    """Each of the seven /livespec:* commands enumerated in the spec has a SKILL.md."""
    skill_path = _SKILLS_DIR / command / "SKILL.md"
    assert skill_path.is_file(), (
        f'SPECIFICATION/contracts.md §"Plugin distribution" enumerates '
        f"/livespec:{command}; missing SKILL.md at "
        f"{skill_path.relative_to(_REPO_ROOT)}"
    )


def test_claude_skills_symlink_absent() -> None:
    """`.claude/skills` MUST NOT be a symlink — it bypasses the plugin loader.

    A `.claude/skills` symlink (typically pointing at `../.claude-plugin/skills`)
    causes Claude Code to discover the plugin's skills as PROJECT-level skills
    (no `livespec:` namespace prefix), defeating the `/livespec:*` invocation
    surface the spec mandates. The plugin must be loaded via the marketplace
    install mechanism instead.
    """
    assert not _CLAUDE_SKILLS_SYMLINK.is_symlink(), (
        f"{_CLAUDE_SKILLS_SYMLINK.relative_to(_REPO_ROOT)} is a symlink; remove it. "
        f"The plugin's skills MUST be loaded via the marketplace install mechanism "
        f"(`/plugin marketplace add ...` + `/plugin install livespec@livespec`) so "
        f"they receive the `livespec:` namespace prefix per the spec."
    )
