---
topic: plan-thread-tombstone-ban
author: claude-opus-5
created_at: 2026-08-04T13:34:20Z
---

## Proposal: Archival MUST be total — no residue may remain at a plan thread's live path

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

"Archive on epic close" already binds a plan thread's lifecycle to its epic: `plan/<topic>/` is active if and only if its epic is open. It does not say what an archival is permitted to LEAVE BEHIND, and that silence has a cost, because the natural reading of "nothing is lost" is that leaving a small forwarding note at the old path is a kindness. It is not. This proposal states that archival MUST be total, states it as a STATE invariant so it also settles retired-slug reuse, and names the two sanctioned dispositions for a thread that would close with something unresolved.

### Motivation

The guidance is inherited by every adopter, so a gap here is a gap everywhere. Two live instances were measured in `livespec-overseer` on 2026-08-04: an archived thread was RESTARTED 1h02m after its archive merged, and a second was RESTARTED 4h19m after its archive merged and nudged again 14h10m after it was finished. In both cases the operator had every reason to believe the thread was gone.

The mechanism is worth stating because it is counter-intuitive. A plan thread IS a directory in this guidance's own terms, so consumers discover threads and test archival at DIRECTORY granularity. Residue that keeps the live directory in existence therefore does not merely look untidy — it makes an archived thread indistinguishable from a live one, so whatever bookkeeping a consumer keeps for that thread is never reclaimed, and the thread remains eligible for whatever a live thread is eligible for.

It also does not stay inert in practice. One measured stub accumulated live routing instructions, a section of loose ends that two sessions independently re-did, and a self-correcting count — a retired thread doing plan work, which is precisely what a live thread or a work-item exists for.

**Why this states a STATE invariant and not only a rule about the archival event.** The mechanical backstop realized for this ban fails on any topic present at BOTH `plan/<topic>/` and `plan/archive/<topic>/`, unconditionally — a directory-name intersection, fail-closed, no opt-in lever, no content read. It cannot distinguish a residual stub from a NEW thread that reuses a retired topic's slug while the old archive remains. An event-only rule would PERMIT that reuse — a directory created later is not something that "remains" after an archival — while "nothing is lost" simultaneously REQUIRES the old archive to stay, so the adopter is handed a permanently red gate whose only escapes are deleting retained history or renaming the new thread, neither of them sanctioned. Core must therefore state the invariant it actually expects to hold, and say plainly that a retired slug is not reused while its archive remains. The alternative — narrowing the backstop — is not available: distinguishing a stub from a reuse structurally is impossible without content sniffing, which is evadable by rewording and false-positives on any document that quotes the banned phrase. Slug reuse is independently broken by the layout in any case, since the reused slug's own next archival collides with the occupied archive slot.

The rule this replaces is the one people actually reach for when a thread is finished but something is unresolved. That case is real and needs an answer, so the clause supplies two dispositions rather than leaving a vacuum a stub will fill.

This stays guidance in the non-functional tree, not a doctor invariant: core states the rule, and mechanical enforcement is realized separately, consistent with the existing sentence that this section's backstops are conformance concerns realized outside core.

### Proposed Changes

In `non-functional-requirements.md` §"Planning Lane guidance", extend "Archive on epic close" with the blockquoted text below. That text is the clause verbatim (quote markers stripped when landed); nothing else in this proposal is to be landed.

> Archival MUST be TOTAL. Whoever archives a plan thread relocates the WHOLE
> directory, and NOTHING remains at `plan/<topic>/` — no stub, no terminal
> marker, no forwarding note, no tracked or untracked residue of any kind, and
> not the directory itself, even empty.
>
> This is a STATE invariant, not only a rule about the moment of archival: in
> no committed tree, from this clause's ratification forward, may the same
> topic exist at both `plan/<topic>/` and `plan/archive/<topic>/`. A retired
> topic's slug is consequently NOT reused for a new thread while its archive
> remains — choose a new slug; or, if the new work genuinely continues the old
> thread, REOPEN ITS EPIC, which unarchives the thread by moving it back.
> Moving an archived thread back WITHOUT reopening its epic is forbidden: it
> produces an active `plan/<topic>/` whose epic is closed, contradicting the
> if-and-only-if binding above.
>
> A plan thread IS a directory, so consumers discover threads and test archival
> at directory granularity; residue that keeps the live directory in existence
> makes a finished thread read as ACTIVE, whatever bookkeeping a consumer keeps
> for it is never reclaimed, and it stays eligible for whatever a live thread
> is eligible for.
>
> When a plan thread would close with anything unresolved, exactly ONE of two
> dispositions is sanctioned. Either the thread is LEFT UN-ARCHIVED — its epic
> staying OPEN, so the lifecycle binding above continues to hold — until its
> blockers are resolved; or ALL of its blockers are TRANSFERRED to a different
> or new NON-ARCHIVED plan thread and/or work-item first, after which the
> thread is archived whole. Archiving it and leaving a note explaining what is
> left is not a third option.
>
> None of this narrows what is already sanctioned beside it. Reopening an epic
> still unarchives its thread by moving the directory BACK, which leaves
> nothing in the archive and is therefore not residue; nothing is still lost,
> since an archived thread remains under `plan/archive/` and in git history;
> and deliberately relocating a research file to a living home in `docs/` or
> `.ai/` remains the sanctioned way to keep a document alive after its thread
> closes — that is a move to a living home, not residue left at the live path.

The clause adds no new `## ` heading and renames none.
