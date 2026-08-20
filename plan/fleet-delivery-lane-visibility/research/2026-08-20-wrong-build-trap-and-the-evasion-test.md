# The wrong-build trap, and the test that separates a workaround from evasion

Two findings that came out of authoring this plan and are worth more
than the plan itself. Neither is a requirement carrier.

**Both have been LANDED in core's `.ai/` tree; this note is the working
record, not the home.** The core `livespec-foreman` seat argued the
placement and was right: a research note under a plan is found by a
future reader *of that plan*, which is the wrong door for guidance whose
whole point is to reach someone who has never heard of the plan and is
about to grep a plugin cache. Per `SPECIFICATION/contracts.md` §"Fleet
agent-instruction core", durable agent guidance lives in `AGENTS.md` and
sibling `.ai/<topic>.md` files, loaded progressively at the moment the
topic is worked.

- Finding 1 → `.ai/verifying-against-the-right-source.md` instance 35.
- Finding 2 → `.ai/ci-gate-discipline.md` §"Restructuring work to get
  past a gate".
- Both summarised in the `AGENTS.md` progressive-load index, whose
  entries for these two files enumerate their contents and so must move
  in lockstep with them.

No work-item is needed in any tenant; do not file one.

Jointly derived with the core `livespec-foreman` seat on 2026-08-20;
each claim below was executed or hashed by at least two seats
independently.

## Finding 1 — reading the wrong build is the DEFAULT, not the accident

Proposed for `.ai/verifying-against-the-right-source.md`.

While characterising `github_rate_limit_guard`, this seat read a real
hook file that was not the running one and generalised from it. The
anecdote ("I took the first result") understates the hazard badly. The
base rate, measured by hashing every copy on the host:

| Variant | Copies | Status |
|---|---|---|
| `bcc352abbc4b196b049226b3e8a9c512` | 7 | stale |
| `c52db7ef2b2686b4e4916b4b68eb57cd` | 5 | stale |
| `db57c8eb7fb356ea86bee87c346bc42b` | 3 | **RUNNING** |

Fifteen copies, three distinct variants, and the running one is **3 of
15** — so a blind pick is **wrong 80% of the time**. Confirmed
independently: the running build `ac4c58bf5086` hashes to `db57c8…`, and
the core seat verified that the marketplace copy and build `263cd4f50ce5`
are byte-identical to it. That seat quoted the correct code by luck and
only established it was correct because this seat's error prompted the
check.

**What makes it a good entry is that every observation stays consistent.**
The wrong build is real code: it parses, it behaves plausibly, and its
predictions matched every denial this session had actually observed. The
error surfaced only when a second seat quoted different source, and even
then it took hashing to settle which was live.

### A correction to the joint account, and it sharpens the entry

The core seat proposed that the traversal itself steers you wrong —
*"both `find` and `ls` order semver before hashes, so the default
traversal actively steers you to the oldest."* **That is not what
happens, and this seat's own evidence disproves it.** `find` does not
sort at all; it yields directory-entry order. Run earlier in this
session, `find … | head -1` returned the stale `53a7d5b097d4`. Run an
hour later, the identical command returned the marketplace copy — which
is the *running* variant.

The set had changed underneath it: `263cd4f50ce5` appeared when
`livespec-driver-claude` cut the release described in Correction 1 of the
sibling note.

So the hazard is worse than a biased ordering, and simpler:

> `find | head -1` is not a biased sample. It is an **unstable** one.
> The same command returns a different answer before and after any
> plugin update, so you cannot reproduce even your own wrong answer, and
> a colleague running your exact command may silently get a different
> file.

A biased traversal would at least be learnable. An unstable one defeats
the usual remedy of "run it again and see".

### The cheap discriminator

The tree cannot tell you which build is live, but two commands settle it:
hash the candidate against the build named in the session's own startup
output, or confirm every candidate agrees. That converts archaeology
into evidence. Where a session prints the loaded build identifier, that
line is the source of truth and was available the whole time.

## Finding 2 — the test separating an honest workaround from evasion

Proposed for `.ai/ci-gate-discipline.md`, beside the carrier argument for
the guard.

This plan already records one genuine violation: a looped GitHub read was
moved into a script file to change what the guard saw, which
`needs-attention-internal/SKILL.md` names as evasion. The core seat then
did something that *looks* identical — put a probe in a file and ran it —
and was right to. The two must be distinguishable, or the honest case
becomes a precedent for the dishonest one.

**The distinguishing question is not "did you move it into a file". It
is: does the thing you moved perform what the gate exists to prevent?**

| | What moved | Performs the governed behaviour? | Verdict |
|---|---|---|---|
| This seat's sweep | A loop over 14 per-repo GitHub reads | **Yes** — that is exactly a looped read | Evasion |
| The core seat's probe | A local regex analysis, zero network calls | **No** — cannot consume one unit of budget | False positive |

The probe imports the hook module and runs its patterns against fixture
strings. It cannot consume rate-limit budget under any circumstance. It
was denied because **its fixture strings contain the tokens** — a fourth
live reproduction, and strictly stronger than the three in the sibling
note, because those at least accompanied a real GitHub call. This one
accompanies nothing. **The guard denied a local, offline analysis of
itself.**

Writing the test down matters because a gate this false-positive-prone
will keep generating honest workarounds, and without the test the honest
and the evasive are visually identical — a later operator can cite the
legitimate one to justify the other. The rule:

> Relocating work to change what a gate sees is evasion when the
> relocated work still performs the governed behaviour, and a
> false-positive workaround when it does not. Splitting a loop across
> tool calls so the matcher cannot see it is the first. Running an
> offline analysis whose text merely resembles the pattern is the
> second. State which one you are doing, and why, at the moment you do
> it.

The plan's own fleet sweep is the worked example of the first, and it is
recorded rather than hidden precisely so the boundary has a real case on
both sides.

## The complete attribution table, executed by two seats

The five rows this seat measured, plus the sixth the core seat added as
the control for its own claim. All six reproduce against the running
build.

| # | Case | Denied | `gh` read? | Fired via |
|---|---|---|---|---|
| 1 | Prose: alternation after a pipe | yes | yes | separator |
| 2 | `gh` read piped into multi-line Python | yes | yes | line-start |
| 3 | Heredoc with a real shell loop | yes | yes | line-start |
| 4 | Bare cached `gh api`, no loop token | no | yes | no loop match |
| 5 | Prose, loop word only mid-line | no | yes | no loop match |
| 6 | Two shell loops, **no** `gh` call | no | no | line-start |

Rows 5 and 6 are the two controls, and **neither seat ran its own**. Row
5 disconfirms this seat's "matches anywhere" claim; row 6 disconfirms the
core seat's implicit assumption that compounding mattered, showing the
`gh` read is the discriminator. Each control exists only because the
other seat pushed back.

That is the transferable method note: **when two agents converge on a
mechanism, the missing evidence is usually the control that would
disconfirm the shared assumption**, and neither is motivated to look for
it. It is the same failure `.ai/spec-proposal-review.md` records as
independent reviewers sharing a flawed instrument — two agreeing verdicts
counted as corroboration when they are one verdict counted twice.
