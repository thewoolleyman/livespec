# Dark-factory operability preconditions (livespec-0jxs)

**STATUS: DRAFT — pending user ratification.** Design pass only; no
work-items are filed by this document. The orchestrator files items
from the §"Proposed work-item one-liners" section after ratification.

Work-item: **livespec-0jxs** (design pass; epic `livespec-4moata`,
wave W6). Authored 2026-06-13. The question this answers, verbatim
from the item: at gate-pass the Dispatcher runs unattended, but today
there is NO failure-notification path, NO escalation, NO telemetry
shipping, NO verified cost ceiling — decide whether to add minimal
operability as an explicit cutover precondition or consciously accept
flying blind in writing; and enumerate the duties retiring
`/livespec-orchestrate` (livespec `a8bb`) would orphan, assigning each
a home BEFORE the skill is deleted.

## Recommendation (up front)

**ADOPT the minimal-operability trio as an explicit cutover
precondition. Do NOT fly blind.** Gate-pass declaration (the streak
rule per `livespec-iaut`) and the operability preconditions are BOTH
required before `/livespec-orchestrate` retires and the Dispatcher
runs unattended:

> **Gate-pass = streak rule satisfied (per iaut) AND the operability
> trio verified live.**

The trio, cheapest-viable-first:

| # | Precondition | Verified state today | Blocked on user? |
|---|---|---|---|
| (a) | Failure-notification path | NOTHING pushes; available mechanism (ntfy) verified live on this host | No |
| (b) | Spend ceiling (fail-closed) | NO cap anywhere; `total_usd_micros` is **null on all 29 fabro runs** (verified 2026-06-13) | No — but has a verification prerequisite |
| (c) | Telemetry shipping (journal → Honeycomb) | Local OTLP capture accretes; nothing ships | Partially — 29f.3 keys |

The cost asymmetry decides this: each leg is hours of work, while the
failure mode it guards is unbounded — a single dispatch can burn up to
54,000 s (15 h) of sandbox wall-clock with retries
(`_dispatcher_engine.py` `_FABRO_TIMEOUT_SECONDS`: implement
2 × 14,400 s + janitor 3 × 3,600 s + fix 2 × 3,600 s + pr 2 × 1,800 s)
and today NOBODY is told it happened and NO ledger of what it cost
exists. "Consciously accept flying blind" would mean accepting
silent unbounded spend with silent failure on an unattended loop —
rejected.

Premise note (per the verify-premises discipline): the item text says
the gate "sits at streak 3/10". At authoring time the session log
records streak 6 (smc, 90k, 7dro, lta, 7us.4, ay2 across 4 repos),
pending the `livespec-iaut` ruling on whether the tpu venue false-red
resets it. Neither number changes this design — the preconditions bind
at gate-pass declaration whenever it comes.

## Leg (a) — failure-notification path

**What exists today.** The Dispatcher's only outputs are: the
append-only JSONL journal (`_dispatcher_io.JournalFile`), the stdout
summary from `_emit_outcomes`, and the process exit code (0 iff all
outcomes green). All three are pull-only: if no human is watching the
terminal or tailing the journal, a `failed` outcome — or worse, a
`blocked` outcome parked indefinitely at the in-loop human gate
waiting for `fabro attach` — is invisible. The reflection-gate design
(impl-beads `research/loop-reflection-gate/best-practices-and-design.md`
§5.3) routes findings into the loop summary and the ledger, which are
also pull-only surfaces.

**What's available on this host (surveyed).**

- **ntfy — verified live.** `/data/projects/claude-code-ntfy` is a
  working Claude Code plugin posting to an ntfy topic via `curl`;
  `CLAUDE_NTFY_TOPIC` is already set in the user's
  `~/.claude/settings.json` (topic `vps-claude-ready-4267`) and the
  Stop/Notification hooks are in daily use. `curl` and `jq` are
  present. Push reaches the user's phone/desktop with zero new
  infrastructure.
- **Journal-tail triggers.** A watcher process tailing
  `tmp/fabro-dispatch-journal*.jsonl` for `outcome` records. Rejected
  as primary: it adds a daemon to babysit, and the Dispatcher already
  holds the terminal outcome in-hand at the exact moment it matters —
  watching a file to rediscover what the producer just knew is
  indirection without benefit.
- Email/Slack/PagerDuty: nothing configured on this host; all heavier
  than the need.

**Minimal viable mechanism (recommended).** A fail-open `_notify`
helper in the Dispatcher (impl-beads), one `curl` POST to an ntfy
topic, invoked at exactly four points:

1. terminal `failed` outcome (item id, stage, repo, PR number if any);
2. terminal `blocked` outcome (item id + the `fabro attach <run-id>`
   instruction — this is the human-gate escalation, today silent);
3. loop summary when any outcome is non-green (counts by status);
4. spend-cap breach (leg (b)).

Discipline pins:

- **Fail-open**: a failed/timed-out `curl` is journaled
  (`notify-error`) and never alters an outcome or exit code — same
  invariant as the reflection stage (reflection doc §6).
- **No secrets in payloads**: messages carry ids, stage names, repo
  names, run ids — NEVER `detail` blobs (journal detail tails are
  credential-adjacent free text per the reflection doc's §2.3
  observation).
- **Dedicated topic** (e.g. `vps-livespec-factory-<rand>`), separate
  from the interactive-session topic, so factory escalations are not
  drowned by session-ready pings. Config via env
  (`LIVESPEC_NTFY_TOPIC`), unset = silently disabled (the ntfy
  plugin's own pattern), set in the documented Dispatcher invocation.
- Loop-start + loop-end notifications included even when all-green:
  silence then becomes a detectable liveness signal for a crashed
  unattended loop (the cheapest watchdog that exists).

**Owning repo:** livespec-impl-beads (Dispatcher engine).

## Leg (b) — spend ceiling (fail-closed)

**What exists today.** Nothing. The only bounds on spend are
wall-clock: `_FABRO_TIMEOUT_SECONDS = 54000` per dispatch, the loop's
`--budget` (item count), and `--parallel`. No USD accounting, no cap,
no per-run or per-session ledger. Retry-once × 4 h implement attempts
mean a pathological item can burn the full 15 h envelope and the loop
will cheerfully pick the next item.

**Verified blocker — the cost signal is dark.** The item premise
"fabro exposes per-run `total_usd_micros` via `fabro ps -a --json`"
is true of the schema but NOT of the data: probed 2026-06-13 on this
host (fabro v0.254.0, 29 runs: 23 succeeded / 2 failed / 4 running),
`total_usd_micros` is **null on every run**, including all succeeded
ones. `fabro events <run> --json` on a succeeded run carries no
cost or token-usage fields either. The interim telemetry capture
(`livespec/tmp/capture_runtime_telemetry.py`) maps
`total_usd_micros → cost.usd` but emits it only when non-null — the
current spans file contains zero `cost.usd` attributes. The
reflection-gate doc's §4.3 noted the same ("null in sampled runs so
far"). **A spend ceiling grounded in a field that has never
populated is a paper ceiling.** Leg (b) therefore has two parts, in
order:

1. **Cost observability** — find out why `total_usd_micros` never
   populates (fabro version/config? does fabro require the agent
   runtime to report usage and the ACP adapter doesn't? is it
   computed only for certain workflow shapes?) and make SOME per-run
   cost signal real. Fallback source if fabro's field is a dead end:
   the agent runtime's own usage telemetry (Claude Code emits
   token-usage/cost metrics via its OTel support — the 29f.1 gap
   analysis covers this), which can be captured locally without the
   user-blocked Honeycomb keys.
2. **Cap enforcement in the Dispatcher**, fail-closed, two ceilings:
   - **per-run USD cap**: checked when a run reaches a terminal state
     (v1: post-run check → breach notifies + halts the loop before
     the next pick; v2 if needed: mid-flight polling + `fabro stop`);
   - **per-session USD cap**: before each pick, sum the session's
     completed-run costs; projected breach → stop picking, notify,
     exit with the standard summary.

**Fail-closed means**: when the loop is in `autonomous` mode and the
cost of a completed run is unobservable (null), that is itself a
cap-accounting failure — the loop stops picking and notifies, rather
than continuing cost-blind. (In `shadow` mode — explicit `--item`
dispatches with a human present — a warn line suffices.) This is the
"fix the gate, not the bypass" shape: the precondition is not "a cap
flag exists", it is "cost is observable AND capped".

Cap values: placeholders pending the first populated cost data —
suggest per-run $25 / per-session $100, env-overridable
(`LIVESPEC_MAX_RUN_USD` / `LIVESPEC_MAX_SESSION_USD`), defaults
committed in the Dispatcher so unset-env does not mean uncapped.

**Owning repo:** livespec-impl-beads (Dispatcher engine); the
cost-observability investigation may touch the fabro invocation/ACP
adapter configuration.

## Leg (c) — telemetry shipping (journal → Honeycomb)

**What exists today.** Local-only:
`livespec/tmp/capture_runtime_telemetry.py` accretes OTLP/JSON span
lines into `tmp/otel-runtime-spans.jsonl` (~1,568 spans across 5
resources: rgr / dispatcher / fabro / subagents / ci; deterministic
ids, append-dedupe, idempotent re-runs), replayable to Honeycomb via
the curl loop documented in the script header. The Dispatcher journal
is the dispatcher-resource source. Nothing ships anywhere; the script
runs only when an orchestrator session remembers to run it.

**What's missing, and what's user-blocked.** Shipping to Honeycomb is
blocked on **29f.3**: the USER must create an ingest-only key, enroll
the account in Honeycomb Intelligence, and create an MCP API key
(manual 1Password entry — agents never edit 1Password Environments).
That is honest and unavoidable: leg (c) cannot fully land on agent
effort alone.

**Non-blocked interim (recommended).** Decouple accretion from
shipping so zero history is lost while keys wait:

1. keep accreting locally — move the capture run from
   "orchestrator-session-start ritual" to a scheduled job (cron/timer)
   so accretion survives a8bb's retirement (see duty table row 6);
2. the moment keys exist: ONE one-shot replay of the accumulated file
   (with a sent-offset marker — Honeycomb ingest has no span dedup on
   re-send, per the reflection doc §4.1), then
3. steady state: direct emit from the Dispatcher
   (`JournalFile.append` dual-write through the OTel SDK's
   fail-open `BatchSpanProcessor` — reflection doc §4.1 option 3),
   retiring the harvest script.

Pre-gate the precondition is satisfied by (1) + the replay runbook
being ready; (3) can land with the 29f epic. Scrub discipline applies
throughout: no `detail`/stdout payload fields leave the host
(credential-adjacent, §2.3 of the reflection doc).

**Owning repos:** livespec (capture script + cron, interim);
livespec-impl-beads (direct emit, steady state); 29f.3 user actions.

## Sequencing claim — these land BEFORE gate-pass

The current plan bundles escalation + checkpoint guidance + the
Architecture-C codification (targeting livespec
non-functional-requirements §"Orchestrator-internal Dispatcher
guidance") into a **post-gate** spec PC. That ordering is INVERTED:
escalation design must precede unattended operation, because the
entire point of escalation is the period when no human is watching —
which begins at gate-pass, not after the paperwork. This document
corrects the plan as follows:

**Moves PRE-gate (operational machinery):**

- failure-notification + blocked-run escalation (leg (a)) — the
  Dispatcher's `blocked` outcome is BY DESIGN a human handoff
  (`fabro attach`); shipping an unattended loop whose human handoff
  has no notification path is a contradiction in terms;
- cost observability + spend caps (leg (b));
- telemetry accretion decoupled from orchestrator sessions + the
  one-shot replay runbook (leg (c) interim);
- the a8bb duty relocations marked "before" in the table below.

**Stays POST-gate (descriptive codification):**

- the spec PC itself — rewriting livespec
  non-functional-requirements §"Orchestrator-internal Dispatcher
  guidance" (explicitly non-normative on core's contract) and
  codifying the realized Dispatcher shape in impl-beads'
  SPECIFICATION can follow gate-pass, PROVIDED the machinery it
  describes is already running. Prose can trail reality; operability
  cannot;
- checkpoint/resume *guidance text* — the operational pieces
  (blocked-run surfacing, loop liveness) are already covered by
  leg (a); the written-down resume protocol rides the post-gate PC.

Relation to `livespec-iaut`: iaut defines what the streak MEANS
(rules, false-red dispositions); this document defines what must be
TRUE OF THE SYSTEM when the streak completes. Gate-pass declaration
requires both.

## a8bb duty relocation table — relocate-never-drop for responsibilities

Duties `/livespec-orchestrate` performs today that retiring it would
orphan. Per the standing relocate-never-drop directive, applied to
responsibilities: every row gets a home BEFORE the skill is deleted;
"home = nobody" is not an option. "Before/after" = relative to
gate-pass declaration.

| # | Duty (today: orchestrator session) | Proposed home | Move before/after gate-pass? |
|---|---|---|---|
| 1a | Ledger: close-after-verified-merge (green) | **ALREADY RELOCATED** — Dispatcher `--close-on-merge` (`ledger-close` stage, `dispatcher.py` `_dispatch_one`) | done |
| 1b | Ledger: outcome evidence on non-green (comment failed/blocked items with stage + run id so the next implementer/human sees it) | Dispatcher feature (small: `bd`-comment via the store API at terminal outcome) | **before** (escalation evidence) |
| 1c | Ledger: item creation + disposition (bd create, priorities, epics, non-green rerouting) | Retained human-invoked capture skills (`capture-work-item`, `capture-impl-gaps`, `capture-memo`) + the out-of-band reflector files findings (29f.4, dedup-first) | after (skills persist regardless; reflector rides 29f) |
| 2 | impl-beads primary-pull embargo sequencing (never pull the impl-beads primary while a dispatcher lives; dispatch impl-beads-targeted items alone) | Dispatcher feature via **impl-beads-ddu** (pinned dispatcher copy + canary kills the self-update hazard, which kills the embargo's reason to exist) | **before** (an unattended loop cannot rely on a human to sequence embargos) |
| 3 | Worktree reaping at sanctioned points + janitor-checkout retention | Scheduled job: `just reap-stale-worktrees` per family repo on a timer; Dispatcher already self-cleans green janitor checkouts — add a retention rule for red-kept ones (e.g. reap after N days or after item closure) | **before** (cheap; unattended disk rot otherwise) |
| 4 | Spec-side operations (/livespec:next, revise, doctor, propose-change cadence; cross-repo doctor as consistency gate) | Retained human-invoked Layer 2 skills (they ship from the driver plugin and survive a8bb untouched); cross-repo doctor cadence: scheduled job or standing human session ritual — decide in the post-gate PC | after (nothing orphans mechanically; cadence ownership written down in the PC) |
| 5 | Memo processing (process-memos dispositions) | Retained human-invoked skill (consent-driven by design; not automatable without violating the consent model) | after |
| 6 | Telemetry capture accretion (re-run capture script at session start) | Scheduled job (cron/timer) interim; superseded by Dispatcher direct emit (29f / leg (c)) | **before** (leg (c) interim) |
| 7 | USER-ACTION surfacing (the handoff-prompt USER-ACTION list — dies with the orchestrator's handoff chain) | Ledger items labeled `user-action` + a recurring line in the loop-summary notification (leg (a)) until acknowledged | **before** (the list currently has live entries, incl. 29f.3 itself — losing it would deadlock leg (c)) |
| 8 | Dispatch goal authoring/curation (premise gates, riders via ledger comments, judgment-leaning vs sandbox-safe routing, reproduction-shaped-goal hazard) | Split: filing-time quality stays human (capture skills); riders stay ledger comments (bn4: goal = description + comments at dispatch time); routing needs an explicit item-level marker (e.g. label `host-only`) the Dispatcher REFUSES to auto-dispatch, instead surfacing via leg (a) | **before** (the routing rule; without it the loop will eventually sandbox an item that must never enter a sandbox) |
| 9 | Cross-repo state verification (master-red CI sweep via `master_ci_green`, primaries ff-pull, open-PR survey) | Dispatcher loop preflight (it already pulls the target primary post-merge; add the master-green check pre-pick) and/or the scheduled reaper job's sweep | **before** (master-red-is-not-a-deferral must survive the orchestrator) |
| 10 | Gate accounting (streak counting, false-red dispositions) | Written rules (**livespec-iaut**) + mechanical accounting derived from the Dispatcher journal (outcomes are already journaled; the streak is a fold over them) | **before** (iaut is already scoped to this) |

Rows 4 and 5 deserve the explicit non-drop note: retiring a8bb removes
the Layer 3 *composition*, not the Layer 2 skills — `/livespec:*` and
the impl-plugin skills remain installed and human-invokable. What is
lost is the *cadence owner*; the post-gate spec PC must name one
(scheduled, or an explicit human ritual), not silently assume "someone
will run revise".

## Proposed work-item one-liners (for the orchestrator to file)

Not filed by this document. Suggested repos and shapes:

1. **impl-beads** — `dispatcher: fail-open ntfy notification on
   failed/blocked outcome, non-green loop summary, cap breach, and
   loop start/end (dedicated topic, no detail payloads)` [leg (a);
   pre-gate]
2. **impl-beads** — `investigate why fabro total_usd_micros is null
   on all runs and establish a real per-run cost signal (fabro
   config/ACP usage reporting; fallback: agent-runtime usage
   telemetry)` [leg (b) part 1; pre-gate]
3. **impl-beads** — `dispatcher: fail-closed per-run + per-session
   USD caps (autonomous mode halts on breach OR on unobservable
   cost; env-overridable committed defaults)` [leg (b) part 2;
   pre-gate; depends on 2]
4. **livespec** — `move telemetry-capture accretion to a scheduled
   job + write the one-shot Honeycomb replay runbook with sent-offset
   marker (interim until 29f direct emit)` [leg (c) interim;
   pre-gate]
5. **impl-beads** — `dispatcher: comment non-green terminal outcomes
   onto the ledger item (stage, run id, PR#)` [duty 1b; pre-gate]
6. **livespec** — `schedule reap-stale-worktrees across family repos
   + retention rule for red-kept janitor checkouts` [duty 3;
   pre-gate]
7. **livespec** — `relocate the USER-ACTION list from handoff prompts
   to user-action-labeled ledger items surfaced in the loop-summary
   notification` [duty 7; pre-gate]
8. **impl-beads** — `dispatcher: honor a host-only routing label —
   refuse to auto-dispatch, surface via notification` [duty 8;
   pre-gate]
9. **impl-beads** — `dispatcher: master_ci_green preflight before
   each pick in autonomous mode` [duty 9; pre-gate]
10. **livespec** — `post-gate spec PC: rewrite non-functional-
    requirements §"Orchestrator-internal Dispatcher guidance" +
    checkpoint/resume + spec-side cadence ownership, codifying the
    machinery already running` [post-gate; explicitly AFTER legs
    (a)–(c) are live]

Existing items this composes with (not duplicated): `livespec-iaut`
(gate rules), `impl-beads-ddu` (pinned copy + canary → duty 2),
`impl-beads-29f.1/.2/.3/.4` (telemetry depth, mechanical reflection
stage, keys, reflector), `dev-tooling-e60` (observability rollup).

## Evidence trail

- Dispatcher engine: `livespec-impl-beads/.claude-plugin/scripts/
  livespec_impl_beads/commands/_dispatcher_engine.py` (timeouts,
  three-valued outcomes, janitor venue, blocked semantics) and
  `commands/dispatcher.py` (`_dispatch_one`, `close_on_merge`,
  `_emit_outcomes`, shadow/autonomous modes, sizing warnings,
  fail-closed ledger-comments read).
- Cost probe: `fabro ps -a --json` 2026-06-13 — 29 runs, 23
  succeeded, `total_usd_micros` null on all; `fabro events` on
  succeeded run `01KTT1X565BAEFGEPJCDHX9T1Y` — no cost/usage fields.
- Notification survey: `/data/projects/claude-code-ntfy` (hook script
  `plugins/ntfy-notify/hooks-handlers/notify-ready.sh`);
  `CLAUDE_NTFY_TOPIC` set in `~/.claude/settings.json`.
- Telemetry: `livespec/tmp/capture_runtime_telemetry.py` +
  `tmp/otel-runtime-spans.jsonl`; reflection-gate design at
  `livespec-impl-beads/research/loop-reflection-gate/
  best-practices-and-design.md` (§2.3 credential-adjacency, §4.1
  transport options, §5.3 notification, §6 fail-open contract).
- Duty inventory: `livespec/.claude/skills/livespec-orchestrate/
  SKILL.md` (Steps 1–4, dispatch table, reaper) + the 2026-06-13
  session log in `tmp/contract-re-steering-session-1-status.md` +
  the W6 facts section of
  `tmp/livespec-4moata-orchestrator-handoff-prompt.md`.
