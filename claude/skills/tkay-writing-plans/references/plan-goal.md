# A goal on a plan

**When I ask for a goal on a plan file - "give me a goal on <plan>.md" -
build it as
`unattended-run.md` says, with this file as the work's part.** "Executing a
plan" in `SKILL.md` holds for the run exactly as it holds by day.

## Before the goal is written

1. **The plan's commit sections are the work**, in order. Which section
   builds on which comes from each one's "Builds on" line; a section with
   none counts as building on every section before it, so a missing answer
   stops more, never less.
2. **Hunt for holes while I am awake.** A fresh subagent invokes this skill
   first and reads the plan against the code, looking for what "Executing a
   plan" stops for, and for a section that touches what another adds
   without naming it on its "Builds on" line. It gets the plan and the
   repo, and nothing of this session's reasoning. What it finds is put to
   me before the goal, and the goal comes once each is settled.

## What the run adds

- **Implement the commit sections in order**, each with the tests it lists.
- **Follow "Executing a plan".** A hole stops only the sections that build
  on it: write it into the plan with its scenario, options and
  recommendation, mark those sections skipped, and carry on with the rest.
  A section that changes a file a skipped section lists counts as building
  on it, whatever its "Builds on" line says.
- **The list of decisions made without asking is the plan's "Decided while
  executing"**, and every CR subagent also gets the plan, to check each
  decision against the architecture it follows.
