# Beads ⇄ livespec schema mapping (design spike)

> **Status: DESIGN SPIKE (li-itxqga).** This document maps the livespec
> `WorkItem` JSONL schema onto the beads (`bd`, backend = Dolt) issue
> schema, and pins the external multi-DB server connection model a
> per-repo beads tenant uses against `dolt-server`. It is consumed by
> **li-srbpds** (build the work-items↔beads bridge / plugin) and
> **li-zmigvx** (migrate the existing `work-items.jsonl` store into a
> beads tenant). It is co-located with
> [`beads-problems.md`](./beads-problems.md), the canonical catalogue of
> the eight known upstream `bd` bugs.
>
> **Scope guard.** This spike does NOT re-verify the eight upstream bugs
> (that is **li-mwwdws**'s job); it only cites `beads-problems.md` where a
> known bug shapes a mapping choice. Every beads-side schema detail that
> could not be verified against authoritative beads docs/source is
> tagged **`UNVERIFIED — confirm in li-mwwdws/li-srbpds`** rather than
> asserted.

## Sources

The livespec side is read from the authoritative schema (no
interpretation needed):

- `livespec-impl-plaintext/.claude-plugin/scripts/livespec_impl_plaintext/types.py`
  — `WorkItem`, `AuditRecord`, and the `WorkItemStatus` /
  `WorkItemType` / `Resolution` / `Origin` `Literal` enums plus the
  `DependsOnRaw = str | dict[str, Any]` typed-dependency form.
- `livespec/SPECIFICATION/contracts.md` §"Work-items JSONL record
  schema" (the prose authority the dataclasses realize).

The beads side is **best-effort web research** against the beads
documentation and source (`github.com/gastownhall/beads`, `bd` ≥
v1.0.5, Dolt-only backend). The beads docs do not publish a single
exhaustive field list, so several beads-side details are flagged
UNVERIFIED below.

- Beads docs — Issues & Dependencies:
  <https://gastownhall.github.io/beads/core-concepts/issues>
- Beads docs — Dependencies:
  <https://github.com/gastownhall/beads/blob/main/docs/DEPENDENCIES.md>
- `dolt-server/SPECIFICATION/contracts.md` §"Beads-tenant contract"
  (connection model, prefix-as-tenant rule, known-bug envelope).

## Part 1 — Field map: livespec `WorkItem` → beads issue

Each row gives the livespec field, the beads home (field / label /
dependency edge), the value transform, and a note. The four livespec
fields with **no clean beads home** are called out in
[§1.3](#13-livespec-fields-with-no-clean-beads-home) and drive the
li-srbpds bridge design.

### 1.1 Direct field mappings

| livespec `WorkItem` field | beads issue home | Value transform | Notes |
|---|---|---|---|
| `id` (e.g. `li-itxqga`) | `id` | **Drop the `li-` prefix on write**; beads re-prefixes with the tenant prefix, which MUST equal the tenant DB name (`dolt-server` contract). If the tenant prefix is `livespec`, beads ids become `livespec-...`. **Decision needed in li-srbpds:** keep the legacy `li-` random suffix as the beads id suffix so cross-references in `work-items.jsonl`, commit trailers, and `depends_on` survive migration. | beads id format observed as `<prefix>-<short>`. **UNVERIFIED** whether beads accepts an operator-supplied id suffix at `bd create` time or always mints its own — confirm in li-srbpds; if beads always mints, li-zmigvx needs an `li-…` → `livespec-…` id remap table. |
| `type` (`bug`/`feature`/`task`/`chore`/`epic`) | `type` | **Identity.** beads `type` enum is `bug`, `feature`, `task`, `chore`, `epic` — an exact match for livespec `WorkItemType`. | The single cleanest mapping; no transform. |
| `status` (`open`/`in_progress`/`blocked`/`closed`/`deferred`) | `status` | **Identity** for all five. beads' status set includes `open`, `in_progress`, `blocked`, `closed`, `deferred` (plus beads-only extras `pinned`/`hooked`/`tombstone` that livespec never emits). | Exact match for livespec `WorkItemStatus`. beads-only statuses are inbound-only and never produced by a livespec write. |
| `title` | `title` | Identity. | — |
| `description` | `description` | Identity. | — |
| `priority` (int) | `priority` (int) | **Scale check required.** beads priority is `0`=critical … `4`=backlog (0 highest). livespec `priority` is a bare `int` with no spec-pinned scale. If livespec already uses 0-highest, identity; otherwise li-srbpds defines the transform once. | **UNVERIFIED** that livespec and beads agree on direction (0=highest) — confirm the livespec convention in li-srbpds before asserting identity. |
| `reason` (free text at closure) + `resolution` (enum) | `close_reason` (free text) | **Compose:** beads exposes a single free-text `close_reason` (set via `bd close --reason`). livespec splits closure into a typed `resolution` enum + a free-text `reason`. Encode as `close_reason = "<resolution>: <reason>"` (e.g. `completed: landed in PR #341`) so both survive the round-trip, and parse back on read. | See [§1.3](#13-livespec-fields-with-no-clean-beads-home): the typed `resolution` enum has no first-class beads field; it rides inside `close_reason`. |

### 1.2 Relationship / label mappings

| livespec `WorkItem` field | beads home | Value transform | Notes |
|---|---|---|---|
| `depends_on` (typed `{"kind":"local","work_item_id":"li-…"}`) | beads **`blocks` dependency edge** | For each `depends_on` entry where `kind == "local"`, add `bd dep add <this-issue> <work_item_id> --type blocks` (the dependency is "this issue is blocked by `work_item_id`"). beads default dep type is `blocks`, matching livespec's blocked-by semantics. | livespec dep is typed-dict (v072). **Non-`local` kinds** (if any cross-repo `kind` ever exists) have **no clean beads home** — beads dependencies are intra-tenant (intra-DB) only; cross-tenant edges are unsupported. Flag for li-srbpds — see [§1.3](#13-livespec-fields-with-no-clean-beads-home). |
| epic linkage (`type == "epic"` + children pointing via `depends_on`) | beads **`parent-child`** relationship (`bd create … --parent <epic>`) | Re-express the livespec convention "an epic is a `type=epic` item whose members reference it" as native beads parent-child. **Decision in li-srbpds:** whether to ALSO keep a `blocks` edge or rely on beads' `waits-for`/`parent-child` epic-rollup. | beads represents parent-child via a `--parent` flag at create time, NOT a `dep --type` edge. **UNVERIFIED** whether `--parent` is also settable on an existing issue (post-hoc) — needed by li-zmigvx for migrating already-existing epics; confirm in li-srbpds. Also note beads epic-rollup status calc has a known upstream sharp edge (epic shows BLOCKED with "0 dependencies") — verify against the pin in li-mwwdws. |
| `superseded_by` (id or null) | beads **`supersedes` dependency edge** | When `superseded_by` is set, add `bd dep add <superseding-issue> <this-issue> --type supersedes` (B supersedes A). beads has a first-class `supersedes` dep type. | Clean native home — one of beads' non-blocking dep types. Direction must be confirmed (which side is the edge source) — **UNVERIFIED**, confirm in li-srbpds. |
| `assignee` (str or null) | `assignee` | Identity when present; omit/null when absent. | **UNVERIFIED** that beads exposes an `assignee` field on the issue record (not surfaced in the public schema example). If absent, falls to a label `assignee:<name>` or to [§1.3](#13-livespec-fields-with-no-clean-beads-home). Confirm in li-srbpds. |
| `gap_id` (str or null) + `origin` (`gap-tied`/`freeform`) | beads **label** + **`discovered-from` edge** (hybrid) | `origin` → label `origin:gap-tied` / `origin:freeform`. For `gap-tied` items, the `gap_id` itself → label `gap-id:<id>` (gap ids are not beads issues, so a `discovered-from` *edge* cannot point at them; a label is the durable home). beads labels are a free-form string array. | The gap-id ↔ label exactly-once invariant (livespec NFR §"Beads invariants" #4) is naturally a beads label. `origin` has no enum field in beads → label. See [§1.3](#13-livespec-fields-with-no-clean-beads-home). |
| `spec_commitment_hint` (str or null) | beads **label** `spec-commitment:<id_hint>` | When non-null, emit a label carrying the originating `id_hint` verbatim. | No structured beads field for this; label preserves it round-trip. |

### 1.3 livespec fields with NO clean beads home

These have no first-class beads field and must be carried by an
encoding the li-srbpds bridge owns (label, composed string, or a
sidecar). They are the design pressure points for the bridge:

1. **`resolution` (typed enum:** `completed` / `wontfix` / `duplicate` /
   `spec-revised` / `no-longer-applicable` / `resolved-out-of-band`**).**
   beads has only a free-text `close_reason`. The typed enum must be
   encoded into `close_reason` (e.g. a `resolution=<enum>;` prefix) and
   parsed back, OR carried as a label `resolution:<enum>`. Recommend a
   label for clean queryability; confirm in li-srbpds.

2. **`origin` (enum `gap-tied`/`freeform`) and `gap_id`.** No structured
   beads field; both ride as labels (`origin:*`, `gap-id:<id>`). The
   gap-id ↔ label exactly-once invariant makes the label encoding a
   natural fit, but it is bridge-owned convention, not a beads schema
   feature.

3. **`audit` (the whole `AuditRecord`:** `verification_timestamp`,
   `commits[]`, `files_changed[]`, `merge_sha` (required, non-empty),
   `pr_number` (int|null)**).** beads has no structured audit/evidence
   sub-object. This is the **biggest gap.** Options for li-srbpds:
   (a) serialize the `AuditRecord` to JSON and stuff it in
   `close_reason` or a `notes`/`design` free-text field (if one exists —
   **UNVERIFIED**); (b) flatten to labels (`merge-sha:<sha>`,
   `pr:<n>`) — lossy for the `commits[]` / `files_changed[]` arrays;
   (c) keep `audit` in a livespec-side sidecar keyed by id and NOT push
   it to beads at all. The merge-evidence static check
   (li-tenpup) consumes `merge_sha`/`pr_number`, so whichever encoding
   li-srbpds picks MUST be reliably parseable back into an
   `AuditRecord`. **Recommend option (c) sidecar** unless a beads
   free-text custom field is confirmed in li-srbpds — beads is an
   issue tracker, not a merge-evidence ledger.

4. **`captured_at` (creation timestamp).** beads owns `created_at` /
   `updated_at` itself (server-assigned). On migration (li-zmigvx) the
   livespec `captured_at` cannot be written into a server-managed
   `created_at` without an import that preserves timestamps —
   **UNVERIFIED** whether `bd import`/JSONL ingest honors a supplied
   `created_at`. If not, `captured_at` must be preserved as a label
   `captured-at:<iso>` so the original capture time is not lost to the
   server clock. Confirm the import-timestamp behavior in li-srbpds.

**Cross-tenant dependency edges** are a fifth latent gap: beads
dependencies are intra-DB only, so any `depends_on` entry whose `kind`
is not `local` (a cross-repo dependency, if the typed-dict form ever
grows one) has no beads representation. Today the only observed `kind`
is `local`, so this is a forward-looking flag for li-srbpds, not a
migration blocker for li-zmigvx.

### 1.4 Mapping summary (cleanliness tiers)

- **Identity / near-identity (cleanest):** `type`, `status`, `title`,
  `description`. The `type` and `status` enums line up field-for-field.
- **Native beads relationship:** `depends_on` (`blocks`),
  `superseded_by` (`supersedes`), epic linkage (`parent-child`).
- **Composed / label-encoded (bridge-owned):** `priority` (scale TBD),
  `reason`+`resolution` (`close_reason` / label), `origin`+`gap_id`
  (labels), `spec_commitment_hint` (label), `assignee` (field-or-label,
  unverified).
- **No clean home (design pressure):** `resolution` (typed enum),
  `origin`/`gap_id` (no enum/structured field), the whole `audit`
  sub-object, `captured_at` (server-clock collision), and
  non-`local` cross-tenant `depends_on` kinds.

## Part 2 — Connection model: per-repo beads tenant against `dolt-server`

Grounded in `dolt-server/SPECIFICATION/contracts.md` §"Beads-tenant
contract" + §"Tenant-connection contract". A per-repo beads client runs
in **server mode** against the shared multi-DB Dolt server; each repo is
a **distinct tenant database**. The **tenant DB name** is the
load-bearing tenant identity (`database == server_user == tenant`, one
`≤32`-char Dolt name serving all three). The beads issue-ID **prefix**
is bd's server-stored create-prefix; it is **decoupled** from the tenant
DB name and need **not** equal it — it MAY be a short readable alias
(e.g. `bd-ib` for the `livespec-orch-beads-fabro` tenant, `bd-gj` for
`livespec-orchestrator-git-jsonl`). Where a repo's prefix happens to
equal its tenant (this core repo is `livespec` == `livespec`), that
equality holds HERE but is no longer a required rule.

### 2.1 Exact connection parameters a per-repo tenant uses

> **CORRECTION (li-srbpds, live-repro 2026-06-08).** The
> `BEADS_DOLT_SERVER_*` env-var surface this section originally assumed
> is **WRONG for v1.0.5**. v1.0.5 server-mode connects via **`bd init`
> FLAGS**, not those env vars. A live-repro against the running
> `dolt-server` (one throwaway tenant, server mode, `bd` v1.0.5)
> established the verified surface below. The pre-correction env-var
> table is dropped; do NOT set `BEADS_DOLT_SERVER_MODE` /
> `BEADS_DOLT_SERVER_HOST` / `BEADS_DOLT_SERVER_PORT` /
> `BEADS_DOLT_SERVER_SOCKET` / `BEADS_DOLT_SERVER_USER` — they are not
> the v1.0.5 connection interface.

**Verified v1.0.5 server-mode connection surface (FLAGS, not env vars):**

- **Only env var:** `BEADS_DOLT_PASSWORD` (the tenant password; secret,
  never committed). All other connection inputs are flags.
- **Flags:**
  - `--server` — select server mode.
  - `--external` — the server is **externally managed**; bd MUST NOT
    manage the server lifecycle (no auto-start/stop).
  - `--server-host 127.0.0.1`
  - `--server-port 3307`
  - `--server-user <tenant>` — the least-privilege tenant user, scoped to
    `${DB}` only.
  - `--server-socket <path>` — **overrides host/port** when supplied.
    We used **TCP** (`--server-host`/`--server-port`) for the live-repro
    because sandboxed agents lack `0750` socket-directory access; the
    socket transport remains available for non-sandboxed callers.
  - `--database <tenant>` — select the tenant DB explicitly (the server
    infers no default tenant).
  - `--prefix <issue-prefix>` — the beads issue-ID create-prefix. It is
    **decoupled** from the tenant DB name (`${DB}`) and need **not**
    equal it; it MAY be a short readable alias. For the livespec core
    repo the prefix happens to equal the DB (`livespec`), so issue ids
    become `livespec-…`, but that equality is no longer required.
  - `--skip-agents --skip-hooks` — family rule; **both flags exist** in
    v1.0.5 and MUST both be passed (no agent files / git hooks injected
    into the consuming repo).
  - `--non-interactive --quiet` — noninteractive-only bd rule.
- **Config-key equivalent:** `dolt.mode=server`.
- **The exact working init command (verified live-repro):**

  ```
  bd init --server --external \
    --server-host 127.0.0.1 --server-port 3307 \
    --server-user <tenant> \
    --database <tenant> --prefix <issue-prefix> \
    --skip-agents --skip-hooks \
    --non-interactive --quiet
  ```

- **Set `dolt.auto-start: false`** in bd config so `bd dolt status`
  truthfully reports `running (external)` (works around #3550); without
  it, `bd dolt status` cosmetically says "not running" even though all
  ops succeed (`bd ping` confirms liveness).
- **`bd init` still creates a local `.beads/` + `.gitignore` in CWD.**
  Run it **only inside the consuming repo** with `--skip-hooks` (and
  `--stealth` where applicable) so it never injects git hooks. See §2.2.
- **Pin the binary by content:** sha256
  `24706f65…aacf3` for `beads_1.0.5_linux_amd64.tar.gz`. **AVOID the
  stale mise shim** at `~/.local/share/mise/shims/bd` (it resolves to
  "not installed") — invoke by **absolute path** or a properly-managed
  pin.

The tenant DB is selected explicitly via `--database` (the server infers
no default tenant), and the tenant is onboarded against an
**already-created** tenant DB (§2.2) — the per-repo client never does
`CREATE DATABASE`.

### 2.2 Initialization invariants (from the `dolt-server` contract)

- Init MUST be **non-interactive** and MUST NOT inject agent files or
  git hooks into the consuming repo: `bd init --server` with `--quiet`,
  plus `--stealth` where the repo must carry no beads git operations.
  (Matches the livespec rule `bd init --skip-agents --skip-hooks` from
  prior family practice and the "Beads invariants" noninteractive-only
  rule.)
- **Server-mode auto-commit MUST stay OFF** (the default). Per-write
  `DOLT_COMMIT` under concurrent load raises "database is read only";
  the server owns the transaction lifecycle. The bridge MUST NOT
  re-enable per-write commits.
- The tenant is onboarded against an **already-created** tenant DB
  (`scripts/onboard-tenant.sh` on the server, run as the ops user over
  the socket) — the per-repo client never does `CREATE DATABASE`.

### 2.3 Known-bug envelope gate (cite, do not re-verify)

`dolt-server` §"Beads-tenant contract" §"Known-upstream-bug envelope"
requires that, before any beads tenant is cut over for production
tracking, **each of the eight issues in
[`beads-problems.md`](./beads-problems.md) is re-verified against the
pinned `bd` version** and recorded as fixed-upstream or worked-around.
That re-verification is **li-mwwdws**, NOT this spike. Two of those
problems directly shape decisions above and should be checked by
li-mwwdws / honored by li-srbpds:

- **Problem 7** (silent `project_id` rewrite + no recovery story):
  **RESOLVED — server mode is IMMUNE (live-repro 2026-06-08, `bd`
  v1.0.5).** `bd init --server` writes a local `.beads/metadata.json`
  whose `project_id` is **server-sourced** (adopts the tenant DB's
  existing `metadata._project_id`, per bd PR #2925), not locally minted.
  A second workspace init'd against the same tenant DB adopted the
  **identical** `project_id` and cross-updated issues with **zero
  `workspace identity mismatch` errors**. The embedded-mode silent-
  rewrite trap does not occur in server mode. Confirmed by live repro,
  not merely scope-argued — see
  [`beads-problems.md`](./beads-problems.md) Problem 7 Status
  (2026-06-08). li-zmigvx may cut over without the embedded-mode
  identity-mismatch concern.
- **Problem 8** (`core.hooksPath` ownership race): the `--stealth` /
  no-git-hooks init above is the structural avoidance; the bridge must
  never install beads git hooks into a livespec-family repo.

## RESOLVED beads-side assumptions (li-mwwdws, 2026-06-08)

The nine open beads-side questions below were resolved by **li-mwwdws**
against the v1.0.5 source/docs (the schema migrations under
`internal/storage/schema/migrations/`, `docs/CLI_REFERENCE.md`,
`docs/DEPENDENCIES.md`, `docs/JSON_SCHEMA.md`, and the GitHub issue
tracker — all read 2026-06-08). Eight of nine were **RESOLVED from
source**; the ninth (#9, server-mode epic rollup) was
NEEDS-LIVE-REPRO and is now **RESOLVED by the 2026-06-08 live-repro**
(server-mode epic rollup is stable — see item 9). **All nine are now
resolved.**

> **Headline for li-srbpds: the mapping is in much better shape than the
> spike feared.** beads accepts operator-supplied ids, agrees on
> priority direction, has a first-class `assignee`, has *multiple*
> structured free-text fields **plus a generic `metadata JSON` column**
> (so the `AuditRecord` has a real carrier — the "biggest gap" in §1.3
> is no longer forced into a sidecar), and `bd import` **preserves
> supplied timestamps**. The one residual risk (a server-mode
> epic-children rollup display bug, #3445) was **cleared by the
> 2026-06-08 live-repro** — server-mode epic rollup is stable (see
> item 9).

1. **`bd create` operator-supplied id — RESOLVED: SUPPORTED.**
   `bd create --id string` is documented as "Explicit issue ID (e.g.,
   `bd-42` for partitioning)" (`docs/CLI_REFERENCE.md`). Combined with
   the tenant prefix == DB rule (§1.1), the legacy `li-<suffix>` random
   suffix CAN be preserved as `livespec-<suffix>` by passing
   `--id livespec-<suffix>` at create/import time. **No id-remap table is
   needed for li-zmigvx** — but the bridge MUST emit the explicit id
   (and `bd import` honors the `id` field per
   §"bd import → Common fields"). Note the id column is
   `VARCHAR(255) PRIMARY KEY` (migration `0001`).
2. **beads priority direction — RESOLVED: `0` IS highest.**
   `docs/CLI_REFERENCE.md`: "`--priority string  Priority (0-4 or P0-P4,
   0=highest) (default 2)`"; `bd priority` examples show `0 = Critical`,
   `2 = Medium`. Schema: `priority INT NOT NULL DEFAULT 2`. The `bd
   import` doc adds "`priority 0-4 (0 = critical). 0 is preserved (no
   omitempty)`." **Action for li-srbpds:** confirm the *livespec* side
   also treats 0 as highest; if so this is identity, else the bridge
   inverts once. (livespec `priority` is a bare `int` with no
   spec-pinned scale — that is the only remaining unknown, and it is
   livespec-side, not beads-side.)
3. **`assignee` first-class? — RESOLVED: YES, first-class.** Migration
   `0001_create_issues.up.sql` declares `assignee VARCHAR(255)` with an
   index `idx_issues_assignee`; `bd ready --assignee` / `--unassigned`
   filters and `bd assign` exist (`docs/DEPENDENCIES.md`,
   `docs/CLI_REFERENCE.md`). The §1.2 label fallback is unnecessary —
   map `assignee` → `assignee` identity (null when absent).
4. **Structured free-text custom field for `AuditRecord` —
   RESOLVED: AMPLE carriers exist.** The issues table has **three**
   dedicated free-text columns — `design TEXT`, `acceptance_criteria
   TEXT`, `notes TEXT` (all `NOT NULL`) — **and a generic `metadata JSON
   DEFAULT (JSON_OBJECT())` column**. `bd import` documents `metadata` as
   "Arbitrary JSON object preserved verbatim." **Recommendation for
   li-srbpds: serialize the whole `AuditRecord` into the `metadata` JSON
   column** (lossless for `commits[]` / `files_changed[]` arrays and
   round-trips cleanly), rather than the §1.3 option-(c) livespec-side
   sidecar. This RESOLVES the spike's "biggest gap." The merge-evidence
   static check (li-tenpup) can then parse `merge_sha`/`pr_number` back
   out of `metadata` reliably. (`notes`/`design` remain available for
   human-readable spillover if desired.)
5. **`bd import` honors supplied `created_at` — RESOLVED: YES.**
   `docs/CLI_REFERENCE.md` (bd import): "Timestamps (`created_at`,
   `updated_at`, `started_at`, `closed_at`) **are preserved when present
   in the JSONL** and otherwise filled in by the importer." Schema:
   `created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP` — a normal
   settable column. **So livespec `captured_at` maps directly to
   `created_at` on import; no `captured-at:<iso>` label workaround is
   needed** to dodge the server clock.
6. **`supersedes` / `parent-child` edge direction — RESOLVED.**
   `docs/DEPENDENCIES.md`: `bd dep add issue-2 issue-1` means "issue-2
   depends on issue-1 (issue-1 blocks issue-2)" — i.e. `bd dep add
   <FROM> <TO>` stores the edge as *FROM depends-on TO*. The
   `dependencies` table (migration `0002`) is `(issue_id,
   depends_on_id, type)`. Therefore, matching the spike's stated
   intent: for `superseded_by` (B supersedes A), `bd dep add B A --type
   supersedes` (source = the superseding issue). `supersedes` is a
   confirmed non-blocking type and `parent-child` a confirmed blocking
   type in the v1.0.5 dependency-type table.
7. **`--parent` settable post-hoc — RESOLVED: YES.**
   `docs/CLI_REFERENCE.md` (bd update): "`--parent string  New parent
   issue ID (reparents the issue, use empty string to remove parent)`."
   So li-zmigvx can attach already-existing epics' children to the epic
   after creation via `bd update <child> --parent <epic>` (and detach
   with `--parent ""`). The create-time `bd create --parent` also exists.
8. **Exhaustive v1.0.5 issue field list — RESOLVED from source.**
   The authoritative column set is `migrations/0001_create_issues.up.sql`
   at the `v1.0.5` tag. Issue-relevant columns: `id, content_hash,
   title, description, design, acceptance_criteria, notes, status,
   priority, issue_type, assignee, estimated_minutes, created_at,
   created_by, owner, updated_at, closed_at, closed_by_session,
   external_ref, spec_id, … metadata (JSON), source_repo, close_reason,
   due_at, defer_until` (plus wisp/event/agent-protocol columns livespec
   never writes: `ephemeral, wisp_type, pinned, is_template, mol_type,
   work_type, event_kind, actor, target, payload, await_*, hook_bead,
   role_bead, agent_state, rig, …`). Note: `issue_type` (not `type`) is
   the column name; the JSON/CLI surface exposes it as `issue_type`.
   Also note `spec_id VARCHAR(1024)` exists as a native field — a cleaner
   home for `spec_commitment_hint` than the §1.2 label
   (`spec-commitment:<id_hint>`); **li-srbpds should evaluate
   `spec_id` vs the label.** The dependency row schema is `(issue_id,
   depends_on_id, type, created_at, created_by, metadata, thread_id)`.
9. **Epic status-rollup sharp edge — RESOLVED: stable & correct in
   server mode (live-repro 2026-06-08, `bd` v1.0.5).** The specific
   symptom named in the spike (completed epics showing BLOCKED with "0
   dependencies", child tasks leaking into `bd ready`) is issue
   [#1495](https://github.com/gastownhall/beads/issues/1495), **CLOSED/
   completed** (2026-03-12, fixed in v0.60.0 commits `21e23bc5` +
   `6155b6cd`) — fixed in both v1.0.4 and v1.0.5. The related
   currently-OPEN server-mode rollup bug
   [#3445](https://github.com/gastownhall/beads/issues/3445) ("`bd show
   <epic>` CHILDREN renders 0/12/24 children depending on
   `wisp_dependencies` state, **server mode**") was the NEEDS-LIVE-REPRO
   risk. **Live-repro result: NO flapping — server-mode epic rollup is
   stable and correct.** An epic + 6 children created via `bd create
   --parent` (hierarchical ids `<epic>.1…6`); `bd show <epic>` rollup
   tracked `0/6 → 2/6 → 4/6 → 3/6` across child state changes with **no
   flapping**, stable across repeated calls; `bd children` and `bd list
   --parent` **agreed** with the rollup. Root cause sidestepped:
   membership is tracked via `type='parent-child'` dependency rows, and
   the `wisp_dependencies` table that #3445 implicates **was empty for
   real (non-wisp) beads**. **li-srbpds may rely on `parent-child` epic
   rollup / `bd show <epic>` child counts in server mode.** (The
   `parent` field / `bd list --parent` query also agrees, so it remains
   available as a belt-and-suspenders source if ever needed.)

### Release-version caveat (cross-reference)

The above answers are version-stable across v1.0.4/v1.0.5 (schema +
CLI surface unchanged for these fields). The pinned target version was
previously contested (v1.0.5 a gated do-not-upgrade pre-release per
multi-machine sync corruptor #4259; v1.0.4 lacking the Problem 1/3/4/5
init/sync fixes). **RESOLVED 2026-06-08 (live-repro): pin v1.0.5.** Per
[`beads-problems.md`](./beads-problems.md) §"Release-landscape finding"
(2026-06-08 SUPERSEDED banner), the #4259/`0043` corruptor only breaks
`bd dolt` multi-machine sync between embedded stores; the `dolt-server`
**standalone** model (one server, bd as plain SQL client, no Dolt remote
on the tenant) never invokes that path, so the fork does not bind.
v1.0.5 carries the Problem 1/3/4/5 fixes, and v1.0.4↔v1.0.5 mixing
against one server is unsafe (#4152 forward schema-skew guard) — so
li-srbpds / li-zmigvx **standardize the whole family on v1.0.5**.
