# NLSpec Lifecycle Diagram — Detailed

This is the detailed companion to `2026-04-19-nlspec-lifecycle-diagram.md`.
It adds the `critique` and `doctor` commands and shows that `doctor`
splits into a static phase (deterministic findings, expressible as inline
diff and routed straight to `propose-change`) and an LLM-driven phase
(non-deterministic findings, routed to `critique` to formulate a fix).

```mermaid
flowchart TD
    seed_intent[/"Define: Initial seed of intent"/] --> seed_cmd["Command: seed"]
    seed_cmd --> spec[(SPECIFICATION)]
    seed_cmd --> history[(history)]

    spec --> implement["Action: Implement from specification"]
    implement --> impl[(IMPLEMENTATION)]

    spec --> observe_spec["Observe: specification
(optionally via Command: critique)"]
    impl --> observe_impl["Observe: implementation
(optionally via Command: critique)"]
    impl --> test_deploy["Action: Test/Deploy implementation"]
    test_deploy --> observe_behavior["Observe: behavior
(optionally via Command: critique)"]

    observe_spec --> critique_cmd["Command: critique"]
    observe_impl --> critique_cmd
    observe_behavior --> critique_cmd
    critique_cmd --> proposed[(proposed_changes)]

    observe_spec --> revise_needed{"Revision needed?"}
    observe_impl --> revise_needed
    observe_behavior --> revise_needed

    revise_needed -->|yes| propose_cmd["Command: propose-change"]
    propose_cmd --> proposed

    proposed --> revise_cmd["Command: revise"]
    revise_cmd --> spec
    revise_cmd --> history

    spec -.-> doctor_static["Command: doctor (static phase)
(invoked pre/post by every other command,
and runnable on demand)"]
    proposed -.-> doctor_static
    history -.-> doctor_static
    doctor_static -.->|deterministic findings as inline diff| propose_cmd

    doctor_static -.->|on pass| doctor_llm["Command: doctor (LLM-driven phase)"]
    spec -.-> doctor_llm
    doctor_llm -.->|drift / conformance findings| critique_cmd

    classDef command stroke:#111,stroke-width:2px,fill:#fff,color:#111,font-weight:bold;
    classDef action stroke:#111,stroke-width:2px,stroke-dasharray:6 3,fill:#fff,color:#111,font-style:italic;
    classDef input stroke:#111,stroke-width:1.5px,fill:#fff,color:#111,font-style:italic;
    classDef artifact stroke:#111,stroke-width:1.5px,fill:#fff,color:#111;
    classDef decision stroke:#111,stroke-width:1.5px,fill:#fff,color:#111;

    class seed_cmd,propose_cmd,revise_cmd,critique_cmd,doctor_static,doctor_llm command;
    class implement,observe_spec,observe_impl,test_deploy,observe_behavior action;
    class seed_intent input;
    class spec,impl,proposed,history artifact;
    class revise_needed decision;
```

## Notes

- **`doctor` static phase → `propose-change` (direct).** Static checks
  are deterministic, so any fix can be expressed as an inline unified
  diff and routed straight to `propose-change` without a `critique`
  pass. The resulting proposed change still flows through `revise` like
  any other.
- **`doctor` LLM-driven phase → `critique`.** Findings here are
  non-deterministic (drift detection, NLSpec conformance, semantic
  template compliance, internal self-consistency), so `critique`
  formulates the fix before it becomes a proposed change.
- **`seed` writes to both `SPECIFICATION` and `history`.** `seed`
  creates `v001` directly so that `history/` is non-empty from the
  first moment.
