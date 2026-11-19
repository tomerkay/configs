# A goal run, nightly or regular

**A goal that builds something has two parts: the work it does, and how
it runs.** The goal for the work - a plan's sections, or a request - names
the work, checks it while I am awake, and says what stops it. This file is
how such a run usually goes, whatever the work - a recommendation, not a
form: each goal is built for its work, a part that does not apply is
dropped, and a risk the work carries gets a part of its own.

## A nightly goal and a regular goal

**A goal is nightly only when I ask for one in that word** - "a nightly
goal on <plan>", "a nightly goal for <what>". Every other goal is a
regular one, and I never have to say so.

- **A nightly goal runs with nobody there to answer.** It is built to
  never prompt and never stop: it takes every choice it can undo, and
  waits only on what it cannot take or cannot undo, as "What the run
  does" says.
- **A regular goal is live work that keeps going.** The work, the CR
  cycles, the suites and the report are the same, but I am there: every
  point where a nightly goal would decide for me is a question to me,
  asked as any live work asks it, and the run waits for the answer - a
  🙋 Your call, a hole in the plan, a gap a request leaves, a large test
  run, a command that needs a prompt.

**The goal says which it is, in its first line, loud and plain**, at the
top of its file above everything else, and as the first line of the reply
that hands it over:

```
**This is a nightly goal: it is built to run with no prompt, and it
decides for itself whatever it can undo.**
```

```
**This is a regular goal: it asks me whenever it needs me.**
```

The same line opens the goal's own text, so the run reads it first.

## Before the goal is handed over

1. **The test commands**: the repo's own check commands and the tests the
   work names, with every package or file named one by one.
   **The suites are the relevant ones, picked from an inventory**: every
   test entrypoint the repo has - its test build tags, its runner's test
   targets, its CI test jobs, scheduled and manual ones included - mapped
   to the paths the branch changes, each in or out with its reason, and
   shown to me before handover. CI's own job commands are preferred to a
   hand-picked subset; one the goal's author is unsure of runs, and the
   repo's quick unit command always does. Each runs in its checkout by
   the tool's own directory flag, or `env -C <checkout>` for a script
   that has none, and is shown to test the branch before handover - the
   step that runs its tests read, or the suite started and its first
   lines checked. A claim about where a script runs its tests is never
   written into the goal unchecked.
2. **For a nightly goal, every step that would stop for a permission
   prompt** - a command a permission rule or a hook asks about, a write
   the sandbox denies, a step only I can take. Each is reshaped so it does not ask, or, when it is the
   last step, the goal ends with "or stop when only <the step> is left".
   A command the work is likely to improvise that `unwatched-goal.md`
   gives no route for gets its own route written into the goal.
   Nothing the run needs waits on a prompt in the middle of the night.
3. **The skills the goal names come from this session's skill list**: the
   one for writing code and fixing a review, and the one for a code review.
4. **The branch**: the run works on the branch the repo's checkout is
   on. On the default branch, unless I have said the repo is worked on
   it, the goal creates a new one. When the work does not belong on the
   current branch, say why in one sentence and ask whether the goal
   creates a new one.
5. **The repo's checkout is clean**, checked with `git status --short`:
   the run commits there, so uncommitted work would ride along under its
   builds and tests. The goal says the checkout is the run's until it
   ends.
6. **A fresh subagent reads the written goal** before it is handed over,
   with the repo and nothing of the session's reasoning: the suite list
   against the inventory, each command against the checkout and branch
   it must act on, and the stop condition against what each phase is
   for. What it finds is fixed in the goal, or put to me.

**A nightly goal is written only once nothing is left that would stop it
reaching its end without me.** Before writing it, look for every such
stop - a step only I can take, a command that would prompt, a hole in the
plan or the request that would stop the run or send it the wrong way -
and put each to me, all in one reply. My answers go into the goal, and a
step only I can take is named in it as mine, to run before the run
starts. Every other gap stays the run's to decide and record.

Ask me only for that and for what none of this answers - the repo, the
files that must never be staged, and, when step 4 cannot settle it, the
branch - besides the suite list and what step 6 puts to me.

**The goal is written into a markdown file in a scratch directory that
outlives the session, and the reply never prints it** - I open the file
and copy from it. The file opens with "Run these, in order": each step
only I can take, then the `/goal` line, each in its own code block,
numbered in the order to run; the goal's full text and the two lists
below come after. The goal points at no file of
any skill and writes every rule out, so the run does the same whatever
skills it loads. A skill the run must invoke, such as the review skill, is
still named by its name, and a plan goal still names its plan by its path:
the plan is the work, not a pointer.

**Under the goal in the file come two lists:**

- **What it does:** one numbered line per thing the run does, in plain
  words and in the order it does them, one naming any departure from these
  files - so the list alone tells me what the run will do. It is checked
  off against the rules of these files one by one before handover, so a
  rule the run needs and the goal left out shows as a missing line.
- **Drawbacks:** two or three one-line bullets on where it may stall, what
  it will not catch and what it decides without me.

**The reply says in one line what the goal builds and ends with the goal
file's full path.** The `/goal` line names the plan or the request and
the goal file for the run to read first, and states the stop condition in
full, as things the conversation will show: the goal's checker reads only
the conversation - it never opens a file - so a stop it cannot see there
is one it cannot judge. The line stays under the harness's cap on a
`/goal` condition.

## What the run does

- **One signed commit per piece of work**, on the branch settled before
  the goal was handed over, in the repo's checkout, by the code skill's
  standards and the repo's conventions.
  After each commit, build and test the packages it touched.
- **The branch never changes during the run.** The run proposes no
  switch, makes none, and creates no branch, even when it comes to think
  the work belongs elsewhere: it says why in the report's "Decided while
  running", and the work stays where it is. Step 4 is the one place a
  branch is asked about.
- **Git runs outside the sandbox from the first call** when the harness
  sandboxes it. Stage explicit paths only; no rebase or reset; a tracked
  file the work deletes goes through `git rm`, never a plain `rm`; a fix to
  an earlier commit is an amend of HEAD or a new commit on top. Never push
  and never open an MR.
- **In a nightly goal, no command stops on a prompt**: the goal writes
  out `unwatched-goal.md`, with any route step 2 added.
- **Every decision made without asking goes in one list**, with the commit
  that carries it. The work's goal file says where the list lives.
- **Every CR is a fresh subagent spawned for that CR alone.** It invokes the
  review skill first, gets the repo path, the whole branch - from where
  it forks off the default branch to HEAD, so its call judges what would
  merge - the list of decisions made without asking, to check each
  against the code around it, and nothing of the session's reasoning,
  and is told it wrote none of that code and has not loaded the code
  skill; it returns the path of its CR file. **The first CR of each cycle
  is fresh**: it is handed no earlier CR file, so every cycle gets an
  independent read. **The rounds within a cycle build on it**: each later
  CR in the cycle is also handed the cycle's previous CR file and told to
  start from it as the review skill's repeat CR says, and when HEAD is
  still the tip that file judged and nothing handed to it changed, no
  subagent is spawned. The session works the CR's To do as the code
  skill's rules for fixing a review say, each fix in a dedicated commit,
  but for a 🙋 Your call row, which it takes as the next rule says. After
  each batch of fixes, a new subagent
  reviews the branch at HEAD, until a CR leaves nothing to fix: each
  blocking finding fixed or waiting on me.
- **A nightly goal never stops; it gets as close to the goal as it can.**
  A regular goal asks me each of these and waits. In a nightly one, a
  🙋 Your call - from a CR, a hole in the plan, a gap the request leaves,
  a fix the code skill's rules say to show and wait on - that one revert
  can undo is taken: the run first builds every piece of work that does
  not depend on it, then the recommended option, in commits of its own,
  and the work that rests on it, so the choice and everything resting on
  it sit at the top of the branch as one range of commits. It goes in the
  report's "Decided while running" with the other options and that range.
  A choice no revert can undo - a data migration, a message sent, a
  resource deleted, an API published to callers outside the repo - is
  never taken: it waits on me, and the run builds everything that does not
  depend on it.
- **What the run cannot take waits on me, and the run carries on**: a
  choice no revert undoes, a step only I can take. It goes in the report
  at once, with its scenario, options and recommendation. A
  failure in code the branch's commits never touched is reported, never
  fixed: it goes in the report as likely there before the branch, waiting on
  me, with no attempt spent on it. A failure the run cannot trace to the
  code gets no fix commit: it is rerun once at the same commit with
  nothing changed, and goes in the report as "passed on rerun, no change"
  or as waiting on me. Anything else gets up to three fix attempts per
  finding or failing suite - an attempt amends the one before it while
  that one is HEAD - and after the third goes in the report as waiting on
  me. Either way the run carries on with the work that does not need it.
- **An item waiting on me is checked again, and retried only on new
  code**: each cycle's CR and suites show whether it is still there, and
  one that no longer shows is marked resolved. It gets one more attempt
  in a later cycle only when a commit since its last attempt changed the
  code around it.
- **A finding that asks for a run, not a code change, gets the run**: a
  claim the review traced and found sound but could not prove. When the
  run it names is one the goal already allows - one of its suites or test
  commands - it runs with the suites, and a failure is handled as theirs
  is; any other goes in the report as waiting on me.
- **The suites run after the CR phase**, in the background, holding
  the machine awake (`caffeinate -i` on a Mac), each with its log in a
  scratch directory that outlives the session. Each failure gets a
  dedicated fix commit and a rerun of that suite, under the three-attempt
  rule above.
- **A suite proves it tested the branch.** Within its first minutes its
  log, or the working directory of its processes, shows which checkout
  and commit it tests; one testing anything else is stopped and started
  again on the branch. Its result counts only when the log shows the
  branch's code ran - a test only the branch has, or paths in the
  branch's checkout. A suite that never tested the branch has not run:
  it is never waiting on me, and no stop counts it.
- **A later cycle reruns a suite only when its code changed**: a commit
  since its last pass touched the dependency tree of what it builds and
  runs (`go list -deps` in Go) or a file it reads at run time. When that
  tree cannot be worked out, it runs again.
- **The CR phase and the suites phase make a cycle, up to three.** A new
  cycle starts only when the suites phase made commits, so a fresh CR
  reviews them. When the third cycle's suites phase made commits, a final
  CR reviews HEAD and fixes nothing: what it finds goes in the report as
  waiting on me. A CR or a suite that cannot run - no CR file, a suite
  that will not start - is retried once with nothing changed; a suite then
  gets a route that starts it on the branch with no prompt, and only when
  none exists waits on me, with the exact command for me to run, and the
  run moves on.
- **A report in that scratch directory stays current, written for the
  morning.** Its top is what only the run knows, in plain words a teammate
  follows - no SHA or log line, two or three sentences an item at most;
  then the paths of every file it made; then the final CR, in full, which
  opens with the branch's overview and ends with its To do:

  ```
  # Goal run: <the plan file, or the request in a few words>

  <the final CR's branch call> - <how far the work got, in one sentence>
  <the branch> · <N> commits · ran <how long> · <how the run stopped>

  ## Needs you
  N1. <what happened and why it needs me, in two sentences> (TD3)
      a) <an option> - <what it costs>
      b) <another option> - <what it costs>
      I'd pick <a or b>: <why>. Reply "N1 a" or "N1 b".

  ## Decided while running - check these
  D1. <the choice, the options it passed over, and the commits that rest on it>

  ## Suites
  - <each suite: passed on the branch, failed, or waiting - its log in Files>

  ## Files
  - <what it is>: <full path>

  ---

  <the final CR, in full>
  ```

  - **The two lines under the title answer "can I merge?"**: the final
    CR's branch call, how far the work got, and whether the run stopped
    on its own or after its third cycle.
  - **Needs you** holds every item waiting on me, in the order to act,
    each numbered N<n> with its scenario, options and recommendation, and
    ending with the reply that settles it; one that is a row of the final
    CR's To do names it. Last, when failed fix attempts can be folded
    into the fixes that closed them, an optional item gives the one
    command that folds them, naming the commits. With nothing waiting, it
    says so in one line.
  - **Decided while running** holds every choice the run made alone,
    numbered D<n>: a 🙋 it took, with the options it passed over and the
    range of commits that rests on it, and every gap decided as the code
    around it would decide it, each with its commit. On a plan, they are
    the plan's "Decided while executing", in plain words.
  - **Suites** gives each suite's result on the branch: passed, failed, or
    waiting on me, and a suite that passed only on a rerun says so.
  - **Files** lists every file the run made or was given, each with what
    it is and its full path: the goal file, the plan or the request, every
    CR file by cycle and round, every suite's log by suite and cycle. Only
    files that exist are listed.
  - **The final CR**, in full, as its file holds it, below the line: the
    run's last CR comes after its last fix, so it is copied once, when the
    run stops, and the report answers why the branch is or is not ready
    without a second file.
- **It stops** when a cycle's suites phase made no commits, or when the
  third cycle and its final CR are done. Either way the report shows
  every piece of work done or stopped for a recorded reason, the last CR
  blocking nothing but what waits on me, and every suite and every run a
  finding asks for passing on the branch - at HEAD, or at a commit since
  which nothing touched its code - or waiting on me. **The run's last
  reply is the two lines under the report's title, then one line per
  rule of the stop condition with what shows it holds - each suite, the
  commit it passed at and the log line that shows it ran on the branch;
  the last CR's call; the cycle count - then the report's full path.**
  It is written only once the stop holds, and the checker judges the
  `/goal` line against it.
