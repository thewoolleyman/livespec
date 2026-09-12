# Unarchive and maintainer-acceptance correction

Date recorded: 2026-09-12

## Why this plan was unarchived

The plan was archived through the archive-time transfer exception after its
remaining work was named in `agent-cockpit-info` issues #2 and #12. That was an
administrative disposition, not completion of the plan's implementation or
acceptance gates. At archive time the PowerEdge Kubernetes substrate and
cockpit had not been brought through G-1, G1, G2, or G3; no tailnet-accessible
cockpit instance had been presented to the maintainer; the quantitative
dogfood window had not run; and the later VPS, migration, second-instance, and
deprecation phases had not completed.

Using the transfer exception in that state contradicted this plan's declared
goal and the plan operation's normal archive rule that work remain live until
it is implemented, merged, shipped where applicable, and verified. Named
follow-up carriers remain useful execution records, but they do not substitute
for this plan's end-to-end supervision or acceptance.

## Missing maintainer gate

The original research said that the implementation was “completely working”
for maintainer review only after G-1 through G3 were green and called for one
consolidated maintainer ceremony after autonomous G0-G3 parity. It did not
record the maintainer's stronger instruction as an explicit closure gate:

- a live agent-cockpit Kubernetes instance on PowerEdge must be running;
- the maintainer must be able to reach and use it through the tailnet,
  including SSH access and the intended remote desktop path;
- all promised cockpit behaviors must have current, attributable acceptance
  evidence on that instance, with every non-applicable host-only behavior
  separately proven in the G3 VM lane rather than silently waived;
- the maintainer must personally test the instance and explicitly accept it;
  automated evidence or an independent completeness review cannot stand in
  for that acceptance; and
- the plan must remain live after that review until every later in-scope phase
  (external VPS dogfood, migration, second-host proof, and old-owner
  deprecation) is either genuinely completed or the maintainer explicitly
  changes the plan's scope. The archive-time transfer exception alone is not a
  permitted closure mechanism for this plan.

This is a correction added on 2026-09-12, not a claim that the omitted wording
was present in the original plan.

## Resumption order

1. Restore the live plan directory and reopen epic `livespec-livyxu`.
2. Reconcile the current `agent-cockpit-info` implementation and GitHub issue
   state against research notes 001-007 without weakening any gate.
3. Resume at the earliest unmet dependency, including the G-1a/G-1b PowerEdge
   substrate prerequisites and their security, storage, evidence, and reboot
   reconstruction receipts.
4. Bring up the G1/G2 Kubernetes cockpit lanes and G3 disposable VM lane,
   iterate until the full acceptance matrix is green, and make the G2 cockpit
   reachable over the tailnet by SSH and the intended VNC path.
5. Present the running instance and evidence to the maintainer for hands-on
   testing. Record explicit acceptance or every observed defect; defects return
   to implementation and verification.
6. Continue the remaining plan phases. Do not archive until the corrected
   closure rule above is satisfied.
