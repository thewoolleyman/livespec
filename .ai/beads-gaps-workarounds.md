# Beads gaps and workarounds

A living catalogue of hacks and hoops the livespec implementation
layer has accumulated while integrating `bd` (gastownhall/beads).
This file started during the v1.0.3 embedded-Dolt bootstrap; a
2026-06-24 review added current shared-Dolt-server notes for the
fleet's Beads/Dolt + Fabro operating model. Each entry is framed
so it can be filed upstream as a discrete proposal — observation,
current workaround in livespec, proposed change(s) to eliminate the
need.

Maintenance lifecycle (the living-index contract this file
carries): each numbered entry is written so it can be lifted
directly into an upstream GitHub issue. When an upstream beads
change lands that addresses a workaround: (1) update the entry's
**Status / pointers** section with the released bd version and the
issue / PR pointer; (2) remove the workaround from whatever code
carries it, in a paired commit; (3) mark the entry retired (or
delete it) once the workaround removal has shipped. Nothing here
is load-bearing spec content — any finding that matures into
"livespec MUST do X about beads" flows through
`/livespec:propose-change` → `/livespec:revise`.

## Provenance and scope

This document complements (does not replace) the foundational
`beads-problems.md` catalogue vendored from Open Brain at
livespec bootstrap (retired from this repo with the
implementation-gaps subsystem at commit `4916bfa`, 2026-06-24;
recoverable from git history). That file documents Problems 1–8 (Dolt
remote synthesis, embedded-mode `bd doctor`, workspace identity
mismatch, lock files, symlinked CLAUDE.md, 0700 permissions,
lefthook npm postinstall, etc.) with upstream issue / PR
pointers. Most of those workarounds also apply to livespec; we
inherit them via the adapted `setup-beads.sh` and `bd-doctor.sh`.

This document focuses on:

- Issues observed during the livespec bootstrap (2026-05-09)
  that surfaced *additional* friction beyond the OB catalogue.
- Issues already in the OB catalogue but with new evidence /
  framings worth surfacing upstream.
- Design concerns about bd's *defaults* and *prose* that don't
  meet a clean "bug" bar but cost real friction at integration
  time.

Scope: the workarounds documented here are the ones livespec is
actively carrying. If an upstream change lands that obviates a
workaround, the corresponding entry should be retired with a
status update.

## 2026-06-24 status pass

The fleet has moved from the original embedded-Dolt bootstrap
shape to per-repo shared Dolt sql-server tenants consumed through
the Beads/Dolt + Fabro orchestrator. Beads itself has also changed
substantially since the v1.0.3-era observations in this document.

Treat the entries below in three buckets:

- **Still relevant to current operations:** Entry 11 is current:
  tenant `bd` commands can still emit a `backup_export` warning in
  a topology where backups are deliberately externalized to a
  dedicated `backup` SQL user. Entry 10 remains conceptually
  relevant because `.beads/config.yaml` now carries shared-server
  tenant connection keys that are intentionally committed as
  fleet bootstrap pointers, while `.beads/metadata.json` remains
  regenerable and gitignored.
- **Historically useful but likely stale for current livespec
  operations:** Entries 1, 2, 4, 5, 6, 7, 8, and the inherited
  embedded-mode Open Brain entries describe the original embedded
  bootstrap scripts (`setup-beads.sh`, `bd-doctor.sh`,
  `.beads/embeddeddolt/`, generated hook templates). Those scripts
  are no longer present in this repo, and current fleet members use
  host-provisioned `bd` plus shared Dolt sql-server tenants. Keep
  these entries as upstream-history references until each issue is
  rechecked against the current Beads release, then retire or
  rewrite them.
- **Still relevant as upstream product/prose concerns, but not
  current blockers:** Entries 3 and 9 about injected agent prose
  and `bd prime` over-claiming task ownership remain plausible
  upstream concerns. They are not load-bearing for current livespec
  operation because the family relies on committed AGENTS.md /
  CLAUDE.md guidance and orchestrator plugin skills instead of
  accepting generic Beads agent prose as authoritative.

Operationally, the current family rule is: a Beads-backed member
needs the `bd` CLI, a reachable Dolt sql-server, a bare
`BEADS_DOLT_PASSWORD` injected by the correct wrapper, and committed
`.beads/config.yaml` pointer values. Tenant users are isolated by
SQL user and database grants. Host-level backup is handled outside
tenant `bd` commands by a dedicated backup user and service.

## Methodology — entry format

Each entry has four parts:

- **Observation** — the concrete behavior we hit, verbatim error
  text where useful.
- **Current workaround** — what livespec does to compensate (file
  paths, function names, config keys).
- **Proposed upstream change** — one or more discrete asks that
  would eliminate the workaround. Phrased as a feature request
  or behavior change, not as a complaint.
- **Status / pointers** — links to existing upstream issues if
  filed; "not yet filed" otherwise. Cross-references to the OB
  catalogue where applicable.

---

## Entry 1 — `bd init` auto-commits regardless of `--skip-*` flags

### Observation

`bd init --non-interactive --skip-agents --skip-hooks --prefix li`
*still* auto-commits to git on completion ("✓ Committed beads
files to git"). The commit lands on whatever branch is currently
checked out, with the subject `bd init: initialize beads issue
tracking`. There is no `--no-commit` or `--dry-run` flag to
suppress this.

For livespec, this is hostile because:

- The commit fires *during* `bd init` while `bd` itself has just
  flipped `core.hooksPath` to `.beads/hooks/`. With `--skip-hooks`
  the new hooks directory is empty, so the commit-msg hook chain
  livespec relies on (`00-no-commit-on-master`,
  `check-conventional-commits`, `check-red-green-replay`) does
  not fire. The commit lands on master regardless of the
  contributor's intent.
- The commit subject (`bd init: ...`) is not Conventional Commits
  compliant. `bd init` is not a recognized type. Livespec's v056
  Conventional Commits mandate would reject this commit if the
  gate fired — but the gate didn't fire (see point 1).
- We had to reset (`git reset --hard HEAD~1`) and replay the
  commit on a feature branch with a corrected `chore(beads):`
  subject. Multiple times, while iterating on the right
  `--skip-*` combination.

### Current workaround

`dev-tooling/implementation/setup-beads.sh` — invokes
`bd init --non-interactive --skip-agents --skip-hooks --prefix li`
and *expects* the auto-commit to land. The script header
documents that a fresh-clone bootstrap MUST be run from a feature
branch (not master) so the auto-commit lands on the branch where
direct commits are allowed; the contributor then amends the
subject to a Conventional-Commits-compliant `chore(beads): ...`
before pushing.

### Proposed upstream change

Add a `--no-commit` (or `--dry-run`) flag to `bd init` that
suppresses the auto-commit entirely, leaving the staged changes
in the index so the user / setup script can craft the commit
themselves.

Rationale: most non-trivial repos have commit conventions
(Conventional Commits, branch protection, lefthook gates, etc.)
that an auto-commit cannot satisfy without the user's
involvement. The auto-commit is a sensible default for a fresh
solo project; it is hostile to any repo that has *already*
adopted commit conventions before adding bd.

Secondary ask: if the auto-commit cannot be made optional, change
its default subject to `chore(beads): initialize beads tracking
infrastructure` (or similar) so it satisfies Conventional Commits
out of the box.

### Status / pointers

Not yet filed upstream. Observed concretely in livespec bootstrap
2026-05-09: commit `1cb5ba0` and `a1f4b64` were both auto-commits
that had to be reset and re-played.

---

## Entry 2 — `--skip-agents` does not fully isolate

### Observation

`bd init --skip-agents` documentation describes it as "Skip
AGENTS.md and Claude settings generation". In practice, the flag
suppresses:

- AGENTS.md modification / creation
- CLAUDE.md modification (BEADS INTEGRATION block)
- `.claude/settings.json` modification

But it does **not** suppress:

- `.gitignore` modification (bd appends `.dolt/` and `*.db`
  patterns at the end of the user's existing file)
- The auto-commit (Entry 1)

So `--skip-agents` is a partial isolation flag: it skips *some*
intrusive mutations but not all of them.

### Current workaround

We accept the `.gitignore` appendage as benign. Our top-level
`.gitignore` has its own beads section above bd's appendage; both
coexist.

### Proposed upstream change

Make `--skip-agents` a complete isolation flag: skip ALL writes
to files outside `.beads/` (CLAUDE.md, AGENTS.md, settings.json,
.gitignore, etc.). If the user wants those mutations, they pass
explicit opt-in flags (`--inject-agents-md`, `--inject-gitignore`,
etc.) or invoke the inject step separately.

Rationale: agents and integration scripts that already manage
those files for the host project need a clean isolation boundary.

### Status / pointers

Not yet filed upstream.

---

## Entry 3 — `bd init`'s default agent-files content prohibits common workflows

### Observation

Without `--skip-agents`, `bd init` injects content into CLAUDE.md
and AGENTS.md asserting:

- *"Default: Use beads for ALL task tracking (`bd create`,
  `bd ready`, `bd close`)"*
- *"Prohibited: Do NOT use TodoWrite, TaskCreate, or markdown
  files for task tracking"*
- *"Memory: Use `bd remember` for persistent knowledge across
  sessions. Do NOT use MEMORY.md files — they fragment across
  accounts."*

These directives are universal in framing but the underlying
capabilities (bd issues, bd remember) are scoped to bd
specifically. Projects that already use TodoWrite / TaskCreate
for in-session task tracking and per-project memory systems for
cross-session agent context get told (by their own CLAUDE.md
post-bd-init) to stop using those tools entirely.

In livespec specifically, the existing workflow uses:

- TaskCreate for in-session task lists (separate concern from
  bd's gap-tied issue tracking).
- A per-project auto-memory tree (`~/.claude/projects/.../memory/`)
  for cross-session agent context.

The bd-injected CLAUDE.md content directly conflicts with both.
Same `bd prime` output (loaded on SessionStart) repeats the
prohibitions.

### Current workaround

Always pass `--skip-agents` to `bd init` (codified in
`setup-beads.sh`). Do not wire `bd prime` (or wire it with
explicit framing in the surrounding skill prose that scopes bd's
guidance to gap-tied work only).

For the BEADS INTEGRATION CLAUDE.md/AGENTS.md content
specifically: livespec's own `.claude/plugins/livespec-implementation/skills/{plan,implement}/SKILL.md`
encode bd guidance with correct scoping (bd is for
implementation-gap tracking, not all task tracking). The
contextual loading via slash command beats baked-in CLAUDE.md
prose.

### Proposed upstream change

Reframe bd's injected agent-files content from prohibitive
("Do NOT use TodoWrite/TaskCreate/MEMORY.md") to additive
("Use bd for issue tracking. Other task-tracking and memory
systems may coexist; bd is one tool among several"). Universal
prohibitions over-claim scope and create real conflict at
integration time.

Same change applies to `bd prime` runtime output.

### Status / pointers

Not yet filed upstream. This is a framing / docs change rather
than a bug; would land via PR against bd's templates and
`bd prime` source.

---

## Entry 4 — `bd bootstrap` fails on truly-fresh state despite documented behavior

### Observation

`bd bootstrap --help` says:

> Bootstrap auto-detects the right action:
>   • If sync.remote is configured: clones from the remote
>   • If git origin has Dolt data (refs/dolt/data): clones from git
>   • If .beads/backup/*.jsonl exists: restores from backup
>   • If .beads/issues.jsonl exists: imports from git-tracked JSONL
>   • **If no database exists: creates a fresh one**
>   • If database already exists: validates and reports status

Empirically, on a fresh clone with NONE of those sources present,
`bd bootstrap --yes` fails with:

```
No active beads workspace found.
Hint: run 'bd where' to inspect the resolved workspace, or
'bd init' to create a new database
Bootstrap is for existing projects that need database setup.
```

The "creates a fresh one" branch documented in help does not
fire; bootstrap requires at least one hydration source to
proceed.

### Current workaround

`dev-tooling/implementation/setup-beads.sh` probes for any
hydration source (refs/dolt/data on origin, `.beads/issues.jsonl`,
`.beads/backup/*.jsonl`) and falls back to `bd init
--non-interactive --skip-agents --skip-hooks --prefix li` if none
exist. Every subsequent run hits the bootstrap path normally.

### Proposed upstream change

Make `bd bootstrap` actually match its documentation: when no
source exists, create a fresh embedded database instead of
erroring. (Or update the docs to match the behavior — but the
behavior is the better fix because callers don't need to
condition on "fresh vs hydrate" anymore.)

### Status / pointers

Not yet filed upstream. Reproduces deterministically on a fresh
clone with no `.beads/` directory or `refs/dolt/data` ref.

---

## Entry 5 — `bd hooks run <unsupported-hook>` errors instead of no-op

### Observation

`bd hooks run commit-msg <args>` returns:

```
Error: unknown hook: commit-msg
exit=1
```

bd's hooks-runner recognizes `pre-commit`, `pre-push`,
`prepare-commit-msg`, `post-merge`, `post-checkout`. It does NOT
recognize `commit-msg` (or any hook outside that fixed set).

For projects that need to run a `commit-msg` lefthook chain
(livespec runs three: `00-no-commit-on-master`,
`01-check-conventional-commits`, `02-check-red-green-replay`)
through the `.beads/hooks/` directory bd manages via
`core.hooksPath`, the bd-recognized error breaks the chain. Our
managed hook templates dispatch lefthook FIRST, then bd, then
re-honor lefthook's exit code; the bd dispatch fails with exit 1
on commit-msg, which propagates as a commit failure.

### Current workaround

`dev-tooling/implementation/setup-beads.sh`'s `write_managed_hook`
function checks the hook name against a hardcoded list of
bd-supported hooks. For hooks bd recognizes (pre-commit,
pre-push, prepare-commit-msg, post-merge, post-checkout), the
template includes the bd integration block. For hooks bd does
NOT recognize (commit-msg), the template includes only the
lefthook chain + exit fix; the bd block is omitted entirely.

This is brittle: if bd adds support for a new hook in a future
version, our hardcoded list goes stale silently.

### Proposed upstream change

`bd hooks run <hook>` should exit 0 silently on hooks it does
not process, rather than exit 1 with "unknown hook". The current
behavior conflates "bd doesn't process this hook" (a benign
pass-through) with "the user invoked something invalid"
(actually erroneous).

Alternatively: provide `bd hooks supported` (or
`bd hooks list-supported --json`) so callers can ask bd which
hooks it processes and conditionally include the dispatch block
at hook-template-write time without hardcoding.

### Status / pointers

Not yet filed upstream.

---

## Entry 6 — `bd init`'s auto-commit subject is not Conventional Commits compliant

### Observation

`bd init`'s auto-commit (Entry 1) uses the subject `bd init:
initialize beads issue tracking`. The form `<word> <word>:` is
not a valid Conventional Commits type — the type-list is
`feat | fix | chore | docs | refactor | test | build | ci |
perf | style | revert` plus optional scope.

This means projects that gate commit-msg with
`check-conventional-commits` reject bd's auto-commit even when
their other gates fire correctly.

### Current workaround

We can't run the auto-commit through our gates (Entry 1
covers why); we replay the commit ourselves with a corrected
`chore(beads): initialize beads tracking infrastructure` subject.

### Proposed upstream change

Change bd's default auto-commit subject to follow Conventional
Commits: `chore(beads): initialize beads tracking infrastructure`
(or similar). Repos that don't enforce Conventional Commits are
unaffected; repos that do can keep their gates.

This also makes the change discoverable in CI / changelog
tooling that consumes Conventional Commits subjects (e.g.,
release-please).

### Status / pointers

Not yet filed upstream. Trivial PR (single string change in
bd's init source).

---

## Entry 7 — `bd init --skip-hooks` leaves `.beads/hooks/` uncreated

### Observation

`bd init --skip-hooks` skips bd's own hook template writing. It
ALSO skips creating `.beads/hooks/` as a directory. The
post-init state is:

- `.beads/embeddeddolt/` exists (the database)
- `.beads/.gitignore`, `metadata.json`, `config.yaml` exist
- `.beads/hooks/` does NOT exist

Callers who pass `--skip-hooks` because they want to write their
own templates must `mkdir -p .beads/hooks` themselves before
writing. Otherwise their template-write step fails with "no such
file or directory."

### Current workaround

`setup-beads.sh` runs `mkdir -p .beads/hooks` immediately after
`bd init --skip-hooks` returns. The script's `write_managed_hook`
loop then writes our chained templates into the directory.

### Proposed upstream change

`bd init --skip-hooks` should still create the empty
`.beads/hooks/` directory and set `core.hooksPath = .beads/hooks/`
— it should only skip the template writing.

Rationale: the directory + hooksPath are infrastructure;
templates are content. The flag's name suggests skipping the
content; users still want the infrastructure.

### Status / pointers

Not yet filed upstream.

---

## Entry 8 — `bd init` does not detect protected branches before auto-committing

### Observation

`bd init` checks neither `git config branch.<branch>.protected`
nor any common branch-protection convention (`master` / `main`
heuristic) before auto-committing. On a freshly-cloned repo
where the contributor accidentally ran `bd init` from `master`,
the commit lands on master regardless of intent.

Combined with Entry 1 (commit bypasses the user's commit-msg
hooks because `core.hooksPath` is mid-flip), this creates a
real protected-branch escape hatch that the user can't easily
prevent.

### Current workaround

Documentation in `setup-beads.sh` and the bootstrap plan: cut a
feature branch BEFORE invoking `setup-beads`. The script does
not enforce this; the user has to know.

### Proposed upstream change

Either:

1. `bd init` refuses to auto-commit when on a branch named
   `master` / `main` / `trunk` / `develop` (or a configurable
   blocklist), unless the user passes an explicit
   `--commit-on-protected` flag.
2. `bd init` always commits — but to a per-bd ref (e.g.,
   `refs/bd/init`) that doesn't pollute the user's working
   branch. The user merges / rebases / cherry-picks at their
   discretion.
3. The simpler fix from Entry 1: `--no-commit` flag, leave it
   to the user.

(3) is the cleanest answer to multiple entries here. (1) is the
most user-protective default.

### Status / pointers

Not yet filed upstream.

---

## Entry 9 — `bd prime` SessionStart output overrides project workflows

### Observation

When `bd prime` is wired as a Claude Code SessionStart hook (per
livespec's NFR-recommended SHOULD), its output enters the
agent's context every session start. The output asserts (verbatim):

- *"Default: Use beads for ALL task tracking..."*
- *"Prohibited: Do NOT use TodoWrite, TaskCreate, or markdown
  files for task tracking"*
- *"Memory: Use `bd remember` for persistent knowledge across
  sessions. Do NOT use MEMORY.md files."*

For livespec, where `TaskCreate` handles in-session task lists
and per-project memory handles cross-session agent context, the
prohibitions are wrong. They apply bd's scope claims to tools
that bd doesn't own.

### Current workaround

In livespec, the implementation skills' SKILL.md files
(refresh-gaps, plan, implement) carry the bd guidance scoped to
implementation-layer work. `bd prime` is wired but the
out-of-scope directives in its output are surfaced to users
during onboarding so they can decide whether to keep the hook
wired or replace it with a project-specific priming command.

### Proposed upstream change

Reframe `bd prime`'s output to describe bd's *capabilities*
without prohibiting other tools. Concretely:

- Replace *"Use beads for ALL task tracking"* with *"bd is
  beads' task tracker for issues you want versioned and
  cross-clone-synced. Use it alongside whatever task / memory
  tooling your environment provides."*
- Drop the *"Prohibited"* / *"Do NOT use"* clauses.

bd's `bd remember` is genuinely useful; users can decide whether
to use it alongside or instead of an existing memory system.
Don't decide for them.

### Status / pointers

Not yet filed upstream. This is a docs/wording change; would
land via PR against `bd prime`'s template source.

---

## Entry 10 — `.beads/config.yaml` git-tracking convention

### Observation

bd's nested `.beads/.gitignore` (auto-generated) lists what to
ignore (embeddeddolt/, dolt/, lockfiles, etc.) and explicitly
notes *"Config files (metadata.json, config.yaml) are tracked
by git by default since no pattern above ignores them."*

But `.beads/config.yaml` contains the per-clone dolt remote URL
(HTTPS on Linux/VPS, SSH on macOS). Tracking it causes per-host
diff thrash whenever a contributor on a different protocol
fetches and pushes.

Open Brain documents this and adds `.beads/config.yaml` to its
top-level `.gitignore` to override bd's default. Livespec is
currently following bd's default (config.yaml is tracked); this
is gap-0006 in `implementation-gaps/current.json` for
investigation later.

### Current workaround

None yet in livespec; gap tracked. Open Brain's pattern
(`.beads/config.yaml` in top-level `.gitignore`, plus
`setup-beads.sh` re-asserting required values on every run) is
the likely fix.

### Proposed upstream change

bd should EITHER:

1. Move host-specific values out of `config.yaml` (specifically
   the dolt remote URL) into a separate `.beads/local.yaml` (or
   similar) that's gitignored by default, leaving `config.yaml`
   safe to track.
2. Add `config.yaml` to `.beads/.gitignore` by default and rely
   on `setup-beads.sh`-style re-assertion on each clone.

Option 1 is the cleaner answer because it preserves the ability
to track shared config (e.g., `dolt.auto-commit`, `export.auto`)
while excluding host-specific bits.

### Status / pointers

Not yet filed upstream. Open Brain's `setup-beads.sh` and its
`beads-problems.md` research catalogue capture the workaround and
rationale.

---

## Entry 11 — Tenant CLI auto-backup warning in externally managed backup topology

### Observation

In the current livespec fleet topology, Beads tenants connect to a
shared Dolt sql-server over TCP with a per-repo tenant SQL user.
That tenant user has the database privileges needed for normal
`bd` operation, but it intentionally does NOT have the privileges
needed to register or sync Dolt backups. Backups are externally
managed by the host-level `dolt-backup.timer` service using a
dedicated `backup` SQL user.

Despite that separation, tenant-side `bd` commands can emit:

```text
Warning: auto-backup failed: register backup remote: add backup backup_export: Error 1105 (HY000): command denied to user 'livespec-console-beads-fabro'@'%'
```

Observed on 2026-06-24 with `bd version 1.0.5 (6a3f515ce)`,
`dolt.mode=server`, `dolt.server-host=127.0.0.1`,
`dolt.server-port=3307`, tenant user
`livespec-console-beads-fabro`, and `backup.enabled=false`
reported as the default by `bd config show`.

The important distinction: `backup.enabled=false` does NOT mean
"this project is not backed up." In this topology it means "the
tenant `bd` CLI should not perform Beads' automatic backup /
`backup_export` registration work." The project is still backed up
through externally managed Dolt-server backup infrastructure.

### Current workaround

Treat this as a benign tenant-permission warning, not as a failed
project backup. Do not grant tenant users broader Dolt backup
privileges merely to suppress the warning. The family backup path
is the host-level backup service as the dedicated `backup` user.

When checking tenant health, prefer ordinary `bd` operations such
as `bd list --json` under the configured environment wrapper, and
verify backup service health separately from the tenant CLI path.

### Proposed upstream change

One of:

1. Honor `backup.enabled=false` before attempting
   `backup_export` registration in all paths, including
   status/config-related commands.
2. Add an explicit escape hatch such as
   `backup.auto-register=false` or `backup.mode=external` that
   suppresses tenant-side `backup_export` registration and
   warnings while leaving out-of-band backups intact.

Rationale: shared-server deployments commonly separate tenant
application privileges from backup privileges. A tenant command
warning that the tenant cannot register a backup remote is noisy
when the backup role is intentionally external.

### Status / pointers

Commented upstream on
[gastownhall/beads#3501](https://github.com/gastownhall/beads/issues/3501#issuecomment-4787562082)
with the current shared-server / dedicated-backup-user repro.
Related upstream issues:
[gastownhall/beads#3522](https://github.com/gastownhall/beads/issues/3522),
[gastownhall/beads#3594](https://github.com/gastownhall/beads/issues/3594),
and
[gastownhall/beads#3878](https://github.com/gastownhall/beads/issues/3878).

---

## Entry 12 — `bd create` cannot create directly in a custom status (forces `open`/`deferred`)

### Observation

`bd create` hard-codes the initial status: in `buildCreateIssue`
(`cmd/bd/create.go`, upstream/main @ `9626f4f1a`, unchanged through
`v1.1.0-rc.1`) `status := types.StatusOpen`, with `StatusDeferred` the
only alternative (when `--defer` has a future date). The create command
registers ~35 flags but **no `--status`** (`-s`/`--status` exists only on
`list`/`count`/`search`/`lint`/`update`). So although beads supports
custom statuses (`bd config set status.custom`), a new issue can only be
born `open` (or `deferred`); reaching any custom status needs a **second**
`bd update --status <x>`.

### Current workaround

The two-step create→update. livespec's store adapter `append_work_item`
(beads-fabro `store.py`) runs `bd create` (lands `open`) then
`bd update --status <target>` in immediate succession; ad-hoc
sessions/scripts do the same with raw `bd create` + `bd update --status
backlog`. Between the two calls the item is transiently non-conforming
(`open`), which the status-conformance doctor gate (bd-ib-2wq /
beads-fabro PR #231) now flags — so a factory dispatch racing an item
creation can transiently fail the pre-dispatch gate. Mitigation: prefer
`append_work_item` (two back-to-back calls) over a raw `bd create` left
un-updated, to keep the window minimal.

### Proposed upstream change

Add a `--status <status>` flag to `bd create`. When set, validate it
against built-in + configured custom statuses by reusing exactly what
`bd update` already does — `types.Status(s).IsValidWithCustom(
store.GetCustomStatuses(ctx))` (`cmd/bd/update.go:63-76`) — and set that
as the initial status in `buildCreateIssue` instead of the hard-coded
`types.StatusOpen` (`cmd/bd/create.go:741`). Default stays `open`;
`--defer` behavior preserved (define precedence: explicit `--status`
wins, or error if `--status` + `--defer` conflict). Frame it as
*completing* the custom-status feature — an item should be creatable
directly in a configured lifecycle state — mirroring the
`claim.from-statuses` generalization that made custom `active` statuses
claimable; NOT as a new status concept (the maintainer is deliberately
minimalist here — see pointers).

### Status / pointers

Confirmed not possible in the latest beads (source-verified 2026-07-01)
and **not requested upstream** — an exhaustive search of
`gastownhall/beads` issues/PRs/discussions (and the `thewoolleyman` fork)
found no `bd create --status` ask; the only create-time status override
ever added is `--defer` → `deferred`
([#4071](https://github.com/gastownhall/beads/issues/4071) → merged
[PR #4112](https://github.com/gastownhall/beads/pull/4112)). It is
intentional design (maintainer Steve Yegge's fixed-schema stance;
[#344](https://github.com/gastownhall/beads/issues/344) /
[discussion #345](https://github.com/gastownhall/beads/discussions/345) —
he prefers labels, which *can* be set at create). The precedent for
generalizing past the `open` baseline is the claim side:
[#4164](https://github.com/gastownhall/beads/issues/4164) (open) /
[PR #4334](https://github.com/gastownhall/beads/pull/4334) (open) make
custom `active`-category statuses claimable. **PR to be driven from the
beads repo** — clone at `/data/projects/beads` on branch
`feat/create-status-flag` (off `upstream/main`); handoff prompt at
`tmp/beads-create-status-pr/handoff.md` (gitignored). Upstream PR:
[gastownhall/beads#4536](https://github.com/gastownhall/beads/pull/4536).

---

## Entries inherited from the Open Brain catalogue

The following are documented in
`dev-tooling/implementation/research/beads-problems.md` (vendored
from Open Brain). Livespec inherits the workarounds via the
adapted `setup-beads.sh` and `bd-doctor.sh`. Pointers for
upstream:

- **OB Problem 1 — `bd init` doesn't synthesize Dolt remote
  pointing at git origin.** Upstream issue:
  [gastownhall/beads#3688](https://github.com/gastownhall/beads/issues/3688)
  (OPEN). Workaround: `setup-beads.sh` re-asserts `bd dolt remote
  add origin <url>` after every bootstrap.
- **OB Problem 2 — `bd doctor` not supported in embedded mode.**
  Upstream:
  [gastownhall/beads#3597](https://github.com/gastownhall/beads/issues/3597)
  (OPEN). Workaround: `dev-tooling/implementation/bd-doctor.sh`
  composes the equivalent diagnostic from primitives that DO
  work in embedded mode.
- **OB Problem 4 — `bd bootstrap` doesn't wire remote on fresh
  embedded init.** Upstream:
  [gastownhall/beads#3419](https://github.com/gastownhall/beads/issues/3419)
  (OPEN). Workaround: same as Problem 1.
- **OB Problem 6 — bd recommends 0700 on `.beads/`; git can't
  track directory perms; bd warns on every command.** Upstream:
  GH#3391 (closed) → GH#3483 (PR merged 2026-04-28, awaiting
  release past v1.0.3). Workaround: `chmod 700 .beads`
  re-asserted in `setup-beads.sh` and in every managed hook
  template.
- **OB Problem 7 — workspace identity mismatch when
  `.beads/metadata.json`'s `project_id` changes after a clone
  bootstrapped.** Upstream issue not directly cited; workaround
  in `setup-beads.sh` probes via `bd config get dolt.auto-commit`
  (which reliably surfaces the mismatch on stderr), backs up the
  stale store with a timestamped suffix, and re-bootstraps from
  origin.
- **OB Problem 8 — lefthook npm postinstall clobbers
  `core.hooksPath`.** Workaround: pin lefthook via mise, NEVER
  install via npm. Codified in livespec NFR §Contracts
  §"Lefthook installation source" and reinforced in
  `dev-tooling/implementation/bd-doctor.sh` Check 9.
- **GH#3701 — `bd prime` hangs indefinitely on stale embedded-dolt
  lock.** Workaround: `setup-beads.sh` uses `lsof` to detect dead
  lock-holders and removes the stale `.beads/embeddeddolt/.lock`
  before invoking bd.
- **GH#3722 — `bd init/bootstrap` corrupts a symlinked CLAUDE.md
  by reading the symlink target string instead of the file
  contents.** Workaround: `setup-beads.sh` saves the symlink
  target before bootstrap and restores if corrupted.

---

## Entry 13 — `.beads/interactions.jsonl` records only `status` value changes, silently omitting reason/label/metadata edits

### Observation

The interactions log is not a complete change trail. It appears to
emit a `field_change` entry only when an issue's `status` VALUE
transitions; an edit that changes `close_reason`, labels, or
metadata while leaving `status` unchanged produces NO entry at all,
with no warning.

Observed 2026-07-19/20 in the `livespec` tenant. `livespec-bg47fr`
was closed at `2026-07-19T23:04:14Z` with a `close_reason` naming
only one of its three replacement slices. A correction re-ran
`bd close livespec-bg47fr --reason-file <file>` to name all three.
The correction succeeded — `bd show --json` afterward reports:

```
"status":     "closed"
"created_at": "2026-07-19T18:13:35Z"   <- unchanged (correct)
"updated_at": "2026-07-19T23:41:31Z"   <- moved forward (correct)
"closed_at":  "2026-07-19T23:41:31Z"   <- moved forward (correct)
```

…but `.beads/interactions.jsonl` shows NO entry for the correction.
Grepping the full log for the issue id returns four entries, the
newest still the ORIGINAL close at `23:04:14Z` carrying the OLD,
now-superseded single-id reason. Status went `closed → closed`
(unchanged), so nothing was logged, even though the reason text —
the very field that carries the disposition — was rewritten.

The gap is easy to miss precisely because the log looks healthy: it
is well-formed, contains entries for that issue, and simply stops
short. A reader auditing "what replaced this item" from the log
alone reads the superseded reason and gets the wrong answer, with
no signal that a later correction exists.

### Current workaround

Do not treat `.beads/interactions.jsonl` as authoritative for
anything other than status transitions. To establish what an issue
actually says now, read `bd show <id>` / `bd show <id> --json`
directly; to detect that a non-status edit happened at all, compare
`updated_at` against the newest interactions entry for that issue —
a forward gap means at least one unlogged edit.

When a correction MUST be auditable, record it in a field the log
cannot lose: livespec writes the correction inline in the edited
text itself (the `livespec-bg47fr` reason carries a dated
`CORRECTION …` paragraph explaining what changed and why), so the
record is self-describing even though the interaction is absent.

### Proposed upstream change

Emit a `field_change` interaction for every mutated field, not only
`status` — minimally `close_reason`, labels, and metadata, each
carrying old and new values like the existing status entries do.
Failing that, emit a single generic `issue_updated` interaction
naming which fields changed, so the log at least signals that
something happened and points a reader at `bd show` for detail.

Either shape restores the property callers reasonably assume: that
an issue's history in the log is complete enough to explain its
current state.

### Status / pointers

Not yet filed upstream. Found by an independent adversarial review
of a cross-repo grooming pass; the underlying reason-field defect it
was correcting is tracked separately as `bd-ib-dvmh` in the
`livespec-orchestrator-beads-fabro` tenant (groom records only LOCAL
slices in a regroomed-out reason, so cross-tenant replacements are
omitted). Note the two compound badly: the groom defect writes an
incomplete disposition, and this logging gap then hides the
correction of it.

---

## Entries to consider but not yet itemized

Lower-priority ergonomic concerns we noticed but haven't itemized
above:

- **Issue id format.** bd assigns alphanumeric hashes (e.g.
  `li-0d0`, `li-bxm`, `li-37p`) rather than sequential integers.
  Some workflows assume sequential ids for ordering / grouping;
  the hash format is fine for collision-resistance but harder to
  scan visually. Worth a `bd init --id-format sequential` flag
  if upstream agrees.
- **Prefix collision risk.** Short prefixes (livespec uses `li`)
  risk collision when multiple beads-using projects share a
  contributor's machine. Worth a registry / longer-default
  prefix, or an option to use the project's directory name.
- **CLI flag inconsistency.** `bd list --label X` (single dash
  flag, named) vs. `bd dep add <id> --type blocks <other-id>`
  (positional + flag). Minor consistency cleanup.
- **`bd init --help` flag truncation.** The flag list is long
  enough that `head -30` truncates `-p, --prefix`. Not a bug,
  but the flag is one of the more important ones; consider
  surfacing it in the synopsis line.
- **`bd list` SILENTLY truncates at 50 rows — always pass `-n 0`.**
  This one is not cosmetic like the `--help` entry above: the
  default limit applies to `--json` too, and nothing in the output
  says the result set was cut. An agent that reads `bd list --json`
  and counts what it got will under-report the ledger and can
  conclude an item does not exist when it does. Every read must be
  `bd list --json -n 0`. Recorded 2026-07-19 after a console-tenant
  session hit it; worth raising upstream as "warn or exit non-zero
  when a limit elides rows in `--json` mode", since silent
  truncation of a machine-readable format is a correctness trap
  rather than a display nicety.

These can graduate to numbered entries above if they accumulate
enough friction to warrant filing.

---

## How to use this document

When filing an upstream issue against gastownhall/beads:

1. Pick a numbered entry above; copy its **Observation**,
   **Current workaround**, and **Proposed upstream change**
   sections into the issue body.
2. Update the entry's **Status / pointers** section with the
   upstream issue URL once filed.
3. When upstream lands a fix, retire the corresponding entry
   from this document with a brief status note ("retired
   YYYY-MM-DD: addressed by gastownhall/beads#NNNN released in
   bd vX.Y.Z").
4. If the workaround in `setup-beads.sh` or `bd-doctor.sh` can
   be removed, do so in a paired commit.

When adding a new entry:

1. Add it under "Entries to consider but not yet itemized"
   first (a paragraph). When friction warrants, promote to a
   numbered entry with full structure.
2. Reference the OB catalogue if the issue is already documented
   there — don't duplicate prose; link instead.
