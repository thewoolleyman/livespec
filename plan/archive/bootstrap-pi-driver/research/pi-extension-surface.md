# pi extension surface — research pass 2

Researched 2026-08-15 against the LOCAL pi installation (the docs ship
inside the npm package, so every citation below is pinned to the
installed version): pi v0.84.1, npm package
`@earendil-works/pi-coding-agent`, installed at
`~/.local/lib/node_modules/@earendil-works/pi-coding-agent/` (symlinked
from `~/.local/bin/pi`). Doc citations are paths under that package's
`docs/` directory. Upstream docs mirror: https://pi.dev.

## Answer 1 — what `pi install <source>` consumes (docs/packages.md)

A **pi package** bundles four resource kinds: extensions (TS/JS),
skills, prompt templates, themes. Resources are declared either via a
`pi` key in `package.json` (`{"pi": {"skills": ["./skills"], ...}}`) or
auto-discovered from conventional directories (`extensions/`, `skills/`
(recursive `SKILL.md` folders), `prompts/`, `themes/`). Three source
types:

- `npm:@scope/pkg@1.2.3`
- `git:github.com/user/repo@ref` (also `https://`/`ssh://` forms) —
  cloned to `~/.pi/agent/git/<host>/<path>` (global) or
  `.pi/git/<host>/<path>` (project). **Refs are PINNED tags or
  commits**; `pi update --extensions` reconciles the clone to the
  configured ref but never moves it. Moving to a new ref is
  `pi install git:host/user/repo@new-ref` (rewrites settings).
- local paths (added to settings without copying; the dev-mode
  analogue of `claude --plugin-dir .`).

On git/npm install pi runs `npm install` **if `package.json` exists** —
i.e. `package.json` is optional for a git package, and a git repo with
no conventional resource directories loads zero resources without
error.

## Answer 2 — pi HAS project-scoped enablement (Claude-like, NOT Codex-like)

This resolves the scoping asymmetry question in initial-research.md:

- `pi install <source> -l` writes to **project settings
  `.pi/settings.json`** (vs the default user scope
  `~/.pi/agent/settings.json`). docs/packages.md: "Project settings can
  be shared with your team, and **pi installs any missing packages
  automatically on startup** after the project is trusted."
- So a governed repo commits `.pi/settings.json` with a `packages`
  array — the analogue of the committed `.claude/settings.json` — and
  pi performs the install step itself; there is NO separate
  enabled-vs-installed split like Claude's (the
  enabled-but-not-installed vacuity family in core's CLAUDE.md does not
  arise; the trust gate replaces it as the thing to verify).
- **Trust gate** (docs/settings.md §Project Trust): interactive startup
  prompts to trust a folder carrying project-local settings; decisions
  persist in `~/.pi/agent/trust.json`. **Non-interactive modes (`-p`,
  `--mode json`, `--mode rpc`) never prompt**: without a saved decision
  they follow global `defaultProjectTrust` (`ask`/`never` ⇒ project
  resources IGNORED; `always` ⇒ trusted), overridable per run with
  `--approve`/`-a`. Dispatcher/factory drives must therefore either
  pre-seed trust.json, set `defaultProjectTrust: always` on the host,
  or pass `-a` per invocation — this is the pi analogue of the Claude
  plugin-currency/session-currency verification concern and belongs in
  the Driver's install contract.

## Answer 3 — the binding mechanism: pi implements the Agent Skills standard

docs/skills.md: pi loads `SKILL.md` skill folders (frontmatter `name`,
`description`, optional `allowed-tools`, `disable-model-invocation` —
the SAME fields the Claude Driver's bindings use) from: global dirs
(`~/.pi/agent/skills/`, `~/.agents/skills/`), project dirs
(`.pi/skills/`, `.agents/skills/` in cwd and ancestors — trusted
projects only), **packages**, settings arrays, and `--skill <path>`.
Skills register as **`/skill:<name>` commands**; name rules are
lowercase/digits/hyphens (NO colons), so the surface is
`/skill:livespec-seed`, not `/livespec:seed`. Prompt templates
(docs/prompt-templates.md) are flat `.md` files that register bare
`/name` commands with positional-argument expansion — they could give
`/livespec-seed` directly. Extensions (TS/JS, `pi.registerCommand`)
could register arbitrary command names, but shipping first-party
TypeScript would pull a new language into the fleet's guardrail
surface for zero architectural gain.

**Recommended binding (default; maintainer may override):** eight
SKILL.md skills in the Driver package — the exact structural analogue
of `livespec-driver-claude`'s `skills/<name>/SKILL.md` bindings, thin,
reading CORE's harness-neutral prose and dispatching the spec-side CLI
named by the governed project's `.livespec.jsonc`. No extensions, no
prompt templates in increment 1 (a template layer can be added later
purely additively if `/livespec-<op>` ergonomics are wanted).

Non-interactive drive (the `codex exec` analogue): `pi -p "<prompt>"`
(print mode) and `--mode rpc` (JSON-per-line stdin protocol,
docs/rpc.md). rpc.md confirms **skill commands (`/skill:name`) and
prompt templates are expanded in `prompt`/`steer`/`follow_up`
messages**; expansion in `-p` print mode is expected to match but is
NOT yet explicitly verified — verify during the live end-to-end leg
(the acceptance evidence has to drive this path anyway).

## Answer 4 — how the pi Driver resolves core, and what core must ship

The existing resolution chain (env override → governed-project checkout
→ installed cache) maps cleanly:

1. Env override — unchanged.
2. Governed-project checkout — unchanged (this repo's
   `.claude-plugin/` when the governed project is livespec core).
3. Installed cache — core installed as a pi package lands at
   `.pi/git/github.com/thewoolleyman/livespec/` (project scope) or
   `~/.pi/agent/git/github.com/thewoolleyman/livespec/` (user scope);
   the Driver's skills resolve `prose/` and `scripts/` under
   `.claude-plugin/` inside that clone.

**Core likely needs NO new packaging artifact for pi.** A git-installed
package with no `pi` manifest and no conventional resource dirs loads
zero resources — which is exactly core's artifact-carrier role (the
Claude marketplace install of core also contributes no skills). Options
to make this explicit rather than incidental: an empty-resources `pi`
manifest declaration, or simply a spec clause stating core is consumed
by pi as a resource-less git package. Decide at proposal time; the
no-new-artifact reading keeps the single cross-runtime artifact rule
(nothing duplicated) trivially satisfied.

**Release-channel seam — RESOLVED (see closed open item 2 below):**
Claude/Codex marketplaces track the `release` BRANCH (`ref: release`),
giving free currency on each release. pi's docs describe git refs as
pinned tags/commits that updates never advance, but the SHIPPED
behavior (verified two independent ways on pi v0.84.1 — live scratch
observation and package-manager source read; details in closed open
item 2) is that a branch name is a valid ref and `pi update
--extensions` moves the clone to the fetched branch tip via a hard
reset. So the pi channel maps directly onto the fleet's
release-branch model: install `@release`, refresh with `pi update
--extensions`; no pin-bump machinery change is needed. The
docs-vs-behavior contradiction is the reason the spec contract
anchors the observed version and requires re-verification on a pi
major bump.

## Answer 5 — Driver repo shape (livespec-driver-pi)

A pi package: `package.json` with `keywords: ["pi-package"]` and
`pi.skills: ["./skills"]` (or the conventional `skills/` dir), carrying
eight thin skills — `livespec-seed`, `livespec-propose-change`,
`livespec-critique`, `livespec-revise`, `livespec-doctor`,
`livespec-prune-history`, `livespec-next`, `livespec-help` — each a
SKILL.md binding that resolves core's plugin root and defers to core
prose, mirroring `livespec-driver-claude`'s bindings and named per the
established convention (domain noun kept, only the runtime differs).
Everything else about the repo is standard driver-plugin fleet
membership per initial-research.md Finding 2 (the repo's own Python, if
any, stays under the fleet's red-green-replay + ROP rules; the skills
themselves are Markdown).

Install surface for a governed project (the docs/installation.md
analogue):

```bash
pi install git:github.com/thewoolleyman/livespec@<ref> -l          # core, artifact carrier
pi install git:github.com/thewoolleyman/livespec-driver-pi@<ref> -l # the Driver's eight skills
```

plus committed `.pi/settings.json` and a trust decision
(`--approve` / trust.json / `defaultProjectTrust`) for non-interactive
drives.

## Open items carried forward (each one small, none blocking scoping)

1. Verify `/skill:<name>` expansion in `-p` print mode empirically
   (rpc-mode expansion is documented; print-mode is assumed).
   PARTIALLY CLOSED 2026-08-15 by source read (independent adversarial
   reviewer): `dist/modes/print-mode.js` calls `session.prompt()`,
   which runs `_expandSkillCommand` since `expandPromptTemplates`
   defaults to true — print mode expands skill commands. The live
   `pi -p` drive in the end-to-end leg remains the closing evidence.
2. ~~Test whether a git ref may be a branch name (`@release`)~~
   CLOSED 2026-08-15, by two independent derivations that agree:
   (a) live scratch-project observation — `pi install
   git:github.com/thewoolleyman/livespec-driver-claude@release -l
   --approve` in a throwaway directory checked out a `release` branch
   tracking `origin/release`; after `git reset --hard HEAD~2` in the
   clone, `pi update --extensions --approve` fetched and moved it back
   to the branch tip (clone status `## release...origin/release`);
   the scratch project was deleted afterwards, so no residue remains
   under `~/.pi/agent/` or the scratch path. (b) source read of the
   shipped package manager (`dist/core/package-manager.js`, pi
   v0.84.1): `updateConfiguredSources` always includes git candidates,
   and `updateGit` runs `git fetch origin <ref>` then
   `git reset --hard FETCH_HEAD^{commit}` — so ANY ref, branch
   included, is moved to the fetched tip (a hard reset, not a
   fast-forward/merge). NOTE the docs contradiction: docs/packages.md
   says "Refs are pinned tags or commits" and that updates "do not
   move them to newer refs" — the shipped behavior for a branch ref
   is the opposite, which is why this record carries the source
   derivation and why the spec contract anchors the observed version
   (re-verify on a pi major bump).
3. Decide core's explicitness: resource-less-package-by-convention vs
   an explicit empty `pi` manifest.
4. Confirm the Codex-precedent spec sections to mirror
   (`SPECIFICATION/contracts.md` §"Plugin distribution",
   `non-functional-requirements.md` Codex dogfooding
   contracts/constraints) and draft their pi siblings.

Next: record the scope event on epic livespec-g5h5ff (requirement
carriers + explicit deferrals), then file the child work-items per
initial-research.md's rough shape.
