# Waiting under a `/goal`

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
