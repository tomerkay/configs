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
- **In a reply, each one still up opens with a ⚠️** - what is running and
  the command you would run to stop it - never a plain item in a list or
  a summary, where it reads as one more thing done and gets skimmed
  past. A report a run writes to a file keeps its own shape.
- **When I ask whether we are done, one still up makes the answer no**,
  until it is stopped or I say to leave it. The reply says no on a ⚠️
  line for each one, naming what is still running, and ends by asking
  whether to stop each; on my yes, you run the stop command. Once each is
  stopped or I say to leave it, the answer is yes, and the session's
  summary names each one left, behind its ⚠️, as still running, left up
  by me. The case that taught it, a session whose tests had started a
  local VM:

  ```
  ❌ Yes, you can exit now.
     Here's a short summary of the session:
     - 5. Colima is still running from the tests; colima stop stops it.
  ✅ ⚠️ No - Colima is still running from the tests (`colima stop`).
     ...
     Stop Colima?
     (I say to leave it)
     Yes, you can exit now.
     Here's a short summary of the session:
     - 5. ⚠️ Colima is still running from the tests, left up by you.
  ```
- **Remove none of them by yourself**: ask me first. What is still up may
  be what my next step needs.
