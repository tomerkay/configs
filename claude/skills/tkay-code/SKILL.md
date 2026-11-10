---
name: tkay-code
description: Standards for writing code - the clean-code rules for every line, commit messages and commit boundaries, the verdict a judgement opens with, and where dev versus production deployment material lives in a repo. Use whenever about to write or change code, a chart, a dashboard or config; to propose a change or give a verdict on one, an option or an idea; to make any glab call - reading a GitLab MR, its review threads or its CI, or uploading a file to GitLab; to commit, amend or write a commit message; to write an MR or PR description; to create or name a git branch; to write or move an installer, a topology file or values, or decide what goes under dev/ versus deploy/; or when unsure whether a comment, mechanism, default or config key is acceptable. A code review is the tkay-review skill's, never this one's.
---

# Code standards

The rules that apply to **all** code work are in `references/clean-code.md`,
each with the worked examples behind it. The other references hold the task-specific
standards.

## Read the reference for the task BEFORE you start

| Task | Read first |
|---|---|
| Anything on a GitLab MR - its review threads, its pipeline, a job log - or any `glab` call | `references/gitlab.md` — **before the first glab call** |
| Writing or amending ANY commit message, or committing at all | `references/commits.md` — **before you type the message** |
| Creating or naming a branch | `references/commits.md` — "Branch Names", **before you pick the name** |
| Writing an MR or PR description | `references/mr-description.md` — **before you look for the MR** |
| Writing or moving deploy tooling, a topology file or values — anything that decides what lives under `dev/` versus `deploy/` | `references/deploy-layout.md` — before creating or moving the file |
| Writing or changing code, or unsure whether a comment, mechanism, default or config key is acceptable | `references/clean-code.md` |
| Proposing a change, or giving a verdict on a change, an option or an idea | `references/verdict.md` — **before you write the verdict** |

**If you are unsure whether a row applies, read it.** Loading a reference I did
not need costs seconds. Skipping one costs me a bad review or a false commit
message, and git history is permanent.

**Never answer from memory of a reference you have not read this session.** If
you catch yourself recalling how my commit bodies are structured, STOP and
read the file. A remembered version of my standards is the same failure as
not having them.

## A code review is another skill, and another session

**This skill writes code; it never reviews it.** The CR standard lives in
the `tkay-review` skill, handed out together with this one, which reads
`references/clean-code.md`, `references/verdict.md` and
`references/commits.md` from here. The two are never loaded in one session:
code written with the review rubric in context is written to the rubric,
and a review by the code's author is not independent. When asked for a CR in
a session that has this skill loaded, say so and ask for the review to run
in a fresh session.

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
line which rule of mine it overrode. The one exception is a repo rule that a
commit must carry no body: quote it to me and ask before the first commit,
rather than following it.
