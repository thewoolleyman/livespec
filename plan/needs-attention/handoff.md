# needs-attention — track handoff (overseer run-prompt)

**Track:** `needs-attention` · **Repo:** `thewoolleyman/livespec` ·
**Ledger epic anchor:** `livespec-bj9x` (read status LIVE from the
ledger; never trust a status written here).

**Read-first chain (open these, in order, before acting):**

1. The `livespec-bj9x` ledger comments, top-to-bottom — the newest is the
   **2026-07-07 CODE-SLICE WAVE PROGRESS** comment, a self-contained live-state
   snapshot. Read via the wrapper: `source
   /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C
   /data/projects/livespec show livespec-bj9x`.
2. `research/design.md` — the settled design + the full cross-repo rollout.
3. `research/glossary.md` — every term used below.

## Current state (2026-07-07 late session; verify LIVE against the ledger)

Code-slice wave outcome (the 3 straddle-remainders; all spec halves already
ratified — BR2 v004, OR3 v017, CN1 v016):

- **OR3-code** (`bd-gj-8nh`, git-jsonl): DONE/closed — PR #196 merged, CI-green,
  live-exercised. (The dispatcher post-merge janitor went RED on the KNOWN
  `bd-gj-9sj` gap — a fresh janitor worktree missing the gitignored
  `dev-tooling/branch-protection.sh` — NOT the code. That gap now blocks *clean*
  factory completion for git-jsonl: code lands + CI-green but the item is left
  ACTIVE by the janitor. Follow-up below.)
- **BR2-code** (`livespec-driver-codex-01a`): DONE/accepted — PR #79 merged,
  post-merge janitor GREEN (driver-codex has no worktree-pack gap). Zero stale
  `orchestrate` skill refs remain; `drive` present.
- **CN1-code** (`livespec-console-beads-fabro-xb7bcr`, console/**Rust**): BLOCKED.
  Two factory-infra walls, one fixed: (1) the Fabro sandbox image is a uv/Python
  image with NO Rust → FIXED by giving the console its own target-local `.fabro`
  workflow (PR #103, `3fa2d5c`: generic workflow + one rustup-1.92.0 prepare step
  + verbatim `workflow.fabro` + `prompts/`). (2) The fleet Fabro GitHub App token
  has a HARD 60-min TTL, minted once at dispatch with no per-node refresh; the
  console cold Rust build ran ~67 min, so the token was EXPIRED at the push stage
  → `Invalid username or token`. DURABLE FIX = JIT-refresh the token at the
  push/PR node (tracked as a candidate slice on factory-safe epic `livespec-nrdk`).
  Re-dispatch alone will NOT work (ephemeral sandbox ⇒ cold build again ⇒ same
  expiry). **CN1 stays blocked until the token-refresh fix lands.**

Maintainer side-directives this session (both DONE):

- **ob-wu8a** (openbrain, `ob-wu8a`): an operator-host item (extend
  `verify-openbrain-env.sh` to probe 4 factory-dispatch secrets) that is
  **NOT factory-safe** — its verification needs real secrets that must never
  enter a sandbox. Steered the openbrain2 Codex session to implement + verify it
  **HOST-SIDE** (probe-only, gate green), landed `4d5961b`, closed. Verified.
- **Codex `needs-attention` picker confusion** (two `needs-attention` skills,
  indistinguishable): root-caused — both orchestrators enabled host-wide in Codex
  (no per-project scoping); **git-jsonl has NO `.codex-plugin`** so its skills
  fall back to the Claude `SKILL.md`; + description drift. Captured as a DEFERRED
  plan (below), per maintainer direction NOT tackled in this track.

New plan threads OPENED this session (deferred; separate epics — do NOT drive
them from this track):

- **factory-safe-by-default** (epic `livespec-nrdk`, PR #913): factory-safe by
  default + a mechanical `not-factory-safe:<reason>` admission gate + capability
  widening + a host-only needs-attention lane. Carries the CN1 token-TTL fix as a
  candidate slice. Resume: `/livespec-orchestrator-beads-fabro:plan factory-safe-by-default`.
- **orchestrator-surface-parity** (epic `livespec-xfqd`, PR #914): git-jsonl
  becomes a FULL PEER — identical cross-runtime + cross-orchestrator skill
  surfaces, mechanically enforced (git-jsonl gains `drive`/`groom`/`plan`/
  `list-plan-threads` + a full `.codex-plugin`). Decision = full peer (supersedes
  OR3 v017 reduced scope). 6-slice plan in its `research/design.md`. Resume:
  `/livespec-orchestrator-beads-fabro:plan orchestrator-surface-parity`.

## How to drive this track (remaining phase)

1. **CN1** (`xb7bcr`): BLOCKED on the factory token-TTL fix (JIT-refresh at the
   push node; candidate slice on `livespec-nrdk`). Do NOT burn re-dispatches until
   that lands (same 67-min cold build ⇒ same expiry). When it lands, re-dispatch
   via the console-local `--workflow` (fleet tenant — no FABRO_HOME) → live-exercise
   → accept-on-behalf.
2. **CO1** (`livespec-bj9x.1`, core reaper refactor) + **CO2** (file the
   `needs-attention-internal` + `needs-attention-fleet` local/unsynced CORE
   skills; CO2 NOT filed yet): both core-tenant → dispatch churns the core pin →
   do from a FRESH session / at session-end, after `/reload-plugins`.
3. **bd-ib-z2ctra** (openbrain durable unblock): still a pending maintainer
   groom-cut; its target-local-workflow pieces (D1/D2a) now relate to
   `factory-safe-by-default`. Not on the needs-attention critical path.
4. **EXIT GATE** (maintainer-owned): close `livespec-bj9x` when every piece is
   done — currently BLOCKED on CN1 (token fix) + CO1/CO2.

Open needs-attention refinement surfaced by dogfooding (filed
`livespec-runtime-ego`, backlog): the shipped `needs-attention` composes
spec-`next` as a USELESS POINTER (`"Run the spec-side next primitive"` + a
`codex exec livespec:next` handoff) instead of DELEGATING to it and inlining the
actual actionable spec items (or nothing). Per design §"Read primitives" it must
invoke spec-`next` cross-plane, adapt the ranked result, surface it only when
real, and fail soft — mirroring how hygiene-scan already inlines real findings.

## Gate map

| Step | Overseer does | Maintainer gate |
|---|---|---|
| Dispatch ready code slices | dispatches through the factory; closes each landed item after journaling live-exercise evidence | **accept-on-behalf is STANDING for this track** (no per-batch ask) |
| Spec propose/revise | drives push + spawns independent CODEX review; surfaces ratification | **spec ratification** (+ mandatory independent review) |
| Next-wave code | files ripe slices; dispatches through the factory | groom / approve per item as needed |
| Close | surfaces the exit gate | **exit gate** (close the epic) |

## Standing authorizations + operating disciplines (this track only)

Maintainer-declared for the `needs-attention` track (epic `livespec-bj9x`)
**only** — NOT system-wide, NOT permanent; these expire when the epic closes.
Also journaled on the epic (read them there too, via the read-first chain).

- **Auto-acceptance (accept-on-behalf) is authorized for EVERY item in this
  track, and PERSISTS ACROSS overseer handoffs.** A fresh overseer does NOT
  re-ask — it closes each landed item (`acceptance → done` via the `accept:`
  valve) without prompting the maintainer. **Guardrail (unchanged):** accept an
  item ONLY after live-exercise evidence is journaled on it (the "done means
  exercised live" discipline); weak or absent evidence → HALT and surface that
  item, never accept on faith.
- **Do not surface a handoff / rotation gate until the overseer's context
  exceeds ~50%.** Below that, keep driving autonomously — never park ready work
  behind a "my context is heavy" rationale.
- **Run non-factory work in scoped subagents** (doc PRs, spec propose-change /
  revise authoring, independent adversarial reviews, grep-migrations, root-cause
  investigations) to keep the overseer context lean; the overseer retains plan /
  dispatch / synthesis and the maintainer-gated exit.
- **Clean-exit before ANY handoff (maintainer-declared 2026-07-07).** Before ANY
  handoff / rotation / session-exit, LAND or EXIT every background agent,
  sub-agent, Monitor, and background subprocess THIS session spawned, so the
  maintainer can fully exit and restart with **nothing orphaned**. Verify none
  remain: no running `dispatcher.py loop`, no live sub-agent, every spawned
  worktree reaped or its PR merged. (The standing Fabro node-pool daemons
  (`fabro server …`) and the Dolt SQL server are HOST INFRA, NOT session-spawned —
  they do not block exit.) A handoff that leaves live background work is
  INCOMPLETE.

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
- **NEVER hand-edit `~/.claude/plugins/installed_plugins.json`**; **NEVER lever
  the currency gate** (no `LIVESPEC_CORE_PLUGIN_ROOT` override, no `--no-verify`)
  per `.ai/ci-gate-discipline.md`; if a livespec CLI reports "stale",
  `/reload-plugins` and retry.
- Independent adversarial review is REQUIRED before every spec ratification — use
  a separately-spawned **CODEX** sub-agent (Fable is out of free usage; Opus 4.8
  is an acceptable fallback).
- **Operator-host items are NOT factory-safe** — their verification needs real
  secrets/host state that must never enter a sandbox; implement + verify them
  HOST-SIDE (the ob-wu8a precedent), never dispatch them at the factory.
- Follow-ups (captured, don't drop): `bd-gj-9sj` (git-jsonl janitor worktree-pack
  hydration — blocks clean git-jsonl factory completion); the CN1 token-TTL fix
  (on `livespec-nrdk`); git-jsonl pre-existing skill-count drift; the
  `livespec-runtime-ego` spec-next-inlining defect.
- Loose ends REAPED this session: the git-jsonl `worktrees/janitor-bd-gj-8nh`
  diagnostic worktree; all this session's sub-agent worktrees (each self-reaped).
- Observability/telemetry is deferred (`design.md` §"Deferred") — out of this rollout.
