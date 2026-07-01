---
topic: credential-wrapper
author: claude-opus-4-8-1m
created_at: 2026-07-01T07:00:07Z
---

## Proposal: generalize-fleet-secrets-to-backend-agnostic-credential-wrapper

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- docs/installation.md
- AGENTS.md

### Summary

Generalize the fleet secret-injection contract in non-functional-requirements.md §"Fleet secrets — 1Password Environment as canonical source" from 1Password/`with-livespec-env.sh`-specific to a backend-agnostic `credential_wrapper`: an opaque literal argv-prefix array declared in `.livespec.jsonc` that injects the project's secrets, execs the child, and propagates its exit code. The livespec 1Password Environment wrapper becomes the fleet reference default of a wrapper-agnostic contract, with AWS/Vault/chamber/dotenvx/custom wrappers as conforming alternatives — so swapping secret backends is a config edit, not a code change. Adds the standardized contract paragraph verbatim as a new bold-lead bullet; folds into existing section bodies with no new H2.

### Motivation

Crit-path step 1 of epic livespec-zd8h. Per plan/credential-wrapper/research/01-design.md, the maintainer directive (locked) requires the credential wrapper to be backend-generic — decoupled from 1Password ahead of a planned AWS migration — with `.livespec.jsonc` gaining a `credential_wrapper` key naming a wrapper CLI that conforms to a standardized contract (inject secrets, exec the child, propagate exit code). The current spec hard-codes the 1Password Environment and `with-livespec-env.sh` as THE contract rather than as the fleet reference default; this generalization makes the contract wrapper-agnostic while preserving the 1Password path as the reference implementation, per research/01-design.md §"2. `credential_wrapper` — opaque literal argv-prefix array" and its conformance matrix.

### Proposed Changes

In `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source", generalize the secret-consumption contract from 1Password/`with-livespec-env.sh`-specific to backend-agnostic. The livespec 1Password Environment (consumed via `with-livespec-env.sh`) becomes the fleet REFERENCE DEFAULT of a wrapper-agnostic contract, not the contract itself. No `## ` H2 is added or renamed; the existing H3 section's bullet bodies are reworded and one bullet is added, so `tests/heading-coverage.json` is NOT affected.

Three edits to the section body:

1. Reword the **Canonical source.** bullet so the 1Password Environment is named as the fleet's reference-default secret STORE (still the single canonical source for the fleet's own secrets), while making explicit that livespec makes no assumption about the backing secret backend — the store an adopter uses is whatever its configured `credential_wrapper` injects (1Password, AWS, Vault, an encrypted `.env`, chamber, dotenvx, or a bare `env`). The fleet's own store remains the livespec 1Password Environment.

2. Reword the **Local consumption rule.** bullet so processes consume secrets via the project's configured `credential_wrapper` — an opaque literal argv-prefix array declared in `.livespec.jsonc` that injects the project's secret environment variables, execs the child, and propagates the child's exit code — rather than naming a 1Password wrapper specifically. The livespec 1Password Environment wrapper `with-livespec-env.sh` is the reference implementation; `aws-vault exec`, `chamber exec`, `op run`, `dotenvx run`, and a custom `with-<project>-env.sh` are conforming alternatives, so swapping the secret backend is a `credential_wrapper` config edit, not a code change. The prohibition on standing secret-bearing files at rest is unchanged.

3. Add a new bold-lead **Credential wrapper.** bullet to the section carrying the standardized wrapper-agnostic contract verbatim (the drop-in text below). This bullet is the authoritative definition of the `credential_wrapper` key that the reworded bullets and the `contracts.md` cross-references point at:

> **Credential wrapper.** A governed project MAY declare a `credential_wrapper`
> in `.livespec.jsonc`: a JSON array of literal argv tokens naming a conforming
> credential-injection CLI and its fixed arguments. A conforming credential
> wrapper is any command that, invoked as `[*credential_wrapper, *child_argv]`,
> (1) injects the project's secret environment variables into the child process
> environment, (2) execs (or runs and awaits) `child_argv` as its child, and
> (3) propagates the child's exit code. livespec treats the array as an opaque
> literal prefix: it prepends the tokens to the command it wants to run and
> invokes the result directly (no shell, no word-splitting, no quoting), and it
> neither synthesizes, repositions, nor strips any `--` separator — the operator
> includes exactly the separator token their chosen backend requires. livespec
> makes no assumption about the secret backend (1Password, AWS, Vault, an
> encrypted `.env`, or a bare `env`); swapping backends is a `credential_wrapper`
> edit, not a code change. A wrapper that must be sourced into the calling shell,
> or that accepts the command only as a single quoted string, does NOT conform.

At revise, co-update the authored-once restatements of the 1Password coupling so they match the generalized contract (list them here as the files this proposal touches; they are updated at revise, not edited now):

- `docs/installation.md` (~L200-203) — the beads-wrapper onboarding restatement currently names the 1Password Environment wrapper (`with-livespec-env.sh`) as the injection mechanism; reword to "the project's configured `credential_wrapper` (the fleet reference default is the 1Password Environment wrapper `with-livespec-env.sh`)".
- root `AGENTS.md` (~L305-313) — the "beads runtime prerequisites" restatement of the tenant-password injection; reword the "injected by THIS project's configured env wrapper" prose to bind it to the `.livespec.jsonc` `credential_wrapper` key, keeping the 1Password Environment wrapper as the reference default.

No new `## ` H2 heading is introduced in any of the five NLSpec files, so `tests/heading-coverage.json` needs no co-edit at revise.

## Proposal: bind-credential-wrapper-key-into-contracts-cli-guard-and-callability

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Bind the new `.livespec.jsonc` `credential_wrapper` key into contracts.md at three existing sections: (1) §"Spec-side CLI contract" — `credential_wrapper` joins the config's named-CLI key set as an optional credential-injection argv-prefix; (2) §"Fleet agent-instruction core" — bind the authored-once phrase "per-project credential-injection wrapper" to the `credential_wrapper` key, and generalize the beads-access guard's `with-<id>-env.sh` recognition to the project's configured `credential_wrapper` (first token), keeping `with-<id>-env.sh` as the reference-default fallback; (3) §"config-named-cli-callability" — extend the invariant so it also verifies the `credential_wrapper` first token resolves and is executable when present. No new H2.

### Motivation

Crit-path step 1 of epic livespec-zd8h. Per plan/credential-wrapper/research/02-surface-inventory.md §"CORE — Contract prose", the contract-surface generalization must (a) make `credential_wrapper` a CORE-owned config key so doctor validates it (not an orchestrator-tier additionalProperties key), (b) bind the existing authored-once beads-runtime phrasing to it so the fleet's single-authoring model does not drift, and (c) generalize the beads-access guard so non-1Password wrappers (aws-vault, chamber, etc.) are recognized as "under a wrapper." These contracts.md edits are the spec-side commitments the schema triplet, doctor callability check, and guard-template implementation (subsequent epic steps) realize.

### Proposed Changes

Bind the new `.livespec.jsonc` `credential_wrapper` key into `contracts.md` at three existing sections. No `## ` H2 heading is added, renamed, or removed — all edits are to existing section bodies and one existing H3 body — so `tests/heading-coverage.json` is NOT affected.

1. §"Spec-side CLI contract" (~L59-63). The paragraph that enumerates what core's config schema carries ("spec-tier facts (`template`, `spec_root`), the orchestrator selection, and the named CLIs") gains the optional `credential_wrapper` credential-injection prefix as a member of the config's named-CLI key set: core's config schema now also carries an optional `credential_wrapper` — a JSON array of literal argv tokens naming the project's conforming credential-injection CLI per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source". Like the other named CLIs, its resolvability is verified by the `config-named-cli-callability` invariant (its first token MUST resolve to an executable).

2. §"Fleet agent-instruction core" (~L250). The authored-once beads-runtime prose already states that every beads tenant injects a single bare `BEADS_DOLT_PASSWORD` "via its configured per-project credential-injection wrapper." Bind that phrase to the new key: the per-project credential-injection wrapper is the `.livespec.jsonc` `credential_wrapper` key (per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source"). The fleet wrapper `with-livespec-env.sh` remains the fleet reference default; an independent (non-fleet) tenant declares its own `credential_wrapper` (e.g. its own `with-<project>-env.sh`). The isolation-boundary sentence (per-tenant SQL user plus DB-scoped grant, not password distinctness or wrapper identity) is unchanged.

3. §"Fleet agent-instruction core" beads-access-guard paragraph (~L258). The guard currently blocks a bare `bd`/`dolt`/`mysql` invocation "unless it runs under a recognized per-project credential-injection wrapper (any `with-<id>-env.sh`)." Generalize the recognition from the `with-<id>-env.sh` literal to the project's configured `credential_wrapper`: the guard recognizes a wrapped invocation by the resolved `credential_wrapper`'s first token, with `with-<id>-env.sh` retained as the reference-default fallback pattern. The guard remains best-effort string-level footgun-prevention, not the isolation boundary; the blocked set stays `bd`/`dolt`/`mysql`.

4. §"Doctor cross-boundary invariants" → `### config-named-cli-callability` (~L133-135). Extend the invariant's coverage so "every CLI named in `.livespec.jsonc`" explicitly includes the `credential_wrapper` credential-injection prefix's first token (spec-side per §"Spec-side CLI contract", orchestrator-side per §"Orchestrator CLI contract — the three named CLIs", and the credential-injection wrapper per `non-functional-requirements.md` §"Fleet secrets — 1Password Environment as canonical source"). When `credential_wrapper` is present and non-empty, its first token MUST resolve and be executable; a missing or non-executable resolution fires `fail` naming the config key. When absent/empty, the invariant is a no-op for that key (the key is OPTIONAL). The zero-shape callability discipline (no required probe subcommand) is unchanged.
