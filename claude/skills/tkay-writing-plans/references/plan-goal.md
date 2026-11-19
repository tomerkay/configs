# A goal on a plan

**When I ask for a goal on a plan file - "give me a goal on <plan>.md" -
build it as `unattended-run.md` says, with this file as the work's part.**
"Executing a plan" in `SKILL.md` holds for the run exactly as it holds by
day.

## Before the goal is written

1. **The plan's commit sections are the work**, in order.
2. **Hunt for holes while I am awake.** A fresh subagent invokes this skill
   first and reads the plan against the code, looking for what "Executing a
   plan" stops for. It gets the plan and the repo, and nothing of this
   session's reasoning. What it finds is put to me before the goal, and the
   goal comes once each is settled.

## What the run adds

- **Implement the commit sections in order**, each with the tests it lists.
  A section may land as more than one commit - a refactor ahead of it, or
  its work split in two - each a new commit on top, never a rebase, squash
  or reorder of what is already committed; each is recorded in the plan's
  commit sections and in "Decided while executing".
- **Follow "Executing a plan": the first hole ends the section work.** Write
  it into the plan with its scenario, options and recommendation, and
  implement no section after it, so the branch stays a prefix of the plan in
  which every commit is correct on its own. The CR-and-suites cycles still
  run on what landed.
- **The list of decisions made without asking is the plan's "Decided while
  executing"**, and every CR subagent also gets the plan, to check each
  decision against the architecture it follows.
