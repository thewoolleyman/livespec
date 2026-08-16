# planning-lane-redesign — brainstorm

Agent-side analysis captured 2026-08-04, same session as
`seed-prompt.md`. Ledger anchor: livespec epic `livespec-zsn2xh`
(cited read-only). Maintainer decisions extracted from this analysis
are in `maintainer-rulings.md`; where this document and that one
disagree, the rulings win.

## Diagnosis correction

The foreman failure was not "handoffs lived in Markdown". It was:
scope and deferral lived in prose with no ledger carrier, and
completion was computed only from the ledger. The stranded phases
lived in a research brainstorm — a document class that stays in git
under this redesign too. Moving handoffs into the ledger therefore
does not, by itself, prevent a recurrence. Two separable fixes:

1. **Scope must always have ledger carriers** (the scoping protocol
   below) — this is the load-bearing fix for the observed failure.
2. **Mutable planning state moves to the ledger** (the migration) —
   this fixes the write-cost/availability problem and removes the
   second drifting source of truth (handoffs restating ledger state).

Both are in scope for this plan; neither substitutes for the other.

## Content taxonomy — what lives where

- **Git, write-once: research inputs.** `plan/<slug>/research/` keeps
  freeform seed prompts, brainstorms, human-driven research, review
  findings. Written at human pace at discrete moments, so the
  worktree → PR cost is acceptable; git versioning and GitHub
  linkability genuinely help. Attached rule: the moment any research
  prose states scope, those pieces get ledger carriers; the prose is
  thereafter historical, never authoritative about what remains.
- **Git, write-once: a minimal metadata anchor.** One tiny file naming
  the epic id, written at plan open, never updated. It preserves the
  "paste a GitHub link" ergonomic and points at the epic instead of
  restating anything. Everything derivable (children, status,
  readiness) is derived by querying the ledger.
- **Ledger: all mutable planning state.** Handoffs, supervisor
  handoffs, status, decisions-in-flight — as append-only entries on
  the plan's epic (exact bd surface — notes/comments/journal — chosen
  at design time). Append-only is what a ledger is good at:
  timestamped, conflict-free when a supervisor and a worker both
  write, cheap at low-context wrap-up time.

Attached content rule for handoffs: an entry carries only
**non-derivable** content — rationale, warnings, what was tried and
abandoned, pointers. Live handoffs measured at capture time (8–28 KB
`handoff.md`, 29–47 KB `supervisor-handoff.md`) consist substantially
of restated ledger/git state ("PR #N merged", "increment ratified"),
which is exactly the content class that goes stale and misleads a
resuming agent. Derivable state is read fresh at resume time.

## Trade-offs accepted (and their mitigations)

1. **Durability window.** A pushed handoff replicates to GitHub
   immediately; the Dolt server is host-local with timer-driven
   backups, so a ledger handoff written just before a host failure
   could be lost (window = backup interval). Counterweights: the
   entire work-items ledger already carries exactly this exposure —a
   plan handoff is not more precious than the work-items themselves —
   and the current design's failure mode (forge or CI down at wrap-up
   → no handoff at all) is strictly worse. Tightening the backup
   interval is an orthogonal, cheap mitigation if wanted.
2. **Read-path availability inverts.** Files are readable with
   everything down; ledger reads need the Dolt server plus the
   credential wrapper. Marginal risk is small (Dolt down already
   halts all orchestration), but dispatch briefs must account for
   "reading the plan requires ledger access".
3. **Linkability regresses until the console renders it.** Bead ids
   are cryptic; there is no GitHub-rendered page for ledger entries.
   The write-once metadata anchor mitigates; the natural completion
   is livespec-console-beads-fabro rendering an epic's planning
   entries as the handoff page with a stable URL.
4. **Long-prose ergonomics in `bd` are unverified.** Nothing in
   `.ai/beads-gaps-workarounds.md` establishes whether notes/journal
   entries handle 30–50 KB of Markdown well (size limits, escaping,
   editing, console rendering). **Named go/no-go precondition:** spike
   a real-sized handoff into a scratch tenant and read it back through
   the CLI and console surfaces before committing the design.
5. **Handoffs lose PR review.** Low cost — handoff PRs are self-merged
   ritual, and adversarial review stays where it earns its keep (spec
   proposals, product changes). Offsetting gains: no CI runs burned on
   doc-only handoff commits; no merge conflicts on shared state files.

## The scoping problem — three routes

An archive gate needs an enumerable notion of "requirement", and
freeform research prose does not provide one (see the seed's
scoping-protocol constraint). Three candidate routes:

1. **Structure the seed.** A required requirements section with stable
   ids; ledger items carry trace fields. Fully mechanical, but it
   deforms the thing being protected — seeds are often the verbatim
   human ask, brainstorms are deliberately freeform, and the foreman's
   stranded phases lived in a brainstorm no seed schema would cover.
2. **Scoping as an explicit ledger event** *(recommended, and adopted
   at capture time — see rulings)*. Research prose stays freeform
   forever. Before a plan's epic takes implementation children, a
   scoping pass distills the prose into requirement-carrier items
   under the epic — including explicitly-deferred ones. From that
   moment requirements never exist only in prose, and deferral is a
   ledger state. The archive gate then splits:
   - *Mechanical leg:* an epic cannot close/archive with an
     undisposed child.
   - *Judgment leg:* an independent adversarial completeness review at
     archive time reads the research docs against the epic's children
     and attests nothing lacks a carrier — the doctor static+LLM split
     applied to archiving, and the same independent-review pattern
     that already gates ratifications.
3. **LLM-judged gate only.** No structure anywhere; an agent extracts
   requirements at archive time. Would likely have caught the foreman
   failure (which required that nobody ever read the seed), but
   non-deterministic as the sole enforcement.

Open design question for route 2: the concrete "deferred"
representation — a bd status if a suitable one exists, else a label
convention — which must honor the existing rule that admission labels
move only through the sanctioned valve, never by hand.

## Vocabulary

"plan thread" is retired in favor of "plan" (maintainer-declared
2026-08-04; see rulings). Survey from committed HEAD across nine fleet
repos on 2026-08-04: 445 files mention the term in total; **98 are
live surface** after excluding frozen `archive/`, `history/`, and
`plan/` trees — livespec-orchestrator-beads-fabro 31, livespec-overseer
20, livespec-dev-tooling 14, livespec (core) 13,
livespec-console-beads-fabro 6, livespec-orchestrator-git-jsonl 5,
livespec-runtime 4, livespec-driver-claude 3, livespec-driver-codex 2.
The mechanical rename folds into the migration's surface rewrites
(`list-plan-threads`, the `plan` operation prose, `supervise-plan`,
identifiers) rather than a standalone rename bump — one cross-repo
contract change instead of two. Frozen trees keep the old term;
quoting existing text verbatim for mechanical replacement targeting is
the only new-prose exception. The ban gets recorded in the fleet's
committed agent-instruction surface alongside the existing vocabulary
bans.

## Home rationale

This plan lives in livespec core because the load-bearing change is to
the Planning Lane contract in livespec's `SPECIFICATION/spec.md`, and
because TWO orchestrator realizations exist
(livespec-orchestrator-beads-fabro and livespec-orchestrator-git-jsonl)
plus supervision surfaces (livespec-overseer `supervise-plan`,
livespec-console-beads-fabro). Parking a contract-level redesign in
one sibling's repo invites the other realizations to drift; core is
the only repo upstream of all of them, matching the
No-Circular-Dependency direction (contract upstream, realizations
downstream). Lineage precedent: the Planning Lane's original design
research lives in livespec core
(`archive/research/planning-workflow-gap/planning-lane-design.md`).

## Affected surfaces (survey, 2026-08-04)

- **livespec (core):** Planning Lane sections of `SPECIFICATION/`
  (spec change via propose-change → revise, with
  `tests/heading-coverage.json` co-edits for any H2 change).
- **livespec-orchestrator-beads-fabro:** the `plan` operation prose
  and store, `list-plan-threads`, the needs-attention plan gather, its
  own SPECIFICATION contracts, the new archive gate.
- **livespec-orchestrator-git-jsonl:** mirrors an orchestrator plan
  surface (5 live files) — per-repo state to verify before scoping,
  not assume.
- **livespec-overseer:** `supervise-plan` (today: authors
  `supervisor-handoff.md` through worktree → PR → merge; becomes a
  ledger write), the foreman read-first chain.
- **livespec-console-beads-fabro:** rendering ledger-held planning
  entries with stable URLs.
- **Live plans to migrate:** three in livespec, several each in
  livespec-overseer and livespec-orchestrator-beads-fabro. Archived
  plans under `plan/archive/` stay frozen as-is.

## Sequencing

1. Design the plan protocol (scoping event, requirement carriers,
   explicit deferred representation, metadata anchor shape) as the
   first increment; the archive gate falls out of it nearly for free.
2. Run the `bd` long-prose spike as the go/no-go on the ledger-held
   handoff design.
3. Rewrite the surfaces (and fold the vocabulary rename into exactly
   those rewrites); migrate live plans; land the completeness-review
   archive leg.

Scoping this plan itself — cutting the above into requirement-carrier
child items under `livespec-zsn2xh` — awaits maintainer approval of
the cut. This plan should be the first practitioner of its own
protocol once the protocol lands.
