# CI-gate discipline — NEVER add escape gates; revert and re-land

**The rule (maintainer directive, 2026-07-04; absolute):** never add a
lever, env var, flag, carve-out, or any other escape mechanism that lets
a commit, push, merge, or dispatch proceed while a CI-green gate (e.g.
`check-master-ci-green`) reports red — and never weaken such a gate's
severity to "warning". This holds even when the gate blocks the very
change that would repair the red. No exceptions, no "repair-only"
framings, no "CI never sets it" mitigations: any such mechanism WILL be
abused by later agents pattern-matching on it, and its mere existence
defeats the gate's purpose (an unbypassable floor under every
agent-driven change).

**Why this is different from the ordinary carve-out convention.** The
fleet's severity-lever convention (warn-vs-fail / run-vs-skip levers on
ordinary checks) applies to checks that verify the CHANGE. It does NOT
apply to gates that verify the WORLD the change lands on — master CI
green, merge-blocking status checks, dispatch-safety gates. Those gates
are load-bearing precisely because no agent can reason its way past
them. `li-4x3a45` (livespec-dev-tooling tenant) is the recorded wontfix:
no skip hatch on `master_ci_green`, upheld and broadened after a
`LIVESPEC_MASTER_CI_GREEN=warn` lever briefly landed in
livespec-dev-tooling PR #245 (2026-07-04) and was removed the same day
by maintainer directive (PR #249, with a regression test pinning the
env var to having NO effect).

**The correct remedy for a gate deadlock is revert-and-reland:**

1. Identify the landed change that turned master red (or otherwise
   deadlocked the gates).
2. **Revert it** — when local commits are themselves blocked by the red
   master, create the revert SERVER-SIDE (a GitHub revert PR via the web
   UI or API), which no local hook mediates. Merging the revert restores
   green without any gate being weakened.
3. Re-land the reverted work **in the right order** (dependencies,
   consumer wiring, and rollout adoption BEFORE the enforcement that
   assumes them), each step through the normal green gates.
4. File a re-land work-item so the reverted work is never silently lost.

**Corollaries:**

- An enforcement check must not land at error severity before the
  rollout it asserts has completed (enforcement-before-adoption is what
  creates revert-worthy breakage in the first place).
- When you find yourself designing "a lever so the fix can land", stop:
  that impulse is the signal to revert instead.
- A test that pins a rejected mechanism to having NO effect (like
  `test_red_conclusion_fails_regardless_of_lever_env` in
  livespec-dev-tooling) is the durable guard — prefer adding one when
  removing any rejected escape mechanism.

## The `workflows` grant withheld from the DISPATCH CREDENTIAL is a deliberate boundary

The boundary lives at the **dispatch credential**, NOT at the App
installation. Get this distinction right before acting on a push
rejection, because the two levels behave differently and only one of
them is the boundary:

- The **factory sandbox's dispatch credential** deliberately does NOT
  carry the `workflows` read-write grant, so GitHub refuses a
  sandbox-token push whose branch history creates or updates a file
  under `.github/workflows/`. THIS is the boundary (maintainer
  decision, 2026-07-04, when a factory run for `livespec-c1k9.3` was
  push-rejected for exactly this).
- The **fan-out** legitimately DOES push `.github/workflows/` changes
  and is expected to. Its bump PRs rewrite `uses: …@<tag>` pin refs in
  every consumer's workflow files — e.g. `livespec-runtime` PR #293
  (author `app/livespec-pr-bot`) updated four files under
  `.github/workflows/`. That is a deterministic pin-string rewrite, not
  an open-ended agent, and it is why the two credentials are scoped
  differently.

So a `.github/workflows/` push succeeding is NOT evidence the boundary
has been weakened — check WHICH credential pushed it.

This is the same boundary as the gates above, one layer down: workflow
files ARE the CI gate definitions, and an agent-pushed branch must
never be able to modify them.

**Do NOT restate this as an App-installation requirement.** The ratified
contract is explicit that the grant must be surfaced as one withheld
from the dispatch credential "never as an App-installation requirement
to be granted" — see `livespec-orchestrator-beads-fabro`
`SPECIFICATION/contracts.md` §"Self-contained plugin dispatch" (accepted
v045) and `constraints.md` §"Factory sandbox credential constraints".
An earlier revision of this section carried that retired framing.

- NEVER request, grant, or work around the `workflows` grant for the
  DISPATCH CREDENTIAL; the rejection is the boundary working.
- Factory-dispatched work-items must not include `.github/workflows/`
  edits in their branch. When an implementation legitimately needs a
  workflow change, CARVE IT OUT: the agent branch restores the workflow
  file to master's content, publishes everything else, and reports the
  dropped diff; the workflow edit lands via a separate MAINTAINER-side
  commit (worktree → PR under the maintainer's own credentials).
- When grooming or briefing a work-item whose acceptance implies
  workflow edits (e.g. wiring an env var into CI), split the workflow
  wiring into an explicitly maintainer-side step up front.
