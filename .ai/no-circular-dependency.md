# The No-Circular-Dependency Directive

**Read this BEFORE adding any cross-repo check, tool, gate, or file read to a
fleet repo.** Maintainer-declared 2026-07-12.

## The directive

A **foundational / upstream** repo must NEVER contain a check, tool, or read
that reaches INTO a **downstream consumer** of it. Doing so creates a circular
dependency: `upstream → downstream → upstream`.

## Scope — CODE AND ARTIFACTS ONLY, never work-items

**This directive governs code and hard dependencies: checks, tools, gates,
file reads, imports, clones, and pinned artifacts that live in a repo and run
in its CI.** It does NOT govern **work-items / ledger (beads) records**, and it
never has. Maintainer-clarified 2026-07-19, after a session wrongly cited it to
avoid linking a cross-tenant epic.

The ledger is a **planning tool**. A dependency between two work-items is a
statement that one piece of work genuinely blocks or contains another —
a fact about the work, not a build-time coupling. **Work-item dependencies may
point in EITHER direction across repos whenever that dependency actually
exists**, including from an upstream repo's item to a downstream repo's item.
Linking them creates no cycle: no CI job clones anything, no build resolves
anything, nothing fails at runtime because an edge points "the wrong way."

So: an epic in `livespec` core MAY carry children in `livespec-dev-tooling`
(upstream) and `livespec-console-beads-fabro` (downstream) simultaneously, and
those edges may be modelled in whichever direction reflects the real
relationship. Do not contort a cross-repo epic, and do not fall back to
citing ids in prose, to satisfy a rule that was never about planning records.

The test below is a CI test for a reason — *"would the upstream repo's CI have
to clone the downstream repo?"* A ledger edge answers "no" trivially, which is
the tell that it is out of scope.

The canonical upstream repo is **`livespec-dev-tooling`** (the shared
enforcement suite every fleet repo consumes), and **`livespec` core** (the
contract + templates). The orchestrator, the console, the Drivers, and every
adopter are **downstream** of those. So a check *inside* `livespec-dev-tooling`
that reads, clones, or parses a file from `livespec-orchestrator-beads-fabro`,
`livespec-console-beads-fabro`, an adopter, etc. is a circular dependency and
is banned — even when it "works," because the upstream's CI then depends on a
downstream repo's layout/availability.

## The test

Before wiring a cross-repo read, ask: **"does this make repo A read repo B,
while B already depends on A?"** If yes, it is circular — stop. The concrete
tell in CI is *"the upstream repo's CI would have to clone/fetch the downstream
repo to run this check."* That clone IS the cycle.

## The two allowed resolutions

1. **Design the coupling away (preferred — no check at all).** Make the
   consumer *resolve* the producer's value at runtime instead of pinning its
   own copy that then needs a cross-repo check. Example (fabro-ci, 2026-07-12):
   the Codex adapter command was hardcoded `npx -y @zed-industries/codex-acp@0.16.0`,
   which would have "needed" a lockstep against the image's baked
   `CODEX_ACP_VERSION`. The fix was NOT a check — it was making the command
   **version-less** (`npx -y @zed-industries/codex-acp`) so it resolves the
   baked global, exactly as the Claude adapter already does. Single source of
   truth, nothing can drift, no cross-repo read.

2. **Put the check on the DOWNSTREAM (consumer) side, reading UP.** When a
   match-check is genuinely wanted, it lives in the *consumer* repo reading the
   *producer's* value (`consumer → producer` — cycle-free, because the consumer
   already depends on the producer). Example: if the console must assert its
   `rust-toolchain.toml` matches the baked image's rust ARG, that check lives
   in the **console** repo reading the image, NOT in `livespec-dev-tooling`
   reading the console.

## Corollary — design drift away before adding a check

A cross-repo *consistency* check is often a symptom that the same value is
pinned in two places. Prefer collapsing to a single source of truth (resolution
1) over adding the Nth guard. Reach for a check only when a single source
genuinely cannot be had, and then only on the consumer side (resolution 2).

## Why this is a standing directive, not a one-off

The fleet shares one enforcement suite over many independent repos, so it is
tempting to "just add the check where the check lives" (`livespec-dev-tooling`).
That instinct is exactly what creates the cycle. The dependency *direction* —
not the convenience of where the check code sits — decides where a cross-repo
read is allowed.
