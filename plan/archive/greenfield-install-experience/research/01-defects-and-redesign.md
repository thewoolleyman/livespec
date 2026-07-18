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

## Design directive (maintainer, 2026-07-04) — prompt-based installer

The fix does NOT take the form of in-place prose repairs to the old
288-line guide. The maintainer's directive reshapes the install
surface:

- **The user-facing instructions ARE a paste-able prompt** —
  `docs/livespec-installation-prompt.md` — that an LLM executes in
  the target project. It handles greenfield AND brownfield (and
  detects already-governed as the verify-only path), walks the agent
  through every requirement up to seed-readiness, and prompts the
  user for exactly two choices — the Driver(s) (claude / codex /
  both) and the orchestrator backend (beads-fabro recommended;
  git-jsonl with requirements and trade-offs; defer allowed) — using
  the harness's structured question facility with a recommendation
  first.
- **`docs/installation.md` becomes minimal** — what livespec is and
  how to run the prompt in each supported harness (Claude Code and
  Codex today).
- **The prompt is idempotent** — survey before mutate; already-set-up
  components are skipped; missing or drifted ones are added or
  repaired; a final report table proves a no-change re-run is a
  no-op.

Each of the six defects maps into the prompt rather than into prose
fixes: (1) the prompt forbids hand-authoring `.livespec.jsonc` (seed
writes it — its Phase 4); (2) every marketplace/install pins
`release`, and the idempotency rules upgrade an unpinned existing
entry; (3) the beads-fabro description names the single bare
`BEADS_DOLT_PASSWORD`; (4) and the `credential_wrapper` declaration;
(5) `compat` pins are described as concrete release tags, never
branch names; (6) tenant provisioning is explicitly post-seed
infrastructure per the orchestrator plugin's own documentation — out
of the install prompt's blocking path (authoring that full procedure
remains follow-up work where that plugin's docs live).

## The dogfooding loop (fix-first, then live test)

Land the prompt-based installer FIRST (the six defects are already
evidence-backed; walking a maintainer-attended bootstrap into known
breakage wastes the interview), THEN run the resume bootstrap
strictly by the published path, as a real user, from inside
`/data/projects/resume`:

- run the installation prompt there exactly as `docs/installation.md`
  says an end user would;
- then run `/livespec:seed` there, maintainer-attended (product
  inspiration: `interactive-resume.gitlab.io`, reimagined AI-centric
  — the archived false-start thread's research note,
  `plan/archive/resume-adopter-onboarding/research/01-onboarding-context.md`,
  still carries the product context and open questions; it remains
  valid INPUT even though its coordination model was wrong);
- every friction point the live test surfaces gets filed against this
  thread and folded back into the prompt.

What was and was not a false start: the manifest registration
(livespec PR #825) and the resume repo bootstrap (root commit,
public repo, `delete_branch_on_merge`) remain valid — those are
fleet-side and repo-side facts respectively. The false start was the
COORDINATION MODEL: adopter-side onboarding planned in livespec's
`plan/` tree with seeding driven from a livespec session
(epic `livespec-5nsw`, closed with a supersession comment; thread
archived).

## Agent-discipline codification

Per maintainer direction (2026-07-04), NOT a one-liner in `AGENTS.md`
and NOT the earlier vague "orient from published user docs" phrasing:
a dedicated progressively-loaded topic file,
**`.ai/adding-an-adopter.md`**, referenced from `AGENTS.md` with the
explicit trigger "read BEFORE touching `.livespec-fleet-manifest.jsonc`
to register a new adopter repo, and before planning or driving any
adopter's onboarding". The file separates the two roles (registration
= fleet-maintainer work in livespec; onboarding = end-user work in
the adopter repo) and names the explicit published-path files
(`docs/installation.md` → `docs/livespec-installation-prompt.md`)
rather than hand-waving at them. Rationale: the false start happened
precisely because the session's context was saturated with fleet
discipline and never consulted `docs/installation.md`, despite
livespec's README pointing at it.
