---
name: tkay-writing-plans
description: The shape for a plan document - problem first, one section per commit, reference material below a divider - and what to stop for while implementing one. Use when asked to write, update, re-check or keep alive a plan, design doc, proposal or implementation write-up, and when implementing an agreed plan.
---

# Writing Plans

When I ask for a plan document, this is the shape I want. Write it to `/tmp` or a
scratchpad unless I name somewhere else.

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
4. The fix
5. The commits
6. **Questions and answers** - see below
7. **TBD** - see below
8. **A divider, then reference material** - how to reproduce the numbers, decisions
   already settled, branch state, things found but not chased

Anything I would read once goes below the divider. Say at the top which sections are the
plan and which are reference, so I know where to stop.

## TBD holds only what we agreed to defer

The TBD section lists work I agreed, with you, to leave out of this plan: a follow-up,
a cleanup after it ships, a decision we postponed on purpose. Each entry says what and
when or why later.

**Never add a TBD entry on your own.** Something you find that this plan does not do is
a finding: it goes below the divider, and you raise it with me. It moves to TBD only
after I agree to defer it. A TBD you invented reads as a commitment I never made.

## Divide it into commits

Not a pile of edits. One section per commit, each independently correct, deployable, and
leaving the tests passing - so any prefix of the list can ship on its own. For each one:
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

Add every question I ask during the review once it is answered, so the section grows
with the review. Answer with the current plan, never with how we got there: a question
whose answer changed the plan is answered as the plan now stands.

## Rules that keep a plan usable

- **No `§`.** Write "Section 4". Same for any notation I have to stop and decode.
- **Cite commits by subject line, never by hash.** I rebase constantly - every hash in a
  plan goes stale within a day. Give me `git log --oneline --grep '<subject>'` instead.
- **Every number must be reproducible.** Put the exact query beside it and name the data
  source. A number I cannot re-derive is one I cannot trust a week later.
- **Measurement windows expire.** Say so, and give the recipe for picking a fresh one.
- **Say what is NOT a problem.** If you checked something and it is fine, write that down
  so I stop wondering about it.
- **Name the decisions that are mine** and ask them one at a time, not as a wall.
- **Flag what rests on an inference rather than a measurement**, say what would falsify
  it, and if a cheap check exists, make it a step in the plan. Do not let a chain of
  reasoning quietly become a stated fact - I will press on exactly that.

## Executing a plan

Implementing a plan is where its holes show: a race nobody traced, an input that does
not exist, an assumption the code contradicts. **When you find a hole or a break in the
plan's architecture, stop and ask me before you write more code on top of it.** Lay it
out as a concrete scenario - the state, the sequence, what goes wrong - then give me
the options with your recommendation, and wait.

That stop is for what needs a discussion: a flaw in the design, a fix that changes how
components interact, adds state or a read, or reverses a decision the plan settled.
A bug you can fix inside the agreed design - a wrong comparator, a missed condition, an
off-by-one - is not a stop: fix it and name it in your next message.

**Every decision made while executing updates the plan, without being asked.** A hole
we settled, an option I picked, a commit dropped, merged or split, a scope change, a
fix that turned out to change behavior the plan describes: the plan is edited in the
same pass as the decision, before the next piece of code. Change the sections it
touches - design, commits, risks, decisions - and add a question and answer when the
reader will ask why. The plan must describe the branch as it stands, so the reviewer
never meets a plan the code already contradicts.

## Keeping it alive

I will ask you to re-check the plan against the branch, repeatedly. When I do: verify the
specific things the plan depends on, tell me plainly whether anything actually changed,
and only then edit. "Is it ready?" is a yes/no question - lead with the answer.

Keep the chat short. The depth belongs in the document, not in your message about the
document.
