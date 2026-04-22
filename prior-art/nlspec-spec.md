<!-- Upstream permalink: https://github.com/TG-Techie/NLSpec-Spec/blob/ed7a531884c456787254d0450d450664e296b75b/nlspec-spec.md -->
<!-- Preserved verbatim for manual diffing against `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md` (our adapted version). -->

# What an NLSpec Is

A grounding document for agents that read, write, implement, and evaluate natural language specifications.

## Version

0.2.2

---

## The Nature of the Artifact

An NLSpec is a **prescriptive, generative document written in natural language that fully determines the construction of a software system**. It sits between human intent and working code. It is the authoritative source of truth from which implementation is derived — not a description of something that already exists, not a proposal for discussion, not a guide for users. It is the thing the code must satisfy.

The relationship is directional and non-negotiable:

**Intent → NLSpec → Implementation**

Intent is what someone wants. It's rough, directional, incomplete. "I need a unified LLM client." "Build me a pipeline runner that uses DOT graphs." Intent contains the *why* and broad *what*, but leaves *how* and *precisely what* unresolved.

Implementation is code. It's maximally specific, executable, testable. It contains every decision, including ones the spec author never thought about (buffer sizes, import ordering, variable names).

The NLSpec occupies the space between. Its job is to resolve every decision that matters for correctness and interoperability while leaving every decision that doesn't matter to the implementer. This is a hard, deliberate line to draw, and drawing it well is what separates a good spec from a bad one.

An NLSpec is not a fuzzy artifact. The word "natural language" might suggest informality. It does not. The language is natural; the precision is engineering-grade. When a spec says "the adapter must inject `cache_control` breakpoints automatically for agentic workloads," that sentence has the same binding force as a type signature. It is a requirement. The implementation either does it or violates the spec.


## Why NLSpecs Work When They Work

An NLSpec enables faithful implementation — by a human or an agent — when it has five properties. These are not stylistic preferences. They are structural requirements. Remove any one and the spec fails at its job.

### 1. Behavioral Completeness

Every externally observable behavior of the system is specified. Not every internal implementation detail — every *behavior*. The distinction matters.

A spec that says "the Client routes requests to the correct provider adapter based on the `provider` field" is behaviorally complete for routing. It doesn't say whether routing uses a hash map, a switch statement, or a linear scan. It doesn't need to. The behavior — correct dispatch — is fully determined. The mechanism is not, and that's fine, because the mechanism doesn't affect callers.

A spec that says "handle errors appropriately" is behaviorally incomplete. It forces the implementer to make judgment calls about what "appropriate" means, and different implementers will make different calls, producing implementations that are mutually incompatible. That's a spec failure.

Behavioral completeness means: **if two competent implementers independently build from this spec without communicating, their implementations are interchangeable from the perspective of any caller.** Internal structure may differ. Observable behavior does not.

### 2. Unambiguous Interfaces

Every boundary where components meet is specified precisely. Interfaces include: function signatures, data structures, wire formats, error types, event schemas, configuration surfaces, and state contracts.

This is where NLSpecs do their heaviest lifting. A spec defines a `Response` record with fields `id`, `model`, `provider`, `message`, `finish_reason`, `usage`, `raw`, `warnings`, `rate_limit`. Each field has a type. Each type is defined elsewhere in the spec. The relationships between them are explicit. An implementer reading this can write the data structure in any language without guessing.

The same precision applies to behavioral interfaces. A spec that defines an edge selection algorithm — "Step 1: condition-matching edges. Step 2: preferred label match. Step 3: suggested next IDs. Step 4: highest weight. Step 5: lexical tiebreak" — has eliminated all ambiguity about what the engine does at a routing decision point. The algorithm is deterministic. Two implementations will select the same edge given the same inputs.

### 3. Explicit Defaults and Boundaries

Every configurable value has a default. Every range has bounds. Every optional parameter has documented behavior when omitted.

This sounds obvious. In practice, it's where most specs fall apart. A spec that introduces a `timeout` parameter without specifying the default, the maximum, and what happens when the timeout fires has created three implementation-divergence points. A good NLSpec closes all three: "default 10 seconds, maximum 10 minutes, on timeout: SIGTERM to process group, wait 2 seconds, SIGKILL, return partial output with timeout message."

Defaults are not details. Defaults are the behavior most users experience. Leaving them unspecified means leaving the most common case to the implementer's imagination.

### 4. Mapping Tables for Translation

When a system interacts with multiple external systems that model the same concept differently, the spec provides explicit translation tables.

A unified LLM client talks to OpenAI, Anthropic, and Gemini. Each has a different name for "the model stopped generating." OpenAI says `stop`. Anthropic says `end_turn`. Gemini says `STOP`. The spec doesn't say "map these appropriately." It provides a table: OpenAI `stop` → unified `stop`. Anthropic `end_turn` → unified `stop`. Gemini `STOP` → unified `stop`. Row by row, exhaustively.

This matters because translation is where subtle bugs hide. An implementer who doesn't know that Gemini has no dedicated "tool_calls" finish reason will fail to detect tool calls in Gemini responses. The spec prevents this by specifying: "Gemini does not have a dedicated 'tool_calls' finish reason. The adapter infers it from the presence of `functionCall` parts in the response." That sentence eliminates an entire class of bugs.

### 5. Testable Acceptance Criteria

The spec includes a "Definition of Done" — a concrete, checkable list of properties the implementation must satisfy. This is not a test plan (which defines *how* to test). It's a contract: *what must be true* when the implementation is correct.

Good acceptance criteria are binary. "Simple text generation works across all providers" is checkable. "The system handles errors well" is not. The cross-provider parity matrix — a grid of test cases × providers where every cell must pass — is the gold standard. It makes completeness visible and gaps impossible to ignore.

Acceptance criteria serve a second purpose: they bound the scope. If something isn't in the Definition of Done, it's not required. An implementer who builds everything in the checklist and nothing more has done the job. This protects against scope creep and gold-plating.


## What an NLSpec Is Not

Several artifacts look like NLSpecs. They share surface features — prose, technical content, descriptions of systems. They are not the same thing. The distinctions are functional, not stylistic.

**A README** describes something that exists. An NLSpec describes something that should be built. The arrow of authority is reversed: a README is derived from code; code is derived from an NLSpec. When code and README conflict, you update the README. When code and NLSpec conflict, you update the code.

**A design document** proposes an approach for evaluation. It says "here's how we could build this; let's discuss." An NLSpec says "here's how this will be built; go build it." A design doc invites disagreement before commitment. An NLSpec is the result of that disagreement being resolved. Shipping a design doc to an implementer produces negotiation. Shipping an NLSpec produces code.

**An architecture decision record (ADR)** captures *why* a decision was made, after the decision is made. An NLSpec captures *what* was decided and *how it behaves*. ADRs are retrospective. NLSpecs are prospective. A good NLSpec may include rationale (the Attractor specs have "Design Decision Rationale" appendices), but the rationale serves understanding, not authority. The spec is authoritative whether or not you agree with the rationale.

**API reference documentation** describes the surface of an existing system for consumers. An NLSpec describes the surface *and internals* of a system that doesn't exist yet, for builders. API docs say "here's what you can call and what it returns." NLSpecs say that, plus "here's the algorithm inside, here's the error hierarchy, here's the retry policy, here's the provider translation table, here's what happens at every edge case."

**A test plan** defines how to verify a system. An NLSpec defines what the system must do. A test plan is derived from a spec; a spec is not derived from a test plan. The Definition of Done in a spec looks like a test plan but serves a different purpose: it's an acceptance contract, not a testing strategy. It says *what* to verify, not *how* to verify it.

**A tutorial or guide** teaches a human how to use or build something, optimizing for learning. It may omit details, simplify, reorder for pedagogy. An NLSpec optimizes for completeness and precision, not for learning. It may be hard to read linearly. That's acceptable. A spec that sacrifices precision for readability has failed at its primary job.

The critical distinction across all of these: **an NLSpec is the source of truth that generates an implementation. Every other document type is either upstream of it (intent, design docs) or downstream of it (API docs, READMEs, tutorials, test plans). Confusing the direction produces the wrong artifact.**


## What Completeness Means

An NLSpec is complete when an agent reading it has everything needed to act correctly, and nothing is left to arbitrary choice that shouldn't be.

This is not the same as specifying everything. A spec that dictates variable names, indentation, internal function decomposition, and memory allocation strategy is not more complete — it's more brittle and less useful. It has wasted precision on decisions that don't affect correctness or interoperability.

Completeness operates at three levels. These are not strictly disjoint — boundary completeness is a special case of behavioral completeness at the edges of the input space. The distinction is worth preserving because each level corresponds to a different failure mode in practice, and each tends to be overlooked for different reasons:

**Behavioral completeness.** Every observable behavior is determined. For any valid input, the spec determines the correct output (or the correct set of acceptable outputs, when nondeterminism is intentional). For any error condition, the spec determines the error type, whether it's retryable, and what the caller sees.

**Interface completeness.** Every point where two components meet is defined with enough precision that the components can be built independently and still connect correctly. Data structures have fields with types. Functions have signatures with parameter and return types. Protocols have message formats and sequencing rules.

**Boundary completeness.** Every limit, default, timeout, maximum, and edge case is specified. What happens when the context window overflows? What happens when a tool call references an unknown tool? What happens when all retry attempts are exhausted? A complete spec has answers.

The judgment call is always: **does this decision affect correctness or interoperability?** If yes, specify it. If no, leave it to the implementer. When in doubt, specify it. Over-specification through additional requirements is less harmful than under-specification, because over-specification produces implementations that are merely constrained, while under-specification produces implementations that are incompatible.

### The Precision-Completeness Distinction

The interchangeability test — would two independent implementations be interchangeable to a caller? — measures **precision**. It asks whether the spec eliminates ambiguity at each point it addresses. But a spec can be perfectly precise at every point it addresses and still be incomplete. Precision means the spec says things clearly. Completeness means the spec says enough things.

A spec that precisely defines request routing, response normalization, and error hierarchy — but never mentions retry behavior — is precise and incomplete. Two implementations would agree on everything the spec covers and diverge on everything it doesn't. The spec eliminated ambiguity within its scope but left scope gaps.

**The recreatability test.** If the implementation were destroyed and only the specification remained, could a competent implementer faithfully recreate the system? This is a completeness proof. It doesn't ask whether the spec is clear (precision). It asks whether the spec is *sufficient* — whether it contains, in itself, everything needed to generate a faithful implementation.

The recreatability test does not require the spec to mention everything. It requires that anything the spec *doesn't* mention falls cleanly into the category of intentional ambiguity — genuine implementation choices where any reasonable decision is acceptable. If a competent implementer, working from the spec alone, would reach a point where they cannot proceed without information the spec doesn't contain, and the missing information isn't a free choice — that's a completeness defect.

This is what makes the NLSpec's claim to be a "prescriptive, generative document that fully determines the construction of a software system" falsifiable. The document asserts that the spec fully determines construction. The recreatability test is how you check that assertion. Without it, "fully determines" is a claim. With it, it's a testable property.

The two tests are complementary. Precision without completeness produces a spec that is clear about what it covers but silent on critical behaviors. Completeness without precision produces a spec that covers everything but leaves room for incompatible interpretations. A well-formed spec passes both: it addresses everything that isn't a free choice (complete), and it addresses each thing without ambiguity (precise).


## Conceptual Fidelity

A spec's data models should reflect the domain's inherent information structure — the distinctions, relationships, and variants that exist in the problem itself, independent of how anyone chooses to represent them. When a spec achieves this, it has conceptual fidelity: the reader absorbs the domain by reading the spec, rather than having to reconstruct the domain from an encoding of it.

Conceptual fidelity matters because a spec that models its encoding rather than its domain has drifted from its own subject matter. The spec is *about* the domain. When its models describe how to transcribe the domain's information rather than what that information *is*, the reader must first decode the representation to reach the concepts — which is exactly the kind of burden a spec should not impose.

Consider a response that is either a success with a body or an error with a code. The domain has two mutually exclusive cases, each carrying different information. A spec with conceptual fidelity models this as a sum type: two variants, each with only the fields that case requires. The reader sees the domain directly.

A spec that instead models this as a single record with optional fields for both the success body and the error code — plus a prose invariant explaining that exactly one must be present — has modeled the encoding, not the domain. The flat record with its invariant is a way to *transcribe* the two-case structure into a representation, but the representation is not the concept. The reader must mentally reconstruct the domain's actual shape from the encoding, and the prose invariant exists only to patch the gap between the model and the domain it claims to describe.

This is not a rule about preferring sum types. It is an observation about what happens when a spec models inherent information directly: the modeling constructs that fit the domain — sum types for mutually exclusive cases, product types for co-occurring fields, sequences for ordered collections — follow from the domain's own structure. The spec author's job is to identify what the information *is* and model that, not to choose a representation and then constrain it with prose.

Unenforced invariants — constraints stated in prose rather than captured by the spec's model structure — are occasionally justified. They are a rarer analogue of intentional ambiguity: sometimes the constraint spans a boundary that no single type can capture or experience from prior implementations of the spec inform the decision to express a model as such. When an unenforced invariant is genuinely necessary, it should be marked explicitly and accompanied by the intent and rationale so the understanding is conveyed to readers of the spec.

A first test for conceptual fidelity: **does the spec's model have the same shape as the domain's information, or does the reader have to reshape one to see the other?** When the conceptual shapes match, the spec is transparent to the domain. When they don't, the spec has interposed its own encoding between the reader and the inherent subject matter of the underlying problem or concept.


## Spec Economy

Spec economy is the discipline of minimizing the context burden on the reader while preserving full precision and completeness. It is not about short specs. It is about specs where every sentence does work that no other sentence does.

Where conceptual fidelity asks whether the spec models the right thing, economy asks whether the spec *says* it without waste or structural self-harm. A complete but uneconomical spec is harder to verify, harder to maintain, and more likely to develop internal contradictions as it evolves.

**Inputs and outputs are the contract.** Both must be explicit. Omitting outputs because they're "derivable" is false economy — it shifts the derivation burden onto the reader. But explicit does not mean verbose: `Output = Input & { pvFuture: USD, totalPV: USD }` is both explicit and economical.

**The economy test.** For each sentence, ask: "would removing this sentence cause two independent implementers to produce different outputs?" If yes, the sentence carries load. If no, it is either redundant with another sentence or specifying implementation mechanism within the intentional ambiguity space — either way, cut it. This is a sentence-level application of the two-implementer test. The spec-level test asks whether the whole document produces interchangeable implementations. The economy test asks whether each individual sentence contributes to that outcome.

Economy interacts with the over-specification principle. This document advises: when in doubt, specify it. Economy adds: specify it *once*. Over-specification through redundancy is not safer — it creates drift risk, and drift produces the self-contradictions that are the most severe class of spec failure.

**Redundancy creates drift.** When the same fact is stated in two places — a formula defines the output and a separate section lists the output fields — there are now two sources of truth. When they drift apart, the spec has a self-contradiction, which this document identifies as always an error, never intentional. The fix is the define-once principle: each concept is introduced exactly once, in the most natural location, and referenced by name everywhere else. This eliminates drift by construction.

**Non-local context dependencies burden the reader.** When understanding one section requires remembering a convention from an earlier section, a default from a third, and an exception from an appendix, the reader is carrying context that the spec's structure should be managing. A well-economized spec either states the relevant convention inline where it's used, or structures itself so that sections are self-contained with explicit references to shared definitions.

**Implementation decomposition is not domain structure.** When a spec mirrors the internal factoring of code — five subsections for five helper functions — it has imported structure from the implementation's intentional ambiguity space into the spec. The spec describes the calculation. How the calculation is decomposed into functions is an implementation choice.


## Intentional vs. Accidental Ambiguity

Every NLSpec contains ambiguity. Some is intentional and valuable. Some is accidental and destructive. Distinguishing the two is a core skill for anyone working with specs.

### Intentional Ambiguity

Intentional ambiguity is **freedom granted to the implementer in areas where the spec author has determined that any reasonable choice is acceptable.** It is characterized by:

- **The spec could have specified this but chose not to.** The absence of a requirement is a deliberate design decision. "The library does not invent its own model namespace" — this is the spec explicitly choosing not to specify a model naming convention, and saying why.
- **Different implementations making different choices here remain interoperable.** If one implementation uses a hash map for provider routing and another uses a match statement, no caller can tell the difference. The ambiguity is below the abstraction boundary.
- **The spec often signals it explicitly.** Phrases like "implementations may," "the mechanism is not specified," "any combination of them," or "this is an implementation detail" are markers of intentional ambiguity.
- **Boundary clarifications sharpen the edges of the spec's scope.** A spec may explicitly exclude adjacent functionality to prevent misreading — "this spec does not cover prompt construction or conversation memory" — not because those are unimportant, but because their absence from this spec is a deliberate boundary, not an accidental gap. Such exclusions are a form of intentional ambiguity: the spec is intentionally silent on those areas and is naming that silence so it isn't mistaken for an omission.

Examples: choice of programming language, internal data structure selection, HTTP client library, concurrency primitives, file system layout for source code, error message wording (as long as the error type is correct).

### Accidental Ambiguity

Accidental ambiguity is **a gap in the spec where the author intended to specify behavior but failed to, or where the specified behavior admits multiple incompatible interpretations.** It is characterized by:

- **Different implementations making different choices here produce incompatible or incorrect behavior.** If one implementation retries on timeout and another doesn't, callers experience different reliability characteristics from the same spec.
- **The spec appears to assume something it never states.** "Process the messages in order" — does "in order" mean insertion order, chronological order, or priority order? The author probably meant one of these but didn't say which.
- **An implementer must guess to proceed.** Intentional ambiguity lets the implementer choose freely. Accidental ambiguity forces the implementer to guess what the author meant. The difference is felt in the implementer's experience: freedom feels like freedom; guessing feels like anxiety.

### How to Tell the Difference

The test is: **would two implementations that resolve this ambiguity differently be interchangeable to a caller?**

If yes, the ambiguity is intentional or at least harmless. If no, the ambiguity is accidental and the spec needs to be tightened.

There is a gray zone. A spec might leave ambiguous whether an error message says "File not found: /path/to/file" or "No such file: /path/to/file." Strictly, these are different outputs. Practically, no caller depends on error message text. The ambiguity is harmless. Judgment is required; the test is a guide, not a theorem.


## The Structure of NLSpecs in Practice

NLSpecs share structural patterns not because someone prescribed a template, but because these patterns solve recurring problems in specification writing.

**Progressive disclosure of detail.** Specs open with an overview (what is this system, what problem does it solve, what are the design principles) and progressively deepen into architecture, data models, algorithms, and edge cases. This isn't pedagogical ordering — it's dependency ordering. You can't understand the edge selection algorithm until you understand what nodes and edges are. You can't understand what nodes and edges are until you understand what a pipeline is.

**Pseudocode for algorithms, prose for contracts.** When behavior is algorithmic (a loop, a selection process, a retry policy), pseudocode specifies it precisely. When behavior is contractual (an interface, a data structure, an error hierarchy), prose with structured definitions specifies it. The choice of representation matches the nature of the thing being specified.

**Tables for mappings.** When the spec must define how concept X in system A corresponds to concept Y in system B, a table is the right representation. Tables are exhaustive, scannable, and make gaps visible. Prose descriptions of mappings hide gaps.

**Appendices for rationale and reference.** The main body of the spec says *what*. Appendices explain *why* (design decision rationale) and provide reference material (complete attribute tables, format specifications, examples). The main body is authoritative. Appendices are supportive.

**A Definition of Done.** The spec ends with a concrete, checkable list of acceptance criteria. This list is the operational definition of "this implementation is correct." It transforms the spec from a document you interpret into a contract you satisfy.


## How NLSpecs Relate to Each Other

Complex systems require multiple NLSpecs that reference each other. The coding agent loop spec depends on the unified LLM client spec. The pipeline runner spec can use either as a backend. These relationships have rules:

**Dependency is explicit.** A spec that depends on another says so directly: "This spec layers on top of the Unified LLM Client Specification, which handles all LLM communication." The dependency is named, the interface boundary is clear, and the importing spec states exactly which types and functions it uses from the dependency.

**Specs don't reach into each other's internals.** The coding agent loop spec uses `Client.complete()` and `Client.stream()` from the LLM SDK. It does not reach into the SDK's provider adapters, SSE parsing, or retry logic. The boundary between specs is an API, not a gentleman's agreement.

**Composition is through interfaces, not inheritance.** The pipeline runner doesn't extend the coding agent — it defines a `CodergenBackend` interface and says "implement this however you want; the pipeline doesn't care." This is the same principle as intentional ambiguity applied at the system level: the spec determines the contract, not the mechanism.


## Specs in Iterative Development

The `Intent → NLSpec → Implementation` chain is not a single pass. In practice — particularly in conversational and agent-assisted development — intent is revealed progressively. A user may not know what they want until they see what they don't want. Requirements emerge, shift, and sharpen as work proceeds.

This does not weaken the spec-first principle. It changes the cadence.

In iterative development, implementation can serve as an epistemological tool — you build something small to discover whether a concept is sound, whether an interface feels right, whether an edge case matters. This is not implementation-of-spec. It is exploration. It lives in the intent phase of the `Intent → NLSpec → Implementation` chain, even though it looks like code. Its purpose is to surface insight, not to satisfy requirements.

When exploration reveals something real — a requirement, a constraint, a behavioral expectation — that insight enters the spec. But it enters **as if the exploration never happened.** The spec is a vacuum artifact. It is written in a world where only intent and domain knowledge exist, not prototypes. The spec does not say "based on our prototype, we discovered X." It says "X." It absorbs the insight and presents it as a freestanding requirement, authoritative on its own terms.

The discipline is: **at no point should the implementation encode a behavioral requirement that the spec does not reflect.** When exploration produces insight, the spec absorbs it before or simultaneously with the implementation encoding it. The spec leads or keeps pace. It never trails. And when the spec absorbs a new requirement, it must do so in a way that preserves self-consistency — the spec at every point in time is a coherent, complete document, not a patchwork of incremental additions.

This connects to the recreatability test. If the spec has successfully absorbed every insight from iterative exploration, then the exploration artifacts (prototypes, experiments, intermediate code) can be discarded. The spec alone is sufficient to regenerate the system. If it can't — if there's knowledge in the prototype that never made it into the spec — the spec has a completeness defect, regardless of how that knowledge was originally discovered.

A spec in an iterative context is a living document, but "living" does not mean "loose." It means the spec accretes deliberately as requirements are discovered, while remaining internally coherent at every revision. Early versions may specify only core behaviors. As edge cases surface, the spec grows to cover them. This is healthy — provided each addition is deliberate and the spec remains self-consistent.

Self-consistency is non-negotiable. A spec that has been updated piecemeal can develop internal contradictions. At any point in time, the spec must be internally coherent. If an update to one section contradicts another, the contradiction must be resolved in the spec before implementation proceeds.

The spec captures the current state of decisions, not the history of how decisions were made. When a requirement changes — "actually, retry three times, not five" — the spec is updated to say three. Rationale for changes, if worth preserving, belongs in commit messages, ADRs, or appendix notes — not in the spec body. The spec is always a present-tense document.


---

## Appendix A: When Implementing from an NLSpec

When you are an agent (or human) building code from a spec, these are the judgment calls that matter:

**The spec is not a suggestion.** Every requirement in the spec is a requirement. If the spec says "the adapter must generate synthetic unique IDs," you generate synthetic unique IDs. You don't decide it's unnecessary. You don't skip it because your language makes it awkward. If you believe the spec is wrong, you raise the issue — you don't silently deviate.

**Intentional ambiguity is your design space.** Where the spec doesn't specify, you choose. Choose well: prefer simplicity, prefer the idiomatic approach for your language, prefer the choice that makes future spec compliance easier. But do choose — don't treat every unspecified detail as a question to ask.

**The Definition of Done is your completion criterion.** When every item in the checklist passes, you're done. When items remain unchecked, you're not. Resist the urge to add features the spec doesn't require, even good ones. Your job is faithful implementation, not improvement.

**When the spec is ambiguous and you can't tell if it's intentional:** apply the interchangeability test. If your choice doesn't affect callers, make the choice and move on. If it might affect callers, flag it. The phrase you want is: "The spec doesn't specify X. I chose Y because Z, but this is a point where the spec may need tightening."

**Understand the failure modes of a spec.** Not all spec problems are the same, and each kind requires different handling:

- **Ambiguity** — the spec admits multiple incompatible interpretations at a specific point. The implementer must judge which interpretation is intended, or flag it. This is the most common failure mode and is addressed by the interchangeability test above.

- **Malformation (self-contradiction)** — the spec asserts two incompatible requirements. Section A says retry three times; Section B says retry five times. This is a document-level defect. Self-contradiction in a specification is never intentional — it is always an error in the document itself. No amount of implementer judgment resolves a contradiction, because any implementation satisfies one requirement by violating the other. Only the spec author can decide which side of the contradiction reflects actual intent. When you identify a self-contradiction, flag it and request repair. Do not pick a side silently.

- **Incorrectness** — the spec is internally consistent but prescribes wrong behavior. The spec says "timeout after 60 seconds" and that's unambiguous, but the correct value for the domain is 10 seconds. This failure mode may not be detectable from within the spec itself — it requires domain knowledge external to the document. The onus of correctness is on the spec author, not the implementer. An implementer faithfully implementing an incorrect spec has done their job correctly; the spec was wrong, not the implementation.

The response to each failure mode is different. Ambiguity calls for judgment. Contradiction calls for repair. Incorrectness calls for domain authority. An operating environment (project conventions, agent instructions, team process) should provide specific protocols for what to do when each failure mode is encountered — particularly when the spec author is unavailable and the defect is blocking. That operational guidance is outside the scope of this grounding document, but its necessity should be anticipated.

**Map the spec's structure to your implementation's structure.** The spec's sections often correspond to modules, packages, or files. The spec's data models correspond to types. The spec's algorithms correspond to functions. This correspondence should be legible — someone reading the spec should be able to find the corresponding code without a treasure map.

**Provider-specific translation tables are not optional.** If the spec provides a mapping table, implement every row. Don't implement "the common ones" and plan to add others later. The table exists because every row matters; the uncommon cases are often where the subtlest bugs hide.


## Appendix B: When Authoring an NLSpec

When you are writing a spec, these are the judgment calls that matter:

**Specify behavior, not mechanism.** Say what the system does, not how it does it internally — unless the internal mechanism is load-bearing. A retry policy's backoff formula is load-bearing (it affects observable timing). A retry policy's implementation using a loop vs. recursion is not.

**When you don't care, say so.** Intentional ambiguity should be visible. "The library does not prescribe internal data structures for provider routing" is better than silence, because silence could be an accidental gap.

**When in doubt, over-specify — but specify once.** An implementer can always choose to ignore a spec detail that turns out to be unnecessary. An implementer cannot invent a spec detail that turns out to be missing. Over-specification constrains; under-specification breaks. But stating the same requirement in two places creates drift risk. Define each fact once, in the most natural location, and reference it by name elsewhere.

**Defaults are requirements.** Every configurable value needs a default. Every optional parameter needs defined behavior when omitted. "Default: 10 seconds" is a requirement as binding as any other. If you don't specify the default, you've left the most common user experience to chance.

**Tables beat prose for mappings.** When you're describing how concept X maps to concept Y across multiple systems, use a table. Tables are exhaustive by visual inspection — you can see when a row is missing. Prose descriptions of the same mapping hide gaps behind sentences.

**Include a Definition of Done.** Without it, the spec has no operational boundary. An implementer doesn't know when they're finished. A reviewer doesn't know what to check. A Definition of Done converts a document into a contract.

**Design rationale belongs in an appendix.** The main body says *what*. Rationale says *why*. Mixing them makes the spec harder to use as a reference. An implementer re-reading the spec for the third time doesn't need to re-encounter the justification for every design choice.

**Write for the implementer who disagrees with you.** The spec should be followable even by someone who thinks your design is wrong. This means the spec must be precise enough that "I would have done it differently" doesn't lead to "so I did it differently." Precision is the antidote to well-intentioned deviation.


## Appendix C: When Evaluating an NLSpec

When you are assessing whether a spec is good — whether as a reviewer, an editor, or an agent deciding whether a spec is ready to implement from — these are the judgment calls that matter:

**Apply the two-implementer test.** For every requirement, ask: if two competent implementers built this independently, would their implementations be interchangeable to a caller? If yes, the spec is sufficiently precise at that point. If no, find the ambiguity and flag it.

**Check the boundaries.** The highest-risk areas in any spec are interfaces between components, default values, error handling, and edge cases. These are where accidental ambiguity hides. Read these sections with maximum skepticism.

**Look for missing rows in mapping tables.** If a spec maps concepts across systems and a known case isn't in the table, that's a gap. If Gemini has no "tool_calls" finish reason and the finish reason mapping table doesn't account for that, the spec is incomplete.

**Verify the Definition of Done against the spec body.** Every requirement in the spec body should have a corresponding item in the Definition of Done. Requirements that aren't testable aren't enforceable. Checklist items that don't trace back to spec requirements are scope creep.

**Distinguish "hard to implement" from "ambiguous."** A requirement can be perfectly clear and extremely difficult. "Execute all tool calls concurrently, wait for all results, send all results in a single continuation request, preserve ordering, handle partial failures gracefully" — this is hard to implement correctly. It is not ambiguous. Don't flag difficulty as a spec problem.

**Assess whether intentional ambiguity is actually intentional.** When the spec is silent on something, ask: is this silence deliberate (the spec author doesn't care about this choice) or accidental (the spec author forgot)? Clues: if the surrounding area is highly specified and one detail is missing, it's probably accidental. If the spec explicitly says "this is left to the implementer" or "the mechanism is not specified," it's deliberate.

**Check temporal assumptions.** Specs that reference specific model names, API versions, or provider capabilities will go stale. Good specs handle this by providing both concrete current values (for immediate use) and the principle for updating them (so future maintainers know what to change). A spec that says "use GPT-5.2" without context is fragile. A spec that says "prefer the latest available model; at time of writing, GPT-5.2" is maintainable.
