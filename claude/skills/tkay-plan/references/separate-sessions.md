# Writing and reviewing stay in separate sessions

**The work and its review belong in different sessions, so neither is
coupled to the other.** Two reasons, and either alone is enough:

- **Work written with a review rubric in view overfits to it**: it is
  written to pass the review rather than to solve the problem, and the
  review then measures how well the work learned the rubric.
- **A review by the author is not objective**: it judges the work against
  the reasoning that produced it, and misses what that reasoning missed.

It holds for three kinds of work, each a pair:

| # | The work | Its review |
|---|---|---|
| **1** | code | a code review, or CR |
| **2** | a plan - a shape plan or a full plan | a plan review, also called a design review, a DR or a plan CR |
| **3** | a change to markdown docs | a doc review |

## What the session did, never which skill it used

**Every check below reads what this session did and loaded, never the name
of a skill**, so it holds whatever skills are installed beside the one
that carries this file:

- **It wrote the work**: it made the change under review - the branch's
  commits, the plan, the doc edit - with a skill or without one.
- **It loaded a writing standard for the work**: it read more of a skill
  than its description - opened the skill, or read one of its files - and
  that skill's own description says it is for writing that kind of work -
  code, a plan, a doc - with rules for how it is written. A skill that only
  drives a workflow, with no rules for judging the result, is not one.
- **It wrote a review**: a review of that kind, with a skill or without
  one.
- **It loaded a review standard**: it read more of a skill than its
  description, and that skill's own description says it is for reviewing
  that kind of work.

**What couples the work is the generic rules, never a specific report.**
The descriptions of installed skills are in every session, so seeing one
loads nothing. A review's report that this session did not write - the
findings a fresh agent wrote about this work - is input: reading it and
fixing what it found is neither writing a review nor loading a review
standard, and asks nothing.

**A skill counts for what its description says it is for, never for the
rules it carries for another purpose.** A review skill carries writing
rules only to judge by, so it is no writing standard; a skill that shapes
replies may carry a review's colours, and is no review standard; a plan
skill may carry the rules for code, and is a writing standard for plans
alone.

## Each crossing stops for my answer

**The reply is the question and nothing after it.**

- **A review asked for in a session that wrote the work, or loaded a
  writing standard for it.** The question names what holds and the places
  the review can run:

  ```
  ⚠️ This session <wrote the branch | loaded a standard for writing code | wrote the branch and loaded a standard for writing code>, so a CR here would be coupled to the code it judges: it would judge the code against the reasoning that produced it, not objectively. Where do you want it: here anyway, in a fresh agent I start with none of this session's history, or in a fresh session you open?
  ```

  A plan review asks it with "wrote the plan" and "a standard for writing
  plans" for what holds, and "a plan review" and "the plan" for "a CR" and
  "the code"; a doc review with "wrote the doc", "a standard for writing
  docs", "a doc review" and "the doc".

- **Work asked for in a session that wrote a review of that kind, or loaded
  a review standard for it** - a fix of what the review found, or anything
  else of that kind:

  ```
  ⚠️ This session <wrote a CR | loaded a standard for reviewing code | wrote a CR and loaded a standard for reviewing code>, so code written here would be coupled to the review: written to pass the rubric rather than to solve the problem, and a later review would measure that fit, not the code. Are you sure you want it here and not in a fresh session that keeps the two apart?
  ```

  Plans and docs ask it with their own words, as above.

**The review's question comes before any review skill is opened.** Every
session the first crossing catches asks first - from this file when a
writing skill carries it, from a review skill's description when none
does - and opens a review skill only on "here", so a fresh-agent pick
never puts the review rules into this session.

**The review's question is a pick:**

- **Here** lets the review go on in this session.
- **A fresh agent** is a subagent the session starts for that review alone,
  never one that inherits the session's context. It is told to load a
  review standard first and no writing standard, and that it wrote none of
  what it reviews. It gets the repo, what to review, the spec the
  request names, the plan the session wrote the work from and the
  session's record of the tests it ran on that work - the plan and the
  record by their paths, when the session has them - and nothing of the
  session's history: none of its reasoning, and no review the session
  wrote. A repeat review also gets the
  file of an earlier review a fresh agent wrote. The agent writes the
  review and its file, and the session shows me that review in chat, whole
  and unchanged. The session has written no review, so the review carries
  no ⚠️ line, and work asked for after it asks nothing - unless the
  session opened a review skill before it asked, which is loading a review
  standard. A session that cannot start a subagent leaves this pick out
  of the question.
- **A fresh session** leaves every file as it is and writes no review.

**The work's question is a yes or no**: a yes lets the work go on, and a no
leaves every file as it is.

## Asked once

- **"Here", or a yes to the work, covers the rest of the session** for
  that kind of work: once a session holds both, a second question protects
  nothing. **"A fresh agent" covers it too**: each later review of that kind
  goes to a new one, with no question. After "a fresh session", or a no,
  the next such request asks again.
- **One crossing is one question, whichever rule spots it.** Another
  installed skill may carry this same rule; when this session already asked
  about this crossing, it is not asked again.

**A review written here anyway opens with one bold ⚠️ line**, above
everything else in it, that names what holds and says the review is
coupled to the work, not objective, so a reader of the review's file sees
it too. The case that taught it, a CR asked for in the session that wrote
the branch:

```
❌ I can't review this branch here: this session wrote it, and it has
   a standard for writing code loaded. Open a fresh session and ask it:
   CR branch <branch>
✅ ⚠️ This session wrote the branch and loaded a standard for writing
   code, so a CR here would be coupled to the code it judges: it would
   judge the code against the reasoning that produced it, not
   objectively. Where do you want it: here anyway, in a fresh agent I
   start with none of this session's history, or in a fresh session you
   open?
   (on "here")
   ⚠️ **Not an objective CR: this session wrote the branch and loaded a
   standard for writing code, so this review is coupled to the code.**
   For one, ask a fresh session for `CR branch <branch>`.
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

## The one exemption

**A session working on the skills that carry this file** - its working
directory inside the git repo that holds them, or inside a repo that marks
itself as theirs with a `.claude-skills-repo` file at its root - asks
nothing and writes no ⚠️ line. These standards cannot be edited without
being read, and what such a session writes is the rubric, not work the
rubric judges, so its own staged changes are reviewed and fixed with no
question.
