---
name: tkay-review
description: The code review (CR) standard - every finding coloured by severity, MUST HAVE and NICE TO HAVE decided by the colour, the per-commit review shape, the CR's sections from the overview to the To do list, one CR per repo. Use only when asked for a code review, a CR, a review of a branch, a PR, an MR or commits, a CR asked for on an MR or PR link, a CR Digest, a CR Brief or a CR Summary, a plan review of a full plan, or a doc review of a change to markdown docs - never while writing code, which the tkay-code skill owns. In a session that wrote the code or the plan under review, it asks first whether to review there, and once it has reviewed, it asks before any code is written there.
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

**A doc review reads `references/doc-review.md` as well**, before its first
finding: it says what changes when the thing judged is a change to markdown
docs, not to code, and when a change gets one.

## Shared references

The references below are shared with other skills of mine and kept in this
skill's own `references/` so it works installed alone:

| Read | For |
|---|---|
| `references/clean-code.md` | what clean code is - every finding is a departure from it |
| `references/security.md` | the security questions every change is asked |
| `references/assessment.md` | the frame every assessment in a CR is written in |
| `references/commits.md` | the commit standard a CR judges messages and boundaries by |
| `references/answers.md` | how an answer, a finding included, is held to the truth |
| `references/numbered-lists.md` | how every list and table in a CR is numbered |
| `references/severity.md` | the four colours a finding carries, and the Fix Profile |
| `references/bycatch.md` | the bycatch table, its calls, and which session rows it carries |
| `references/plan-shape.md` | a plan review only: the shape it holds a plan to |
| `references/design-note.md` | a plan review only: the design note a plan gives each new responsibility |
| `references/writing-mds.md` | a doc review only: where a fact goes and how a doc points |
| `references/copied-stale-and-personal.md` | a doc review only: the rules it asks of every added line |
| `references/questions.md` | when a reference above names it: how a proposal or a question that stops a reply is written |
| `references/issue-tree.md` | when a reference above names it: the closing a session gives once nothing is open |
| `references/reading-list.md` | when a reference above names it: how a reply to a message about several things opens |

Read every one before the first finding, but for a row that names the one
review it is for, which is read before that review's, and a row read when a
reference names it, which is read then. **Never answer from memory of a
reference you have not read this session.**

The hook in this skill's frontmatter checks the shape of every assessment
and table the CR carries once the skill is loaded, and sends a reply back
once when one breaks it. **A CR sent back is corrected, never repeated**:
the next reply is one line saying what was wrong and only the lines or
rows that change, each under the heading or the row number it belongs to,
and the CR's file gets the same fix.

## Code and a CR stay in separate sessions

**A CR belongs in a session that did not write the code and has not loaded
`tkay-code`, and code belongs in a session that wrote no CR.** Two
reasons, and either alone is enough: a review by the code's author is not
independent, and code written with this standard in context is written to
the rubric rather than to the problem.

**So each crossing stops for my answer, and the reply is its question and
nothing after it:**

- **A CR asked for in a session that wrote the code under review, or has
  the code skill loaded.** The question names what holds and the
  places the CR can run:

  ```
  ⚠️ This session <wrote the branch | has tkay-code loaded | wrote the branch and has tkay-code loaded>, so a CR here would not be independent of the code it judges. Where do you want it: here anyway, in a fresh agent I start with none of this session's history, or in a fresh session you open?
  ```

  A plan review asked for in a session that wrote the plan asks the same
  question, with "wrote the plan" for what holds and "a plan review" and
  "the plan" for "a CR" and "the code". A doc review asked for in a session
  that wrote the doc asks it with "wrote the doc", "a doc review" and "the
  doc".

- **Code asked for in a session that wrote a CR** - a fix of what it
  found, or any other code:

  ```
  ⚠️ Writing code here ties it to the CR this session wrote: the code would be written to the rubric, and the CR would no longer be independent of the code it judges. Are you sure you want it here and not in a fresh session that keeps the two apart?
  ```

Each is a question in a shape of its own. A yes to code lets the work go
on, and a no leaves every file as it is. The CR's question is a pick:

- **Here** lets the CR go on in this session.
- **A fresh agent** is a subagent the session starts for that CR alone,
  never one that inherits the session's context. It is told to invoke this skill first and never the code skill, and
  that it wrote none of what it reviews. It gets the repo, what to review
  and the spec the request names, and nothing of the session's history:
  none of its reasoning, and no review the session wrote. A repeat CR
  also gets the file of an earlier CR a fresh agent wrote. The agent
  writes the CR and its file, and the session shows me that CR in chat,
  whole and unchanged.
  The session has written no CR, so the CR carries no ⚠️ line, and code
  asked for after it asks nothing. A session that cannot start a subagent
  leaves this pick out of the question.
- **A fresh session** leaves every file as it is and writes no CR.

**"Here", or a yes to code, covers the rest of the session**: once a
session holds both, a second question protects nothing, so neither is
asked again. **"A fresh agent" covers it too**: each later CR goes to a
new one, with no question. After "a fresh session", or a no to code, the
next such request asks again. The question is the one stop: one decision
is one question, so no hook asks it a second time.

**A CR written here still opens with one bold ⚠️ line**, above
everything else in it, that names what holds and says the review is not
independent, so a reader of the CR file sees it too. The case that
taught both, a CR asked for in the session that wrote the branch:

```
❌ I can't review this branch here: this session wrote it, and it has
   tkay-code loaded. Open a fresh session and ask it for this:
   CR branch <branch>
✅ ⚠️ This session wrote the branch and has tkay-code loaded, so a CR here
   would not be independent of the code it judges. Where do you want it:
   here anyway, in a fresh agent I start with none of this session's
   history, or in a fresh session you open?
   (on "here")
   ⚠️ **Not an independent CR: this session wrote the branch and has
   tkay-code loaded.** For one, ask a fresh session for `CR branch <branch>`.
   <the CR>
```

The case that taught the fresh agent, a question that offered only a
session I had to open myself:

```
❌ ...Are you sure you want it here and not in a fresh session?
   me: can you do the CR in a fresh agent so it will start fresh?
✅ ...Where do you want it: here anyway, in a fresh agent I start with
   none of this session's history, or in a fresh session you open?
```

The one exemption is a session working on these skills themselves, whose
working directory is inside the git repo that holds them, or inside a repo
that marks itself as theirs with a `.claude-skills-repo` file at its root:
this standard cannot be edited without being read, and what such a session
writes is the rubric, not code the rubric judges, so it reviews its own
staged changes in place and fixes them, with no question and no ⚠️ line.

## A CR writes out fixes and never makes them

**A CR changes no file, and never offers to.** Every fix is written out
under its finding and left for me - no "want me to fix it?", no fix as a
next step. A fix I ask for anyway is code after a CR, and the question
above comes first. A plan review edits no plan, and a doc review no doc, on
the same terms.

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

**Where the repo documents a convention - commit message format, branch
names, MR description sections, test style, comment style - judge by the
repo, not by these references.** The references fill only what the repo
leaves unsaid. When the two disagree, follow the repo and say in one line
which rule of mine it overrode.
