# Testing approach

- integration testing is python scripts testing skills a throwaway tmp dir, directly executing claude code and comparing to spec expectations
- Integration tests reflect actual specifications. Have an CLAUDE.md in the tests dir which helps enforce consistency
  of tests with actual specification. Split into separate test files per part of the specification - intent, contracts, constraints.
- Meta test "test_drift_prevention" test which ensures that every major section of the specification has a corresponding test.

# File location

- prompt to Default to SPECIFICATION dir in root, or if non-default, save in .livespec.jsonc config file in project root. Must handle multiple specifications in same project.

# SPECIFICATION directory structure

-
`.livespec.jsonc` - optional config file for livespec, including default specification dir, and any other config options, lives at root of project
- `SPECIFICATION` - contains all files generated/mainained by livespec (except .livespec.jsonc)
    - `README.md` - overview of the specification files and subdirs
    - Actual specification files based on template, e.g. `intent.md`, `contracts.md`,
      `constraints.md`, `scenarios.md`
    - `proposed_changes`
        - `README.md`
        - versioned proposed changes
        - filename format: `v001-proposed-change-<topic>.md`
    - `history` dir
        -
        `vnnn` directories - All past and current versions of specification and proposed_changes / acknowledgements, in subdirs by version
           - All spec files, but prepended with `vnnn-` to indicate version, e.g. `v001-intent.md`, `v001-contracts.md`, etc.
             This prevents the historic version files from confusing LLMS or being found through autocomplete by humans.
           - proposed changes files for that version, with filename format:
             `v001-proposed-change-<topic>.md`
           - acknowledgements for proposed changes from revise step with the filenamd format:
             - `v001-proposed-change-<topic>-acknowledgement.md`
        - all spec versions, all critiques and acknowledgements

# `livespec` skill sub-commands

- `help`
    - shows usage and sub-commands
- `help <sub-command>`
    - shows help for sub-command
- `seed <freeform text>`
    - With no args, explains and prompts user for seed. Freeform text, which can include references to existing specifications, examples, projects, or other context.
    - creates initial spec structure and files, including README.md with instructions
- `propose-change <topic> <freeform text>`
    - create or update a change proposal
    - Can reference an inline diff against latest version, to make specific targeted and deterministic edits.
- `critique <author>`
    - Author defaults to current AI model
    - Automatically use AI to critique the current plan and create or update a change proposal with topic `<author-critique>`
- `revise <freeform text>`
    - Automatically processes and acknowledges all change proposals
    - Processes any other freeform text argument prompt
    - create new versioned history dir
    - save new version to history
    - write acknowledgements to history, including rationale for which proposed changes were accepted, which were rejected, and any revisions made to the proposed changes.
      - `v001-proposed-change-<topic>-acknowledgement.md`
    - move proposed change to history
    -  and acknowledgements to history
- `doctor`
    - static script, not AI
    - Check and optionally fix any statically-enforcable constraint.
    - e.g.: directory structure, template compliance, missing versions in history, diff between current version and latest version in history, missing tests, etc.
    - For diff between current and latest history version, prompt to auto-create a proposed change (contianing just the diff and a summary) and a revision. 
- All commands should run doctor before and after execution.

# MLSpec conformance

- Enforce conformance with NLSpec guidelines
- Use https://github.com/TG-Techie/NLSpec-Spec/blob/main/nlspec-spec.md as prior art inspiration
    - but there are concerns with "intent" terminology, and implied one-way flow from intent -> spec -> implemenetation.
    - Instead It's a loop.

# Spec templates

- Allow different formats of specification
- Allow custom critique prompt
