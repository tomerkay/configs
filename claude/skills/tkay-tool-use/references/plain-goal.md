# A goal for work with no plan

**When I ask for a goal that builds something and name no plan file -
"give me a goal for <what to build>" - build it as `goal-run.md`
says, with this file as the work's part.** A request that names a plan file
is not this file's. A goal is nightly only when I ask for a nightly goal;
any other is a live one.

## Before the goal is written

**Hunt the request for open decisions while I am awake.** A fresh subagent
reads the request against the code and lists every decision it leaves open
that would change what a user or a caller observes - an API, an output, a
default, a stored format. It gets the request and the repo, and nothing of
this session's reasoning. Each decision is put to me as a question, and my
answer goes into the goal as a "settled: <decision>" clause.

## What the run adds

- **The work is the request and its settled clauses**, cut into commits as
  the code skill's commit standard says.
- **A gap that changes what a user or a caller observes, and that neither
  the request nor a settled clause decides, is a 🙋 Your call**: write it
  in the report with its scenario, options and recommendation. A live
  goal asks me and waits; a nightly goal takes it as `goal-run.md`
  says a nightly goal takes a 🙋.
- **Every other gap is decided as the code around it would decide it.** The
  list of decisions made without asking is a "Decided while running"
  section of the report.
