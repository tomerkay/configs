# Fixing what a review found

**When I hand you a review to fix - a CR, an MR's review threads, a bot's
summary - the target is a correct branch, never a clean review.** A fix that
brings a bug of its own is worse than the finding it closed: the finding was
named and visible, the new bug is neither.

## What gets fixed

- **What the review says blocks the merge, and nothing else.** What it calls
  optional, nice to have or a nit stays my call, and every extra fix is one
  more chance at a new bug.
- **A review that does not say which findings block is asked about, never
  guessed.**
- **A design choice where both sides are valid, and anything that may be
  intentional, is shown and waits**, even when I said to fix the blockers: a
  finding that questions a choice does not settle it.

## How each fix is made

- **A finding's written-out fix is where you start, not an order.** It is
  checked against the two questions below before it is applied.
- **Every fix is the smallest, plainest change that closes its finding** -
  delete, reorder, rename, add the missing guard or the missing call: a
  change a reader verifies at a glance. One that needs a new mechanism, a new
  code path or a restructure, or that touches code the finding never named,
  is shown and waits.
- **Every fix answers two questions as it is made: does it do what it claims,
  and did it break anything around it?** Trace what it touches - its callers,
  the paths beside it, the rest of the branch - and run what can be run.
  Striking the finding answers neither.
- **A fix that fails either question gets one easy fix of its own, or it
  stops**: name the finding, what the fix failed to do or broke, and the
  options as you see them. A hard fix is never stacked on top of it.
- **A finding closes only because the code got better.** Never close one by
  arguing it down, softening its severity, or deleting the test, check or log
  that exposed the problem.

Which commit each fix belongs in is `commits.md`'s.
