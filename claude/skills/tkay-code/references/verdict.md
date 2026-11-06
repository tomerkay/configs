# Verdicts

A verdict is your judgement on something, written before the thing itself: I
decide faster when I know what you think before I read it, and a proposal
with no verdict reads as one you would defend. It comes in two forms, the
Full Verdict and the TL;DR Verdict, and nothing else is called a verdict.

## The check comes before the verdict

**A verdict sits above the change but is written after the change is
checked.** Before its first line, run the check I would ask for next - "did
you check yourself?", "is it good?": read the change against everything it
touches - the rest of the file a doc edit lands in, the rules next to it,
the callers of a function - and run every test you can run yourself; a test
is run, never listed. What the check finds is fixed in the proposal, and
the verdict judges the fixed version. A verdict that the same check, one
message later, turns from go into not ready was written before its check.

The case that taught it, a new rule drafted for an instructions file:

```
❌ ✅ Do it on the draft; asked "is it good?", the next reply found the
   old rule still standing beside the new one, two rules both claiming
   the top of the reply, and the rule in the wrong section
✅ the same three found and fixed before the draft was shown, and the
   verdict written on the fixed draft
```

## The Full Verdict

```
- **Verdict:** ✅ Do it · **How sure:** LIKELY · **Size:** medium · **Difficulty:** hard
- **Why Yes?**
  - <an advantage of making the change>
- **Why Not?**
  - <a drawback, a cost or a risk of making it>
```

Its first line is the TL;DR Verdict after `**Verdict:**`. Every line is a list
item, so a terminal keeps each on its own line wherever the verdict stands -
under a question, above a proposal, in a commit's review. The points under
Why Yes and Why Not are numbered from the second on, so one is answered as
"Why Not 2"; a single point keeps its dash and is named by its heading.

## The TL;DR Verdict

One line, for a place with no room for Why Yes and Why Not - a table cell, a
summary entry:

```
✅ Do it · **How sure:** LIKELY · **Size:** medium · **Difficulty:** hard
🔧 Needs change (<the reason in a few words>) · **How sure:** VERIFIED · **Size:** small · **Difficulty:** easy
```

The reason goes in brackets right after the call, and only when the call
needs one. A TL;DR Verdict never carries Why Yes or Why Not.

## The call

One set per kind of thing judged. The words are fixed, never
improvised, and each set is used only for its own kind. **Each call opens
with its emoji**, wherever it is written - a verdict, a table cell or a
sentence; nothing else in a verdict carries one.

**A change** - a change proposed to me, an option, a tool or an idea:

- **✅ Do it** - you would make it.
- **⚖️ Close call** - both ways are defensible; the text around the verdict
  says which way you lean and why.
- **❌ Don't** - you advise against it, and say what you would do instead.

**A commit** under review:

- **✅ Ship it** - the commit goes in as it is.
- **👌 Fixed later (by `<sha>`)** - a later commit on the branch fixes what
  blocks it; that commit's own call is picked on its own content.
- **🔧 Needs change** - amending this commit fixes what blocks it.
- **🪓 Split (<the parts>)** - nothing blocks it, but it does more than one
  thing; the brackets name the commits it splits into.
- **🔀 Squash into `<sha>`** - it belongs inside that earlier commit.
- **🗑 Drop** - the branch is better without it.

**A branch** under review, on the one line that opens its overview. It
follows from the entries, the worst one deciding, in the order ❌, ✂️, ⚖️,
🔧, ✅:

- **✅ Merge it** - every entry is ✅ Keep it.
- **🔧 Merge after fixes** - an entry is 🔧 Needs fixes, and none is ✂️ or ❌.
- **✂️ Split first** - an entry is ✂️ Carve out; the rest merges once it is
  moved.
- **⚖️ Close call** - an entry is ⚖️ Close call and it decides the branch.
- **❌ Don't merge** - an entry is ❌ Drop it, or the branch's purpose is
  wrong.

**A branch overview entry** - one thing a branch under review does, as it
lands:

- **✅ Keep it** - the change is right and every commit it lives in is
  ✅ Ship it, 👌 Fixed later or 🪓 Split.
- **🔧 Needs fixes** - the change is right, and a commit it lives in must
  change first; the brackets name the commit and what it needs.
- **⚖️ Close call** - keeping and dropping it are both defensible; the text
  around the verdict says which way you lean and why.
- **✂️ Carve out** - the work is sound but does not belong in this branch;
  it moves to a branch of its own.
- **❌ Drop it** - the change itself is wrong or out of scope, whatever its
  commits are called, and the work goes away.

**🎣 Bycatch** - something found on the way that is not part of what is being
judged:

- **🔧 Add fix** - fix it as part of this work.
- **⏸ Leave for now** - not in this work, with the reason in a few words.

The call says what to do, never how sure you are of it.

## How sure, Size and Difficulty

- **How sure is how sure you are that the thing is right and does what it
  claims** - for a bycatch row, that the fix you name would be - not how sure
  you are of the call or that I will agree. One of four, each defined by what
  backs it: VERIFIED, you ran it or tested the exact behaviour; CONFIDENT,
  not run, but you traced every step in the code or the docs; LIKELY, one
  unchecked inference carries it; 50-50, more than one unchecked inference,
  or you do not know. Below 50-50 the call never says go ahead: never ✅ Do it,
  ✅ Ship it, 👌 Fixed later, 🪓 Split, ✅ Merge it, 🔧 Merge after fixes,
  ✂️ Split first, ✅ Keep it, 🔧 Needs fixes, ✂️ Carve out or 🔧 Add fix.
- **Size is how much the change touches**, one of four: huge, large, medium,
  small. **Difficulty is how hard it is to get right**, one of four: super
  hard, hard, easy, super easy. The two are independent: a one-line change
  to a lock is small and super hard.
- **Never a time estimate** - no minutes, hours or days, for a change, a part
  or a plan step. You cannot know how long the work takes, and the guess
  reads as a fact. Size and difficulty are what I get instead.

## Why Yes and Why Not

**They are the part I read most**, so they hold the real case and nothing
else. Why Yes is the advantages of making the change; Why Not is its
drawbacks, costs and risks. Both are about the change, never about the call
or how sure you are: under ❌ Don't, Why Yes holds the case you argue
against.

- **Nothing real is left out.** Every advantage and every drawback that could
  change my answer or how the change is done is there: what it breaks, costs,
  rules out or locks in, and a gain the proposal does not already state. A
  missing drawback costs me more than a long list.
- **Nothing else goes in.** Never a restatement of the change, a drawback
  dismissed in the same line, or a cost true of every change - "the old
  behaviour stays until it is installed" is one, and earns no line.
- **The change taking effect is never a drawback.** Its intended effect, and
  the way every change of its kind goes live, are what the change is for. Why
  Not holds what goes wrong, costs or is lost beyond them: a side effect
  nobody asked for, a case the change breaks, a door it closes. The case that
  taught it, a hook change that rates `go env -w` as a write:

  ```
  ❌ - The hook goes live in every open session the moment it's copied.
  ❌ - Commands already running that call it start getting the 🟠 rating.
  ✅ - none (checked: every existing selftest case keeps its decision)
  ```

- **Every Why Not point passes four tests before it is written**, and a point
  that fails one is cut, not softened:
  1. **Is it the change working?** Its effect, the way it goes live, and
     what was written before it under the old shape are the change taking
     effect.
  2. **Would it be true of any change this size or of this kind?** "One more
     section", "the file grows", "it is rewritten, not extended" are its
     Size, which the Verdict line already gives.
  3. **Could I fix it in the proposal instead?** A flaw in the draft - a
     weak example, a wrong word, a missing case - is fixed before the
     verdict, never listed under it.
  4. **Does it name what goes wrong, and for whom?** A real point names a
     case that breaks, a cost someone pays or a door that closes. A point
     that only describes the change does none of these.

  The case that taught it, a rewrite of the branch overview's calls:

  ```
  ❌ - the overview section and the branch calls are rewritten, not extended
  ❌ - CRs written before the change use the old entry calls
  ❌ - one more section in a file every session loads
  ❌ - the example is illustrative, not from a session
  ✅ - none (checked: every place that names the old calls is in the two
       files the change rewrites)
  ```

- **Each point is one short clause**, and a list holds as many points as the
  case has. How the risk plays out, when it bites or what undoes it belongs
  in the text above, never in the point. The case that taught it:

  ```
  ❌ - An environment override such as GOFLAGS=-modfile can still point a
       scratch go mod tidy at a repo file, but a check after the command
       reports it and it takes a deliberate override.
  ✅ - An environment override can still move Go's writes into a repo.
  ```

- **No list is padded to match the other**: one with no such point says
  "none", and an empty Why Not adds what you checked in a bracket -
  `none (checked: <what was checked>)` - so the bracket reads as the proof
  of the "none", never as a drawback.

**Independent parts get a verdict each.** One verdict over parts you rate
differently hides the weak one.
