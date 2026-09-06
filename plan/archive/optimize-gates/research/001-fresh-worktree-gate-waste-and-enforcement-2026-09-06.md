# Fresh-worktree gate waste: mechanism, chosen fix, and the enforcement surfaces that must prove it — measured 2026-09-06

Captured 2026-09-06 01:00–04:30 UTC from livespec session transcripts, the
installed `livespec-dev-tooling` v1.44.0 package, the fleet manifest, and
the local clones of every fleet member and adopter. Every claim below was
read from a file, a ledger record, or a transcript at the stated time;
nothing is inferred. This note is the seed for this plan's charter and
its first scoping event; it ratifies nothing.

The maintainer's question that opened this plan, verbatim: "I keep getting
these messages, seems like a waste of time. How can we fix/optimize:
`Same gate the previous session hit: a fresh worktree needs just bootstrap
to materialize the worktree pack. Running it, then pushing again.`" — and
the follow-up: is the fix the best mechanical one, how do we ensure it
does not rot or regress, and how do we ensure it reaches every current
and future tenant. The exit criteria of this plan are therefore PROVEN
mechanical enforcement of all three, not a merged code change.

## 1. The waste, as observed

- Two livespec sessions on 2026-09-06 (transcripts `62dc86ef…` and
  `bfb0b6f0…`, cwd `/data/projects/livespec`) each hit
  `worktree_pack_absent` four times. Both created their worktrees with raw
  `git -C /data/projects/livespec worktree add -b <branch> …`, the exact
  command this repo's own `CLAUDE.md`/`AGENTS.md` §"Repository mutation
  protocol" step 2 prescribes.
- The failing gate is `check-primary-checkout-commit-refuse-hook-installed`
  inside the pre-push `just check` aggregate (and the pre-commit aggregate
  for `.py` changes). Its remedy string names `just bootstrap` FIRST — the
  full local first-touch reconcile (mise trust/install, `uv sync`, four
  Claude plugin install-and-update rounds, Codex plugins, beads hardening,
  hooks, notes refspec) — when the one-command repair
  `just install-worktree-pack` (a single `uv run python -m …`) suffices.
  The remedy deliberately names bootstrap first because the standalone
  recipe exists only in wired repos; in a linked worktree of a wired repo it
  always exists.
- After bootstrap the agent re-runs the push, so the full aggregate runs
  twice. `livespec-dev-tooling-ebkrhz.1` (closed 2026-08-16) measured the
  same shape from the `just gate-start` path: a wasted 25–30 minute gate run
  versus a 3.7 s self-heal.

## 2. The mechanism chain (why it happens)

1. **The pack is gitignored-and-installed by design** ("model B",
   `install_worktree_pack.py` docstring): six files (`worktree-lib.sh`,
   `branch-protection.sh`, `gate-run.sh`, `check-no-workflow-edits.sh`,
   `worktree.just`, `branch-protection.just`) plus a generated
   `dev-tooling/.gitignore`, installed from package-data into each
   checkout's `dev-tooling/`, byte-verified against the package on every
   `just check`. The rationale is the fleet "reuse, no copies" delivery rule
   and the commit-refuse-hook precedent (single canonical body, installed
   into an untracked location). A raw `git worktree add` copies no ignored
   file, so every new worktree is born without the pack.
2. **The pack's own creation recipe is undocumented where agents read.**
   `just worktree-create <branch>` (in the pack's `worktree.just`) adds the
   worktree AND provisions the pack. Surveyed 2026-09-06: seventeen
   instruction files (`AGENTS.md`/`CLAUDE.md`) across the fleet members and
   adopters `livespec`, `livespec-dev-tooling`, `livespec-driver-claude`,
   `livespec-driver-codex`, `livespec-runtime`,
   `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`,
   `livespec-console-beads-fabro`, `livespec-overseer`, and `resume`
   prescribe raw `git worktree add -b`; none of the `AGENTS.md` files in
   `/data/projects/*` names `just worktree-create`. (The ledger items
   `livespec-qpk4` and `livespec-dev-tooling-5kcy` record that
   `livespec-overseer` documents it; that text was not re-verified here.)
   The justfile comment above the `import?` lines already names this "the
   discoverability hole that let a session fall back to a raw
   `git worktree add`".
3. **`worktree-create` copies the pack from the PRIMARY checkout**
   (`worktree_provision_pack_from_primary`), and the primary's pack is
   whatever version was last installed there. Measured 2026-09-06 04:00Z in
   `/data/projects/livespec`: the primary was MISSING
   `check-no-workflow-edits.sh` and its `worktree-lib.sh` DIFFERED from the
   v1.44.0 package (pack files dated 2026-08-24; the pin bumped since), so
   `just worktree-create` would have refused with "BLOCKED — missing …
   check-no-workflow-edits.sh". Running `just bootstrap` from a linked
   worktree installs the pack into THAT worktree (the `worktree-pack` row
   targets the invoked worktree by design), so the primary is never
   refreshed by the sessions that hit the gate. This is
   `livespec-dev-tooling-ov9o` (P1 bug, backlog since 2026-08-04). The
   primary was repaired by `just install-worktree-pack` at 02:12Z as part of
   opening this plan.
4. **The shipped self-heal is unreachable from `git push`.**
   `livespec-dev-tooling-ebkrhz.1` added a pack preflight to
   `gate-run.sh start`; that script is itself a pack member, so a raw
   worktree does not have it, and the `git push` → pre-push hook → lefthook
   → `just check-pre-push` path never invokes it.
5. **Two enumerations of the pack set have already drifted.** The verifier
   (`checks/_primary_checkout_worktree_pack.py`) asserts six files; the
   bootstrap `worktree-pack` row (`fleet/_rows_local.py::_worktree_pack_files`)
   asserts FOUR (`branch-protection.just`, `branch-protection.sh`,
   `worktree-lib.sh`, `worktree.just`), its docstring still reading "The
   four canonical pack files". Bootstrap's assert leg can therefore pass a
   pack the gate rejects. This is the clause-lockstep defect class
   `.ai/spec-proposal-review.md` records.
6. **The gate is only reachable through the full aggregate**, so it fires
   at commit or push time, after the work is done (`livespec-qpk4`).

## 3. Candidate mechanisms, evaluated

- **(a) Self-heal inside the verifier check.** Rejected on placement. The
  `check` aggregate runs canonical slugs in alphabetical order
  (`check-aggregate-completeness` enforces this), so `check-no-workflow-edits`
  — which executes `bash dev-tooling/check-no-workflow-edits.sh` — fails
  before `check-primary-checkout-…` would heal, and `check-shell-quality`
  also reads the pack. Healing inside one member cannot order itself ahead
  of its siblings.
- **(b) Track the pack in git.** Rejected as a values reversal, not on
  technical grounds. It would undo the ratified "reuse, no copies" delivery
  rule (`livespec-zs22.7.9`, `livespec-usd3`), duplicate six files into ten
  repositories, require the `bump-pin` fan-out to rewrite pack files as well
  as pins, and still leave a template-born repo unwired.
- **(c) A `post-checkout` git hook** (git fires it on `worktree add`).
  Partial: a fresh worktree has no `.venv` yet, so the installer would sync
  one at creation time; bd's managed hook set includes `post-checkout`
  (`.ai/beads-gaps-workarounds.md`), a coordination seam; and it does not
  cover pin-bump drift in an existing worktree.
- **(d) `just install-worktree-pack` as the FIRST lefthook command of
  `pre-commit` and `pre-push`.** CHOSEN. Every gate path already funnels
  through lefthook (the shared commit-refuse hook body at `.git/hooks/*`
  `exec`s `mise exec -- lefthook run --no-auto-install <hook>` at worktrees),
  and CI already does exactly this step (`ci.yml` "Install canonical worktree
  pack (satisfy invariant)") before its checks. The installer is idempotent,
  writes only gitignored files, and runs under `uv run`, so the installed
  bodies are the BRANCH's pinned package — which also fixes item 3 above
  (ov9o) for the gate path. `check-no-direct-tool-invocation` already
  requires every lefthook `run:` to be `just <target>`, so the line is
  `run: just install-worktree-pack`. Cost: one `uv run` per hook invocation
  (seconds; the first run in a fresh worktree also syncs the venv, which
  `just check` would do anyway).
- **(e) Hook-body trampoline.** The shared `.git/hooks/*` body carries the
  refuse-at-primary logic plus the lefthook `exec`; after a pin bump it too
  drifts from the package until bootstrap re-installs it (hooks were
  re-installed 2026-09-06 03:25Z by a session's bootstrap). A stable
  five-line trampoline delegating everything else to the package would
  remove that class. Noted as the deeper generalization; DEFERRED (see the
  scoping event) because (d) needs no hook-body change and the hook-body
  drift has not yet been measured as a recurring cost.

## 4. Enforcement surfaces that already exist (the carriers for "never rots, all tenants")

- **Central fleet-conformance contract** (`fleet/fleet_conformance.py`,
  livespec v108 §"Fleet membership contract"): reads every manifest
  member's committed `master` files from a central vantage in
  `livespec-dev-tooling`; runs in that repo's `just check`, its per-PR CI
  job, the daily `fleet-conformance.yml` sweep (13:30 UTC), and the release
  fan-out preflight. `--member-ci` attributes a violation to the owning
  member only. Repo birth is register-first: a member registered before it
  is wired is red until `wire_fleet_member` (reconcile mode) fixes it. A
  discovery sweep flags any `livespec-*` repo absent from the manifest.
  Committed-file rows (`_rows_files.py`) already read `justfile`,
  workflows, `copier-answers`, and the dev-tooling pin, so a
  `worktree-pack-wired` row has a template to follow. Manifest members
  today: `livespec` (core), `livespec-dev-tooling` (enforcement-suite),
  `livespec-driver-claude`/`-codex`/`-pi` (driver-plugin),
  `livespec-orchestrator-beads-fabro`/`-git-jsonl` (impl-plugin),
  `livespec-runtime` (library), `livespec-console-beads-fabro` (console),
  `livespec-overseer` (control-plane-tool). All ten invoke the shared
  verifier from their justfiles.
- **In-repo wiring gates**: `check-aggregate-completeness` (every canonical
  slug present, alphabetical) and `check-no-direct-tool-invocation` (every
  lefthook `run:` is `just <target>`). Neither asserts a first-command
  today.
- **The byte-identity verifier** stays the invariant: self-heal writes, the
  verifier still asserts.
- **The copier template** (`templates/orchestrator-plugin/`, routed from the
  root `copier.yml`): `justfile.jinja` already carries both `import?` lines
  and the `install-worktree-pack` recipe; `.gitignore` carries the entries;
  `lefthook.yml.jinja` carries the same three pre-commit commands as
  livespec's and does NOT yet carry the install first-command.
  `TEMPLATE_BORN_CLASSES` is `impl-plugin` only.
- **Guidance rows**: `_rows_instructions.py` (`agent-instruction-surface`)
  asserts the fleet-universal `AGENTS.md` core headings centrally — the
  precedent for single-sourcing the worktree-creation paragraph instead of
  hand-porting it (what `livespec-dev-tooling-5kcy` asks for).
- **Adopters** (`openbrain` pinned, `dolt-server` released, `resume` pinned,
  `homelab` released): by ratified rule (non-functional-requirements
  §"Plugin currency and the release train", `_adopter_lane.py`) adopters
  carry NO per-class obligations and the lane runs exactly one row
  (`claude-plugin-currency`); the fleet GitHub App's installation MUST be
  restricted to fleet repos, so a private adopter is structurally
  unreadable centrally. Local state 2026-09-06: `dolt-server` fully wired
  (pack stale at three `.sh`); `homelab` has the recipe but no `import?`
  and no pack; `openbrain` and `resume` unwired (`resume` has no justfile).
  `docs/livespec-installation-prompt.md` (the published adopter onboarding
  surface) does not mention the pack at all.
- **`poweredge-xubuntu-info`** is NOT a manifest member or adopter and has
  no justfile; it is out of scope. (The session that hit the gate was the
  livespec plan `poweredge-raid-array-maintenance`, working in livespec.)

## 5. Draft requirement carriers and deferrals (to be cut in the scoping event)

Requirements — each must be PROVEN by a mechanical check or test, not by a
merged diff:

- R1 heal-at-gate: a raw `git worktree add` worktree of any wired repo
  commits and pushes with no bootstrap; a pack drifted by a pin bump heals
  at the same seam. Proof: subprocess test in `livespec-dev-tooling` over a
  real wired repo fixture driving the real hook path.
- R2 one pack-set enumeration: installer, verifier, and bootstrap row derive
  from one constant. Proof: lockstep test that fails when any consumer's set
  differs from the installer's.
- R3 central `worktree-pack-wired` row over every manifest member (class
  scope to be decided: all classes that invoke the verifier, today all
  ten): `import?` lines, `.gitignore` entries, `install-worktree-pack`
  recipe, lefthook first-command in both hooks, `.livespec.jsonc`
  `worktree_discipline` key. Proof: row tests plus a green daily sweep and
  a red run against a deliberately unwired fixture member.
- R4 template lockstep: the rendered copier template passes R3's row.
  Proof: a livespec test rendering the template and running the row's
  predicate on the output.
- R5 `worktree-create` installs from the package (or copies then verifies
  and reinstalls), never trusting the primary. Proof: test with a stale
  primary fixture.
- R6 guidance single-sourced: the worktree-creation paragraph enters the
  fleet-universal instruction core asserted by `agent-instruction-surface`,
  and the nine hand-ported items are retired. Proof: the row goes red on a
  fixture `AGENTS.md` lacking it.
- R7 remedy text names `just install-worktree-pack` first when the recipe is
  wired, `just bootstrap` only when it is not. Proof: unit test on the
  remedy composer.
- R8 live evidence (the "done means rolled out" rule): after the pin bump
  lands in every member, a raw worktree in `livespec` pushes a trivial
  branch with no bootstrap; the daily sweep is green with R3 active; both
  journaled on the epic.

Deferrals (concrete, with where they are reconsidered):

- Central enforcement over ADOPTERS — bounded by the ratified one-row
  adopter lane and the App-installation restriction; the adopter's own
  `just check` (same shipped package) is the enforcement. Reconsider only
  via `propose-change` against livespec non-functional-requirements if the
  maintainer wants adopters held to pack wiring centrally. This plan adds a
  test that the installation prompt names every artifact R3 asserts.
- The hook-body trampoline (§3e) — reconsider under this plan if hook-body
  pin drift is measured as a recurring gate cost after R1 lands.

## 6. Ledger items this plan consolidates (verified 2026-09-06)

- `livespec-qpk4` (backlog) — port worktree-create guidance into AGENTS.md → absorbed by R6.
- `livespec-dev-tooling-1buh` (backlog), `livespec-dev-tooling-f7xs` (backlog) — same port, dev-tooling copies → absorbed by R6.
- `livespec-dev-tooling-5kcy` (backlog) — single-source the guidance and check it → IS R6.
- `livespec-dev-tooling-ov9o` (backlog, P1 bug) — worktree-create copies a stale primary pack → IS R5 (and healed at the gate by R1).
- `livespec-dev-tooling-zi4q`, `-3pre`, `-sons` (backlog) — `worktree_primary_path` SIGPIPE exit 141; the shipped v1.44.0 `worktree-lib.sh` already consumes the whole stream (`awk '/^worktree / && !seen …'`, fixed by `livespec-dev-tooling-2oip`) → verify against the shipped body and close as fixed.
- `livespec-dev-tooling-ebkrhz.1` (closed) — the gate-start preflight; precedent, superseded in reach by R1.
- `livespec-dev-tooling-y6e2` (ready) — check-shell-quality passes in CI only because CI skips installing the pack it inspects → related; not absorbed, cross-linked.

## 7. Claims in this note that expire

- Package version: `livespec-dev-tooling` v1.44.0 was the pin in livespec at
  capture; a `chore/bump-livespec-dev-tooling-v1.45.1` branch appeared on
  origin during this session. Re-read file sets and row ids against the pin
  current at implementation time.
- The seventeen-file survey and the adopter wiring states are point-in-time
  reads of local clones on 2026-09-06; re-derive from `origin/master` via
  `git show` before acting on them.
