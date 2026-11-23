# The design note

**A design names four things for each new responsibility a change adds**,
before any code rests on it:

- **Owner** - which module, type or service holds it, and why there: a
  place the reader knows. A job split across two owners, or given to one
  that already has an unrelated job, is settled here, never left for
  whoever writes the code.
- **State** - where each new piece of state lives, and who alone writes
  it.
- **Interface** - what each piece asks of the other: what a caller must
  know, and nothing more.
- **Departures** - each rule of `clean-code.md`, beside this file, the
  design breaks, with the simpler design it was weighed against and why
  that one loses; "none" when it breaks none.

**An obvious design gets one sentence, not four fields**: when the owner is
already there, nothing new is kept and no rule is broken, the note says
exactly that and stops.

**The note is held against `clean-code.md` before anything rests on it**,
since a design mistake found in the diff is paid for twice.

**A note sits under an architecture and never picks one.** How one worker
stays the active one, how two services stay in step - a choice between
known architectures is made first, and the note is written on the one
chosen.
