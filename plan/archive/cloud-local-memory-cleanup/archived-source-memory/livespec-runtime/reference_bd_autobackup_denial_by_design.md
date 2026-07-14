---
name: bd-autobackup-denial-by-design
description: "bd's \"auto-backup failed … command denied\" warning is correct-by-design; hourly systemd dolt-backup.timer does the real backups — never file an item for it"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7536741f-7f82-41df-845c-47c6d7b900ed
---

Every `bd` write in livespec-governed repos emits
`Warning: auto-backup failed: register backup remote: … command denied
to user '<tenant>'@'%'` (dolt-server :3307). Per the github-app-auth
overseer (2026-07-02): the tenant-level DOLT_BACKUP denial is
**correct-by-design** — tenants are deliberately not granted backup
rights; the real backups run via the hourly systemd
`dolt-backup.timer` on the host. Do NOT file work-items or attempt
fixes for this warning. Related: [[beads-tenant-access]].
