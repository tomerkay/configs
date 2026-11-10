---
name: tkay-review
description: The code review (CR) standard - every finding coloured by severity, MUST HAVE and NICE TO HAVE decided by the colour, the per-commit review shape, the branch overview, the commits and bycatch tables, one CR per repo. Use only when asked for a code review, a CR, a review of a branch, a PR, an MR or commits, a CR asked for on an MR or PR link, or a CR Summary - never while writing code, which the tkay-code skill owns, and never in the session that wrote the code under review.
---

# Code review

**Read `references/code-review.md` before writing a single finding.** It is
the whole standard: what a finding is, how bad each one is, what blocks the
merge, the shape of a commit's review, the branch overview, the commits table,
the bycatch table, and what a CR on an MR link may and may not do.

## This skill is one half of a pair

This skill is handed out together with `tkay-code`, installed beside it under
the same skills directory, and reads three of that skill's references rather
than carrying copies that would drift:

| Read | For |
|---|---|
| `${CLAUDE_SKILL_DIR}/../tkay-code/references/clean-code.md` | what clean code is - every finding is a departure from it |
| `${CLAUDE_SKILL_DIR}/../tkay-code/references/verdict.md` | the calls and fields of every verdict a CR carries |
| `${CLAUDE_SKILL_DIR}/../tkay-code/references/commits.md` | the commit standard a CR judges messages and boundaries by |

Read all three before the first finding. **Never answer from memory of a
reference you have not read this session.**

## Never in the session that writes the code

**A CR runs in a session that did not write the code and has not loaded
`tkay-code`.** Two reasons, and either alone is enough: a review by the
code's author is not independent, and code written with this standard in
context is written to the rubric rather than to the problem. When the code
skill is already loaded in the session, or the session wrote the branch under
review, say so and ask for the review to run in a fresh session; do not
review. The one exemption is a session working on my Claude config itself,
under `~/.claude`: this standard cannot be edited without being read, and
what such a session writes is the rubric, not code the rubric judges, so it
reviews its own staged changes in place.

## The repo's conventions win

**Where the repo documents a convention - commit message format, branch
names, MR description sections, test style, comment style - judge by the
repo, not by these references.** The references fill only what the repo
leaves unsaid. When the two disagree, follow the repo and say in one line
which rule of mine it overrode.
