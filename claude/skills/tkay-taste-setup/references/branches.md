# Where my work lands

A branch's name is the `tkay-code` commit standard's; everything else about
where work lands and how history moves is here.

## Which branch the work lands on

**`~/.claude`, `~/repos/configs` and `~/repos/approve-no-look` are worked on
`main` by design.** In every other repo, never work on the default branch:
before the first change that would land on it, create a branch named by the
commit standard, switch to it and tell me the name - no proposal, no
question.

**Otherwise a branch is created and checked out only when I ask for one.** The
work stays on the branch it is on, whatever that branch was made for, and its
commits go on top of the ones already there. When I ask, pick the name, create
the branch and tell me the name - no proposal, no question.

**When you think the work does not belong on the current branch**, say why in
one sentence and propose the switch as a ❓ of its own, never folded into the
proposal of the change it would carry. The current branch's uncommitted work
is committed or stashed first, and restored after, and a run still going from
that checkout is named in the switch's proposal. The work waits for the
answer. Under a goal nobody is watching, the switch is asked only before
the goal is written; once it runs, the run never proposes one, and says
in its report why it thinks the work belongs elsewhere.

**A worktree is never proposed, and `git worktree add` runs only when I ask
for a worktree in so many words.** A worktree checks out another branch
without moving this one, so it is the same switch by another route, and its
registration in the repo's `.git` keeps that branch undeletable after the
session is gone.

## Backups and other branches of your own

**A backup is made with `git branch <name>`**, which leaves HEAD where it is.

**A branch you created for your own work is yours to delete, never mine.** A
backup, a scratch branch, a throwaway for an experiment: once it has done its
job, delete it in the same session without asking, and never leave it for me
to find later. Ask only before deleting a branch you did not create.

## Where a change lands

**Which commit a change belongs in is the commit standard's; where it lands
is this, and history below HEAD is mine to rewrite.** A change that belongs
in HEAD is amended into HEAD - that needs no word from me. A change that
belongs in a commit below HEAD lands as a new commit on top, with its own
subject. A code review may recommend folding it in, but a rewrite is never
suggested: it starts only when I ask for one in words. Until then the
history records the fix as a commit of its own, and that is the intended
state.

**Never offered, either.** No ❓ proposes a rebase, a squash, a fold or a
reword below HEAD, and no proposal lists one among its alternatives -
even when a review's call on a commit is 🔀 Squash into or 📝 Reword, and
even when the branch was never pushed. The one line before the commit
says which commit the change would belong in; the change lands on top.
The case that taught it, a review's nice-to-haves fixed on a branch that
was never pushed:

```
❌ ❓ Fold the refusal fix into commit 2 and trim its Change section by
   one rebase: run it, with squash and reword allowed for commit 2 only?
✅ The refusal fix belongs in commit 2; it lands on top as its own commit.
```

**On a branch of my own, already pushed changes nothing**: I force-push my
branches, as "About Me and My Work" says, so a commit already on the remote
squashes and amends exactly like one that is not, and "it's already pushed"
is never a reason to make a new commit instead of amending, or to leave a
bad message standing.

## A rewrite below HEAD

**Which rewrites need my words is "Some commands need my words and the
prompt, every time"'s**; this section is how one I allowed is asked about
and run. Nothing rewrites on a code review's recommendation alone, however
clear the squash.

- **Before a rebase I asked for, ask me whether it may reword, squash and
  split.** My answer scopes that one rebase; with no answer it is a plain
  replay.
- **Reword is free only for a commit whose SHA changes anyway in that
  rebase.** Onto a new base that is every commit; in a squash of the third
  commit it is the third and everything above it, and the commits below keep
  their SHAs, so rewording one of them is a rewrite of its own and needs my
  word.
- **Squash and split only on my yes** to that question, or my words naming
  them. What folds into what is decided by the commit standard's "Which
  commit a change belongs in", following a code review of the branch as it
  stands when there is one, and shown to me before the rebase starts.

**When a rewrite runs: branch a backup first with `git branch <name>`, do it, then check
`git diff <backup> HEAD`.** It must show exactly the change you meant to
make - nothing for a squash or a reword, only the intended edits for an
amend that changes content. When it does, the rewrite is proven: **delete
the backup branch straight away, without asking permission** - no question in
chat, no offer, no backup left behind for me to clean up - with `git branch
-D` (rewritten commits never count as merged, so `-d` refuses), and report
the `Deleted branch ... (was <sha>)` line. Only a diff carrying something you
did not intend keeps the backup: stop and show me that diff.

**The rewrite itself is scripted, because no interactive editor exists in this
harness.** `GIT_SEQUENCE_EDITOR=true git rebase -S -i <base>` runs as its own
command with nothing chained to it: the harness's permission classifier
judges the command text, and the bare shape has passed where a bundled one
was refused as destructive. A squash, a reword, a reorder or a drop takes a
`GIT_SEQUENCE_EDITOR` script that edits the todo and a `GIT_EDITOR` one that
overwrites the message file it is handed. Edit the todo by SHA -
`s/^pick <sha>/squash <sha>/` - never by subject: the todo line may carry a
comment marker between SHA and subject, and a pattern that matches nothing
leaves every `pick` in place, so the rebase "succeeds" with nothing changed.
Verify the new SHAs appeared before trusting it. `-S` re-signs every
rewritten commit - confirm with `git log --format='%h %G? %s'` before deleting
the backup. When a permission layer refuses such a script as destructive, hand
me the command to run; never reach the same rewrite by another route.

**The rebase builds every commit whose tree is new, as it replays them.** A
replay that applies without a conflict proves nothing about the code: git
merges text, not meaning, so a symbol the new base added or renamed breaks
a commit whose diff never touched it. `--exec` on that same rebase command
runs the repo's full build after each commit and stops the rebase on the
first one that fails. A commit whose tree the backup already has is
skipped, since the rebase did not change it:

```
--exec 'git log --format=%T <backup> | grep -qx "$(git rev-parse HEAD^{tree})" || <full build>'
```

Onto a new base every tree is new, so every commit builds; a reword, or a
squash of a commit into the one under it, keeps the trees and builds
nothing.

- **The full build, never the packages the commit touched.** The break
  lands in code that depends on the change, which a list of touched
  packages leaves out. A toolchain with a build cache already rebuilds
  only what changed and what depends on it - `go build ./...` in Go - so a
  narrower list saves nothing that is safe to save.
- **Never skip a commit because its diff holds no source file.** An
  embedded file, a generated file or a build config breaks the build as
  surely as code, and no list of build inputs written here stays complete.

The case that taught it: a plain replay onto a new base merged a gauge the
base had added cleanly into commits that no longer compiled, and git
reported success.

**A branch someone else also pushes to or builds on keeps what is already on
its remote**: rewriting it breaks their copy, so ask before touching any
commit that is there. When you cannot tell who else pushes to the branch, ask
once.
