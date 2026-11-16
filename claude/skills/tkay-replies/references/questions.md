# Every proposal or question that stops the reply opens with ❓

**A reply that stops because the next step is gated on my answer ends with
its proposals and questions, one dedicated line per decision, each opening
with `❓ **Q<n>**`.** The test is the stop: a tool call or a change you would
make the moment I reply and cannot make before. A question you could settle
by reading the code is settled, not asked. A question you would proceed past
under an assumption is stated as the assumption, in prose, and the reply goes
on. Anything else is not a ❓.

**A stop is a proposal or a question**, as `assessment.md` defines them: only a
proposal carries an assessment, and its Full Assessment nests under its line.

**Proposals and questions are numbered Q1, Q2, Q3 across the whole
session**, so I answer any of them ever asked by its number; the Q keeps it
apart from the reading list's `R<n>` and from the outline numbers of the
issue tree. A new one takes the next free number, whatever reply it is
in, and one asked again keeps its number. After a context summary,
numbering goes on from the highest `Q<n>` still in the context. When one
rests on material above it - a diff, a doubt, a risk, the steps it would
take - that part of the reply is headed `Q<n>. <the decision>` with the same
number, and the shared number is the whole reference: the ❓ line never says
"see above". Those numbered parts are the elaboration; no separate section
repeats them.

**An earlier one is referred to by its own `Q<n>`**, in any later reply, and
a new one never reuses a number. The case that taught it, a reply that
handed off my answers to the previous Q1 and Q2 and then asked about
cleanup:

```
❌ **Q1**: paste into a new session opened in <repo>: ...
   **Q2**: paste into a new session opened in <other repo>: ...
   ❓ **Q1** Delete the whole directory: ...
✅ **Q1**: paste into a new session opened in <repo>: ...
   **Q2**: paste into a new session opened in <other repo>: ...
   ❓ **Q3** Delete the whole directory: ...
```

**`Q<n>` in my message names a proposal or a question; `1)` does not.** An
item of mine that says `Q1` or `q1` is the answer to Q1 and nothing else. A
numbered list - `1)`, `2)`, `1.` - is not an answer sheet: each item may
answer the one of that number, or raise something new that has nothing to do
with it. Each item is read on its own words, in the reading list -
`reading-list.md` has its shape. The case that taught it: a reply to a Q1 and
a Q2 whose `1)` took up the bycatch table of the review above them, `2)`
asked for a new rule and `3)` for this one.

**This shape binds every stop, whoever told you to stop**: a rule in my
instructions, another skill, a repo's `CLAUDE.md`, or your own judgement
that a step needs my sign-off. A skill or repo that says "ask" and nothing
about shape gets this shape. One that prescribes its own shape for a
question wins on the parts it prescribes; the ❓ marker and the end-of-reply
position still apply wherever that shape does not contradict them.

The line is `❓ **Q<n>** **<the decision>**: <what you propose or need>. <the
question>?` Never a clause inside a paragraph, where I cannot see that the
reply stopped for it. Everything that does not depend on the answer is done
above the lines, and what does waits.

**The ❓ line is the cleanest line in the reply.** The decision in a few
plain words, then a question I answer with yes, no or a pick - nothing else.
How the change would be carried out - the branch, the order of steps, a test
to run first, a file, a flag, a version - lives in its `Q<n>` part above,
never on the line.

```
❌ ❓ **Q1** **Drop Unique Labels from multi-alert posts**: apply the diff
   above on a new branch, then render both post shapes with amtool before
   the commit. Do you want this change?
✅ ❓ **Q1** **Drop Unique Labels from multi-alert posts**: make this change?
```

A proposal's Full Assessment nests under its line, and none of it goes on
the line itself:

```
❓ **Q1** **<the decision>**: <what you propose>. <the question>?
  - **Call:** ✅ Do it
  - **Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
  - **Why Yes?**
    - <an advantage of making the change>
  - **Why Not?**
    - <a drawback, a cost or a risk of making it>
```

**The nest has no copy above it.** What it cannot carry - the lean of a
⚖️ Close call, why the proposal comes before an Equivalent proposal, an
assessment per part - stays in the text above the line. What you would do
instead of a ❌ call is a Better proposal, inside the nest.

**A proposal I ask for in that word is a ❓ block and nothing more**: one
`❓ Q<n>` line per independent part, each with its Full Assessment nested
under it, and above the block only what the nests cannot carry. Never a
diff, a commit split, a test list or another team's steps: those come when
I ask for the full plan. The case that taught it, "give me final proposal"
on a three-part change: three assessments above five diffs, two named
commits and a test list, and no ❓ line at all.

The nest is list items, never bare indented lines: markdown folds an
indented line under a paragraph into that paragraph, and every point runs
together on the ❓ line. **A blank line goes between two ❓ lines**, or the
second folds into the last point of the first and the reply shows one where
it asked two. The case that taught it, two proposals in one block:

```
❌ ❓ **Q1** **Refuse a deleting cell on update**: add it to this branch?
     - **Why Not?**
       - it lands in an unrelated MR
   ❓ **Q2** **Scope the cell to its cluster**: fix it in a separate MR?
✅ ❓ **Q1** **Refuse a deleting cell on update**: add it to this branch?
     - **Why Not?**
       - it lands in an unrelated MR

   ❓ **Q2** **Scope the cell to its cluster**: fix it in a separate MR?
```

**A proposal asks whether to make the change, even when you advise against
it**: yes always means "make it", and your judgement carries the advice
against it. A line that asks whether to leave the change out flips what yes
means, and advice against it reads as a double negative:

```
❌ ❓ **Q3** **Validate the cluster type on update**: leave it out of this
   branch?
     - **Call:** ❌ Don't
✅ ❓ **Q3** **Validate the cluster type on update**: add it to this branch?
     - **Call:** ❌ Don't
```

**No ❓ line carries a ⚠️.** A risk a yes carries is named in its Why Not, and a command that reaches remote state or data git does not hold
needs my explicit go-ahead anyway; a ⚠️ on the line only repeats them. A ⚠️
is a plain warning on a line with no ❓, and stops nothing.

**Something found on the way is never part of another proposal.** A fix
for a problem outside the change in hand - bycatch - goes in only when I
say so, in words that name that fix. Until then it is reported, or put to
me as a ❓ proposal of its own, never as a line inside another proposal's
diff, review or commit, where my yes to that proposal would carry it in.
The case that taught it:

```
❌ the diff for a new hook rating also removed a stale docstring
   paragraph, marked "B1 goes in the same edit", and my yes to the
   rating installed both
✅ the stale paragraph reported as B1, and fixed only once I said "add
   the B1 fix"
```

**A reply ends with at most one ❓ block.** Its lines are independent
decisions, ordered by what you would do first once answered. A decision
whose answer changes the next one makes the block exactly one line, and
every other decision waits for a later reply.

Not covered: the harness's permission prompts, which are not chat.
