Research complete. Here is the consolidation map.

---

# BOTTOM LINE

1. **23 existing items** touch pin propagation / CI redness across 5 reachable tenants; **6 of the 10 named seeds are ALREADY DONE** — silently fixed on master, ledger never updated.
2. Verdict split: **7 ALREADY DONE · 8 CHILD · 6 KEEP SEPARATE · 2 SUBSUME**. The new plan is mostly a **ledger-reconciliation and closure** job, not a build job.
3. **Yes — settled decisions constrain the plan.** The binding one is adqmnm's "fan-out writes the wiring" (2026-07-05) with three explicitly rejected alternatives, plus the absolute ban on CI-green escape levers (2026-07-04). Both are quoted verbatim below.
4. **One live contradiction:** adqmnm's ratified boundary says the reconcile edits `justfile` ONLY, "never `.github/workflows/`" — but shipped code (`ci_yaml_canonical_reconcile.py`, 2026-07-14) edits `ci.yml`. The App's missing `workflows` permission makes this load-bearing and I could **not** verify how the push succeeds.
5. **New unfiled gap I found:** `livespec-dev-tooling` is outside its own fan-out. Its `ci.yml` image is `python-v0.43.2` and its `uses:` ref is `@v0.46.5` while all 7 consumers sit at `v0.49.2`.

---

# MASTER TABLE

| id | tenant | title (abbrev) | status/pri | scope | created | verdict |
|---|---|---|---|---|---|---|
| `livespec-o0x1` | livespec | bump-pin must not redden master on stamped-projection drift | open P2 | restamp `canonical-slugs.yml` in fan-out | 2026-07-03 | **ALREADY DONE** |
| `livespec-p9s0` | livespec | cross-repo check reads local clone HEAD not origin | open P1 | stale-clone false red | 2026-07-15 | **CHILD** |
| `livespec-dev-tooling-adqmnm` | dev-tooling | fan-out reconciles consumer justfile canonical block | **BLOCKED** P2 | the decision record | 2026-07-05 | **ALREADY DONE** |
| `livespec-dev-tooling-fz4` | dev-tooling | workflow.toml docker tag = 5th pin format | open P1 | pin format | 2026-07-12 | **ALREADY DONE** |
| `livespec-dev-tooling-xb7` | dev-tooling | ci.yml container image is unmanaged pin | open P1 | pin format | 2026-07-17 | **ALREADY DONE** |
| `livespec-dev-tooling-p73` | dev-tooling | pin-freshness uses FIRST record as representative | open P2 | safety-net blind spot | 2026-07-19 | **CHILD** |
| `livespec-dev-tooling-u0x` | dev-tooling | reconcile can wire a check the pinned version lacks | open P2 | version skew | 2026-07-13 | **ALREADY DONE** |
| `livespec-dev-tooling-9j8.1` | dev-tooling | port pin-rewriters out of action.yml heredocs | **closed** P1 | adqmnm's blocker | 2026-06-30 | **ALREADY DONE** |
| `livespec-dev-tooling-9j8.6` | dev-tooling | extract logic from reusable-pin-freshness.yml | open P2 | untested CI logic | 2026-06-30 | **CHILD** |
| `livespec-dev-tooling-q9a` | dev-tooling | exclude world-gates from ci-matrix-completeness | open P2 | gate scope | 2026-07-10 | **ALREADY DONE** |
| `livespec-dev-tooling-r5m` | dev-tooling | release commit leaves uv.lock behind pyproject | open P2 | intra-repo pin lockstep | not queried | **CHILD** |
| `livespec-dev-tooling-800` | dev-tooling | branch-protection must recognize ci-green gate job | open P2 | CI gate wiring | not queried | **CHILD** |
| `livespec-dev-tooling-s2t` | dev-tooling | CI-runner host config is hand-edited systemd state | open P1 | CI substrate | not queried | **KEEP SEPARATE** |
| `livespec-dev-tooling-9mp` | dev-tooling | T10 cache-tiering | open P1 | CI perf | not queried | **KEEP SEPARATE** |
| `livespec-dev-tooling-xam` | dev-tooling | enforce release-park.yml shim fleet-wide | open P2 | release train | not queried | **KEEP SEPARATE** |
| `livespec-dev-tooling-2kt` | dev-tooling | release-park unreleased-backlog detection | open P2 | release train | not queried | **KEEP SEPARATE** |
| `livespec-dev-tooling-afd` | dev-tooling | release-park parity + fleet enforcement | open P2 | release train | not queried | **KEEP SEPARATE** |
| `bd-ib-brry` | orchestrator-beads-fabro | janitor reads stale local sibling trees (false red) | open P2 | same as p9s0 | 2026-07-19 | **SUBSUME** → p9s0 |
| `bd-ib-wmqsn7` | orchestrator-beads-fabro | check-master-ci-green: tolerate transient flake | **BLOCKED** P2 | CI-red consequence | not queried | **CHILD** |
| `bd-ib-bwgko4` | orchestrator-beads-fabro | pr node rebase before push (stale-workflow race) | **BLOCKED** P2 | CI-red consequence | not queried | **CHILD** |
| `bd-ib-9yi` | orchestrator-beads-fabro | janitor cargo-not-found on Rust repos | open P2 | image contents | not queried | **KEEP SEPARATE** |
| `livespec-console-beads-fabro-7wy` | console-beads-fabro | rewrite § citation before next core-pin bump | open P2 | pin-bump landmine | 2026-07-19 | **KEEP SEPARATE** |
| `livespec-3lev` (+ `.3`–`.8`) | livespec | fabro-ci-image-factoring epic | open P2 | CI substrate | not queried | **SUBSUME** the `xb7` Track-B remainder only |

---

# ALREADY DONE — verified against git, with commits

These are the highest-value finding: **7 items the ledger still shows as open work**.

| item | fixed by | date |
|---|---|---|
| `o0x1` | `5689c73` "re-stamp canonical-slugs projection in bump-pin fan-out" | 2026-07-10 |
| `adqmnm` | `8975025` "fix: reconcile canonical check wiring in bump pins" + extracted to `justfile_canonical_reconcile.py` (`d90494b`) | 2026-07-09 |
| `u0x` | `7dc0d9b` — canonical set now supplied as DATA via `$CANONICAL_JSON` captured from the **consumer's own** env; the module docstring names this exactly "Version-skew discipline (the defect that deadlocked the fan-out)" | 2026-07-14 |
| `q9a` | `5693955` "exclude world-gate checks from ci-matrix-completeness"; `_WORLD_GATE_CHECK_SLUGS` + `world_gate_check_slugs()` live in `canonical_checks.py` | ~2026-07-12 |
| `fz4` | `ebf54cc` "cover fabro-sandbox docker image tag as the 5th bump-pin format" | 2026-07-12 |
| `xb7` | `b0c320d` "walk the fabro-sandbox CI container image pin (xb7)"; its propose-change is no longer in the pending queue, so the spec leg ratified too | **2026-07-19 00:03** |
| `9j8.1` | closed in ledger | 2026-07-15 |

`pin_autodiscovery` now documents **six** formats, including `walk_fabro_workflow_docker`, `walk_github_workflow_container_image`, and `walk_codex_acp_docker_arg`.

**The xb7 fan-out demonstrably propagated** — I verified every consumer's `ci.yml` is now `python-v0.49.2` (console: `python-rust-v0.49.2`). `u0x`'s comment facet (a) — "the freshness bot cannot add the CI matrix job" — is also closed by `ci_yaml_canonical_reconcile.py`. Facet (b), *ordered cross-repo merge sequencing*, I found **no** evidence of a fix; that residue should survive as a child.

---

# THE NEW UNFILED GAP — the producer is outside its own fan-out

| repo | `ci.yml` image | `uses:` ref |
|---|---|---|
| all 7 consumers | `python-v0.49.2` ✅ | `@v0.49.2` ✅ |
| **`livespec-dev-tooling`** | **`python-v0.43.2`** (6 releases behind) | **`@v0.46.5`** (3 behind) |

Nothing fans out to `livespec-dev-tooling` itself. This is precisely `p9s0`'s Direction 3 ("orphaned repos … ensure every governed repo is either a fan-out target … or explicitly out-of-scope"), and it is unfiled. **Recommend the new epic own it.**

---

# DECISION RECORDS THE NEW PLAN MUST HONOR (verbatim)

### 1. "Fan-out writes the wiring" — maintainer, 2026-07-05 (`adqmnm`; thread `livespec:plan/archive/fleet-plugin-currency/handoff.md`)

> **Decision (maintainer): "fan-out writes the wiring."** The fan-out reconciles each consumer's `check:` canonical block to the newly-pinned set atomically with the pin bump (reusing `aggregate_completeness`'s parser); the check stays the verifier. Rejected: grace-period soft-warn (drift-prone state + softens the check) and manual-wave (the status quo that caused the cascade).

The three rejected alternatives, from the item body:

> (b) grace-period soft-warn on aggregate_completeness for a brand-new slug — adds drift-prone per-slug "first-release version" state AND deliberately softens the check for a window …; (c) accept the manual wave / sequence by hand — the status quo that produced the cascade

### 2. NO escape levers on CI-green gates — maintainer, 2026-07-04

> The `LIVESPEC_MASTER_CI_GREEN=warn` repair lever briefly added in dev-tooling PR #245 was ruled absolutely unacceptable: NO escape gates on CI-green gates, ever — they WILL be abused; the remedy for a gate deadlock is a server-side REVERT PR of the breaking change and a re-land in the right order.

### 3. CI-wiring stays maintainer-side (`fleet-ci-aggregate-coverage/handoff.md`)

> **CI-wiring stays maintainer-side.** The fleet App (`livespec-pr-bot`) deliberately lacks `workflows` permission, so factory-dispatched branches cannot touch `.github/workflows/`.

### 4. Single all-green gate job — maintainer, 2026-07-10

> "Done" for a repo = **CI provably runs the full aggregate AND blocks merges on all of it**, realized via a **single all-green gate job** (maintainer-chosen 2026-07-10 over per-check required contexts, which are brittle …).

### 5. No-Circular-Dependency killed the cross-repo pin lockstep — maintainer, 2026-07-12

> **The cross-repo pin lockstep as written is a CIRCULAR DEPENDENCY — do NOT build it.** … `livespec-dev-tooling` is the foundational enforcement-suite repo those consumers depend ON, so it must never reach INTO them.

### 6. Do NOT hand-bump image tags (`fabro-ci-image-factoring/handoff.md`)

> **Do NOT hand-bump the six repos as a workaround** — once the pin format covers the `ci.yml` line the normal fan-out reconciles them and KEEPS them reconciled; a manual bump just re-rots on the next release, which is the actual bug.

### 7. Spec-leads-implementation ordering for pin-format changes

> cont. 4 scoped this code-first (add the scan, then amend the contract). That is backwards. … Landing the scan first would ship code that CONTRADICTS the live contract.

---

# DUPLICATE / OVERLAPPING PAIRS

| pair | survivor | why |
|---|---|---|
| `livespec-p9s0` ↔ `bd-ib-brry` | **`p9s0`** | Same defect (cross-repo check reads stale local trees). p9s0 is older, deeper, names the exact file and gives a recommendation. brry contributes the janitor/Dispatcher symptom — fold it in as evidence. |
| `livespec-dev-tooling-xb7` ↔ `livespec-3lev` Track B | **`xb7`** (now done) | Track B in the live plan thread is the unexecuted plan for xb7; xb7 landed today, so Track B's B1–B5 should be marked done, not re-run. |
| `livespec-dev-tooling-fz4` ↔ `bd-ib-wwe` | **`fz4`** | fz4 names `bd-ib-wwe` as its symptom tracker to close on landing. fz4 landed 2026-07-12; wwe did not appear in the open orchestrator ledger, so it likely already closed. |

---

# CONTRADICTIONS

1. **The workflow-file boundary.** `adqmnm`'s ratified acceptance says: *"WORKFLOW-FILE boundary respected: the reconcile edits `justfile` ONLY (never `.github/workflows/`), so it stays within the fleet App's push permission."* But `ci_yaml_canonical_reconcile.py` (shipped 2026-07-14) writes `.github/workflows/ci.yml`, and the standing decision is that the App deliberately lacks `workflows` permission. **Either the App gained the scope, or these bump PRs fail to push their ci.yml edits.** I could not verify which — flagging as the single most important thing for the new plan to resolve first.

2. **Check ownership.** `bd-ib-brry` says the check "lives in livespec-dev-tooling (doctor-static)". `p9s0` says livespec core. **`p9s0` is right** — I confirmed `wiring_completeness_cross_repo.py` exists only in core (`.claude-plugin/scripts/livespec/doctor/static/`) and not in dev-tooling. brry's grooming note would send an implementer to the wrong repo.

3. **Contract vs. implementation on pin-freshness.** Per `p73`, `contracts.md` describes per-`(source_repo, current_pin, latest_tag)` triple semantics; the workflow implements first-record-per-source; *"today the contract describes (b) and the code implements neither."*

---

# BLOCKED ITEMS THE PLAN MUST UNBLOCK OR ABSORB

| item | block | disposition |
|---|---|---|
| `livespec-dev-tooling-adqmnm` | `blocked-reason:needs-human`; dep `9j8.1` **already closed 2026-07-15** | Blocker is stale AND the work shipped. **Close as superseded.** |
| `bd-ib-wmqsn7` | `blocked-reason:needs-human` | CI-green flake tolerance — collides head-on with decision #2 (no escape levers). Needs an explicit maintainer ruling. |
| `bd-ib-bwgko4` | `blocked-reason:needs-human` | stale-workflow push-gate race on pin PRs. |
| `livespec-3lev.3`/`.4` | ledger-gated on intentionally-open `.1` | Plan thread says: *"Do NOT `bd close --force`"* — maintainer owns the call. |

---

# COULD NOT VERIFY / FAILED SOFT

- **Adopter ledgers unreachable** — `openbrain`, `resume`, `homelab` all return `Access denied for user '<tenant>'` on `127.0.0.1:3307`. They are independent tenants with their own passwords; the fleet wrapper does not carry them. **No adopter items are in this map.**
- **The `workflows` push-permission question** (contradiction #1) — unresolved.
- Several items marked "not queried" in the table: I listed them from `bd list` but did not pull full `bd show` bodies, so their scope lines are title-derived.
- **Fleet master CI is GREEN right now** (all 8 repos, checked via `--workflow CI`; core's latest run was still in progress). The redness this plan targets is episodic — triggered by slug-adding releases — not a current outage.