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
clean `/livespec:doctor` run for a project that already has one.
Follow the phases in order. Do not skip the survey.

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
  declares in `.livespec.jsonc` (`credential_wrapper`). Choose this
  when multiple agents or an unattended loop will write the ledger
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
that clones, CI, and sandboxes resolve the same plugins), then tell
the user to restart the session or run `/reload-plugins`.

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

## Phase 4 — Do NOT hand-author `.livespec.jsonc`

If the survey found no `.livespec.jsonc`: leave it absent. The seed
operation is the ONLY livespec operation designed to run before
`.livespec.jsonc` exists, and its CLI **writes** `.livespec.jsonc`
itself — atomically, together with the spec tree — during
`/livespec:seed`. Hand-authoring the config first either duplicates
what seed would write or makes seed refuse (it refuses when
template-declared target files already exist).

If the survey found an existing `.livespec.jsonc` (already-governed
project): leave its contents alone, with one exception — if an
orchestrator was chosen in Phase 2 and the file has no section for
it, tell the user the orchestrator's section (its `format`, `compat`
pin — a concrete release tag, not a branch name — and its
store-specific keys) is added per that orchestrator plugin's own
documentation, and offer to do it.

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
     an unattended step.
   - **Already governed**: run `/livespec:doctor` and surface its
     findings. Do not seed.
3. **If beads-fabro was chosen**, note (do not execute) the post-seed
   infrastructure that remains before implementation work-items can
   flow, per the orchestrator plugin's own documentation: the `bd`
   CLI, the Dolt server, the per-tenant SQL user/database, the
   project's `credential_wrapper` injecting the bare
   `BEADS_DOLT_PASSWORD`, and the `.beads/` pointer files. None of it
   blocks seeding.
4. **Print the idempotency report**: every component this prompt
   touched or verified, marked "already present", "added", or
   "updated" — so a re-run that changes nothing proves itself as a
   no-op.
