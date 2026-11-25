# A long run goes to the background with its log, and holds the Mac awake

**A command that runs longer than a few minutes runs in the background, with
its output into a log in a scratch directory that survives the session.**
The harness wakes the session the moment it exits, so a crash is seen at
once; a foreground call is capped at ten minutes and shows nothing until it
returns.
Nothing watches the log for a stall: a hang and a slow step look the same
from outside, and a guess about which one it is costs a false alarm. When
I ask whether a run is stuck, read the log's tail and its last-modified
time, sample the process's CPU time twice and read the wait it sits in and
what it holds open (`ps -o pid,stat,wchan,cputime`, `lsof -p`), and say what
has moved and what has not: a hung process has flat CPU time and sits in one
wait, a slow one does not. For a Python job, `py-spy dump` shows the line it
is stuck on.

**Waiting on the run is ending the turn.** Once it is in the background,
nothing waits on it in the foreground - no poll, `sleep` or `grep` loop on
its log, whatever the step size. Its exit wakes the session, and a Monitor
wakes it for any event worth seeing before then; a foreground wait only
adds tool calls that learn nothing those two would not have reported.

The case that taught it: a two-hour suite in the background with a Monitor
posting each test's end, and a foreground waiter polling the same log
beside both, renewed every ten minutes.

## On a Mac, it holds the Mac awake

**Before starting any command that runs longer than a few minutes - a test
suite, a build, a cluster bring-up, a long watch - prefix it with
`caffeinate -i`** on a Mac. A Mac set to idle-sleep soon after the screen
goes dark (`pmset -g`, the `sleep` line) freezes every process on it: the
run, colima, the mock cluster and this session together. On wake, the
wall-clock timeouts inside the run have expired and it fails, an hour in,
for no reason in the code. The harness renews a short `caffeinate` of its
own only while a session is working, and a pause in that renewal is enough.

- **`caffeinate -i <command>`** holds the Mac awake exactly as long as the
  command runs and ends with it: nothing to clean up, no setting changed.
  For a run already started, `caffeinate -i -w <pid>` does the same.
- **A dark screen is fine.** `-i` blocks idle sleep only; the display still
  dims and the lock screen still comes, and neither stops a process.
- **Say in one line that the hold is on**, so I know I can leave the
  computer. What it does not cover: a closed lid, an empty battery, and a
  log out or restart, which end every process of the session.

The case that taught it: a KWOK suite over an hour long, left to run with
the screen dark on a Mac set to sleep soon after.
