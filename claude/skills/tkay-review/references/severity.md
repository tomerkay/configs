# The four colours

**Every finding and every bycatch row carries one colour, with its exact
emoji and word, or the 🧪 below for a claim that is sound but
unproven**, so I can tell at a glance whether something is broken or
merely imperfect:

| Tag | Meaning | Bar to qualify |
|-----|---------|----------------|
| 🔴 **BUG** | The work is wrong. It will fail, break, lose data, hang, or give the wrong result - code that crashes, a step that does the wrong thing, a figure that is false. | You can state a concrete failure: *"in case X, it gives the wrong result at <where>"* - in code, *"input/state X → wrong output or crash at `file:line`"* |
| 🟠 **RISK** | Not provably wrong today, but a real hazard: a case nobody covered, something that grows with no limit, a failure nobody would notice. In code: race window, unbounded growth, missing error path, perf regression on the hot path, silent failure, broken observability. In code, two that look like quality and are hazards: a promise - a behaviour callers rely on, a bug fix included - with no test that pins it when a unit test could; and a label value (enum, metric label, status word) that is false for some case producing it and has not shipped yet - after it ships, renaming it breaks every dashboard and alert that reads it. | You can name the condition that triggers it (scale, an empty input, a deadline, a source that changes; in code, concurrency or an upstream error) |
| 🟡 **QUALITY** | Works correctly, but is harder to keep up: structure, naming, repetition, stale docs, a broken house rule. In code: DRY, a missing log, a commit message that does not hold, a broken rule of the repo's `CLAUDE.md`. | It is right, but whoever maintains it pays a price |
| ⚪ **NIT** | Cosmetic. Whitespace, wording, ordering, style preference. | If I ignore it forever, nothing bad happens |

**The colour is picked on the hazard, never on the kind of thing.** Docs
that now lie are 🟡 - the same as a false commit message - until the lie
makes someone do harm: a wrong runbook step, an API contract a caller acts
on, and then they are a 🟠 on their own merits, as a silent failure. A
broken repo rule is 🟡; when breaking it created a hazard - a secret in a
log, a missing pin - that hazard is the 🟠.

**Never pick 🟡 to dodge an argument.** If you're unsure whether it is a
hazard, it's 🟠 and you say you're unsure. 🟡 is a claim that shipping
without it is safe - own it.

## 🧪 UNTESTED, the finding with no colour

**🧪 UNTESTED marks a claim that is not in doubt, only unproven**: you
traced it and found it sound, but only a check you cannot make yourself
proves it - a run, a measurement, a test on real data. It has no colour,
since nothing in it is wrong or at risk, and it asks for the check, never
a fix. A doubt you can name - a condition under which it might fail, which
you could not check - is never 🧪: it is a 🟠 RISK, because the doubt is
about the work.

**In place of a Fix Profile it carries a `Test 🧪` Profile**, in the frame
of `assessment.md`: the check in a few words, then the Evidence the claim
would have once the check passes, and the Size and Difficulty of making
it.

## The Fix Profile

**A fix is profiled on its own line**, in the frame of `assessment.md`:
what to do in a few words, then the Evidence that the fix would work and
the Size and Difficulty of the fix. Its label names only the colours its
findings have: `Fix 🔴`, `Fix 🟠` or `Fix 🔴🟠` for a fix of 🔴 and 🟠,
`Fix 🟡`, `Fix ⚪` or `Fix 🟡⚪` for a fix of 🟡 and ⚪. A thing with
findings of both kinds has one Fix Profile for each, and one whose kind
has no finding is left out.
