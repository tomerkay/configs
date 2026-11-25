---
name: tkay-code
description: Standards for writing code - the clean-code rules for every line, commit messages and commit boundaries, and where dev versus production deployment material lives in a repo. Use whenever about to write or change code, a chart, a dashboard or config; to fix what a code review found; to commit, amend or write a commit message; to name a git branch; to write or move an installer, a topology file or values, or decide what goes under dev/ versus deploy/; or when unsure whether a comment, mechanism, default or config key is acceptable. It never reviews code, and asks before writing code in a session that reviewed code or loaded a standard for reviewing it, and before a code review in a session that wrote the code or loaded a standard for writing it.
---

# Code standards

The rules that apply to **all** code work are in `references/clean-code.md`,
each with the worked examples behind it. The other references hold the
task-specific standards.

## Read the reference for the task before you start

| Task | Read first |
|---|---|
| Writing or amending any commit message, committing at all, or naming a branch | `references/commits.md`, `references/commit-boundaries.md` and `references/human-readable.md` — **before you type the message** |
| Fixing what a code review found - a CR, an MR's review threads, a review summary | `references/fixing-review-findings.md` — **before the first fix** |
| Running a throwaway test, or handing a tool a file of your own, inside a repo | `references/scratch-in-a-repo.md` |
| Writing or moving deploy tooling, a topology file or values — anything that decides what lives under `dev/` versus `deploy/` | `references/deploy-layout.md` — before creating or moving the file |
| Writing or changing any code, a chart, a dashboard or config, or unsure whether a comment, mechanism, default or config key is acceptable | `references/clean-code.md` and `references/security.md` — **read both in full before the first line** |
| Writing any line into a repo - code, a chart, config, a doc, a test - that could carry a copy, a specific value or a person's setup | `references/copied-stale-and-personal.md` |
| Writing code, or a CR asked for, in a session that may already hold the other | `references/separate-sessions.md` |
| Running a test on code you wrote, or handing that code to a review | `references/test-record.md` — **before the first test run** |

**If you are unsure whether a row applies, read it.** Loading a reference I did
not need costs seconds. Skipping one costs me a bad review or a false commit
message, and git history is permanent.

**Never answer from memory of a reference you have not read this session.** If
you catch yourself recalling how my commit bodies are structured, stop and
read the file. A remembered version of my standards is the same failure as
not having them.

## A structural change states its design before its first line

**A change is structural when it adds a module, a responsibility, state that
outlives a call, or an interface between two components.** A change inside
what exists - a condition, a value, a function body - is not. When unsure
which it is, treat it as structural.

**Before the first line of a structural change that follows no agreed plan,
state its responsibilities in chat**, as "Responsibilities" in
`references/clean-code.md` gives them: a few lines I can correct while
correcting them is still free. It is not a question: the work goes on under
them, and I interrupt when the design is wrong.

**When the design rests on a choice between known architectures, the
change needs a plan**: say so in place of the responsibilities, name the
choice, and wait for my answer before any code.

## Code and its review stay in separate sessions

**This skill writes code; it never reviews it.** Its rules are not a review
standard: with none installed, say that this session has no review standard,
and review nothing by this skill's rules.

**Read `references/separate-sessions.md` before the first line of code, and
whenever a CR is asked for in this session.** It says when writing code
stops for a question because this session reviewed code or loaded a
standard for reviewing it, and when a CR does
because this session wrote the code or has this skill loaded, whatever
skill writes the review.

## The repo's conventions win

**Where the repo you are working in documents a convention, follow the repo,
not these references.** Commit message format, branch names, test style,
comment style: check its `CLAUDE.md` files, its `CONTRIBUTING.md`, its
README and any style guide they point to before the first commit or branch
of the session.

These references fill only what the repo leaves unsaid, topic by topic. A
repo that fixes the commit message format but says nothing about branch
names gets its own commit format and my branch names. Mixing the two is
the point: do not drop a reference wholesale because the repo covers part
of it.

When the repo and a reference disagree, follow the repo and tell me in one
line which rule of mine it overrode; `references/commits.md` names the one
exception.
