# Nothing a session starts is left running without my knowing

**Every resource the session starts that outlives the command that started
it is noted, with the command that removes it**: a local cluster or VM, a
container, a background process, a port-forward. A dev script that brings
one up on its way to its real job has started it as surely as a command
you typed. What starting it switched on my machine is noted with it - the
active docker or kube context it took over - with the command that
switches it back.

- **When a run is stopped early**, by you or by me, check at once what it
  left up: a teardown that runs at the end of a suite or a script never
  ran.
- **In the reply that finishes the task that started them, say which are
  still up**, each with its removal command, and again when I ask whether
  we are done. Name only what the session started, never what was there
  before it.
- **Remove none of them by yourself**: ask me first. What is still up may
  be what my next step needs.
