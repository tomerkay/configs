# Plan review

A plan review judges a plan - a shape plan or a full plan - before anything
is built on it: whether to
start, fix the plan first, run an experiment first, or go back to design. It
is the plan's version of a code review, modelled on the design reviews of
mature projects - a reviewer who did not write the design, a fixed list of
what to check, and a call that ends it, as Kubernetes runs its
[production readiness review](https://github.com/kubernetes/community/blob/master/sig-architecture/production-readiness.md).

`plan-shape.md`, beside this file, is the shape a full plan is held to; a
shape plan is held to the headings it was sent under. The colours, the 🧪
UNTESTED finding, the FINDINGS line, the MUST HAVE and NICE TO HAVE
sections, the blockers, the Design, bycatch and To do tables and "Rules
that keep the tags honest" are `code-review.md`'s, and hold here as written
there; this file says what changes when the thing judged is a plan instead
of a branch.

## A cold read

**The reviewer reads the plan file and the code it describes, never the
conversation that produced them.** A plan is read by people who were not in
its discussion, and the review stands in for them. A line that only makes
sense to someone who was there is a finding: 🟡 when the design holds without
it, 🟠 when a decision rests on it.

**A shape plan is read from a saved copy.** It lives only in chat, so the
session writes its text, word for word, to a file in its scratch directory
before the review starts, and the review reads that file - the same copy a
fresh agent is handed.

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
- **Every new responsibility**: has its owner, state, interface and
  departures, as "Responsibilities" in `clean-code.md` gives them - a shape
  plan's bullets give the owner, the state and any departure - with its
  owner checked against the code that owner already holds. Each break is a
  finding on the section that holds the fix and a row of the Design table:
  a responsibility with no owner or a missing field is **DS1**, an owner
  with two reasons to change **DS2**, a piece of state with two writers
  **DS11**, and a departure nobody named the row of the rule it breaks.
- **Every link to a known architecture**: opened, and read for whether it
  says what the plan says it does.

**What a shape plan leaves out by design** - numbers, incidents, commits
and tests - is no finding; its headings are checked for what they do say.

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

**A plan review has a CR's shape, its sections named for a plan**, so the
two read the same from top to bottom. Each section sits under its own
top-level heading, in this order, below the title
`# Repo <repo> plan <plan> plan review` - `<plan>` the plan's file name, or
`shape plan <its topic>` for a shape plan, and the repo named as a CR's
title names it:

1. `# Overview` - what the plan does, in the bullets a CR's overview gives,
   and the Given line: the plan's file, or the saved copy of a shape plan.
2. `# Design` - the table `code-review.md` gives, each row held against the
   planned design, each Work cell naming the plan section that carries the
   fix, as **S6**. There is no Implementation table: a plan has no lines.
3. `# Sections` - `## In short`, one row per heading of the plan, in its
   own order, and `## In detail`, each section with a finding under
   `### S<n> · Section <n> of <total>: <its heading>`, with its FINDINGS
   line and then the MUST HAVE, UNTESTED and NICE TO HAVE sections as
   `code-review.md` gives a commit. One line after the last names the
   sections with no finding and what was checked in them.
4. `# 🎣 Bycatch` - the table `code-review.md` gives, for what the review
   turned up in the code it read that the plan neither changes nor depends
   on.
5. `# To do` - as `code-review.md` gives it, with `## Before it is built` in
   place of `## Before it merges`; a row that edits the plan reads
   `🔧 Fix (plan)` in its Who cell.
6. `# Summary` - the section calls table for Design and Sections; the plan
   call, its bracket naming what holds the build as a branch call's does;
   the plan's FINDINGS line, counting every section's findings, and its
   Full Assessment in the frame of `assessment.md` - the plan's call as the
   Call, a **Plan** Profile, the plan as it stands with Evidence that its
   design does what it claims, and the Fix Profiles and the `Test 🧪`
   Profile `code-review.md` gives a commit; and last, the line naming the
   review's file.

The In short table:

```
## In short

| # | What the section says | Findings | Call | Blocker |
|---|---|---|---|---|
| **S6** | The fix: a client timeout on the router's pool | 🟠 1 · 🧪 1 | 🔧 Needs fix (two sources for the timeout) | ⛔ Hard: design |
| | **Evidence:** LIKELY · **Size:** medium · **Difficulty:** easy | **Fix 🟠:** one source for the timeout · **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy | | |
```

- **Its rows are the plan's own headings**, numbered **S1**, **S2** in
  plan order: a full plan's sections, as `plan-shape.md` lists them, or the
  headings a shape plan was sent under. The second row of each holds the
  section's Profile and its Fix and Test Profiles, as a commit's does.
- **The section calls**, each with its reason in a few words:
  - **✅ Holds** - nothing in the section holds the build.
  - **🔧 Needs fix (<what>)** - a 🔴 or 🟠 an edit to the section fixes.
  - **🧪 Needs a spike (<the run>)** - no 🔴 or 🟠, and a 🧪 only a run or a
    prototype settles.
  - **❌ Back to design (<why>)** - the section's design fails a concrete
    scenario no edit fixes.
- **A blocker in a plan review** is `⛔ Hard: design` for a break whose fix
  edits the planned design, and the kind of what the fix touches otherwise -
  `test code` for a test the plan must add, `doc` for its wording - as
  "Hard and soft merge blockers" in `code-review.md` gives.

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
