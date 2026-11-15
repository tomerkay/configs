# Verdicts

A verdict is your judgement on something, written before the thing itself: I
decide faster when I know what you think before I read it, and a proposal
with no verdict reads as one you would defend. It comes in two forms, the
Full Verdict and the TL;DR Verdict, and nothing else is called a verdict.

## The check comes before the verdict

**A verdict sits above the change but is written after the change is
checked.** Before its first line, run the check I would ask for next - "did
you check yourself?", "is it good?", "are you sure about this verdict?" -
asked of yourself as if I had asked it: read the change against everything
it touches - the rest of the file a doc edit lands in, the rules next to
it, the callers of a function - and run every test you can run yourself; a
test is run, never listed. What the check finds is fixed in the proposal,
and the verdict judges the fixed version. If my question one message later
would flip the verdict, the verdict was written too early, and each flip
costs me a round of ping-pong. The check is not a CR: it never loads the
review standard.

The case that taught it, a new rule drafted for an instructions file:

```
❌ ✅ Do it on the draft; asked "is it good?", the next reply found the
   old rule still standing beside the new one, two rules both claiming
   the top of the reply, and the rule in the wrong section
✅ the same three found and fixed before the draft was shown, and the
   verdict written on the fixed draft
```

**The check starts with whether the change is worth making**: what leaving
it costs, read from the code, before any design is drawn. When leaving it is
cheap and the change is not, the call says so and no design is polished.

## The Full Verdict

```
- **Verdict:** ✅ Do it
- **Change:** **Evidence:** CONFIDENT · **Size:** medium · **Difficulty:** hard
- **Why Yes?**
  - <an advantage of making the change>
- **Why Not?**
  - <a drawback, a cost or a risk of making it>
```

Its first line is the TL;DR Verdict after `**Verdict:**`. Every line is a list
item, so a terminal keeps each on its own line wherever the verdict stands -
under a question, above a proposal, in a commit's review. Two or more
points under Why Yes or Why Not are numbered `1`, `2`, however deep the
verdict sits, so one is answered as "Why Not 2"; a single point keeps its
dash. **The number is written as a dash item opening with it in bold**,
`- **1.** <point>`: a terminal renders a numbered list nested in another
list with letters, so a plain `1.` under a label line shows as `a.`. A
proposal's Full Verdict ends with its alternatives when it has any, also
siblings of the Verdict line; "Alternatives" below gives their shape. The
case that taught the numbering, a verdict whose `1.` and `2.` showed on
screen as `a.` and `b.`:

```
❌ - **Why Yes?**
     1. <first>
     2. <second>
✅ - **Why Yes?**
     - **1.** <first>
     - **2.** <second>
```

**The call and the thing judged are two lines, because they are two
claims**: whether to do it, and whether it is correct. A staged change can
be verified by its tests while doing it is a close call, and a commit whose
code is verified can still need splitting. The Verdict line carries the
call - in a CR, with the Evidence that the call is right; for a change,
the call alone, since whether to make a change is a judgement and Evidence
rates a claim; the line under it carries the thing - its Evidence, Size
and Difficulty - under the name of what it is:

- **Change**, for a proposal: the change as drafted, or the design when
  nothing is drafted yet.
- **Commit** or **Bycatch**, in a CR: the thing as it sits in the code.
  Then one line per fix, each naming what to do in a few words with the
  Evidence, Size and Difficulty of doing it: `Fix 🔴🟠` is what unblocks the
  merge, `Fix 🟡⚪` the clean-up left to my judgement, and one with
  nothing to do is left out.

```
- **Verdict:** 🔧 Needs change (hangs on timeout) · **Evidence:** CONFIDENT
- **Commit:** **Evidence:** VERIFIED · **Size:** medium · **Difficulty:** hard
- **Fix 🔴🟠:** add a client timeout · **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy
- **Fix 🟡⚪:** rename the two helpers · **Evidence:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  ...
```

All of them are siblings of the Verdict line, never nested under it.

## The TL;DR Verdict

One line, for a place with no room for Why Yes and Why Not - a table cell, a
summary entry:

```
✅ Do it · **Evidence:** LIKELY · **Size:** medium · **Difficulty:** hard
🔧 Needs change (<the reason in a few words>) · **Evidence:** CONFIDENT
```

The reason goes in brackets right after the call, and only when the call
needs one. A TL;DR Verdict never carries Why Yes, Why Not or
alternatives. A proposal's carries the call and the change's Evidence,
Size and Difficulty on its one line, since it cannot nest; a CR's is the
call alone on a table's head row, and the Commit or Bycatch line, the Fix
lines and the call's Evidence fill the row under it, each without a label
its column already gives.

## The call

One set per kind of thing judged. The words are fixed, never
improvised, and each set is used only for its own kind. **Each call opens
with its emoji**, wherever it is written - a verdict, a table cell or a
sentence; nothing else in a verdict carries one.

**A change** - a change proposed to me, an option, a tool or an idea. Its
call says whether to make it and nothing else, so its Verdict line carries
no Evidence: whether the change works is the Change line's.

- **💯 No brainer** - you would make it, and its Why Not is none.
- **✅ Do it** - you would make it: what it gains outweighs what it costs.
- **⚖️ Close call** - what it gains and what it costs are about even; the
  text around the verdict says which way you lean and why.
- **❌ Don't** - you advise against it: what it costs outweighs what it
  gains. You name what you would do instead: on a proposal, a Better
  proposal under it; on an alternative, the proposal it is judged against;
  anywhere else, the text around the verdict.
- **😱 Hell NO** - you advise against it because it does harm nothing
  undoes - data lost, an outage, a leak - and name what you would do
  instead, as for ❌ Don't.

**The call and the Evidence never stand in for each other.** Doubt about
whether the change works is the Change line's Evidence, never a ⚖️ Close
call, and a change you are sure works is not a stronger call for it. The
case that taught it, a proposal to narrow a table so a terminal renders
it: the row details it moved out of the table were a cost, which made the
call close, and the width the terminal falls back at was unchecked, which
made the Change line LIKELY - two lines, each saying one thing:

```
- **Verdict:** ⚖️ Close call
- **Change:** **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy
```

**A commit** under review:

- **✅ Ship it** - the commit goes in as it is.
- **👌 Fixed later (by `<sha>`)** - a later commit on the branch fixes what
  blocks it; that commit's own call is picked on its own content.
- **🔧 Needs change** - amending this commit fixes what blocks it.
- **🪓 Split (<the parts>)** - nothing blocks it, but it does more than one
  thing; the brackets name the commits it splits into.
- **📝 Reword (<the reason in a few words>)** - nothing blocks it, but its
  message is false or misleading; a new message fixes it.
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
  ✅ Ship it, 👌 Fixed later, 🪓 Split or 📝 Reword - the four calls whose
  code is right, which differ only in what the commit needs.
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

A call says what to do, never what backs it: that is the Evidence, beside
the call on a CR's Verdict line and on the Change line of a change.

## Evidence, Size and Difficulty

- **Evidence is what backs the claim on its line**: on a CR's Verdict
  line, that the call is right - on a commit, that its findings are real
  and in the right colour, since the call follows from them; on a Change,
  Commit or Bycatch line, that the thing does what it claims; on a Fix
  line, that the fix would work. A change's Verdict line has none: its
  call is a judgement, not a claim. It never rates whether I will agree.
  Each level is defined by what backs it:
  - **VERIFIED** - you ran it or tested the exact behaviour.
  - **CONFIDENT** - not run, but you traced every step in the code or the
    docs.
  - **LIKELY** - one unchecked inference says it holds.
  - **50-50** - more than one unchecked inference, and they do not settle
    it.
  - **DOUBTFUL** - one unchecked inference says it does not hold.
  - **REFUTED** - you ran or traced it, and it does not hold.
  - **UNKNOWN** - nothing backs it either way. It is off the scale, not
    its lowest step: 50-50 has inferences to check, and UNKNOWN has
    nothing yet to check.
- **DOUBTFUL and REFUTED are only for a claim that is not yours** - what a
  commit says it does, an idea of mine. A claim of your own is stated as
  what you believe, so each claim is written one way: "LIKELY that it
  fails", never "DOUBTFUL that it works".
- **On DOUBTFUL, REFUTED or UNKNOWN a CR call never says go ahead**: never
  ✅ Ship it, 👌 Fixed later, 🪓 Split, 📝 Reword, ✅ Merge it,
  🔧 Merge after fixes, ✂️ Split first, ✅ Keep it, 🔧 Needs fixes,
  ✂️ Carve out or 🔧 Add fix.
- **Size is how much the thing touches**, one of four: huge, large, medium,
  small. **Difficulty is how hard it is to get right**, one of four: super
  hard, hard, easy, super easy. The two are independent: a one-line change
  to a lock is small and super hard. On a Change, Commit or Bycatch line
  they describe the thing as it is; on a Fix line, the fix.
- **Never a time estimate** - no minutes, hours or days, for a change, a part
  or a plan step. You cannot know how long the work takes, and the guess
  reads as a fact. Size and difficulty are what I get instead.

## Why Yes and Why Not

**They are the part I read most**, so they hold the real case and nothing
else. Why Yes is the advantages of making the change; Why Not is its
drawbacks, costs and risks. Both are about the change, never about the call
or its Evidence: under a ❌ call, Why Yes holds the case you argue
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

## Alternatives

**A proposal shows every other way it was weighed against**, so a real
choice never hides behind the one you picked. Only a Change has
alternatives: a Commit or Bycatch verdict judges what already sits in the
code.

- **Three fields, in this order, each opening with its count** - a count
  of one takes the singular, and a field with none is left out:
  1. **`<N>` Better proposals:** - a better call than the proposal, each
     written out. Only a proposal that is mine, a change I asked for, can
     have one.
  2. **`<N>` Equivalent proposals:** - the same call as the proposal, each
     written out; a ✅ Do it beside a 💯 No brainer proposal is Lesser.
     Beside a Better proposal it is the count alone:
     **`<N>` Equivalent proposals are possible**.
  3. **`<N>` Lesser proposals** - a worse call; the count alone, until I
     ask to see them.
- **Each one written out opens with its number, even alone**, so "Better
  2" names one, and is judged against the proposal, never on its own: its
  own Verdict and Change, then **Gains** and **Losses** - what it has over
  the proposal and what it gives up against it - each held to the rules of
  Why Yes and Why Not. An Equivalent has both; one with no Losses is
  Better, one with no Gains is Lesser.
- **A proposal with no alternatives ends at its Why Not**, and a fix to
  the draft goes into the draft, never into an alternative.
- **Beside Equivalents written out, one sentence above the question says
  why the proposal comes first**, where the lean of a ⚖️ Close call goes:
  when two carry the same call, the order is the real choice.
- **"Make Better 2 the proposal" swaps them**: it gets its own Why Yes and
  Why Not, and every other way - the old proposal included - is judged
  again against it and lands in the field it now belongs to. With no
  Better left, the Equivalents are written out again.

The shape, with every field present:

```
- **Why Not?**
  - <a drawback of the proposal>
- **2 Better proposals:**
  - **1. <another way>**
    - **Verdict:** ✅ Do it
    - **Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
    - **Gains:**
      - <what it has over the proposal>
    - **Losses:**
      - <what it gives up against the proposal>
  - **2. <another way>**
    - <its own Verdict, Change, Gains and Losses>
- **1 Equivalent proposal is possible**
- **2 Lesser proposals**
```

The case that taught it, a router timeout proposed with every way it beat
written out under it, and its alternatives judged on their own, which
left the comparison with the proposal to the reader:

```
❌ - **Equivalent Alternatives:**
     - **`asyncio.wait_for` around the call**
       - **Why Yes?**
         - <an advantage of making it>
   - **Lesser Alternatives:**
     - **1.** a circuit breaker per decode pod
     - **2.** a shorter readiness probe period
✅ <one sentence: why the client timeout comes before `asyncio.wait_for`>
   - **1 Equivalent proposal:**
     - **1. `asyncio.wait_for` around the call**
       - <its own Verdict and Change>
       - **Gains:**
         - covers the connect step too, not only the read
       - **Losses:**
         - a cancelled read can leave the connection out of the pool
   - **2 Lesser proposals**
```

**Independent parts get a verdict each.** One verdict over parts you rate
differently hides the weak one.
