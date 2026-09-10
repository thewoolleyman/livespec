# Original requirements seed

Date captured: 2026-09-10

Source: the maintainer's initial turn that opened this planning thread.

Purpose: preserve the original brain dump verbatim so future planning,
implementation, and completeness reviews can distinguish the maintainer's
requirements from later interpretation. Spelling, capitalization, numbering,
and terminology below are intentionally uncorrected.

```text
I want to make this repo able to reproduce a box build from scratch on a bare/fresh linux instance.  Similar to how the k3s-on-gmktec-for-vps-usage plan is doing things like setting up full gitops reproducibility for repos / roles / machines like hp-xubuntu-info, poweredge-xubuntu-info, and gmktec-xubuntu-info.  

This repo is different, it was originally set up with the agent-flywheel process, and thus includes many utilities and helpers and config that came from that (see agent-flywheel related repos in /data/projects/

What I want is to to be able to reproduce an instance machine from this repo, from gitops, on a bare linux install, but there can be multiple of them, and even be containerized potentially in the future.


I know currently there's some bespoke services on it that can't be reproduced, e.g., the dolt server, the backups, etc.

Those obviously are not things that can have multiple instances, so this is going to create a NEW repo, agent-cockpit-info, that ONLY includes the stuff related to driving the AI work via tmux sessions, the 1password wrappers, the gh access, tailnet membership, etc.

So what we are NOT copying to the new repo is bespoke things like:

1. dolt-server install and assocaited backup/launchd
2. local (currently unused) fabro server
3. VS Code installation (I don't use it and don't want it). 
 
I don't need to preserve much from agent-flywheel install, but there are some things I like:

0. Anything this vps-info repo already refers to except above bespoke items
1. keep the existing tmux config
2. tailscale setup, assuming a new tailnet machine ID in the form of agent-cockpit-{n}, where {n} starts at 0. This should also be assumed to be the local hostname. 
3. 1password wrapper setup (manually provisioned with the single baked systemd service)
4. the custom bash history command (i.e. CTRL-r binding)
5. honeycomb config
6. claude, codex, and pi installed
7. gh CLI
8. AWS CLI setup
9. all other existing shared config (including MCP setup) for claude, codex, or pi
10. Local vnc server, running and exposed, with the same window manager currently used
11. Chrome installed locally and accessible in the vnc
12. 1password desktop installed and accessible in the local vnc
13. Honeycomb observability configured and emitted for all agent activity - see existing honeycomb-related repos in ~/workspaces/ for context, and any existing plumbing, launchd jobs, etc. 
14. Anything else needed for agent cockpit that I missed. 

There should also be a some config file added (ai-cockpit-config.jsonc, unless theres some other better gitops-y way to do this) to keep track of things.

FOr example, all the repos that should be auto-cloned.  Start with the list of currently cloned repos in ~/workspace, and we can prune them later

And another thing for the config would be the local hostname, e.g. which {n} the current host is.

Notes: 

- The username should still be ubuntu, NOT cwoolley
- The projects should be cloned direct to ~/workspace/.  NOT /data/projects which is symlinked by /workspace/
- THis can use ansible, like the other existing -info repos.

The main goal is to make the tmux-ai-agent-driving role of this machine be LESS OF A PET and MORE LIKE CATTLE, where ideally it can eventually even be containerized and run on kubernetes pods, with just an attached persistent disk.  


OPEN QUESTIONS:

I don't know the extent to which the existing *-xubuntu-info gitops repos rely on the livespec-dev-tooling or livespec repos for their gitops plumbing. 

Preferably this repo is standalone, but if there's a ton of easily reusable stuff in the livespec ecosystem, then we can consider making this a repo under the livespec ecosystem, e.g. livespec-agent-cockpit. With it listed as a full-fledged livespec fleet member.  Otherwise, if we don't have a dependency on dev-tooling, then it can just be a regular repo (not even necessarily an official livespec adopter), like the existing *-info repos.  Before writing the plan, we should discuss the pros and cons and run them by fable and sol subagents to get expert critique on tradeoffs. 

So the plan will include an explicit migration plan, to spin up this instance on a new VPS somewhere (to be provisioned), and start dogfooding it.

THEN we will DEPRECATE the duplicated info/roles/stuff out of this vps-info repo, and stop using this vps to drive agents as a cockpit.

The goal being that eventually all that will be left here is really the dolt-server, 

Use the $livespec-orchestrator-beads-fabro:plan skill to create this plan, with the slug create-agent-cockpit-repo.
```
