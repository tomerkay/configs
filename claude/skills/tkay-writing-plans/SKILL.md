---
name: tkay-writing-plans
description: The shape for a plan document - problem first, a design grounded in a known architecture, one section per commit, reference material below a divider - and what to stop for while implementing one. Use when asked to write, update, re-check or keep alive a plan, design doc, proposal or implementation write-up, and when implementing an agreed plan.
---

# Writing Plans

When I ask for a plan document, this is the shape I want. Write it to a directory that
survives the session unless I name somewhere else - never `/tmp` or a session
scratchpad, which can vanish while the plan is still in use.

## The problem comes first. Always.

**Open with what is broken, in plain language.** Not the branch, not commit hashes, not
what you verified, not caveats about your method. I cannot evaluate any of that before I
know what we are fixing, and if I have to scroll to find the problem, the document has
failed no matter how correct it is.

Structure:

1. What the thing does and what is broken - a few lines
2. **Glossary** - every term the plan gives a specific meaning, one line each, so a
   word means one thing from the first section to the last. Terms that a reader of the
   code would mix up go here first: two layers with similar names, a count that has
   two sources, a word the codebase uses loosely.
3. One section per problem, with the evidence for it
4. The fix, opening with the known architecture it follows - see below
5. **Known incidents** - see below
6. The commits
7. **Questions and answers** - see below
8. **TBD** - see below
9. **A divider, then reference material** - how to reproduce the numbers, decisions
   already settled, branch state, things found but not chased

Anything I would read once goes below the divider. Say at the top which sections are the
plan and which are reference, so I know where to stop.

## Start from a known architecture

**The idiomatic architecture is the core motivation of every design discussion.** A
design is chosen from known architectures out in the world, not invented: a pattern
of a mature system, a documented controller or protocol, the way a well-known
project handles the same failure. Inventing a mechanism is a cost the plan has to
justify; following a known one hands the reader its documentation, its failure modes
and its track record.

**Without it, the design is built from the symptom outward.** Each hole found gets
its own patch, each patch opens the next hole, and the result is a hand-made copy of
a mechanism some mature system already ships - with none of its documentation and
all of its early bugs. Starting from the architecture means understanding the whole
problem before the first decision, so every later decision is placed in a design
that already has a place for it. Proper preparation and planning prevent piss poor
performance.

**Search first, then discuss it with me, before the design is written.** Look
outward - the documentation and source of the systems that solved the same problem,
not only this codebase - and bring me what you found:

- **The candidates**: each known architecture that is relevant, with a link, and how
  it matches and does not match our needs.
- **Which one you recommend**, and why it suits us better than the others.
- **When none is relevant, say so** and say what you searched, so I can point you
  at one you missed. Never present an invented design as if no search were needed.

The choice of architecture is mine, like any other decision in the plan. Every later
question in the discussion - a race, a failure mode, a limit - is argued from that
reference first: what it does in the same case, and whether we follow it.

Once it is chosen, the plan carries it:

- **The fix opens by naming it**: "this follows X, because it suits us in A and B",
  with a link to where X is documented - or, when none fit, the ones considered.
- **Every decision names the design it resembles and the approach it rejected**:
  "Z resembles X's design; over W it gives <advantage>, and it costs
  <disadvantage>." In a decision table, that sentence is the reason column.
- **A departure from the reference is stated where it happens**, with why: a state
  the reference keeps reversible that this design makes final, a check it runs that
  this one skips.
- **The same holds for a decision taken while implementing** (see "Executing a
  plan"): a fix that changes the design names the known design it moves toward.

## Known incidents, each with a status

When the plan replaces, rewrites or fixes something that has failed before, it lists
every incident it knows about - from the code's comments and tests, the rules a team
wrote after an outage, commit bodies, postmortems, tickets - and says what the change
does to each. The section is there whether the change is a redesign, a feature or a
bug fix; an incident the plan never names is one the reader assumes it handles.

**The section opens with a summary table**: one row per incident, numbered, with
the incident, its status, and in one line how it is fixed or why it is not. A
reader sees the state of every incident before reading any of them.

**Then one block per incident, in a fixed shape, its heading carrying the status**,
so the answer is never buried in a paragraph:

- **The status**, one word, in the heading: **Solved** (the cause cannot occur by
  construction), **Mitigated** (it can still occur and is handled another way),
  **Not solved** (it can still occur and nothing new handles it), or **Gone** (the
  mechanism that failed no longer exists). No other word.
- **What happened**: the symptom, with the numbers, the date and the system when the
  source has them. A detail the source does not state is written as not stated, never
  filled in.
- **Cause**, in the old code.
- **Fix**: the mechanism in the new code, naming the function, the rule or the
  section that carries it, and the test that pins it. For **Not solved**, this line
  is **Why not**: what still lets it happen, and what covers it meanwhile - a TBD
  entry, a known gap, an operator action. For **Gone**, it names the mechanism that
  no longer exists.
- **Source**: the file and the function or test, or the commit subject.

**A status is a claim about the new code, so it is checked against the new code, not
taken from the plan's own prose.** Solved without a named mechanism is not a status
it may claim.
A not solved is written as plainly as a solved: it is the entry the reviewer most needs,
and it pairs with the risks section or a TBD entry that I agreed to.

## TBD holds only what we agreed to defer

The TBD section lists work I agreed, with you, to leave out of this plan: a follow-up,
a cleanup after it ships, a decision we postponed on purpose. Each entry says what and
when or why later.

**Never add a TBD entry on your own.** Something you find that this plan does not do is
a finding: it goes below the divider, and you raise it with me. It moves to TBD only
after I agree to defer it. A TBD you invented reads as a commitment I never made.

## Divide it into commits

Not a pile of edits. One section per commit, each independently correct and leaving the
tests passing - so any prefix of the list is correct on its own. Where the repo requires a
version bump, the bump is the last commit and the one that releases. For each one:
the subject line, the files, the tests, and **what the commit body has to say**.

Call out whatever a commit touches that is easy to miss: a doc whose wording it
invalidates, a rule it deliberately reverses, a config list it has to join.

## End the plan with questions and answers

A design plan gets read by people who were not in the review: the component's owner,
the reviewer, the next engineer. Before the divider, add a "Questions and answers"
section with the questions the review raised and the ones those readers will ask -
why not the obvious alternative, what happens in a race, what breaks in the next
planned feature. Group them by topic. Answer each in a few sentences with a concrete
example where one helps, and point to the section that holds the detail.

**A question belongs here only if a design reviewer would ask it.** Judge each one
yourself, from the questions I ask during the review and from the decisions taken
while executing, and never ask me whether to add one. The test: would someone reading
the plan cold, who was not in the discussion, ask it and be better off for the
answer? A decision's "why this and not the obvious alternative", a race, a failure
mode and a limit pass. A question I asked only to understand something for myself,
or one whose answer is common knowledge, stays out.

Answer with the current plan, never with how we got there: a question whose answer
changed the plan is answered as the plan now stands.

## Every line is for a human reader

A plan is read by a person who wants to know what is broken, what we will do and why.
A line that does not help them with that is noise, and noise buries the lines that
matter. Cut it:

- **Dates and timestamps** - "as of", "verified on", "last updated", a date heading a
  section. A date says when a sentence was typed, not whether it is still true. Keep
  one only when the date is itself the fact: when an incident happened, a deadline,
  the window a measurement covers.
- **The plan's own history** - "v2", "updated after review", "this section used to
  say". The plan describes the design as it stands; how it got there is the commit
  bodies' and the chat's.
- **Narration of the work** - "I checked", "as discussed", "per your request", "after
  reading the code". State the finding. A method worth keeping is a reproduction
  recipe, and it goes below the divider.
- **Machine coordinates** - an absolute path into someone's machine, a scratch path,
  a line number. Name the file relative to the repo and the function in it.
- **Raw output** - a pasted log, a whole command output, a dumped config. Quote the
  line that proves the point and give the command that produces the rest.

The test: would a reader who was not in the session lose anything if the line were
gone? If not, cut it.

## Rules that keep a plan usable

- **No `§`.** Write "Section 4". Same for any notation I have to stop and decode.
- **Cite commits by subject line, never by hash.** I rebase constantly - every hash in a
  plan goes stale within a day. Give me `git log --oneline --grep '<subject>'` instead.
- **Every number must be reproducible.** Put the exact query beside it and name the data
  source. A number I cannot re-derive is one I cannot trust a week later.
- **Measurement windows expire.** Say so, and give the recipe for picking a fresh one.
- **Say what is NOT a problem.** If you checked something and it is fine, write that down
  so I stop wondering about it.
- **Name the decisions that are mine** and ask them.
- **Flag what rests on an inference rather than a measurement**, say what would falsify
  it, and if a cheap check exists, make it a step in the plan. Do not let a chain of
  reasoning quietly become a stated fact - I will press on exactly that.

## Call it when planning turns into a rabbit hole

**Be the third person in the design review who says "time to try it".** Implementing
and testing are cheap now - a prototype that checks a design end to end often takes
minutes - so a question a test can answer is not argued for another round. Watch the
discussion for the signs, and say so unprompted the moment one shows, mid-discussion
included:

- the same question comes back without new evidence
- two options are argued on how they would behave, and running them would show it
- hypothetical edge cases pile up faster than they are settled
- the plan grows sections nobody will read before the code exists

Name the question, the experiment that answers it - a throwaway prototype, a test, a
run on a dev cluster - and roughly how long it takes. The experiment is a spike: its
code is thrown away and what it shows goes back into the plan; a spike can also pick
between candidate architectures. Once the architecture is chosen and the questions
left are all of that kind, propose starting on the first commit; "Executing a plan"
is what makes that safe, because a hole found while implementing stops the work and
goes back into the plan.

A question whose wrong answer is expensive to undo - a data migration, a wire format
other systems will depend on, a change customers see - is still settled before it
ships. An experiment is often the fastest way to settle it: run it against a copy, a
dev cluster or a scratch branch, never against production.

## Executing a plan

Implementing a plan is where its holes show: a race nobody traced, an input that does
not exist, an assumption the code contradicts. **When you find a hole or a break in the
plan's architecture, stop and ask me before you write more code on top of it.** Lay it
out as a concrete scenario - the state, the sequence, what goes wrong - then give me
the options with your recommendation, and wait. Search for how known architectures
handle the same case first, and anchor each option in one where one fits, as "Start
from a known architecture" says.

That stop is for what needs a discussion: a flaw in the design, a fix that changes how
components interact, adds state or a read, or reverses a decision the plan settled.
A bug you can fix inside the agreed design - a wrong comparator, a missed condition, an
off-by-one - in the code this plan's commits write is not a stop: fix it and name it in
your next message. A bug in code the plan does not touch is a finding: report it, do not
fix it.

**Every decision made while executing updates the plan, without being asked**, in
the shape "Start from a known architecture" gives a decision. A hole we settled, an
option I picked, a commit dropped, merged or split, a scope change, a fix that turned
out to change behavior the plan describes: the plan is edited in the same pass as the
decision, before the next piece of code. Change the sections it touches - design,
commits, risks, decisions - and add a question and answer when the reader will ask
why. The plan must describe the branch as it stands, so the reviewer never meets a
plan the code already contradicts.

## Committing a plan to a repo

Committed to a repo, a plan becomes a record read by someone who was not in the
review. It names a setting in force by its owner, the key and the file, never by
its value. It keeps a measurement only as the reason for a decision, with the
query that reproduces it and no date: git history dates it. Working notes go:
instructions to whoever executes it, people's names, branch names, a section on
running things on one machine.

## Keeping it alive

I will ask you to re-check the plan against the branch, repeatedly. When I do: verify the
specific things the plan depends on, tell me plainly whether anything actually changed,
and only then edit. "Is it ready?" is a yes/no question - lead with the answer.

Keep the chat short. The depth belongs in the document, not in your message about the
document.
