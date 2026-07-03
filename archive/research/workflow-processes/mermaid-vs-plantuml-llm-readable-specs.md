# Mermaid vs PlantUML for LLM-readable specs — research capture

**Status:** decision MADE 2026-06-10 — the user officially adopted **Mermaid as
the standardized livespec diagram format** (with the staged migration this doc
recommends). Formalization flows through the normal propose-change → revise
lifecycle; this capture is the reference rationale.

**Date:** 2026-06-10 (retrieved).

**Source:** Claude research artifact authored by the user's research session —
<https://claude.ai/public/artifacts/6a5e1cdc-f321-4b73-a794-37bc7cf8d0d2>
(downloaded verbatim below; content is user-generated and unverified per the
hosting page's banner).

**Why this capture exists:** livespec standardized on PlantUML
(`research/workflow-processes/diagrams/*.plantuml` + rendered `.svg` pairs;
spec.md commits to a `livespec-with-diagrams` template variant worded as
"the canonical PlantUML-supporting variant"). This research evaluates whether
Mermaid is "almost as good" for LLM interpretation and evolution and concludes
the switch is justified; the decisive practical factor is GitHub-native
rendering (no source↔render pairing, no render pipeline, no drift class).

---

## TL;DR

Yes — for livespec's purpose, Mermaid is "almost as good" as PlantUML for LLM
interpretation and evolution, and in several respects better. No published
study shows PlantUML's UML-standard basis improves machine interpretation; the
evidence that exists points to training-data familiarity (which favors both
formats, with Mermaid uniquely advantaged by GitHub-native rendering) as the
dominant driver of LLM fluency. The PlantUML→SVG rendering pipeline is not
worth maintaining as a default for a generic spec tool.

The honest caveat: a true head-to-head Mermaid-vs-PlantUML LLM-accuracy
benchmark does not exist (as of June 2026). The recommendation rests on (a)
single-format benchmarks showing both formats are generated competently by
frontier models, (b) the GitHub-native rendering asymmetry, and (c) the fact
that LLM diagram errors are overwhelmingly semantic/completeness failures that
are format-independent.

Recommended path: make Mermaid the livespec default and keep PlantUML as a
per-diagram-type escape hatch for the handful of constructs Mermaid lacks
(deployment, timing, object diagrams, mind maps, rich C4/sprites). Migrate
existing `@startuml` blocks opportunistically, not in a big bang.

## Key Findings

**1. No direct head-to-head benchmark exists.** Across the 2023–2026
literature there is no controlled study that runs identical prompts through an
LLM targeting both Mermaid and PlantUML and reports a syntax-error-rate or
semantic-accuracy delta. This is a genuine evidence gap, and any confident
claim that one format is "X% better for LLMs" is unsupported. The user's
instinct to demand evidence over anecdote is correct here.

**2. Both formats are generated competently by frontier models; errors are
mostly semantic, not syntactic, and semantic errors are format-independent.**
The strongest signal is that the failure mode that matters for specs —
capturing the intended meaning — is not a function of notation:

- PlantUML-only, image→UML (Eklund & Jonsson, Mälardalen University thesis,
  18 June 2025): four multimodal LLMs (ChatGPT 4o, Claude 3.7 Sonnet, Gemini
  2.5 Pro, Llama 4 Maverick) produced syntactically valid PlantUML at high
  rates (ChatGPT 4o ~83.6%–98.1% depending on diagram type; Claude 3.7
  ~80%–98.6%), but "even the best-performing models in our study rarely
  exceeded 70% semantic accuracy."
- PlantUML-only, requirements→sequence (Ferrari, Abualhaija, Arora, arXiv
  2404.06371, Apr 2024, GPT-3.5): scored high on adherence-to-standard
  (4.54/5) and understandability (4.37/5) but weak on correctness (3.22/5,
  not significantly above the mean, p>0.05) and completeness (3.63/5). The
  authors' own conclusion: diagrams "exhibit significant issues related to
  completeness and correctness, such as missing/incorrect elements, structural
  issues, or components that deviate from what is specified."
- Mermaid-only, NL→sequence (MermaidSeqBench; Basel Shbita, Farhan Ahmed &
  Chad DeLuca, IBM Research San Jose, arXiv 2511.14967, v2 dated 25 Apr 2026;
  NeurIPS 2025 LLM-evaluation workshop): a 132-sample benchmark built via
  human-verified flows plus LLM and rule-based expansion, scored 0–1 across
  six dimensions by two LLM-as-Judge models, DeepSeek-V3 (671B) and GPT-OSS
  (120B). Syntax scores for capable models are high (Llama-3.1-8B 92.0%,
  Qwen-2.5-7B 91.3%), with the larger gaps appearing in logic, completeness,
  activation handling and error tracking — i.e., the semantic dimensions.

The pattern across both formats is identical: syntax is largely solved for
capable models; semantic fidelity is the hard part, and nothing in the data
attributes semantic quality to UML-standardness.

**3. Where the two formats sit side-by-side, PlantUML did not win on machine
interpretation.** The only paper placing Mermaid, Graphviz and PlantUML
together (Pan et al., flowchart understanding, arXiv 2412.16420, 2024) found
extraction was "comparable results for Graphviz and Mermaid, but lower for
PlantUML," attributing PlantUML's difficulty to its "complex pseudocode-like
syntax." This measures interpretation (not generation) and is not a clean
delta, but it cuts against the hypothesis that UML-standard PlantUML is
inherently easier for models to read.

**4. Training-data familiarity, not formal-standard compliance, is the
credible mechanism.** Conrardy & Cabot ("From Image to UML," arXiv 2404.11376,
2024) state directly that "the choice of the notation is important, as it
affects the quality of the output," and that "the better performance when
using the PlantUML notation seems to correlate with the popularity of the
notation… more PlantUML data being available and thus, more PlantUML data
contained in the LLMs' training data." This is the key theoretical point for
livespec: models are fluent in a DSL because they have seen lots of it, not
because it complies with the OMG UML 2.5.1 spec. Mermaid's GitHub-native
rendering (live since 14 Feb 2022 per the GitHub Blog "Include diagrams in
your Markdown files with Mermaid"; Gist support followed 28 Feb 2022) has
driven enormous public-corpus volume — every README, issue, PR and discussion
can embed it — which plausibly gives Mermaid more recent training-data
representation, not less. The mermaid-js/mermaid repo shows 88,515 stars and
9,032 forks as of 9 June 2026.

**5. The semantic-expressiveness gap is real but narrow, and mostly outside
spec-critical diagram types.** Per-type, as of 2026:

- Sequence: near-parity. PlantUML has richer built-ins (create/destroy
  lifelines, dividers, reference frames, finer activation control,
  stereotypes). Mermaid covers participants/actors, activation,
  alt/opt/loop/par, notes, autonumber, and recently added create/destroy and
  multi-directional arrows. The one materially missing Mermaid equivalent for
  specs: multi-line `note` blocks and certain `ref` frames.
- Class: near-parity for documentation use. Mermaid supports all 8 standard
  UML relationship types (inheritance, composition, aggregation, association,
  dependency, realization, link, bidirectional), visibility markers, and
  stereotypes/annotations. PlantUML edge case: attribute-to-attribute edges
  and deeper layout control.
- State: near-parity (Mermaid stateDiagram-v2 covers composite states, forks,
  concurrency).
- ER: near-parity; commonly judged to render better in Mermaid.
- Activity: PlantUML more expressive (explicit if/else/fork, swimlanes);
  Mermaid uses flowcharts.
- Component / Deployment / Timing / Object / Use-case / Mind map / JSON-YAML
  viz: PlantUML clearly ahead. Deployment, timing, object diagrams and mind
  maps have no first-class Mermaid equivalent.
- C4: PlantUML (via C4-PlantUML) and Structurizr are materially stronger;
  Mermaid's C4 support is still labelled experimental, with weaker layout and
  sprite/icon support.

For a generic spec tool, the high-frequency types (sequence, class, state,
ER, flowchart) are at parity; the gaps fall in lower-frequency
architecture/specialty types.

**6. The rendering asymmetry is the decisive practical factor — and it has
not changed.** As of June 2026, GitHub still has no native PlantUML rendering.
The long-running feature request (GitHub community Discussion #10111) remains
open with no commitment from GitHub; PlantUML's own answer is a browser
extension (which requires every reader to install it) plus a client-side
TeaVM build. Mermaid renders inline by default on GitHub, GitLab, Notion,
Obsidian and most docs platforms, plus VS Code and its forks. For a tool whose
premise is specs as version-controlled, human- AND agent-readable context that
"renders by default," this is the crux: PlantUML requires a build step (Java +
Graphviz, or a server/Kroki, or a GitHub Action that commits SVGs) that the
user must maintain, and the diagrams do not render locally without running a
process.

**7. Real-world spec/agent tooling overwhelmingly defaults to Mermaid.**
GitHub spec-kit's community diagram extension generates GitHub-renderable
Mermaid; OpenSpec's intent-driven workflows reference C4/Mermaid; ADR practice
(adr.github.io, Martin Fowler's bliki) lists both but defaults to Markdown +
Mermaid for inline rendering, reserving PlantUML/Structurizr for formal C4.
Where teams need a single model with multiple consistent views, Structurizr
DSL (which can export to both Mermaid and PlantUML) is the premium choice —
relevant if livespec ever wants model-derived views.

## Details

**On the "does UML-standard matter for LLMs" hypothesis.** The
counter-hypothesis is the better-supported one. There is no evidence that an
LLM interprets a diagram more correctly because the notation maps to OMG UML
semantics; the evidence (Conrardy & Cabot; the symmetrical syntax-vs-semantics
split across MermaidSeqBench and the PlantUML studies) indicates models
operate on learned surface patterns of the DSL plus the natural-language
labels inside it. For livespec specifically, the semantic richness that
matters is carried by (a) the node/edge labels and (b) the surrounding spec
prose — both format-agnostic. PlantUML's stricter UML vocabulary buys
precision for a human UML expert reviewer and for formal modeling tools; it
does not buy measurably better LLM comprehension.

A nuance worth flagging honestly: if the consuming LLM has more PlantUML in
its training data for a given specialty diagram type (because that type —
e.g., deployment — barely exists in Mermaid), PlantUML could be locally better
for that type purely on familiarity grounds. This reinforces the
per-diagram-type escape-hatch recommendation rather than a single global
choice.

**Token efficiency.** Mermaid is consistently the more compact
representation. Brissard, Cuppens & Zouaq (arXiv 2507.11356, accepted to the
AI4BPM Workshop at BPM 2025), evaluating 9 process-model representations over
55 process descriptions with LLaMA-3.3-70B, found verbatim that "Mermaid is
the most compact, achieving over 90% reduction in lines, tokens, words, and
characters compared to BPMN" and that "Mermaid achieves the highest overall
score across six PMo criteria." (Note: that study did not include PlantUML as
a separate arm.) Compactness matters for context-window budget when specs are
loaded as agent context — a direct livespec concern.

**Rendering-pipeline cost, concretely (if you were to stay on PlantUML).**
The minimal setups are all real but all are ongoing maintenance: a GitHub
Action (e.g., `grassedge/generate-plantuml-action`) that renders
`.puml`/fenced blocks to SVG and commits them back; a pre-commit hook
(`weikangchia/pre-commit-hooks-plantuml`) requiring a local `plantuml.jar` +
Java; mkdocs plugins (`mkdocs_puml`, `mkdocs-build-plantuml-plugin`,
`mkdocs-plantuml-local`) for docs-site rendering. Every one of these means
generated SVGs can drift from source, readers without the toolchain see raw
text locally, and the agent's "what renders" and "what's in git" diverge.
Recent PlantUML ships a Graphviz-free Java layout engine (Smetana) and a
TeaVM client-side build, which reduce but do not remove the dependency story.

**Migration reality (you already use `@startuml` blocks).** PlantUML→Mermaid
translation is "mostly mechanical for sequence diagrams and flowcharts"
(participant declarations and arrows have direct equivalents). The known
friction points: label line-breaks (`\n` vs `<br/>`), PlantUML `note` blocks
having no clean Mermaid sequence equivalent, and nested-boundary/C4 diagrams.
An LLM does this conversion well as a one-shot per file, but each output needs
a render check. (There are also off-the-shelf PlantUML→Mermaid converters, but
per-file LLM conversion is fine at livespec's scale.)

## Recommendations

**Stage 1 — Adopt Mermaid as the livespec default now.** Set the standard
convention to fenced ` ```mermaid ` blocks for the common types (sequence,
class, state, ER, flowchart/dependency, light C4 context). Rationale: renders
by default for both humans (GitHub/IDE/Notion) and agents, is the most
training-data-familiar and most token-compact format, and requires no
pipeline to maintain. This directly serves the "rich human- AND agent-readable
context that renders by default" goal.

**Stage 2 — Define a per-diagram-type escape hatch to PlantUML.** Permit
`@startuml` blocks only for types where Mermaid lacks the construct:
deployment, timing, object diagrams, use-case, mind maps, JSON/YAML
visualization, and heavy C4 with sprites. Document that these require the
rendering step. This is the highest-value hybrid: you pay the pipeline cost
only on the <10% of diagrams that need it, not globally. Practically,
livespec can encode this as a documented convention plus an optional opt-in
GitHub Action that only fires on `.puml`/`@startuml` content.

**Stage 3 — Migrate existing PlantUML opportunistically.** Convert
`@startuml` blocks to Mermaid when a spec is next touched (LLM-assisted, with
a render check), not in a big bang. Leave specialty-type diagrams as PlantUML.

**Stage 4 — If/when you need a single model with multiple consistent views,
evaluate Structurizr DSL** (exports to both Mermaid and PlantUML) rather than
hand-maintaining cross-diagram consistency. This is a later concern, not a v1
need.

**Benchmarks/thresholds that would change this recommendation:**

- If GitHub ships native PlantUML rendering (watch community Discussion
  #10111), the single biggest argument for Mermaid evaporates and the choice
  becomes a near-toss-up driven by expressiveness — tilt back toward PlantUML
  for UML-heavy users.
- If a credible head-to-head benchmark shows a material (>10–15 point) LLM
  accuracy or edit-fidelity gap favoring PlantUML on the common diagram
  types, revisit. None exists today.
- If livespec's user base skews heavily to formal-UML / regulated /
  enterprise-architecture users, raise PlantUML to co-default.

## Caveats

**The core comparison is under-evidenced.** No controlled Mermaid-vs-PlantUML
LLM benchmark exists; the recommendation is an inference from adjacent
single-format benchmarks, the training-data-familiarity mechanism, and the
rendering asymmetry. Treat the "almost as good" conclusion as well-reasoned,
not empirically proven.

**Source-quality flags.** The single-format academic benchmarks (Eklund &
Jonsson 2025; Ferrari et al. 2024; MermaidSeqBench 2025; Rouabhia & Hadjadj
2025, which found all 9 tested LLMs exceeded 90% PlantUML compile success) are
sound but each tests one format. Many "Mermaid vs PlantUML 2026" comparison
pieces are vendor/SEO blogs (mermaideditor.com, findutils, gleek,
infrasketch, etc.) — directionally consistent with each other and with
primary sources, but not independent empirical evidence; treat their
feature-gap claims as corroborated-by-consensus rather than authoritative.
The "90% first-try accuracy" and "lower hallucination rate" claims circulating
for Mermaid (and competing claims for tools like FlowZap) are marketing
assertions with no reproducible methodology — disregard them.

**Currency.** GitHub PlantUML-rendering status verified to June 2026 (still
none; Discussion #10111 open). Mermaid feature set as of v11.13.x (released
20 April 2026, adding Venn and Ishikawa types). Re-check Discussion #10111
and Mermaid's C4/deployment coverage periodically, as both are moving.

**Expressiveness gap is type-dependent.** "Almost as good" holds for
sequence/class/state/ER/flowchart. It does NOT hold for
deployment/timing/object/mind-map/rich-C4, where PlantUML is genuinely better
— hence the escape hatch.

**Naming note.** The livespec under analysis is
github.com/thewoolleyman/livespec (a Claude/agent skill-based spec tool with
versioned `<spec-root>/history/` snapshots). A separate, similarly named
`ftzi/livespec` ("Specs in sync with code and tests") also exists; ensure
conventions you publish are scoped to your repo to avoid confusion.
