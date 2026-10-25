# Verdicts

A verdict is your judgement on something, written before the thing itself: I
decide faster when I know what you think before I read it, and a proposal
with no verdict reads as one you would defend. It comes in two forms, the
Full Verdict and the TL;DR Verdict, and nothing else is called a verdict.

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
under a question, above a proposal, in a commit's review.

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

Three sets, one per kind of thing judged. The words are fixed, never
improvised, and each set is used only for its own kind. **Each call opens
with its emoji**, wherever it is written - a verdict, a table cell or a
sentence; nothing else in a verdict carries one.

**A change** - a change proposed to me, a change a branch makes, an option, a
tool or an idea:

- **✅ Do it** - you would make it.
- **⚖️ Close call** - both ways are defensible; the text around the verdict
  says which way you lean and why.
- **❌ Don't** - you advise against it, and say what you would do instead.

**A commit** under review:

- **✅ Ship it** - the commit goes in as it is.
- **🔧 Needs change** - amending this commit fixes what blocks it.
- **🔀 Squash into `<sha>`** - it belongs inside that earlier commit.
- **🗑 Drop** - the branch is better without it.

**A leftover** - something found on the way that is not part of what is being
judged:

- **🔧 Add fix** - fix it as part of this work.
- **⏸ Leave for now** - not in this work, with the reason in a few words.

The call says what to do, never how sure you are of it.

## How sure, Size and Difficulty

- **How sure is how sure you are that the thing is right and does what it
  claims** - for a leftover, that the fix you name would be - not how sure
  you are of the call or that I will agree. One of four, each defined by what
  backs it: VERIFIED, you ran it or tested the exact behaviour; CONFIDENT,
  not run, but you traced every step in the code or the docs; LIKELY, one
  unchecked inference carries it; 50-50, more than one unchecked inference,
  or you do not know. Below 50-50 the call never says go ahead: never ✅ Do it,
  ✅ Ship it or 🔧 Add fix. A test you can run yourself is run before the
  verdict, not listed.
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
- **Each point is one short clause**, and a list holds as many points as the
  case has. How the risk plays out, when it bites or what undoes it belongs
  in the text above, never in the point. The case that taught it:

  ```
  ❌ - The hook goes live in every open session the moment it's copied.
       Any regression would show up there before the live tests run, and
       git restore is the fallback.
  ✅ - The hook goes live in every session the moment it's copied.
  ```

- **No list is padded to match the other**: one with no such point says
  "none", and an empty Why Not adds what you checked.

**Independent parts get a verdict each.** One verdict over parts you rate
differently hides the weak one.
