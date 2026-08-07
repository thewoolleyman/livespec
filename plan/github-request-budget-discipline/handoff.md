# Handoff — github-request-budget-discipline

**Thread anchor (ledger epic):** `livespec-httc`, in THIS repository's tenant
(`livespec`). This handoff records no status of its own; read status from the
ledger.

**One-line state:** the Contract, Installer, and Mechanism slots are DONE and
live-exercised. The Verifier slot is BLOCKED — not on ordering any more, but on
a fleet-wide retrofit that must land before its ban may arm. Four retrofit
work-items are filed and the first one is ready to drive.

## Read-first chain

Read these, in order. Nothing else is required.

1. `plan/github-request-budget-discipline/research/01-design.md` — the design
   record: the incident, the verified GitHub limits, the propagation-surface
   analysis, the Conformance-Pattern reframing, and the two obligations recorded
   after review.
2. `SPECIFICATION/non-functional-requirements.md` §"Request-budget discipline" —
   the ratified contract this thread implements (added by revision `v195`).
3. `.ai/dispatcher-drain-operations.md` — REQUIRED before driving any factory
   dispatch. Read it even if you think you know the flow.

## Compose current status first

```bash
/usr/local/bin/with-livespec-env.sh -- bd show livespec-httc
```

The epic's notes carry the full slot-by-slot record. Cross-tenant items are cited
in prose because beads cannot resolve a foreign-tenant id (`bd-ib-dvmh`); read one
with `bd show <id>` from inside that repository's checkout, under the same
credential wrapper.

## Five spec slots, four tracked work slots

These two counts are different things, and conflating them has already caused
confusion in this thread. `SPECIFICATION/non-functional-requirements.md`
§"Conformance Pattern" defines **five** slots — Contract, Mechanism, Installer,
Verifier, Exemption — and revision `v195` filled all five *in the spec text*.
The **Exemption** slot needs no separate implementation work: it is discharged by
the declaration in the ratified text plus the in-place exemption on the
credential-minting path. So this thread tracks **four** work slots. When the spec
rule says "a concern is not adopted until all five slots are filled", it is
talking about the spec text, which is already satisfied; adoption is still
blocked by the Verifier's implementation.

## What is DONE — do not redo

- **Contract slot.** Ratified as spec revision `v195` (livespec PR #2030,
  merged). Registers **Request-budget-discipline** in the Conformance-Pattern
  concern registry and fills all five slots in the spec text.
- **Installer slot.** `livespec-driver-claude-6xj` — merged (PR #423), released
  as `v0.5.0`. `github_rate_limit_guard.py` ships in that plugin's own
  `.claude-plugin/hooks/hooks.json` and reaches adopters with zero per-repo
  wiring. Live-exercised through the adopter `resume`'s resolved plugin path.
- **Mechanism slot.** BOTH slices merged and live-exercised on 2026-08-07:
  - `livespec-runtime-lzq` (slice A, measurement) — PR #487, **implementation
    commit `9f28c77`**.
  - `livespec-runtime-g2s` (slice B, mitigation) — PR #489, **implementation
    commit `c77f2d7`**.

  The evidence is journaled on each item. The headline result: 6 conditional
  reads returned `304` with the per-response `x-ratelimit-used` counter FLAT,
  against a control of 6 unconditional reads where it climbed by 5 — so the
  design record's largest claimed reduction is now verified, not assumed.

## Two traps this thread paid for — do not re-learn them

**A dispatch's reported `merge_sha` is not the implementation commit.** For BOTH
Mechanism slices, the dispatcher's `merge_sha` and the forge's `mergeCommit`
named a later release-please commit ("chore(master): release …"), because
`livespec-runtime` rebase-merges. Auditing against the reported SHA shows a
version bump and none of the work. Find the real commit by message or by PR
commit list, and verify against that.

**A green measurement needs a control.** While verifying the 304 claim, reading
the rate-limit endpoint's `core.used` before and after 8 conditional reads gave a
delta of 0 — which looks like proof. A control of 8 UNCONDITIONAL reads gave a
delta of 0 too, falsifying the instrument rather than confirming the claim. The
correct instrument was the per-response `x-ratelimit-used` header. Without the
control, a confident and unfounded "verified" would have been recorded.

## NEXT ACTION — drive the retrofit, in order

**Maintainer decision, 2026-08-07: retrofit first, then arm.**

The finding that forced it: `GithubBudgetedClient` has **zero production
callers**. Its only references anywhere are its own definition, its re-export,
and its tests. The Mechanism is built but adopted nowhere — including in its own
repository — so this epic's acceptance ("every GitHub call originating from fleet
automation routes through the client") is not met by the slices alone.

Direct-call surface, first-party non-test, measured 2026-08-07 with a positive
control:

| Repository | Sites |
|---|---|
| `livespec-runtime` | 4 (plus the exempt credential-minting path) |
| `livespec` | 4 |
| `livespec-dev-tooling` | 7 |
| `livespec-orchestrator-beads-fabro` | 12 |

Four retrofit items are filed, each in its own tenant. Drive them in this order:

1. **`livespec-runtime-wpt`** — the ANCHOR. Land it first: the client lives in
   that repo, and this slice establishes the calling pattern the other three
   copy. Its branches and compare reads are the highest-value conditional-read
   conversions in the fleet.
2. **`livespec-umy2`** (core) — carries a real packaging question: plugin scripts
   ship under bare system `python3` with no virtualenv, so confirm how the client
   is reachable on that path before assuming an ordinary import works.
3. **`livespec-dev-tooling-z69s`** — the enforcement suite. This repo also owns
   the Verifier, which must not arm until this lands.
4. **`bd-ib-li4d`** (orchestrator tenant) — largest and most operationally
   sensitive: these are the running factory's own merge, create, and
   update-branch paths. Convert reads first, verify a real dispatch still
   completes green, then convert mutations.

## Then — the Verifier slice

`livespec-dev-tooling-t2q4` stays deliberately in backlog and **un-routed**.

Its blocking reason has CHANGED. The old reason — a cross-tenant dependency beads
cannot express as an edge — discharged when slice A merged. The current reason is
that arming a fleet-wide ban with 27 un-retrofitted call sites would red four
repositories on their next pin bump, reproducing the enforcement-before-adoption
failure recorded as `livespec-runtime-s8q`, and would violate the
New-obligation discipline in
`SPECIFICATION/non-functional-requirements.md` §"Fleet membership contract"
("the retrofit travels with the rule").

Route and dispatch it only after all four retrofit items have landed. Do **not**
resolve a retrofit by adding an exemption entry — the exemption list is reserved
for the credential-minting path.

## Routing rules that bind every remaining slice

- Implementation is **factory-side**. Use `drive --action impl:<id>` or let the
  Dispatcher drain. Do NOT use the in-session `implement` operation.
- **Resolve the orchestrator plugin path from the install record**, never with
  `ls … | tail -1` or `head -1` — those pick a lexically-sorted directory, not
  the installed build. Take the entry whose `projectPath` equals the repository
  you are dispatching against, per `.ai/dispatcher-drain-operations.md`.
- **Preflight the checkout.** `git status --short` must be clean before every
  dispatch; the engine pushes the checkout state. Note that any `uv run` — such
  as running a verification script — dirties `uv.lock`, which is exactly the
  tracked churn that makes the engine fall back to a synthetic base.
- **Never wrap a dispatch in `timeout`.** A dispatch runs 7–76 minutes. Background
  it and wait for the completion notification. A timer that fires mid-run kills
  the supervisor while the sandbox keeps going, and the item must then be reset
  to `pending-approval` by hand — no valve repairs it.
- Keep dispatchable descriptions near ~1500 chars. Both Mechanism slices tripped
  the sizing warning and completed anyway, but a 7196-char item is recorded as
  losing a full factory hour mid-publish.
- Verify a dispatch outcome from THREE sources — the drive result block's
  `status`/`merge_sha`, the forge, and the ledger — and then find the real
  implementation commit per the rebase-merge trap above. A shell exit code is the
  last command's status, never the dispatch verdict.

## Completion bar

Per this repository's completion rule, "done" requires driving the SHIPPED
behaviour end-to-end in its real environment with live-exercise evidence
journaled on the item — not merely merged, CI-green, and accepted. Both Mechanism
slices discharge it; their journalled notes are the worked examples to follow,
including the honest recording of what was deliberately NOT exercised (a real
primary-limit exhaustion, because inducing one means burning the shared budget
this concern exists to protect).

## Known defect in the Installer slot

`livespec-driver-claude-mu5` (P1, backlog) — the shipped guard denies on
substrings rather than behavior. It will deny a command whose *payload* merely
mentions a GitHub call, because its loop test matches the ordinary English word
"for". It blocked this thread's own evidence journaling. Workaround: write the
payload to a file with a non-Bash tool, then pass only the file path on the
command line.

## Closing the thread

When the Verifier slot is filled, close `livespec-httc` and archive:

```bash
git mv plan/github-request-budget-discipline/ plan/archive/github-request-budget-discipline/
```

Do **NOT** archive before then: `plan/<topic>/` is active if and only if its epic
is open. Request-budget-discipline is currently REGISTERED but not yet ADOPTED.

## Spec-change discipline, if any slice needs one

Every proposed change needs an independent READ-ONLY adversarial review by a
separately-spawned Fable-model agent before `/livespec:revise` accepts it. The
revise CLI enforces this mechanically: it requires a `ratification_review` mode
plus `ratification_evidence` carrying a sha256 `content_digest` over the proposal
bytes AND each resulting file's content. **Every edit after a review invalidates
that digest** — batch all fixes into one pass, then request a single
digest-bound verdict. Note `.livespec.jsonc` pins the reviewer model, and the CLI
requires `reviewer_identity` to equal `reviewer_model`.
