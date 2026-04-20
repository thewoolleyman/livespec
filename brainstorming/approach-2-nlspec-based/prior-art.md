# Prior Art

This document collects the prior art discussed while developing the current NLSpec-inspired `livespec` model. It is organized as an annotated bibliography: each entry includes a citation-style reference, a link, and a short note on why it mattered to the discussion.

## Core NLSpec Reference

1. TG-Techie. "NLSpec Spec." GitHub. <https://github.com/TG-Techie/NLSpec-Spec/blob/ed7a531884c456787254d0450d450664e296b75b/nlspec-spec.md>

   Context: This was the main direct prior art. It was useful for its emphasis on strong separation between intent, specification, and implementation; self-consistency; ambiguity discipline; and specification-first thinking. It was also the source of the specific framing we pushed against: `Intent -> NLSpec -> Implementation`.

## Requirements Engineering Foundations

2. Zave, Pamela, and Michael Jackson. "Four Dark Corners of Requirements Engineering." <https://www.pamelazave.com/4dc.pdf>

   Context: This was one of the most important foundations for separating kinds of intent. It supports distinguishing desired effects, domain assumptions, and specification, which helped clarify why incoming revision pressure and current authoritative specification should not be collapsed into the same term.

3. Zave, Pamela. "Foundations of Requirements Engineering." <https://www.pamelazave.com/fre.html>

   Context: This gave additional grounding for the distinction between requirements-level desire and formalized specification. It reinforced the idea that "specification" is a committed and structured form of intent, not the absence of intent.

4. de Boer, Remco, et al. "On the Similarity Between Requirements and Architecture." *Journal of Systems and Software*. <https://www.sciencedirect.com/science/article/pii/S0164121208002574>

   Context: This was important because it supports the claim that requirements and architecture are not cleanly separable kinds of statements. That directly backed the concern that a specification is itself a form of intent, and that architecture can legitimately live inside the main living spec surface.

## Iterative Requirements and Architecture Development

5. Nuseibeh, Bashar. "Weaving the Software Development Process Between Requirements and Architectures." <https://cin.ufpe.br/~straw01/epapers/paper05/paper05.html>

   Context: This was used as support for rejecting a strictly one-way lifecycle model. It reinforces the idea that requirements and architecture co-develop iteratively rather than flowing cleanly in only one direction.

6. Microtool. "What Is the Twin Peaks Model?" <https://www.microtool.de/en/knowledge-base/what-is-the-twin-peaks-model/>

   Context: This is a secondary summary rather than the canonical source, but it was useful as a concise explanation of the Twin Peaks idea: requirements and architecture evolve together. It supported the loop-based framing of the `livespec` process.

## Multi-View Documentation and Structured Descriptions

7. ISO/IEC/IEEE 42010. "Conceptual Model." <https://www.iso-architecture.org/ieee-1471/cm/>

   Context: This supported the move away from treating the specification as a single monolithic artifact. It helped justify the model of one logical specification represented through multiple files or views.

8. Kruchten, Philippe. "The 4+1 View Model of Architecture." <https://www.researchgate.net/publication/220018231_The_41_View_Model_of_Architecture>

   Context: This was relevant because it shows a mature precedent for representing one system through several complementary views. It helped frame `contracts.md`, `constraints.md`, and `scenarios.md` as operational partitions rather than separate competing specifications.

9. arc42. "Overview." <https://arc42.org/overview>

    Context: arc42 is practical prior art for decomposing architecture/specification documentation into multiple structured sections. It reinforced that a multi-file or multi-view representation can still be one coherent description.

## Living Documentation and Executable Specification

10. Fowler, Martin. "Specification by Example." <https://martinfowler.com/bliki/SpecificationByExample.html>

    Context: This was useful as a concise articulation of living, example-driven specification work. It helped connect the discussion to scenarios as executable or reviewable spec artifacts rather than just prose examples.

11. Cucumber. "BDD Is Not Test Automation." <https://cucumber.io/blog/bdd/bdd-is-not-test-automation/>

    Context: This was useful for separating discovery and communication from mere test writing. It supported keeping scenarios as a first-class specification partition rather than collapsing them into implementation verification alone.

12. Cucumber. "BDD in the Finance Sector." <https://cucumber.io/blog/bdd/bdd-in-the-financial-sector/>

    Context: This offered additional applied support for scenario-driven, executable specification approaches in serious domains. It reinforced the value of keeping scenarios separate and concrete.

13. Cucumber. "Isn't the Business Readable Documentation Just Overhead?" <https://cucumber.io/blog/bdd/isn-t-the-business-readable-documentation-just-ove>

    Context: This was relevant to the argument that human-readable, scenario-oriented artifacts are not redundant overhead if they remain part of the living specification corpus.

## AI-Native Spec-Driven Tooling

14. Augment Code. "Intent Overview." <https://docs.augmentcode.com/intent/overview>

    Context: This was relevant because it shows one contemporary AI-native approach to "intent" as a maintained artifact aligned with implementation. It was useful both as inspiration and as a contrast, especially around terminology.

15. Augment Code. "Intent." <https://www.augmentcode.com/product/intent>

    Context: This product page was a lighter-weight complement to the documentation. It was useful as evidence that "intent" is already emerging as a term in AI-assisted software workflows, which made the terminology question more important.

16. Fission AI. "OpenSpec." GitHub. <https://github.com/Fission-AI/OpenSpec>

    Context: This is the main project-level reference for OpenSpec as a spec-driven development system for AI coding assistants. It was especially relevant because its README explicitly frames the workflow as iterative rather than waterfall and shows a concrete change/spec/design/tasks flow that is very close to the kind of operational lifecycle `livespec` is exploring.

17. Fission AI. "OpenSpec Concepts." GitHub. <https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md>

    Context: This was one of the most directly relevant modern precedents. It supported the idea of separating current authoritative specification state from queued or proposed changes, which aligned strongly with `proposed_changes` and `revise`.

18. Fission AI. "OpenSpec Getting Started." GitHub. <https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md>

    Context: This helped show how a modern spec-centered tooling workflow can be presented operationally. It was useful for thinking about command-level ergonomics as distinct from conceptual lifecycle structure.

19. BMad Code. "BMAD-METHOD." GitHub. <https://github.com/bmad-code-org/BMAD-METHOD>

    Context: This was added as broader workflow prior art for AI-assisted agile development. It is less directly about specifications than OpenSpec or Kiro, but relevant as an example of a structured, agent-mediated development method that tries to scaffold planning, collaboration, and execution rather than treat AI coding as an unstructured prompt-to-code jump.

20. Kiro. "Specs." Kiro Docs. <https://kiro.dev/docs/specs/>

    Context: This was useful as a contemporary example of a three-phase spec workflow built around `requirements.md`, `design.md`, and `tasks.md`. It is relevant both as a contrast and as inspiration: it shows one practical decomposition of spec work into files and phases, especially around planning-to-implementation transitions.

21. clay-good. "spec-gen." GitHub. <https://github.com/clay-good/spec-gen>

    Context: This was useful as prior art for AI-assisted or code-assisted specification generation and drift management. It supported the concern with explicit boundaries, drift detection, and keeping spec and implementation aligned over time.

22. Sumers, Theodore R., Shunyu Yao, Karthik Narasimhan, and Thomas L. Griffiths. "Cognitive Architectures for Language Agents." arXiv. <https://arxiv.org/pdf/2309.02427>

    Context: This is not direct prior art for specification management, but it is relevant background for AI-native implementation systems. It provides a useful vocabulary for separating memory, action space, and decision-making loops in language agents, which may help frame the downstream implementation step that consumes a `SPECIFICATION` even though it does not directly solve spec governance.

## How These Sources Shaped the Current Model

The sources above pushed the design in five concrete directions:

1. The specification is one logical living specification, even if represented across multiple files.
2. `spec.md` is a clearer name than `intent.md` for the current authoritative spec surface.
3. `intent` is better reserved for incoming change pressure and revision inputs.
4. The process should be modeled as a loop, not as a single pass from rough idea to code.
5. `contracts`, `constraints`, and `scenarios` are best understood as specialized operational partitions or views, not as competing sources of truth.
