# Handoff — greenfield-install-experience

The single resumable entry point for the **greenfield install
experience** thread: replace the old 288-line install guide with the
paste-able idempotent installer prompt
(`docs/livespec-installation-prompt.md`, pointed at by a minimal
`docs/installation.md`) that carries an end user to an in-repo
`/livespec:seed`, then prove it by bootstrapping the resume adopter
strictly through it. A fresh session can execute the next action from
this file alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The resume adopter
  (`github.com/thewoolleyman/resume`, local `/data/projects/resume`)
  false-started: its onboarding was planned through fleet-internal
  machinery instead of the published end-user path
  (`docs/installation.md` — livespec's README points to it). The
  maintainer's correction, the six evidence-backed doc defects, the
  fix-first-then-live-test rationale, and what remains valid from the
  false start are all in the read-first chain's
  `research/01-defects-and-redesign.md`. The false-start thread is
  archived at `plan/archive/resume-adopter-onboarding/` (its research
  note remains valid PRODUCT input for the eventual seed interview);
  its epic `livespec-5nsw` is closed with a supersession comment.
- **Epic anchor:** `livespec-rh0i` (livespec core tenant, `backlog`).
  Status is READ from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-rh0i
  ```
- **Working model.** The doc fix is livespec-repo work (worktree → PR
  → merge, doc-only commit, no red-green ritual). The live test is
  END-USER work: it runs from inside `/data/projects/resume` using
  only published artifacts — no livespec clone consulted, no fleet
  credential, no core-tenant writes. Keep the two roles separate; the
  live test is void if it leans on maintainer machinery.
- **⚑ Golden rule.** FILE ripe work + GROOM it; never hand-code
  factory-safe implementation inline in the planning session. The doc
  rewrite itself is spec-side core-docs work a maintainer-attended
  session executes directly through the normal PR flow.
- **Resume command:**
  `/livespec-orchestrator-beads-fabro:plan greenfield-install-experience`.

## The next action

Run the live test of the prompt-based installer. (The installer
itself — `docs/livespec-installation-prompt.md`, the minimal
`docs/installation.md` pointing at it, and `.ai/adding-an-adopter.md`
+ its `AGENTS.md` reference — lands with this thread's doc-work PR;
the PR number is commented on `livespec-rh0i`. If that PR is still
open, finishing its review/merge is the immediate step.)

1. **Compose status LIVE** first: `bd show livespec-rh0i` (command
   above) — its comments carry the doc-work PR number and any
   friction already filed.
2. **Run the installation prompt in the resume repo** exactly as an
   end user: a maintainer-attended session with working directory
   `/data/projects/resume`, following `docs/installation.md`'s "Run
   it" section for Claude Code (fetch the raw
   `livespec-installation-prompt.md` and follow it). No livespec
   clone consulted, no fleet credential, no maintainer shortcut.
3. **Then run `/livespec:seed` there**, maintainer-attended (product
   context and open questions:
   `plan/archive/resume-adopter-onboarding/research/01-onboarding-context.md`).
   File every friction point — from the prompt run AND the seed —
   as a comment on `livespec-rh0i`; a friction point needing code or
   doc change becomes a child work-item of this epic.
4. **Close** when the live test completes with zero unfixed friction:
   close `livespec-rh0i` (completion comment: the doc PR list + the
   resume seed PR) and archive this thread
   (`git mv plan/greenfield-install-experience/ plan/archive/`).

## Read-first chain (in order)

1. **`research/01-defects-and-redesign.md`** — the six verified
   defects with evidence, the maintainer's prompt-based-installer
   design directive, the live-test protocol, what survives from the
   false start, and the `.ai/adding-an-adopter.md` codification. (The
   only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan greenfield-install-experience
```
