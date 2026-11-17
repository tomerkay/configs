# An unattended run

**A goal that builds something with nobody there to answer has two parts:
the work it does, and how it runs.** The goal for the work - a plan's
sections, or a request - names the work, checks it while I am awake, and
says what stops it. This file is how such a run usually goes, whatever the
work - a recommendation, not a form: each goal is built for its work, a
part that does not apply is dropped, and a risk the work carries gets a
part of its own.

## Before the goal is handed over

1. **The test commands**: the repo's own check commands and the tests the
   work names, with every package or file named one by one.
2. **Every step that would stop for a permission prompt** - a command a
   permission rule or a hook asks about, a write the sandbox denies, a step
   only I can take. Each is reshaped so it does not ask, or, when it is the
   last step, the goal ends with "or stop when only <the step> is left".
   Nothing the run needs waits on a prompt in the middle of the night.
3. **The skills the goal names come from this session's skill list**: the
   one for writing code and fixing a review, and the one for a code review.

Ask me only for what none of this answers - the repo, and the files that
must never be staged.

**The reply lays out two goals that run the same way, each ready to paste,
in this order:**

1. **Short** - verified at a glance. It tells the run to follow the work's
   goal file and this one, each by its skill and file name, and states only
   what is this run's own: the repo, the plan or the request, the files
   never to stage, the suites, the stop condition, and any departure from
   these files.
2. **Standalone** - points at no file of any skill and writes every rule
   out, so it does exactly what the short goal does. Above it, one line
   says so, and a numbered list names each rule it carries, a few words
   each: the rules of these files this run needs, checked off against them
   one by one before handover. A skill the run must invoke, such as the
   review skill, is still named by its name, and a plan goal still names its
   plan by its path: the plan is the work, not a pointer.

**Under both come two short lists of one-line bullets:**

- **Covers:** two or three, on what the goal does, in plain words, one
  naming any departure from these files.
- **Drawbacks:** two or three on where it may stall, what it will not
  catch and what it decides without me, then one for each option on what
  it alone costs.

## What the run does

- **One signed commit per piece of work**, on a new branch in a new
  worktree, by the code skill's standards and the repo's conventions.
  After each commit, build and test the packages it touched.
- **Git runs outside the sandbox from the first call** when the harness
  sandboxes it. Stage explicit paths only; no rebase or reset; a tracked
  file the work deletes goes through `git rm`, never a plain `rm`; a fix to
  an earlier commit is an amend of HEAD or a new commit on top. Never push
  and never open an MR.
- **Every decision made without asking goes in one list**, with the commit
  that carries it. The work's goal file says where the list lives.
- **Every CR is a fresh subagent spawned for that CR alone.** It invokes the
  review skill first, gets the worktree path, the branch range and the list
  of decisions made without asking, to check each against the code around
  it, and nothing of the session's reasoning, and it returns the path of
  its CR file. The session fixes each blocking finding in a dedicated commit
  by the code skill's rules for fixing a review, and writes in the report
  any fix those rules say to show and wait on. After each batch of fixes, a
  new fresh subagent reviews the branch at HEAD.
- **The fix loop stops itself** when a CR finds a blocking finding that a
  fix commit brought in, or a finding a fix commit claimed to close.
- **The full suites run last**, in the background, holding the machine awake
  (`caffeinate -i` on a Mac), each with its log in a scratch directory that
  outlives the session. Each failure gets a dedicated fix commit and a rerun
  of that suite, at most twice per failure.
- **A report in that scratch directory stays current**: each piece of work
  done or stopped with its reason, every decision made without asking, the
  path of every CR file with the last CR's commits table, and each suite's
  result.
- **It stops** when the report shows every piece of work done or stopped
  for a recorded reason, the last CR blocking nothing, and every suite
  passing - or when the fix loop's stop or a failure cap ends it, with the
  reason in the report.
