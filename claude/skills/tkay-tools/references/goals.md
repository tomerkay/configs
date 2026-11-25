# Under a `/goal`

**The harness says a goal's Stop hook blocks stopping until the goal
holds. That is a reason to answer the hook, never to keep a tool call
going.**

- **A goal waiting on me**: say so once, with the command that unblocks it
  and `/goal clear`.
- **A goal waiting on a background run of yours**: say once what it waits
  for and what each outcome leads to, then end the turn, as `long-runs.md`
  says.

Either way, every time the Stop hook fires again, answer in one line; the
full status never repeats.

**A goal whose work is done but whose checker refused the reply is a third
case: it waits on neither me nor a run, but on the reply.** The checker
reads the last reply for what the goal line asks, and may check each claim
in it against what the session's commands printed. So every later reply is
the full reply in the line's shape, never one line: it fills each gap the
refusal names, and backs each claim the refusal doubts with a command whose
output shows it. The first of those replies also says once that the work is
done and `/goal clear` ends it now.

The case that taught it: a goal whose work was done after its first cycle,
refused thirteen times - four of them on one-line answers to the Stop hook,
others on proof no command had printed: an empty vet log, a cached test
line.

**When two refusals in a row name the same gap, and nothing the session
could run or write would close it without breaking the goal's own rules,
the refusals have no exit: the next reply says so, once.** It says the
work is done, which line the checker refuses, why no reply can meet it,
and that `/goal clear` ends the goal now; every Stop-hook firing after it
gets one line. A gap a command could still close is never one of these:
it gets the command.

The case that taught it: a finished nightly goal refused about fifteen
times on one suite line, for a test that failed the same way on the
default branch, whose only fix the goal itself forbade.

**A goal that will stall on me gets a better `/goal` line suggested in
the reply that acknowledges it, and nothing more.** The goal I typed stays
set, the suggestion is one line I may ignore, and the work starts in that
same reply as though it were not there: no ❓, no wait. A goal stalls on
me when it needs a go-ahead of mine the goal line can carry, or a step only
I can take - a command that needs my explicit permission, an install the
sandbox refuses, a decision of mine. When that step is the
last one, the suggested line ends with "or stop when only <the step> is
left", which the goal's checker accepts as met; when work follows it, the
line gets no such clause, since the pause is what lets the goal carry on
once I answer.

The case that taught it: a goal set before the go-ahead it needed, which
answered "Still blocked on you" until the harness paused it, when the same
goal with the go-ahead in its line ran through.
