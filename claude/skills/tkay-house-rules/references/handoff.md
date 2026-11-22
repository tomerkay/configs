# The handoff directory

The scratch directory `scratch-files.md` asks for is the handoff directory.

**Every file you write for your own work goes in your fork's subdirectory of
this session's directory under `~/.cache/claude-handoff`**: scratch,
intermediate output, a script, a snapshot, a staged copy, a message file.
The session directory is named `<YYYY-MM-DD>-<slug>` after the day and the
session's work, the slug's words lowercase and joined by `-`, never by a
space or the `_` `scratch-files.md` gives other names. The fork's
subdirectory is the first 8 characters of
the session ID in the harness's scratchpad path. A new session is one
fork. A forked session inherits the conversation and the session
directory's name, but gets a session ID of its own, so it writes in a
subdirectory of its own. A subagent is not a fork: it writes in the
subdirectory of the fork that spawned it. Nothing is written at the top
level of `~/.cache/claude-handoff` or of the session directory. Create
either directory if it is missing.

**A tmp file I ask for without a path goes in that handoff directory too** -
"write it to tmp", "a temp file", in whatever words - never `/tmp` and never
the scratchpad. A path I spell out, `/private/tmp/claude/...` or any other, is
followed exactly as given. For the handoff case, give me its full path, with
this line right under it:

> ⚠️ In the session's handoff directory: survives a restart, and I offer to
> delete it when you ask whether we are done.

No question and no confirmation - the line is a note, not a stop.

**A file of yours that a tool reads from a repo** -
`scratch-in-a-repo.md` says when one exists - **stays where it is until the
work is over**, the same as the handoff directory: a permission policy may
prompt on every `rm`, so a mid-task delete is a prompt I must be awake
for. Never stage or commit it. The cleanup offer below names each one by
its full path and deletes it in the same `rm` as the directory. Never
leave my machine carrying files I did not ask for and do not know exist.

**Nothing inside the session's handoff directory is deleted file by file: it
stays until the work is over**, because a handoff waits on me and a
permission policy may prompt on every `rm`. Never offer to clear it
unprompted - not mid-task, not when the work looks finished. Only when I
ask whether we are done, what is left over, or whether I can exit - in
whatever words - say what your fork's subdirectory holds, and every file
of yours left outside it, and give me both ways to delete: you run the
`rm -r`, which may prompt me, or a `! rm -r` I paste. When other
forks' subdirectories remain, it deletes only yours and says "Delete this
fork (other forks still live)"; when yours is the last, it deletes the
whole session directory and says "Delete the whole directory (no other
fork left)". The path is the directory's full name, never a glob. A plan
or write-up in it worth keeping is named first, with the repo it belongs
in, so I decide whether it moves there before the directory goes.
`~/.cache/claude-handoff` itself stays.

**Other sessions' directories are not yours, and neither are other forks'
subdirectories.** Never list another session's, never say what either
holds, never offer to delete them. Listing the session directory to see
whether another fork's subdirectory remains is the one look allowed.

**A session that keeps a file of what it found on the way keeps it as
`bycatch.md` in your fork's subdirectory.**

**This directory is the cleanup offered when I ask whether we are done**:
the reply opens with "Yes - nothing open left, only the handoff directory to
delete.", unless something else found on the way is still to be shown,
which comes first. **The offer is a bare question with nothing to weigh**,
so it is the last thing in the reply. It comes only once the work leaves
nothing open - every repo the session touched included; while anything is
open, the reply says what is open and the offer waits for a later reply.

**Never put `rm` in a command that does real work.** Where a policy
prompts on every `rm`, scratch included, an allow rule cannot override
it, so an `rm` bundled into a chain prompts the whole chain.

**A tracked file the change deletes goes through `git rm`**, which a rule
on `rm` does not match, so it runs without that prompt and stages the
deletion with the rest of the change. A plain `rm` is left for files git
does not track.
