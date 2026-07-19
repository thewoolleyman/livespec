---
topic: adopter-install-requires-explicit-plugin-install
author: claude-opus-4-8
created_at: 2026-07-19T06:28:00Z
spec_commitments:
  impl_followups:
    - id_hint: adopter-install-step-docs
      description: |
        Update the adopter-facing docs to match the amended contract: add the explicit `claude plugin install ... -s project` step and an install-verification gate to the Claude block of `docs/livespec-installation-prompt.md` (mirroring the Codex block, which already pairs `marketplace add` with `plugin add`), correct the updater-hook guidance so it verifies the touched record's `projectPath` instead of trusting a zero exit, and fix `AGENTS.md` §"Plugin install (end users)", which carries the same omission and additionally discourages the only command that installs.
---

## Proposal: Adopter install path requires an explicit per-project plugin install

### Target specification files

- SPECIFICATION/contracts.md

### Summary

§"Plugin distribution" currently defines the Claude Code end-user install path as committing a project-scoped `.claude/settings.json` with `extraKnownMarketplaces` and `enabledPlugins`. That enables a plugin but never installs one, so a conforming adopter lands in an enabled-but-not-installed state where no operation resolves and no error is reported. Amend the contract to require an explicit `claude plugin install <plugin>@<marketplace> -s project` alongside the committed settings file, correct the sentence that frames `/plugin install` as a discouraged machine-wide alternative, and add an install verification invariant stated against the `installed_plugins.json` record's `projectPath` rather than against a command's exit status.

### Motivation

Filed as work-item `livespec-s2de` (P1) after adopter repo `homelab` was found
in a fully-broken state having followed `docs/installation.md` to completion.

`~/.claude/plugins/installed_plugins.json` held project-scoped entries for 11
other projects and none for `/data/projects/homelab`, whose committed
`.claude/settings.json` enabled all three plugins. No `/livespec:*` operation
resolved, and nothing had ever reported an error.

The docs are not the root cause — they faithfully implement this contract. This
section currently presents the committed `.claude/settings.json` as THE
end-user install path and relegates `/plugin install` to a discouraged
machine-wide alternative, so a conforming adopter never installs anything.

Two supporting observations. First, the correct behavior already exists in the
fleet's own tooling: `livespec_dev_tooling/fleet/ensure_plugins.py:93-94`
issues `claude plugin install <plugin> -s project` then
`claude plugin update <plugin> -s project`. Fleet repos reach it through
`just bootstrap`; a third-party adopter has no justfile and never runs it. That
asymmetry — the working install path being maintainer-only and undocumented for
adopters — is the defect. That core's own tooling found an explicit `install`
necessary is also the strongest evidence that `enabledPlugins` does not install.

Second, the failure is structurally silent. Verified directly with cwd
`/data/projects/homelab`:

    $ claude plugin update livespec-orchestrator-git-jsonl@... -s project
    ✔ Plugin "..." updated from e48b9987c710 to ec2a1e7bd36b for scope project
      (/data/projects/resume). Restart to apply changes.
    EXIT=0

`-s project` reached into a different project's install and exited 0. The
`released`-posture SessionStart updater hook has therefore been advancing
unrelated projects' plugins on every session start while the invoking project
stayed uninstalled. The hook's `|| true` is not what hides this; the exit code
is genuinely 0, so no amount of error-propagation would have surfaced it. Only
an explicit `projectPath` assertion catches it, which is why amendment 3 states
the invariant in terms of the record rather than the exit status.

Same root-cause family as `livespec-driver-claude-6lc` (core-root resolution
picking `installed_plugins.json` `entries[0]`, a wrong sibling build): wrong-entry
resolution in `installed_plugins.json`, surfacing as two different symptoms.

### Proposed Changes

Three amendments to §"Plugin distribution", all in
`SPECIFICATION/contracts.md`. Each REPLACE-TARGET below exists verbatim in the
live file at the cited line.

### 1. The end-user install path must include an actual install

REPLACE-TARGET (line 197, opening sentence of the "End-user install path"
paragraph, quoted through the trailing colon that introduces the JSON block):

    End-user install path. Consumer projects enable `livespec` **at project scope** by committing a `.claude/settings.json` that declares the remote-GitHub marketplaces it needs under `extraKnownMarketplaces` and turns the plugins on under `enabledPlugins`, so the skills (and the Driver's bundled hooks) load ONLY in the governed project — never machine-wide:

REPLACEMENT:

    End-user install path. Consumer projects enable `livespec` **at project scope** by committing a `.claude/settings.json` that declares the remote-GitHub marketplaces it needs under `extraKnownMarketplaces` and turns the plugins on under `enabledPlugins`, so the skills (and the Driver's bundled hooks) load ONLY in the governed project — never machine-wide. The committed settings file is NECESSARY BUT NOT SUFFICIENT: `enabledPlugins` enables a plugin that is ALREADY installed and installs nothing by itself. Every enabled plugin MUST ALSO be installed into project scope by an explicit `claude plugin install <plugin>@<marketplace> -s project`, run from the project root. An adopter that commits only the settings file reaches an enabled-but-not-installed state in which no operation resolves and NO error is reported:

### 2. Correct the machine-wide-alternative sentence, which currently implies
### that `/plugin install` is the only install form and is always machine-wide

REPLACE-TARGET (inside line 214):

    A machine-wide `/plugin marketplace add thewoolleyman/livespec` + `/plugin install livespec@livespec` remains supported, but it enables the plugin in EVERY project on the host; the committed project-scoped form is the contract default.

REPLACEMENT:

    Installing is distinct from enabling, and install has its own scope. `claude plugin install <plugin>@<marketplace> -s project` is the contract default and is REQUIRED alongside the committed settings file. The machine-wide form (`/plugin marketplace add thewoolleyman/livespec` + `/plugin install livespec@livespec`, equivalently `-s user`) remains supported but installs into EVERY project on the host. Note that `-s project` resolves against the set of project-scoped install records rather than binding to the invoking project root: a `claude plugin update <plugin> -s project` issued from a project with no install record of its own can act on ANOTHER project's record and still exit 0. Tooling MUST therefore verify the record it touched, per the invariant below, rather than trusting a zero exit status.

### 3. Add the verification invariant

INSERT as a new paragraph immediately AFTER line 214's paragraph (before the
existing paragraph beginning "After installing core plus a runtime Driver,"):

    Install verification. A project is correctly provisioned only when, for EVERY key in its committed `enabledPlugins`, `~/.claude/plugins/installed_plugins.json` holds an entry for that plugin whose `projectPath` equals the project root. Enabled-without-installed, and installed-against-a-different-`projectPath`, are both defective states that any provisioning or currency tooling MUST detect and report loudly; neither may be inferred from a command's exit status. Reference implementation: `livespec_dev_tooling/fleet/ensure_plugins.py`, which derives the marketplace and plugin set from the committed `.claude/settings.json` and issues `claude plugin install ... -s project` followed by `claude plugin update ... -s project` for each.
