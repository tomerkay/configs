---
name: tkay-code
description: Standards for writing code - the clean-code rules for every line, commit messages and commit boundaries, and where dev versus production deployment material lives in a repo. Use whenever about to write or change code, a chart, a dashboard or config; to make any glab call - reading a GitLab MR, its review threads or its CI, or uploading a file to GitLab; to commit, amend or write a commit message; to write an MR or PR description; to create or name a git branch; to write or move an installer, a topology file or values, or decide what goes under dev/ versus deploy/; to take screenshots of UI work; or when unsure whether a comment, mechanism, default or config key is acceptable. A code review is the tkay-review skill's, never this one's.
hooks:
  PreToolUse:
    - matcher: "Skill|Read"
      hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/skill-clash.py"'
---

# Code standards

The rules that apply to **all** code work are in `references/clean-code.md`,
each with the worked examples behind it. The other references hold the
task-specific standards.

## Read the reference for the task before you start

| Task | Read first |
|---|---|
| Anything on a GitLab MR - its review threads, its pipeline, a job log - or any `glab` call | `references/gitlab.md` — **before the first glab call** |
| Writing or amending any commit message, or committing at all | `references/commits.md` — **before you type the message** |
| Running a throwaway test, or handing a tool a file of your own, inside a repo | `references/scratch-in-a-repo.md` |
| The first change in a repo, or creating, naming or deleting a branch | `references/branches.md` — **before the first change** |
| Writing an MR or PR description | `references/mr-description.md` — **before you look for the MR** |
| Writing or moving deploy tooling, a topology file or values — anything that decides what lives under `dev/` versus `deploy/` | `references/deploy-layout.md` — before creating or moving the file |
| Writing or changing any code, a chart, a dashboard or config, or unsure whether a comment, mechanism, default or config key is acceptable | `references/clean-code.md` and `references/security.md` — **read both in full before the first line** |
| Writing any line into a repo - code, a chart, config, a doc, a test - that could carry a specific value or a person's setup | `references/stale-and-personal.md` |

**If you are unsure whether a row applies, read it.** Loading a reference I did
not need costs seconds. Skipping one costs me a bad review or a false commit
message, and git history is permanent.

**Never answer from memory of a reference you have not read this session.** If
you catch yourself recalling how my commit bodies are structured, stop and
read the file. A remembered version of my standards is the same failure as
not having them.

## Screenshots of UI work show every state the change touches

**When I ask for screenshots of UI work, every state whose rendering the
change touches gets a screenshot of its own** - each variant of a changed
component, and each condition it renders differently in: empty, loading,
error, populated, disabled, expanded, a value long enough to wrap or
truncate. Find them in the diff before the first shot: every branch the
change adds or edits in what renders - a condition, a variant, a prop - is
a state, and a style it edits touches every state that style applies to. A
state the change leaves as it was gets none.

- **Each screenshot is captioned with the state it shows**, so a missing
  state shows in the list of captions.
- **What the change touched is boxed in red**, so a reader sees at a glance
  where to look. Before the shot, outline each changed element on the page
  itself - `outline: 3px solid red` with an `outline-offset`, which moves
  nothing on the page - and take the outline off after; a UI that is not a
  web page gets the box drawn on the image. A box goes on what the change
  added or altered, never on the whole screen.
- **A state you cannot reach is named, never skipped** - no data that
  triggers it, a backend you cannot make fail: say which state has no
  screenshot and what it takes to reach it.

## A code review is another skill, and another session

**This skill writes code; it never reviews it.** The CR standard lives in
the `tkay-review` skill, handed out together with this one, which carries
`references/clean-code.md` and `references/commits.md` too. The two belong in separate sessions:
code written with the review rubric in context is written to the rubric,
and a review by the code's author is not independent. When asked for a CR in
a session that has this skill loaded, load the review skill anyway; it says
how its CR warns that it is not independent. The hook in this skill's
frontmatter asks before the review skill loads beside it.

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
line which rule of mine it overrode; `references/commits.md` names the one
exception.
