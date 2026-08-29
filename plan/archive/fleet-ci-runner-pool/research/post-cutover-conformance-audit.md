# Post-cutover conformance audit — §"Self-hosted CI runner host requirements"

Audited 2026-08-21 against LIVE state: the k3s cluster on `poweredge-xubuntu`,
the GitHub API, and each repository's `origin/master`. Not against any
document's description of that state.

## Why this audit exists

The k3s/ARC cutover (`livespec-s43svm.16`, `.18`) moved nine repositories'
merge-gating CI onto self-hosted capacity. Several clauses in
`SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
requirements" are CONDITIONAL — they engage the moment a repository starts
gating on self-hosted capacity. Nothing in the cutover procedure verifies them
at the moment they engage, so nine repositories crossed that line with the
preconditions merely assumed.

Two of the fifteen clauses turned out not to hold. Both had been silently false
for days. (A third — the rootless clause — was recorded as HOLDS here on
wrong-source evidence and found violated on 2026-08-23; see its row.)

## Verdicts

| Clause | Verdict | Evidence |
|---|---|---|
| Fork-exclusion precondition | **VIOLATED — repaired** | `livespec-overseer` and `livespec-driver-pi` sat at `first_time_contributors` while gating on self-hosted capacity. Repaired to `all_external_contributors`, re-verified uncached. `livespec-s43svm.39` |
| Availability — observe a host has stopped taking jobs | **VIOLATED — open** | `ci-runner-heartbeat.service` failed on every 5-minute firing since 2026-08-15 19:59; 1498 failures, zero successes in 14 days of journal. No OTLP collector exists on the host. `livespec-s43svm.20` |
| Availability — retain a hosted-capacity route | HOLDS | Emptying or deleting `CI_RUNNER_LABELS` falls back to the hosted literal repeated inline at each `runs-on`; documented in `livespec-dev-tooling`'s `ci.yml` header |
| Execution identity | HOLDS | Runner pods run `runAsNonRoot: true`, `runAsUser: 1000`, `capabilities: drop [ALL]`, `allowPrivilegeEscalation: false` |
| Containerized execution — rootless | **VIOLATED at audit time — WRONG-SOURCE verdict, corrected 2026-08-23; repaired** | The 2026-08-21 row read "HOLDS — no container runs as root", read off RUNNER pods (`runAsUser: 1000`). The pod a job's `container:` image actually runs in is the hook-created WORKFLOW pod, whose root was HOST root: `/proc/self/uid_map` read `0 0 4294967295` inside a live workflow pod on 2026-08-23. Repaired by `hostUsers: false` in the hook pod template (`livespec-dev-tooling` PR #1622 → `dda8ee3a`): re-read from inside a live workflow pod, `uid_map` is `0 3210149888 65536` and the job's processes run on the host as uid 678625280 (read with `ps` on the node). `livespec-s43svm.44` |
| Containerized execution — no daemon socket in a job | HOLDS — re-derived against WORKFLOW pods 2026-08-23 | The 2026-08-21 row's evidence ("runner pods mount zero `hostPath` volumes") was the wrong pod. Re-read on the workflow pod: its only `hostPath` is the read-only warm uv cache lower at `/var/cache/ci-runner/warm` (`livespec-s43svm.2`); no daemon socket is mounted; `privileged` is not set; the AppArmor profile's `deny mount` holds. The verdict stands, now on the right evidence |
| Event routing | HOLDS | All nine gating `ci.yml` workflows carry a byte-identical `on:` block — `pull_request:` unqualified, plus `push:` restricted to `branches: [master]`. The clause's allowed set is same-repository pull-request events and pushes to a protected branch, and the branch restriction was read verbatim rather than inferred from the trigger name |
| Event routing — auxiliary lane | HOLDS | `livespec-overseer`'s two extra self-hosted-routed workflows (`release-lane-watch`, `release-readiness`) trigger only on `schedule` and `workflow_dispatch`, neither reachable by a non-collaborator |
| A host is proven by EXECUTING a job | HOLDS | The cluster has executed thousands of jobs; a fresh proof job ran green on 2026-08-21 (run `32501915647`) |
| Shared pool label + host-unique label | **DRIFT — open** | Satisfied by the podman pool (`local-ci` shared, `poweredge` host-unique). NOT satisfiable by ARC, whose runners register with an empty label array. `livespec-s43svm.40` |
| Pool MAY span more than one host | N/A today | The pool is a single host |
| Platform / Runner agent runtime / Workflow runtime / Network | NOT AUDITED | Implied by thousands of green jobs, but not directly verified clause-by-clause |
| Ephemeral registration | HOLDS, with a caveat | ARC `EphemeralRunner` serves one job then the pod is deleted. See the caveat below |

## The `sudo` group finding, and why it is NOT a violation

Worth recording because it looks alarming and is not. The proof job's own `id`
output shows the runner identity in group `27(sudo)`:

    uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),4(adm),...,27(sudo),...

The Execution-identity clause forbids an identity that "holds no administrative
escalation". Group membership alone would suggest it does. It does not: the
container sets `allowPrivilegeEscalation: false`, which sets `no_new_privs`, so
setuid binaries cannot gain privileges and `sudo` cannot function regardless of
group membership. The membership is inert.

The general shape is worth keeping: a permission that appears in an identity
listing may be neutralised by a control somewhere else entirely. Read the
enforcing control, not only the listing.

## Caveat on Ephemeral registration

The clause requires that each registration "serve at most one job and MUST
deregister afterwards". ARC satisfies this by construction.

The 482 surviving PODMAN-era registrations are in an odd relationship to it:
they are actively re-minted by `ci-runner-rate-replenisher.service`, they have
served ZERO jobs since the cutover, and they never deregister because nothing
routes work to their labels. They do not violate the letter — no registration
has served more than one job — but a standing population of never-used
registrations is not what the clause contemplates, and it is exactly the value
the clause's own rationale ("this bounds ... the value of a captured
registration") exists to bound. `livespec-s43svm.19` removes them.

## The pattern behind both violations

Neither was found by a check. Both were found by reading a clause and asking
whether it was still true.

- The fork-approval violation was invisible because its detector's own prose
  said the detector was effectively free and therefore never worth running. The
  cutover falsified that prose and nothing updated it.
- The liveness violation was invisible because the mechanism that would report
  it is the thing that broke, and nothing watched for its absence — the precise
  failure mode the sibling §"CI telemetry export" clause says its closed-loop
  design exists to eliminate.

A third instance surfaced 2026-08-23 and is recorded in the table above rather
than counted here, because it is a different shape: a **wrong-source verdict**.
The two "Containerized execution" rows were read off RUNNER pods, whose
`securityContext` never reaches the hook-created WORKFLOW pod the job actually
executes in (`livespec-dev-tooling` `ci-runner/k3s/phase2/README.md` "The
workflow pod is not the runner pod"). The rootless row was therefore a false
HOLDS over a live violation, and a false HOLDS is worse than the violation it
hides because it is what suppresses re-discovery. When re-deriving any row of
this table, read the pod the job's steps run in — `<runner>-workflow` — not
the runner.

Both original violations are the same shape: **a conditional obligation engaged by an architecture
change, with its verifier calibrated on the pre-change world.** That is the
thing to look for after the next architecture change, and it is why
`livespec-s43svm.39` asks for the precondition to be part of the CUTOVER rather
than only of a scan someone may or may not run.
