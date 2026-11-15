---
topic: fleet-secrets-parameter-store-canonical
author: claude-opus-5-5
created_at: 2026-11-15T04:46:08Z
---

## Proposal: L01 — Parameter Store is the canonical fleet secret source; the installed wrapper keeps its interface

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Rename the fleet-source heading to “Fleet secrets — Parameter Store as canonical source”. Replace the fleet canonical-source claims with: “Parameter Store is canonical and written first; the livespec Environment is a temporary downstream copy. Callers retain `/usr/local/bin/with-livespec-env.sh` and its existing calling convention until each host converts. Under maintainer ruling B, canonical AWS writes use one dedicated write-only writer; host identities remain read-only. Homelab owns the shared service; see homelab `SPECIFICATION/spec.md` §“Shared GitOps credential service” and §“Secrets”. Detailed writer policy is governed by homelab’s specification lifecycle.” This is the ruling-level limit: do not specify writer bootstrap identity, stdin tooling, exact bindings, custody, rotation, issuance or launcher implementation here before H11 revise. Preserve current bootstrap exceptions, independent-adopter boundaries and local env/exit semantics. Keep mint/apply OPEN and deletion/revocation actor unruled. The cited homelab text establishes ownership and migration constraints, not an already-ratified singleton writer contract.

### Motivation

Coordinator-approved change-plan-v4.md (plan epic overseer-iyfjbo, central credential service), entry L01 (coordinator fix 3: ruling-level writer/read-only wording only, citing homelab's spec). The maintainer's rulings of 2026-11-15 make AWS SSM Parameter Store canonical for fleet secrets: one dedicated write-only writer identity, separate from host readers; hosts read-only; `/usr/local/bin/with-livespec-env.sh` keeps its name and calling convention and will read Parameter Store through homelab's shared-credentials launcher; no dual-backend fallback. NO HOST HAS CONVERTED YET, so the spec must state the canonical source and the target wrapper backend without describing any converted state as current. No deployment, key mint, owner apply, deletion or revocation is authorized by this proposal; the mint/apply question stays OPEN and the deletion/revocation actor stays unruled.

### Proposed Changes

Apply this approved disposition exactly. Unmentioned requirements MUST remain unchanged.

Rename the fleet-source heading to “Fleet secrets — Parameter Store as canonical source”. Replace the fleet canonical-source claims with: “Parameter Store is canonical and written first; the livespec Environment is a temporary downstream copy. Callers retain `/usr/local/bin/with-livespec-env.sh` and its existing calling convention until each host converts. Under maintainer ruling B, canonical AWS writes use one dedicated write-only writer; host identities remain read-only. Homelab owns the shared service; see homelab `SPECIFICATION/spec.md` §“Shared GitOps credential service” and §“Secrets”. Detailed writer policy is governed by homelab’s specification lifecycle.” This is the ruling-level limit: do not specify writer bootstrap identity, stdin tooling, exact bindings, custody, rotation, issuance or launcher implementation here before H11 revise. Preserve current bootstrap exceptions, independent-adopter boundaries and local env/exit semantics. Keep mint/apply OPEN and deletion/revocation actor unruled. The cited homelab text establishes ownership and migration constraints, not an already-ratified singleton writer contract.

Current text, `SPECIFICATION/non-functional-requirements.md:1348` (verified at livespec master 90409a29, v0.47.11):

```text
### Fleet secrets — 1Password Environment as canonical source
```

Approved source citation (change-plan-v4 L01): homelab/SPECIFICATION/spec.md:219: “The service MUST preserve canonical secret ownership, expose the scoped provisioning and verification interface in contracts.md, and preserve existing consumers through any deliberate source migration.” Lines 202–206 say “Git contains secret references and policy, never secret values, and no secret has two writable authorities.” The singleton/read-only sentence above derives from ruling B, not from a claim that H11 already revised homelab. H11 stays unedited.

Freshness note for the reviser (evidence only; it does not change the disposition): at homelab origin/main 6580040 the cited `SPECIFICATION/spec.md` lines are unchanged (§"Secrets" at L200, the two-writable-authorities sentence at L204–206, §"Shared GitOps credential service" at L213, the canonical-ownership sentence at L219). Since the plan's 14aa48e snapshot, homelab revisions v013–v015 added a dedicated-writer clause to homelab `SPECIFICATION/contracts.md`; the reviser should re-check the disposition's closing caveat about an already-ratified singleton writer contract against that text.

Mechanical consequence of the heading rename, noted for the reviser: the in-file cross-references to the old heading in `non-functional-requirements.md` (currently at L474, L1378 and L1409) follow the rename; their content is otherwise unchanged. The three `contracts.md` references are carried by the companion L02 proposal in this file.

## Proposal: L02 — contracts.md cites the renamed fleet-secrets heading; independent tenants keep their own source

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Update all three heading references (L62/136/275) to L01. Family credentials come through the unchanged installed wrapper; Parameter Store is canonical, but wrapper backend changes only on each host’s conversion. Independent tenants keep their own source and bare BEADS_DOLT_PASSWORD; do not require their migration.

### Motivation

Coordinator-approved change-plan-v4.md (plan epic overseer-iyfjbo, central credential service), entry L02 (same batch as L01). The maintainer's rulings of 2026-11-15 make AWS SSM Parameter Store canonical for fleet secrets: one dedicated write-only writer identity, separate from host readers; hosts read-only; `/usr/local/bin/with-livespec-env.sh` keeps its name and calling convention and will read Parameter Store through homelab's shared-credentials launcher; no dual-backend fallback. NO HOST HAS CONVERTED YET, so the spec must state the canonical source and the target wrapper backend without describing any converted state as current. No deployment, key mint, owner apply, deletion or revocation is authorized by this proposal; the mint/apply question stays OPEN and the deletion/revocation actor stays unruled.

### Proposed Changes

Apply this approved disposition exactly. Unmentioned requirements MUST remain unchanged.

Update all three heading references (L62/136/275) to L01. Family credentials come through the unchanged installed wrapper; Parameter Store is canonical, but wrapper backend changes only on each host’s conversion. Independent tenants keep their own source and bare BEADS_DOLT_PASSWORD; do not require their migration.

Current text (verified at livespec master 90409a29): `SPECIFICATION/contracts.md` L62, L136 and L275 each cite `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source". L62 excerpt:

```text
`non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source". Like the other named CLIs, its resolvability is verified by the `config-named-cli-callability` invariant per §"Doctor cross-boundary invariants"
```

Each reference is updated to the renamed heading §"Fleet secrets — Parameter Store as canonical source" from the L01 proposal.
