# Handoff — github-app-auth

The single resumable entry point for the **fleet GitHub App-token auth**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The coordination anchor for standardizing the fleet on
  GitHub **App installation tokens** for ALL automated GitHub operations —
  factory dispatch AND standalone agent worktree commits — **retiring the fleet
  PAT** (`LIVESPEC_FAMILY_GITHUB_TOKEN`) and **removing the human OAuth token
  from the agent path**. The current model is fragmented across three identities
  (factory PAT, human `gho_` OAuth, CI `GITHUB_TOKEN`), none right for
  automation; see `research/01-design.md` for the full why + the four pillars.
- **Epic anchor:** `livespec-2ef0` (core tenant, `backlog`). Status is READ from
  the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-2ef0
  ```
- **Working model.** This is a **CORE coordination thread** — resume it from a
  core session. The code slices are **cross-tenant**: the **factory** slice is
  groomed + built from a `livespec-orchestrator-beads-fabro` session; the
  **host/adopter** slices from their own sessions. Factory changes are careful
  **self-modifications** — human-approved admission, never auto-dispatch blind.
- **⚑ Golden rule.** FILE + GROOM ripe work; DISPATCH ready, factory-safe slices
  through the factory under the janitor gate; NEVER hand-code inline. Every repo
  change is worktree→PR→merge, never `--no-verify`.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan github-app-auth`.

## The next action

**Groom the epic (`livespec-2ef0`) into dependency-layered slices** from the
appropriate session:

```
/livespec-orchestrator-beads-fabro:groom livespec-2ef0
```

The following is **grooming guidance**, explicitly NOT a shadow `[ ]`/`[x]`
checklist — status is composed from the ledger, there is no shadow queue.
Proposed slice shape (each a careful self-mod — groom + human review; do NOT
auto-dispatch blind):

1. **Shared credential provider + git credential helper with first-class
   remint** — the core primitive. Hard acceptance = **survives a >1-hour run /
   re-mints transparently** (Pillar 1).
2. **Factory** [beads-fabro] — route `real-work-dispatch.sh` + the entrypoint +
   all dispatch paths through **target-scoped `credential_wrapper` resolution**,
   retiring the hardcoded fleet PAT. Reshape `bd-ib-gsl` into this slice.
3. **Standalone / host** [host/fleet] — wire the git credential helper as the
   agent-context credential, drop the ambient `gh` OAuth from the agent path,
   scrub `GH_TOKEN` (Pillar 3).
4. **Enforcement guardrails** — the `github_auth_guard` PreToolUse hook (sibling
   of `beads_access_guard`) + document the VPS **per-tenant-OS-user** boundary as
   the real enforcement (Pillar 4).
5. **Retire `LIVESPEC_FAMILY_GITHUB_TOKEN`** from the fleet Environment +
   restrict the fleet App's install scope to fleet repos only.
6. **Adopter dogfood acceptance** — openbrain via its own App with the fleet
   secrets UNREADABLE (Pillar 2 dogfood). Fold `C16`; close `bd-ib-p2e` as
   obsolete.

## Read-first chain (in order)

1. `research/01-design.md` — the why, the decision, the research basis, the four
   pillars + mechanics, existing items to fold in, and open questions. The only
   companion; everything else needed is in this handoff.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan github-app-auth
```
