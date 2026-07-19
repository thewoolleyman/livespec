# factory-safe-by-default — design

## Problem / motivation
A 2026-07-07 factory dispatch wave (needs-attention epic livespec-bj9x) surfaced three "factory failures" that looked like one class but are two:
- **CN1 (livespec-console-beads-fabro, Rust):** the Fabro sandbox image is a uv/Python image with no Rust toolchain, so the build died at `cargo: absent`. A **capability gap**, not a classification error. (Prior console Rust builds succeeded only because the implement agent happened to self-install rustup mid-run — a nondeterministic accident.)
- **OR3 (livespec-orchestrator-git-jsonl, Python):** implement + PR + merge succeeded and CI was green, but the dispatcher's post-merge janitor died in a fresh worktree on an unhydrated gitignored worktree-pack (`dev-tooling/branch-protection.sh`; filed as bd-gj-9sj). A **factory-tooling bug**, not a classification error.
- **ob-wu8a (openbrain):** an operator-host item whose verification probes the LIVE credential environment (real GitHub App private key, DB password, OAuth token) was aimed at the factory. Its verification genuinely cannot run in a sandbox — those secrets must never enter a sandbox running agent-written code. A **genuine host-only boundary.**

Two of the three argue for MORE factory (equip it), not less; only one is a genuine not-factory-safe case, and it is a hard SECURITY boundary. The recurring pain is not that the distinction is wrong — it is that the boundary is (a) implicit and prose-buried in a work-item description, and (b) discovered ~19 minutes into a sandbox run instead of at dispatch time.

## Thesis
Head toward **factory-safe by DEFAULT** — not "literally everything runs in the factory." Assume factory-safe; require an explicit, machine-readable, admission-enforced opt-out for a small ENUMERABLE residue; and invest in widening factory capability so the residue stays tiny.

## The irreducible residue — what genuinely cannot run in the factory
1. **needs-host-secrets** — verification requires real secrets that must never enter a sandbox running agent-written code (ob-wu8a).
2. **mutates-host-machinery** — changes the live host substrate the factory itself runs on (systemd timers, credential wrappers, the plugin cache, Fabro servers, installed_plugins.json).
3. **needs-privileged-host** — privileged provisioning (standing up a Dolt server, a 1Password environment, a per-tenant Fabro server).
4. **requires-human-judgment** — grooming, spec ratification, approvals (already not-factory).

Sharp line: writing CODE for any of these (including the dispatcher's own code, which is just code + tests in the orchestrator repo) is factory-safe; APPLYING host state is host-only.

## The four moves
1. **Invert the default.** Assume factory-safe. Require an explicit machine-readable opt-out: a `not-factory-safe: <reason>` label, reason in {needs-host-secrets, mutates-host-machinery, needs-privileged-host}. No more "operator-host item" buried in prose that nothing enforces.
2. **Enforce at admission; fail fast.** The dispatcher REFUSES a not-factory-safe item at dispatch time with a clear message — turning a 19-minute sandbox burn into an instant, actionable refusal. This is "fix the gate, not the bypass": the system classifies, not a human's memory.
3. **Widen capability aggressively.** Target-local workflows + parameterized prepare per toolchain (already the z2ctra direction). Console = the Rust exemplar; openbrain = the pnpm exemplar. Each new toolchain is a one-time per-repo workflow file; then the opt-out set shrinks to only the residue above.
4. **Give the residue a home.** Host-only work today has nowhere to go — so it gets shoved at Fabro (ob-wu8a) or strands READY forever. Surface it as a distinct needs-attention kind ("host-only action") for the overseer/maintainer to run with host + secret access. Dovetails with the needs-attention track (epic livespec-bj9x).

## Implications / cost
- One-time per-repo workflow authoring + slower first-compile sandboxes.
- A tiny schema addition (one label + reason) and one dispatcher admission check that REPLACES fuzzy per-item judgment — net LESS to reason about.
- Doctrine simplifies from "decide per item whether it is factory-safe" (error-prone) to "everything is factory-safe unless the mechanical check trips."
- Risk if done naively: preaching "everything runs in the factory" WITHOUT the mechanical gate yields MORE ob-wu8a-style burns. The aspiration only works paired with the fail-fast admission gate.

## Relationship to existing work
- **z2ctra** (orchestrator tenant; D1 target-local-workflow precedence spec clause + D2a dispatcher auto-resolution) IS move #3's plumbing. The console (Rust) folds into z2ctra as the Rust exemplar alongside openbrain's pnpm.
- **needs-attention** (epic livespec-bj9x) is move #4's home (the host-only attention kind).
- **bd-gj-9sj** (git-jsonl janitor worktree-pack hydration) is a factory-tooling robustness fix in the same family (move #3's "make the factory tooling robust").
- This thread coordinates those and adds moves #1/#2 (the classification label + admission gate).

## Open questions / candidate slices (to develop)
- Label schema: work-item label vs. a first-class schema field; finalize the reason enum.
- Admission gate: dispatcher pre-check location + message; interaction with explicit `--item` targeting (does an explicit target override, or still refuse?).
- Host-only needs-attention kind: schema + renderer + how the overseer/console consume it.
- Capability roadmap: enumerate every fleet toolchain; per-repo target-local workflow authoring; land bd-gj-9sj.
- Spec home: the orchestrator (beads-fabro) contract for the classification + admission gate; git-jsonl parity.

## Reshape (2026-07-17) — grounded in code + spec, maintainer-endorsed

A four-agent read-only sweep of the live code (`livespec-orchestrator-beads-fabro`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime`, `beads`) and the ratified
orchestrator spec collapsed the five open questions above to a single cut. The
findings overturn parts of the original design's framing, so they are recorded
here as the settled basis; the Problem/Thesis/Residue/Four-moves sections above
still hold except where this section corrects them.

### What is already built (the design under-counted)

- **The fail-fast admission gate — move #2 — already ships.** The Dispatcher
  refuses a host-only item BEFORE any Fabro launch:
  `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands/_dispatcher_host_only.py`
  (`is_host_only_item`) + `_dispatcher_completion.py` (`host_only_refusal`,
  emitting a `host-only-refused` DispatchOutcome). So "turn a 19-minute burn into
  an instant refusal" is realized; what is missing is only the CLASSIFICATION
  (move #1).
- **The shipped classifier is exactly the prose-buried marker this thread
  objects to.** `is_host_only_item` is a word-bounded regex hunting the literal
  token `host-only` / `host_only` in the item's TITLE or DESCRIPTION. Its
  docstring states the marker sits in the description because it is "the only
  field-space the `WorkItem` schema exposes without a cross-repo contracts.md
  change (the mapped beads record drops unrecognised labels)" — i.e. the prose
  regex was a deliberate expedient to dodge a schema change, not an oversight.

### The spec contradicts the code (this is the thing to fix)

`livespec-orchestrator-beads-fabro/SPECIFICATION/contracts.md` (§"Admission valve
(ready → active)", ~L1362-1368; and §"Dispatcher grooming behavior", ~L784)
declares the host-only marker **retired** — "the `admission_policy` field is the
first-class realization that replaces the prior `host-only` / `human-gated` text
markers" — and declares the `ready → active` valve "purely mechanical …
`admission_policy` plays no part at this valve." But the shipped code still
implements the host-only marker at exactly that valve. The claim is not merely
incomplete, it is wrong on the merits: `admission_policy ∈ {auto, manual}` gates
only whether a HUMAN must approve (`pending-approval → ready`). A human approving
a host-only item just sends it into a sandbox that physically cannot run it. The
field cannot express the runnability constraint it was declared to replace —
which is why the code had to smuggle the marker back in.

### Resolution — two orthogonal axes (maintainer-endorsed 2026-07-17)

Model factory-safety as a NEW first-class axis beside `admission_policy`, not
folded into it:

- **`admission_policy`** answers *does a human approve?* — gates
  `pending-approval → ready`. Unchanged.
- **`factory_safety`** (new) answers *can a sandbox run this at all?* — gates
  `ready → active` (the seam `is_host_only_item` occupies today). The field
  carries the OPT-OUT reason directly (null = factory-safe), mirroring how
  `blocked_reason` carries a reason string that is null when not blocked.

The two are independent: an `admission_policy: auto` item can still be
not-factory-safe. This de-duplicates the reason enum: the original design's
fourth reason **`requires-human-judgment` IS exactly `admission_policy: manual`**,
so the new axis carries only THREE reasons —
`{needs-host-secrets, mutates-host-machinery, needs-privileged-host}`.

### Encoding + cross-repo cost (both precedented)

- **Field, not bare label.** In the beads store, first-class `WorkItem` fields
  are ALREADY encoded as prefixed beads labels — `store.py` carries `admission:`,
  `acceptance:`, `origin:`, `gap-id:`, `resolution:`, `blocked-reason:`. A "field"
  and a "label" are not alternatives here: a field IS a label with a recognized
  prefix. A BARE `not-factory-safe:` label (the original design's proposal) is
  silently dropped on read (the store only reads prefixes it knows), so it is
  non-functional. `factory_safety` follows the six-example prefix precedent.
- **git-jsonl parity is one line.** `livespec-orchestrator-git-jsonl` re-exports
  the SAME shared `WorkItem` (from `livespec_runtime`) and validates writes
  against a CLOSED key allowlist — so adding ANY field, even optional, breaks its
  write path UNLESS the codec pops it. Three fields already do exactly this:
  `store_codec.py` pops `admission_policy`, `acceptance_policy`, `blocked_reason`.
  A fourth pop follows the same pattern. The Rust console tolerates unknown
  fields silently (no `deny_unknown_fields`), so it needs work only if the field
  must render.
- **Enum enforcement is post-hoc, not a boundary.** The store read path
  `cast(...)`s enum values through unvalidated; there is no `__post_init__`. Real
  enum enforcement lives in the ledger-check registry (`_dispatcher_ledger_checks.py`,
  e.g. `status-conformance` deriving its allowed set from the `WorkItemStatus`
  Literal via `get_args`). A `factory_safety` reason enum wanting mechanical
  enforcement follows that `get_args`-derived ledger-check template — NOT a
  dataclass check. (Also note: `just check` runs work-item checks over an EMPTY
  fake tenant under `LIVESPEC_BEADS_FAKE=1`, so it smoke-tests the check code, not
  live rows.)

### Two open questions were already settled by the ratified spec

- **`--item` interaction:** `contracts.md` §"Dispatcher loop invocation surface"
  (~L1265) ratifies that `--item` "NARROWS the ranked selection; it never
  bypasses it — a named item that is not dispatch-eligible … MUST NOT be
  dispatched, exactly as if it were not named." So factory-safety-as-eligibility
  inherits the refusal for an explicit target for free — no new decision.
- **Host-only needs-attention home:** the cited epic `livespec-bj9x` is CLOSED —
  needs-attention already shipped. `livespec-runtime/livespec_runtime/attention_item.py`
  carries a live `AttentionKind` Literal (`human-valve|impl|spec|plan|hygiene|internal`)
  and a `HandoffKind` including `shell` (already models "run this on the host").
  Move #4 is a small ADDITIVE change to a shipped surface, not new machinery.

### The settled cut (children of epic `livespec-nrdk`)

Epic `livespec-nrdk` is anchored in the **livespec core** tenant (the plan thread
lives here). Per the bj9x cross-tenant precedent, impl slices are filed into their
OWNING repo's tenant and associated to the core epic by prose; the epic's
%Complete tracks only same-tenant children.

- **A — spec contract (route: `/livespec:propose-change` in
  `livespec-orchestrator-beads-fabro`). FOUNDATIONAL.** Codify the two-axis
  model: the `factory_safety` opt-out field (3-reason enum, label-prefix
  encoded); CORRECT the false "`admission_policy` replaces the host-only marker"
  clause (they are orthogonal — permission vs. runnability); the `ready → active`
  refusal keys on this field; cross-reference the already-ratified
  `--item`-narrows-never-bypasses rule. Goes through independent Fable review
  before revise. Spec-side → NOT a ledger work-item.
- **B — mechanical field + gate (impl, factory-dispatched; beads-fabro tenant
  `bd-ib`, cross-repo: `livespec-runtime` field + beads store encode/decode +
  git-jsonl codec pop).** Add `factory_safety` to the shared `WorkItem`; encode
  as a `factory-safety:` beads label; REPLACE the `is_host_only_item`
  title/description regex with a field read; fix the refusal-detail message
  (it currently points operators at the RETIRED "livespec-implementer dispatch
  path"). Blocked-in-prose on A ratifying (spec is not a ledger dep edge).
  Epic-shaped/cross-repo → routes to `groom` for the per-repo ready cut
  (runtime-first, per bj9x's foundational-first ordering).
- **C — host-only needs-attention lane (impl, factory-dispatched; depends_on B).**
  Add a `host-only` value to `AttentionKind` and surface not-factory-safe items
  (and dispatch refusals) in needs-attention with a `shell` handoff for the
  maintainer to run on the host.
- **D — capability-widening (move #3) STAYS under `z2ctra` (beads-fabro tenant),
  coordinated not absorbed** (maintainer-endorsed 2026-07-17). Recorded as a
  comment on `livespec-nrdk`, not a new work-item (prefer primitives over
  artifacts). Covers the per-toolchain target-local workflows (console = Rust,
  openbrain = pnpm), landing `bd-gj-9sj` (git-jsonl janitor worktree-pack), and
  the Fabro GitHub-App-token 60-min-TTL candidate already captured on the epic
  comment thread.

**Migration note for B/groom:** existing items marked by the old prose `host-only`
regex must not silently lose their classification when the regex is removed —
either migrate them to the field or keep the regex as a read-fallback. A B/groom
detail, flagged here so it is not dropped.
