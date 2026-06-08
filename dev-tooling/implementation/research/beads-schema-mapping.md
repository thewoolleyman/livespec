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
a **distinct tenant database**, and the beads **prefix equals the tenant
database name** (this is the load-bearing identity rule —
`dolt-server` §"Tenant-onboarding contract": "A tenant `${DB}` name …
MUST match the beads prefix when the tenant is a beads client").

### 2.1 Exact connection parameters a per-repo tenant uses

Set via environment (per the `dolt-server` Beads-tenant contract table),
preferring the Unix socket transport for sandboxed agents:

| `bd` setting | Env var | Value for a per-repo tenant |
|---|---|---|
| server mode | `BEADS_DOLT_SERVER_MODE` | `1` |
| host | `BEADS_DOLT_SERVER_HOST` | `127.0.0.1` |
| port | `BEADS_DOLT_SERVER_PORT` | `${DOLT_PORT}` (default `3307`) |
| socket (preferred) | `BEADS_DOLT_SERVER_SOCKET` | `${DOLT_SOCKET}` (default `/var/lib/doltdb/dolt.sock`) |
| user | `BEADS_DOLT_SERVER_USER` | the tenant `${USER}` (least-privilege, scoped to `${DB}` only) |
| password | `BEADS_DOLT_PASSWORD` | the tenant `${PASSWORD}` (secret, never committed) |

The tenant DB is selected explicitly — the server infers no default
tenant. The **`--prefix` doubles as the tenant database name `${DB}`**:
for the livespec repo, prefix == DB == (e.g.) `livespec`, so issue ids
become `livespec-…`.

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

- **Problem 7** (silent `project_id` rewrite + no recovery story): the
  tenant-DB identity is server-owned in server mode, which sidesteps
  the embedded-mode `metadata.json` rewrite trap — but li-mwwdws should
  confirm the server-mode path is not subject to an analogous identity
  mismatch on the pinned version before li-zmigvx cuts over.
- **Problem 8** (`core.hooksPath` ownership race): the `--stealth` /
  no-git-hooks init above is the structural avoidance; the bridge must
  never install beads git hooks into a livespec-family repo.

## UNVERIFIED beads-side assumptions (route to li-mwwdws / li-srbpds)

The orchestrator should route these open beads-side questions before
li-srbpds asserts a final mapping or li-zmigvx migrates real data:

1. Whether `bd create` accepts an **operator-supplied id suffix** (to
   preserve the legacy `li-<suffix>` across the prefix change), or
   beads always mints its own id (→ li-zmigvx needs an id remap table).
2. The **beads priority direction** (is `0` highest?) vs the livespec
   `priority` convention — needed before claiming identity.
3. Whether **`assignee` is a first-class beads issue field** or must
   fall back to a label.
4. Whether beads exposes any **structured free-text custom field**
   (`notes` / `design` / `acceptance_criteria`) usable to carry the
   serialized `AuditRecord`, or whether `audit` must live in a
   livespec-side sidecar.
5. Whether **`bd import` / JSONL ingest honors a supplied
   `created_at`** (else `captured_at` must be label-encoded to avoid
   server-clock collision).
6. The **edge direction** of the `supersedes` and `parent-child`
   relationships (which issue is the source of the edge).
7. Whether **`--parent` is settable post-hoc** on an existing issue
   (needed by li-zmigvx for already-existing epics).
8. The **exact, exhaustive beads issue record field list** in the
   pinned `bd` v1.0.5 JSONL export (the public docs publish only an
   illustrative subset) — pin this from `bd export` output or source on
   the actual pinned version in li-srbpds.
9. The **beads epic status-rollup sharp edge** (completed epics showing
   BLOCKED with "0 dependencies") — verify against the pin in
   li-mwwdws before relying on `parent-child` epic rollup.
