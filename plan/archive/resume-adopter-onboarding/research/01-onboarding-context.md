# resume-adopter-onboarding — onboarding context and design frame

Why this thread exists, what is already done, and the reasoning frame
for the three onboarding tracks. The resumable execution point is the
sibling `../handoff.md`; this note carries the durable "why this
shape" reasoning.

## What the resume repo is

- **Product**: the maintainer's resume application — a real app, not a
  toy. Repo: `https://github.com/thewoolleyman/resume` (private at
  bootstrap; flipping public is a later product decision). Local
  primary checkout: `/data/projects/resume` (reachable as
  `~/workspace/resume` through the workspace symlink).
- **Inspiration**: `interactive-resume.gitlab.io` — the maintainer's
  existing interactive resume, a Vue/Nuxt.js single-page app deployed
  via GitLab Pages (local clone: `/data/projects/interactive-resume.gitlab.io`).
  The new app is NOT a port: it reimagines that product with a modern
  **AI-centric** update. The old repo is source material for content
  and product intent; its stack carries no authority over the new
  design. What "AI-centric" concretely means (conversational interface
  over the resume? agent-queryable resume data? AI-assisted tailoring
  per audience?) is deliberately OPEN — it is the central product
  question the `/livespec:seed` interview must settle with the
  maintainer before any implementation exists.
- **Dogfooding role**: the second registered livespec adopter and the
  first **greenfield** one. openbrain (adopter #1) was brownfield — an
  app that existed before adopting the workflow. resume inverts that:
  the specification comes first (`/livespec:seed` against an empty
  repo), then factory-driven implementation. This exercises the
  livespec value proposition on the path it was designed for and
  should surface gaps the brownfield path never hits (e.g. seeding
  with zero existing code to read, template choice for an app-class
  project, first factory dispatch into a repo with no toolchain).

## What is already done (evidence, all merged/pushed)

- **Manifest registration** — livespec PR #825 (merged 2026-07-03,
  master commit `5a8f0c0`): `.livespec-fleet-manifest.jsonc` gained
  `{ "repo": "resume", "profile": ["baseline", "orchestrator-plugin", "app"],
  "posture": "pinned" }`. Registered per the register-first birth
  procedure; adopter entries carry no enforced obligations yet, so the
  profile is the declared conformance TARGET, not a current claim.
  Side observation logged there: openbrain (also an app) does not
  declare the `app` layer; aligning it is optional follow-up, not
  blocking.
- **Repo bootstrap** — `thewoolleyman/resume` created on GitHub
  (private), root commit `3a4f0a7` (README only) pushed on `master`,
  `delete_branch_on_merge` enabled (aligned with the fleet
  merged-branch-cleanup invariant proposed in livespec, thread
  `plan/fleet-merged-branch-cleanup/`).
- **Epic anchor** — `livespec-5nsw` in the livespec core tenant
  (status normalized `open→backlog` at filing).

## The three onboarding tracks and their ordering

1. **Seed the spec** (`/livespec:seed`, run in the resume repo). First
   because everything downstream (template choice, toolchain, factory
   work-items) derives from what the app IS. Needs the maintainer live
   (product interview). Inputs: the inspiration repo's content and
   product intent; the AI-centric reframe question above.
2. **Adopter infrastructure**, per the openbrain precedent (adopter
   brings its OWN everything; the fleet holds no privileged path):
   `.livespec.jsonc` (naming `spec_clis`, `credential_wrapper`,
   profile mirroring the manifest declaration), a resume 1Password
   Environment + `with-resume-env.sh` wrapper (canonical wrapper
   pattern: `/data/projects/1password-env-wrapper/`), its own GitHub
   App (contents/pull-requests/workflows read-write, installed on
   `thewoolleyman/resume` only), a beads tenant on the shared Dolt
   server (TCP 127.0.0.1:3307; per-tenant SQL user + DB-scoped grant),
   and conformance wiring (`just` as task keystone, baseline checks,
   commit-refuse hook, lefthook). Sequenced AFTER seeding because the
   toolchain half of the wiring (justfile recipes, lefthook, CI)
   depends on the stack the seed interview selects.
3. **Factory-driven build.** Once seeded and wired, implementation
   work-items are filed into the resume tenant, groomed to ready, and
   dispatched through the Dispatcher/Fabro path under the janitor gate
   (`just check` + `/livespec:doctor`). The planning thread files and
   grooms; it never hand-codes the app inline.

## Open questions (settle in-thread, one at a time)

- What does "AI-centric" mean for this product? (THE seed-interview
  question; do not pre-answer it in infrastructure work.)
- Public vs private repo timing — a resume wants to be public
  eventually; when does it flip?
- Deployment target (the old app used GitLab Pages; the new repo is on
  GitHub — Pages? a Worker? decided by the seed interview's
  non-functional requirements).
- Does the resume tenant's beads DB get provisioned by hand (openbrain
  precedent) or is this the occasion to file the deferred
  `dolt-server` adopter-wiring work (see the openbrain manifest
  comment: "dolt-server registration DEFERRED")?
