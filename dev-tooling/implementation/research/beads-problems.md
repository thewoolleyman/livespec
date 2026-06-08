# Beads upstream problems we've hit

> **Provenance.** Vendored from the Open Brain repository's
> `research/beads-problems.md` per
> `SPECIFICATION/non-functional-requirements.md` §Constraints
> §"Beads invariants" #5 ("Open Brain's `research/beads-problems.md`
> is the canonical reference for known beads upstream issues that
> the setup-beads script's recovery paths address"). Most prose,
> file references (`scripts/...`), incident narrative, and beads
> issue ids (`ob-*`, e.g. `ob-068`, `ob-5i4`, `ob-a1y`, `ob-d29`,
> `ob-ir5`) are Open Brain artifacts preserved as-is for upstream-issue
> citation continuity. Livespec's own beads issues use the `li-`
> prefix (NFR §Constraints §"Beads invariants" #1) and live in
> `.beads/issues.jsonl` once the gap-tracked work begins. The
> upstream `bd` problem catalogue (Problems 1–8) is the load-bearing
> portion of this document; the surrounding incident narrative is
> kept verbatim because the workaround commits, file pointers, and
> upstream-comment URLs cite each other in ways that would lose
> meaning if rewritten.

Living index of problems with the `bd` (beads) tool we've encountered while
running it on this project. For each: the upstream issue / PR (if any),
our own comment evidence (if posted), the workaround in this codebase
(with file pointers and commit SHAs), and a **Status** that we update as
the upstream side moves.

This file is the source of truth for "what bd workarounds are we still
carrying, and why?" — it lets us drop workarounds quickly when an
upstream fix lands.

Conventions:

- Each problem gets its own H2 section.
- The **Upstream** subsection links to the issue / PR / comment.
- The **Our experience** subsection captures the failure mode we hit.
- The **Workaround** subsection points at the file + commit that mitigates.
- The **Status** subsection is the one that gets updated as the situation
  evolves — date-stamped entries, newest first.

---

## Problem 1 — `bd init` doesn't synthesize a Dolt remote pointing at git origin

### Upstream

- Issue: [gastownhall/beads#3688](https://github.com/gastownhall/beads/issues/3688) — `feat(init): synthesize Dolt remote pointing at git origin (refs/dolt/data) instead of DoltHub` (OPEN)
- Our comment: <https://github.com/gastownhall/beads/issues/3688#issuecomment-4381074654>

### Our experience

A fresh `bd init` left no `dolt remote` configured. Cross-machine sync
(via `refs/dolt/data` on the same git origin) is the canonical
beads sync mechanism, but `bd init` doesn't wire it up — operator has
to know to run `bd dolt remote add origin <git-url>` manually.
Without this, `git pull` brought new JSONL content but `bd hooks run
post-merge` had no remote to pull from, so Dolt stayed stale; the
next `git commit` then fired the pre-commit auto-export and wrote
the stale Dolt over the freshly-pulled JSONL → data loss on
`.beads/issues.jsonl`. ~8 hours of misdiagnosis (count-based guards,
ORIG_HEAD checks, briefly considered third-party Dolt hosting)
before reading `docs/SYNC_SETUP.md` and finding the architecture.

### Workaround

`scripts/setup-beads.sh` lines 73–81 (commit `fcfb4f8`) — after
`bd bootstrap`, idempotently run `bd dolt remote add origin
<git-origin-url>` if `bd dolt remote list` doesn't already show
`origin`. Plus we write `sync.remote: <url>` to `.beads/config.yaml`
(committed) so fresh clones inherit the remote via `bd bootstrap`.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): FIXED — but only in the gated
  v1.0.5.** Issue [#3688](https://github.com/gastownhall/beads/issues/3688)
  is **CLOSED/completed** (2026-05-13), fixed by PR
  [#3909](https://github.com/gastownhall/beads/pull/3909) "fix(init): use
  git origin as default Dolt remote" (merged 2026-05-13). The
  `main`-branch DOLT.md confirms `bd init` now "auto-detects `git origin`
  and persists it as `sync.remote`." **Release-ancestry caveat:** PR
  #3909's merge commit is `ahead` of the v1.0.4 tag and `behind` v1.0.5,
  so the fix is **NOT in the stable v1.0.4 release — it ships only in the
  gated/do-not-upgrade v1.0.5.** On v1.0.4 the `sync.remote` workaround
  (`setup-beads.sh`) must stay. On v1.0.5 it can be dropped, but v1.0.5
  itself is unsafe to run multi-machine (see banner #4259).
- 2026-05-05: filed our comment; upstream maintainer hasn't yet
  responded. Issue remains OPEN. Workaround in place.

---

## Problem 2 — `bd doctor` is unsupported in embedded mode

### Upstream

- Issue: [gastownhall/beads#3597](https://github.com/gastownhall/beads/issues/3597) — `bd doctor: support embedded mode (currently stubbed across all modes incl. --check=conventions / --json)` (OPEN)
- Our comment: <https://github.com/gastownhall/beads/issues/3597#issuecomment-4381074787>

### Our experience

`bd doctor` errors with `Note: 'bd doctor' is not yet supported in
embedded mode.` Embedded mode is the default for new repos via
`bd init`, so doctor is effectively unavailable for the largest
class of users. We use embedded mode and need a working health
check.

### Workaround

`scripts/bd-doctor.sh` (commit `edd0d5b`, ob-a1y) — composes the
equivalent checks from primitives that DO work in embedded mode
(`bd version`, `bd where`, `bd dolt status`, `bd dolt remote list`,
`bd config get dolt.auto-commit`, `bd config get export.auto`,
`git ls-remote origin | grep dolt`). Wired into `pnpm run bd:doctor`
and the `setup:all` PHASE 6 smoke.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): STILL-OPEN upstream;
  WORKAROUND-AVAILABLE (ours); N/A in server mode.** Issue
  [#3597](https://github.com/gastownhall/beads/issues/3597) is **OPEN**.
  The maintainer's latest comment (2026-05-11) leans toward *not*
  supporting database-coupled `bd doctor` in embedded mode at all:
  *"`bd doctor`'s value in embedded mode still needs investigation and
  scoping, since its output won't yield anything actionable … except
  possibly introducing a foot gun."* So there is no upstream fix in
  v1.0.4 or v1.0.5. We carry `scripts/bd-doctor.sh` as the workaround
  (so this is NOT a no-workaround blocker). **Crucially for the cutover:
  livespec's `dolt-server` tenant runs in SERVER mode, not embedded
  mode** (`beads-schema-mapping.md` §2), so the embedded-mode doctor
  limitation does not apply to the cutover deployment — confirm in
  li-srbpds that `bd doctor` (or the bd-doctor.sh equivalent) behaves in
  server mode.
- 2026-05-05: filed our comment; OPEN. Workaround in place; remove
  the script + the wrapper-table row when upstream lands the fix.

---

## Problem 3 — Conceptual confusion: git vs Dolt as source of truth

### Upstream

- Issue: [gastownhall/beads#3135](https://github.com/gastownhall/beads/issues/3135) — `Clarify git vs dolt as source of truth for issue data` (OPEN)
- Our comment: <https://github.com/gastownhall/beads/issues/3135#issuecomment-4381074937>

### Our experience

Same trap as the original reporter — assumed `.beads/issues.jsonl`
was the cross-machine source of truth (because git tracks it),
built two layers of defensive guards (count-based shrinkage
detection, ORIG_HEAD-based safety checks) on top of that wrong
model before reading `docs/SYNC_SETUP.md` and discovering that
`refs/dolt/data` is the canonical wire protocol. Confirmed in our
comment that the confusion is still happening 6 months after the
original report.

### Workaround

`AGENTS.md § Beads architecture` section (commit `fcfb4f8`, ob-a1y)
— prominent top-of-bd-section guardrail with: architecture
statement, anti-patterns list, upstream-doc pointers, `bd prime`
mandate, diagnostic command list. Plus
`~/.claude/projects/-data-projects-openbrain/memory/feedback_third_party_docs_first.md`
— private memory rule: read upstream docs the first time a
third-party tool surprises us.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): FIXED — but only in the gated
  v1.0.5.** Issue [#3135](https://github.com/gastownhall/beads/issues/3135)
  is **CLOSED/completed** (2026-05-13). Two PRs address it: PR
  [#3909](https://github.com/gastownhall/beads/pull/3909) (init defaults to
  git-origin remote) and PR
  [#4063](https://github.com/gastownhall/beads/pull/4063) "fix(init): make
  JSONL auto-export opt-in" (merged 2026-05-21). The v1.0.5 Upgrade Notes
  state it unambiguously: *"Dolt is the primary datastore.
  `.beads/issues.jsonl` is now treated as an optional export … It is not
  the canonical git-tracked source of truth, not cross-machine sync, and
  not a full database backup."* **Release-ancestry caveat:** both #3909
  and #4063 are `ahead` of v1.0.4 and `behind` v1.0.5 — the
  source-of-truth clarification + opt-in export land **only in the gated
  v1.0.5, NOT v1.0.4.** Behavioral note for the bridge: on v1.0.5,
  `export.auto`/`export.git-add` default to **off**; if any livespec
  tooling still reads `.beads/issues.jsonl`, it must explicitly set those
  on (li-srbpds).
- 2026-05-05: filed our comment; OPEN. Suggested fix in our comment
  is to auto-include a one-line architecture statement in the
  bd-init-generated AGENTS.md preamble so agents/operators don't
  need to read 4 deep docs to assemble the picture. Workaround
  is solid in our project; no urgency to remove.

---

## Problem 4 — `bd bootstrap` doesn't wire remote on fresh embedded init

### Upstream

- Issue: [gastownhall/beads#3419](https://github.com/gastownhall/beads/issues/3419) — `bug: bd bootstrap doesn't wire remote on fresh embedded init` (OPEN)
- Our comment: <https://github.com/gastownhall/beads/issues/3419#issuecomment-4381075115>

### Our experience

After `bd bootstrap` cloned data via `refs/dolt/data` on a fresh
clone, `bd dolt remote list` was still empty — needed manual
`bd dolt remote add` to make `bd dolt push` / `pull` work. Closely
related to Problem 1 from the clone-side.

### Workaround

We wrote `sync.remote: <url>` to `.beads/config.yaml` (committed)
so that `bd bootstrap` on subsequent fresh clones sees the
config and clones via that remote — populating `repo_state.json`
correctly. Combined with `scripts/setup-beads.sh`'s defensive
`bd dolt remote add` re-assertion (Problem 1's workaround), this
covers both the install side and the bootstrap side.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): FIXED — but only in the gated
  v1.0.5.** Issue [#3419](https://github.com/gastownhall/beads/issues/3419)
  is **CLOSED/completed** (2026-05-13), fixed by the same PR
  [#3909](https://github.com/gastownhall/beads/pull/3909) as Problem 1
  (the synthesize-remote-at-init and rehydrate-remote-on-bootstrap fixes
  landed together, exactly the "close the loop natively" combination
  predicted below). The `main` DOLT.md confirms `bd bootstrap`
  auto-detects `refs/dolt/data` on origin and clones from it, with
  `sync.remote` taking precedence. **Release-ancestry caveat:** #3909 is
  `ahead` of v1.0.4 / `behind` v1.0.5 → **NOT in v1.0.4, only in the
  gated v1.0.5.** Keep the `.beads/config.yaml` `sync.remote` workaround
  on v1.0.4.
- 2026-05-05: filed our comment with the workaround as a possible
  fix shape. OPEN. The combination of fixing #3688 (synthesize
  remote at `bd init`) + this issue (rehydrate remote on bootstrap)
  would close the loop natively without our config workaround.

---

## Problem 5 — Documentation gaps for `bd prime`, `bd remember`, `bd dream`, `bd edit`, etc.

### Upstream

- Issue: [gastownhall/beads#3683](https://github.com/gastownhall/beads/issues/3683) — `Lacking docs (bd prime, remember, dream, edit)` (OPEN)
- Our comment: <https://github.com/gastownhall/beads/issues/3683#issuecomment-4381076206>

### Our experience

bd-init-generated AGENTS.md references commands that have no public
documentation. An agent reading AGENTS.md as the entry point doesn't
know how to use `bd prime` (the project's session-start ritual)
because the docs trail goes cold. We had to read 4 separate upstream
docs (ARCHITECTURE.md, SYNC_SETUP.md, GIT_INTEGRATION.md,
DOLT-BACKEND.md) to assemble the architectural picture.

### Workaround

`AGENTS.md § Beads architecture` section provides the entry-point
documentation for our project. Internal-only; doesn't help other
projects.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): FIXED (docs).** Issue
  [#3683](https://github.com/gastownhall/beads/issues/3683) is
  **CLOSED/completed** (2026-05-10). Maintainer: *"PR #3820 and #3842
  address the substantive part of the missing and bad docs."* PR
  [#3820](https://github.com/gastownhall/beads/pull/3820) is **in
  v1.0.4** (merged ~1h before the v1.0.4 tag, `behind` v1.0.4); PR
  [#3842](https://github.com/gastownhall/beads/pull/3842) is **only in
  v1.0.5** (`ahead` of v1.0.4). Lowest-severity of the eight (docs only,
  no behavior). Note: `bd dream` is not a real command in the v1.0.5 CLI
  reference; the memory family is `bd remember`/`memories`/`recall`/
  `forget` — the original AGENTS.md reference was likely stale.
- 2026-05-05: filed our comment with concrete suggestions
  (consolidated "How cross-machine sync works" entry-point doc;
  auto-include architecture statement in generated AGENTS.md).
  OPEN.

---

## Problem 6 — `.beads/` permissions warning on every bd invocation

### Upstream

- Original issue: [gastownhall/beads#3391](https://github.com/gastownhall/beads/issues/3391) — `bd init: chmod existing .beads/ to 0700 instead of warning on every call` (CLOSED, fixed in #3483)
- Fix PR: [gastownhall/beads#3483](https://github.com/gastownhall/beads/pull/3483) — MERGED 2026-04-28
- Sibling issue (different code path): [gastownhall/beads#3593](https://github.com/gastownhall/beads/issues/3593) — `bd worktree create: chmod new worktree's .beads/ to 0700 instead of warning on every call` (OPEN)
- We did NOT post a comment on these — fix already accepted
  upstream; we just need to wait for the release.

### Our experience

`bd ready` and every git hook invocation (`bd hooks run post-merge`
etc.) emit `Warning: /path/to/.beads has permissions 0755
(recommended: 0700). Run: chmod 700 /path/to/.beads`. Git can't
track directory permissions (only the executable bit on files), so
`.beads/` checks out as 0755 from a fresh clone regardless of
source. Persistent warning noise.

### Workaround

Two-layer self-heal:
1. `scripts/setup-beads.sh` lines 89–92 (commit `f9f1e39`) — chmod
   700 `.beads/` once on every prepare run.
2. The hook template in `scripts/setup-beads.sh` (commit `fe3169c`)
   — every `pre-commit`, `pre-push`, `post-merge`, `post-checkout`,
   `prepare-commit-msg` hook re-asserts `chmod 700 .beads/` before
   invoking bd. Self-healing on every git operation.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): FIXED (main path);
  sibling-path STILL-OPEN.** PR
  [#3483](https://github.com/gastownhall/beads/pull/3483) (chmod existing
  `.beads/` to 0700, GH#3391) merged 2026-04-28 and its merge commit is
  **`behind` the v1.0.4 tag → the fix IS in stable v1.0.4** (so the
  on-every-call warning for the primary `.beads/` is resolved without
  needing v1.0.5). **However the sibling issue
  [#3593](https://github.com/gastownhall/beads/issues/3593)** ("`bd
  worktree create`: chmod new worktree's `.beads/` to 0700") **is still
  OPEN** — the worktree code path is unfixed in both v1.0.4 and v1.0.5.
  Keep the chmod-700 self-heal in `setup-beads.sh` + the hook template
  until #3593 lands (it is also the safety belt against #3593). Low
  severity: warning noise only, no data loss; not a cutover blocker.
- 2026-04-28: PR #3483 merged upstream. Fix is in master but no
  release tag past `v1.0.3` (which was tagged 2026-04-24, four days
  before the merge).
- 2026-05-05: tracked in our beads issue **ob-d29** (`Check
  2026-05-12: bump bd pin past v1.0.3 once a release contains
  GH#3483`). When v1.0.4 lands, bump the pin in `.mise.toml` and
  remove our self-heal workaround.

---

## Problem 7 — workspace identity mismatch silently breaks all bd operations; no upstream recovery story

### Upstream

- Issue: [gastownhall/beads#3733](https://github.com/gastownhall/beads/issues/3733) — `bd workspace identity mismatch: silent project_id rewrite + no detection in bd doctor + no recovery story` (OPEN, filed 2026-05-06). Covers all three gaps below.
- Related (different code paths, same error string): [gastownhall/beads#3476](https://github.com/gastownhall/beads/issues/3476).

### Our experience

A macOS clone hit `Error: workspace identity mismatch detected` on
`pnpm setup:all`'s bd:doctor step, with three downstream WARN
symptoms (no dolt remote, dolt.auto-commit unset, export.auto unset).

Root cause traced via `git log -p .beads/metadata.json`:

- `da3d4ff` (2026-05-04 05:20) — initial `bd init`; metadata.json
  committed with `project_id: 6737e2a6-6659-4604-934d-12cf8d483ff6`.
- `934900c` (2026-05-05 17:34) — message "bd init: initialize beads
  issue tracking"; **rewrote metadata.json** to
  `project_id: f5aef29f-8401-4a85-9160-28ae14497c52`. Single-line
  change; no other files touched (so it wasn't a re-init).

The macOS clone bootstrapped its local Dolt store at 08:19 May 5
against the OLD project_id (6737e2a6), then pulled commit 934900c
which changed the tracked project_id (f5aef29f). bd refuses to
operate on the mismatched pair. Every `bd config get`, `bd dolt
remote list`, `bd config set` errors with `workspace identity
mismatch detected`. Our `setup-beads.sh` then silently swallows
those errors via `>/dev/null 2>&1 || true` (see commit `e6f5144`
lines 96–97 + 79–81), reporting `setup:beads: ok` despite zero
actual progress. bd:doctor reports three downstream WARN lines
without diagnosing the root cause.

### Three coupled gaps

1. **bd silently rewrites metadata.json's project_id**. The
   project_id should be a stable invariant for the project's
   lifetime; whatever code path produced commit `934900c` (probably
   a `bd init` re-run, or a side-effect of `bd dolt remote add` /
   `bd dolt push` in some configuration) violates that invariant.
   When the rewrite is committed and pushed, every existing
   bootstrapped clone is silently broken until manual recovery.
2. **bd:doctor doesn't detect identity mismatch directly**. It
   probes individual properties (remote list, config get) and
   reports the *symptoms* of the mismatch (three WARN lines),
   never the root cause. An operator running bd:doctor sees
   "remediation: bd config set dolt.auto-commit on" and runs that
   command, which re-errors with the same identity mismatch — UX
   trap.
3. **No upstream "stale local Dolt + new tracked project_id"
   recovery story**. The recovery is `mv .beads/embeddeddolt
   .beads/embeddeddolt.corrupt.backup.<ts>` + `bd bootstrap --yes`
   (re-clone from origin's refs/dolt/data), but bd doesn't surface
   this hint anywhere; you have to reverse-engineer it from the
   error message.

### Workaround

`scripts/setup-beads.sh` (commit TBD — landing alongside this
documentation entry):

- **Stop swallowing errors with `|| true`** on `bd config set` and
  `bd dolt remote add` calls. Specific failures (identity mismatch)
  are now detected and handled explicitly; other failures bubble
  up.
- **Detect identity mismatch upfront** with a `bd dolt status`
  probe; if stderr contains `workspace identity mismatch`, auto-
  recover by `mv`ing `.beads/embeddeddolt` to a timestamped backup
  and re-running `bd bootstrap --yes`. This re-clones the local
  Dolt from origin's `refs/dolt/data` (the canonical state), which
  carries the tracked project_id by construction. Backup is
  preserved (not deleted) in case the operator wants to recover
  any local-only Dolt state that wasn't pushed.

The auto-recovery is destructive in the sense that it moves the
old store aside, but it's REVERSIBLE (the old store is preserved
under `.beads/embeddeddolt.corrupt.backup.<unix-ts>/`) and the
canonical state is on origin. For a single-operator project where
all real bd state is pushed to refs/dolt/data, this is the safe
recovery.

### Status

- **2026-06-08 (live-repro, post Phase-1 dolt-server standup): RESOLVED
  — server mode is IMMUNE to the embedded `project_id` rewrite trap.** A
  live repro on `bd` **v1.0.5** in server mode against the running
  `dolt-server` confirms the NEEDS-LIVE-REPRO below is closed. `bd init
  --server` writes a local `.beads/metadata.json` whose `project_id` is
  **server-sourced** — it adopts the tenant DB's existing
  `metadata._project_id` (per bd PR
  [#2925](https://github.com/gastownhall/beads/pull/2925)), not a
  locally-minted UUID. A second workspace init'd against the same tenant
  DB **adopted the identical `project_id`** and cross-updated issues with
  **zero `workspace identity mismatch` errors**. The embedded-mode
  silent-rewrite trap (commit `934900c` narrative below) does NOT occur
  in server mode because the server-owned identity is the single source
  of truth both workspaces read. **Verdict for li-zmigvx/li-srbpds:
  server-mode-safe — confirmed by live repro, not merely scope-argued.**
  The embedded-mode `setup-beads.sh` mv-and-rebootstrap recovery remains
  the workaround for any embedded usage, but is N/A to the server-mode
  cutover.
- **2026-06-08 (li-mwwdws / v1.0.5 gate): STILL-OPEN;
  WORKAROUND-AVAILABLE (reversible); NEEDS-LIVE-REPRO for server mode
  (after Phase 1).** Issue
  [#3733](https://github.com/gastownhall/beads/issues/3733) is **OPEN**
  as of 2026-05-27 (maintainer drift-check: *"still open and unlabeled …
  #4173 partially mitigates the same failure class by treating
  `--from-jsonl` as local-source intent and refusing to silently diverge
  … reduces one path to accidental `project_id` …"*). So **only a partial
  mitigation** exists, in neither v1.0.4 nor a safe release; the silent
  rewrite + no-detection-in-doctor + no-recovery-story gaps are not fully
  closed. The related identity issue
  [#3476](https://github.com/gastownhall/beads/issues/3476) (global-memory
  sentinel-UUID rejection) IS closed/completed (2026-05-29). Our
  mv-and-rebootstrap auto-recovery in `setup-beads.sh` is the workaround,
  so this is NOT a no-workaround blocker — but it was authored for
  EMBEDDED mode. **livespec's cutover uses server mode, where the tenant
  identity is server-owned (`beads-schema-mapping.md` §2.3), which
  *should* side-step the embedded `metadata.json` rewrite trap — but this
  is UNVERIFIED. Mark NEEDS-LIVE-REPRO: confirm against a running
  `dolt-server` (Phase 1) that the server-mode tenant is not subject to
  an analogous identity mismatch before li-zmigvx cuts over.** Do NOT
  assert server-mode-safe without a live repro.
- 2026-05-06: filed Problem 7 in this index. Workaround landed in
  `setup-beads.sh` (commit `414a9df`) — auto-detect + mv-and-rebootstrap
  recovery. Cross-reference comments added (commits `d6b3000`,
  `8436431`).
- 2026-05-06: upstream filed as [gastownhall/beads#3733](https://github.com/gastownhall/beads/issues/3733),
  consolidating all three gaps into one issue. No maintainer response yet.

---

## Problem 8 — multi-tool ownership race over `core.hooksPath` (lefthook vs. bd's `.beads/hooks/`)

### Upstream

- bd-side issue: [gastownhall/beads#1380](https://github.com/gastownhall/beads/issues/1380) — `Multi-tool ownership race over git hook files (husky / lefthook / bd reciprocal clobber)` (CLOSED, in-flight via #2217-#2220). Pursuing **section markers** as the convergence point — the same `<!-- BEGIN BEADS INTEGRATION -->` style markers our `.beads/hooks/pre-commit` template already uses.
- lefthook-side related history: [evilmartians/lefthook#198](https://github.com/evilmartians/lefthook/issues/198) — `disable postinstall force-install` (CLOSED wontfix, 2025-01-14). Maintainer position: *"if you add lefthook into devDependencies I assume that you want its postinstall script to do `lefthook install` automatically… For the optional use you can always remove the lefthook dependency."*
- lefthook-side mitigation that landed but doesn't reach us: [evilmartians/lefthook#1248 → PR #1292](https://github.com/evilmartians/lefthook/pull/1292) (merged 2026-02-03). `lefthook install` now errors when `core.hooksPath` is non-default and adds a `--reset-hooks-path` flag for the explicit-opt-in case. **But** the npm postinstall still calls `lefthook install -f`, and `-f` bypasses the new safety — so the upstream fix doesn't reach us through the path that's actually firing.

### Our experience

The bd architecture expects `git config core.hooksPath = .beads/hooks/` so the openbrain-managed hook chain at `.beads/hooks/{pre-commit,pre-push,post-merge,...}` fires on every git operation. Those hooks delegate to lefthook via `lefthook run --no-auto-install <hook>` AND run `bd hooks run <hook>` for the JSONL auto-export and `refs/dolt/data` sync.

Lefthook's npm package ships a postinstall script (`node_modules/lefthook/postinstall.js`) that runs `lefthook install -f` on every `pnpm install`. `lefthook install -f` writes lefthook-only hook files to `.git/hooks/` AND unconditionally re-asserts `git config core.hooksPath = .git/hooks`. This silently bypasses the bd integration entirely:

- `bd close` / `bd update` writes update Dolt → `export.auto` writes the JSONL → bd's pre-commit hook never fires on `git commit` → JSONL drift accumulates as "modified working tree" or stranded staged changes.
- `git push` does NOT push `refs/dolt/data` because bd's pre-push hook is also bypassed → cross-clone bd state silently diverges.
- The chmod-700 self-heal from [Problem 6](#problem-6--beads-permissions-warning-on-every-bd-invocation) lives inside `.beads/hooks/*` and ALSO doesn't fire while the path is wrong.

The user-visible symptom we hit was a staged-but-uncommitted `.beads/issues.jsonl` waiting on the working tree at the start of an `openbrain:update-specification-drift` invocation. Tracing it back, `git config core.hooksPath` was `/data/projects/openbrain/.git/hooks` despite `scripts/setup-beads.sh` setting it to `.beads/hooks`. The most likely culprit is the `pnpm install --prefer-offline --frozen-lockfile` invocation inside `scripts/hydrate-worktree.sh` — worktrees share `.git/config` with the main checkout, so a worktree-isolated sub-agent's hydration runs lefthook's postinstall and flips the **shared** path setting for every worktree and the main checkout simultaneously.

`bd:doctor` did not catch this — it verified bd version, dolt remote, refs/dolt/data presence, `dolt.auto-commit`, and `export.auto`, but had no check for `core.hooksPath`. Same shape of failure as [Problem 7](#problem-7--workspace-identity-mismatch-silently-breaks-all-bd-operations-no-upstream-recovery-story): a doctor that probes properties without checking the architecturally-load-bearing config knob underneath them.

### Workaround

**Drop the lefthook npm package; install lefthook via mise** (commit TBD, ob-5i4). Specifically:

1. `.mise.toml` pins `aqua:evilmartians/lefthook = "1.13.6"` (matches the prior npm version exactly).
2. `package.json` `dependencies` no longer carries `lefthook`. The npm postinstall does not exist on disk and cannot fire.
3. `scripts/setup-beads.sh`'s hook-template generator dispatches lefthook via `mise exec -- lefthook run --no-auto-install <hook>` (the prior `node_modules/lefthook/...` fallback chain was dead code after the npm removal and is dropped).
4. `scripts/bd-doctor.sh` adds two new checks: (8) `core.hooksPath` MUST equal `.beads/hooks` or `.beads/hooks/` (FAIL otherwise), and (9) lefthook MUST be resolvable via `mise exec --`. A reappearance of `node_modules/lefthook/postinstall.js` triggers a WARN line documenting the regression.
5. `lefthook.yml`, `scripts/hydrate-worktree.sh`, and the bd-managed hook templates' header comments are updated to point at this Problem 8 entry as the rationale.

The upstream maintainer position on lefthook#198 is that uninstalling the npm package is the supported escape hatch for projects that don't want the auto-install postinstall — so this workaround is endorsed by the lefthook side, not a hack against it. Lefthook stays the orchestrator of pre-commit / pre-push gates via `lefthook.yml`; only its **installation method** changes.

### Status

- **2026-06-08 (li-mwwdws / v1.0.5 gate): WORKAROUND-AVAILABLE
  (ours, pin-independent); upstream marker fix present but does NOT
  address our vector; server-mode init structurally avoids it.** The
  bd-side section-markers feature
  ([#1380](https://github.com/gastownhall/beads/issues/1380), PR
  [#2222](https://github.com/gastownhall/beads/pull/2222)) shipped in
  v0.57.0 and is therefore in v1.0.4 and v1.0.5 — but it only makes bd's
  OWN hook writes marker-safe; it does NOT stop lefthook's npm
  postinstall from re-asserting `core.hooksPath=.git/hooks` (the actual
  antagonist we hit). lefthook still declines an npm-postinstall opt-out.
  So our **mise-pinned-not-npm-installed lefthook** workaround stands and
  is **independent of the bd version pin** — a v1.0.4 vs v1.0.5 choice
  does not change it. **For the cutover specifically:** the `dolt-server`
  server-mode tenant model uses `bd init --server --quiet --stealth`
  (no git hooks injected into the consuming repo,
  `beads-schema-mapping.md` §2.2/§2.3), which structurally avoids the
  `core.hooksPath` ownership race entirely — there are no `.beads/hooks/`
  to fight over. Not a cutover blocker.
- 2026-05-07: filed our Problem 8 entry. Workaround landed in commit TBD (ob-5i4) — mise pin + npm removal + bd:doctor checks. **Just watching upstream from here.**
- The bd-side fix (beads#1380 section markers) is the convergence path: once bd ships section markers natively, third-party hook managers that respect markers (which lefthook does NOT, today) could coexist without an arms race. Until then, our mise-pinned-not-npm-installed approach removes the antagonist entirely and is more durable than waiting on either side to land a fix.
- Re-evaluate this workaround if lefthook ever ships an opt-out for the npm postinstall (a recurring community request that the maintainer has explicitly declined). Until then, no urgency to revisit.

---

## Internal beads issues we've filed for our own tracking

| ID | Title | Status | Notes |
|---|---|---|---|
| **ob-d29** | Check 2026-05-12: bump bd pin past v1.0.3 once a release contains GH#3483 | OPEN | Tracks Problem 6's upstream release wait |
| **ob-ir5** | Re-track scripts/with-openbrain-env.sh after 1password-env-wrapper factory ships cross-platform output | OPEN | Adjacent — not strictly a bd problem; tracks the post-factory-ship wrapper re-track |
| **ob-5i4** | Migrate lefthook from npm to mise | (closing alongside this entry) | Tracks Problem 8's workaround: drop the npm package + add core.hooksPath check to bd:doctor |

---

## How to update this file

When upstream moves (issue closed, PR merged, release tagged), update
the relevant **Status** subsection with a new dated entry at the top.
When you remove a workaround from this codebase because the upstream
fix landed in a pinned version, mark the workaround removal commit
in the Status entry too.

When a new bd problem surfaces, add a new H2 section at the bottom
(numbered, so the order tells the chronology) with the same
subsection structure.

---

## v1.0.5 re-verification (li-mwwdws, 2026-06-08) — BEADS-BUG-EXPOSURE GATE

This is the **Known-upstream-bug envelope gate** required by
`dolt-server` §"Beads-tenant contract" before any beads tenant is cut
over for production tracking (`beads-schema-mapping.md` §2.3). It
re-verifies each of Problems 1–8 against the target version.
Per-problem verdicts are recorded inline in each Problem's **Status**
subsection below (entries dated 2026-06-08); this banner is the
gate summary. Evidence: beads `CHANGELOG.md`, GitHub issue/PR states,
and release-tag ancestry (`gh api .../compare/<tag>...<sha>`) — all
read on 2026-06-08.

### Release-landscape finding (CUTOVER-AFFECTING)

> **2026-06-08 SUPERSEDED for our architecture — pin v1.0.5.** A
> live-repro (post Phase-1 dolt-server standup, `bd` v1.0.5 in server
> mode) demonstrated that the v1.0.4-vs-v1.0.5 fork below does NOT bind
> the `dolt-server` **standalone** model. The #4259 / migration-`0043`
> corruptor only breaks `bd dolt` **multi-machine sync between embedded
> stores**; our model is **one dolt-server, bd is a plain SQL client, no
> Dolt remote on the tenant, durability via Dolt-native `remotesapi`
> replication** — that sync path is never invoked. Live-repro evidence:
> migration `0043` applied cleanly to the single-server store
> (`schema_migrations` advanced **1→49**); `bd dolt remote list` reported
> **"No remotes configured"**; **zero sync activity under `--verbose`**;
> writes land as native Dolt commits (committer **"beads"**). Mixing
> v1.0.4 and v1.0.5 against one server is **UNSAFE** — v1.0.5's forward
> schema-skew guard (#4152) hard-fails a v1.0.4 binary against a
> v1.0.5-migrated DB — so **standardize the whole family on v1.0.5**.
> The "pin v1.0.4 + wait for v1.0.6" recommendation later in this
> section is retained for the historical record but is **no longer the
> recommended posture** for the standalone server architecture.

The task names **v1.0.5** as the pinned target, but the live release
landscape (as assessed 2026-05-29 → 2026-06-08, embedded-sync framing)
made that pin look unsafe:

- **v1.0.5 is a GATED pre-release** (`prerelease: true`, published
  2026-05-29). Its release notes say: *"🚨 This release is gated — do
  not upgrade. v1.0.5 contains a migration (`0043`) that can silently
  and unrecoverably break multi-machine `bd dolt` sync after both
  clones upgrade. See
  [#4259](https://github.com/gastownhall/beads/issues/4259)."*
  Homebrew was reverted to v1.0.4.
- **#4259 is still OPEN/reopened** as of 2026-06-07 ("reopening as
  #4266 is only one of the necessary fixes"). **No v1.0.6 exists** —
  v1.0.5 remains the latest tag (verified 2026-06-08).
- The latest *stable, safe* release is **v1.0.4** (2026-05-09).

Release-tag ancestry shows the fixes for Problems **1, 3, 4, 5 land
ONLY in v1.0.5**, NOT in v1.0.4 (the relevant fix commits are `ahead`
of the v1.0.4 tag and `behind` the v1.0.5 tag). So the operator faces
a hard fork:

- Run **v1.0.4 (safe sync)** → Problems 1/3/4/5 are NOT fixed; their
  workarounds must stay carried.
- Run **v1.0.5 (Problems 1/3/4/5 fixed)** → exposes the #4259
  multi-machine sync-corruption migration (do-not-upgrade).

**Either way, no single currently-available release is both safe to
sync across machines AND carries the Problem 1/3/4/5 fixes.** This was
the headline blocker under the *embedded multi-machine sync* framing,
and the posture then was to **pin v1.0.4 + keep the existing workarounds
and wait for v1.0.6**. **2026-06-08 update: SUPERSEDED for the
`dolt-server` standalone architecture (see the banner at the top of this
section).** Because the standalone model never invokes the `bd dolt`
multi-machine sync path that #4259/`0043` corrupts, the fork does not
bind — **pin v1.0.5** (it carries the Problem 1/3/4/5 fixes) and
standardize the whole family on it; v1.0.4↔v1.0.5 mixing against one
server is unsafe per the #4152 forward schema-skew guard. The "wait for
v1.0.6" path remains valid only for any future *embedded multi-machine*
usage, which the cutover does not use.

> Server-mode note: livespec's intended deployment is the
> `dolt-server` **server-mode** tenant model
> (`beads-schema-mapping.md` §2), not the embedded mode in which most
> of Problems 1–8 were originally hit. Several embedded-mode problems
> (1, 2, 4, 6) are structurally side-stepped by server mode, but that
> is a *scope* argument, not an upstream fix — flagged per-problem
> below.

### Per-problem gate verdict table

| # | Problem | v1.0.5 verdict | Fix lands in |
|---|---|---|---|
| 1 | `bd init` doesn't synthesize Dolt remote at git origin | **FIXED** (#3688 closed; PR #3909) | v1.0.5 only (NOT v1.0.4) |
| 2 | `bd doctor` unsupported in embedded mode | **STILL-OPEN-NO-WORKAROUND** upstream (#3597 OPEN, maintainer leaning won't-support); livespec carries `bd-doctor.sh` workaround; **N/A in server mode** | — |
| 3 | git-vs-Dolt source-of-truth confusion | **FIXED** (#3135 closed; PRs #3909 + #4063 make JSONL opt-in / Dolt canonical) | v1.0.5 only (NOT v1.0.4) |
| 4 | `bd bootstrap` doesn't wire remote on fresh embedded init | **FIXED** (#3419 closed; PR #3909) | v1.0.5 only (NOT v1.0.4) |
| 5 | Docs gaps (`bd prime`/`remember`/`dream`/`edit`) | **FIXED** (#3683 closed; docs PRs #3820 in v1.0.4, #3842 in v1.0.5) | partially v1.0.4, fully v1.0.5 |
| 6 | `.beads/` perms warning on every invocation | **FIXED** (#3391/#3483 merged; in v1.0.4) — sibling **#3593** (worktree path) **STILL-OPEN** | v1.0.4 |
| 7 | workspace identity mismatch / silent `project_id` rewrite / no recovery | **RESOLVED for server mode (live-repro 2026-06-08): IMMUNE** — `bd init --server` adopts the tenant DB's server-sourced `project_id` (bd #2925); a second workspace adopted the identical id with zero mismatch errors. Embedded-mode #3733 stays OPEN (workaround carried) but is N/A to the server-mode cutover. | — |
| 8 | `core.hooksPath` ownership race (lefthook vs `.beads/hooks/`) | upstream section-markers fix (#1380) shipped (v0.57.0, in v1.0.4), but it does NOT resolve livespec's lefthook-npm-postinstall vector; livespec's mise-not-npm workaround stands and is **independent of the bd pin**; server-mode `--stealth`/no-hooks init structurally avoids it | v1.0.4 (markers); workaround stands regardless |

**Gate outcome:** No `STILL-OPEN-NO-WORKAROUND` problem is an
*unconditional* blocker (Problem 2 is N/A in server mode; Problem 7 is
now **RESOLVED for server mode** — live-repro 2026-06-08 confirmed
server-mode immunity to the `project_id` rewrite trap). The
release-landscape fork above was the binding blocker under the
embedded-sync framing; **as of the 2026-06-08 live-repro it is
SUPERSEDED** for the `dolt-server` standalone architecture (the
#4259/`0043` corruptor never fires on the standalone single-server, no-
remote model — verified empirically). **Resolved gate posture: pin
v1.0.5 family-wide.** No remaining unconditional blocker for the
server-mode cutover.

---
