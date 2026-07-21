# Spec-proposal review — the defect taxonomy a Fable reviewer checks

Read this when performing (or briefing) the independent adversarial review that
`AGENTS.md` requires before every `/livespec:revise` accept, and when authoring a
proposed change you want to survive that review.

`AGENTS.md` names five minimum criteria: replacement-target fidelity,
design-record fidelity, drift-sweep completeness, ratification mechanics, and
cross-repo consistency. Those catch a proposal that is *wrong about the world*.
The three below catch a proposal that is *correct today and rots on contact with
its own ratification* — a class the five do not address, because each of these
proposals is accurate at the moment it is written.

Every one is drawn from a defect that actually shipped. None is hypothetical.

## 1. Claims that expire at ratification

**Reject any spec sentence whose truth depends on the pre-ratification state.**

A proposal is written while the change is pending, so it is natural to describe
the world as it is at authoring time. The moment `/livespec:revise` accepts it,
that description is part of the ratified spec — and it is now false, because
ratification is exactly the event that changed the thing being described.

The tell is tense and aspect, not content: *"is not yet"*, *"currently lacks"*,
*"will be"*, *"remains unimplemented"*, *"today the Dispatcher does X"*. A spec
states contracts and invariants; it is not a status report. If a sentence would
need editing the instant it lands, it does not belong in the spec at all — the
livespec discipline already says an artifact belongs in `SPECIFICATION/` only if
it stays meaningful after the work it describes is done.

Seen live: a ledger epic's description asserted "the IMPLEMENTATION DOES NOT
EXIST YET" and had to be corrected after the implementation landed under that
very epic. The same sentence in a ratified spec would have had no correcting
event at all — nothing forces a re-read of a clause that quietly went stale.

**The reviewer's move:** for each added sentence, ask "is this still true one
second after the accept?" If not, it is a proposal-body remark, not spec text.

## 2. Prefer positive assertions about sibling-owned surfaces

**A claim about what a sibling repo does NOT have is owned by that sibling and
will go stale without notice.**

Negative cross-repo claims — "the console has no merge-evidence check", "git-jsonl
ships no dispatcher" — are true when written and silently become false the moment
the sibling adds the thing. Nothing in the owning repo knows a foreign spec
asserted its absence, so no gate fires and no reviewer is prompted. The claim rots
in place, and the next reader treats a stale absence as a live contract.

Prefer asserting what IS true of the surface you own, and state the cross-repo
relationship as a dependency or a reference rather than as a claim about the
sibling's internals. When a negative claim is genuinely load-bearing, anchor it:
cite the sibling repo, the file, and the commit or version at which the absence
was observed, so a future reader can tell a still-true absence from a rotted one.

Seen live: the whole `bd-gj-rb3` disposition turned on the two "Full autonomous
modes" being *different surfaces sharing a name* — a Dispatcher drain mode in one
repo, a per-skill consent flag in another. Reasoning about a sibling's surface
from its NAME rather than its content produced a category error that made both
originally-offered options rest on a false premise.

**The reviewer's move:** for every sentence describing another repo, ask "who
would notice if this became false?" If the answer is nobody, require an anchor or
require it rewritten as a positive claim about the owning surface.

## 3. Clause lockstep at revise

**A clause that counts, enumerates, or cross-references other clauses MUST be
re-derived whenever the set it describes changes.**

Specs accumulate summary statements over enumerations: "the twenty keys below",
"each of the three phases", "both valves". These are duplicated state — the count
lives in two places — and a proposal that adds or removes a member updates the
enumeration while leaving the summary untouched. The result is a spec that
contradicts itself in the same section, and neither half looks wrong in isolation.

This is the same failure mode as any hand-maintained projection over a source it
has no mechanical link to; the fleet discipline elsewhere says to derive rather
than hardcode, and the same reasoning applies to prose.

Seen live: removing `decided_by` during the v034 autonomous-mode retirement left
the schema preamble asserting **"twenty keys"** over an enumeration of
**nineteen**, plus a dangling mention of the removed key. It was NOT in the
change's own edit map — the mandatory drift sweep found it, and the count was
then verified by explicit enumeration (14 + `rank` + 4 = 19). That is the
argument for sweeping BEFORE declaring a change done, and for treating counts as
derived values that must be re-counted rather than assumed.

**The reviewer's move:** grep the touched files for number words, "each", "both",
"all N", and anchor references near the changed enumeration, and re-count by hand
against the post-change set. Do not trust the proposal's own edit map to have
listed them — by construction it lists what the author noticed.

## Why these three sit together

All three are **latent** defects: the proposal is accurate when written, passes
every fidelity check, and ratifies cleanly. The damage appears later, to a reader
who has no signal that the text ever changed meaning. That is what distinguishes
them from the five criteria in `AGENTS.md`, which catch a proposal that is wrong
at the moment of review — something a careful reader can see.

A reviewer who checks only the five will pass all three of these every time.
