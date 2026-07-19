# Reverse-Hazard Sweep — Upstream Tightening Against Existing Consumer Code

**Captured:** 2026-07-19, for work-item `livespec-b7ropo`.

## Bottom Line

No live reverse-hazard instance was found.

The active fleet has no pending upstream check-definition tightening between the
consumer-pinned refs and the target refs checked here. The dev-tooling canonical
check tree is byte-identical from every active consumer's pinned
`livespec-dev-tooling` ref (`v0.50.3`) to `livespec-dev-tooling` `origin/master`.
The core doctor static-check tree is byte-identical from every active
consumer's core pin to `livespec` `origin/master`, including the console's older
`v0.16.0` pin. The reusable workflow callable contracts are unchanged from
`livespec-dev-tooling` `v0.50.3` to `origin/master`.

This sweep therefore starts with zero confirmed instances and ends with zero
confirmed instances. The previously-cited `livespec-console-beads-fabro-7wy`
example is not a live instance: `no_spec_section_citation_in_code.py` has the
same sha256 prefix (`74bd494da6cdef5f`) at core `v0.16.0` and core
`origin/master`, and the console committed source has zero `§"` hits under
`crates/**/src/`.

## Inputs And Scope

The in-scope consumers are exactly the eight committed `fleet` entries in
`.livespec-fleet-manifest.jsonc`:

| Repo | `origin/master` checked | Core pin | Dev-tooling package pin | Reusable workflow ref |
|---|---:|---:|---:|---:|
| `livespec` | `64189c3619b68467a5bfe1c4331155a0781f596b` | `v0.18.0` | `v0.50.3` | `v0.50.3` |
| `livespec-dev-tooling` | `e78754663da93c0181c80cdeb2f2051b385301b2` | `v0.18.2` | producer | `v0.50.3` |
| `livespec-driver-claude` | `d604ffd1eb07fdd812955e6b75cb7388fea62c34` | `v0.18.2` | `v0.50.3` | `v0.50.3` |
| `livespec-driver-codex` | `4ed377644999316f2500d98065dce245ac01a565` | `v0.18.2` | `v0.50.3` | `v0.50.3` |
| `livespec-orchestrator-beads-fabro` | `0716e7076c2ce0a971a5d78ca7ce0fe3b6b2101a` | `v0.18.2` | `v0.50.3` | `v0.50.3` |
| `livespec-orchestrator-git-jsonl` | `11f84e7be716300e97247193a2b8cefedf210df7` | `v0.18.2` | `v0.50.3` | `v0.50.3` |
| `livespec-runtime` | `86da6bc134b85b8cdfea7259fd1526d1d44e501e` | `v0.18.2` | `v0.50.3` | `v0.50.3` |
| `livespec-console-beads-fabro` | `df2c8d80d845da362dec1857ab4f75a1ae4ad5e4` | `v0.16.0` | `v0.50.3` | `v0.50.3` |

Adopters (`openbrain`, `resume`, `homelab`) are out of scope per the work-item
brief and were not swept.

The dispatcher's host-side `/data/projects/<repo>` paths do not exist inside
this Fabro sandbox. I used the sandbox's committed fleet clones instead:
`/workspace/livespec` for core and `/workspace/siblings/<repo>` for siblings.
All evidence below was still read from committed refs with `git show`, `git
diff`, `git log`, `git rev-parse`, and `git grep`; no sibling working tree state
was used.

## Swept Upstream Surfaces

| Upstream surface | Consumers | Pinned ref -> target ref | Result |
|---|---|---|---|
| `livespec-dev-tooling/livespec_dev_tooling/checks/**` plus `canonical_checks.py` | all Python consumers with a dev-tooling package pin: `livespec`, both Drivers, both orchestrators, `livespec-runtime`, console | `v0.50.3` -> `origin/master` | No changed files. Check-tree object is `e35708fbb750de69b64cc348e45f14fd3fc0cfd4` at both refs; 54 non-helper check modules at both refs. |
| `livespec-dev-tooling` installed body constants: `install_commit_refuse_hooks.py`, `install_no_shadow_ledger.py`, `install_worktree_pack.py` | consumers that inherit the byte-identity checks | `v0.50.3` -> `origin/master` | No changed files. No stricter byte-identity definition exists at target. |
| `livespec/.claude-plugin/scripts/livespec/doctor/static/**` | all repos with a core pin; `check-doctor-static` is live in the six non-core consumers recorded by the recovered sweep | `v0.18.0` or `v0.18.2` or `v0.16.0` -> `origin/master` | No changed files. Static-check tree object is `c6e692092528538d56d0295fc5c1930e5d7e0793` at `v0.16.0`, `v0.18.0`, `v0.18.2`, and `origin/master`; 21 non-helper static modules at every ref. |
| `livespec-dev-tooling/.github/workflows/reusable-*.yml` callable contracts | all repos with reusable workflow shims pinned to dev-tooling | `v0.50.3` -> `origin/master` | No reusable workflow changes. The only `.github/workflows` diffs are dev-tooling's own local shim refs changing `@v0.50.2` to `@v0.50.3`; no `workflow_call.inputs` or required secret contract changed. |

## Starting-Point Candidate Checks

The recovered inventory's six latent candidates were used as starting points,
not as the answer:

| Candidate | Sweep result |
|---|---|
| `check-ci-matrix-completeness` warn-lever asymmetry | No target tightening. The dev-tooling check module is unchanged from every consumer's `v0.50.3` package pin to `origin/master`; no consumer will newly fail on the next dev-tooling pin bump from this rule. |
| `check-behavior-scenario-link` severity flip | No target tightening. Core's doctor static tree is unchanged from every core pin to `origin/master`; no fail-default flip is present at target. |
| `file_lloc` hard-gate lever | No target tightening. The dev-tooling `file_lloc.py` module is unchanged from `v0.50.3` to `origin/master`; no default hard-gate expansion is present at target. |
| `copier-update-drift` workflow arming | No target tightening in inherited reusable workflow definitions. This remains a latent policy/trigger concern, but no pinned-ref -> target-ref workflow contract diff newly flags existing consumer code. |
| Console `console-spec-check` gap-id golden inverse hazard | Not a reddening instance. It is an inverse silent-drift hazard, not a stricter upstream check that newly fails a consumer. |
| Worktree-discipline pack byte-identity | No target tightening. The upstream installer constants are unchanged from `v0.50.3` to `origin/master`; no committed consumer pack file can newly fail against a changed body. |

## Dev-Tooling Tightening History Checked

The recent dev-tooling history did tighten and add checks before the current
fleet pins:

```text
v0.46.5..v0.50.3 changed:
M  livespec_dev_tooling/canonical_checks.py
A  livespec_dev_tooling/checks/_self_hosted_routing_parse.py
M  livespec_dev_tooling/checks/check_mutation.py
A  livespec_dev_tooling/checks/handoff_dispatch_routing.py
M  livespec_dev_tooling/checks/main_guard.py
M  livespec_dev_tooling/checks/pbt_coverage_pure_modules.py
A  livespec_dev_tooling/checks/plan_thread_anchor_declared.py
A  livespec_dev_tooling/checks/plan_thread_epic_parity.py
M  livespec_dev_tooling/checks/rop_pipeline_shape.py
A  livespec_dev_tooling/checks/self_hosted_routing.py
A  livespec_dev_tooling/checks/source_trees_scoped_to_consumer.py
M  livespec_dev_tooling/checks/supervisor_discipline.py
M  livespec_dev_tooling/checks/tests_mirror_pairing.py
```

Those changes are not live reverse hazards now because the active consumers
already pin `livespec-dev-tooling` `v0.50.3` and their current committed state is
the post-repair state. The required next-bump comparison is therefore
`v0.50.3..origin/master`, and that comparison has no changed check definitions.

The only dev-tooling commit in `v0.50.3..origin/master` touching the swept paths
is `e787546 chore(deps): bump livespec pin to v0.18.2`. It changes dev-tooling's
own pin/config context, not consumer-inherited check rules.

## Disproved Console Example

The work item explicitly warned not to treat `livespec-console-beads-fabro-7wy`
as a live instance. This sweep confirms that warning:

| Evidence | Result |
|---|---|
| Core static-check tree from `v0.16.0` to `origin/master` | No changed files; tree object `c6e692092528538d56d0295fc5c1930e5d7e0793` at both refs. |
| `no_spec_section_citation_in_code.py` sha256 prefix | `74bd494da6cdef5f` at both `v0.16.0` and `origin/master`. |
| Console committed source marker search | `git grep -n '§\"' origin/master -- 'crates/**/src'` returns zero hits. |

## Conclusion

No consumer carries pre-existing code that would newly fail under a stricter
upstream check at the next pin bump to the target refs checked here. The active
pin pairs were swept across the dev-tooling canonical registry, dev-tooling
byte-identity constants, core doctor static checks, and reusable workflow
contracts. Every candidate either has no pinned-ref -> target-ref rule diff or
is a latent/non-reddening hazard outside this reverse-hazard acceptance target.
