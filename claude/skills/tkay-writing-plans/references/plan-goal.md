# A goal on a plan

**When I ask for a goal on a plan file - "give me a goal on <plan>.md" -
build it as `goal-run.md` says, with this file as the work's part.**
A goal is nightly only when I ask for a nightly goal; any other is a
live one. "Executing a plan" in `SKILL.md` holds for a live goal
exactly as it holds by day, its stop included: a hole stops the run and
is asked. In a nightly goal it holds but for that stop: nobody is there
to answer it.

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
- **A hole "Executing a plan" would stop for is a 🙋 Your call.** Write it
  into the plan with its scenario, options and recommendation. A live
  goal asks me and waits. A nightly goal takes it as `goal-run.md`
  says a nightly goal takes a 🙋: the sections that do not
  depend on it are built first, then the recommended option and every
  section resting on it, as one range of commits at the top, each named in
  "Decided while executing". Only a choice no revert can undo stops the
  sections that need it.
- **The list of decisions made without asking is the plan's "Decided while
  executing"**, and every CR subagent also gets the plan, to check each
  decision against the architecture it follows.
