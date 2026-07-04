# Adding an adopter repo

Read this when registering a new adopter in
`.livespec-fleet-manifest.jsonc`, or when planning or driving the
onboarding of any adopter repo the maintainer owns.

## Two roles — do not mix them

Adding an adopter is TWO jobs in two different places:

1. **Fleet-maintainer registration** (happens HERE, in livespec):
   add the adopter entry to the `adopters` array of
   `.livespec-fleet-manifest.jsonc` via the normal worktree → PR →
   merge flow. Entry shape: `{ repo, profile, posture }` — profile is
   `baseline` plus any additive layers (`fleet-infra`,
   `orchestrator-plugin`, `app`); posture is `released` / `pinned` /
   `none`. Precedents: `openbrain` (brownfield), `resume`
   (greenfield). Register-first is deliberate: a declared-but-unwired
   adopter should surface as a conformance finding, not stay
   invisible.

2. **Adopter-side onboarding** (happens IN THE ADOPTER REPO, never
   here): everything else — plugin enablement, `/livespec:seed`,
   config, credentials, tenant, conformance wiring — is END-USER
   work, driven from inside the adopter repo by livespec's published
   install surface: **`docs/installation.md`** (this repo) points the
   user's agent at the paste-able idempotent installation prompt
   **`docs/livespec-installation-prompt.md`**. Run that prompt in the
   adopter repo exactly as any end user would. Do NOT plan an
   adopter's onboarding in livespec's `plan/` tree, do NOT drive its
   seed from a livespec session, and do NOT substitute fleet-internal
   machinery (the fleet credential wrapper, the core tenant,
   maintainer plan threads) for the published path.

## Why this rule exists

The resume onboarding false-started (2026-07-04): its onboarding was
planned in livespec's `plan/` tree with seeding to be driven from a
livespec session. A real adopter has no livespec clone — the ONLY
thing it has is the published install surface. Every adopter
onboarding is therefore also a live test of the installation prompt:
follow it exactly, and file every friction point against livespec
rather than working around it with maintainer knowledge.

## Greenfield specifics

- `/livespec:seed` needs only core + Driver enabled; the orchestrator
  choice can be deferred (the installation prompt offers this) until
  implementation work starts.
- Seed WRITES `.livespec.jsonc` itself — never hand-author the config
  before seeding.
- The adopter brings its OWN credential wrapper, GitHub App, and
  work-items tenant (the fleet is adopter #0 with no privileged
  path); those arrive with the post-seed infrastructure step, not
  before seeding.
