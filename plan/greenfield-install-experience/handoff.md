# Handoff — greenfield-install-experience

The single resumable entry point for the **greenfield install
experience** thread: fix the six verified defects in
`docs/installation.md` so a greenfield end user reaches an in-repo
`/livespec:seed` by following the doc alone, then prove the doc by
bootstrapping the resume adopter strictly through it. A fresh session
can execute the next action from this file alone via the read-first
chain — no chat history required.

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

Fix `docs/installation.md` (livespec repo, worktree → PR → merge):

1. **Compose status LIVE** first: `bd show livespec-rh0i` (command
   above). If its comments show the doc fix already landed, skip to
   step 4.
2. **Apply the six fixes** enumerated (with their evidence) in
   `research/01-defects-and-redesign.md` §"The six verified defects" —
   headline: restructure the ordered path into an explicit greenfield
   path (settings.json → reload → `/livespec:seed` writes
   `.livespec.jsonc`) vs existing-project path; add `"ref": "release"`;
   correct the secret convention to bare `BEADS_DOLT_PASSWORD`; show
   `credential_wrapper`; pin release tags in examples; add or point to
   tenant provisioning. Also state the orchestrator is deferrable
   (seed needs core + Driver only). In the same change, add the
   agent-discipline line from the research note §"Agent-discipline
   codification" to `AGENTS.md` (or `.ai/agent-disciplines.md`).
3. **Land it** through the normal livespec PR flow (doc-only), then
   comment the PR number on `livespec-rh0i`.
4. **Run the live test** — a maintainer-attended session with working
   directory `/data/projects/resume`, following the FIXED doc as a
   real user: commit `.claude/settings.json` per §3, reload, run
   `/livespec:seed` there (product context and open questions:
   `plan/archive/resume-adopter-onboarding/research/01-onboarding-context.md`).
   File every friction point as a comment on `livespec-rh0i`; a
   friction point that needs code or doc change becomes a child
   work-item of this epic.
5. **Close** when the live test completes with zero unfixed friction:
   close `livespec-rh0i` (completion comment: the doc PR list + the
   resume seed PR) and archive this thread
   (`git mv plan/greenfield-install-experience/ plan/archive/`).

## Read-first chain (in order)

1. **`research/01-defects-and-redesign.md`** — the six verified
   defects with evidence, the fix-first rationale, the live-test
   protocol, what survives from the false start, and the
   agent-discipline line to codify. (The only companion file;
   everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan greenfield-install-experience
```
