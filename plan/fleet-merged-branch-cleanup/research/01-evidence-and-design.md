# Evidence and design — fleet merged-branch cleanup

Provenance: surfaced by the fleet-followups wrap-up audit (2026-07-03/04,
`plan/archive/fleet-followups/handoff.md` §"Session 15 (continued)" in the
`livespec` repo): seven lingering merged-PR head branches had to be
hand-deleted across three sibling repos, because those repos never delete
merged heads while core does. Maintainer directive (2026-07-04): "they
should all clean up consistently, with DRY implementation via dev-tooling
shared logic."

## Evidence (verified live 2026-07-04 via `gh api repos/thewoolleyman/<repo>`)

| repo | class | `delete_branch_on_merge` | non-master/release remote branches |
|---|---|---|---|
| livespec | core | **true** | 2 |
| livespec-driver-claude | driver-plugin | **true** | 0 |
| livespec-dev-tooling | enforcement-suite | false | ≥100 (page cap) |
| livespec-orchestrator-beads-fabro | impl-plugin | false | ≥100 (page cap) |
| livespec-orchestrator-git-jsonl | impl-plugin | false | 98 |
| livespec-runtime | library | false | 77 |
| livespec-driver-codex | driver-plugin | false | 45 |
| livespec-console-beads-fabro | console | false | 39 |
| openbrain | adopter (`pinned`) | false | 1 |

The two repos WITH the setting are clean; the six without it have
accumulated roughly 460 stale branches between them. GitHub's native
`delete_branch_on_merge` repo setting is the proven mechanism — no
workflow or bot is needed for the go-forward behavior.

Branch counts are an UPPER bound on sweepable branches: some are heads of
OPEN PRs or unmerged live work (e.g. another session's active track).
Only MERGED heads may be swept.

## Design — four pieces plus a decision

1. **One-time setting rollout (operator).** For each repo with `false`:
   `gh api -X PATCH repos/thewoolleyman/<repo> -F delete_branch_on_merge=true`.
   Changing repo settings needs GitHub *Administration* permission; the
   fleet App installation token was provisioned for contents/PR/workflows
   scopes, so ASSUME the operator's own `gh` auth does the rollout —
   verify the App's actual permissions in-thread before deciding to
   automate rollout through the factory.

2. **One-time stale sweep (dev-tooling code, factory-built; operator-run).**
   A tested Python module in `livespec-dev-tooling` (per that repo's
   shell-logic-hardening rule — substantive logic never lives in ad-hoc
   shell; adjacent epic: `livespec-dev-tooling-9j8`). Behavior: for each
   fleet repo (read `.livespec-fleet-manifest.jsonc` from livespec core —
   never a hardcoded repo list), enumerate remote branches; classify a
   branch SWEEPABLE only if it is the head of a MERGED pull request (query
   PRs by head) AND has no open PR AND is not `master`/`release`;
   `--dry-run` default with a per-repo report; deletion via the GitHub
   API. Never classify by "tip reachable from master" alone — rebase-merge
   rewrites SHAs, so PR-state is the reliable signal (the fleet merges by
   rebase). NEVER delete a branch that is not a merged-PR head — that is
   the never-touch-another-session's-branch rule, mechanized.

3. **The durable DRY enforcement (dev-tooling shared logic, factory-built).**
   A fleet-conformance Verifier in `livespec-dev-tooling` asserting
   `delete_branch_on_merge == true` for every repo in
   `.livespec-fleet-manifest.jsonc`'s `fleet` array — the same
   manifest-driven pattern as the existing fleet-conformance checks, so
   every consumer repo enforces it identically (DRY: one implementation,
   fleet-wide wiring via the shared package). Always wired into
   `just check`; one warn-vs-fail env lever for token-less contexts
   (local runs without a GitHub token WARN; CI, which has a token, FAILS)
   — the carve-out-as-severity-lever discipline, never a silent skip.

4. **Provisioning parity (dev-tooling).** New fleet members must be born
   with the setting: fold the PATCH (or a post-create assertion) into the
   member-onboarding path (`livespec_dev_tooling/fleet/wire_fleet_member.py`
   or its documented onboarding procedure), so the Verifier never fires
   for a freshly-wired repo.

**Decision for the maintainer (kickoff):**

- **Adopter scope.** Does the invariant bind adopters (openbrain, posture
  `pinned`) or only the `fleet` array? Recommendation: enforce for the
  fleet array; for adopters, PATCH openbrain opportunistically (same
  owner) but keep the Verifier fleet-only — adopters own their repos, and
  the adopter contract (livespec core
  `SPECIFICATION/non-functional-requirements.md` §"Fleet membership
  contract") deliberately imposes less.

**Self-resolved (recommendation, revisit at kickoff only if challenged):**

- **Spec codification.** A one-clause repo-settings invariant belongs in
  livespec core's fleet-membership contract only if it stays meaningful
  after rollout — it does (it binds future repos), so file a
  `/livespec:propose-change` against
  `SPECIFICATION/non-functional-requirements.md` §"Fleet membership
  contract" naming the invariant + the Verifier as its enforcement, and
  let the maintainer accept/reject at the next attended
  `/livespec:revise`. Content is maintainer-gated as always.

## Adjacent, deliberately OUT of scope

- **Local branch/worktree cruft** (the ~16/17/26 stale LOCAL branches
  observed in core/beads-fabro/dev-tooling clones, and reaper extensions
  for them) — different mechanism (host clones, not GitHub), different
  risk profile (local branches may be unmerged live work). File
  separately if wanted; do not fold into this thread.
- **The dispatcher's own PR flow** — today's factory PRs merge with
  branches left behind on repos lacking the setting; piece 1 fixes that
  class fleet-wide, so no dispatcher change is needed.
