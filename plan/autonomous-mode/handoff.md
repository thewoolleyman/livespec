# Autonomous-mode MVP — overall plan handoff (livespec core)

## OPERATING DIRECTIVES (standing — maintainer-declared 2026-07-12)
1. **Hand off at 50% context.** When driver/overseer context passes ~50%, STOP
   at a clean boundary and hand off to a fresh session (land the plan + write a
   resume prompt) — do not push past it.
2. **Delegate to sub-agents / the Fabro factory to preserve driver context.** Do
   the heavy lifting (repairs, authoring, multi-file work, live-run iteration
   where feasible) in scoped sub-agents or the factory; keep the driver session
   for plan / dispatch / synthesis.
3. **Dogfood the console TUI as the overseer's operator-steering surface
   (maintainer-declared 2026-07-12).** As soon as possible, drive operator work
   through the live console TUI myself — launched in a tmux session named
   EXACTLY `console-autonomous-mode` (so the maintainer can attach and watch),
   one pane per repo tenant when overseeing more than one. Launch per repo with
   `just tui` from that repo's checkout (builds the release binary + runs it
   under `with-livespec-env.sh -- … serve`). **Any operator-steering action I
   cannot cleanly drive through the TUI is a USABILITY HOLE** — log it and route
   it to the maintainer for a fix discussion, do NOT silently fall back to the
   CLI for it. See "## TUI dogfooding — scope boundary" below for the
   in-scope (holes) vs. by-design-CLI (not holes) split, agreed with the
   maintainer.

## TUI dogfooding — scope boundary (maintainer-declared 2026-07-12)
The console is the **Control Plane / operator cockpit** — deliberately NOT a
Driver and NOT a dev environment (the plane model). So there is a real line
between operator-steering work (must be TUI-drivable; a gap is a hole) and
driver/dev work (the console was never meant to carry it; CLI there is
by-design). Default posture: assume an action SHOULD be TUI-drivable and only
carve out the genuinely-architectural boundaries below.

**Drive via the TUI — a gap is a USABILITY HOLE:**
- Watch each track's ledger / factory / needs-attention state.
- Flip autonomous mode on/off (this IS the I2 acceptance).
- Per-item valves: approve / accept / reject / set-admission / set-acceptance.
- Drain the factory; observe auto-resolutions reflected.
- Triage a truly-unresolvable needs-attention item.

**Stays CLI / sub-agent — by design, NOT a hole:**
- Spec lifecycle (`/livespec:*` seed/propose-change/critique/revise/doctor/next).
- Grooming a work-item (maintainer-owned drafting conversation).
- Code authoring/repair + running the golden-master acceptance script.
- worktree → PR → merge git mechanics.
- Sub-agent / Fabro factory dispatch internals; diff & PR review.

**First confirmed hole: Track D** — the per-item valves are NOT bound to any TUI
key (verified at wind-down: `console-tui` constructs none of the valve command
types; the palette recognizes only `drain`). Driving a valve from the TUI fails
on contact, which is the intended forcing function. Track D's build closes it.

The right-hand (by-design-CLI) list is provisional and subject to maintainer
revision — if the maintainer rules any of it SHOULD be TUI-drivable, it moves to
the hole list.

## WIND-DOWN STATE — 2026-07-12 (resume from here in a fresh session)

Track A (repair the embedded golden-master → run I2) is mid-repair; Tracks B/C/D
pending; two doc PRs merged; two sub-agents were in flight at wind-down.
Everything below this section is prior context.

**Landed / in-flight this session:**
- **Embedded beads-client fix — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #489 credential precheck; PR #508 `connection.prefix` + `invoke`
  embedded-awareness; releases 0.17.15 / 0.17.23).
- **Golden-master staleness repair — UNVERIFIED, on branch
  `fix-golden-master-custom-statuses` (orchestrator, commit `a102190`, NO PR
  yet).** Adds gate #4 (register custom statuses after `bd init`) + gate #5 (seed
  the item as `ready` + read `--status ready`). **NEXT: run it live to verify**,
  from its worktree
  (`~/.worktrees/livespec-orchestrator-beads-fabro/fix-golden-master-custom-statuses`):
  `/usr/local/bin/with-livespec-env.sh -- bash orchestrator-image/acceptance-live-golden-master.sh --run --poll-attempts 80`.
  Open question the run answers: does a `ready` item clear the
  Definition-of-Ready ledger checks, or need more fields? If green → open+merge
  that PR, then the autonomous I2. If a gate #6 appears → keep going (maintainer:
  "whatever it takes").
- **Console TUI docs — MERGED** (`livespec-console-beads-fabro` PR #165 TUI
  guide; core PR #1077 README blurb + the SESSION UPDATE below).
- **TUI usability PR — IN FLIGHT at wind-down** (delegated console sub-agent:
  `just tui` recipe + `?` help overlay + ↑/↓ focus-nav). Check
  `livespec-console-beads-fabro` for its PR and merge if green. (Maintainer's
  live-test "pathing error" on run 2 = a copy-paste hyphen-split of the long
  binary name, not a bug; `just tui` fixes it.)

**Embedded golden-master gate ledger (context):** credential precheck ✓(#489) ·
`connection.prefix` ✓(#508) · `invoke` embedded ✓(#508) · custom-statuses
✓(branch `a102190`, unverified) · seed-as-ready ✓(branch `a102190`, unverified) ·
[next live run reveals a gate #6 if any].

**Open worktrees:** `fix-golden-master-custom-statuses` (orch — the live repair,
keep) and `docs-plan-handoff-winddown` (core — this update). The stale
`fix-embedded-ledger-credential-precheck` (orch, merged branch + now-redundant
uncommitted edits) can be reaped.

**Resume order (A→D→C→B, maintainer-chosen):**
1. Verify + land the golden-master repair (branch above) → live golden-master GREEN.
2. **Autonomous I2:** parameterize the golden-master with `--mode autonomous` +
   the VALIDATED human-only plant (`bd config set status.custom …`; `bd update
   <id> --status acceptance`; `bd update <id> --add-label acceptance:human-only`);
   assert ready→`done` + `autonomous-decision` audit records + the human-only
   item rests in `Lane::Acceptance`; then the console observe/reflect leg + the
   MAINTAINER's TUI acceptance (the human core of I2 "done").
3. Track D (wire TUI valves), Track C (console release-binary publishing via
   release-please + CI), Track B (golden-master anti-rot cadence: daily +
   pre-release blocking gate, capped whole-test retry-backoff 1min→10min→fail).
   DELEGATE these per directive #2.

## SESSION UPDATE — 2026-07-12 (driver `autonomous-mode`): I2 unblocking + new deliverables

**"ONLY I2 remains" is superseded.** Driving I2 live surfaced that the
disposable-tenant factory substrate had bit-rotted and that the console is not
yet a real (downloadable) deliverable. The MVP now carries FOUR tracked
additions (A–D). **Landed this session:**
- **Orchestrator credential precheck fix — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #489, release 0.17.15): the dispatcher bootstrap demanded
  `BEADS_DOLT_PASSWORD` even for EMBEDDED ledgers (which need none); now derived
  from `.beads/config.yaml` `dolt.mode: server`. Exercised live.
- **Orchestrator test-hermeticity fixes — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #488): two non-hermetic tests that reddened local `just check` on a
  dogfooding host (codex-resolution reading real `~/.codex`; a reflector line
  needing `claude` absent).
- **Console TUI docs — IN FLIGHT**: console README "Running the console (TUI)"
  guide (`livespec-console-beads-fabro` PR #165, up); main livespec README
  console blurb (the PR carrying this update).

### Track A — repair the embedded factory substrate (I2 prerequisite)
The core beads CLIENT dropped embedded-ledger support (accumulated
server-mode-assuming gates). Gates found in the dispatch path:
1. bootstrap credential precheck — **FIXED** (`livespec-orchestrator-beads-fabro` PR #489).
2. `resolve_store_config` requires `connection.prefix`, absent from the
   e2e-skeleton — **FIXED in a worktree, NOT yet committed/PR'd.** The 2
   recoverable edits: `orchestrator-image/e2e-skeleton/.livespec.jsonc`
   connection block gains `"prefix": "e2egreet"`; `acceptance-live-golden-master.sh`
   `bd init --prefix "e2egreet"` (was `"${rand}greet"`).
3. `_beads_client_shell.py::invoke` demands `BEADS_DOLT_PASSWORD` AND asserts a
   SERVER tenant identity match — both meaningless for embedded — **PENDING.**
Maintainer chose **option 1 (holistic)**: make the beads client embedded-aware
(embedded → skip the password + tenant-match; server path untouched), with the
fix's own ritual tests. Capped per gate: if fixing #3 reveals yet another
embedded gate, reassess vs. the server-tenant-pivot alternative.

### Track B — anti-rot cadence for the live golden-master (NEW, maintainer-directed)
The live golden-master (`acceptance-live-golden-master.yml`) is NON-BLOCKING +
operator-triggered only, so it rotted silently while the dispatcher's
credential/config layers evolved (the per-PR `acceptance` check is a HERMETIC
mirror that never exercised the embedded path). Close the gating hole with
BOTH a **daily** scheduled run that REDS master on failure AND a **pre-release
blocking gate** — engineered against transient live-infra flake: tight inner
retries around infra calls PLUS a capped whole-test retry-with-backoff (fail →
wait 1 min → retry → fail → wait 10 min → retry → then real failure). Red ONLY
on a genuine dispatch/merge/greeting-assert failure. Token burn per run is
small.

### Track C — console release-binary publishing (NEW, maintainer-directed)
`livespec-console-beads-fabro` has **no release pipeline**: no release-please,
no CI build-and-attach job, zero published releases — the only way to get it is
a source build. Per the maintainer, "it's not a real deliverable until it's
published on the version schedule via release-please." Deliverable: add
release-please + a CI job that cross-compiles the standalone binary and
attaches it to each GitHub Release on the version schedule. **Gates the MVP
being a REAL deliverable** (the operator must download the cockpit, not compile
Rust). File as a console-repo epic.

### Track D — wire the operator valves into the TUI (NEW, verified gap)
The per-item valves (approve / accept / reject / set-admission / set-acceptance)
are server-side command handlers but are NOT bound to any TUI key (verified:
`console-tui` constructs none of the valve command types; the command palette
recognizes only `drain`). I2's DoD requires the truly-unresolvable item to
surface in-TUI as an **actionable** needs-attention item; today it surfaces
(flagged + shown in Detail) but is not TUI-actionable. Likely an additional MVP
deliverable — confirm scope with the maintainer.

### Next-session resume order
1. Finish Track A: commit the `connection.prefix` fix + land the beads-client
   `invoke` embedded fix (option 1), then run the live golden-master GREEN
   (from a checkout carrying the fixes — the dispatcher runs from the
   bind-mounted repo, no image rebuild).
2. Build + run the autonomous I2 on the now-green substrate (embedded tenant +
   `--mode autonomous` + the VALIDATED human-only plant: `bd config set
   status.custom "..."`, `bd update <id> --status acceptance`, `bd update <id>
   --add-label acceptance:human-only`). Assert ready→done + `autonomous-decision`
   audit records + the human-only item rests in `Lane::Acceptance`.
3. Land Tracks B, C, D (each its own PR/epic). Track D likely blocks the full
   I2 "actionable in-TUI" DoD; Track C blocks "real deliverable."
4. The MAINTAINER's TUI acceptance is the human core of I2 "done."

Everything below predates this update; trust this section for current state.

---

**Status: C3 COMPLETE (2026-07-11) — ONLY I2 (end-to-end live exercise = MVP
"done") REMAINS. Step 0 + O1 + C1 ratified; O2 (orchestrator engine, 4/4)
COMPLETE; C2 (console command foundation, 5/5) COMPLETE; persistence-seam
RATIFIED to console v018; and now C3 (console autonomous feature — 3/3 slices
`rt4.1/.2/.3` + folded finding `d6o`) COMPLETE, all merged, post-merge-reviewed
SOUND, console master green (`e749a6c`). The maintainer CHECKPOINTED AGAIN at
C3-complete (2026-07-11) before I2 — the maintainer-gated MVP acceptance. See
"## Build phase progress" (the C3 record) + "## Remaining to MVP" (the I2 plan +
recommendation) below for the next session's resume pointers.** The Step-0
fable-review loop exited (round-6 NOTHING-BLOCKING + maintainer certification, in
the Loop state below); the driver dispatched O1 and C1 as scoped subagents and
drove each through propose-change → independent read-only Fable review → revise.

**Ratification record (2026-07-10):**
- **O1 → orchestrator v033 (RATIFIED).** Two propose-changes (irreducible human
  touchpoints; arming/audit contract): filed by the delegate (orchestrator
  PR #415), reconciled by the driver toward a fuller parallel maintainer/Fable
  draft (folded amendments K/L/O + the Scenario-33 routine qualifier; PR #416),
  Fable-reviewed NOTHING-BLOCKING, revised accept/accept to v033 (PR #417).
  **Arming/audit contract FROZEN → overall I1 SATISFIED** → console C3 and
  orchestrator O2 unblocked. On master: `drive --mode autonomous`=0;
  `loop --mode autonomous` is the mode surface; the design-human-gated set +
  `human-only` carve-out + single-persistent-permission key are live.
- **C1 → console v017 (RATIFIED).** Two propose-changes (citation-currency;
  autonomous-resolution delegation): filed (console PR #147), Fable-reviewed
  NOTHING-BLOCKING, revised accept/accept to v017 (PR #149) with a
  behavioral-coverage lockstep co-edit (process note below). MAIN ratification
  done; the persistence-seam amendment stays DEFERRED but is now I1-unblocked.
  `rt4` version pointer refreshed v013→v016.
- Reaped two stale/absorbed branches: orchestrator
  `o1-autonomous-mode-touchpoints-arming` (absorbed parallel draft; source at
  git 1f25529 + driver scratchpad), console `autonomous-mode-c1-spec-currency`
  (empty stale).

**PROCESS NOTE (carry forward) — console behavioral-coverage co-edit.** The
console repo's coverage gate binds normative-CLAUSE gap-ids (content-hashes of
each MUST/SHOULD line) to scenarios — NOT H2 names. ANY console spec revise that
adds/removes/rewords a normative clause REQUIRES a lockstep co-edit
(`tests/heading-coverage.json` clause-gap-id rebinding + the
`crates/console-spec-check/src/tests.rs` ground-truth count refresh) even with
zero `## ` H2 changes — the console analogue of core's H2 heading-coverage
co-edit (precedent: console v016 CN1 + v014). Future console propose-changes
should carry this in their `resulting_files`.

## Build phase progress (2026-07-11 — driver session `autonomous-mode`)

The maintainer resumed the build phase 2026-07-11. Both grooming cuts were
drafted by scoped read-only delegates, ACCEPTED by the maintainer, and FILED:

- **Orchestrator `bd-ib-82a` → 4 slices** (`.1` two-factor arm / `.2` per-decision
  audit record + published read surface / `.3` two-valve collapse / `.4` in-band
  LLM `needs-human` resolve-or-escalate). Epic re-based v025→v033, surface
  `loop --mode autonomous`. Backstop for the spec-change tier = option (a): a
  conservative guard on the existing `spec_commitment_hint` signal, NO new field.
- **Console `pke3y3` → 4 slices** (`.1` shared `drive` port + approve / `.2`
  accept+reject / `.3` set-admission / `.4` set-acceptance), re-based onto the
  v017 valve model; the 4 still-contract factory/spec commands split to new
  sibling `8aw`; the 3 v014-retired commands dropped. All five commands ride ONE
  shared `drive` port + a single `work_item.action.*` event family (thin console
  validation; orchestrator is state-legality authority). `mb64bv` was already
  landed (rename in `3eca905`) → CLOSED as already-fixed; con-S4's supposed block
  was illusory.

**Merge posture (maintainer-approved 2026-07-11): auto-merge-on-green +
post-merge review.** The approved intent is NO pre-merge gate: a green PR merges
and the driver reviews AFTER, reverting only on a real problem (revert is
driver-held). CORRECTION (found during C3): the
`livespec-console-beads-fabro` repo has NO auto-merge bot and NO `livespec-pr-bot`
(only `ci.yml` + `bump-pin-from-dispatch.yml`); its green PRs merge by the
delegate/driver running `gh pr merge --rebase` (recent PRs showed `autoMerge=yes`
only because someone's token ENABLED auto-merge — the `mergedBy: thewoolleyman`
just reflects who enabled it). So under the approved posture the merger IS the
delegate/driver, not a bot; each C3 slice delegate rebase-merged its own green PR
and the driver post-merge-reviewed the diff on master. Do NOT wait on a
nonexistent bot. Full worktree/TDD/`just check` discipline unchanged; delegates
halt-and-report on any red.

**O2 (orchestrator engine): COMPLETE.** All four `bd-ib-82a` slices merged,
reviewed sound, closed; master CI green; releases 0.14.0–0.17.0. orch-S4's
in-band LLM `needs-human` stage (`resolution_resolves`) fails safe toward
escalation on every branch (not-confident / design-gated / `human-only`), the
production resolver fail-safes to escalate on any subprocess/parse error, and
not-armed behavior is exactly the pre-existing bounce.

**C2 (console command foundation): COMPLETE — 5/5 commands merged** (con-S1
drive-port+approve / con-S2 accept+reject / con-S3 set-admission / con-S4
set-acceptance, which extended read-side `AcceptancePolicy` to
`{ai-only,human-only,ai-then-human}`). All reviewed sound; Scenario 11 fully
bound; `pke3y3` epic + all children closed. One follow-up FILED for C3:
`livespec-console-beads-fabro-d6o` — `requires_attention_from_lane`
(`console-application/src/lib.rs`) flags `AiThenHuman` in the Acceptance lane but
NOT `HumanOnly`; VERIFY where a `human-only` item lands and, if the Acceptance
lane, extend the arm (latent until C3 wires policy-setting into the TUI).

**Persistence-seam amendment: RATIFIED → console v018** (`e741af8`). Dropped the
console's own `autonomous_mode.enabled` persistence clause; the console now
derives/reflects the mode from — and writes it through — the orchestrator's
single `dispatcher.autonomous_mode` permission key (per O1 v033). Independent
Fable review = NO-BLOCKERS (gap-ids + counts verified computationally); the
revise folded two Fable advisories (`console-spec-check` total 123→122 + comment;
Scenario-9 `reason` reword). This CLOSES the last residual of cross-repo risk #1
(persistence-model seam).

**Orchestrator repo hygiene: one flaky test fixed (parallel, unrelated).**
`test_receiver_oversized_body_is_bad_request` (OTLP receiver) was root-caused as a
REAL socket RST race (a hard close with an unread request body emits RST not FIN)
and fixed with a lingering close + a bounded/timed/fail-open drain (PR #448,
release 0.17.2), verified by 325 repeated runs — not `@flaky`/skipped.

**Operational learnings (carry forward):**
- Dispatching build executors as context-inheriting FORKS spikes tokens (a fork
  inherits the parent delegate's large context) and hit a session rate limit
  mid-build. Prefer LIGHT self-contained general-purpose agents for executors.
- An idle subagent does NOT self-wake on external CI completion — the driver (or
  the delegate's own Monitor) must watch master CI and nudge/close the slice.
- Concurrent slices editing the same file (orch-S3/S4 both touched
  `dispatcher.py`) need the second-to-merge to rebase-own-branch +
  `--force-with-lease`; the bot will NOT auto-merge a CONFLICTING PR. Sequence,
  or accept the rebase on the second.
- Two session rate-limit interruptions cost only build/coordination time — no
  landed work was lost (committed slices + unpushed local branches all recovered;
  a merged-but-not-yet-closed slice is normal serialized-close lag, not failure).

## Remaining to MVP — I2 only (C3 is DONE)

**C3 — console autonomous feature: COMPLETE (2026-07-11).** Groomed
(maintainer-approved 3-slice cut) from epic `rt4` into `rt4.1/.2/.3`; all merged,
post-merge-reviewed SOUND, console master green (`e749a6c`); epic + all children +
folded finding `d6o` CLOSED:
- **`rt4.1` (console PR #160, `395fa87`)** — the Configuration context:
  `config.autonomous_mode_set` (confirmed-guard rejects an unconfirmed enable with
  NO effect — no port call, no key write, no audit event); the
  `factory.autonomous_mode_{enable,disable}_requested` commands +
  `LivespecJsoncArmingPort` that writes the orchestrator `dispatcher.autonomous_mode`
  key DIRECTLY in the consumer `.livespec.jsonc` (declarative shared config;
  comment-preserving minimal edit); the `config.autonomous_mode.{enabled,disabled}`
  audit events; `read_autonomous_mode_from_jsonc` derive-on-read (absent = disabled).
  `not_wired` honesty, never fabricated success.
- **`rt4.2` (console PR #162, `e749a6c`)** — the TUI surface: autonomous toggle,
  "dangerous / use with caution" label, type-to-confirm modal (enable only; disable
  no-confirm; submits `confirmed:true`), header mode indicator DERIVED-and-reflected
  (never owned).
- **`rt4.3` (console PR #161, `747a81c`)** — the autonomous RUN: the factory-drain
  launcher passes `--mode autonomous` to `loop` (re-derived per drain from the key;
  NOT `drive`); observe/reflect via `JournalAutonomousDecisionsPort` mirroring the
  orchestrator's published `read_autonomous_decisions`, reflecting each
  auto-resolution through the console's OWN command+outcome-event path
  (`factory.autonomous_decision_reflected` + `attention_item.resolved`; idempotent;
  NO console-side resolver, no double-resolution); truly-unresolvable left in the
  inbox; folded `d6o` (VERIFIED: a `human-only` acceptance item rests in
  `Lane::Acceptance`, so `requires_attention_from_lane`'s Acceptance arm extended to
  `AiThenHuman | HumanOnly`, AiOnly unflagged).

**I2 — end-to-end live exercise (MVP "done"): the SOLE remaining step;
maintainer-gated.** Gate: C3 ✓ + O2 ✓ AND the design.md §9 operability conditions —
BOTH now MET: the cost ceiling is real and fail-closed (`cost_gate_decision`, LIVE in
the orchestrator), and the failure-surfacing path is C3's observe/reflect/
needs-attention. On a REAL tenant: flip autonomous mode ON from the TUI → the
orchestrator engine drives ready work to `done` unattended → the console
observes/reflects each auto-resolution → a truly-unresolvable item surfaces in-TUI as
an actionable needs-attention item. "Done means rolled out and exercised live" — this
live evidence IS the MVP acceptance.

**RECOMMENDED I2 approach (driver-drafted; the maintainer CHECKPOINTED at C3-complete
2026-07-11 BEFORE choosing an I2 approach — so this is a recommendation, not a
decision):** run I2's truly-unresolvable plant at the LEDGER LEVEL — seed a
`human-only` acceptance item, which the engine will NOT collapse (deliberate gate), so
it rests in `Lane::Acceptance` and the console surfaces it as needs-attention via the
`d6o` fix `rt4.3` shipped. This AVOIDS the in-loop-park path that orchestrator bug
`bd-ib-18r` breaks (`bd-ib-18r` + `bd-ib-6vu` BOTH still OPEN/backlog as of 2026-07-11)
— no park, so the bug never bites. The alternative is to triage `bd-ib-18r`
(blocked-as-first-class + ledger write-back on park) first, then I2 with a genuine
mid-run park — more faithful to long unattended runs but pulls engine bug-fixing into
the MVP critical path. `bd-ib-18r`/`bd-ib-6vu` affect LONG unattended runs, not the MVP
demonstration; keep them tracked follow-ups.

**I2 tenant (recommended target) — run on a DISPOSABLE `livespec-e2e-*` tenant, NOT a
fleet/production tenant.** I2 auto-drives ready work to `done`, so it MUST NOT consume a
real backlog. The `livespec-e2e-*` throwaway repos (in the disposable `livespec-e2e`
GitHub org) are genuine "real tenants" — real GitHub repo + real beads/Dolt tenant + real
Fabro factory dispatch — but disposable, which is exactly what "done means exercised live
on a real tenant" needs without touching production. They are created by the dark-factory
acceptance harness `livespec-orchestrator-beads-fabro/orchestrator-image/acceptance-live-golden-master.sh`
(host-side create/clone/delete use `LIVESPEC_E2E_GITHUB_TOKEN`, injected by the 1Password
env wrapper). Sweep orphans with the fail-safe reaper
`orchestrator-image/reap-e2e-repos.sh` (or `just reap-e2e-repos`), run ONLY at boundaries
(session-start / post-confirmed-merge / deliberate teardown), NEVER mid-dispatch. CAVEAT:
provisioning a Fabro GitHub-App installation over the e2e throwaway repos is a HUMAN act in
GitHub org settings, NOT factory-executable (orchestrator `bd-ib-w4iaaf`) — confirm that
installation exists before the I2 run, or surface it to the maintainer. Running I2 against
a live fleet/production tenant is an outward-facing, side-effecting act; get explicit
maintainer authorization for the specific tenant before any non-disposable target.

**SEAM to assert at I2 (flagged by the `rt4.3` delegate):** if the needs-attention
surface lags the ledger (still lists an item the engine already auto-resolved), ingest
re-appears it and idempotent reflect won't re-resolve it; in practice the engine updates
the ledger → the surface drops it, and reflect runs AFTER ingest so it wins on first
sighting. I2 may want to assert surface/ledger convergence.

**Checkpoint note (2026-07-11):** the build phase ran end-to-end in one long
driver session through two token-limit interruptions with zero lost work; the
maintainer chose to checkpoint here so C3/I2 get a fresh full-context session. All
delegates (`console-autonomous-mode`, `orchestrator-autonomous-mode`) and their
worktrees are wound down; both sibling repos are clean on master and green.

The Step-0 loop rules are kept below for the historical record: each round, a
FRESH Fable session reviewed ALL THREE plans AND FIXED every problem it found
(via worktree → PR → merge); a session that landed fixes could not clear the
gate (no self-certification) — the clean verdict always came from the NEXT fresh
session.

**Loop state:**
- Round 1 (2026-07-10, Fable session `livespec-autonomous-mode`): Step-0
  validation of the ORIGINAL plans → NO-BLOCKERS with 9 observations
  (`research/step0-fable-verdict.md`); the SAME session then FIXED every
  finding in all three plans (orchestrator PR #395, console PR #134, core
  PRs #1000 + this one) and wrote
  `research/fable-revising-session-self-assessment.md` — which does NOT
  clear the gate, because reviser and reviewer were the same session.
- Round 2 (2026-07-10, fresh Fable session, this repo's session
  `livespec-autonomous-mode` pane): first fresh-session review-AND-FIX over the
  REVISED plans → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-2.md`; core PR #1014, console PR #141,
  orchestrator PR #404). All round-1 revisions re-verified against live state;
  fixes were currency + internal-soundness precision (stale `orchestrate run`
  in core C2 step text; C2-gate two-phase-C1 ambiguity; fabro-token-refresh
  state moved; mb64bv type; O2 done-surface pin). Because fixes landed, this
  round does NOT clear the gate.
- Round 3 (2026-07-10, fresh Fable session): second fresh-session
  review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-3.md`; orchestrator PR #410 + the core PR
  carrying that record). Every rounds-1-2 revision re-verified against live
  state; no structural defect anywhere; the two fixes were small currency/
  precision (stale "PR #136 cleanup" pending-decision in core §9 +
  orchestrator §5 — the validation vehicle auto-merged 2026-07-10;
  `livespec-zs22.6` is a closed task, not an epic). The CONSOLE plan passed
  clean — its first no-fix round. Because fixes landed, this round does NOT
  clear the gate.
- Round 4 (2026-07-10, fresh Fable session spawned by the driver): third
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-4.md`; fixes in core PR #1022, record +
  loop state in core PR #1023). Every rounds-1-3
  revision re-verified against live state; the two fixes were small
  consistency/currency, both in the overall plan (design §7 graph missing
  the `I1 ─► C1 persistence-seam` edge its own prose asserts; stale
  "revised rounds 1-2" Read-first annotation). BOTH sibling plans passed
  clean (console's second consecutive clean round; orchestrator's first).
  Because fixes landed, this round does NOT clear the gate.
- Round 5 (2026-07-10, fresh Fable session spawned by the driver): fourth
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-5.md`; fix in core PR #1024, record + loop
  state in the core PR carrying this bullet). One currency fix, in the
  overall plan's own Loop state (the round-4 bullet omitted its
  record-carrying PR #1023). BOTH sibling plans passed clean again
  (console's third consecutive clean round; orchestrator's second).
  Because a fix landed, this round does NOT clear the gate.
- Round 6 (2026-07-10, fresh Fable session spawned by the driver): fifth
  fresh-session review → **NOTHING-BLOCKING** (verdict:
  `research/fable-review-round-6.md`; a purely read-only round — no fix
  was warranted, none was landed, so the no-self-certification rule is
  satisfied). Every load-bearing claim in all three plans re-verified
  first-hand as true; both sibling plans clean for the fourth/third
  consecutive round (console/orchestrator); the convergence trajectory
  (9 obs → 6 → 2 → 2 → 1 fixes) reaches zero. The verdict affirmatively
  certifies all three plans SOLID, EXECUTABLE, and MVP-MEETING.
- Maintainer certification: **GIVEN 2026-07-10** — the maintainer
  certified round 6's NOTHING-BLOCKING verdict in the driver session
  (recorded here by the driver). THE STEP-0 LOOP IS EXITED; C1/O1
  dispatch is unblocked (Next actions, step 4). → Dispatching C1 and O1
  in parallel is the next action.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the driver + per-repo delegate-context delegation model (design.md §8).
livespec core authors no product code here.

## Read first
1. This file, then `design.md` in this directory (the full plan).
2. For the review loop: `research/fable-review-brief.md` (the brief each
   fresh reviewer runs), then the prior rounds
   (`research/step0-fable-verdict.md`,
   `research/fable-revising-session-self-assessment.md`,
   `research/fable-review-round-N.md` as they accumulate).
3. The two sibling repo plans this coordinates (both carry the accumulated
   review-round findings in their own step texts, kept current across the
   review-loop rounds):
   - `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
   - `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

## Goal (one line)
A human flips per-repo **full autonomous mode** from the
`livespec-console-beads-fabro` **TUI** (GUI out of scope) and the Beads/Dolt +
Fabro factory drives ready work to `done` unattended — LLM-resolving the human
gates, auditing every decision, surfacing only the truly-unresolvable back to the
operator.

## The spine (see design.md §7 for the full step catalogue)
```
Step 0 (fable-review LOOP — HARD GATE) ✓ MET 2026-07-10 (round 6 NOTHING-BLOCKING + maintainer certification)
  status (2026-07-11): O1 ✓ (orch v033, I1) · C1 ✓ (console v017) · O2 ✓ · C2 ✓ · persistence-seam ✓ (console v018) · C3 ✓ (rt4.1/.2/.3 + d6o; console master e749a6c) · ONLY I2 remains (maintainer-gated).
  ├─ Console track (delegate console-autonomous-mode):  C1 spec fixes ✓ ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (delegate orchestrator-autonomous-mode): O1 spec fixes + arming contract ✓ ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ✓ ─► C3 (and C1's persistence-seam portion, now I1-unblocked)
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel — but ONLY after the Step-0
loop exits. Contract-first: O1 publishes the arming/audit contract before C3
builds on it.

## Next actions (exact steps for a new session — the BUILD phase)

Step 0 + O1 + C1(main) are DONE (Ratification record at top). The build phase is
COMPLETE (see "## Build phase progress"): **step 1 (O2) COMPLETE; step 2 (C2)
COMPLETE; step 3 (persistence-seam) RATIFIED to v018.** The ONLY live remaining
steps are **4 (C3)** and **5 (I2)** — the fresh session's work. Steps 1–3 below
are kept as the executed record; steps 4–6 are the forward work:

1. **O2 — implement the orchestrator engine (`bd-ib-82a`).** FIRST groom
   `bd-ib-82a` into dependency-layered slices — grooming is a MAINTAINER-OWNED
   cut (`/livespec-orchestrator-beads-fabro:groom`; the front-end drafts, the
   maintainer owns the acceptance), so set it up FOR the maintainer, do NOT
   auto-slice. Then build: the `dispatcher.autonomous_mode` key + `loop --mode
   autonomous` gate-collapse + the NEW LLM `needs-human` resolution stage +
   truly-unresolvable escalation + per-decision audit journal, composing the
   shipped valve/escalation/cost-gate machinery. Sequence the auto-admit slice
   around `livespec-nrdk` (factory-safe admission gate; design.md §9). Gate: O1
   (met). Refresh `bd-ib-82a`'s stale v025 spec pointer to v033 as it opens.
2. **C2 — console command foundation.** Add the five `work_item.*` valve/policy
   `CommandType` variants + handlers + a port onto the orchestrator's published
   `drive` action surface + the Scenario-11 test (TDD, console Red-Green ritual).
   Folds `pke3y3` (regroom against the current valve model — MAINTAINER-OWNED
   cut). Gate: C1's MAIN ratification (met). Runs concurrently with O2.
3. **Persistence-seam amendment (console, now I1-unblocked).** File the small
   console propose-change that drops/derives the console's own
   `livespec-console-beads-fabro.autonomous_mode.enabled` block so ONLY the
   orchestrator's `dispatcher.autonomous_mode` key persists (the C1 persistence
   portion deferred to I1; O1 froze the arming contract at v033). Route
   propose-change → independent read-only Fable review → revise, and per the
   PROCESS NOTE at top carry the `tests/heading-coverage.json` clause-rebinding +
   `console-spec-check` ground-truth co-edit in `resulting_files`. Gates C3.
4. **C3 — console autonomous feature.** Gate: C1 + C2 + I1 (I1 met; needs C2 +
   the persistence-seam amendment). Build `config.autonomous_mode_set` +
   `.livespec.jsonc` persistence/audit + `factory.autonomous_mode_*_requested` +
   TUI toggle/confirm-modal/dangerous-label/header + the Scenario-10
   enable/observe/reflect/escalate loop (NOT a console-side resolver — the engine
   owns resolution, per the ratified delegation re-scope).
5. **I2 — end-to-end live exercise (MVP "done").** Gate: C3 + O2 AND the
   design.md §9 operability conditions (verified cost ceiling + a real
   failure-surfacing path — note orchestrator bug `bd-ib-18r`: an in-loop park
   today orphans without ledger write-back, so I2's truly-unresolvable plant
   must be ledger-level or `bd-ib-18r` triaged first).
6. Every spec change routes propose-change → independent read-only Fable review →
   revise; core H2 changes co-edit `tests/heading-coverage.json`; CONSOLE
   normative-clause changes carry the clause-rebinding co-edit (PROCESS NOTE).
   Ratification is DRIVER-held: a delegate FILES + halts; the driver runs the
   Fable review and dispatches the revise on a NO-BLOCKERS verdict.

## Delegation model (design.md §8)
Driver + per-repo delegate contexts; the driver dispatches each delegate as a
scoped subagent (NOT a tmux pane — that mechanism is retired). Delegate contexts
are named for their repo so cross-plan status references resolve.
- Driver: Claude session `autonomous-mode` (cwd `/data/projects/livespec`) — owns
  the plan, gates, dispatch, synthesis, and the ratification review gate.
- Delegate `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.
- Reviewer: a FRESH Fable session per round for the Step-0 loop (review-AND-FIX —
  it lands its own fixes; no continuity with sessions whose fixes it reviews).
  For per-step ratification (C1/O1 etc.), the DRIVER spawns the read-only
  independent Fable review after a delegate files its propose-change.

## Ledger items in play (per repo tenant)
> **Currency note (2026-07-11):** several descriptions below are superseded by
> "## Build phase progress" — `bd-ib-82a` is groomed into `.1`–`.4` and CLOSED
> (O2 complete); `pke3y3` is re-based onto the v017 valve model (`.1`–`.4`, con-S4
> in flight), NOT "7 unimplemented commands"; the factory/spec split lives in new
> sibling `8aw`; `mb64bv` is CLOSED (already-fixed via `3eca905`). Trust the Build
> phase progress section for current slice/close state.

- Core: `livespec-bvuy4w` — this thread's epic anchor (driver filed it
  2026-07-10 via the `capture-work-item` operation, closing the round-2
  finding; epic-shaped → `backlog` per the intake Definition-of-Ready
  checklist; edges: `livespec-nrdk` blocks, `livespec-0jxs` related — bd
  refuses an epic→task `blocks` edge by design, so the task dependency
  carries a `related` edge instead).
- Console: `rt4` (operator surface → C3; version pointer refreshed v013→v016 during C1, but its description substance still reads pre-re-scope — refresh at C3 grooming), `pke3y3` (epic, "7 unimplemented commands" — regroom + split for C2, maintainer-owned cut), `ipi` (attention-stream TUI migration), `mb64bv` (chore: backlog-bounce vocab rename — verify the rename target against the orchestrator's actual journal field `bounced_to_regroom` before landing).
- Orchestrator: `bd-ib-82a` (the engine → O2; stale v025 pointer — refresh to v033 when O2 opens).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness); orchestrator bugs `bd-ib-18r` / `bd-ib-6vu` (unattended-run robustness — sequence around).

## Key cross-repo risks (design.md §6) — ALL THREE now RESOLVED by O1/C1 ratification
1. Persistence-model seam: RESOLVED at O1 v033 — the arming contract pins the
   orchestrator `dispatcher.autonomous_mode` key as the single persistent
   permission, the console factory-drain path as launcher, and `loop` (not
   `drive`) as the `--mode autonomous` surface. (Residual: the console still
   drops/derives its own duplicate block — the I1-unblocked persistence-seam
   amendment, Next actions step 3.)
2. Division of resolution: RESOLVED at C1 v017 — the Scenario-10 re-scope makes
   the engine own ALL gate resolution; the console enables/observes/reflects; the
   double-resolution race is explicitly killed (console-side resolver deferred).
3. Vocab drift: RESOLVED at C1 v017 — all four citation sites swept
   (`orchestrate`/`orchestrate run` → `drive`; lane-vocab ownership → orchestrator).

## Next action
**C3 COMPLETE (2026-07-11); the maintainer CHECKPOINTED at C3-complete before I2.**
All of Step 0, O1 (orch v033), C1 (console v017), O2 (`bd-ib-82a`), C2 (`pke3y3`),
the persistence-seam (console v018), and C3 (`rt4` → `rt4.1/.2/.3` + `d6o`) are
landed, reviewed sound, and green. The SOLE remaining step is **I2 — the end-to-end
live exercise on a real tenant = MVP "done"** (maintainer-gated; needs the maintainer
for the live acceptance). Its gate (C3 + O2 + §9 operability — cost ceiling +
failure-surfacing path) is MET; the ONE open decision is the
truly-unresolvable-plant approach — see "## Remaining to MVP" for the driver's
RECOMMENDATION (a ledger-level `human-only`-acceptance plant that sidesteps still-open
orchestrator bug `bd-ib-18r`) and the alternative (triage `bd-ib-18r` first). Merge
posture: green PRs merge by the delegate/driver via `gh pr merge --rebase` (the console
repo has NO auto-merge bot — see the corrected merge-posture note above) + driver
post-merge review. All C3 delegates + worktrees are wound down; core, console, and
orchestrator are clean on master and green.

## Pointers
- Ledger read (per tenant): `bd list --json` (or `bd show <id> --json`) run from
  inside the repo, via the credential wrapper
  `/usr/local/bin/with-livespec-env.sh -- bd …`; prefer it over the shared
  `list_work_items.py` cache path, which can mis-resolve the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
