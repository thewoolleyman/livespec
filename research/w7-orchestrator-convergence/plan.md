# Plan (APPROVED 2026-06-15, session 12 — executing): W7 orchestrator-reference convergence + golden-master acceptance

**Status:** design settled with the user 2026-06-15 (session 11); APPROVED and entering
execution in session 12. This doc was graduated from `tmp/` to
`research/w7-orchestrator-convergence/` as the first commit of W7 execution. Ledger anchor:
`livespec-zkmn.1` (livespec tenant); first action: `livespec-impl-beads-o2f` (the
Fabro-under-Docker-in-Docker spike, step 0).

**Epic context:** `livespec-zkmn` (W7: swap proofs + diagram codification). The
diagram-codification half landed (PR #441 / history/v113). This plan delivers the
**swap-proofs half** — but reframed (with the user) from the handoff's "abstract dispatcher.py
over both ledgers (~800–1200 lines)" into a cleaner, spec-faithful shape that also retires the
memo concept and containerizes the orchestrator as the universal execution substrate.

---

## Why the handoff's framing was wrong (and what replaced it)

`spec.md:199` is explicit: the Ledger/Loop/Dispatcher decomposition is **"orchestrator-internal
guidance only … core's contract … never names Ledger/Loop/Dispatcher in any config key or
invariant."** The claim *"the two halves swap independently"* is a property of the
**decomposition**, demonstrated by **two self-contained reference orchestrators** (git-jsonl
serial; Beads/Dolt+Fabro parallel) — NOT by making one Dispatcher runtime-pluggable over two
ledgers. Both reference orchestrators already exist and have run (the git-jsonl/homegrown path
drove epic sessions 1–10; the Beads/Dolt+Fabro path proven live at 29f.3).

User's key correction: nothing in the spec forbids abstracting across two reference impls **we
own** — that is squarely "the orchestrator's private choice." The only surviving boundary: the
abstraction lives **orchestrator-side** (a shared library both impls import), NEVER lifted into
core's contract (no `.livespec.jsonc` key, no doctor invariant, no core dependency).

So the swap proof becomes **executable, not prose**: one golden-master acceptance test, same
fixture spec through BOTH orchestrators, same asserted behavior.

---

## Settled design decisions

### A. Memo: symmetric kill (spec-first)
- Memo currently exists **identically in BOTH impls** (`capture-memo`/`process-memos`/`list-memos`
  skills + `store.py`/`types.py` + e2e fixtures). The premise "absent in Beads" was false.
- Current re-steered contract already treats memo as **orchestrator-private, NOT required**
  (`contracts.md:142`, `:223`). The `§"Heavyweight authored skills (6)"` the shipped skills cite
  no longer exists → shipped skills implement the pre-v103 contract.
- The ledger fully absorbs memo's function: `capture-work-item` is already low-friction freeform
  filing; deferred triage = an "untriaged" status, not a separate substrate; the newest capture
  machinery (29f.4 reflector) already bypasses memo entirely (files work-items + lessons-PRs).
- **Two things to preserve (relocate-never-drop):** (1) retarget the core `block-auto-memory.sh`
  redirect from `capture-memo` → `capture-work-item`; (2) `research/loop-reflection-gate/lessons.md`
  is the home for the "this is a lesson, not a task" disposition.
- **Path:** `/livespec:propose-change` → `/livespec:revise` on the SPECIFICATION (retire memo +
  redirect retarget + knowledge home), then remove memo from both impls; recoverable SHA cited.

### B. Shared `Store` extraction into `livespec-runtime`
- Home = **`livespec-runtime`** (the existing shared runtime sibling library BOTH impls already
  depend on `v0.3.0` and vendor under `_vendor/`). No new package. NOT core.
- **Moves (shared once):** the `WorkItem` data model (currently duplicated per-repo) + a `Store`
  interface (typing.Protocol: `read_work_items` / `append_work_item` / `materialize_work_items` /
  comments) + genuinely-identical pure logic (materialize/head-reduction, identity, validation).
  (No `Memo` — killed in A.)
- **Stays per-impl (the "fill"):** backend I/O — `impl-beads` → Beads/Dolt via `bd`; `impl-git-jsonl`
  → JSONL files. Each just *implements* the shared interface.
- Converge the two real divergences: the config/param type (`StoreConfig` vs `Path`) and the
  comments API. Version-bump `livespec-runtime` + pin-and-bump fan-out to BOTH consumers atomically
  (watch the schema-tightening-breaks-shared-wrapper hazard — backfill both together).

### C. Golden-master acceptance test (the executable swap-proof)
- **Shape:** a minimal fixture livespec SPECIFICATION (hello-world CLI that greets a name) → run
  the orchestrator factory → assert the **produced software's BEHAVIOR** (run it, check the
  greeting) against the fixture spec. Behavioral assertion is robust to LLM non-determinism (the
  irreducibly non-deterministic core); only fails when the factory produces genuinely wrong software.
- **Same fixture through both orchestrators ⇒ proves the swap.**
- **Agent-runtime dimension:** the acceptance story also records which runtime is being exercised
  by each tier: Claude Code Driver, OpenAI Codex project-local adapters, and the future Pi harness.
  Codex is not treated as "Claude with different prompts": the fixture evidence must show that
  Codex loaded the participating repository instruction surface, used verified project-local
  adapters where they exist, and recorded any unsupported or Claude-only mechanism explicitly.
- **Cadence:** dedicated `just` target, OUTSIDE the fast `just check` aggregate; wired as a
  **required CI check pre-merge** (branch protection already enforces required checks); on-demand
  locally as a safety net. NOT in the inner loop.

### D. Containerize the orchestrator as the universal substrate
- Build a Docker image bundling the orchestrator runtime: **Dolt server + pinned `bd` (v1.0.5) +
  the dispatcher runtime + Fabro + deps** — codifying the fragile host runtime that `just bootstrap`
  explicitly cannot provision (CLAUDE.md "Beads runtime prerequisites").
- **Fabro nesting = Docker-in-Docker** (user-ratified): a nested daemon inside the image keeps
  sandboxes self-contained and host-decoupled (DooD socket-mount rejected — it re-couples to the
  host, defeating the goal). Privileged container + nesting-safe storage driver accepted; spike
  step 0 verifies Fabro targets the inner daemon. DinD used UNIFORMLY (acceptance + real work) —
  one image, one model everywhere.
- **Use it for ALL work, not just the test** — retire coupling to hand-installed host state. Real
  work clones repos fresh from GitHub (as Fabro sandboxes already do); host `/data/projects` trees
  become the maintainer's view, not the substrate.
- **Externals, all injectable:** ledger endpoint (Dolt host/port/pw — ephemeral local for
  acceptance vs shared family Dolt for real), model API key, git creds, Honeycomb key. Secret
  provisioning becomes the one concentrated host touchpoint.
- **Acceptance vs real differs only in:** ledger endpoint (ephemeral vs shared) + whether the
  external tails are wired. **Orchestrator-private ⇒ NO spec/contract change** ⇒ unblocked.
- **GitHub for the full-fidelity acceptance:** throwaway repo per run (create → factory → real `gh`
  PR open+auto-merge → validate behavior → delete). Exercises the REAL PR tail.
  - Dedicated Honeycomb **E2E environment** (separate ingest key) — keeps test spans out of `livespec`;
    enables a telemetry assertion too. Agent spans must keep raw tokens as the primary metric and
    treat provider-specific dollar estimates as overlays, so Codex evidence is never derived from
    Claude Code cost spans.
  - **Reaper** for leaked `livespec-e2e-*` repos (crash between create/delete).

---

## Sequencing (each step guarded by the prior; the acceptance net comes before the refactors)

0. **SPIKE — Fabro under Docker-in-Docker.** Nesting approach DECIDED: **Docker-in-Docker**
   (user-ratified 2026-06-15) — a full Docker daemon inside the orchestrator container, sandboxes
   nested within it. Chosen because it serves the self-containment/host-decoupling goal that the
   DooD socket-mount alternative would betray; the "DinD is an anti-pattern" warning targets
   host-build-cache sharing, which is not our case. The spike's narrowed job: verify **Fabro
   cleanly targets the INNER daemon** (`DOCKER_HOST`/default socket), and pick a nesting-safe
   storage driver (`fuse-overlayfs`/vfs). Costs accepted: privileged container; nesting overhead.
   FIRST, small.
1. **Orchestrator Docker image** (impl-beads). Dolt + pinned bd + runtime + Fabro + deps;
   injectable externals. Verify a dispatch runs against an ephemeral in-container ledger.
2. **Golden-master acceptance harness.** Fixture spec; git-jsonl tier (local/hermetic, fast);
   Beads/Fabro tier (throwaway GitHub repo + E2E Honeycomb env + behavioral assertion + teardown +
   reaper); explicit agent-runtime matrix covering Claude Code, Codex, and the future Pi harness;
   `just acceptance` target + CI merge-gate wiring on both impl repos; on-demand local.
   **= the executable swap-proof.**
3. **Memo kill** (spec-first: propose-change → revise; then both impls + retarget
   `block-auto-memory.sh`). Guarded by step 2's net.
4. **Shared `Store` extraction** into `livespec-runtime`; both impls import; converge divergences;
   version-bump + pin fan-out atomically. Guarded by step 2's net.
5. **Promote the image to the real-work substrate** — shared Dolt + fresh GitHub clones + injected
   secrets; retire host-state coupling.

## USER-ACTION gates (agents never provision these)
- Dedicated Honeycomb **E2E environment** + ingest key (for step 2).
- GitHub **repo create/delete token** (for step 2) — most privileged secret; dedicate + tightly
  scope + namespace + isolate blast radius.

## Cross-cutting discipline (every step)
- RGR verbatim for product `.py`; HOST for dispatcher self-machinery; serialize same-file edits.
- `mise exec -- git`; `--no-verify` banned; gate on `just check` + `/livespec:doctor`; end on master.
- Spec changes dogfooded via `/livespec:propose-change` → `/livespec:revise`; co-edit
  `tests/heading-coverage.json` if any H2 set changes.
- Relocate-never-drop: memo machinery recoverable at its pre-deletion SHA (cite).
- File the work as bd items under a new epic (or under `zkmn`), per repo; coordinate cross-repo via
  doctor + labels.
