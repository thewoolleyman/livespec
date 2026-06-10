"""Rule test for SPECIFICATION/contracts.md §"Plugin distribution".

Asserts the on-disk plugin-bundle artifacts match the live spec's
plugin-distribution contract, as realized after the Claude-binding
extraction (the Phase-3 work the contract's packaging parenthetical
anticipates — the `/livespec:*` SKILL.md bindings ship from the
`livespec-driver-claude` Driver repo; core retains the harness-neutral
prose, the reference CLIs, the schemas, and the templates):

- `.claude-plugin/marketplace.json` exists at the repo-root path
  the spec mandates.
- Marketplace name = `livespec`; single plugin entry name = `livespec`;
  source = `./.claude-plugin` (the plugin-root directory).
- `marketplace.json`'s plugin description duplicates `plugin.json`'s
  description verbatim (the SoT rule: `plugin.json` wins, marketplace
  duplicates manually for v1).
- Each of the eight spec-side operations ships its harness-neutral
  prose artifact at `.claude-plugin/prose/<name>.md` (the core half of
  the prose + thin-binding decomposition).
- Core ships NO `.claude-plugin/skills/` bindings — the Claude Code
  Driver bindings live in the `livespec-driver-claude` repo.
- The `.claude/skills` symlink is NOT present (its presence would cause
  Claude Code to discover skills as PROJECT-level without the
  `livespec:` namespace prefix).

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
_PROSE_DIR = _PLUGIN_DIR / "prose"
_SKILLS_DIR = _PLUGIN_DIR / "skills"
_CLAUDE_SKILLS_SYMLINK = _REPO_ROOT / ".claude" / "skills"

_OPERATIONS_PER_SPEC: tuple[str, ...] = (
    "seed",
    "propose-change",
    "critique",
    "revise",
    "doctor",
    "prune-history",
    "next",
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
    """Marketplace `plugins[]` has exactly one entry, named `livespec`, source `./.claude-plugin`."""
    data = json.loads(_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data["plugins"]
    assert len(plugins) == 1, (
        f'SPECIFICATION/contracts.md §"Plugin distribution" mandates a single plugin '
        f"in the marketplace; got {len(plugins)} entries."
    )
    entry = plugins[0]
    assert entry["name"] == "livespec", f"plugin name MUST be 'livespec'; got {entry['name']!r}."
    assert entry["source"] == "./.claude-plugin", (
        f"plugin source MUST be './.claude-plugin' (relative path to .claude-plugin directory); "
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


@pytest.mark.parametrize("operation", _OPERATIONS_PER_SPEC)
def test_prose_exists_for_each_operation(*, operation: str) -> None:
    """Each of the eight spec-side operations ships its core prose artifact.

    Per spec.md §"Contract + reference implementations architecture",
    the harness-neutral driving prose is CORE's artifact; Drivers (e.g.
    livespec-driver-claude) read it at runtime and bind it to their
    agent runtime.
    """
    prose_path = _PROSE_DIR / f"{operation}.md"
    assert prose_path.is_file(), (
        f"core MUST retain the harness-neutral prose for {operation!r}; "
        f"missing {prose_path.relative_to(_REPO_ROOT)}"
    )


def test_no_skill_bindings_in_core() -> None:
    """Core ships NO Claude Code skill bindings post-extraction.

    The `/livespec:*` SKILL.md bindings are Driver surface and ship from
    the `livespec-driver-claude` repo (plugin `livespec@livespec-driver-claude`).
    A reappearing `.claude-plugin/skills/` tree here would re-couple core
    to one agent runtime and shadow the Driver's bindings.
    """
    assert not _SKILLS_DIR.exists(), (
        f"{_SKILLS_DIR.relative_to(_REPO_ROOT)} exists; the Claude Code skill "
        f"bindings were extracted to the livespec-driver-claude repo — add new "
        f"bindings there, and keep core's plugin bundle binding-free."
    )


def test_claude_skills_symlink_absent() -> None:
    """`.claude/skills` MUST NOT be a symlink — it bypasses the plugin loader.

    A `.claude/skills` symlink (typically pointing at `../.claude-plugin/skills`)
    causes Claude Code to discover skills as PROJECT-level skills (no
    `livespec:` namespace prefix), defeating the `/livespec:*` invocation
    surface the spec mandates. The Driver plugin must be loaded via the
    marketplace install mechanism instead.
    """
    assert not _CLAUDE_SKILLS_SYMLINK.is_symlink(), (
        f"{_CLAUDE_SKILLS_SYMLINK.relative_to(_REPO_ROOT)} is a symlink; remove it. "
        f"The /livespec:* skills MUST be loaded via the marketplace install mechanism "
        f"(`/plugin marketplace add thewoolleyman/livespec-driver-claude` + "
        f"`/plugin install livespec@livespec-driver-claude`) so "
        f"they receive the `livespec:` namespace prefix per the spec."
    )
