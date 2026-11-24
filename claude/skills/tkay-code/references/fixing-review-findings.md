# Fixing what a review found

**When I hand you a review to fix - a CR, an MR's review threads, a bot's
summary - the target is a correct branch, never a clean review.** A fix that
brings a bug of its own is worse than the finding it closed: the finding was
named and visible, the new bug is neither.

## What gets fixed

- **A review with a To do list is worked from it, top to bottom**, and
  nothing beyond it, each row as its Who says: a 🔧 Fix row is fixed, as
  the finding it points to writes the fix out, or written as the new
  commit it names; a 🧪 Run row is run and its result reported; a 🙋 Your
  call row - a decision, a large run, a run that needs what only I have -
  is asked as a question, with the review's options and its
  recommendation, and waits for my answer - never picked for me. The list
  already holds the set the next bullet gives, with what is not built yet
  and the runs.
- **Any other review - an MR's threads, a bot's summary - is fixed for
  what it says blocks the merge, and the cheap rest**, unless I name a
  narrower set: every NICE TO HAVE finding whose fix is cheap; every
  bycatch row whose call is 🔧 Add fix, fixed when its fix is at least
  LIKELY, easy or super easy and medium or smaller, and otherwise asked as
  "fix it now or leave it?" - a large or hard one is always mine; and
  every ⏸ Leave for now bycatch row whose fix is cheap. **A fix is cheap
  when the review rates it super easy, or small and easy, with Evidence at
  least CONFIDENT**: a NICE TO HAVE or ⏸ Leave for now fix the review only
  believes would work is not made untried, and not asked about either.
  Anything else optional is left unfixed, listed, and fixed only when I
  ask for it: every extra fix is one more chance at a new bug. A bycatch
  fix is a commit of its own.
- **Each finding is checked before it is fixed.** One the code shows is
  wrong, or whose fix would not close it, is left unfixed and named, with
  why.
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

Which commit each fix belongs in is `commit-boundaries.md`'s.
