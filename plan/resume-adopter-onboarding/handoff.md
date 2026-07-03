# Handoff — resume-adopter-onboarding

The single resumable entry point for the **resume adopter onboarding**
thread: take the resume repo from bootstrapped skeleton to
fully-onboarded livespec adopter — seed interview, adopter wiring,
then factory-driven build. A fresh session can execute the next action
from this file alone via the read-first chain — no chat history
required.

## For a fresh session — read first

- **What this is.** `thewoolleyman/resume` (local primary checkout
  `/data/projects/resume`) is the second registered livespec adopter
  and the first GREENFIELD one — the maintainer's resume app,
  inspired by the existing Vue/Nuxt.js `interactive-resume.gitlab.io`
  (local clone `/data/projects/interactive-resume.gitlab.io`) but
  reimagined with a modern AI-centric update. Registration
  (livespec PR #825) and repo bootstrap (root commit, private GitHub
  repo, `delete_branch_on_merge` on) are DONE; full evidence, the
  three-track design frame, and the open product questions are in the
  read-first chain's `research/01-onboarding-context.md`.
- **Epic anchor:** `livespec-5nsw` (livespec core tenant, `backlog`).
  Status is READ from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-5nsw
  ```
- **Working model.** A livespec-core session coordinates (the adopter
  registration and this thread live in core); the seed interview and
  all resume-repo commits happen IN the resume repo
  (`/data/projects/resume`, its own worktree → PR → merge discipline
  once hooks exist there); infrastructure that is host-level (1Password
  Environment, GitHub App, Dolt tenant) is OPERATOR work surfaced as
  explicit gates, mirroring the openbrain onboarding precedent —
  the adopter brings its OWN credential wrapper, App, and tenant; no
  fleet-credential fallback.
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready,
  factory-safe slices through the factory — NEVER hand-code the resume
  app inline in the planning session. The seed interview itself is
  maintainer-attended spec work, not factory work.
- **⚑ Ordering constraint.** Seed BEFORE toolchain wiring: the
  justfile/lefthook/CI half of adopter wiring depends on the stack the
  seed interview selects. Do not scaffold a toolchain first and let it
  anchor the product decisions.
- **Resume command:**
  `/livespec-orchestrator-beads-fabro:plan resume-adopter-onboarding`.

## The next action

Run the `/livespec:seed` interview for the resume app, maintainer
attended, in a session whose working directory is
`/data/projects/resume`:

1. **Compose status LIVE** first: `bd show livespec-5nsw` (command
   above) and confirm the resume repo state is still the bootstrap
   skeleton (`git -C /data/projects/resume log --oneline` shows the
   README root commit; a longer history means a prior session advanced
   the thread — re-read the epic's comments before proceeding).
2. **Prepare the interview inputs**: skim the inspiration repo's
   content (`/data/projects/interactive-resume.gitlab.io` — the
   resume CONTENT and product intent are the inputs; its Vue/Nuxt
   stack carries no authority), and bring the open product questions
   from `research/01-onboarding-context.md` §"Open questions" — the
   central one being what "AI-centric" concretely means for this
   product. Ask them one at a time, recommendation first.
3. **Run `/livespec:seed`** in the resume repo and land the seeded
   `SPECIFICATION/` tree on the resume repo's master via a plain
   branch → `gh pr create` → merge (the repo has NO hooks, CI, or
   required checks yet — those arrive with the infrastructure track —
   so the PR is reviewable history, not a gate; `delete_branch_on_merge`
   is already on, so the head branch cleans itself up).
4. **Record the outcome on the epic**
   (`bd -C /data/projects/livespec comment livespec-5nsw "<text>"`),
   then refresh THIS handoff so the next action becomes the
   infrastructure track (`.livespec.jsonc`, `with-resume-env.sh` +
   resume 1Password Environment, resume GitHub App, Dolt tenant,
   conformance wiring — the full list and its openbrain-precedent
   rationale are in the research note §"The three onboarding tracks").

## Read-first chain (in order)

1. **`research/01-onboarding-context.md`** — what the resume app is,
   the completed-work evidence, the three-track design frame with its
   ordering rationale, and the open product questions for the seed
   interview. (The only companion file; everything else needed is in
   this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan resume-adopter-onboarding
```
