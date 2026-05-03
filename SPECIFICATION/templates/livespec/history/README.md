# History

This directory holds the immutable per-revision snapshots of the
sub-specification. Each `vNNN/` subdirectory contains a
byte-identical copy of every sub-spec file as it stood when
revision `vNNN` was finalized. Versions are contiguous starting at
`v001`. Each `vNNN/proposed_changes/` subdirectory contains the
proposed-change files plus paired `-revision.md` records that drove
that revision. The directory is skill-owned: `livespec` writes new
versions on `/livespec:revise --spec-target SPECIFICATION/templates/livespec/`,
`/livespec:prune-history --spec-target SPECIFICATION/templates/livespec/`
removes the oldest contiguous block, and the doctor static phase
enforces version contiguity plus revision-pairing invariants.
