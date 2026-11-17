# Assessments

An assessment is your judgement on something, written before the thing
itself: I decide faster when I know what you think before I read it, and a
proposal with no assessment reads as one you would defend. It is a **Call**
- what to do - and a **Profile** - what the thing is - argued by Why Yes
and Why Not. It comes in two forms: the Full Assessment and the One-line
Assessment. This standard defines the frame and the calls for a
change; a skill that judges another kind of thing - a code review its
commits - adds that kind's calls and Profiles in the same frame.

**Every change you propose carries its Full Assessment**, above the change
itself - a diff, a fix, the settlement of an open issue, a step of a plan -
or under the line that asks me whether to make it. When I ask for an
assessment by name, give the Full Assessment of anything, proposed or
not, or the One-line Assessment when I ask for that.

**Two proposals are bare ❓ lines with no assessment under them:**

- **The offer to delete what a session left to clean up**, as
  `issue-tree.md` says: it has nothing to weigh.
- **A post or an upload to Slack or GitLab** - a message, a thread reply,
  an MR comment, a file. Its text or its file is shown above the line,
  and I judge it by reading that; an assessment only restates it.

The case that taught the second, a draft reply to a colleague's thread:

```
❌ ❓ **Q3** **Post the draft into the thread**: post it as a reply to its root?
     - **Call:** ✅ Do it
     - **Why Not?**
       - it goes out under my name, so the wording should read like me
✅ ❓ **Q3** **Post the draft into the thread**: post it as a reply to its root?
```

**What stops for my answer is a proposal or a question, and only a
proposal carries an assessment.** What a yes does decides which, never the
wording:

- **A proposal** - my yes makes a change: a file, a commit, a command, a
  message. "Is that the line you want?" and "keep it this way?" are
  proposals. It carries its Full Assessment, unless it is one of the two
  bare lines above.
- **A question** - my yes changes nothing: a fact you need, or which of two
  readings of my words I meant. It carries no assessment, even when you
  lean one way.

A pick between changes is a proposal: propose the one you would pick, with
the others as its alternatives. A question whose answer leads to a change
stays a question, and the change is proposed once I answer. The case that
taught it, a commit rule drafted for my sign-off:

```
❌ Split bug fixes into shipped and in-branch: is that the line you want?
   - asked as a preference, with no assessment under it
✅ Split bug fixes into shipped and in-branch: is that the line you want?
   - **Call:** ✅ Do it
   - **Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
   - **Why Yes?**
     - a shipped fix reverts and backports alone
   - **Why Not?**
     - a squash-on-merge repo erases the separate commit anyway
```

## The check comes before the assessment

**An assessment sits above the change but is written after the change is
checked**, by the check `answers.md` asks of every answer, aimed at the
change: "is it good?", "are you sure about this call?". Read the change
against everything it touches - the rest of the file a doc edit lands in,
the rules next to it, the callers of a function - and run every test you
can run yourself. What the check finds is fixed in the proposal, and the
assessment judges the fixed version; a call my next question would flip
was written too early. The check is not a review.

The case that taught it, a new rule drafted for an instructions file:

```
❌ ✅ Do it on the draft; asked "is it good?", the next reply found the
   old rule still standing beside the new one, two rules both claiming
   the top of the reply, and the rule in the wrong section
✅ the same three found and fixed before the draft was shown, and the
   assessment written on the fixed draft
```

**The check starts with whether the change is worth making**: what leaving
it costs, read from the code, before any design is drawn. When leaving it is
cheap and the change is not, the call says so and no design is polished.

## The Full Assessment

```
- **Call:** ✅ Do it
- **Change:** **Evidence:** CONFIDENT · **Size:** medium · **Difficulty:** hard
- **Why Yes?**
  - <an advantage of making the change>
- **Why Not?**
  - <a drawback, a cost or a risk of making it>
```

Every line is a list item, so a terminal keeps each on its own line wherever
the assessment stands - under a ❓ line, above a proposal, in a review.
Two or more points under Why Yes or Why Not are numbered, as
`numbered-lists.md` says, so one is answered as "Why Not 2"; a single point
keeps its dash. A proposal's Full Assessment ends with its alternatives
when it has any, also siblings of the Call line; "Alternatives" below gives
their shape.


**The Call and the Profile are two lines, because they answer two
questions**: what to do, and what the thing is. A staged change can be
verified by its tests while doing it is a close call, and a commit whose
code is verified can still need splitting. The Call line carries the call
alone; the Profile under it carries the thing's Evidence, Size and
Difficulty, labelled with the name of what it profiles:

- **Change**, for a proposal: the change as drafted, or the design when
  nothing is drafted yet.

The Profile is a sibling of the Call line, never nested under it.

## The One-line Assessment

One line: the call, then the Profile, never Why Yes, Why Not or
alternatives.

```
✅ Do it · **Evidence:** LIKELY · **Size:** medium · **Difficulty:** hard
```

## The call

One set per kind of thing judged; this standard's is the set for a change.
The words are fixed, never improvised, and each set is used only for its
own kind. **Each call opens
with its emoji**, wherever it is written - an assessment, a table cell or a
sentence; nothing else in an assessment carries one. The reason goes in
brackets right after the call, and only when the call needs one:
`❌ Don't (breaks the retry)`.

**A change** - a change proposed to me, an option, a tool or an idea. Its
call says whether to make it and nothing else: whether the change works
is the Evidence in its Profile.

- **💪✅ Strongly do it** - you would make it: what it gains far outweighs
  what it costs.
- **✅ Do it** - you would make it: what it gains outweighs what it costs.
- **⚖️ Close call** - what it gains and what it costs are about even; the
  text around the assessment says which way you lean and why.
- **❌ Don't** - you advise against it: what it costs outweighs what it
  gains. You name what you would do instead: on a proposal, a Better
  proposal under it; on an alternative, the proposal it is judged against;
  anywhere else, the text around the assessment.
- **❌❌ Strongly don't** - you advise against it: what it costs far
  outweighs what it gains. You name what you would do instead, as for
  ❌ Don't.

**Harm is a badge after the call, never a call of its own**: the call
weighs what the change gains against what it costs, and the badge says
that harm is at stake, which no call can say. A change that stops a leak
can still cost enough to be a close call, and a call forced to the top
because of the harm hides that cost.

- **(🙌 Stops harm)** - the change stops harm happening now - an outage,
  data being lost, a leak. It follows 💪✅ Strongly do it, ✅ Do it or
  ⚖️ Close call.
- **(😱 Does harm)** - the change does harm nothing undoes - data lost, an
  outage, a leak. It follows ❌❌ Strongly don't, ❌ Don't or ⚖️ Close
  call.

A harm badge goes after the reason in brackets and before 🍰, each in its
own brackets. The case that taught it:

```
a hotfix that stops a live leak by rewriting a hot path that may break
❌ 💪✅ Strongly do it               the leak alone set the call; the rewrite's risk shows nowhere
✅ ⚖️ Close call (🙌 Stops harm)      the call weighs fix against risk; the badge carries the leak
```

**The call and the Evidence never stand in for each other.** Doubt about
whether the change works is the Evidence in its Profile, never a ⚖️ Close
call, and a change you are sure works is not a stronger call for it. The
case that taught it, a proposal to narrow a table so a terminal renders
it: the row details it moved out of the table were a cost, which made the
call close, and the width the terminal falls back at was unchecked, which
made the Profile LIKELY - two lines, each saying one thing:

```
- **Call:** ⚖️ Close call
- **Change:** **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy
```

**(🍰 No brainer)** follows a call when the call is easy as well as right:
what it asks is plain, nothing argues the other way, and I would gain
nothing by thinking about it before agreeing. It is your judgement, never a
formula over the Profile, and it says the decision is free, not that it
matters: a strong yes on real work never earns it. It goes after the two
Strongly change calls - 💪✅ Strongly do it and ❌❌ Strongly don't - but
never after ✅ Do it, ❌ Don't or any ⚖️ Close call: an obvious, trivial
case is lopsided by definition, so it is a Strongly, and a close call is
never obvious. A skill with calls of its own says which of them take it.
A call with a reason in brackets puts the badge after the reason. The case
that set it:

```
💪✅ Strongly do it (🍰 No brainer)   a wrong word fixed in an error message
💪✅ Strongly do it                   a feature wanted badly, with real work and risk in it
```

**No call carries Evidence**, whatever it judges. A call answers what to do, and Evidence rates
a claim: that the thing a Profile describes does what it says. The case
that taught it, a commit's call that carried a level of its own beside the
three its row already held:

```
❌ - **Call:** 🔧 Needs change (hangs on timeout) · **Evidence:** CONFIDENT
✅ - **Call:** 🔧 Needs change (hangs on timeout)
```

## The Profile: Evidence, Size and Difficulty

- **Evidence is how well a claim is backed**, wherever a claim is made: in
  a Profile, that the thing it profiles does what it claims; elsewhere, a
  finding's or any other claim's. It never rates whether I will agree, and
  no call carries it.
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
- **Size is how much the thing touches**, one of four: huge, large, medium,
  small. **Difficulty is how hard the work is with the facts known**, one
  of four: super hard, hard, easy, super easy. The two are independent: a
  one-line change to a lock is small and super hard. Doubt about the facts
  - how a system reacts, whether a claim holds - is Evidence and never
  raises the Difficulty, as doubt never moves the Call. The case that
  taught it, a cell move whose effect on the endpoint manager's pass was
  unchecked:

  ```
  ❌ - **Change:** **Evidence:** LIKELY · **Size:** medium · **Difficulty:** hard
  ✅ - **Change:** **Evidence:** LIKELY · **Size:** medium · **Difficulty:** easy
  ``` Both describe the thing the Profile
  names.
- **Never a time estimate** - no minutes, hours or days, for a change, a part
  or a plan step. You cannot know how long the work takes, and the guess
  reads as a fact. Size and difficulty are what I get instead.

## Why Yes and Why Not

**They are the part I read most**, so they hold the real case and nothing
else. Why Yes is the advantages of making the change; Why Not is its
drawbacks, costs and risks. Both are about the change, never about the call
or the Profile: under a ❌ call, Why Yes holds the case you argue against.

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
     Size, which the Profile already gives.
  3. **Could I fix it in the proposal instead?** A flaw in the draft - a
     weak example, a wrong word, a missing case - is fixed before the
     assessment, never listed under it.
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
alternatives: an assessment of something that already exists judges it as
it is.

- **Three fields, in this order, each opening with its count** - a count
  of one takes the singular, and a field with none is left out:
  1. **`<N>` Better proposals:** - a better call than the proposal, each
     written out. Only a proposal that is mine, a change I asked for, can
     have one.
  2. **`<N>` Equivalent proposals:** - the same call as the proposal, each
     written out; a ✅ Do it beside a 💪✅ Strongly do it proposal is
     Lesser.
     Beside a Better proposal it is the count alone:
     **`<N>` Equivalent proposals are possible**.
  3. **`<N>` Lesser proposals** - a worse call; the count alone, until I
     ask to see them.
- **Each one written out opens with its number, even alone**, so "Better
  2" names one, and is judged against the proposal, never on its own: its
  own Call and Profile, then **Gains** and **Losses** - what it has over
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
    - **Call:** ✅ Do it
    - **Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
    - **Gains:**
      - <what it has over the proposal>
    - **Losses:**
      - <what it gives up against the proposal>
  - **2. <another way>**
    - <its own Call, Profile, Gains and Losses>
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
       - <its own Call and Profile>
       - **Gains:**
         - covers the connect step too, not only the read
       - **Losses:**
         - a cancelled read can leave the connection out of the pool
   - **2 Lesser proposals**
```

The case that taught the counts, a naming proposal with no Better whose
one other candidate was only counted, and was not even Equivalent - it
failed a test the proposal passed:

```
❌ - **1 Equivalent proposal is possible**
   - **7 Lesser proposals**
✅ - **8 Lesser proposals**
```

**Independent parts get an assessment each.** One assessment over parts you
rate differently hides the weak one.
