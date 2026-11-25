---
name: tkay-plan
description: The shape for a plan document - problem first, a design grounded in a known architecture, one section per commit, reference material below a divider - and what to stop for while implementing one. Use when asked for a plan, a shape plan, a design doc or an implementation write-up, to update, re-check or keep alive one, when implementing an agreed plan, and when asked for a goal on a plan file. A plan is brainstormed first - talked through, nothing built - becomes a shape plan in chat when one is asked for in those words, and a document only when a full plan is asked for in those words. It asks before writing a plan in a session that reviewed one or loaded a standard for reviewing plans, and before a plan review in a session that wrote the plan or loaded a standard for writing plans.
---

# Writing Plans

When I ask for a full plan, `references/plan-shape.md` is the shape I want: read it
before the first line of one. Write it to a directory that survives the session
unless I name somewhere else - never `/tmp` or a session scratchpad, which can
vanish while the plan is still in use.

**Every plan, in every mode, is human readable**: read
`references/human-readable.md` before the first item of a brainstorm, a shape
plan or a full plan.

**A plan and its review stay in separate sessions**: read
`references/separate-sessions.md` before the first item of a plan, and
whenever a plan review - a design review, a DR or a plan CR - is asked for
in this session. It says when writing a plan stops for a question because
this session reviewed one or loaded a standard for reviewing plans, and
when a plan review does because this session
wrote the plan or has this skill loaded, whatever skill writes the review.

## Three modes: a brainstorm plan, a shape plan, a full plan

**A plan is brainstormed until I ask for a shape plan or a full plan in those words.** The
brainstorm settles what we want: the problem in plain words, what is in scope and what
is out, the decisions still open, and what is already settled or not a problem. It
judges as shaping does in Basecamp's
[Shape Up](https://basecamp.com/shapeup/1.1-chapter-02) - judging, cutting, naming the
rabbit holes - never a list where every idea stands unchallenged.

- **What the brainstorm produces**: a list in chat, one line per item, each with an outline
  number I can answer by - `1`, `1.a`, `1.a.i` - that never changes once given. Each
  item is a dash opening with its number in bold, `- **1.** <item>`, at every depth:
  a terminal renders a plain `1.` list nested in another with letters.
  Nothing else is drafted: no plan document, no contract, no black-box tests, no
  commits, no incidents table, no questions-and-answers or TBD section. What we want
  may still change completely, and anything built now is built for a plan that may
  not survive the conversation.
- **One line never stands for a bundle.** An item that names another plan, a
  handed-over list or a run of commits hides every change inside it, and I approve
  what I cannot see. Each change it delivers is a decision of its own, so it nests
  under the item as a sub-item - every time the brainstorm is shown, not only when I ask
  what is in it. The case that taught it, a page
  column that was in the plan but in no line of the brainstorm:

  ```
  ❌ - **5.d** The load-balancing weights plan, on this branch
  ✅ - **5.d** The load-balancing weights plan, on this branch
       - **i.** The weights leave the pin rows and the scaling lock
       - **ii.** A new name for the scaling page's pins tab
       - **iii.** A column on that tab showing which way each pin scaled
  ```
- **The brainstorm thinks as hard as the full plan; only what it writes is smaller.** The
  full plan's checks run while brainstorming, and what they find reaches me as items and
  decisions in chat, never as a drafted section:
  1. The problem first, in plain words.
  2. The known architecture: "Start from a known architecture" of
     `references/plan-shape.md` in full - search outward, bring the candidates with
     links and your recommendation - before any item rests on a design. The chosen
     one is an item of the brainstorm.
  3. "Responsibilities" in `references/clean-code.md`, for each new
     responsibility on the architecture chosen: its owner, state, interface and
     departures are items of the brainstorm.
  4. What must always be true.
  5. The questions of "Check security", "Check high availability" and "Check
     operability" in `references/plan-shape.md`, asked of what we are
     brainstorming.
  6. What has failed here before, and which of those the brainstorm must answer.
  7. What is not a problem, what rests on an inference, and when planning turns into
     a rabbit hole.

  What waits for the full plan is the writing: the document, the contract and its
  tests, the commits, the incidents table, the questions and answers, and TBD. The
  case that taught it, a brainstorm rule that left the architecture search for the
  full plan:

  ```
  ❌ the brainstorm asks "which known design does this resemble?" and moves on
  ✅ the brainstorm brings the known designs it found, with links, and a pick,
     before any item of it rests on one
  ```
- **The shape plan** is what I need before work starts and nothing that is itself
  work, sent in chat when I ask for a "shape plan" - never a file, and built from what
  the brainstorm settled, so it needs no document to exist first; when a full plan exists it
  is cut from that instead. A few bullets under each of these headings, in this
  order, and no other:
  1. **Problem and motivation** - one heading; two only when the motivation is not
     the problem.
  2. **The design it follows** - the known architecture picked, with its link, then
     one bullet per new responsibility: its owner, the state it keeps and any
     departure, as "Responsibilities" in `references/clean-code.md` gives them.
  3. **What we are going to do, and what we are not** - the goals, each with the
     check that proves it, as "Goals and non-goals" in `references/plan-shape.md`
     asks, and the non-goals.
  4. **The contract** - only what the plan adds, changes or removes, plus the
     invariants the change rests on, and the test that pins each, by a name that
     states the behaviour. The existing API that stays as it is goes unmentioned,
     and the tests are named, never written.
  5. **High availability**, 6. **Security** and 7. **Operability** - the answers
     to the questions those sections of `references/plan-shape.md` ask, "not
     needed, because" included.
  8. **Risks** - what has failed here before, and what the new design could break.
  9. **Questions and answers** - only the few whose other answer would change the
     design.
  10. **TBD** - only what I agreed to defer.

  Tests, commits, the glossary, the incidents table and the reference material stay
  out: they are the full plan's work. A shape plan hands off to implementation with
  the commits cut as we go, one at a time, each proposed before it is written;
  a change large enough to want its commits fixed in advance is a reason to ask for
  the full plan instead.
- **The full plan** is the document `references/plan-shape.md` describes, written
  when I ask for it, and it starts from what the brainstorm settled, or from the
  shape plan when one was sent. A design doc asked for by name is one.

## Call it when planning turns into a rabbit hole

**Be the third person in the design review who says "time to try it".** Implementing
and testing are cheap now - a prototype that checks a design end to end often takes
minutes - so a question a test can answer is not argued for another round. Watch the
discussion for the signs, and say so unprompted the moment one shows, mid-discussion
included:

- the same question comes back without new evidence
- two options are argued on how they would behave, and running them would show it
- hypothetical edge cases pile up faster than they are settled
- the plan grows sections nobody will read before the code exists

Name the question, the experiment that answers it - a throwaway prototype, a test, a
run on a dev cluster - and roughly how long it takes. The experiment is a spike: its
code is thrown away and what it shows goes back into the plan; a spike can also pick
between candidate architectures. Once the architecture is chosen and the questions
left are all of that kind, propose starting on the first commit; "Executing a plan"
is what makes that safe, because a hole found while implementing stops the work and
goes back into the plan.

A question whose wrong answer is expensive to undo - a data migration, a wire format
other systems will depend on, a change customers see - is still settled before it
ships. An experiment is often the fastest way to settle it: run it against a copy, a
dev cluster or a scratch branch, never against production.

## Executing a plan

Implementing a plan is where its holes show: a race nobody traced, an input that does
not exist, an assumption the code contradicts. **When you find a hole or a break in the
plan's architecture, stop and ask me before you write more code on top of it.** Lay it
out as a concrete scenario - the state, the sequence, what goes wrong - then give me
the options with your recommendation, and wait. Search for how known architectures
handle the same case first, and anchor each option in one where one fits, as "Start
from a known architecture" in `references/plan-shape.md` says.

**Where the plan edit would land decides whether it is a stop**, since every decision
edits the plan (below):

- **Stop and ask** when the edit would change the contract - an API, an invariant or a
  test that pins one - reverse a decision the plan settled, or replace the architecture
  it follows because that architecture fails a concrete scenario.
- **Decide and record** every other gap the plan left - a field, a read, a helper, how
  two pieces it names talk - picked the way its architecture would pick it. Each goes
  under a "Decided while executing" heading in the plan, one line with the commit that
  carries it, so a reviewer checks every one against the architecture, and you name it
  in your next message. It is never a stop.

A bug you can fix inside the agreed design - a wrong comparator, a missed condition, an
off-by-one - in the code this plan's commits write is not a stop: fix it and name it in
your next message. A bug in code the plan does not touch is a finding: report it, do not
fix it.

**Every decision made while executing updates the plan, without being asked**, in
the shape "Start from a known architecture" in `references/plan-shape.md` gives a
decision. A hole we settled, an option I picked, a commit dropped, merged or split, a
scope change, a fix that turned out to change behavior the plan describes: the plan
is edited in the same pass as the decision, before the next piece of code. Change
the sections it touches - design, commits, risks, decisions - and add a question and
answer when the reader will ask why. The plan must describe the branch as it stands,
so the reviewer never meets a plan the code already contradicts.

**When I ask for a goal on a plan file** - "give me a goal on <plan>.md", in
whatever words - read `references/plan-goal.md` and `references/goal-run.md`
first and follow them.

## Committing a plan to a repo

Committed to a repo, a plan becomes a record read by someone who was not in the
review, and `references/copied-stale-and-personal.md` binds it: a setting in force is
named by its owner, and a measurement stays only as the reason for a
decision. Until then the plan keeps them as they are - the measurements with
their queries, the settings in force, the branch - because whoever works from
it needs them. Working notes go:
instructions to whoever executes it, people's names, branch names, a section on
running things on one machine.

## Keeping it alive

I will ask you to re-check the plan against the branch, repeatedly. When I do: verify the
specific things the plan depends on, tell me plainly whether anything actually changed,
and only then edit. "Is it ready?" is a yes/no question - lead with the answer.

Keep the chat short. The depth belongs in the document, not in your message about the
document.
