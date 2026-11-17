---
name: tkay-review
description: The code review (CR) standard - every finding coloured by severity, MUST HAVE and NICE TO HAVE decided by the colour, the per-commit review shape, the branch overview, the commits and bycatch tables, one CR per repo. Use only when asked for a code review, a CR, a review of a branch, a PR, an MR or commits, a CR asked for on an MR or PR link, or a CR Summary - never while writing code, which the tkay-code skill owns. In the session that wrote the code under review it still runs, and opens with a warning that the review is not independent.
hooks:
  PreToolUse:
    - matcher: "Skill|Read"
      hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/skill-clash.py"'
  Stop:
    - hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/cr-shape.py"'
---

# Code review

**Read `references/code-review.md` before writing a single finding.** It is
the whole standard: what a finding is, how bad each one is, what blocks the
merge, the shape of a commit's review, the branch overview, the commits table,
the bycatch table, and what a CR on an MR link may and may not do.

## Shared references

Four references are shared with other skills of mine and kept in this
skill's own `references/` so it works installed alone:

| Read | For |
|---|---|
| `references/clean-code.md` | what clean code is - every finding is a departure from it |
| `references/security.md` | the security questions every change is asked |
| `references/assessment.md` | the frame every assessment in a CR is written in |
| `references/commits.md` | the commit standard a CR judges messages and boundaries by |

Read all four before the first finding. **Never answer from memory of a
reference you have not read this session.**

The hook in this skill's frontmatter checks the shape of every assessment
the CR carries once the skill is loaded, and sends a reply back once when
one breaks it.

## The author's own session warns, and reviews anyway

**A CR belongs in a session that did not write the code and has not loaded
`tkay-code`.** Two reasons, and either alone is enough: a review by the
code's author is not independent, and code written with this standard in
context is written to the rubric rather than to the problem.

**When I ask for one in a session that wrote the branch, or has the code
skill loaded, write the CR, never a refusal.** It opens with one bold ⚠️
line, above everything else in it, that names what holds - the session
wrote the branch, has the code skill loaded, or both - and says the review
is not independent, so I decide whether to rerun it in a fresh session.
The case that taught it, a CR asked for in the session that wrote the
branch:

```
❌ I can't review this branch here: this session wrote it, and it has
   tkay-code loaded. Open a fresh session and ask it for this:
   CR branch <branch>
✅ ⚠️ **Not an independent CR: this session wrote the branch and has
   tkay-code loaded.** For one, ask a fresh session for `CR branch <branch>`.
   <the CR>
```

The one exemption is a session working on these skills themselves, whose
working directory is inside the git repo that holds them, or inside a repo
that marks itself as theirs with a `.claude-skills-repo` file at its root:
this standard cannot be edited without being read, and what such a session
writes is the rubric, not code the rubric judges, so it reviews its own
staged changes in place, with no ⚠️ line, and a fix there gets no
warning before it.

The hook in this skill's frontmatter asks before `tkay-code` loads beside
it, except in such a session.

## A CR writes out fixes and never makes them

**A CR changes no file, and never offers to.** Every fix is written out
under its finding and left for me - no "want me to fix it?", no fix as a
next step. A session that fixes what it reviewed ties the review to the
fix, and the review is no longer independent of the code it judges.

**When I ask for a fix anyway, the reply is this line and nothing after
it**, whether or not a hook or another skill asks as well:

```
⚠️ Fixing here ties this review to the fix: the fix would be written by the session that wrote the CR, and the CR would no longer be independent of the code it judges. Are you sure you want it here and not in a fresh session that keeps the two apart?
```

It is a question in a shape of its own, and it stops the reply: the fix is
made only on my yes, and a no leaves every file as it is.

## Every CR is also a file

**Every CR is written to a new markdown file as well as to the chat**, in
a scratch directory that outlives the session, never in the repo under
review. The file is `cr-<n>.md`, the next free number in that directory,
so no CR overwrites another: the review after a round of fixes is a new
CR and a new file, and so is a CR Summary. A CR over several repos is one
file per repo. Each CR in chat ends, under its bycatch table, with one
line that names its file by its full path:

```
**CR file:** <full path>
```

## The repo's conventions win

**Where the repo documents a convention - commit message format, branch
names, MR description sections, test style, comment style - judge by the
repo, not by these references.** The references fill only what the repo
leaves unsaid. When the two disagree, follow the repo and say in one line
which rule of mine it overrode.
