# A goal nobody is watching never stops on a prompt

**While a goal runs with nobody there to answer, every command you
improvise is shaped so no permission prompt stops it.** Before the first
one, read the `ask` rules of every settings file that applies - the
organisation's managed policy included - and what the hooks ask about. A
step one of them names takes a route none of them names; a step with no
such route goes in the run's report as waiting on me, or in the reply when
the run keeps none, and the run carries on with the rest.

- **Set files aside with git, never by moving them.** `git stash push
  --include-untracked -- <paths>` holds tracked edits and new files alike,
  and `git stash pop` brings them back, with no `mv` or `rm` for a
  policy to ask about.
- **No `cd` in front of a repo command**: the tool takes the repo by its
  own flag - `git -C <repo>`, `go -C <repo>`, `make -C <repo>`, `yarn
  --cwd <repo>` - or, for one that has none, `env -C <repo>` or a runner
  target that moves there itself. A `cd` before a git command can draw a
  prompt of its own, since the directory's hooks and config run with it.
- **No shell variable and no `$(...)` in a command**: every path is
  written out in full, every time, even when it repeats. The harness
  cannot tell where a write through a variable lands until the shell has
  run, so it asks.
- **A file is edited with the edit or write tool**, never `sed -i`,
  `perl -pi` or a redirect into it - a commit message included: it is
  written with the write tool, then committed with `git -C <repo> commit
  -F <its full path>`.
- **A banned shape is never what stands between the run and its
  purpose.** When a step's only shape is one these rules ban, the run
  finds a route that keeps both - the flags above - and only when none
  exists does the step wait on me.

The cases that taught it: a run that set new files aside to build a
refactor on its own, under a policy that asks about every `mv`; and one
that kept two paths in variables to edit and commit its message, which
stopped on "a variable in this command can't be checked before it runs"
with nobody there to answer.

```
❌ cd <repo> && git stash push -- <edited files> && mkdir -p <scratch>/park && mv <new files> <scratch>/park/ && go build ./...
   the run stopped on a prompt with nobody there to answer it
✅ git -C <repo> stash push --include-untracked -- <edited files> <new files>
   go -C <repo> build ./...

❌ M=<scratch>/msg.txt; sed -i '' 's/a/b/' $M; R=<repo>; git -C $R commit -F $M
   the run stopped on a prompt with nobody there to answer it
✅ <the message edited with the edit tool>
   git -C <repo> commit -F <scratch>/msg.txt
```
