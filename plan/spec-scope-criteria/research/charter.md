## The maintainer's statement of what done means

Why are you saying that everything needs a spec change? Where are you making these spec changes? Not every fucking thing has to be in the spec. We should prefer to put things in the skills and tools. What should the criteria be for putting things in a spec? / Not everything is a spec change and that is, I believe, one of the biggest bottlenecks in the factory. We need to open a new plan that looks into the suggestions it gave and makes a clear distinction on what actually belongs in the spec or the non-functional spec so the spec stops blowing up and slowing everything down. (maintainer, 2026-11-16; source: comment on livespec-dev-tooling-6tgd2z 20:27Z)

## Definition of Done assertions derived from that statement

- The livespec specification states criteria for what belongs in the spec and the non-functional spec versus code with tests and skills or tools, admitting only contracts between components or repos, safety or security guarantees, and promises to users or operators.
- The orchestrator tier judge chooses spec-change only when the item changes or adds a contract, safety guarantee or user promise, and not merely because no clause covers it.
- The coordinator guidance no longer names ratify as the default route and no longer limits release-spec-tier to items a clause already states.
- The items held as spec-change that are not contracts, including bd-ib-qawphe, bd-ib-ugel56 and bd-ib-2sbrov, are released to the factory.
- The share of factory wait attributable to spec-change holds is measured before and after the tier-judge change and recorded on the plan epic.

# spec-scope-criteria — charter

Why are you saying that everything needs a spec change? Where are you making these spec changes? Not every fucking thing has to be in the spec. We should prefer to put things in the skills and tools. What should the criteria be for putting things in a spec? / Not everything is a spec change and that is, I believe, one of the biggest bottlenecks in the factory. We need to open a new plan that looks into the suggestions it gave and makes a clear distinction on what actually belongs in the spec or the non-functional spec so the spec stops blowing up and slowing everything down. (maintainer, 2026-11-16; source: comment on livespec-dev-tooling-6tgd2z 20:27Z)

Scope: (a) criteria for spec/NFR vs code+tests and skills/tools (start: contracts between components or repos, safety or security guarantees, promises to users or operators); (b) tier judge default -> spec-change only when item changes/adds a contract, safety guarantee or user promise; (c) replace .ai/coordinator-duties.md 'Ratify is the default route' and the clause-only release-spec-tier rule; (d) sweep held items bd-ib-qawphe, bd-ib-ugel56, bd-ib-2sbrov (+ livespec-orchestrator-beads-fabro#5392) and every other spec-change-held item, release non-contracts; (e) measure spec-change holds' share of factory wait before/after (lever-1 contribution).
