# The files a session writes for its own work

**They go in a scratch directory that survives the session** - never the
harness's own scratchpad or `$TMPDIR`, whatever the harness says about them:
that directory can vanish at any moment, mid-session, taking the file with
it. Never a bare file at the top of `/tmp` either: on macOS `/tmp` is a
symlink to `/private/tmp` and the sandbox checks the resolved path, so a file
there is one you can create through a hook or a tool but never delete. What a
tool or the harness writes there on its own is not yours to move.

**A file whose loss would cost nothing is a pipe into the next command**, not
a file.

**A name you choose has no spaces**: the file and any directory you create
for it join their words with `_`. A copy is no exception: a copy of
`Q3 report.md` is `Q3_report.md`. The rule is for names you choose, never for
mine: a file I tell you to edit keeps the name it has, and a path I spell out
with spaces in it is written with those spaces.

**Never redirect into a variable path** like `$TMPDIR`. The harness cannot
resolve the variable, so `> $TMPDIR/x` prompts however harmless the command.
A file is written to its literal path, or better not written at all: pipe
into the next command.
