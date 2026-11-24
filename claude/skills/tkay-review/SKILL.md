---
name: tkay-review
description: The code review (CR) standard - every finding coloured by severity, MUST HAVE and NICE TO HAVE decided by the colour, the per-commit review shape, the CR's sections from the overview to the To do list, one CR per repo. Use only when asked for a code review, a CR, a review of a branch, a PR, an MR or commits, a CR asked for on an MR or PR link, a CR Digest, a CR Brief or a CR Summary, a plan review of a shape plan or a full plan - also called a design review, a DR or a plan CR - or a doc review of a change to markdown docs - never while writing code. In a session that wrote what it would review, or loaded a standard for writing it, it asks before it is opened whether to review here, in a fresh agent or in a fresh session, and once it has reviewed, it asks before that kind of work is written there.
hooks:
  Stop:
    - hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/cr-shape.py"'
---

# Code review

**Read `references/code-review.md` before writing a single finding.** It is
the whole standard: what a finding is, how bad each one is, what blocks the
merge, the CR's sections from the overview to the To do list, the shape of
a commit's review, the views of a CR, and what a CR on an MR link may
and may not do.

**A plan review reads `references/plan-review.md` as well**, before its first
finding: it says what changes when the thing judged is a plan, not a branch.
A design review, a DR and a plan CR are the same review by other names.

**A doc review reads `references/doc-review.md` as well**, before its first
finding: it is the CR with the sections that judge running code cut out,
and it says when a change gets one.

## Shared references

The references below are shared with other skills of mine and kept in this
skill's own `references/` so it works installed alone:

| Read | For |
|---|---|
| `references/separate-sessions.md` | when a review stops for a question because this session wrote the work or loaded a standard for writing it, and when work stops because it wrote a review or loaded a standard for reviewing it |
| `references/clean-code.md` | every review but a doc review: what clean code is - every code finding is a departure from it |
| `references/security.md` | every review but a doc review: the security questions every code change is asked |
| `references/assessment.md` | the frame every assessment in a CR is written in |
| `references/commit-boundaries.md` | how a branch is cut into commits, which a CR judges each commit's boundaries by |
| `references/answers.md` | how an answer, a finding included, is held to the truth |
| `references/human-readable.md` | the plain words every line of a review is written in |
| `references/numbered-lists.md` | how every list and table in a CR is numbered |
| `references/severity.md` | the four colours a finding carries, and the Fix Profile |
| `references/bycatch.md` | the bycatch table, its calls, and which session rows it carries |
| `references/plan-shape.md` | a plan review only: the shape it holds a plan to |
| `references/writing-mds.md` | where a fact goes and how a doc points, for the docs in any change |
| `references/copied-stale-and-personal.md` | the rules asked of every line a change adds to a doc |
| `references/questions.md` | when a reference above names it: how a proposal or a question that stops a reply is written |
| `references/issue-tree.md` | when a reference above names it: the closing a session gives once nothing is open |
| `references/reading-list.md` | when a reference above names it: how a reply to a message about several things opens |

Read every one before the first finding, but for a row that names the
reviews it is for, which is read only before those, and a row read when a
reference names it, which is read then. **Never answer from memory of a
reference you have not read this session.**

The hook in this skill's frontmatter checks the shape of every assessment
and table the CR carries once the skill is loaded, and sends a reply back
once when one breaks it. **A CR sent back is corrected, never repeated**:
the next reply is one line saying what was wrong and only the lines or
rows that change, each under the heading or the row number it belongs to,
and the CR's file gets the same fix.

## The work and its review stay in separate sessions

**Read `references/separate-sessions.md` before the first finding of any
review, and before any code, plan or doc is written in a session that has
written a review or loaded a standard for reviewing it.** It holds the
questions each crossing stops for and the one exemption, judged by what
the session did, whatever skills wrote the work.

## A CR writes out fixes and never makes them

**A CR changes no file, and never offers to.** Every fix is written out
under its finding and left for me - no "want me to fix it?", no fix as a
next step. A fix I ask for anyway is code after a CR, and
`references/separate-sessions.md` asks its question first. A plan review
edits no plan, and a doc review no doc, on the same terms.

## Every CR is also a file

**Every CR is written to a new markdown file as well as to the chat**, in
a scratch directory that outlives the session, never in the repo under
review. The file is `cr-<n>.md`, the next free number in that directory,
so no CR overwrites another: the review after a round of fixes is a new
CR and a new file, and so is a CR Digest, a CR Brief or a CR Summary. A
CR over several repos is one file per repo. Each CR in chat ends, under its To
do, with the ending `references/code-review.md` gives, whose last line
names its file by its full path:

```
**CR file:** <full path>
```

A plan review is a file the same way, named `plan-review-<n>.md`, and its
line reads `**Plan review file:**`; a doc review is `doc-review-<n>.md`, and
its line `**Doc review file:**`.

## The repo's conventions win

**Where the repo documents a convention - how commits are cut, MR
description sections, test style, comment style - judge by the
repo, not by these references.** The references fill only what the repo
leaves unsaid. When the two disagree, follow the repo and say in one line
which rule of mine it overrode.
