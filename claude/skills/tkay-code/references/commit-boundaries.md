# How Commits Are Cut

**A repo that documents its own convention for how commits are cut
overrides this file**, and the override is named to me in one line. How a
commit's message is written is not this file's.

## Commits Serve the Branch - One Thing Each, and No More Cuts Than That

**Commits serve the branch's final outcome, never the other way round.** What
ships is the tree at the top of the branch; the commits are how a reader
understands it, how a bisect finds a fault in it and how a revert takes one
change out of it. A commit is never a target of its own.

**A commit does one thing when a reader, a bisect and a revert each want it
whole.** A reader follows the branch commit by commit without assembling a
change from several; a bisect that lands on it finds one cause; a revert
takes out one change and nothing else. That is the test for every boundary,
squash and split alike - never the size of the diff, the number of files or
the length of a bullet.

**Every boundary costs something, so it must earn itself.** One more commit
is one more message to write and verify, one more commit for a code review
to read, and one more place a change is spread across. A cut none of the three wants is that cost
with no return: a branch of twenty immaculate two-line commits is harder to
read than one of five that each mean something. Both halves of the test
bite - a commit that mixes two things a revert would want apart, and two
commits that are one thing a reader has to reassemble.

**Which commit a change belongs in is judged by the test, and said in one
line before the commit.** The three cases:

- **It belongs in an earlier commit** when it only exists because that commit
  got something wrong or left it half done: it corrects a claim that commit
  made, rewrites prose that commit added, or finishes what it should have
  carried. A doc fix to wording an earlier commit introduced is the usual
  case - see "Documentation Sync on Every Commit".
- **Two commits are one thing** when apart they hide what the branch does:
  one is broken or meaningless until the other lands, or the reader has to
  assemble the change from both. The version bump keeps its own commit
  regardless; see "A Version Bump Is Its Own Commit, at the Top of the
  Branch". A fix for a shipped bug is never one of the two; see "A Fix for a
  Shipped Bug Stands Alone".
- **It stands on its own** when it is a different change for a different
  reason, one that would still make sense if the earlier commit were reverted.

## Two Suits: a Fix Stands Alone, a Feature Is a Series

**A commit is cut by what it is for.** A fix for a shipped bug is one commit
built to travel - the next section. A feature is a series, in this order,
each commit leaving the build and the tests green so any prefix of it is
correct on its own - the shape of the Linux kernel's
[Submitting patches](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)
("Separate your changes") and git's own
[SubmittingPatches](https://git-scm.com/docs/SubmittingPatches):

1. **Preparatory refactors**, one per commit - each changes no
   behaviour, so a reader checks it by eye and a bisect never lands on it.
   Make the change easy before making the easy change.
2. **The behaviour**, with the tests that pin
   it in the same commit. Several behaviour commits when a reader, a bisect
   or a revert would want them apart - the one-thing test above - and one
   when they would not.
3. **Docs** the behaviour makes true - or inside the behaviour
   commit when the two lines of a README would stand on their own in no
   reader's eyes.
4. **The version bump**, last - see "A Version Bump Is Its Own Commit, at the
   Top of the Branch".

**A refactor and a behaviour change never share a commit.** The one
exception is a rename the behaviour change cannot land without, and then the
commit's message names the rename as such.

A code review flags a mixed commit as one to split, and a series out of
order as a quality issue: the branch works either way, and the cost is the
reader's. A chore, a CI or style change and a test-only change are neither
suit, and each stands alone.

## A Fix for a Shipped Bug Stands Alone

**A fix for a bug that reached the default branch or a release is its own
commit, and nothing is ever squashed into it or it into anything** - not a
feature, not a refactor, not another fix. It must revert on its own,
cherry-pick to a release branch without dragging anything along, and be the
one commit a bisect lands on. Check where the bug came from before the first
line of the fix: `git merge-base --is-ancestor <introducing-sha>
<default-branch>` exits 0 when it shipped - against the remote copy of the
default branch whenever the repo has a remote.

- **One bug per commit.** No cleanup, no refactor, no second fix, no test
  for anything else.
- **The smallest diff that removes the root cause**, not one overfit to the
  symptom: a special case for the input that failed leaves the cause in
  place for the next input.
- **The test that fails without the fix lands in the same commit.**

**A bug introduced earlier on this unmerged branch is not a shipped-bug
fix.** It never ran anywhere, so its fix belongs in the commit that
introduced it, as the first case of "Commits Serve the Branch" says, and a
code review recommends folding a commit that carries it elsewhere into it.
A follow-up to a shipped-bug fix while that fix is still unmerged belongs
in the fix the same way.

The case that taught it: one fix commit to a shipped hook carried a second,
unrelated selftest with it.

```
❌ one commit: expand a bare ~ in the scratch exemption, and a selftest
   case that pins the denial of an unpinned kubectl that passes an
   empty kubeconfig

✅ commit 1: expand a bare ~ in the scratch exemption
✅ commit 2: deny an unpinned kubectl with an empty kubeconfig
```

Reverting the ❌ commit to undo a bad `~` expansion also drops a guard
nobody meant to touch.

## Documentation Sync on Every Commit

**Before creating any commit, check whether the change makes the repo
`CLAUDE.md` or any `README.md` near the changed files stale.** A line about
something that no longer exists is deleted, never turned into a record of what
used to be there; a line that is now wrong is corrected in place. Either way
the doc change lands in the same commit. If the docs are already accurate, say
so briefly and move on - don't update docs just to touch them.

This applies to every commit, not just when I explicitly ask for documentation
updates.

## A Version Bump Is Its Own Commit, at the Top of the Branch

**When a repo requires a version bump for a change - a plugin manifest, a
chart version, a package version - the bump is a dedicated commit,
the last one on the branch, and never folded into the commit that made the
change.** One bump at the top says it releases every commit under it, so a
reader sees at a glance which commits ship together; a bump inside the first
change says nothing about the commits that came after it, and a bump inside
the last one hides which earlier commits it covers.

A prefix of the branch without the bump then fails a CI version guard on
purpose: that prefix is not a release, and the guard saying so is correct.
