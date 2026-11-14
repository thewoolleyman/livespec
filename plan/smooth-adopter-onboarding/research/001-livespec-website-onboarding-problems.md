## The maintainer's statement of what done means

update the docs/ onboarding and setup and other docs, and anything else associated, so that future seeds don't have all these hassles, and it's all smooth and no problems

## Definition of Done assertions derived from that statement

- Running docs/livespec-installation-prompt.md on a fresh empty repository scaffolds, with no manual edits, a complete .gitignore, the contributor toolchain (.mise.toml, pyproject.toml with uv.lock, justfile, lefthook.yml), AGENTS.md with a CLAUDE.md symlink and the .ai/ convention, and a CI workflow that runs just check.
- After seed and the installation prompt's post-seed phases, the adopter's .livespec.jsonc carries implementation.plugin, worktree_discipline, credential_wrapper, and the orchestrator connection block without any hand-merging.
- A new adopter's beads tenant is provisioned through committed automation linked from the docs (dolt-server-3lgc6c), with status.custom set and the fleet .beads/config.yaml shape, so the adopter's first capture-work-item succeeds on its first attempt.
- Phase 2 of the installation prompt asks up front whether the repository lives in the GitHub App owner's account and whether its beads tenant is family or independent.
- The revise operation's documentation states the ratification-evidence identity, timing, and content-digest rules, so a first revise succeeds without a refused attempt.
- Every item in research note 001 is fixed, linked to its filed work item, or explicitly deferred with a reason.

# livespec-website onboarding: what went wrong (2026-11-14)

On 2026-11-14 a fresh repository, `livespec-ai/livespec-website`, was taken
from an empty repo to a seeded, implemented, deployed adopter. It used
`docs/installation.md` and `docs/livespec-installation-prompt.md` with Claude
Code on `hetzner-xubuntu`, with Claude Driver only, the beads-fabro
orchestrator, the `released` posture and the `livespec-with-diagrams`
template. This note records every step that failed, needed a manual fix, or
needed knowledge found only in sibling repos, code or script output. The
plan's job is to make the docs/onboarding path smooth end to end, so the
next seed hits none of these.

Items the coordinator already filed are referenced, not re-filed.

## A. Repository scaffolding the prompt assumes but does not create

1. **`.gitignore` is not covered.** Phase 4b adds only the six
   `/dev-tooling/*` pack lines. A new adopter needs ecosystem excludes
   (here: website and macOS), `/.venv/`, `/tmp/` (agent session scratch such
   as `tmp/session-waits/`), `.claude/settings.local.json`,
   `/dev-tooling/.gitignore`, and the Beads/Dolt set (`/.beads/metadata.json`,
   `*.lock`, `.dolt/`, `*.db`, `.beads-credential-key`, `.beads/proxieddb/`).
   All of these were hand-written by copying from `hetzner-xubuntu-info`.
2. **Phase 4b assumes a toolchain that a greenfield repo lacks.** It says
   "targets a repo that already runs `just` and `lefthook`" and otherwise
   marks itself n/a. Nothing scaffolds `.mise.toml` (uv, just, lefthook pins),
   a `pyproject.toml` with the `livespec-dev-tooling` git dependency and
   release tag, `uv.lock`, the `justfile` (`bootstrap`,
   `install-worktree-pack`, `check`), or `lefthook.yml`. All were reverse
   engineered from a sibling adopter, including which dev-tooling tag to pin
   (looked up by hand as the latest release).
3. **`AGENTS.md` / `CLAUDE.md` symlink and the `.ai/` convention are not
   mentioned.** The fleet convention (an `AGENTS.md` that points at
   `.ai/<topic>.md`, with `CLAUDE.md` as a symlink) was discovered by grepping
   sibling repos. The memory-redirect hook, which says to put durable
   guidance in `AGENTS.md`/`.ai/` and not session memory, was discovered by
   tripping it. A fleet-wide `AGENTS.md` SendMessage pointer later showed up
   in the new repo from outside this session.
4. **No repository and CI baseline.** The prompt does not cover a CI
   workflow, GitHub repo settings (auto-merge was off and there was no branch
   protection), or a PR process. The agent had to discover that
   `gh pr merge --auto` was unavailable, and the maintainer had to state the
   auto-merge-on-green policy explicitly (`.ai/pr-process.md`).
5. **Fleet registration is not mentioned.** The new repo is not in
   `.livespec-fleet-manifest.jsonc` `adopters[]` (posture), and the prompt
   says nothing about whether or how to register.

## B. Installation-prompt accuracy

6. **Stale `bd` pin.** The prompt says `bd` is "pinned v1.0.5"; the host
   runs `bd 1.2.2`, as does every live tenant.
7. **Seed's `.livespec.jsonc` is minimal, not "the full commented schema
   skeleton".** `prose/seed.md` Post-CLI says the CLI writes the full
   commented skeleton. The 0.47.5 CLI wrote only
   `{ "template": "livespec-with-diagrams" }`. Every other key
   (`implementation`, `worktree_discipline`, `credential_wrapper`, the
   orchestrator `connection` block, `spec_governance`) was merged by hand from
   sibling examples.
8. **No `spec_governance` defaults for a new adopter.** Fleet adopters run a
   long, tuned `spec_governance` block. A new adopter gets the safe defaults
   (`manual`, `manual-spawn`) with no guidance. That made the first revise
   needlessly heavy (see C).
9. **Seeding inside a worktree is unaddressed.** `AGENTS.md` (written by
   this onboarding) requires worktree + PR. A worktree path has no
   project-scope install record, so every spec CLI printed "livespec plugin
   currency could not be verified". The prompt does not say whether seed
   should run in the primary checkout or a worktree, or what the warning
   means there.
10. **The Phase 6 GitHub App question surfaces too late.** The repo lives in
    the `livespec-ai` org, but the fleet App (`thewoolleyman-factory-bot`) is
    private, so it cannot be installed outside its owner account. The
    prompt's same-account shortcut silently does not apply. This should be
    asked in Phase 2 alongside the orchestrator choice ("is the repo in the
    App owner's account?"), together with family vs independent tenant. The
    maintainer ended up deferring factory dispatch entirely.

## C. Spec-lifecycle operations: contracts only discoverable in code

11. **Revise ratification evidence rules are undocumented in the prose.**
    The first revise was refused twice with exit 4:
    - `reviewer_identity` must equal `reviewer_model`
      (`_revise_ratification_errors.py`);
    - `reviewed_at` must precede `revised_at` by at least
      `min_review_age_seconds` (default 1s).
    The canonical content digest algorithm is also only in code: SHA-256 over
    uint64-big-endian length-prefixed proposal bytes, then path and content
    pairs sorted by path. `prose/revise.md` lists the evidence fields but
    none of these rules.
12. **The doctor `open-spec-pr` dimension has no way to apply.** Its
    predicate needs a "GitHub-shaped repo/host entry" in `.livespec.jsonc`,
    which seed never writes and the prompt never mentions.
13. **Doctor false positive on absolute URLs.** `agents-ai-reference-resolution`
    flags `https://…/.ai/x.md` links to other repos as missing local files.
    This trips every repo carrying the fleet SendMessage pointer. Filed:
    thewoolleyman/livespec#3216.
14. **The `no-spec-section-citation-in-code` rule is invisible to
    adopters.** Code comments citing `§"…"` fail doctor static, but no
    adopter-facing doc says so. Tripped once in a new check script and fixed.
15. **Post-step `capture-impl-gaps` cannot run before the tenant exists**,
    and revise gives no clear narration for that case.

## D. Beads tenant and ledger bootstrap

16. **Chicken-and-egg tenant onboarding.** A new repo cannot seed its ledger
    or plan without a tenant. The only route is an operator-run script that
    the fleet guard blocks for agents. → **dolt-server-3lgc6c** (committed
    tenant registry plus converge; livespec-website is its first entry,
    adopted as existing).
17. **The family-tenant incantation is undocumented.** The runbook's family
    example omits `FAMILY_BEADS_PASSWORD`, so the maintainer's first run
    failed. It must be mapped from `with-livespec-env.sh`'s
    `BEADS_DOLT_PASSWORD`. → **dolt-server-33s3c4**.
18. **The required post-onboarding step appears only in script output.**
    Committing `backup.enabled: false` in `.beads/config.yaml` is not in any
    doc. → covered by dolt-server-3lgc6c / -33s3c4; the adopter docs must
    state it.
19. **`bd init` in a worktree writes `.beads/` into the PRIMARY checkout.**
    It resolves the main worktree via git's common dir. The prompt warns
    "do not run `bd init` inside a primary checkout or worktree" but offers
    no alternative procedure, so the operator has to improvise.
20. **`bd init --server` output is not the fleet shape.** Its
    `config.yaml` lacked every `dolt.*` key and `backup.enabled: false`, and
    added `sync.remote`. Init also warned that adding the remote was denied
    (tenant users lack the privilege, by design). The committed file had to
    be hand-written to match `livespec-dev-tooling`. `bd` also warns that
    `.beads` should be 0700 and that `dolt_server_port` in `metadata.json`
    is redundant.
21. **A new tenant lacks `status.custom`, and capture fails halfway.** The
    orchestrator needs
    `status.custom = backlog,pending-approval,ready:active,active:wip,acceptance:wip`.
    Without it, `capture-work-item` created the issue, then failed on
    `bd update --status backlog`, leaving an orphan (`lsw-5g6hlo`) that had
    to be deleted by hand. Nothing in onboarding sets it or checks for it.
22. **The `References:` line must include the `## ` marker.** The
    capture/plan prose says "the verbatim text of an existing H2 heading",
    but the resolver requires `## <heading>`. The first filing got a
    mechanical DoD finding that withheld `ready`.
23. **`filing_display(...)` returns a string, not lines.** The prose says
    "show every line", so iterating it printed one character per line.

## E. Host and fleet environment (coordinator-observed)

24. Seats stalled at Claude's folder-trust prompt for unprovisioned
    `~/workspace` checkouts → **hetzner-xubuntu-info#113** (fixed for
    provisioned repos).
25. `codex` on hetzner failed with "no complete local package" (bare
    binary) → **hetzner-xubuntu-info#114**.
26. SendMessage from hetzner does not reach seats on vmi3006760 → plan
    **distributed-send-message**.
27. **The fleet host guard blocks the only tenant path.** It correctly
    refuses ssh+sudo host changes by agents, but no committed automation
    exists for the step it blocks (→ dolt-server-3lgc6c).

## F. Adopter-implementation papercuts worth a template or profile

28. **Pages workflow action versions.** The agent's first Pages workflow
    used outdated majors (`upload-pages-artifact@v3` + `deploy-pages@v4`),
    and the first deploy failed with "No artifacts named github-pages". A
    vetted, versioned workflow for common adopter shapes (a static site
    here) would avoid this.
29. **Workflow-edit guard semantics for in-session adopters.** The
    worktree pack ships `check-no-workflow-edits.sh` (factory-scoped). It is
    unclear to an adopter whether attended in-session workflow additions
    need a ledger authorization label.

## What smooth looks like

One prompt run on a fresh repo should end with all of these done, with no
sibling-repo archaeology and no manual repair:

- a scaffolded toolchain and `.gitignore`;
- `AGENTS.md` and `CLAUDE.md` with the `.ai/` convention;
- a CI and PR baseline;
- a complete `.livespec.jsonc`;
- a provisioned, correctly configured tenant with the committed `.beads/`
  shape;
- an early App/tenant decision;
- documented revise evidence rules;
- a first `capture-work-item` that succeeds.
