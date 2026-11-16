# Branches: where work lands and what it is called

Read before the first change in a repo, and before creating or naming a
branch.

## Which branch the work lands on

**Never work on the default branch, unless I have told you a repo is worked on
its default branch.** Before the first change that would land on it, create a
branch by the naming convention below, switch to it and tell me the name - no
proposal, no question.

**Otherwise a branch is created and checked out only when I ask for one.** The
work stays on the branch it is on, whatever that branch was made for, and its
commits go on top of the ones already there. When I ask, pick the name, create
the branch and tell me the name - no proposal, no question.

**`git worktree add` runs only when I ask for a worktree in so many words.** A
worktree checks out another branch without moving this one, so it is the same
switch by another route, and its registration in the repo's `.git` keeps that
branch undeletable after the session is gone.

**When you think the work does not belong on the current branch**, say why in
one sentence and ask whether to check out a new branch for it. The work waits
for the answer.

## Backups and other branches of your own

**A backup is made with `git branch <name>`**, which leaves HEAD where it is.

**A branch you created for your own work is yours to delete, never mine.** A
backup, a scratch branch, a throwaway for an experiment: once it has done its
job, delete it in the same session without asking, and never leave it for me
to find later. Ask only before deleting a branch you did not create.

## Branch names

**Before naming a new branch, read the convention of the repo it lives in and
follow it.** The remote branches show it - `git for-each-ref
--sort=-committerdate --count=30 --format='%(refname:short)' refs/remotes` -
whether names carry a person, a type (`feat/`, `fix/`), a ticket key, and which
separator. Check the repo's `CONTRIBUTING.md`, `CLAUDE.md` and README too, and
any CI rule that matches on the branch name: a name that misses such a rule
runs a different pipeline without saying so.

**When the convention puts a person in the name, that person is me**, spelled
as the handle I have given you, whatever older branches of mine use. With no
handle given, spell it the way my own recent branches in this repo do; with
none of those either, the local part of `git config user.email`. When the
convention carries no person, do not add one.

**The rest of the name is the change, in kebab case** - what the branch does,
never who asked for it or what wrote it (`fix-by-claude` says nothing). A
ticket key goes in when the convention has one and the task has one.
