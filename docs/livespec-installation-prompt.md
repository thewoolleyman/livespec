# livespec installation prompt

Paste everything below the horizontal rule into an agent session
(Claude Code or OpenAI Codex) running in the root of the project you
want livespec to govern. See `installation.md` for the one-liner per
harness. The prompt is idempotent — re-running it skips whatever is
already set up and repairs whatever is missing or broken.

---

You are installing **livespec** governance on the current project.
livespec governs a living natural-language specification: a core
plugin carries the contract (prose, reference CLIs, schemas,
templates), a per-harness Driver plugin exposes the eight
`/livespec:*` operations (`seed`, `propose-change`, `critique`,
`revise`, `doctor`, `prune-history`, `next`, `help`), and a pluggable
orchestrator owns the implementation-side work-item ledger.

Your goal: bring THIS project to the point where the spec lifecycle
can start — `/livespec:seed` for a project with no spec yet, or a
clean `/livespec:doctor` run for a project that already has one — and,
for a project that will DISPATCH implementation work through the
Beads/Dolt + Fabro factory, stand up (or explicitly flag) the
post-seed factory infrastructure that unattended dispatch needs
(Phase 6). Follow the phases in order. Do not skip the survey. Where a
phase's work depends on a Phase-2 choice it says so: a project on the
zero-infrastructure `livespec-orchestrator-git-jsonl` backend is done
at Phase 5, and Phase 6 is a no-op for it.

## Ground rules

- **Idempotent, always.** Survey before you mutate. Anything already
  correctly set up: leave it alone and record it as "already
  present". Anything missing: add it. Anything present but wrong
  (e.g. a marketplace entry missing its `ref` pin): fix it and record
  it as "updated". Never clobber an existing config file — merge into
  it, preserving unrelated keys. Finish with a report table:
  component → already present / added / updated.
- **Ask, don't assume, on the two product choices** (Driver(s) and
  orchestrator — Phase 2). Use your harness's structured
  multiple-choice question facility if you have one (in Claude Code:
  the AskUserQuestion tool), always with a recommended option listed
  first and the trade-offs in the option descriptions. If you have no
  structured facility, ask in chat, leading with the recommendation.
  Everything that is not one of these two choices should be done
  without prompting.
- **Never touch secrets.** Nothing in this installation needs a
  credential value. If you encounter secret material, do not read,
  echo, or commit it.

## Phase 1 — Survey (read-only)

Detect the current state before changing anything:

1. **Which harness are you?** Claude Code → the project-scoped
   `.claude/settings.json` path applies. Codex → the host-wide
   `codex plugin` path applies (Codex has no project-scoped plugin
   enablement).
2. **Existing livespec state.** Check for:
   - `.livespec.jsonc` at the project root (if present, note its
     `spec_root` and any orchestrator section);
   - a populated spec tree (the `spec_root` from `.livespec.jsonc`,
     else the default `SPECIFICATION/` — "populated" means `spec.md`
     or equivalent template files exist);
   - Claude Code: `.claude/settings.json` — which of the
     marketplaces/plugins in Phase 3 are already declared;
   - Codex: `codex plugin marketplace list` and the
     `[plugins."…"]` entries in `~/.codex/config.toml` — record
     these as HOST-wide facts, never as this project's choices
     (see Phase 2);
   - a `.beads/` directory (an existing Beads/Dolt work-items store).
3. **Classify the project.** Exactly one of:
   - **Already governed**: `.livespec.jsonc` exists AND the spec tree
     is populated. The end state here is verification only — never
     re-seed (seed refuses when target files exist; the spec carries
     across backends unchanged).
   - **Brownfield**: the project has existing source code but no
     livespec spec. Seeding will author the initial specification OF
     the existing system — the seed interview draws on the codebase.
   - **Greenfield**: no meaningful source code yet. Seeding will
     author the specification first, before any implementation
     exists.

   State the classification to the user in one sentence before
   proceeding.

## Phase 2 — The two choices

Ask these two questions (structured picker, recommendation first).
Skip a question ONLY when a **project-level** artifact already
answers it. Host state is NOT project choice — in particular, Codex
plugin enablement is HOST-WIDE, so entries in `~/.codex/config.toml`
may exist because OTHER projects on this host installed them; their
presence never answers a question for THIS project. Concretely:

- **The Driver question is answered only by** the project's own
  enablement: on Claude Code, a committed `.claude/settings.json`
  that already enables a Driver. If the current harness's Driver is
  already installed host-wide (Codex), the install step later
  becomes a no-op, but you still ASK — the user may want the other
  harness's Driver wired for this project too (for Claude, that
  wiring is the project-scoped settings file, which only this
  question surfaces).
- **The orchestrator question is answered only by** the project's
  `.livespec.jsonc` naming one (`implementation.plugin`), or — on
  Claude Code — the project's committed settings enabling exactly
  ONE orchestrator plugin. Host-wide registrations never answer it,
  and MULTIPLE installed orchestrator plugins are ambiguity, not an
  answer: ask.

**Question 1 — which Driver(s)?**

- **The harness you are running in now (Recommended)** — Claude Code
  → `livespec-driver-claude`; Codex → `livespec-driver-codex`.
- **Both Drivers** — if the team drives the spec from both harnesses.
  Note the asymmetry: the Claude Driver enables per-project via a
  committed `.claude/settings.json`; the Codex Driver enables
  HOST-WIDE via `~/.codex/config.toml` and applies to every project
  on the machine.

**Question 2 — which orchestrator backend?**

- **`livespec-orchestrator-beads-fabro` (Recommended)** — parallel and
  concurrency-safe: work-items live in a Beads ledger on a Dolt SQL
  server; a Dispatcher can drain ready items into sandboxes
  unattended. Requirements (all POST-seed; none block today's
  install): a `bd` CLI (pinned v1.0.5), a running Dolt `sql-server`
  reachable over TCP, a per-tenant SQL user + database, and the
  tenant password supplied as the single bare `BEADS_DOLT_PASSWORD`
  environment variable injected by a credential wrapper the project
  declares in `.livespec.jsonc` (`credential_wrapper`) — plus, for
  unattended DISPATCH, the project's own GitHub App and a per-tenant
  Fabro server holding it, all walked in Phase 6. Choose this when
  multiple agents or an unattended loop will write the ledger
  concurrently.
- **`livespec-orchestrator-git-jsonl`** — serial, zero
  infrastructure: work-items and memos are committed JSONL files in
  the repo, one writer at a time. Choose this for a single-maintainer
  project or to avoid standing up any backing service. You can start
  here and migrate the ledger to Beads/Dolt later; the `/livespec:*`
  surface is identical.
- **Defer the choice** — spec-side work (`seed`, `doctor`,
  `propose-change`, `revise`, …) needs only core + Driver. The
  orchestrator can be added by re-running this prompt when
  implementation work starts.

## Phase 3 — Install the plugins

Three plugins (or two, if the orchestrator was deferred): **core**
(`livespec@livespec`), the chosen **Driver(s)**, and the chosen
**orchestrator**. Everything pins `release` — released builds are the
validated artifact; never install from a default branch.

**Each Driver registers ONLY in its own harness's mechanism.** The
Claude Driver goes in the project's `.claude/settings.json`; the
Codex Driver goes in `~/.codex/config.toml` via the `codex` CLI.
NEVER add `livespec-driver-codex` to `.claude/settings.json` — that
repo ships no Claude packaging, so Claude's marketplace add fails on
every session start (and never add `livespec-driver-claude` via the
`codex` CLI). "Both Drivers" therefore means: do the Claude block
below AND run the Codex commands below — not cross-registering
either Driver in the other harness's config. Core and the
orchestrator DO register in both places when both Drivers are
chosen (each harness resolves them independently).

**Claude Code** — merge (do not overwrite) the following into the
project's `.claude/settings.json`, keeping existing keys; substitute
the chosen orchestrator for the `livespec-orchestrator-beads-fabro`
lines, or drop them if deferred:

```jsonc
{
  "extraKnownMarketplaces": {
    "livespec":               { "source": { "source": "github", "repo": "thewoolleyman/livespec", "ref": "release" } },
    "livespec-driver-claude": { "source": { "source": "github", "repo": "thewoolleyman/livespec-driver-claude", "ref": "release" } },
    "livespec-orchestrator-beads-fabro": { "source": { "source": "github", "repo": "thewoolleyman/livespec-orchestrator-beads-fabro", "ref": "release" } }
  },
  "enabledPlugins": {
    "livespec@livespec": true,
    "livespec@livespec-driver-claude": true,
    "livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro": true
  }
}
```

Idempotency checks for this step: an entry that already exists with
`"ref": "release"` is "already present"; an entry that exists WITHOUT
the `ref` pin gets the pin added and is "updated". Commit the settings
file (project-scoped enablement is the contract default precisely so
that clones, CI, and sandboxes resolve the same plugins).

**Then install each plugin — the settings file alone does NOT install
anything.** `enabledPlugins` enables a plugin that is already
installed; it never fetches one. Run, from the project root, once per
enabled plugin:

```bash
claude plugin install livespec@livespec -s project
claude plugin install livespec@livespec-driver-claude -s project
claude plugin install livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro -s project
```

Substitute the project's OWN `enabledPlugins` keys. `-s project` is
required: the default `-s user` scope installs into every project on
the host. `install` exits 0 when the plugin is already installed, so
this step is idempotent and safe to re-run.

**Verify the install landed on THIS project** before moving on. This is
the check that catches the enabled-but-not-installed state, which
otherwise produces no error at all — every operation simply fails to
resolve:

```bash
python3 - "$PWD" <<'EOF'
import json, pathlib, sys
root = str(pathlib.Path(sys.argv[1]).resolve())
settings = json.loads(pathlib.Path(".claude/settings.json").read_text())
raw = settings.get("enabledPlugins", {})
markets = settings.get("extraKnownMarketplaces", {})
if not isinstance(raw, dict) or not isinstance(markets, dict):
    sys.exit("DEFECT: enabledPlugins and extraKnownMarketplaces must both be "
             "JSON objects in .claude/settings.json.")
if any(v is not True and v is not False for v in raw.values()):
    sys.exit("DEFECT: enabledPlugins values must be JSON booleans; a string "
             'like "false" is truthy in most languages and would be counted '
             "as enabled.")
# Count only TRUE-valued entries. A false value is an explicit disable, not
# an enablement: `{"p@m": false}` is a non-empty dict, so testing the dict
# for emptiness alone would let an all-false file slip past the guards below
# and certify a project with nothing enabled. `claude plugin disable <plugin>
# -s project` was observed writing exactly that (false, key retained, install
# record left intact); note `--all` cannot be combined with `--scope`.
enabled = {k for k, v in raw.items() if v is True}
if markets and not enabled:
    sys.exit("DEFECT: extraKnownMarketplaces declared but no plugin is enabled "
             "(enabledPlugins is empty, absent, or all-false). Restore "
             ".claude/settings.json from version control, then re-run the "
             "install step above. If this is a deliberate de-adoption, remove "
             "BOTH blocks and commit that, rather than leaving them "
             "inconsistent.")
if not enabled:
    sys.exit("DEFECT: no plugin is enabled; there is nothing to verify.")
# Per-marketplace non-vacuity. Whole-set non-vacuity above still passes a
# PARTIALLY stripped file: three marketplaces declared but only one plugin
# left enabled looks healthy, because the expected set is derived from the
# same mutable file every failure mode here corrupts. Require each declared
# marketplace to be referenced by at least one enabled plugin.
disabled = {k for k, v in raw.items() if v is False}
unreferenced = sorted(
    m for m in markets
    if not any(k.split("@", 1)[-1] == m for k in enabled)
)
if unreferenced:
    # Distinguish an explicit disable (key present, value false) from a strip
    # (key gone). Both fail — a governed project needs its plugins enabled —
    # but they call for opposite remedies, and sending an operator to hunt
    # corruption when the state is a visible `false` wastes their time.
    off = sorted(m for m in unreferenced
                 if any(k.split("@", 1)[-1] == m for k in disabled))
    gone = [m for m in unreferenced if m not in off]
    parts = []
    if off:
        parts.append(f"explicitly disabled: {off} — re-enable, or de-adopt by "
                     "removing both blocks and committing that")
    if gone:
        parts.append(f"no enablement entry at all: {gone} — looks partially "
                     "stripped; compare .claude/settings.json against version "
                     "control")
    sys.exit("DEFECT: marketplaces declared with nothing enabled from them. "
             + "; ".join(parts))
# Absent registry == nothing installed anywhere. Treat as empty rather than
# raising: the file legitimately does not exist on a machine where no plugin
# has ever been installed, and a traceback there reads as tooling breakage
# rather than the actionable "not installed" it actually is.
registry = pathlib.Path.home() / ".claude/plugins/installed_plugins.json"
try:
    installed = json.loads(registry.read_text()) if registry.is_file() else {}
except (OSError, json.JSONDecodeError) as exc:
    sys.exit(f"DEFECT: cannot read {registry}: {exc}")
if not isinstance(installed, dict) or not isinstance(installed.get("plugins", {}), dict):
    sys.exit(f"DEFECT: unexpected shape in {registry}; expected an object with "
             "a 'plugins' object.")
missing = [
    name for name in enabled
    if not any(e.get("projectPath") == root
               for e in installed.get("plugins", {}).get(name, []))
]
if missing:
    sys.exit(f"MISSING (enabled but not installed for {root}): {missing}")
print(f"OK: {len(enabled)} enabled plugins all installed for {root}")
EOF
```

A non-empty `MISSING` list means the plugin is enabled but not
installed for this project — re-run the install above. Do NOT infer
success from a command's exit status alone; see the `-s project`
caveat under the updater hook below.

The `DEFECT` branches matter as much as the `MISSING` one. A check that
merely enumerates `enabledPlugins` reports success whenever that set is
effectively empty, and several ordinary operations get it there — each
observed on Claude Code v2.1.215:

- `claude plugin uninstall <plugin> -s project` rewrites the committed
  `.claude/settings.json` and empties `enabledPlugins`, rather than
  merely dropping the install record.
- `claude plugin disable <plugin> -s project` writes `false` for that
  plugin in the same committed file, retaining the key and leaving the
  install record intact. (`--all` cannot be combined with `--scope`.)
- A single-plugin uninstall, a hand edit, or a merge resolution can drop
  some keys while leaving others — a partial strip, which whole-set
  non-vacuity alone still passes.

That is why the check counts only `true`-valued entries, and why it also
requires every declared marketplace to be referenced by an enabled
plugin. Without both guards it would certify a stripped project healthy.

After an uninstall or disable you did not intend, restore
`.claude/settings.json` from version control before re-verifying. If the
removal WAS intended — you are de-adopting — remove the `enabledPlugins`
and `extraKnownMarketplaces` blocks together and commit that, rather
than leaving a half-stripped file that reads as corruption.

Finally, tell the user to restart the session or run `/reload-plugins`
— a freshly installed plugin does not load into the session that
installed it.

**Codex** — for each selected plugin, skip any marketplace/plugin the
survey found already registered in `~/.codex/config.toml`:

```bash
codex plugin marketplace add thewoolleyman/livespec --ref release
codex plugin add livespec@livespec

codex plugin marketplace add thewoolleyman/livespec-driver-codex --ref release
codex plugin add livespec@livespec-driver-codex

# only if the orchestrator choice was livespec-orchestrator-beads-fabro:
codex plugin marketplace add thewoolleyman/livespec-orchestrator-beads-fabro --ref release
codex plugin add livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro
```

(For `livespec-orchestrator-git-jsonl`, the same two lines with that
name. Remind the user this registration is host-wide.)

**Ongoing currency — choose a posture, then wire it (idempotent).**
An adopter tracks livespec updates under one of TWO explicit
**currency postures**. Pick one now and set it up per harness; if an
equivalent setup is already present, leave it and record it "already
present".

- **`released` (DEFAULT — recommended for any adopter the maintainer
  owns or keeps current).** Track the moving `release` channel and
  stay auto-current every session: each new release reaches the
  project at its next session start with no manual step.
- **`pinned` (opt-out — for an adopter that wants to control its own
  updates).** Pin a FIXED release tag and update manually when the
  adopter chooses. The running build never drifts from the tag until
  someone bumps it.

Posture is a **local setup choice**, not a new `.livespec.jsonc`
field. It is realized entirely by the marketplace `ref` (a moving
`release` vs. a fixed `vX.Y.Z` tag) plus, on Claude, whether the
session-start updater hook is committed. For a fleet-TRACKED adopter,
the fleet manifest's `adopters[].posture` is the central declaration
of which posture that repo runs; a self-governing third-party adopter
simply chooses its `ref` (and, on Claude, the hook) directly. Either
way, nothing about posture is written into `.livespec.jsonc`.

livespec itself surfaces a stale plugin build so a drifted install
does not go unnoticed — blocking on Claude, and a non-blocking warning
on Codex (which auto-updates). Under `released` you never see it
(you stay current); under `pinned` it stays quiet because the running
build already matches the pinned tag.

**Claude Code.** Claude does NOT auto-update a project-scope install —
a build advances only when an explicit `claude plugin update` runs,
and it applies at the NEXT session ("restart required to apply"). So
on Claude a committed updater hook is load-bearing, and the posture is
realized by the marketplace `ref` PLUS that hook:

- **`released`** — keep the Phase-3 `extraKnownMarketplaces` entries
  pinned to `"ref": "release"` AND commit a `SessionStart` updater
  hook. Merge it (do not overwrite) into the project's
  `.claude/settings.json`, preserving any existing hooks. For the
  `released` posture this hook is REQUIRED, not optional:

  ```jsonc
  {
    "hooks": {
      "SessionStart": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "claude plugin marketplace update >/dev/null 2>&1 || true; for p in livespec@livespec livespec@livespec-driver-claude livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro; do claude plugin update \"$p\" -s project >/dev/null 2>&1 || true; done"
            }
          ]
        }
      ]
    }
  }
  ```

  Substitute the project's OWN enabled plugins for the `for` list —
  exactly the `enabledPlugins` keys committed in Phase 3, each spelled
  `plugin@marketplace` (drop the orchestrator entry if it was
  deferred). Three load-bearing details:

  - **`-s project` is load-bearing, and still not sufficient.** The
    default `-s user` scope is a silent no-op (or failure) against a
    project-scope install, so an updater missing `-s project` never
    advances the build — the exact `resume`-adopter trap. But
    `-s project` resolves against the set of project-scoped install
    RECORDS rather than binding to the invoking project root: run from
    a project that has no record of its own, it can act on ANOTHER
    project's record and still exit 0. Observed in the field:

    ```text
    $ cd /data/projects/homelab      # no install record of its own
    $ claude plugin update livespec-orchestrator-git-jsonl@... -s project
    ✔ Plugin "..." updated ... for scope project (/data/projects/resume).
    EXIT=0
    ```

    So a zero exit proves nothing about the invoking project. `claude
    plugin marketplace update` with no name refreshes ALL registered
    marketplaces to their pinned refs, so it needs no per-marketplace
    list.
  - **The hook cannot bootstrap a missing install.** `claude plugin
    update` only advances an ALREADY-INSTALLED plugin, and the hook
    swallows output with `>/dev/null 2>&1 || true`. Combined with the
    previous point the failure is structurally invisible: the exit
    code is genuinely 0, so removing `|| true` would not surface it
    either. The install step in Phase 3 — not this hook — is what
    provisions a project; re-run the Phase-3 verification snippet if
    operations stop resolving.
  - **Never track `release` WITHOUT this hook.** That "illegal middle"
    — a moving `release` ref and no updater — freezes the installed
    build in place while the marketplace advances underneath it, so
    the project silently falls behind. Do not do it: either commit the
    hook (`released`) or pin a tag (`pinned`), never neither.

  One-session lag: because `claude plugin update` applies at the next
  session start, the project lands one release-tick behind the tip
  rather than instantly current — the trade-off for a
  zero-infrastructure updater. A session that must be current
  immediately can run `/reload-plugins` AFTER the hook has run;
  `/reload-plugins` is a slash command the user types, so the shell
  hook cannot auto-invoke it. (Fleet repos wrap this same behavior in
  a `just ensure-plugins` recipe that derives the plugin list from
  settings; adopters need no `just`/`mise` — the raw `claude plugin`
  commands above are the decoupled equivalent.)

- **`pinned`** — set the Phase-3 marketplace entries to a FIXED
  release tag, `"ref": "<vX.Y.Z>"`, and OMIT the updater hook
  entirely. Update by editing the `ref` to a newer tag when the
  adopter chooses. The stale-build gate never trips, because the
  running build already matches the pinned tag.

**Codex.** Codex auto-upgrades a release-tracking git marketplace to
its `--ref` tip at every session start, so on Codex you do NOT ship a
hook — the posture is realized entirely by the `--ref` passed in the
Phase-3 Codex registration:

- **`released`** — the Phase-3 `--ref release` registration is already
  the released posture; there is nothing further to wire:

  ```bash
  codex plugin marketplace add thewoolleyman/livespec --ref release
  codex plugin add livespec@livespec
  ```

  Codex automatically upgrades this release-tracking marketplace to
  the release tip at every session start — no hook, no manual step. Do
  NOT commit a Codex `SessionStart` `codex plugin marketplace upgrade`
  hook: it is redundant AND races Codex's native auto-upgrade, logging
  non-fatal errors for no benefit. (Same one-session lag as Claude;
  the auto-upgrade needs network at session start.)

- **`pinned`** — register (in Phase 3) with a FIXED tag instead of
  `release`:

  ```bash
  codex plugin marketplace add thewoolleyman/livespec --ref <vX.Y.Z>
  ```

  Native auto-upgrade is a no-op on an immutable tag, so the build
  stays put; bump by re-adding the marketplace with a newer tag.

**The runtime asymmetry (read this before choosing).** Claude
REQUIRES a committed updater hook to stay current — it does not
auto-update a project-scope install — whereas Codex is auto-current
NATIVELY with no hook at all. So the "illegal middle" (tracking
`release` with no updater) is a **Claude-only hazard**; it cannot
occur on Codex, where the auto-upgrade is unconditional. Note too that
Codex enablement is **host-wide** (`~/.codex/config.toml`, applying to
every project on the host), unlike Claude's project-scoped, committed
enablement.

Record the outcome in the final idempotency report, per harness:
"currency posture (`released` / `pinned`) + session self-update hook —
already present / added / updated".

## Phase 4 — Record the orchestrator selection in `.livespec.jsonc`

Choosing an orchestrator in Phase 2 has TWO independent effects, and
the install is not done until BOTH are in place:

- **Enablement + install** (Phase 3) — on Claude, the
  `.claude/settings.json` `enabledPlugins` entry AND the paired
  `claude plugin install <plugin>@<marketplace> -s project`; on Codex,
  the `codex plugin add` registration. Both halves are required on
  Claude: enablement alone leaves the orchestrator's `/<plugin>:*`
  skills unavailable. Together they make those skills *available* in
  the harness.
- **Selection** (this phase) — the `implementation.plugin` key in
  `.livespec.jsonc` *names* that orchestrator as THIS project's
  active one. This is the key livespec's OWN prose reads to route to
  the orchestrator: `/livespec:doctor`'s `capture-as-work-item`
  disposition, the auto-memory redirect hook, and `/livespec:revise`'s
  post-step gap check each resolve their work-item front-end from
  `implementation.plugin` — never from harness enablement. Enabling
  the plugin WITHOUT setting this key leaves the skills installed but
  unreachable through livespec: the exact symptom
  "`capture-as-work-item` isn't offered — no impl orchestrator
  (`implementation.plugin`) is configured."

Never PRE-CREATE `.livespec.jsonc` before seed runs, but DO record the
selection once the file exists:

- **No `.livespec.jsonc` yet (greenfield / brownfield):** leave it
  absent for now. `/livespec:seed` is the only operation designed to
  run before the config exists, and its CLI writes the file itself,
  atomically with the spec tree. (Seed refuses only when a
  template-declared *spec* file already exists, and it PRESERVES an
  existing `.livespec.jsonc` verbatim rather than clobbering it — so
  it is the spec tree, not this config file, that a premature write
  would collide with.) Recording `implementation.plugin` for this
  project therefore happens AFTER seed, in Phase 5.
- **Existing `.livespec.jsonc` (already-governed project, or a re-run
  after seed):** if an orchestrator was chosen in Phase 2, MERGE the
  selection key into the file — without prompting; this is the
  mechanical consequence of the Phase-2 choice, not a new decision —
  preserving all other keys and comments:

  ```jsonc
  { "implementation": { "plugin": "<chosen-orchestrator>" } }
  ```

  Substitute the chosen plugin name (e.g.
  `livespec-orchestrator-git-jsonl` or
  `livespec-orchestrator-beads-fabro`). Idempotency: if the key is
  already present and names the chosen orchestrator, record it
  "already present"; if it names a DIFFERENT orchestrator, that is a
  conflict — surface it to the user rather than silently overwriting.

  SEPARATELY, the chosen orchestrator MAY own a top-level config
  section named for itself (`"<plugin-name>": { … }`) carrying its
  `format`, a `compat` pin (a concrete release tag, not a branch
  name), and any store-specific keys — add it per that orchestrator
  plugin's own documentation. For `livespec-orchestrator-git-jsonl`
  this section is OPTIONAL (the store defaults to `work-items.jsonl`
  at the project root), so a bare `implementation.plugin` is already a
  complete, working selection. For `livespec-orchestrator-beads-fabro`
  the section carries the Dolt tenant connection block and needs
  values from that plugin's onboarding; offer to add it, and note the
  post-seed factory infrastructure (Phase 6) it depends on.

## Phase 5 — Verify, then hand off to the spec lifecycle

1. **Plugins loaded**: `/livespec:help` (Codex:
   `codex exec 'livespec:help'`) lists the eight operations. If it
   does not, the harness has not reloaded plugins — resolve that
   before continuing. A Driver installed for the OTHER harness
   cannot be verified from this session: tell the user to open that
   harness in this project and verify there (Claude Code: start a
   session — or `/reload-plugins` in a running one — then
   `/livespec:help`; Codex: `codex exec 'livespec:help'`), and mark
   that Driver "installed — verification pending in <harness>" in
   the final report rather than claiming it verified.
2. **By classification**:
   - **Greenfield / brownfield** (no spec yet): tell the user the
     project is seed-ready, and that running `/livespec:seed` starts
     the attended interview that authors the initial specification
     (and writes `.livespec.jsonc`). For brownfield, note the
     interview will draw on the existing codebase. Offer to start it
     now if the user is ready — seeding is an attended dialogue, not
     an unattended step. **If seed runs in this session AND an
     orchestrator was chosen (not deferred), record the selection
     immediately afterward** per Phase 4's already-governed rule —
     seed writes only the skeleton `{ "template": … }` config, so
     `implementation.plugin` must be merged into the now-existing
     `.livespec.jsonc` before the work-item routing (`doctor`'s
     `capture-as-work-item`, the auto-memory redirect, `revise`'s gap
     check) becomes reachable.
   - **Already governed**: run `/livespec:doctor` and surface its
     findings. Do not seed. (Phase 4 has already recorded
     `implementation.plugin` if an orchestrator was chosen, so
     `capture-as-work-item` is offered on every non-`pass` finding.)
3. **Factory infrastructure — branch on the Phase-2 orchestrator
   choice.** Spec-side work is complete once the above passes;
   implementation work-items can be filed now. Whether DISPATCHING one
   into a sandbox needs more setup depends on the orchestrator:
   - **`livespec-orchestrator-beads-fabro`:** post-seed infrastructure
     remains before an implementation work-item can be dispatched and
     driven — the project's GitHub App, the full dispatch credential
     set, the work-items tenant, and the per-tenant Fabro server.
     **Phase 6** walks it. None of it blocks seeding or any spec-side
     operation; proceed to Phase 6.
   - **`livespec-orchestrator-git-jsonl` or orchestrator deferred:**
     there is NO factory infrastructure to stand up — git-jsonl
     dispatches serially with no sandbox, no Fabro server, and no
     GitHub App; a deferred orchestrator has nothing to provision yet.
     This project is DONE after the report below (Phase 6 is a no-op
     you still record as such).
4. **Print the idempotency report**: every component this prompt
   touched or verified, marked "already present", "added", or
   "updated" — so a re-run that changes nothing proves itself as a
   no-op. For a `livespec-orchestrator-git-jsonl` or
   orchestrator-deferred project this is the FINAL step. For a
   `livespec-orchestrator-beads-fabro` project, continue to Phase 6
   FIRST and print the report at its end, so the factory-infrastructure
   rows are included.

## Phase 6 — Post-seed factory-infrastructure prerequisites (dispatch)

**Bottom line first.** Phases 1–5 brought the SPEC lifecycle to life.
This phase provisions the separate infrastructure the IMPLEMENTATION
side needs before a work-item can be *dispatched* — drained from the
ledger into an isolated **Fabro sandbox**, driven Red→Green, and landed
as a merged pull request by the unattended **Dispatcher** (the
"factory"). It runs POST-seed and is **branched by the orchestrator you
chose in Phase 2**; for most adopters it is either the whole job or
nothing:

- **`livespec-orchestrator-git-jsonl` → NO-OP (this is CORRECT and
  COMPLETE — a genuine no-op, not a hand-wave).** git-jsonl is the
  serial, zero-infrastructure backend, and Phase 6 provisions nothing for
  it for three concrete reasons:
  1. **Dispatch is IN-SESSION, not a factory.** git-jsonl's `implement`
     walks the user through Red→Green live in the session — author the
     failing test, implement until it passes, close the work-item — so
     there is NO Dispatcher, NO Fabro sandbox, and NO Fabro server to
     stand up.
  2. **GitHub goes through the operator's OWN commit / PR cycle.** The
     change lands as a commit inline or via the consumer's own PR cycle
     under the operator's ambient `gh` auth — so there is NO per-tenant
     GitHub App to create and NO `FABRO_HOME` to target.
  3. **The work-items store is a local file.** Work-items are a
     `work-items.jsonl` committed alongside the code and merged one
     writer at a time — so there is NO Dolt tenant and NO
     `BEADS_DOLT_PASSWORD`.

  If you chose git-jsonl you are DONE at Phase 5 — do NOT create a GitHub
  App, do NOT stand up a Fabro server, and do NOT ask the user for any
  dispatch credential. Record each Phase-6 row in the report as "n/a —
  git-jsonl (in-session Red→Green; PRs via your own cycle; local JSONL
  store)".
- **Orchestrator deferred → deferred with the choice.** The factory
  infrastructure is only meaningful once a beads-fabro orchestrator is
  selected. Tell the user that re-running this prompt and choosing
  `livespec-orchestrator-beads-fabro` later will walk this phase then;
  record the Phase-6 rows as "deferred with orchestrator".
- **`livespec-orchestrator-beads-fabro` → APPLIES.** Work the steps
  below. Keep them idempotent throughout: a re-run leaves correct setup
  alone, repairs what is missing, and SURFACES (never silently
  overwrites) a conflict.

**Why this phase exists (the failure it prevents).** A Fabro server
holds exactly ONE GitHub App identity — a structural fact of the
engine. Dispatching an adopter's work-item through a server that holds a
DIFFERENT App (for example the fleet's shared server) fails at
sandbox-creation time with *"the GitHub App is not installed for the
`<org>` organization"* — that server's App has no installation on the
adopter's target org/repo. An adopter therefore brings its OWN GitHub
App, its OWN dispatch credential set, and its OWN per-tenant Fabro
server holding that App. livespec is adopter-agnostic: the fleet is
"adopter #0" with no privileged path, so every adopter — the fleet
included — walks exactly these steps.

> **Scope — the seven steps below are `livespec-orchestrator-beads-fabro`
> ONLY.** The GitHub App, the dispatch credential set, the Dolt tenant,
> the per-tenant Fabro server, the `FABRO_HOME` targeting, and the
> preflight are all beads-fabro FACTORY machinery. A
> `livespec-orchestrator-git-jsonl` adopter does NONE of them — it is
> already DONE at Phase 5 per the branch table above (in-session
> Red→Green, PRs via the operator's own cycle, local JSONL store). Never
> tell a git-jsonl adopter to create a GitHub App or stand up a Fabro
> server. If your Phase-2 choice was not beads-fabro, skip this entire
> numbered sequence.

1. **Surface the full dispatch credential set — up front, not one
   failure at a time.** Enumerate for the user EVERY credential the
   dispatch path consumes, so readiness is known before the first
   dispatch rather than discovered as a chain of mid-run failures. The
   orchestrator's contract requires the dispatch TARGET's own configured
   `credential_wrapper` to inject the FULL per-dispatch set, and every
   credential-consuming seam on the dispatch path fails closed naming
   the specific missing variable AND the target's own wrapper as the fix
   (never a fleet wrapper). The set:
   - **GitHub App environment** — `GITHUB_APP_ID` + `GITHUB_PRIVATE_KEY`
     (the App's private-key PEM); optionally `GITHUB_APP_INSTALLATION_ID`
     (pin when the App has more than one installation) and
     `GITHUB_API_URL` (a GitHub Enterprise API root). This is the SOLE
     GitHub credential on the dispatch path — there is no personal
     access token fallback.
   - **Work-items store secret** — `BEADS_DOLT_PASSWORD` (the bare
     variable, no per-tenant suffix): the tenant's Dolt password.
   - **Engine LLM credential** — `CLAUDE_CODE_OAUTH_TOKEN` today (the
     model auth the Dispatcher projects into each sandbox; the variable
     is engine-specific by nature).

   All THREE live in the adopter's OWN `credential_wrapper` (Step 3);
   name them here so the user can gather them before proceeding. Do NOT
   read, echo, or commit any value — presence is probed by byte count
   only (`printenv NAME | wc -c`).

2. **Create and install the adopter's own GitHub App** (guided — YOU
   walk the human through the GitHub UI actions you cannot perform, and
   wire what is wireable). Idempotency probe FIRST: if Step 7's preflight
   already mints a token and the App is installed on the target org/repo,
   this App is set up — record "already present" and skip creation.
   Otherwise:
   - **Create the App (human, GitHub UI):** Settings → Developer settings
     → GitHub Apps → New GitHub App. Grant the repository permissions the
     dispatch operations imply:
     - **Contents: Read & write** — the in-sandbox fresh clones and the
       branch/commit pushes.
     - **Pull requests: Read & write** — the in-sandbox `gh pr create`
       leg and the merge-poll.
     - **Workflows: Read & write** — REQUIRED: a push that touches any
       `.github/workflows/` file structurally needs the App's `workflows`
       grant, or the push is rejected.

     Capture the numeric **App ID**.
   - **Generate the private key (human, GitHub UI):** on the App's page,
     "Generate a private key" → download the `.pem`. This is the durable
     App secret — it goes into the credential wrapper's secret backend
     (Step 3), NEVER into the repo, a log, or `.livespec.jsonc`.
   - **Install the App on the target (human, GitHub UI):** the App's
     "Install App" tab → install on the org/account that owns the target
     repo, scoped to that repo (or "All repositories" if the tenant
     dispatches several). Capture the **installation ID** from the
     resulting URL (`…/settings/installations/<installation_id>`) —
     needed as `GITHUB_APP_INSTALLATION_ID` only if the App ends up with
     more than one installation.

   State clearly which parts are human-only UI actions (App creation, key
   generation, installation) and which you will wire (the wrapper entries
   in Step 3, the per-tenant server standup in Step 5, and the preflight in
   Step 7).

3. **Wire the `credential_wrapper` to inject the full set.** The adopter
   declares, in `.livespec.jsonc`, a `credential_wrapper` — an opaque
   argv prefix the orchestrator's bd-backed CLIs and the dispatch path
   re-exec through, so a bare invocation self-heals its secrets by
   injecting them from the adopter's OWN secret backend. Shape (an
   existing adopter's precedent):

   ```jsonc
   { "credential_wrapper": ["/path/to/with-<tenant>-env.sh", "--"] }
   ```

   The wrapper is the adopter's own (backed by the adopter's own secret
   store — e.g. a 1Password Environment); it must inject the full Step-1
   set (`GITHUB_APP_ID`, `GITHUB_PRIVATE_KEY`, optionally
   `GITHUB_APP_INSTALLATION_ID`, `BEADS_DOLT_PASSWORD`, and
   `CLAUDE_CODE_OAUTH_TOKEN`) into the environment of anything it wraps.
   An adopter that already runs `bd` through a wrapper for
   `BEADS_DOLT_PASSWORD` EXTENDS that same wrapper to add the App
   environment + engine credential — it does NOT create a second wrapper.
   Idempotency: if `credential_wrapper` is present and each required
   variable probes non-empty under it (`printenv NAME | wc -c`, byte
   count only), record "already present" and add only the missing keys;
   otherwise add the key/entries. NEVER commit a secret value, and for an
   INDEPENDENT (non-fleet) tenant NEVER reference the fleet's wrapper —
   the dispatch-path diagnostics name the TARGET's own wrapper as the
   fix.

4. **Provision the work-items tenant (`bd` / Dolt).** The beads backend
   needs host-level runtime that plugin installation does NOT provision:
   the `bd` CLI (pinned v1.0.5) with `LIVESPEC_BD_PATH` pointing at it, a
   running Dolt `sql-server` reachable over TCP (the fleet reference is
   `127.0.0.1:3307`), a per-tenant SQL user + DB-scoped grant (the
   isolation boundary — password distinctness is NOT the boundary), and
   the `.beads/` pointer files in the repo: a committed `config.yaml`
   carrying the `dolt.*` server host/port/user/database keys (NO `socket`
   key, NO password) and a gitignored, regenerable `metadata.json`. This
   is a REFERENCE, not a duplication: follow the orchestrator plugin's
   own tenant-provisioning documentation and the Beads runtime-
   prerequisites procedure it points to; do NOT run `bd init` inside a
   primary checkout or worktree (it auto-commits and clobbers `.beads/`).
   Idempotency probe: `bd list` (under the credential wrapper) returns
   the ledger without a "no beads database found" error.

5. **Stand up the adopter's per-tenant Fabro server holding its OWN App
   identity.** *(beads-fabro ONLY — a git-jsonl adopter has no Fabro
   server and skips this entire step; see the scope note above.)* This is
   the ROOT of the "App is not installed for the `<org>` organization"
   dispatch failure. A Fabro server holds exactly
   ONE App integration, so an adopter's dispatch MUST run against a
   server instance that holds the ADOPTER's App — a dedicated
   `FABRO_HOME` carrying the adopter's `app_id`, its PEM in the server
   process environment, and its own listen port and authentication —
   NEVER the fleet's shared server (whose App is not installed for the
   adopter's target). A dispatch preflight SHOULD verify the serving App
   can reach the target repo before launching, refusing with an
   actionable diagnostic rather than failing inside the engine run. The
   requirement, its shape, and the root cause are authoritative; the
   fleet's reference realization is the containerized orchestrator
   supervisor (`orchestrator-image/` + `orchestrator-entrypoint.sh` in
   the orchestrator plugin's repository), which provisions a Fabro server
   from the injected `GITHUB_APP_ID` / `GITHUB_PRIVATE_KEY` (a
   hand-written `settings.toml` with `[server.integrations.github]
   strategy = "app"` + the App id, the PEM in the server process env, and
   a chosen listen port) and re-mints installation tokens on demand.

   **Executable standup (adopter-generalized from that reference).**
   HAND-provision the server — do NOT run `fabro install`: its GitHub step
   validates a *static* gh token and REJECTS App installation tokens
   (`ghs_*`), whereas fabro natively supports App auth via
   `[server.integrations.github] strategy = "app"` + `app_id`, minting and
   refreshing its OWN installation tokens from the PEM held in the server
   process environment. The steps below reproduce the fleet entrypoint's
   `provision_fabro` (orchestrator plugin repo,
   `orchestrator-image/orchestrator-entrypoint.sh`), differing only in that
   a PER-TENANT server uses a DEDICATED `FABRO_HOME` and its OWN loopback
   port instead of the fleet default `~/.fabro`:

   - **Choose (human) a dedicated home and a free loopback port.** Set
     `FABRO_HOME=~/.fabro-<tenant>` (the fleet's openbrain reference uses
     `~/.fabro-openbrain`) and pick an unused port `<port>` (openbrain uses
     `32277`). These two are operator choices; everything below is
     scriptable.
   - **Idempotency probe FIRST.** If `<FABRO_HOME>/settings.toml` already
     names the adopter's App id
     (`grep -q 'app_id = "<APP_ID>"' "<FABRO_HOME>/settings.toml"`) AND the
     server answers (`curl -sf -o /dev/null "http://127.0.0.1:<port>/"`),
     the per-tenant server is already standing — record "already present"
     and SKIP the rest of this step.
   - **Generate the control-plane credentials** (the dev token that gates
     the control plane + a session secret), exactly as the entrypoint does:

     ```bash
     dev_token="fabro_dev_$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
     session_secret="$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
     mkdir -p "$FABRO_HOME/storage" "$FABRO_HOME/environments"
     ```
   - **Write the generated server credentials** (both mode `0600`; the dev
     token is a secret — write it, never echo it):

     ```bash
     ( umask 077
       printf 'FABRO_DEV_TOKEN=%s\nSESSION_SECRET=%s\n' "$dev_token" "$session_secret" \
         > "$FABRO_HOME/storage/server.env"
       printf '{"servers":{"http://127.0.0.1:%s":{"kind":"dev-token","token":"%s","logged_in_at":"%s"}}}\n' \
         "<port>" "$dev_token" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
         > "$FABRO_HOME/auth.json" )
     ```
   - **Write `settings.toml` — `app_id` ONLY, NEVER the PEM.** The private
     key lives in the server process env (a later step) and NOWHERE in
     settings on disk:

     ```toml
     _version = 1

     [cli.target]
     type = "http"
     url = "http://127.0.0.1:<port>"

     [server.api]
     url = "http://127.0.0.1:<port>/api/v1"

     [server.auth]
     methods = ["dev-token"]

     [server.integrations.github]
     strategy = "app"
     app_id = "<APP_ID>"

     [server.listen]
     address = "127.0.0.1:<port>"
     type = "tcp"

     [server.web]
     enabled = true
     url = "http://127.0.0.1:<port>"
     ```

     Bind loopback (`127.0.0.1`). The fleet entrypoint binds `0.0.0.0` ONLY
     because it runs inside a container and publishes the port to the host
     loopback; a host-local per-tenant server binds loopback directly —
     this is exactly the openbrain reference's `address = "127.0.0.1:32277"`.
   - **Provide the `livespec-ci` execution environment.** The dispatch
     workflow runs in a fabro execution environment NAMED `livespec-ci`;
     create `<FABRO_HOME>/environments/livespec-ci.toml` defining it (a
     `provider = "docker"` sandbox environment naming the sandbox image +
     resources). This file carries NO secret: the Dispatcher appends the
     per-run `[environments.livespec-ci.env]` secret table to a mode-`600`
     overlay at dispatch time and deletes it post-run. The fleet reference
     targets the published family sandbox image; a non-Python adopter points
     it at its own image (paired with the adapted workflow in Step 6).
   - **Start the server with the PEM in its PROCESS ENV only** (never argv,
     never a settings key), under the chosen `FABRO_HOME`:

     ```bash
     export GITHUB_APP_PRIVATE_KEY="$GITHUB_PRIVATE_KEY"   # PEM: process env ONLY
     FABRO_HOME="$FABRO_HOME" fabro server start --no-upgrade-check
     ```

     Like the fleet reference, the engine LLM credential MAY ride the SAME
     server-process-env channel (the entrypoint's `ANTHROPIC_API_KEY`
     export); the Dispatcher additionally projects the per-run engine
     credential (`CLAUDE_CODE_OAUTH_TOKEN`) into each sandbox itself, so no
     LLM secret is ever written to `settings.toml`.

   **Point the dispatch AT this server — the targeting that fixes the
   `"App is not installed"` failure.** Standing the server up is NOT
   enough: the dispatch's `fabro` CLI must be told to USE it, or it
   defaults to `~/.fabro` — the fleet's shared server, whose App is not
   installed for the adopter — and fails at sandbox-creation with the "App
   is not installed for the `<org>` organization" error. Targeting is by
   `FABRO_HOME`, a NON-secret host path pointing at Step 5's per-tenant
   server home. Because it is non-secret it is **dispatch CONFIGURATION,
   not a credential — it does NOT go in the `credential_wrapper`**, which
   is a pure secret injector (`op run`); putting a plain host path there
   would be a category error. Two forms, one intended and one executable
   today:

   - **Intended holistic mechanism — `.livespec.jsonc`
     `dispatcher.fabro_home`.** Commit the per-tenant home as a dispatcher
     config key, mirroring the existing `dispatcher.fabro_bin`:

     ```jsonc
     {
       "livespec-orchestrator-beads-fabro": {
         "dispatcher": { "fabro_home": "~/.fabro-<tenant>" }
       }
     }
     ```

     The dispatcher is intended to resolve this exactly as it resolves
     `fabro_bin` — env `LIVESPEC_FABRO_HOME` > `.livespec.jsonc`
     `dispatcher.fabro_home` > default `~/.fabro` — and export the result
     as `FABRO_HOME` onto the `fabro` subprocess. **HONESTY: this
     resolution is NOT yet shipped** (a pending slice of orchestrator
     ledger item `bd-ib-z2ctra`); committing the key now records intent
     but has NO effect until that slice lands, so it cannot be the
     mechanism you dispatch with today.
   - **Interim executable form (the stopgap until the key resolves) — a
     manual `FABRO_HOME=` env prefix on the dispatch invocation.** Set it
     as an AMBIENT env var on the command line (NOT inside the wrapper);
     the credential wrapper still injects the secrets and passes the
     ambient `FABRO_HOME` straight through to the `fabro` subprocess:

     ```bash
     FABRO_HOME="$HOME/.fabro-<tenant>" <credential-wrapper> -- python3 \
       "${CLAUDE_PLUGIN_ROOT}/scripts/bin/drive.py" \
       --action impl:<work-item-id> --repo <target-repo>
     ```

     This is the actual openbrain-proven targeting today. The same
     `FABRO_HOME=` ambient prefix rides ANY dispatch entry point,
     including the `dispatcher.py dispatch --workflow …` form in Step 6.

   (Also in-flight under `bd-ib-z2ctra`: a dispatch preflight that verifies
   the TARGETED server's App can reach the target repo BEFORE launching,
   refusing with an actionable diagnostic instead of failing inside the
   engine run.)

6. **Adapt the dispatch workflow to the adopter's toolchain — only if it
   is not the fleet's `uv`/Python toolchain.** The default
   `implement-work-item` workflow's *prepare* steps — the commands that
   provision each fresh sandbox clone before Red→Green runs — are the FLEET
   toolchain's realization, hardcoded to `uv` + `lefthook` + the
   `livespec_dev_tooling` Python package:

   - `git fetch --unshallow --quiet`
   - `mise trust && mise install --quiet`
   - `uv sync --all-groups`
   - `uv run lefthook install`
   - `uv run python -m livespec_dev_tooling.install_commit_refuse_hooks`
   - `git config livespec.sandboxExempt true`
   - `uv run python -m livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed`
   - `uv run python -m livespec_dev_tooling.checks.plugin_resolution`

   On an adopter whose toolchain is NOT `uv`/Python (for example a
   pnpm/TypeScript repo) those `uv …` prepare steps FAIL, aborting the run
   BEFORE any work is driven — the SECOND wall, behind the server-identity
   one in Step 5. Prepare steps are TARGET-TOOLCHAIN facts, not fleet
   constants. The executable fix today: author a TARGET-repo-local workflow
   at `<target-repo>/.fabro/workflows/implement-work-item/workflow.toml`
   carrying the adopter's OWN prepare chain (its dependency install, its
   hook install, its equivalent conformance gates), then pass it to the
   Dispatcher via the existing `--workflow` override — e.g. when the
   Dispatcher is invoked directly:

   ```bash
   <credential-wrapper> -- python3 \
     "${CLAUDE_PLUGIN_ROOT}/scripts/bin/dispatcher.py" dispatch \
     --repo <target-repo> --item <work-item-id> \
     --workflow <target-repo>/.fabro/workflows/implement-work-item/workflow.toml
   ```

   The Dispatcher already honors this: `--workflow <path>` overrides the
   plugin-default workflow (its `_workflow_toml` resolver returns the passed
   path when `--workflow` is set, else the plugin-root default).
   Idempotency: if the target-local `workflow.toml` already exists with the
   adopter's prepare chain, record "already present". (In-flight, orchestrator
   ledger item `bd-ib-z2ctra` deliverable (d): DURABLE auto-resolution — the
   target's `.fabro/workflows/implement-work-item/workflow.toml` taking
   precedence over the plugin payload automatically, plus parameterized
   per-toolchain prepare steps, so no hand-carried `--workflow` flag is
   needed. Until it ships, the `--workflow` recipe above is the executable
   mechanism.) A fleet-`uv` adopter needs neither the override nor this
   step — record it "n/a" and continue.

7. **Idempotent preflight — confirm readiness up front.** Verify the
   GitHub App credential resolves and mints an installation token BEFORE
   the first dispatch, so readiness is known now rather than at
   sandbox-creation time. Run the orchestrator plugin's token-mint CLI
   UNDER the adopter's credential wrapper, discarding stdout (the token
   is a secret) and checking only the exit status — resolve the script
   from the orchestrator plugin root (`${CLAUDE_PLUGIN_ROOT}` on Claude
   Code):

   ```bash
   <credential-wrapper> -- python3 \
     "${CLAUDE_PLUGIN_ROOT}/scripts/bin/mint_app_token.py" >/dev/null
   ```

   Exit 0 confirms the App environment is present and an installation
   token was minted (the App has a resolvable installation); a non-zero
   exit prints an actionable diagnostic on stderr naming the missing or
   empty variable and the wrapper to fix. If the App has more than one
   installation the mint refuses until `GITHUB_APP_INSTALLATION_ID` pins
   the target's installation — set it in the wrapper. Finally confirm the
   installation covers THIS target repo: in the GitHub UI, the App's
   installation settings must list the target org/repo among its
   repository access. (Verifying the SERVING App can reach the target
   automatically at dispatch time is part of the preflight the per-tenant
   server in Step 5 owns.)

**Idempotency report (terminal step for a beads-fabro adopter).** Extend
the Phase-5 report with a factory-infrastructure section — one row each:
GitHub App, dispatch credential set (wrapper), work-items tenant,
per-tenant Fabro server, adapted dispatch workflow (n/a for a fleet-`uv`
adopter), and preflight — marked "already present" / "added" / "updated" /
"n/a" so a re-run that changes nothing proves itself a no-op.
