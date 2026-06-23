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

The v129 contract ALSO distributes `livespec` as a Codex plugin over
the SAME `prose/` and `scripts/` (a single cross-runtime artifact, no
duplication). The Codex-packaging half of the contract asserts:

- A Codex marketplace catalog at the repo-root path
  `.agents/plugins/marketplace.json`, name `livespec`, listing a single
  plugin `livespec` whose `source.path` is `./.claude-plugin` — the
  IDENTICAL payload dir the Claude marketplace plugin sources, so prose
  and scripts are shared, never duplicated.
- A paired `.codex-plugin/plugin.json` inside that payload dir
  (`.claude-plugin/.codex-plugin/plugin.json`), name `livespec`, carrying
  the same version and description as `.claude-plugin/plugin.json` (the
  single-artifact SoT), and declaring NO `skills`/`hooks` — core is an
  artifact carrier whose command surface ships from the
  `livespec-driver-codex` Driver, not from core.

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
_SCRIPTS_DIR = _PLUGIN_DIR / "scripts"
_SKILLS_DIR = _PLUGIN_DIR / "skills"
_CLAUDE_SKILLS_SYMLINK = _REPO_ROOT / ".claude" / "skills"

# Codex-packaging artifacts (v129 §"Plugin distribution"). The Codex
# marketplace catalog lives at the repo-root path .agents/plugins/, and
# the paired Codex plugin marker lives inside the SAME payload dir the
# Claude marketplace sources (.claude-plugin/), so a single artifact
# carries both runtime markers over one prose/scripts tree.
_CODEX_MARKETPLACE_JSON = _REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
_CODEX_PLUGIN_JSON = _PLUGIN_DIR / ".codex-plugin" / "plugin.json"

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


def test_codex_marketplace_json_exists_at_spec_path() -> None:
    """Codex marketplace catalog lives at .agents/plugins/marketplace.json (repo root)."""
    assert _CODEX_MARKETPLACE_JSON.is_file(), (
        f'SPECIFICATION/contracts.md §"Plugin distribution" requires a Codex '
        f"marketplace at {_CODEX_MARKETPLACE_JSON.relative_to(_REPO_ROOT)}; file not found."
    )


def test_codex_marketplace_json_is_valid_json() -> None:
    """The Codex marketplace catalog parses cleanly as JSON."""
    _ = json.loads(_CODEX_MARKETPLACE_JSON.read_text(encoding="utf-8"))


def test_codex_marketplace_name_is_livespec() -> None:
    """Codex marketplace top-level `name` equals `livespec` (stable v1 contract).

    The install command `codex plugin add livespec@livespec` depends on
    both the marketplace name and the plugin name being `livespec`.
    """
    data = json.loads(_CODEX_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "livespec", (
        f'SPECIFICATION/contracts.md §"Plugin distribution" mandates Codex '
        f"marketplace name 'livespec'; got {data['name']!r}."
    )


def test_codex_marketplace_lists_single_livespec_plugin_over_shared_payload() -> None:
    """Single plugin `livespec`, source `./.claude-plugin` — the SAME payload dir as Claude.

    Pointing the Codex plugin source at `./.claude-plugin` (the identical
    directory the Claude marketplace plugin sources) is the mechanical
    realization of the contract's "single cross-runtime artifact; no
    prose, wrapper, schema, or template is duplicated".
    """
    data = json.loads(_CODEX_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugins = data["plugins"]
    assert len(plugins) == 1, (
        f'SPECIFICATION/contracts.md §"Plugin distribution" mandates a single Codex '
        f"plugin in the marketplace; got {len(plugins)} entries."
    )
    entry = plugins[0]
    assert entry["name"] == "livespec", f"plugin name MUST be 'livespec'; got {entry['name']!r}."
    source = entry["source"]
    assert (
        source["source"] == "local"
    ), f"Codex plugin source.source MUST be 'local' (repo-relative); got {source['source']!r}."
    assert source["path"] == "./.claude-plugin", (
        f"Codex plugin source.path MUST be './.claude-plugin' — the SAME payload dir the "
        f"Claude marketplace sources, so prose/scripts are shared not duplicated; "
        f"got {source['path']!r}."
    )


def test_codex_plugin_json_exists_inside_shared_payload_dir() -> None:
    """The Codex plugin marker lives at .claude-plugin/.codex-plugin/plugin.json.

    Placing the `.codex-plugin/` marker inside the shared `.claude-plugin/`
    payload dir keeps the Codex install self-contained: when Codex installs
    the plugin it flattens `.claude-plugin/`, landing `prose/` and `scripts/`
    at the install root exactly as the Claude cache does.
    """
    assert _CODEX_PLUGIN_JSON.is_file(), (
        f'SPECIFICATION/contracts.md §"Plugin distribution" requires a paired '
        f"Codex plugin.json at {_CODEX_PLUGIN_JSON.relative_to(_REPO_ROOT)}; file not found."
    )


def test_codex_plugin_json_is_valid_json() -> None:
    """The Codex plugin.json parses cleanly as JSON."""
    _ = json.loads(_CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))


def test_codex_plugin_name_is_livespec() -> None:
    """Codex plugin `name` equals `livespec` (stable v1 contract)."""
    data = json.loads(_CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    assert data["name"] == "livespec", (
        f'SPECIFICATION/contracts.md §"Plugin distribution" mandates Codex plugin '
        f"name 'livespec'; got {data['name']!r}."
    )


def test_codex_plugin_version_matches_claude_plugin_json() -> None:
    """Codex and Claude plugin.json carry the same version — one cross-runtime artifact.

    The contract frames Codex and Claude distribution as a single artifact
    over shared prose/scripts; the two markers version in lockstep so a
    bump cannot leave the runtimes describing different releases.
    """
    codex = json.loads(_CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    claude = json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))
    assert codex["version"] == claude["version"], (
        f"Codex plugin.json version must match Claude plugin.json version (single "
        f"cross-runtime artifact).\n"
        f".claude-plugin/plugin.json:              {claude['version']!r}\n"
        f".claude-plugin/.codex-plugin/plugin.json: {codex['version']!r}"
    )


def test_codex_plugin_description_duplicates_plugin_json() -> None:
    """Codex plugin.json description = Claude plugin.json description verbatim (SoT)."""
    codex = json.loads(_CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    claude = json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))
    assert codex["description"] == claude["description"], (
        f"Codex plugin.json description does NOT match Claude plugin.json description; "
        f"the v1 SoT rule requires verbatim duplication.\n"
        f".claude-plugin/plugin.json:              {claude['description']!r}\n"
        f".claude-plugin/.codex-plugin/plugin.json: {codex['description']!r}"
    )


def test_codex_marketplace_description_duplicates_plugin_json() -> None:
    """Codex marketplace plugin-entry description = plugin.json description verbatim (SoT)."""
    marketplace = json.loads(_CODEX_MARKETPLACE_JSON.read_text(encoding="utf-8"))
    plugin = json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))
    marketplace_desc = marketplace["plugins"][0]["description"]
    assert marketplace_desc == plugin["description"], (
        f"Codex marketplace plugin description does NOT match plugin.json description; "
        f"the v1 SoT rule requires verbatim duplication.\n"
        f"plugin.json:                  {plugin['description']!r}\n"
        f".agents/plugins/marketplace.json: {marketplace_desc!r}"
    )


def test_codex_plugin_declares_no_command_surface() -> None:
    """Core's Codex plugin declares NO `skills`/`hooks` — it is an artifact carrier.

    Core exposes no Codex command surface of its own: the eight `/livespec:*`
    operations ship from the `livespec-driver-codex` Driver, which resolves
    core's prose/scripts at runtime. A `skills` or `hooks` key here would
    re-couple core to one agent runtime and shadow the Driver's bindings —
    the Codex analog of `test_no_skill_bindings_in_core`.
    """
    data = json.loads(_CODEX_PLUGIN_JSON.read_text(encoding="utf-8"))
    assert "skills" not in data, (
        "core's Codex plugin.json MUST NOT declare `skills`; the command surface "
        "ships from the livespec-driver-codex Driver, not from core."
    )
    assert "hooks" not in data, (
        "core's Codex plugin.json MUST NOT declare `hooks`; the Codex footgun guard "
        "ships from the livespec-driver-codex Driver, not from core."
    )


def test_codex_shared_payload_dir_carries_prose_and_scripts() -> None:
    """The Codex-sourced payload dir is the one carrying prose/ and scripts/.

    Guards the "no duplication" half of the contract from the payload side:
    the dir the Codex plugin sources (`.claude-plugin/`) is the very dir that
    holds `prose/` and `scripts/`, so there is no second copy for Codex.
    """
    assert _PROSE_DIR.is_dir(), f"shared payload dir missing prose/: {_PROSE_DIR}"
    assert _SCRIPTS_DIR.is_dir(), f"shared payload dir missing scripts/: {_SCRIPTS_DIR}"
    assert _CODEX_PLUGIN_JSON.parent.parent == _PROSE_DIR.parent, (
        "the Codex plugin marker MUST live inside the shared payload dir that holds "
        f"prose/scripts ({_PROSE_DIR.parent}); found marker under "
        f"{_CODEX_PLUGIN_JSON.parent.parent}."
    )
