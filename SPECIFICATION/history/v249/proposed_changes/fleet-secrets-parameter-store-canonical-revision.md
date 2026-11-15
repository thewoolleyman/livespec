---
proposal: fleet-secrets-parameter-store-canonical.md
decision: modify
revised_at: 2026-11-15T05:10:11Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Modified and accepted by the decider, legacy-coordinator-agent, under its R301 authority (plan epic overseer-iyfjbo, change-plan-v4 entries L01 and L02, coordinator fix 3). The maintainer's 2026-11-15 rulings make AWS SSM Parameter Store canonical for fleet secrets, with one dedicated write-only writer separate from read-only host identities, and keep `/usr/local/bin/with-livespec-env.sh` and its calling convention, with no dual-backend fallback. No host has converted, so the wording states the canonical source and the conversion target without describing any converted state as current. Preserved unchanged: the Local consumption rule including the sealed bootstrap-token exception, the Credential wrapper contract, independent-adopter boundaries, and local env/exit semantics; the mint/apply question stays OPEN and the deletion/revocation actor stays unruled. Explicit NON-CHANGE: the **GitHub Actions exception** paragraph is deliberately left verbatim this wave. It is a separate surface with its own consumers (the hosted-runner Actions secrets projected from the Environment), and the decider ruled that L01's replacement of the canonical-source claims does not reach it. Also unchanged this wave: the body of the §"CI telemetry export" ingest-key sentence beyond its heading citation. Stale-branch precondition (Step 3.5) skipped via `--skip-stale-branch-check` at the decider's ruling. Warning, recorded verbatim: "spec/doctor-surfaces-open-spec-pull-requests (livespec#3250, e887b75b) is a live, graded PASS, unrelated proposal by throughput-plans-coordinator; neither merged nor abandoned; no file overlap with fleet secrets or the wrapper table."

## Modifications

Modified at the decider's rulings (legacy-coordinator-agent, R301):
1. L01's "Callers retain ... until each host converts" sentence is replaced with: "Callers retain /usr/local/bin/with-livespec-env.sh and its calling convention; on each host's conversion its backend becomes homelab's shared-credentials launcher."
2. The proposal's homelab caveat is stale and is dropped. The Canonical source paragraph instead cites homelab v016 `SPECIFICATION/contracts.md` §"Shared credential consumer contract" (verified on homelab origin/main 30733aa), which ratifies the dedicated writer: the committed unsealing wrapper, its isolated interpreter and root-ownership refusal, and the canonical secret writer.
3. Rename scope: the heading becomes "Fleet secrets — Parameter Store as canonical source"; the three in-file citations in non-functional-requirements.md (§"CI telemetry export" ingest-key discipline, §"Request-budget discipline" contract, and §"Fleet membership contract" reconcile mode) and the three contracts.md citations follow it. L01's replacement of the fleet canonical-source claims reaches the **Write-side constraint** paragraph: the canonical write path is homelab's canonical secret writer acting as the dedicated writer role, and manual 1Password UI writes are no longer canonical.
L02 is applied as proposed: contracts.md's beads-runtime clause names the unchanged installed wrapper, states Parameter Store as the canonical source with the backend changing only on each host's conversion, and keeps independent tenants on their own source with no required migration.

## Resulting Changes

- contracts.md
- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-15T05:07:39Z
verdict: NO BLOCKERS
proposal_stem: fleet-secrets-parameter-store-canonical
content_digest: 97eed89153f63463962461ad014a19a328f81ec92fde3cc55ca009e38d01467d
