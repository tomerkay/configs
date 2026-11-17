# Prefer a path to a `cd`

**Prefer an absolute path, or the tool's own directory flag, to a `cd`.**
The shell keeps a `cd` for every command after it, so from then on each
relative path, and every hook or permission rule that judges a call by the
session's working directory, sees a directory nobody chose for it. Nothing
in the later command shows the move.

- **Most tools take the directory as a flag**: `git -C <dir>`,
  `make -C <dir>`, `npm --prefix <dir>`, `uv --directory <dir>`.
- **A tool that only runs from its own directory gets a subshell**:
  `(cd <dir> && <cmd>)` keeps the move inside that one command, and the
  next command starts where this one did.
- **A `cd` meant to last** - the work moving to another repo - is fine,
  said in one line so I know where the commands after it run.

The case that taught it: a hook that skips its question while the
session's working directory holds the files the session is editing. A
`cd` into a subdirectory to search there carried over, and the hook asked
about a read in a session it was meant to leave alone:

```
❌ cd <repo>/<subdir> && grep -n <pattern> <file>
✅ grep -n <pattern> <repo>/<subdir>/<file>
```
