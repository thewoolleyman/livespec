# Frozen plaintext tracking store

As of epic **li-ws2iv4** ("Phase 5 — Flip each repo's `.livespec.jsonc`
to `livespec-impl-beads`; archive/freeze plaintext store"), this repo's
OWN impl tracking moved from the plaintext JSONL store at the repo root
onto its per-repo **livespec-impl-beads** Dolt tenant.

- Tenant identity: `livespec`
  (`database == server_user == prefix == tenant`).
- Live store: the beads tenant, reached via `.beads/config.yaml` +
  the `BEADS_DOLT_PASSWORD` env var (never committed). Connection
  details live in `.livespec.jsonc` under `livespec-impl-beads`.

The files in this directory are the **frozen** pre-cutover plaintext
store, retained for audit/history only:

- `work-items.jsonl` — frozen work-item records (migrated into the tenant).
- `memos.jsonl` — frozen memos.

These files are no longer read by any tooling and MUST NOT be edited.
The cutover is reversible: restoring `.livespec.jsonc`'s
`livespec-impl-plaintext` impl block (pointing `work_items_path` /
`memos_path` back at these files, moved to the repo root) re-activates
the plaintext store.

> NOTE: the `just check`-time doctor static checks
> (`no-orphan-dependency`, `no-stalled-epic`, `no-duplicate-gap-id`,
> `no-stale-gap-tied`, `depends-on-ref-wellformedness`,
> `unresolved-spec-commitment`) gate on the active impl-plugin being in
> their `livespec-impl-plaintext`-only supported set, so under the
> `livespec-impl-beads` flip they `skip` and no longer read this repo's
> own root store — the move is CI-safe.

> NOTE: the generic `work-items.jsonl` / `memos.jsonl` references that
> remain throughout the plugin's own source (`.claude-plugin/scripts/`,
> the doctor static checks, skills, and `tests/**/fixtures/**`) are the
> plugin's GENERIC store handling and TEST DATA — they are unrelated to
> this repo's own frozen tracking store and were intentionally left
> untouched. The Layer 3 orchestrator
> (`.claude/skills/livespec-orchestrate/SKILL.md`) still reads sibling
> stores via `git show origin/master:work-items.jsonl`; refactoring that
> executable logic for the beads store is the separate work-item
> li-dgpqk6 and is deliberately NOT done here.
