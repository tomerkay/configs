# Plan review

A plan review judges a full plan before anything is built on it: whether to
start, fix the plan first, run an experiment first, or go back to design. It
is the plan's version of a code review, modelled on the design reviews of
mature projects - a reviewer who did not write the design, a fixed list of
what to check, and a call that ends it, as Kubernetes runs its
[production readiness review](https://github.com/kubernetes/community/blob/master/sig-architecture/production-readiness.md).

`plan-shape.md`, beside this file, is the shape the plan is held to. The
colours, the 🧪 UNTESTED finding, the FINDINGS line, the MUST HAVE and NICE
TO HAVE sections, the bycatch table and "Rules that keep the tags honest"
are `code-review.md`'s, and hold here as written there; this file says what
changes when the thing judged is a plan instead of a branch.

## A cold read

**The reviewer reads the plan file and the code it describes, never the
conversation that produced them.** A plan is read by people who were not in
its discussion, and the review stands in for them. A line that only makes
sense to someone who was there is a finding: 🟡 when the design holds without
it, 🟠 when a decision rests on it.

## Claims are checked, not trusted

**A plan's facts are run, the way a commit's runtime claims are.** Before the
plan's call:

- **Every number**: its query is run again against its data source. A number
  that no longer comes out is a finding; one with no query beside it is too.
- **Every incident status**: Solved and Mitigated are checked against the
  mechanism and the test the plan names, in the code once it exists and in
  the fix's design before it does. A Solved with no mechanism behind it is 🟠.
- **Every "not a problem"**: checked the way the plan says it was.
- **Every invariant**: names the test that pins it, or is written as
  unpinned.
- **Every new responsibility**: has its design note, as `design-note.md`
  gives it, with its owner checked against the code that owner already
  holds. An owner that would end up with two reasons to change, or a job
  with two owners or none, is a finding on the fix: 🟠 when a change you
  can name elsewhere would then break it, 🟡 otherwise - the test "One
  reason to change" in `clean-code.md` gives. A piece of state with two
  writers, or a departure the note does not name, is a finding the same
  way.
- **Every link to a known architecture**: opened, and read for whether it
  says what the plan says it does.

A claim the reviewer cannot check itself - a query against a system it
cannot reach, a behaviour only a prototype shows - is 🧪 UNTESTED, with the
three lines `code-review.md` gives every 🧪. A doubt it can name is a 🟠 RISK
(UNVERIFIED), as there.

## What each colour means in a plan

| Tag | In a plan |
|-----|-----------|
| 🔴 **BUG** | The design as written fails a concrete scenario: the state, the sequence, the wrong outcome. |
| 🟠 **RISK** | A check of `plan-shape.md` missing or answered with no reason, an invariant with no test, a status with no mechanism, a decision with no architecture behind it, a number that does not reproduce. |
| 🟡 **QUALITY** | The design holds, but the plan breaks its shape: a section out of place, a line for nobody, a value that goes stale, a TBD entry the plan depends on. |
| ⚪ **NIT** | Wording, ordering, formatting. |

## A finding goes on the section its fix edits

**Each finding sits under the plan section whose edit closes it**, as a CR
puts a finding on the commit that should carry the fix. A problem that spans
sections - an invariant the contract states and no test pins - goes on the
section the fix edits, never on every section it touches.

## The shape of a plan review

Three sections, in this order, each under its own top-level heading:

1. `# Findings` - one `## Section <n>: <title>` per plan section with a
   finding, in plan order, each with its FINDINGS line and then the MUST
   HAVE, UNTESTED and NICE TO HAVE sections as `code-review.md` gives a
   commit. A section has no assessment of its own: the plan's call judges the
   plan. One line after the last section names the sections with no finding
   and what was checked in them.
2. `# Plan <file> Call` - the plan's FINDINGS line, counting every
   section's findings, then its Full Assessment in the frame of
   `assessment.md`: the plan's call as the Call, a **Plan** Profile - the
   plan as it stands, Evidence that its design does what it claims - and the
   Fix Profiles and the `Test 🧪` Profile `code-review.md` gives a commit.
3. `# 🎣 Bycatch` - the table `code-review.md` gives, for what the review
   turned up in the code it read that the plan neither changes nor depends
   on.

## The plan's call

The worst finding decides it, in the order ❌, 🔧, 🧪, ✅:

| Call | When |
|---|---|
| `✅ Build it` | no 🔴, 🟠 or 🧪 |
| `🔧 Build after fixes (<the sections>)` | a 🔴 or 🟠 that an edit to the plan fixes |
| `🧪 Build after a spike (<the run or the experiment>)` | no 🔴 or 🟠, and a 🧪: a claim only a run the reviewer could not make, or a prototype, settles |
| `❌ Back to design (<the problem or the architecture>)` | the problem is the wrong one, or the architecture fails a concrete scenario no edit fixes |

**(🍰 No brainer)** may follow ✅ Build it and ❌ Back to design, on the
judgement `assessment.md` gives. **A Plan Profile whose Evidence reads
DOUBTFUL, REFUTED or UNKNOWN never gets ✅ Build it**, as no such Profile
gets a go-ahead in a CR.
