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
