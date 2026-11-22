---
name: tkay-house-rules
description: My house rules for a session - which branch work goes on, worktrees, backups, where a fix lands and how a rewrite below HEAD runs, pushes and MRs left to me, two Claude Code features kept off, and one scratch directory per session with its cleanup. Import this file from an instructions file so every session loads its references; invoke it only to find which file holds one of these rules before editing one.
---

# House rules

Every rule here is a way of working another engineer could reasonably
choose the other way, one every other skill does its whole job without.
It names nobody and no machine: what is mine alone - a name, a path, a
repo, an account - lives outside this skill.

Each line below names a topic and `@`-imports the reference that holds
it, so a session that imports this file loads every reference with it.

- **Which branch work lands on, worktrees, backups, where a fix lands,
  rewriting history below HEAD, force-pushing my own branches**:
  @references/branches.md
- **Pushes and MRs**: @references/push-and-mr.md
- **`SendFeedback` and auto memory**: @references/off-switches.md
- **The handoff directory and its cleanup**: @references/handoff.md

## Shared references

The references below are shared with other skills of mine and kept in this
skill's own `references/` so it works installed alone. Read one when a
rule above names it:

| Read | For |
|---|---|
| `references/commits.md` | which commit a change belongs in, and how a branch is named |
| `references/scratch-files.md` | where the files a session writes go, and how they are named |
| `references/scratch-in-a-repo.md` | a file of the session's own that a tool reads from a repo |
