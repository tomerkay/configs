# The four colours

**Every finding and every bycatch row carries one colour, with its exact
emoji and word**, so I can tell at a glance whether something is broken or
merely imperfect:

| Tag | Meaning | Bar to qualify |
|-----|---------|----------------|
| 🔴 **BUG** | Code is wrong. It will misbehave, crash, corrupt data, hang, or produce the wrong result. | You can state a concrete failure: *"input/state X → wrong output or crash at `file:line`"* |
| 🟠 **RISK** | Not provably broken today, but a real hazard: race window, unbounded growth, missing error path, perf regression on the hot path, silent failure, broken observability. Two that look like quality and are hazards: a bug fix with no test that reproduces it when a unit test could, and a label value (enum, metric label, status word) that is false for some case producing it and has not shipped yet - after it ships, renaming it breaks every dashboard and alert that reads it. | You can name the condition that triggers it (concurrency, scale, empty input, upstream error) |
| 🟡 **QUALITY** | Behaves correctly. Structure, naming, DRY, missing log, stale docs, a weak or false commit message, a broken rule of the repo's `CLAUDE.md`. | Code is right, but whoever maintains it pays a price |
| ⚪ **NIT** | Cosmetic. Whitespace, comment wording, ordering, style preference. | If I ignore it forever, nothing bad happens |

**The colour is picked on the hazard, never on the kind of thing.** Docs
that now lie are 🟡 - the same as a false commit message - until the lie
makes someone do harm: a wrong runbook step, an API contract a caller acts
on, and then they are a 🟠 on their own merits, as a silent failure. A
broken repo rule is 🟡; when breaking it created a hazard - a secret in a
log, a missing pin - that hazard is the 🟠.

**Never pick 🟡 to dodge an argument.** If you're unsure whether it is a
hazard, it's 🟠 and you say you're unsure. 🟡 is a claim that shipping
without it is safe - own it.

## The Fix Profile

**A fix is profiled on its own line**, in the frame of `assessment.md`:
what to do in a few words, then the Evidence that the fix would work and
the Size and Difficulty of the fix. Its label names only the colours its
findings have: `Fix 🔴`, `Fix 🟠` or `Fix 🔴🟠` for a fix of 🔴 and 🟠,
`Fix 🟡`, `Fix ⚪` or `Fix 🟡⚪` for a fix of 🟡 and ⚪. A thing with
findings of both kinds has one Fix Profile for each, and one whose kind
has no finding is left out.
