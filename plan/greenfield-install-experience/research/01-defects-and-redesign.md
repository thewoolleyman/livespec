# greenfield-install-experience — verified defects and the redesign frame

Why this thread exists: the resume adopter's onboarding false-started
because the session drove it through fleet-internal machinery (a plan
thread in livespec, seeding planned FROM livespec) instead of the
published end-user path. The maintainer's correction (2026-07-04):
a real greenfield adopter has no livespec clone — it bootstraps from
`docs/installation.md` inside its own repo. This thread makes that
doc actually carry a greenfield user to a successful in-repo
`/livespec:seed`, then proves it by bootstrapping
`github.com/thewoolleyman/resume` strictly through the doc.

The resumable execution point is the sibling `../handoff.md`; this
note carries the evidence and the design frame.

## The six verified defects in `docs/installation.md`

Each verified directly against the named sources on 2026-07-04.

1. **Ordering contradicts seed's design.** The doc's §4 and Quick
   Reference (steps 3 and 5) have the user author and commit
   `.livespec.jsonc` BEFORE running `/livespec:seed`. But core's
   `prose/seed.md` states seed "is the only operation designed to run
   before `.livespec.jsonc` exists"; the seed CLI WRITES
   `.livespec.jsonc` atomically alongside the spec tree, and seed
   refuses (exit 3, idempotency) when any template-declared target
   file already exists. A doc-following greenfield user either
   hand-authors a config seed would have written (divergence) or
   trips the refusal. Fix: restructure around an explicit
   **greenfield path** (settings.json → reload → seed writes the
   config) vs an **existing-project path**.
2. **Missing `"ref": "release"`.** §3's `extraKnownMarketplaces`
   example omits `ref`; every real committed `.claude/settings.json`
   in the fleet (livespec's own included) pins `"ref": "release"` on
   all three marketplaces — released plugin builds, per the
   pins-track-releases rule. Doc-following users silently get
   master-built plugins.
3. **Stale secret convention.** §5(3) documents
   `BEADS_DOLT_PASSWORD_<tenant_with_underscores>` plus a
   per-tenant→bare mapping. The current contract (livespec
   `.claude/CLAUDE.md` §"Beads runtime prerequisites", post-dating the
   doc's 2026-07-01 revision) is a single bare `BEADS_DOLT_PASSWORD`
   injected by the tenant's own `credential_wrapper` — NO per-tenant
   suffix, NO mapping; isolation comes from the per-tenant SQL user +
   DB-scoped grant.
4. **`credential_wrapper` never shown.** Both real adopter configs
   carry a top-level `credential_wrapper` key
   (livespec `.livespec.jsonc:22`; openbrain `.livespec.jsonc:40`).
   The doc's §4 examples omit it and never say where the wrapper is
   declared.
5. **`"pinned": "master"` placeholders.** §4's `compat.pinned`
   examples say `master`; an adopter with posture `pinned` pins a
   concrete release tag (openbrain pins `v0.5.0`). The examples
   should show a release tag and say why.
6. **No tenant-provisioning procedure.** §5 presumes a running Dolt
   server AND an existing per-tenant SQL user with a DB-scoped grant,
   but provides no procedure or pointer for creating the tenant (the
   fleet's machinery lives in the `dolt-server` repo). This is the
   wall a greenfield beads adopter hits; even openbrain's dolt-server
   registration is still deferred (see the manifest comment).

Plus one structural improvement (not a defect): the doc frames
"always three plugins", but `/livespec:seed` needs only core +
Driver. State explicitly that the orchestrator is deferrable until
implementation work starts, and that git-jsonl-first (zero
infrastructure) with a later beads migration is a valid greenfield
route the doc already half-promises ("You can start on git-jsonl and
migrate").

## The dogfooding loop (fix-first, then live test)

Fix the six known defects FIRST (they are already evidence-backed;
walking a maintainer-attended bootstrap into known breakage wastes
the interview), THEN run the resume bootstrap strictly by the fixed
doc, as a real user, from inside `/data/projects/resume`:

- commit `.claude/settings.json` per the fixed §3;
- reload plugins; run `/livespec:seed` there, maintainer-attended
  (product inspiration: `interactive-resume.gitlab.io`, reimagined
  AI-centric — the archived false-start thread's research note,
  `plan/archive/resume-adopter-onboarding/research/01-onboarding-context.md`,
  still carries the product context and open questions; it remains
  valid INPUT even though its coordination model was wrong);
- every friction point the live test surfaces gets filed against this
  thread and folded back into the doc.

What was and was not a false start: the manifest registration
(livespec PR #825) and the resume repo bootstrap (root commit,
public repo, `delete_branch_on_merge`) remain valid — those are
fleet-side and repo-side facts respectively. The false start was the
COORDINATION MODEL: adopter-side onboarding planned in livespec's
`plan/` tree with seeding driven from a livespec session
(epic `livespec-5nsw`, closed with a supersession comment; thread
archived).

## Agent-discipline codification

One durable line for `AGENTS.md` (or `.ai/agent-disciplines.md`) in
livespec, filed as part of this thread's doc work: **when the task is
dogfooding an end-user path, orient from the published user docs
first (README → docs/), not from fleet-internal machinery; the
fleet's own conventions are the maintainer's view, not the user's.**
Rationale: the false start happened precisely because the session's
context was saturated with fleet discipline and never consulted
`docs/installation.md`, despite livespec's README pointing at it.
