# 005 — Phase 0: the estate, sized and classified; where the Ansible tree lives (2026-09-09)

Phase 0 of `livespec-sab5gn.4`, the maintainer-directed migration of host
provisioning off the home-grown installer/converge shell. Read `004` first for
the directive, its bounds, and the mandatory stop-and-summarize gate; this note
is the measurement `004` §5 asked for, plus the two decisions Phase 0 owed.

Every artifact under the three provisioning trees was read at its committed tip
and given exactly one row. The four per-slice tables are in `005-estate/`
beside this file; this note is the analysis over them.

## 1. The estate in one table

349 committed artifacts across three repositories and four hosts.

| Slice | Artifacts | (a) host glue | (b) Kubernetes-declarative | (c) dead / one-shot | (d) repo-side |
|---|---|---|---|---|---|
| `livespec-dev-tooling` `ci-runner/k3s/phase2/` | 140 | 61 | 48 | 4 | 27 |
| `livespec-dev-tooling` `ci-runner/` (rest) | 75 | 35 | 3 | 8 | 29 |
| `vps-info` `services/` | 69 | 55 | 0 | 0 | 14 |
| `fabro-hosts` `services/` | 65 | 40 | 0 | 0 | 25 |
| **Total** | **349** | **191** | **51** | **12** | **95** |

Class (a) migrates to Ansible. Class (b) stays as manifests and kustomizations
that Flux could reconcile unchanged; a playbook may apply them but may not
encode their ordering. Class (c) is deleted with its pre-deletion SHA cited.
Class (d) is exit-test suites, READMEs and fixtures, which are repo tooling
rather than host plumbing and are deleted only when the shell they test goes.

**191 artifacts is the migration.** It is larger than `004` assumed, and the
reason is that `004` sized the CI slice and estimated the other two. The two
host-record repositories are not a tail: they are 95 of the 191, and they carry
the estate's only per-host templating convention (`fabro-hosts`' `*.in` files
plus `hosts/<host>.env`), which is `template` plus `host_vars` written by hand.

## 2. Three findings that change the plan

**The `gate-runner/` tier targets a host the plan never listed.** `004` and the
work-item both scope the estate to `poweredge-xubuntu`, `gmktec-xubuntu`,
`hp-xubuntu` and the VPS, and assign `ci-runner/` to the two CI nodes. Six
scripts, five systemd units and a polkit rule under `ci-runner/gate-runner/`
are installed on **neither** CI node: they run on the shared factory host,
which is the VPS. Verified by file listing there — every unit and all six
scripts under `/usr/local/lib/ci-runner/` are present, dated 2026-08-23,
matching that directory's last commit. The tier is live and permitted by
`SPECIFICATION/non-functional-requirements.md` §"Fleet CI execution posture".
So the VPS carries host glue from **three** repositories, not one, and
`ci-runner/README.md`'s opening sentence attributing this tier to
`poweredge-xubuntu` is wrong. Phase 3 gains this tier; Phase 2 loses it.

**Twelve artifacts are already dead and eight of those are a superseded phase.**
`install-arc.sh`, `install-kueue.sh`, `arc/values-host-unique.yaml` and
`kueue/resources.yaml` are phase-1 by-hand legs that `converge-ci-stack.sh`
inlines rather than invokes, applying different values files in both cases.
They can be deleted in Phase 0's wake without waiting for Phase 4, and doing so
removes two of the three remaining class-(b) rows outside `phase2/`.

**Nineteen manual steps survive any migration.** Eleven in `vps-info`, eight in
`fabro-hosts`: building the Fabro binary, minting a server token file, loading
a GitHub App private key into a vault, adding a `tailscale serve` mapping in
another repository, pre-installing a package an installer then refuses to run
without. These are not laziness in the shell and Ansible does not absorb them.
They must be recorded as inventory-level preconditions with a preflight
`assert` per role, or the first apply on a rebuilt host fails in the middle
rather than at the start. `004`'s cost model did not count them.

## 3. Decision — the Ansible tree lives in `livespec-dev-tooling/ansible/`

One tree, one inventory, one convention, in the repository that already owns
110 of the 191 migrating artifacts, has a `just check` aggregate to wire the
linter into, and has CI. `vps-info` and `fabro-hosts` have neither a task
runner nor any CI workflow, so "wire `ansible-lint` into the owning repo's
`just check`" resolves to exactly one candidate. The two host-record
repositories keep their `AGENTS.md` host sections, which are the useful half of
what they hold, and reference the roles.

Rejected, with reasons, so this is not re-derived:

- **A new dedicated repository.** It needs CI, livespec adoption, a fleet
  manifest entry, plugin installs and a ledger tenant before it can hold a
  single role. That is far past the standing "if a plan would create more than
  about two new artifacts, check whether a convention suffices" bar, and the
  convention does suffice.
- **Three trees, one per repository.** This is the fragmentation the directive
  exists to end. It also triples the inventory, which is the one file that must
  never disagree with itself about which host is which.
- **`vps-info`.** It provisions the control node, which is superficially
  appealing, but it is the least-governed repository in the set — no task
  runner, no CI, no enforcement suite — so the linter would have nowhere to run.

The one cost is that `livespec-dev-tooling` is the shared enforcement suite
consumed by thirteen repositories, so churn there is visible fleet-wide. It is
not a new cost: `ci-runner/` already lives there and already causes it.
Provisioning changes land as `chore(ansible):`, which this repository's
`release-please-config.json` marks hidden, so they cut no release and fan out
no pin bump.

## 4. Decision — Ansible resolves through `uvx`, not a dependency group

`ansible-core` 2.21 requires Python 3.12. `livespec-dev-tooling`'s
`requires-python` floor is 3.10.16 and `livespec` core's is `>=3.10.16,<3.11`,
so no fleet repository can carry ansible-core as a project dependency today.
Raising that floor is a fleet-wide decision about the shared enforcement suite
and has nothing to do with provisioning hosts.

The alternative of pinning ansible-core 2.16 or 2.17, the last branches
supporting 3.10, buys compatibility with an old branch in exchange for the
thing being migrated to. Ansible is a tool this repository invokes and never a
library it imports, so it resolves through `uvx` with both versions pinned
exactly in the justfile recipes, which remain the single source of truth for
how the tool is invoked. Recorded here because the constraint is not obvious
and the temptation to move the floor will recur.

## 5. Reachability, measured rather than assumed

Ansible's `setup` module was run against all four hosts from the VPS before any
role was written. Every one answered.

| Host | Connection | Distribution | Python | Passwordless sudo |
|---|---|---|---|---|
| `vps` (`vmi3006760`) | local | Ubuntu 25.10 | 3.14.2 | yes |
| `poweredge-xubuntu` | ssh as `cwoolley` | Ubuntu 26.04 | 3.14.4 | yes |
| `gmktec-xubuntu` | ssh as `cwoolley` | Ubuntu 26.04 | 3.14.4 | yes |
| `hp-xubuntu` | tailnet ssh as `cwoolley` | Ubuntu 26.04 | 3.14.4 | yes |

No bootstrap role is needed, which removes the largest unknown in Phase 1. The
VPS is the control node and manages itself over a local connection, so a run
needs no ssh credential toward it and no inbound reachability to it.

## 6. Migration order, revised against the measurement

`004` ordered the phases CI hosts, then VPS and `hp-xubuntu`. The measurement
inverts part of that.

1. **Phase 1 — skeleton, proven on `gates_kubeconfig`.** Done; see §7.
2. **Phase 2 — the host-record repositories** (`vps-info` 55, `fabro-hosts`
   40). These are 95 of the 191 and they are almost pure class (a): file
   copies, unit installs, template rendering. `fabro-hosts`' `render-unit.sh`
   plus `hosts/<host>.env` is a one-to-one translation to `template` plus
   `host_vars`, and its uniform guard order makes the roles nearly mechanical.
   Doing these second builds the inventory's host_vars against the simplest
   cases and retires two whole conventions.
3. **Phase 3 — the CI hosts** (`phase2` 61, `ci-runner` rest 35, including the
   `gate-runner/` tier now known to live on the VPS). Hardest and most
   coupled: role-aware step plans, boot-ordered converge, the tmpfs datastore's
   rebuild-from-git property. Its class (b) half, 51 artifacts, is the durable
   asset and must come out shaped as kustomizations.
4. **Phase 4 — retire the shell**, citing pre-deletion SHAs. The twelve class
   (c) artifacts can go earlier and independently.

Swapping 2 and 3 costs nothing and means the hardest slice is written by
someone who has already written 95 roles' worth of the same primitives.

## 7. Phase 1 is done, and applying found what checking could not

The tree is `livespec-dev-tooling/ansible/`
([PR #2077](https://github.com/thewoolleyman/livespec-dev-tooling/pull/2077)).
`check-ansible-lint` runs in `just check` at ansible-lint's `production`
profile; `just ansible-drift` is `--check --diff` and replaces the bespoke
`verify-installed-tree.sh`; `just ansible-apply` converges.

The first role, `gates_kubeconfig`, re-expresses `vps-info`'s
`services/gates-kubeconfig/install.sh` — R4.S8, merged in
[vps-info#64](https://github.com/thewoolleyman/vps-info/pull/64) and never run.
About 100 lines of installer became five tasks. The shell's `sudo -u <user>
sudo` inversion disappeared: the credential is read on the control-plane node
under its own become and written on the target under ours, so no ssh identity
has to straddle two accounts.

It was applied to the VPS and verified against the live API server rather than
asserted: `create jobs`, `get jobs`, `watch pods` and `get pods/log` in the
`gates` namespace all yes; `delete jobs`, `get secrets` and `list nodes` all
no. A second apply reports `changed=0` and the drift report is clean.

**`--check` reported a change where the apply reported a failure.** Check mode
showed the credential copy as a would-be change; the real apply failed on a
missing `/etc/ci-runner`, because the shell created that directory as a side
effect inside `refresh-gates-kubeconfig` rather than in the installer. The role
now owns the directory. The general form is worth carrying into every later
phase: a `--check` diff over a path whose parent does not exist is not a
verification, and the estate is full of installers whose directory creation
hides inside a helper.

## 8. One defect found, not fixed here

The gates credential is installed root-owned at mode 0600, faithfully
reproducing the shell installer. R4.S7's `gate-remote` client runs as the
maintainer's ordinary account, which therefore **cannot read it** — confirmed
on the VPS. The merged installer's own verification step used
`sudo -u "${SUDO_USER}"`, so its author expected the invoking user to read the
file; that expectation and the mode contradict each other, and the
contradiction was never executed because the installer was never run.

Not fixed here, because the right resolution belongs to R4.S7's design: either
the client runs under `sudo` via `with-gates-kubeconfig`, or the file gets a
group and mode 0640. Recorded on `livespec-sab5gn.4` and to be settled when S7
is written. It does not block anything today.
