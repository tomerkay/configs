---
name: tkay-writing-plans
description: The shape Tomer wants for a plan document - problem first, one section per commit, reference material below a divider. Use when asked to write, update, re-check or keep alive a plan, design doc, proposal or implementation write-up.
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
2. One section per problem, with the evidence for it
3. The fix
4. The commits
5. **A divider, then reference material** - how to reproduce the numbers, decisions
   already settled, branch state, things found but not chased

Anything I would read once goes below the divider. Say at the top which sections are the
plan and which are reference, so I know where to stop.

## Divide it into commits

Not a pile of edits. One section per commit, each independently correct, deployable, and
leaving the tests passing - so any prefix of the list can ship on its own. For each one:
the subject line, the files, the tests, and **what the commit body has to say**.

Call out whatever a commit touches that is easy to miss: a doc whose wording it
invalidates, a rule it deliberately reverses, a config list it has to join.

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

## Keeping it alive

I will ask you to re-check the plan against the branch, repeatedly. When I do: verify the
specific things the plan depends on, tell me plainly whether anything actually changed,
and only then edit. "Is it ready?" is a yes/no question - lead with the answer.

Keep the chat short. The depth belongs in the document, not in your message about the
document.
