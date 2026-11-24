---
name: tkay-mr
description: Standards for an MR or PR page and for GitLab from the host - the title and description, screenshots of UI work, and every glab read and upload. Use when writing an MR or PR title or description, adding screenshots to one, taking screenshots of UI work, or making any glab call - reading an MR, its review threads, its pipeline or a job log, or uploading a file to GitLab.
---

# MR pages and GitLab

## Read the reference for the task before you start

| Task | Read first |
|---|---|
| Anything on a GitLab MR - its review threads, its pipeline, a job log - or any `glab` call | `references/gitlab.md` — **before the first glab call** |
| Writing an MR or PR title or description, or adding screenshots to it | `references/mr-page.md` and `references/human-readable.md` — **before you look for the MR** |
| Writing a note on an MR or PR | `references/human-readable.md` — **before the first word of it** |
| A Go CLI, `glab` among them, fails TLS with `OSStatus -26276` inside the sandbox | `references/go-tls-in-sandbox.md` |

**Never answer from memory of a reference you have not read this session.**
A remembered version of my standards is the same failure as not having them.

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

## The repo's conventions win

**Where the repo documents an MR or PR convention - a description
template, its sections, a title format - follow the repo, not these
references.** Check its `CLAUDE.md` files, its `CONTRIBUTING.md`, its
README and any MR template before the first MR of the session. These
references fill only what the repo leaves unsaid, and when the two
disagree, follow the repo and tell me in one line which rule of mine it
overrode.
