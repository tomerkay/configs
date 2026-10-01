---
name: tkay-code
description: Tomer's standards for code reviews (CR), commit messages, and where dev versus production deployment material lives in a repo, plus the worked examples behind his comment / over-engineering / one-source-of-truth / enum rules. Use whenever asked to review code, a branch, a PR or commits; to commit, amend or write a commit message; to write or move an installer, a topology file or values, or decide what goes under dev/ versus deploy/; or when unsure whether a comment, mechanism, default or config key is acceptable.
---

# Tomer's code standards

The rules that apply to **all** code work — comments, over-engineering, one
source of truth, enums — live in my global CLAUDE.md and are always in force.
This skill holds the task-specific standards, and the worked examples behind
those always-on rules.

## Read the reference for the task BEFORE you start

| Task | Read first |
|---|---|
| A code review / CR / "review my branch, PR, commits" | `references/code-review.md` — **before writing a single finding** |
| Writing or amending ANY commit message, or committing at all | `references/commits.md` — **before you type the message** |
| Writing or moving deploy tooling, a topology file or values — anything that decides what lives under `dev/` versus `deploy/` | `references/deploy-layout.md` — before creating or moving the file |
| Unsure whether a comment, mechanism, default or config key is acceptable | `references/code-examples.md` |

**If you are unsure whether a row applies, read it.** Loading a reference I did
not need costs seconds. Skipping one costs me a bad review or a false commit
message, and git history is permanent.

**Never answer from memory of a reference you have not read this session.** If
you catch yourself recalling what my review format is, or how my commit bodies
are structured, STOP and read the file. A remembered version of my standards is
the same failure as not having them.

A CR and a commit almost always travel together — a review whose first
checklist item is the commit message needs `references/commits.md` too. Read
both rather than guessing which half applies.

## How I talk

I talk casually but care deeply about quality: *"be thoruogh af this is fucking
super serious production!!!!"*, *"good luck!!!!!"* (I mean it), *"its ok"* (that
is approval). Match my energy — direct and thorough. Don't be nice if something
is actually wrong, and don't ask permission to *report* something.
