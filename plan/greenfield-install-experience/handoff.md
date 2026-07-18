# Handoff — greenfield-install-experience

The single resumable entry point for the **greenfield install
experience** thread: the old 288-line install guide has been replaced
by the paste-able idempotent installer prompt
(`docs/livespec-installation-prompt.md`, pointed at by a minimal
`docs/installation.md`) and live-tested through the resume adopter
(`github.com/thewoolleyman/resume`). The remaining thread work is to
resolve the live-test residual filed as `livespec-p340`, then close the
epic and archive the thread. A fresh session can execute the next
action from this file alone via the read-first chain — no chat history
required.

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
- **Open child residual:** `livespec-p340` — seed exit-3 refusal is
  silent because the seed supervisor maps the failure to exit code 3
  without emitting the `LivespecError` / structured-finding message on
  stderr. It was found during the 2026-07-04 resume verification and
  linked under `livespec-rh0i` on 2026-07-18.
- **Working model.** The doc fix is livespec-repo work (worktree → PR
  → merge, doc-only commit, no red-green ritual). The live test was
  END-USER work: it ran from inside `/data/projects/resume` using only
  published artifacts — no livespec clone consulted, no fleet
  credential, no core-tenant writes. Keep the two roles separate for
  any follow-up verification.
- **⚑ Golden rule.** FILE ripe work + GROOM it; never hand-code
  factory-safe implementation inline in the planning session. The doc
  rewrite itself is spec-side core-docs work a maintainer-attended
  session executes directly through the normal PR flow.
- **Resume command:**
  `/livespec-orchestrator-beads-fabro:plan greenfield-install-experience`.

## The next action

Resolve `livespec-p340`, the remaining live-test residual, through the
factory path. Do not hand-code the Python fix inline in the planning
session.

1. **Compose status LIVE** first:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-rh0i
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-p340
   ```
   `livespec-rh0i` comments carry the doc PR sequence and the resume
   verification record; `livespec-p340` carries the acceptance
   criteria for the remaining fix.
2. **Dispatch the child residual** via the reference
   `livespec-orchestrator-beads-fabro` factory path, e.g. the `drive`
   operation for action `impl:livespec-p340`, or let the Dispatcher
   drain it if it is already ready. If the dispatcher reports that the
   item is not factory-ready, run the
   `livespec-orchestrator-beads-fabro:groom` operation on
   `livespec-p340`; file any resulting child work, then dispatch the
   ready child item.
3. **Verify the fix against the resume-discovered failure mode.**
   The acceptance criterion is concrete: an idempotency refusal from
   `/livespec:seed` must exit 3 AND emit the `PreconditionError` /
   structured-finding message on stderr. If the fix changes published
   install or seed guidance, rerun the relevant published-path
   verification from `/data/projects/resume`.
4. **Close only after zero unfixed live-test friction remains.** Add a
   completion comment to `livespec-rh0i` naming the doc PR sequence,
   the resume verification evidence, and the `livespec-p340` fix PR;
   close `livespec-rh0i`; then archive this thread with
   `git mv plan/greenfield-install-experience/ plan/archive/`.

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
