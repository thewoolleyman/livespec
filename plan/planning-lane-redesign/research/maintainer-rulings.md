# planning-lane-redesign — maintainer rulings

Decisions from the 2026-08-04 capture session, separated by authority:
**rulings** are the maintainer's explicit statements; **accepted
recommendations** are agent proposals the maintainer approved for
capture by opening this plan, still subject to scoping and (where they
touch spec) ratification. Where anything elsewhere in this plan
disagrees with a ruling, the ruling wins.

## Rulings (maintainer-stated, 2026-08-04)

1. **Mutable planning state belongs in the ledger.** The plan
   directory keeps metadata clearly indicating the epic/beads plus
   original research items (seed, human or human+LLM research); "all
   actual planning and handoff must live in the ledger." (The
   maintainer's own sweet-spot formulation.)
2. **"plan thread" is banned vocabulary.** Two words for one thing,
   never approved, agent-coined. The thing is called a **plan**.
   Quoting pre-existing text verbatim for mechanical replacement
   targeting is the only exception; frozen archive/history trees keep
   the old term.
3. **No gate may presume a seed/research shape that does not exist.**
   The seed-requirement trace gate cannot be treated as small or
   independent; it depends on a scoping protocol decision, because
   research docs are freeform and not even filename-uniform.
4. **This plan's home is livespec core**, approved on the
   recommendation that core owns the Planning Lane contract and is
   upstream of both orchestrator realizations.

## Accepted recommendations (capture-stage, not yet ratified)

- **Scoping as an explicit ledger event** (route 2 in
  `brainstorm.md`): research prose stays freeform; requirement
  carriers — including explicitly-deferred ones — are cut into the
  ledger before the epic takes implementation children; deferral is a
  ledger state, never a prose sentence.
- **Two-leg archive gate:** mechanical (no undisposed children) plus
  an independent adversarial completeness review of research docs
  against the epic's children at archive time.
- **Handoff entries carry only non-derivable content**; derivable
  state is read fresh from the ledger and git at resume time.
- **The vocabulary rename folds into the migration's surface
  rewrites** (one cross-repo contract change, not two), and the ban is
  recorded in the fleet's committed agent-instruction surface
  alongside the existing vocabulary bans.
- **Go/no-go precondition:** a spike writing a real-sized (30–50 KB)
  Markdown handoff into a scratch tenant and reading it back through
  the CLI and console surfaces, before the ledger-held handoff design
  is committed.
- **Write-once metadata anchor** in `plan/<slug>/` naming the epic id,
  never updated after plan open.
