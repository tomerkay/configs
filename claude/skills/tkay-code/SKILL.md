---
name: tkay-code
description: Standards for code reviews (CR), commit messages, and where dev versus production deployment material lives in a repo, plus the comment / over-engineering / one-source-of-truth / enum rules. Use whenever asked to review code, a branch, a PR or commits; to read a GitLab MR, its review threads or its CI through glab; to commit, amend or write a commit message; to create or name a git branch; to write or move an installer, a topology file or values, or decide what goes under dev/ versus deploy/; or when unsure whether a comment, mechanism, default or config key is acceptable.
---

# Code standards

The rules that apply to **all** code work — comments, over-engineering, one
source of truth, enums — are in `references/code-examples.md`, each with the
worked examples behind it. The other references hold the task-specific
standards.

## Read the reference for the task BEFORE you start

| Task | Read first |
|---|---|
| A code review / CR / "review my branch, PR, commits" | `references/code-review.md` — **before writing a single finding** |
| Anything on a GitLab MR - its review threads, its pipeline, a job log - or any `glab` call | `references/gitlab.md` — **before the first glab call** |
| Writing or amending ANY commit message, or committing at all | `references/commits.md` — **before you type the message** |
| Creating or naming a branch | `references/commits.md` — "Branch Names", **before you pick the name** |
| Writing or moving deploy tooling, a topology file or values — anything that decides what lives under `dev/` versus `deploy/` | `references/deploy-layout.md` — before creating or moving the file |
| Writing or changing code, or unsure whether a comment, mechanism, default or config key is acceptable | `references/code-examples.md` |

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

## The repo's conventions win

**Where the repo you are working in documents a convention, follow the repo,
not these references.** Commit message format, branch names, MR description
sections, test style, comment style: check its `CLAUDE.md` files, its
`CONTRIBUTING.md`, its README and any style guide they point to before the
first commit, branch or MR of the session.

These references fill only what the repo leaves unsaid, topic by topic. A
repo that fixes the commit message format but says nothing about the MR
description gets its own commit format and my description standard. Mixing
the two is the point: do not drop a reference wholesale because the repo
covers part of it.

When the repo and a reference disagree, follow the repo and tell me in one
line which rule of mine it overrode.
