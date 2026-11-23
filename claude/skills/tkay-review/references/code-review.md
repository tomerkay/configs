# Code Review Standards

`clean-code.md`, `security.md`, `commits.md`, `assessment.md`,
`severity.md` and `bycatch.md` sit beside this file in `references/`; this
skill's SKILL.md says what each is for.
`assessment.md` gives the frame every assessment in a CR is written in - the
Call, the Profile, Evidence, Size and Difficulty, Why Yes and Why Not; "The
calls and Profiles of a CR" below adds what only a review judges.

**Read `clean-code.md`, `security.md` and `severity.md` before the first
finding.** The first two define clean code, and `severity.md` how bad a
departure is; this file says how to report one.

## How I Want Code Reviews Done

A code review (CR) is of production code: report every problem you find, plainly and at its real severity.

## The branch is what ships, not the commits

**The target of a review is the final outcome: the tree at the top of the
branch, merged into its base.** Commits are how that outcome is reached and
read; they are never a target of their own. The worst review I can get is
every commit marked `✅ Ship it` while the branch as a whole is broken - each
commit judged against the one before it, and nobody judging what lands.

- **Read the whole branch first, as one change**: `git diff
  <merge-base>..HEAD`. Know what the branch delivers before judging any
  commit's part in it.
- **Judge the outcome at HEAD**: does the merged result work, does every piece
  the branch adds join up, does it do what the branch set out to do. A defect
  that lives in no single commit - two commits that pass alone and break
  together, a change no later commit finishes - is still a finding. It goes in
  the review of the commit that should carry the fix, so that commit's call
  blocks.
- **The commit calls never read greener than the outcome.** If the branch
  at HEAD is broken, at least one row of the In short table is none of
  `✅ Ship it`, `👌 Fixed later`, `🪓 Split`, `📝 Reword` and
  `🔀 Squash into`: a fix that HEAD does not hold is no fix.
- **Squash when it makes the outcome clearer.** When reading the commits apart
  hides what the branch does - steps that only make sense together, a commit
  that is broken until a later one lands, a split that leaves the reader to
  assemble the change in their head - recommend `🔀 Squash into` even when no
  commit got anything wrong. A commit earns its place by making the outcome
  easier to understand or to bisect, not by existing. The review recommends
  every squash and split; the rewrite itself waits for my word.

## One CR per repo

**A CR over more than one repo is one CR per repo, one after the other,
never interleaved.** Each repo gets its own sections under a heading
that names the repo, its own branch line, and its own numbering, so
"<repo> row 2" names one row and no row carries a repo tag. One line
above the first repo says whether the branches merge independently or in
which order. A CR Digest over several repos is split the same way.

## The CR's sections

**Every CR has the same sections, in this order, each under its own
top-level heading, below the title "The overview" gives, whatever the
branch and whatever it was given:**

1. `# Overview` - what the branch does; see "The overview".
2. `# Changes` - one entry per thing the branch does, judged as it lands;
   see "The changes".
3. `# Goals`, `# Contract`, `# Readiness`, `# Incidents` - whether the
   branch delivers what its spec asked for; see "The spec tables".
4. `# Design` and `# Implementation` - every rule of `clean-code.md`, held
   against the branch at the level its break lives; see "The Design and
   Implementation tables".
5. `# Commits` - `## In short`, each commit in one line, then `## In
   detail`, each commit's review; see "The commits".
6. `# 🎣 Bycatch` - what the review turned up on the way; see "The bycatch
   table".
7. `# To do` - every piece of work the CR asks for, in `## Before it merges`
   and `## Optional`; see "To do".
8. `# Summary` - the section calls, the branch call and the CR's file;
   see "The ending".

A CR that checks the fixes of an earlier one adds `# Was it fixed` right
after the overview; see "Was it fixed?".

**The sections above `# Commits` judge the branch as a whole, never one
commit.** Each of their rows is about the branch at HEAD, and its **Work**
cell ties it back to the commits: the commits it lives in (`**C2**,
**C3**`), the commit whose finding carries its fix (`**C3**, its 🔴`), or
what is not built yet (`not built: <what the new commit adds>`). The detail
of every finding - the file, how it fails, the fix written out - lives in
its commit's review under `## In detail`, and a row only points there.

**Every section is always there.** A section with nothing to say says why,
in one line, so an empty section never reads as one the review skipped:
"No spec given - nothing to check the branch against.", "The spec states
no incidents.", "Couldn't tell: <why> (checked: <what was read>).", "No
bycatch.", "Nothing to do."

**The CR stands on its own.** It names what it was given once, on the
overview's Given line, and takes from the spec whatever it judges, in its
own words: no row points into the spec ("Section 4"), so the CR reads the
same with the spec closed.

**Every number names what it numbers by its letter**, so a reply names a
row and nothing else: **CH** a change, **G** a goal, **A** an API row,
**IV** a constraint or invariant, **SE**, **HA** and **OP** a security,
high-availability and operability claim, **IN** an incident, **DS** a
Design row, **IM** an Implementation row, **C** a commit, **B** a bycatch row, **TD** a To do row,
**SC** a row of the section calls the CR ends with.
Each is bold and counts from 1 in its section; **B** goes on from the
session's count of bycatch.

A CR in the session that wrote the code opens with the ⚠️ line this
skill's `SKILL.md` gives, above everything else, and every CR closes as
"The ending" says.

### The views: CR, CR Digest, CR Brief and CR Summary

**A CR comes in these views, each asked for by its name:**

- **CR** - every section.
- **CR Digest** - every section but `## In detail`.
- **CR Brief** - `# Overview`, `# To do` and `# Summary`.
- **CR Summary** - `# Summary` alone.

**A Digest, a Brief or a Summary is only of a CR already done in this session**:

- **This session already reviewed the branch**: the sections are rebuilt
  from that review under "A repeat CR". A commit whose review is carried
  stays off the screen; a commit that needs a fresh review brings its
  review back under `## In detail`, because its findings are new to me.
- **No CR of the branch in this session**: the view is a full CR. Every
  commit is reviewed, and the reply is every section.

**A table is never cut to fit a view.** A section is in a view whole, or
not at all.

```
"CR Digest", after this session's CR of the branch, nothing changed since:
❌ every section, In detail included - the CR again
✅ every section but In detail

"CR Brief", no CR of the branch yet:
❌ # Overview, # To do - a call no review stands under
✅ the full CR
```

## Is it a real bug or a nit - and must I fix it now?

**One question I must be able to answer about every single finding, without reading between the lines: is this code broken or merely imperfect?** The colour answers it, and the colour alone decides whether the merge waits for a fix; a 🧪 UNTESTED finding, which has no colour, makes it wait for a run instead:

- **MUST HAVE** is 🔴 and 🟠. It blocks the merge: I fix it now, or I don't ship. One that is a soft blocker I may also merge past on my word; "Hard and soft merge blockers" says which.
- **NICE TO HAVE** is 🟡 and ⚪. I ship without it; worth doing when I'm in there anyway, and my call by definition.

Nothing moves between the two: no promotion, no demotion, no bracket that makes a 🟡 block or lets a 🟠 through. A finding is headed by its colour and its claim, and the section it sits in says whether it blocks:

```
##### 🔴 BUG: <one-line claim>
##### 🟡 QUALITY: <one-line claim>
```

A wall of findings where I can't tell the colours apart is a useless review, however thorough.

### The severity tags (use the exact emoji + word)

The four colours, the bar each one sets and how one is picked are
`severity.md`'s, beside this file.

**🧪 UNTESTED is a finding with no colour: the code is not in doubt, only unproven.** It marks a claim the commit rests on that you traced and found sound, but that only a run you cannot make yourself proves - "Rules that keep the tags honest" says which runs. It is neither MUST HAVE nor NICE TO HAVE: it asks for a run, never a code change, so it gets a section of its own and a call of its own, `🧪 Needs test`. A doubt you can name - a condition under which the code might fail, which you could not check - is never 🧪: it is a 🟠 RISK (UNVERIFIED), because the doubt is about the code.

```
##### 🧪 UNTESTED: <the claim only a run proves>
```

The case that taught it, a fix for a failing nightly suite, traced end to end, that only the hour-long suite could prove:

```
❌ FINDINGS: 🟠 1 · Call: 🔧 Needs change (not yet run against the suite it fixes) (⛔ Hard blocker: code)
✅ FINDINGS: 🧪 1 · Call: 🧪 Needs test (the nightly suite) (🚧 Soft blocker: untested)
```

A departure from `clean-code.md` keeps the colour the checklist below gives it.

**Who introduced it does not change the colour, and only sometimes where it goes:**

- **The branch introduced it**: a finding on that commit, whatever the colour.
- **It is pre-existing and stops what the branch delivers from working well**: a finding on the commit that should carry the fix, headed `##### 🟠 RISK [pre-existing; <what of the branch it breaks>]: <claim>`, so nobody looks for it in that commit's diff. It blocks: whether the branch works does not depend on who wrote the bug.
- **It is pre-existing and the branch does not depend on it**: 🎣 bycatch, see "The bycatch table".

### The calls and Profiles of a CR

Every assessment in a CR is written in the frame of `assessment.md`, with these calls and Profiles added for what a review
judges.

**The Profiles.** Under the Call line of a commit:

- **Commit**, in a CR: the thing as it sits in the code. Then one Fix
  Profile per fix, as `severity.md` gives it: the blocking fix is what
  unblocks the merge, the clean-up fix what is left to my judgement. A
  bycatch row's Profiles are `bycatch.md`'s. A commit with a 🧪 UNTESTED
  finding adds a `Test 🧪` Profile after them: the run in a few words, with
  the Evidence the claim would have once the run passes and the Size and
  Difficulty of making it.

```
- **Call:** 🔧 Needs change (hangs on timeout) (⛔ Hard blocker: code)
- **Commit:** **Evidence:** VERIFIED · **Size:** medium · **Difficulty:** hard
- **Fix 🔴🟠:** add a client timeout · **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy
- **Fix 🟡⚪:** rename the two helpers · **Evidence:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  ...
```

All of them are siblings of the Call line, never nested under it.

On a Commit Profile, Evidence backs that the thing does what it claims; on
a change's Change Profile, that the change works once all its commits are
in. Size and Difficulty describe the thing as it is.

**The calls.** Each opens with its emoji, wherever it is written:

**A commit** under review:

- **✅ Ship it** - the commit goes in as it is.
- **👌 Fixed later (by `<sha>`)** - a later commit on the branch fixes what
  blocks it; that commit's own call is picked on its own content, and
  says whether it squashes in.
- **🔧 Needs change** - amending this commit fixes what blocks it.
- **🙋 Needs your call (<the decision>)** - what blocks it is a choice only
  I can make: a break that may be intended, a design choice where both
  sides are valid, a fix that would change the contract or reverse
  something decided. The finding writes the question out, as "🙋 Your
  call" below says.
- **🧪 Needs test** - nothing in its code blocks it, but a claim it rests on
  has not run; the run clears it, and my acceptance marks it
  `accepted untested`. It is not a go-ahead.
- **🪓 Split (<the parts>)** - nothing blocks it, but it does more than one
  thing; the brackets name the commits it splits into.
- **📝 Reword (<the reason in a few words>)** - nothing blocks it, but its
  message is false or misleading; a new message fixes it.
- **🔀 Squash into `<sha>` (<which message survives>)** - nothing blocks
  it, but it belongs inside that commit, earlier or later.
- **🗑 Drop** - the branch is better without it.

**A branch** under review, on the Branch call line that ends the CR. It
follows from every section but the bycatch - what the review found on the
way is not what the branch does - the worst row deciding, in the order ❌,
✂️, ⚖️, ⏳, 🙋, 🔧, 🧪, ✅:

- **✅ Merge it** - every change is ✅ Keep it, and every row of the spec
  tables is ✅ Met or ✅ Additive.
- **🧪 Merge after tests** - a change is 🧪 Needs test or a spec row 🧪 Met
  untested, and every other is ✅.
- **🔧 Merge after fixes** - a change is 🔧 Needs fixes, and none is ✂️, ❌
  or 🙋.
- **🙋 Merge after your call** - a decision only I can make holds the
  branch, and no ⏳, ✂️, ⚖️ or ❌ outranks it.
- **⏳ Finish the work first** - a row of a spec table is ⏳ Not reached:
  the branch may be correct, and it still delivers only part of what it
  was asked for.
- **✂️ Split first** - a change is ✂️ Carve out; the rest merges once it is
  moved.
- **⚖️ Close call** - a change is ⚖️ Close call and it decides the branch.
- **❌ Don't merge** - a change is ❌ Drop it, the branch's purpose is
  wrong, or a spec row is ❌ Missed and no fix inside the work delivers it.

**A change** - one thing a branch under review does, as it lands:

- **✅ Keep it** - the change is right and every commit it lives in is
  ✅ Ship it, 👌 Fixed later, 🪓 Split, 📝 Reword or 🔀 Squash into - the
  calls whose code is right, which differ only in what the commit needs.
- **🔧 Needs fixes** - the change is right, and a commit it lives in must
  change first; the brackets name the commit and what it needs.
- **🧪 Needs test** - the change is right as far as the code shows, and a
  commit it lives in waits for a run; the brackets name the run.
- **🙋 Needs your call** - a commit it lives in waits on a decision only I
  can make; the brackets name it.
- **⚖️ Close call** - keeping and dropping it are both defensible; the text
  around the call says which way you lean and why.
- **✂️ Carve out** - the work is sound but does not belong in this branch;
  it moves to a branch of its own.
- **❌ Drop it** - the change itself is wrong or out of scope, whatever its
  commits are called, and the work goes away.

**A row of a spec table** - a goal, a contract row, a readiness claim or
an incident - judged at HEAD:

- **✅ Met** - the branch delivers it, checked the way the spec says a
  reader checks it.
- **🔧 Met after fixes (<the commit>)** - the branch delivers it, and a
  commit it lives in has a 🔴 or 🟠.
- **🧪 Met untested (<the run>)** - the code delivers it as far as the
  review traced, and only a run the review could not make proves it.
- **⏳ Not reached (<what is missing>)** - what delivers it is not on the
  branch yet.
- **❌ Missed (<why>)** - what delivers it is on the branch, and it does
  not hold.

An **A** row has two calls more, for the question no spec has to ask -
does an existing caller keep working:

- **✅ Additive** - nothing that exists today changes: a new endpoint, an
  optional field.
- **❌ Breaks callers (<who>)** - an existing caller stops working; it is
  also a 🔴 or 🟠 finding. A break the spec asks for is ✅ Met once every
  caller has moved off; a caller still on it is the finding.

With a spec, an A row gets both questions, and the worse answer is its call.

**A row of the Design or Implementation table**:

- **✅ Holds** - the branch's code keeps it.
- **🔴, 🟠, 🟡 or ⚪ Broken (<what>)** - the branch breaks it; the colour is
  the finding's.
- **➖ Irrelevant** - the branch's code never touches it.

**🙋 Your call** - a finding that needs a decision only I can make, not a
fix a session can apply: a break that may be intended, a design choice
where both sides are valid, a fix that would change the contract or
reverse something decided. Under the finding, the question and its
options, with the one you recommend:

```
🙋 **Your call:** keep `retry_budget` required, or give it a default?
- **a)** default it to 0 - no caller breaks, and retries stay off until set
- **b)** keep it required - both services must change before this merges
- I'd pick **a)**: nothing breaks, and **b)** can still follow.
```

A session handed the CR asks me each one; it never picks for me.

**🎣 Bycatch** - something found on the way that is not part of what is being
judged: its calls are `bycatch.md`'s.

**(🍰 No brainer)** may follow every commit, entry and bycatch call, on the
same judgement `assessment.md` gives for a change. A branch's call carries it
only when every entry does, since a branch's call follows its entries. The
case that set it for a commit:

```
🗑 Drop (⛔ Hard blocker: drop) (🍰 No brainer)   a back-merge of the default branch that carries no change
```

**(🙌 Stops harm)** may follow a commit, entry or branch call, on the
same judgement `assessment.md` gives for a change: the change stops harm
happening now - an outage, data being lost, a leak - so the merge should
not wait in a queue. A plain bug fix does not earn it; harm still
happening does. It never follows 🗑 Drop, ❌ Drop it or ❌ Don't merge. A
branch's call carries it when an entry does. It goes after the reason in
brackets and before 🍰. **(😱 Does harm)** is never on a CR call: harm a
commit does is a 🔴 finding, and the badge would only repeat it. The
shape:

```
🧪 Needs test (a run on a live cluster) (🚧 Soft blocker: untested) (🙌 Stops harm)   a hotfix for a live leak, traced, not yet run
```

**The go-ahead floor.**

- **A commit, bycatch or change whose Profile reads DOUBTFUL,
  REFUTED or UNKNOWN never gets a go-ahead call**, and neither does an entry
  or a branch it decides: never ✅ Ship it, 👌 Fixed later, 🪓 Split, 📝 Reword,
  🔀 Squash into, ✅ Merge it, 🔧 Merge after fixes, ✂️ Split first, ✅ Keep it,
  🔧 Needs fixes, ✂️ Carve out or 🔧 Add fix.

### Hard and soft merge blockers

**Whatever holds the merge is a hard blocker or a soft one, by whether my
word can clear it, and its kind says what it is:**

- **⛔ Hard blocker** - something wrong ships, or a choice only I can make
  is still open: product code that is wrong or missing, a test that passes
  on the bug it guards, a doc that makes its reader do harm, a change that
  should not be there. Only its fix or my decision clears it.
- **🚧 Soft blocker** - what ships is right, and something is still owed: a
  test, a run, sound work that belongs in another branch. It clears when
  the work is done, or when I say to merge past it; until then it stays on
  the branch call. A session handed the CR does the work either way.

The usual level, the kind, and when the level moves:

| What holds the merge | Usual | Kind | Moves when |
|---|---|---|---|
| a 🔴, or a 🟠 other than a missing test, in product code | ⛔ | code | never |
| a 🔴, or a 🟠 other than a missing test, in anything else | ⛔ | what it is in: test code, doc or commit message | never |
| a spec row not delivered | ⛔ | what delivers it: code, test code or doc | never |
| 🗑 Drop, ❌ Drop it | ⛔ | drop | never |
| a 🔴, or a 🟠 other than a missing test, in a plan's design, in a plan review | ⛔ | design | never |
| a 🙋 decision | ⛔ | decision | 🚧 when either answer can still be taken after the merge, and neither leaves what merged wrong |
| a bug fix with no test that reproduces it | 🚧 | no repro test | ⛔ when the bug coming back would do harm nothing undoes |
| a 🧪 UNTESTED claim | 🚧 | untested | ⛔ when the claim is what the branch exists for, and its failing would do harm |
| ✂️ Carve out | 🚧 | carve out | never |

- **Product code is whatever ships and runs**: the code, a chart, a
  dashboard, config, and a name or a label inside any of them. Test code, a
  doc and a commit message are not. The kind `code` is product code alone,
  so a blocker of kind `code` says the code I ship is wrong.
- **The level is judged by the definition, never picked**: the table gives
  the usual answer, and a level moves only in the case its row names, with
  the reason after the kind: `⛔ Hard: untested, its failing loses data`.
- **The kind is one of the table's words, never improvised.**
- **In a table, the blocker is a column of its own, `Blocker`, always the
  last**: `⛔ Hard: code`, or `-` on a row that holds nothing. The header
  names the blocker, so the cell leaves the word out. The Goals, Contract,
  Readiness, Incidents, Design, Implementation, In short, Before it merges
  and Summary tables have it; the bycatch and Optional tables, whose rows never
  hold the merge, do not.
- **Outside a table, the call carries it as a badge**, after the reason in
  brackets and before any other badge: `🔧 Needs change (crashes on an
  empty list) (⛔ Hard blocker: code)`. A call with no badge holds nothing.
- **A row or a call that closes more than one blocker carries the worst
  level, ⛔ before 🚧, then every kind at that level**: `⛔ Hard: code,
  decision`.
- **A soft blocker I wave no longer holds the merge**: it reads `🚧 Soft:
  untested, waved`, or `(🚧 Soft blocker: untested, waved)` as a badge, and
  a 🧪 I accept untested is waved. A branch whose blockers are all soft
  merges on my word.

### Mandatory output shape per commit

Each commit's review sits under `## In detail`, headed `### C<n> · Commit <n> of <total>: <its subject line>`, so its number is the one the In short table and every Work cell give it. Open it with the FINDINGS line and its Full Assessment, then dive straight into details. (This is not the banned "recap of the findings before the findings" - it's a count and an assessment, not a recap.)

**The FINDINGS line counts each colour**, in the order 🔴 🟠 🟡 ⚪, only the colours with a finding, then the 🧪 UNTESTED findings, and `none` when nothing was found:

```
FINDINGS: 🔴 2 · 🟠 1 · 🟡 4
FINDINGS: 🟠 2 · ⚪ 1
FINDINGS: 🟡 1 · 🧪 1
FINDINGS: none
```

A 🔴 or 🟠 count on the line means the commit blocks; a 🧪 count, that it waits for a run; a line with only 🟡 and ⚪ means it ships. Nothing else goes on it.

**The commit's Full Assessment** follows the FINDINGS line, in the frame of `assessment.md` and with the commit calls of "The calls and Profiles of a CR":

- **Its call is the one its In short row gives**, under the rules in "The commits" below. The row carries this assessment's call and Profiles, so the two never disagree.
- **The Commit Profile is the commit as it is**: the Evidence that it does what it claims at HEAD, apart from its findings, and how big and hard it is.
- **The Fix Profiles are the work the findings ask for.** The blocking fix names what unblocks the merge and what it costs; the clean-up fix names the clean-up and what it costs, and is mine to take or leave. One whose colours have no finding is left out, and each label names only the colours its findings have. The case that taught it, a commit with one 🔴, one 🟡 and one ⚪:

  ```
  ❌ Fix 🔴🟠: a cross_zone flag on the removal check · Fix 🟡⚪: correct the pool-node claim
  ✅ Fix 🔴: a cross_zone flag on the removal check · Fix 🟡⚪: correct the pool-node claim
  ```
- **Every finding has a fix that changes something.** A finding whose fix would be to leave the code as it is is not a finding: drop it before the assessment, never write it with a Fix Profile that says to leave it. A bycatch row's `⏸ Leave for now` is different: its fix exists, and the call defers it. A 🧪 UNTESTED finding is different too: its run is its fix, and the run changes what is known. The case that taught it, a ⚪ on a heading that repeated the repo name the change was asked to add:

  ```
  ❌ FINDINGS: ⚪ 1 · Fix ⚪: none needed; leave the repeat
  ✅ FINDINGS: none - the repeat is what the change is for
  ```
- **Why Yes and Why Not hold what the change gains and costs** - behaviour it introduces, alerts it shifts, doors it closes - never its findings, which the sections below list. When nothing is left beyond them, Why Not says "none beyond the findings above (checked: <what was checked>)".

Then two sections, in this order, with the divider, each under a `####` heading inside its commit, worst colour first within each, and a third between them for a commit with a 🧪 UNTESTED finding; each finding under them is headed `#####`:

```
#### MUST HAVE — 🔴🟠, blocks the merge
...🔴 first, then 🟠...

#### UNTESTED — 🧪, waits for a run
...each claim, the run that proves it, and its three lines...

---

#### NICE TO HAVE — 🟡⚪
...🟡 first, then ⚪...
```

**If a section is empty, say so** - and say what you actually checked, not that correctness is proven: "MUST HAVE: none - I traced both new branches and grepped every caller in HEAD." An empty section means you found nothing, so don't write "the code is correct" as if you'd proved it. Never make me infer emptiness from absence.

### The overview — the first section, every CR

What the branch does as a whole at HEAD and what the CR was given, in
plain words a teammate reading release notes would follow - no
file, function, flag or SHA. Under the CR's title, which names the repo
and the branch by its full name, so a CR read on its own says what it
judged:

```
# Repo <repo> branch <branch> CR

# Overview

**What the branch does:**

- **1.** <what someone who never opens the diff gets when it merges>
- **2.** <the next thing they get>

**Given:** <the spec, one per line, or "the branch only - no spec">
```

- **The title names the repo, never the folder the review ran in.** The
  repo's name is the folder that holds the git directory every checkout of
  it shares, which `git rev-parse --path-format=absolute --git-common-dir`
  prints - or, for a bare repo, that directory's own name without `.git`.
  A review that ran in a worktree - a checkout whose own `--git-dir` is not
  that shared directory - adds its folder in a bracket, `# Repo <repo>
  (worktree <folder>) branch <branch> CR`, so every CR of one repo carries
  one name and the title still says where the code was read.
- **What the branch does comes first**, in bullets: everything someone
  who never opens the diff gets when it merges, the most important first.
  A branch that does one thing gets one bullet, still numbered. The
  bullets judge nothing: the calls are the sections'.
- **Given** names what the CR was handed besides the branch: a plan, a
  ticket, a request or hand-off file, an MR link, one per line. It is the
  one place the CR names its spec.

### The changes — after the overview, every CR

One entry per distinct thing the branch does, judged as it lands. A
branch that does one thing gets one entry; several changes get one each,
never folded into one entry where a weak part hides behind a strong one.

```
# Changes

• **CH1** <one thing the branch does, in plain words>
✅ Keep it
**Change:** **Evidence:** LIKELY · **Size:** medium · **Difficulty:** hard
**Work:** **C1**, **C2**

• **CH2** <the next thing the branch does>
🔧 Needs fixes (**C3**'s 🔴) (⛔ Hard blocker: code)
**Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
**Work:** **C3**, its 🔴
```

- **Each entry is a `•` paragraph opening with its bold number, never a
  markdown list item**: `• **CH1**`, the sentence, then its call, its
  Change Profile and its Work line, one per line, and a blank line before
  the next entry. A terminal drops the blank line between list items, and
  the entries run together; the number is how I answer an entry.
- **Each entry carries a call on that change as it stands at HEAD**, one
  of the change calls of "The calls and Profiles of a CR": what to do with
  this part, never whether the branch merges. The call carries nothing but
  its bracket, which says what the change needs, and its blocker badge
  when it holds the merge.
- **Under the call, a Change Profile on that change as it lands**: whether
  it works once every commit it lives in is in, how much it touches and
  how hard it is to get right. A commit's Profile judges the commit alone,
  and what a fix costs is in the commit's row.
- **The call follows the commits it names.** `✅ Keep it` only when every
  one of them is `✅ Ship it`, `👌 Fixed later`, `🪓 Split`, `📝 Reword` or
  `🔀 Squash into`; `🧪 Needs test` when one or more is `🧪 Needs test` and
  the rest are among those, naming the run; `🙋 Needs your call` when one
  is, naming the decision; any other commit call makes it `🔧 Needs
  fixes`, naming the commit and what it needs, unless the change itself
  earns `⚖️ Close call`, `✂️ Carve out` or `❌ Drop it`. An entry never
  reads greener than a commit it lives in, even when that commit changes
  nothing in the tree. The case that taught it, a branch whose only extra
  commit was a back-merge of the default branch that carried no change:

  ```
  ❌ ✅ Keep it
     with `<sha>` 🗑 Drop (carries no change), Blocker ⛔ Hard: drop, in
     the In short table
  ✅ 🔧 Needs fixes (drop the back-merge `<sha>`) (⛔ Hard blocker: drop)
  ```

- **✂️ Carve out is the split recommendation.** Work that is sound but does
  not land with this branch moves to a branch of its own, and the rest
  merges once it is moved. The review recommends the split; whether to
  make it is mine.
- **The Work line names every commit the change lives in**, in branch
  order, with the finding that carries its fix where one does. A commit
  that serves two entries is on both lines.
- **These entries judge the outcome, so a broken branch shows up here.** A
  `❌ Drop it`, or a Change Profile whose Evidence is below `CONFIDENT`,
  under commits of nothing but `✅ Ship it` means the commits are missing
  a finding or a `🗑 Drop`: find it on the commits the entry names and put
  it on the one that should carry it.

### The spec tables — Goals, Contract, Readiness, Incidents, every CR

**A CR is given a spec when the request names what the branch
implements**: a plan, a ticket, a request or hand-off file - a plan goal's
CR subagent gets it with the repo. A branch whose every commit ships can
still leave a promise undelivered, so what the spec promises is judged on
its own, in four tables. Each takes from the spec only what the spec
states:

| # | Section | Its rows, numbered | Taken from the spec's |
|---|---|---|---|
| **1** | `# Goals` | **G** - one per outcome | goals: a plan's "Goals and non-goals", or each outcome a ticket or request asks for, or each step when it lists steps, judged done or not |
| **2** | `# Contract` | **A** - an API the branch adds, changes or removes; **IV** - a constraint or invariant | contract: its API, its constraints and invariants |
| **3** | `# Readiness` | **SE**, **HA**, **OP** - one per security, high-availability or operability claim | answers on security, high availability and operability |
| **4** | `# Incidents` | **IN** - one per known incident | known incidents, each with the status the spec gives it |

Every table has the same columns:

```
# Goals

| # | Goal | How we know | Work | Call | Blocker |
|---|---|---|---|---|---|
| **G1** | <the goal, in plain words> | <the test, run or read that showed it> | **C2**, **C3** | ✅ Met | - |
| **G2** | <the next goal> | - | not built: <what the new commit adds> | ⏳ Not reached (<what is missing>) | ⛔ Hard: code |
```

`# Contract` heads its second column "The promise", `# Readiness` "The
claim", and `# Incidents` "Incident", with a column after it, "The spec
says", holding the status the spec claims.

- **How we know** - what showed the call: a test the review ran, a run, a
  read of the code at HEAD. A dash when nothing on the branch could be
  checked.
- **Work** - where the work lives, as "The CR's sections" says.
- **Call** - one of the spec-row calls of "The calls and Profiles of a CR".
- **Blocker** - what the row holds, as "Hard and soft merge blockers"
  gives it.
- **The API rows are there with or without a spec.** Every API the branch
  adds, changes or removes gets an **A** row, so a break shows whether or
  not anyone promised otherwise. With no spec, its call says whether an
  existing caller keeps working: ✅ Additive or ❌ Breaks callers.
- **A non-goal gets no row.** A branch that does one is an entry that does
  not belong: ✂️ Carve out or ❌ Drop it.
- **A row that does not hold is also a finding**: ❌ Missed and ❌ Breaks
  callers are a 🔴 or 🟠 on the commit that should carry the fix, so its
  call blocks. One under commits of nothing but `✅ Ship it` means the
  commits are missing that finding. An incident the spec calls Solved,
  whose mechanism the branch does not hold, is ❌ Missed.
- **A row not met holds the branch.** ⏳ Not reached makes the branch's call
  ⏳ Finish the work first; ❌ Missed and ❌ Breaks callers block through
  their finding; 🧪 Met untested makes it wait for the run. A spec merged
  in stages moves what a stage does not deliver to its TBD first.
- **A table the spec has nothing for says so**, in one line: "No spec
  given - nothing to check the branch against." when no spec was given,
  "The spec states no <rows>." when it is silent there. The Contract table
  keeps its API rows above either line.

### The Design and Implementation tables — before the commits, every CR

**Every rule of `clean-code.md` gets a row at the level its break lives, in
the same order in every CR**, so the two tables show at a glance which rules
the branch keeps, which it breaks, and which it never touches. `# Design`
judges the structure - who owns what, what state is kept and who writes it,
how the parts call each other - and `# Implementation` judges the lines:

```
# Design

| # | Rule | How we know | Work | Call | Blocker |
|---|---|---|---|---|---|
| **DS1** | responsibilities | read of the client and the router against the plan's | **C1** | ✅ Holds | - |
| **DS11** | one owner for each piece of state and config | read of where the timeout is set | **C2**, its 🟠 | 🟠 Broken (the config and the client both own it) | ⛔ Hard: code |

# Implementation

| # | Rule | How we know | Work | Call | Blocker |
|---|---|---|---|---|---|
| **IM3** | internal names mean one thing, literally | read of the new helpers' names | **C3**, its ⚪ | ⚪ Broken (`wait` also counts) | - |
| **IM4** | comments say only what the code cannot | read of every comment the branch adds | **C3** | ✅ Holds | - |
```

**The rows, in the order and with the numbers every CR gives them**, each
with the section of `clean-code.md` it judges, its usual colour and when a
break of it blocks:

| # | Rule | Section | Usual | Blocks (🟠, or 🔴 when the failure can be shown) when |
|---|---|---|---|---|
| **DS1** | responsibilities | Responsibilities | 🟠 | a responsibility with no owner, or code whose owner, state or interface is not the plan's |
| **DS2** | one reason to change | One reason to change | 🟡 | a change you can name elsewhere would break this code |
| **DS3** | a small interface, a lot behind it | A small interface, a lot behind it | 🟡 | another service or repo will call the interface, and it exposes what a later fix would have to take back |
| **DS4** | solid, not fragile | SOLID vs fragile | 🟡 | a small change you can name elsewhere breaks it far away, or leaves it silently wrong |
| **DS5** | one result, all or nothing | One result, all or nothing | 🟠 | always: a half-done result is corrupt state |
| **DS6** | fail fast, parse at the boundary | Parse at the boundary, and "Fail fast" under Over-engineering | 🟠 | always, once a bad state reaches deep code; 🟡 while nothing reaches it yet |
| **DS7** | asyncio, and one lock at a time | Asyncio, and One lock at a time | 🟠 | always: a deadlock, a blocked event loop, or a value gone stale across an `await` |
| **DS8** | self healing | Self healing | 🟠 | a copy a lost event or a crash leaves wrong, with nothing to bring it back |
| **DS9** | every wait has a bound | Every wait has a bound | 🟠 | always: a wait with no bound holds a worker with nothing to free it |
| **DS10** | no mechanism nobody asked for | Over-engineering | 🟡 | never: the code works, it is only bigger than needed |
| **DS11** | one owner for each piece of state and config | One source of truth | 🟡 | the copies already disagree, or one will drift with nothing to catch it |
| **DS12** | public names say what is true | A name means one thing, literally | 🟡 | a label or status value false for some case, not shipped yet |
| **IM1** | no option, parameter or abstraction nobody asked for | Over-engineering | 🟡 | never: the code works, it is only bigger than needed |
| **IM2** | no value or logic written twice | One source of truth | 🟡 | the copies already disagree, or one will drift with nothing to catch it |
| **IM3** | internal names mean one thing, literally | A name means one thing, literally | 🟡 | never: only the next reader pays |
| **IM4** | comments say only what the code cannot | Comments in code | 🟡 / ⚪ | never |
| **IM5** | the plain version wins | The plain version wins | 🟡 | never |
| **IM6** | every bad path is counted, then logged | Every bad path is counted, then logged | 🟠 | always: a failure nobody can see |
| **IM7** | a check costs what its answer is worth | A check costs what its answer is worth | 🟡 | it sits on a hot path |
| **IM8** | tests check the contract, not the code | Tests check the contract, not the code | 🟡 | a bug fix with no test that reproduces it, when a unit test could |
| **IM9** | enums over strings | Enums over strings | 🟡 | a string value already misspelled somewhere |

- **A section that holds at both levels gives a row in each**, worded for
  that level: Over-engineering (**DS10**, **IM1**), One source of truth
  (**DS11**, **IM2**) and A name means one thing (**DS12**, **IM3**). A break
  goes in the row of the level it lives at, never in both: a cache nobody
  asked for is **DS10**, an unused parameter **IM1**.
- **DS1 judges the code against the plan's responsibilities.** With no plan
  given, it reads ➖ Irrelevant, "no plan given", and the rows under it
  still judge the structure.
- **Call** - ✅ Holds, a colour and Broken with what is broken, or
  ➖ Irrelevant when the branch's code never touches the rule; "How we
  know" then says why, such as "the branch takes no lock".
- **Blocker** - what a break holds, as "Hard and soft merge blockers"
  gives it; `-` for a row that holds nothing.
- **A rule broken is a finding** on the commit that should carry the fix,
  under its colour; the row's Work cell names it. A break no single commit
  owns - two commits that each add a copy of the same logic - goes on the
  later commit, or, when the fix is a refactor of its own, the Work cell
  says what is not built yet.
- **The colour of a break is decided by two questions**, never by the rule:
  can I name the scenario where it hurts a user or an operator, and does
  the fix get more expensive once this merges? A yes to either is
  MUST HAVE - 🔴 when the failure can be shown, 🟠 when only its trigger
  can be named. Two no's is NICE TO HAVE - 🟡, or ⚪ when only the next
  reader's eye pays. The rules table above gives each rule's usual answer.

### The commits — In short, then In detail, every CR

`# Commits` holds two parts: `## In short`, one table that gives every
commit in one line, then `## In detail`, every commit's review in the
shape "Mandatory output shape per commit" gives, in branch order.

```
# Commits

## In short

| # | What the commit does | Findings | Call | Blocker |
|---|---|---|---|---|
| **C1** | `<sha>` <one sentence> | 🔴 1 · 🟡 2 | <call> | <blocker> |
| | **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **Fix 🔴🟠:** <the fix> · **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> · **Fix 🟡⚪:** <the fix> · **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | | |
```

- **The head row** is the commit, its findings, its call and its blocker,
  nothing else.
  **The second row** puts the Commit Profile under the commit, the Fix
  Profiles under the findings they answer, and leaves the cells under the
  call and the blocker empty, since neither carries Evidence; its `#` cell stays empty, which
  is what makes it read as part of the row above. A table cell cannot hold a line break, so the lines are rows.
  The column names what a cell holds, so the Commit and Bycatch Profiles
  drop their label there; the two Fix Profiles keep theirs, since they
  share one cell. A commit with no findings leaves that cell empty: its head
  row already says so.
- **#** — **C1**, **C2**, **C3** down the table in branch order, in bold, so I answer a row by
  its number; the same number heads the commit's review under `## In detail`.
- **What the commit does** — one sentence on what the diff actually does,
  verified against it. Never the subject line pasted in: the subject may be the
  very claim the review flagged as false.
- **Findings** — the commit's FINDINGS line without the word: `🔴 1 · 🟡 2`,
  `🧪 1`. With none, it reads `✨ Gucci` beside ✅ Ship it, where it says
  the commit goes in as it is, and `none` beside any other call. A commit
  with a 🧪 puts its `Test 🧪` Profile in the cell under it, after any Fix
  Profile.
- **Call** — the call of that commit's Full Assessment on the head row, with
  the reason in a few words for anything other than ✅ Ship it, which
  carries a bracket only when a commit squashes into it, in the shape of
  `assessment.md`. The commit call is picked by these
  rules:

| Call | When |
|---|---|
| `✅ Ship it` | no 🔴, 🟠 or 🧪, and it does one thing |
| `👌 Fixed later (by <sha>)` | its 🔴 or 🟠 are fixed by a later commit on the branch, named in the bracket. Alone it says who fixes it, never that a squash follows; the bracket adds `which squashes in` when one does |
| `🔧 Needs change` | a 🔴 or 🟠 in the code, and amending this commit fixes it. A 🧪 beside it keeps its `Test 🧪` Profile, and the run waits for the fix |
| `🙋 Needs your call (<the decision>)` | a 🔴 or 🟠 whose fix is a choice only I can make, written out as "🙋 Your call" says. It outranks 🔧 Needs change: the other fixes wait on the answer |
| `🧪 Needs test (<the run>)` | no 🔴 or 🟠, and a 🧪 UNTESTED finding. Once I accept the commit untested, the bracket reads `accepted untested`, and the call stays: the commit is still unrun. A commit that also needs 🪓 Split or 📝 Reword keeps this call, and its reason names the other need too. A `🔀 Squash into` or `🗑 Drop` keeps its own call, and the 🧪 moves with a squash to the commit it lands in |
| `🪓 Split (<the parts>)` | no 🔴 or 🟠, but it does more than one thing a reader, a revert or a bisect would want apart - the one-thing test in `commits.md`. It works as it is, so it blocks nothing. A `Bycatch:` bullet that is not one simple line is the usual sign. A commit that also has a 🔴 or 🟠 is `🔧 Needs change`, and its reason names the split too |
| `📝 Reword (<the reason>)` | no 🔴 or 🟠, but its message is false or misleading - a 🟡 in the message with the code right. Only the message changes, so it blocks nothing. When the message and the code disagree, the review says which side is wrong before it picks the call: the code right and the message not is this call; the message describing what the code should have done and the code not doing it is a 🔴 or 🟠 on the code and `🔧 Needs change`; and no way to tell which was meant is a 🟠 on the commit and `🔧 Needs change (message and code disagree)`, the finding stating both readings, what would settle it, and a fix for each |
| `🔀 Squash into <sha> (<which message survives>)` | it only exists because another commit on the branch got something wrong or left it half done, or the two read better as one — apart they hide what the branch does — the squash rule in `commits.md`. Never a fix for a bug that reached the default branch or a release, which stands alone in either direction. It works as it is, so it blocks nothing. A commit that also has a 🔴 or 🟠 is `🔧 Needs change`, and its reason names the squash too |
| `🗑 Drop` | the branch is better without it: nothing needs it, a later commit undoes it, or it is out of scope |

The later commit's call is picked by its own row of this table: carrying the
fix makes it neither a squash nor a ship. It is `🔀 Squash into` the commit
it fixes only when it exists because that one got something wrong, and
`✅ Ship it` when it stands on its own and fixes the earlier one along the way.
The earlier commit's 👌 Fixed later is the same either way.

**Which way a squash goes is the reviewer's pick**: into the commit the
change reads best in, earlier or later. The call sits on the commit that
moves, its SHA names where it lands, and both rows of the pair say so:

- **The commit that moves** says which message survives:
  `🔀 Squash into <sha> (fixes it, keep its message)` when it exists only
  to fix the other, whose message stays as it is, or
  `(one change with it, new message)` when the two are one change and one
  message is written for both.
- **The commit it lands in** adds `(<sha> squashes in)` to its call:
  `✅ Ship it (<sha> squashes in)`, or `👌 Fixed later (by <sha>, which
  squashes in)` when the fix is the commit that moves.

So the In short table reads as the rebase it recommends: ✅ Ship it and
👌 Fixed later a `pick`, 🔀 Squash into a `fixup` or a `squash` beside the
commit it names, 🗑 Drop a `drop`, 📝 Reword a `reword`, 🪓 Split an `edit`,
and every other call a `pick` once its fix or its run is in.

**Blocker** — what the commit holds, as "Hard and soft merge blockers"
gives it; `-` for a commit that holds nothing.

The call agrees with that commit's FINDINGS line: never `✅ Ship it`,
`🪓 Split` or `📝 Reword` while the line counts a 🔴, a 🟠 or a 🧪. `👌 Fixed
later` is the one call that carries one, the one its named commit fixes. A
single-commit CR still has a two-row table. The sections and the
ending's section calls are the only summaries allowed in a CR: no prose
under a table, but for the one line an empty section gives.

### The bycatch table — after the commits, every CR

The commits are judged under `# Commits`. The bycatch table holds what the review
turned up on the way that the branch neither introduced nor depends on, and
that is still open at HEAD: a pre-existing bug in a file the branch touched,
a stale or false doc next to the change, a trap the diff happened to expose.
Two tests decide it, and only what fails both is bycatch:

1. **The branch introduced it** - blame it, never guess: a finding on that
   commit, whatever it touches. The branch's own work is always judged.
2. **It stops what the branch delivers from working well**, whoever
   introduced it: a 🔴 or 🟠 finding on the commit that should carry the
   fix, marked pre-existing, as "Who introduced it" says above.

The table, its columns, its calls and its Profiles are `bycatch.md`'s,
beside this file, which also says which rows of the session's bycatch file
the table carries as well; it sits under its own `# 🎣 Bycatch` heading. A
repeat CR keeps a carried row's number and gives a new row the next free
one, so my earlier answers still point at the right rows. 🔧 Add fix is a
new commit on this branch, once I ask for it - by name, or by handing the
CR over to be fixed, as "To do" says which.

**A problem the branch already fixes is not bycatch.** Its fix is part of
the commit that carries it - a commit of its own, or a `Bycatch:` line in
another commit's message, the bycatch rule in `commits.md` - and
is reviewed in that commit's findings. It never gets a row, and "fixed" is
never a call - both bycatch calls are work still to do. A row the branch fixes
in part keeps only the part still open, worded as though the fixed part
was never there. A repeat CR drops a row the branch has fixed since; the
rows left keep their numbers.

The case that taught it, a CR whose branch had already fixed two of its
three rows:

```
❌ | **B1** | Panel 12 double-counted during a pod overlap. | 🟡 1 | Fixed by `<sha>`. |
   | **B3** | Standby passes stamp the last-pass timestamp. The board side is now covered by tile 30. The code half is still open. | 🟠 1 | ⏸ Leave for now (...) |
✅ | **B3** | Standby passes stamp the last-pass timestamp (`internal/looprun/metrics.go`). | 🟠 1 | ⏸ Leave for now (...) |
```

When nothing is open, the heading stays and the table is one line instead:
"No bycatch." Never skip it silently - an absent section reads as
"did not look".

### To do — before the summary, every CR

**Every piece of work the CR asks for, in one section**, so neither I nor
a session handed the CR to fix has to gather it from the sections above. A
row says what to do and points to where its detail lives; it never repeats
the fix a finding writes out. The section has two tables: what holds the
merge, and what does not, so a ✅ Merge it above optional work never reads
as a contradiction.

```
# To do

## Before it merges

| # | What to do | Where | Who | Fix Profile | Blocker |
|---|---|---|---|---|---|
| **TD1** | decide: <the question> | **C1**'s 🟠 (A2) | 🙋 Your call | **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | ⛔ Hard: decision |
| **TD2** | <what the fix does> | **C3**'s 🔴 (G2, IN1) | 🔧 Fix (product code) | ... | ⛔ Hard: code |
| **TD3** | <what the new commit adds> | new commit (G3) | 🔧 Fix (new commit) | ... | ⛔ Hard: code |
| **TD4** | run <the run> on the branch | **C2**'s 🧪 (HA1) | 🧪 Run | ... | 🚧 Soft: untested |

## Optional

| # | What to do | Where | Who | Fix Profile |
|---|---|---|---|---|
| **TD5** | <a cheap clean-up> | **C3**'s 🟡 (IM3) | 🔧 Fix (rename) | ... |
| **TD6** | <a bycatch fix> | **B1** | 🔧 Fix (docs) | ... |
```

- **Before it merges** holds every row that holds the merge: a 🔴 or 🟠, a
  row not built, a run, a decision. With none, it is one line: "Nothing
  blocks the merge." A bycatch row never holds the merge, whatever its
  colour, since the branch call leaves bycatch out: it goes under
  Optional, a 🙋 Your call row included, and Optional is worked through
  like the rest, as "What it holds" below says.
- **Optional** holds the rest. With none, it is one line: "Nothing
  optional."

**What it holds** is exactly what a session handed the CR to fix does:

- **1.** every 🔴 and 🟠 finding;
- **2.** every row of a spec table that is not built yet, as a new commit;
- **3.** every 🧪 UNTESTED finding, as its run - a 🧪 Run row when its
  Test Profile's Size is small or medium, a 🙋 Your call row when it is
  large or more;
- **4.** every 🟡 and ⚪ finding whose fix is cheap;
- **5.** every bycatch row whose call is 🔧 Add fix: a 🔧 Fix row when
  its fix's Evidence is at least LIKELY, its Difficulty easy or super
  easy and its Size medium or less; a 🙋 Your call row, "fix it now or
  leave it?", for every other - a large or hard one is always mine;
- **6.** every ⏸ Leave for now row whose fix is cheap.

**A fix is cheap when its Fix Profile reads super easy, or small and easy,
and its Evidence is at least CONFIDENT.** A NICE TO HAVE or ⏸ Leave for
now fix the review only believes would work - LIKELY or below - is not
cheap, however small: fixing it untried is the new bug the fix scope
exists to avoid. A 🔧 Add fix has the bar of item 5, since the reviewer
already recommends it.

Anything optional beyond that - a 🟡 whose fix is medium, hard or not
CONFIDENT, a ⏸ Leave for now that is not cheap - stays in its own
section: not fixed, not asked about, and fixed only when I ask for it. A
🔧 Add fix is never left that way: the reviewer recommends it, so it is
fixed or asked.

- **#** - **TD1**, **TD2** down both tables in one count: within each,
  🙋 rows first, since a decision holds things up more than a known fix.
- **Where** - the finding, the bycatch row or "new commit", and in
  brackets the rows of the sections above it closes.
- **Who** - who acts, and how:
  - **🔧 Fix** - a session changes the code, as the finding writes the fix
    out, or writes the new commit the row names. Its bracket says what the
    fix edits, read off the fix as the finding writes it: `(product code)`,
    `(test code)`, `(rename)`, `(docs)`, or `(new commit)` for a row not
    built yet;
  - **🧪 Run** - a session runs what the 🧪 finding names and reports the
    result, when the run is small or medium and needs nothing only I
    have. A large run, or one that needs a cluster, a deploy or a
    credential, is 🙋 Your call, with the exact command for me: a long
    run is mine to start;
  - **🙋 Your call** - a decision only I can make; the question and its
    options are written out under the finding, as "The calls and Profiles
    of a CR" says.
- **A fix that needs a history rewrite is never a row.** A reword, a
  squash or a split of a commit below HEAD, or a rebase onto a moved
  base, stays where the review already says it: the commit's call -
  📝 Reword, 🔀 Squash into, 🪓 Split - and its finding. The CR recommends
  it and never asks me about it: a rewrite starts only on my words. That
  a branch is behind its base is no finding; when it matters, it is one
  line of fact in the overview.
- **Fix Profile** - the Evidence that the fix would work, and its Size and
  Difficulty; for a run, Size says how long it takes, not how hard it is.
- **Blocker** - under Before it merges only: what the row closes, as
  "Hard and soft merge blockers" gives it, so I see which rows hold the
  merge because the code is wrong and which owe lighter work. Optional has
  no Blocker column, since its rows hold nothing.

With nothing in either table, the heading stays and the section is one
line: "Nothing to do."

### The ending — after To do, every CR

**The CR closes on its verdict, stated once, under `# Summary`**: the
section calls, then the branch call, then the line naming its file that
`SKILL.md` gives, so the path is the last line of every view and the
verdict sits right above it. Every view of a CR ends with it, a CR Brief
included.

```
# Summary

| # | Section | Calls | Blocker |
|---|---|---|---|
| **SC1** | <a section's title> | <each call its rows carry, with its count> | <the worst blocker its rows carry, or -> |

**Branch call:** <the branch's call (what holds the merge, by level and kind) (its badge)>

<the line naming the CR's file, as SKILL.md gives it>
```

- **The section calls show where the branch call came from**: one row for
  each section whose rows or entries carry a call of "The calls and
  Profiles of a CR", in the order "The CR's sections" gives them, titled
  as its heading is.
  - **Calls** - every call the section's rows carry, each with how many
    rows carry it, the calls that hold the merge first: `🔧 Needs fixes 1
    · ✅ Keep it 2`. A section with no rows reads ➖ and its one line, such
    as "➖ (no spec given)".
  - **Blocker** - the worst level a row of the section carries, with
    every kind at that level, as "Hard and soft merge blockers" gives it:
    `⛔ Hard: code, test code`, and `-` when it has none. Which row it is,
    and what clears it, is To do's to say.
- **The branch call** is one of the branch calls of "The calls and
  Profiles of a CR", answering whether the branch merges, and follows
  from the sections as that list says. It is never a judgement of its
  own.
- **Its bracket names what holds the merge, by level and kind**, so the
  branch call says whether the code is wrong or lighter work is owed: the
  hard blockers first, then the soft, each kind with its To do rows, the
  kind as their Blocker cell gives it - `hard - code: **TD1**, test code:
  **TD2** · soft - untested: **TD3**` - and what To do never lists by its
  own row: `drop: **C4**`, `carve out: **CH2**`. The call carries the
  badge of its worst blocker, with every kind at that level, and a ✅ Merge
  it names nothing, since nothing holds it.

### Rules that keep the tags honest

- **No severity inflation.** If you cannot write the concrete failure scenario, it is not a 🔴 BUG - downgrade it. Dressing a nit up as a bug wastes my time and destroys my trust in every other tag in the review.
- **No severity deflation.** Never bury a 🔴 inside a nit list and never soften it ("might be worth considering..."). If it's broken, the first words are "🔴 **BUG**:".
- **Verify before tagging 🔴.** Read the code path, grep the callers, check HEAD. If you couldn't verify, tag it **🔴 BUG (UNVERIFIED)** and state exactly what you couldn't check.
- **✅ Ship it, 🪓 Split and 📝 Reword need executed evidence, not reasoning.** Every runtime claim a commit's correctness rests on - a path resolving, a command working, a permission rule firing, a script running from another directory - is proven by running or rendering it before the assessment, and the review names the command that proved it. "The docs say so" is a reason to expect it works, not proof that it does. A command that changes state is proven by its dry run or render, or handed to me to run - never run to prove it.
  **Every test you can run yourself is run before the assessment, as `assessment.md` says - without asking and without reporting it as a finding.** A local command, a render, a dry run, a script run from a scratch directory, a read against something already reachable: run it, and the review names the command and what it showed. A run is left to me only when its proof genuinely needs me: something only I can supply (a cluster, a machine, a credential, a setting), a command that would change state with no dry run, or a test long or costly enough that it is worth my decision. What the claim becomes depends on what you found when you traced it:
  - **You traced it and found nothing wrong**: a **🧪 UNTESTED** finding. It names the claim and the command that would prove it, and gives the commit `🧪 Needs test` until it is run; once I accept it untested, the call reads `🧪 Needs test (accepted untested)`.
  - **You have a doubt you can name**: a **🟠 RISK (UNVERIFIED)**. It names the doubt, the claim and the command that would settle it, and blocks ✅ Ship it until it is run or I accept it as untested - and accepting it changes no colour: it stays a 🟠 I chose to merge past.

  A 🧪 or an UNVERIFIED finding for a test you could have run in seconds is a review you did not finish.
  Every 🧪 and every UNVERIFIED finding carries three lines, so I can decide whether the test is worth running or the claim is safe to accept untested:
  - **Cost** - moderate or hard, and what it needs: the command, how long it takes, and what I have to supply or what it would change.
  - **Sure without it** - an Evidence level from `assessment.md` and the reason: which parts of the claim are already proven and what rests on reasoning alone.
  - **Sure with it** - an Evidence level, and what would still be unproven after the test passes.
- **A CR is always finished.** A run it cannot make - a hook refuses it, it
  takes too long, it needs what only I have - never holds the CR back and
  never ends the reply with a question about it: the claim is a 🧪
  UNTESTED finding, To do gets a 🧪 Run row with the exact command, and
  every section is written in full with what the review did reach. The
  session handed the CR runs it.
- **State confidence when you're unsure**, as an Evidence level from `assessment.md` and what backs it: "🟠 RISK (CONFIDENT)" vs "🟠 RISK (50-50 - couldn't reproduce)". Never hide uncertainty behind vague wording, and never let low confidence silently turn a 🟠 into a 🟡.
- **Where the borderline cases land:**
  - Weak/vague commit message → 🟡. Commit message making a false claim about behavior → 🟡 too, the code works; the commit's call is 📝 Reword, and the Fix 🟡⚪ line names the new message. A message the code disagrees with is coloured by which side is wrong - the 📝 Reword row of the commit calls says how - and when you cannot tell, the doubt is a 🟠 on the commit. Docs that now lie about behaviour → 🟡, unless the lie makes someone do harm, which is a 🟠 as a silent failure.
  - Missing log, or wrong log level → 🟡. Metric defined but never called, or called on only some code paths → 🟠 (blind in prod).
  - Redundant comment, YAML whitespace/blank lines, ordering, style preference → ⚪. Genuinely misleading name or a DRY violation someone will trip over → 🟡.
  - A name that holds more than its words say, is named for a cause instead of a meaning, or kept its name after its meaning changed (see "A name means one thing, literally" in `clean-code.md`) → 🟡. A reader already acting on the literal word and doing the wrong thing → 🔴 for that reader, with the rename as the fix. A label (enum, metric label value, status word) whose words are false for some case that produces it → 🟡.
  - Clever code a plain version replaces with the same behaviour → 🟡. Clever code hiding a bug you traced → 🔴 for the bug, and the plain version is the fix.
  - Suspicious logic you traced and it's genuinely wrong → 🔴. Suspicious logic you can't prove either way → 🟠, and say what would prove it.
  - Perf: measurable regression on the per-request path → 🟠 minimum. Cold path → 🟡.
  - Tests: a test coupled to the implementation (private state, mocked internals, a whole-object snapshot), or a test of nothing the component promises → 🟡. A bug fix with no test that reproduces it → 🟠 when a unit test through the component's public interface could fail on the unfixed code: the bug can come back and nothing will notice. When none could - a race, a failure only a live cluster shows, a fix to config alone - it is 🟡, and the bracket names which of those it is. A test that cannot fail on the bug it is named for (the expected value computed with the code's own formula, the unit under test mocked out) → 🟠: it reports green while the thing it guards is broken. "Tests check the contract, not the code" in `clean-code.md` says what a good one checks.
- **Still report the nits.** NICE TO HAVE ≠ "don't mention". Put them below the divider where they can't be mistaken for real problems.
- **🟠 is not a wish list.** If everything is 🟠, the colour means nothing and I'll start ignoring it. Be willing to write 🟡 and stand behind it.

### What to Review (inspect in this order - but report by severity, never in this order)

This is the checklist order for *looking*, not for *writing the review*. Commit messages are first to inspect and nearly last to report - a lowercase-subject nit never appears above an IndexError.

Each category below has a **default severity** - deviate only with a stated reason.

1. **Commit Messages & Descriptions** [default: 🟡; a false claim about behavior is 🟡 too, and makes the commit's call 📝 Reword]
   - **The full standard is in `commits.md` — read it before judging a commit message.** Subject line rules, body structure, accuracy checks and format all live there.
   - The accuracy checks are the ones that make a message false: does the message match what the code actually does, are there false claims, is the explanation backwards or misleading, does it mention all significant files changed?

2. **Critical Bugs** [default: 🔴 if you can show the failure, 🟠 if you can only name the trigger condition]
   - Will this break production?
   - Are there metrics defined but never called?
   - **When functions/methods/metrics are removed: verify they're not called anywhere in HEAD**
   - **Check if later commits on the same branch broke what this commit did correctly**
   - Are there function calls with wrong parameters?
   - Any nil pointer risks?
   - Race conditions or concurrency issues?

3. **Security** [default: 🟠, a leak or bypass you can show: 🔴]
   - **Ask every question in `security.md`** of the diff and of the component it lands in.
   - An exposure the branch did not introduce goes into the bycatch table, unless it stops what the branch delivers from working well - then it is a pre-existing finding on the commit that should carry the fix. Never dropped because it is pre-existing.

4. **Metrics & Observability** [default: 🟠 for missing/partial metric calls and wrong metric type, 🟡 for naming]
   - Is every bad path counted, and the unit of work too? "Every bad path is counted, then logged" in `clean-code.md` says what counts as one
   - Are metrics called before logs? (metric-first pattern)
   - Are metric names/labels correct?
   - Right metric type? (Counter vs Gauge vs Histogram)
   - Any missing metric calls?

5. **Logging** [default: 🟡, missing context on an error path that would block debugging prod: 🟠]
   - Is every metric accompanied by a log?
   - Log levels correct? (INFO vs WARNING vs ERROR)
   - Consistent formatting across similar log messages?
   - Include all necessary context (pod_name, pod_ip, model_name)?

6. **Design and implementation** [default: the row's usual colour in "The Design and Implementation tables"]
   - **Ask every rule of `clean-code.md` of the change**, and give each its call; "The Design and Implementation tables" number the rows and give each one's usual colour and when a break of it blocks.
   - Ordering issues? (should things be grouped differently?)
   - Naming clarity? Does each name mean one thing, literally, that a cold reader gets from the name alone? A name that only a comment explains is the wrong name: make it longer or split it. Any state that hides a compound condition, is named for its cause, or kept its name when a change shifted its meaning? When a diff changes what a field means, grep every reader of it.
   - Any TODOs or FIXMEs that shouldn't be there?
   - **Redundant comments**: the comment rules and their worked examples are in `clean-code.md`. Flag any comment that states the obvious or repeats what code/logs say. When in doubt, the comment should be deleted.
   - **Inconsistent spacing/indentation in YAML/config files**:
     - Check for extra blank lines between similar sections (e.g., model entries in config)
     - Flag trailing whitespace (spaces after content on a line)
     - Verify consistent indentation (2 spaces for YAML, not tabs or 4 spaces)
     - Example violations: random blank line between two model entries, trailing space after `checkImage: true `
   - **Unused parameters**: Flag function parameters that are defined but never used in the body (YAGNI violation)
   - **Logical correctness of new code**: Don't just check for bugs, analyze if the logic makes sense:
     - **Question suspicious patterns**: Why access `list[0]` when there might be multiple items with different values?
     - **Trace variable usage**: Follow variables from definition to all uses - does the usage match the intent?
     - **Check assumptions**: If code assumes "first item represents all items", verify that's actually true
     - **Example**: `corrupted_pattern = text_prompts[0].get("corruptedRegex", ...)` - why only first prompt when each can have different patterns?
     - **For refactors**: Carefully analyze new logic paths, don't just check that old functions aren't called

7. **Nits** [default: ⚪ - always below the divider]
   - Minor style issues
   - Comment quality
   - Documentation gaps

### A CR asked for on a link

**When I ask for a CR on an MR or PR link, the link names what to review, not
where the review goes.** A link on its own asks for no review. The review runs
locally and its findings come back in chat:

- **The MR itself is read through its API**: the description, the review
  threads and the pipeline.
- **The code is read from git, not from the web diff.** Fetch the MR's head
  with no local destination - `git fetch origin
  refs/merge-requests/<iid>/head` on GitLab, `refs/pull/<n>/head` on GitHub -
  and pin its SHA at once with `git rev-parse FETCH_HEAD`: the next fetch
  overwrites `FETCH_HEAD`, and after a fetch of two refs it resolves to the
  first. Review that SHA with `git log`, `git show` and `git diff` against its
  target branch. Never fetch into a named ref (`<src>:<dst>`): the ref stays
  in the repo after the review. The current branch and the working tree stay
  as they are. If no checkout of that repo is open, ask where it is.
- **Nothing goes back to the link.** No note, no draft note, no inline
  comment, no suggestion, no approval, no resolved thread, no label, and no
  review tool's commenting mode. Each of those runs only when my message
  asks for that one in plain words.

### A repeat CR

**An earlier review of a commit is knowledge the CR starts from, never work
it repeats - even when I ask for the CR "from scratch".** The earlier
review is one still in this session's context, or a CR file the request
hands to the CR. While the commit's code is unchanged, what that review
found on it stands: its code is unchanged when its tree and its parent's
tree are the ones the earlier review saw, and together they pin its diff
and everything below it, so a fresh read has nothing new to find. Carry
its findings over, with one line naming the review they come from, and
spend the effort on what changed: the CR does only the work the earlier
reviews do not already answer, so the more they share with the branch,
the less it reads. Compare `git rev-parse <sha>^{tree} <sha>~1^{tree}`
for each commit with the same for the commit in its place in the earlier
CR's In short table.

**What is carried is the findings; the call is decided again.** A commit
judged on its own does not change, but the branch around it does: a later
commit that fixes its 🔴 or 🟠 turns its call to 👌 Fixed later (by
`<sha>`), and a later commit that breaks it gives it a new finding. Its
section is rewritten only where the call moved.

- **The same tip is that review.** When HEAD is the commit an earlier
  review's In short table ends on, and nothing else the CR is judged
  against - the plan it was given, a list of decisions - changed since,
  nothing is reviewed: the CR is that review, given again with one line
  on top naming it and why it stands, and its file is a copy of that
  review's file under the same line.
- **The same HEAD tree is a recut, never a review.** When HEAD's tree is
  the tree of the tip the earlier review judged (`git rev-parse
  HEAD^{tree}`), the branch's code is what was reviewed, however its
  commits were reworded, split, squashed or reordered. No code is read
  again: each code finding is carried to the commit that now holds its
  line, and each new commit gets only what a recut can break - its
  message against its diff, its one-thing boundary, and one build-and-test
  run, since a split can leave a commit in the middle that does not build.
- **The same SHA keeps its findings.**
- **A new SHA over the same trees changed only commit messages** - a reword
  of it or of a commit below it, a rebase that moved nothing else. Its code
  findings are carried; a message that changed is reviewed again, and its
  findings and call follow the new message.
- **A new tree is a new commit, once HEAD's tree has changed too**: an
  amend that changed content, a fixup folded into it or below it, a rebase
  onto a moved base. It gets a full review, tests included, even when its
  own diff reads the same as before.
- **Otherwise the interdiff is what is read.** `git range-diff <old
  base>..<old tip> <new base>..<new tip>` pairs the two versions commit
  by commit: a commit it marks unchanged keeps its review, one whose
  message alone changed gets the message read, one it marks changed gets
  the diff between its two diffs read as new code, and one with no pair
  gets a full review. A pairing that looks wrong after a heavy rewrite is
  not trusted: that commit is reviewed in full.
- **Only a review still in the context, or a CR file handed over, is
  carried.** One summarised away, or from another session, with no file
  handed over, has lost the findings it would carry; review that commit
  again. A file carries only the commits its In short table names by SHA
  and its `## In detail` reviews, since the tree test needs the commit the
  review saw; a CR Digest's, a CR Brief's or a CR Summary's file holds no
  reviews and carries none.
- **The outcome is judged afresh whenever the tip moved.** Each new or
  rewritten commit is read against the carried ones, and a carried commit
  that a later change breaks gets the finding. Every section but the
  carried reviews is rebuilt for the branch as it now stands.

The case that taught it: a second CR of a five-commit branch, after a
fixup was folded into the third commit and a sixth was added.

```
❌ every commit read again and every test rerun, for a branch where two
   commits kept their SHAs
✅ 1st, 2nd: carried from the first CR (same SHA)
   3rd-5th: new trees from the autosquash, reviewed in full
   6th: new, reviewed in full
```

And a third CR of the same branch, after a rebase that only reworded the
second commit's message:

```
❌ 2nd-6th reviewed in full because every SHA from the 2nd up moved
✅ 1st: carried (same SHA)
   2nd: code carried (same trees), new message reviewed
   3rd-6th: carried (same trees, same messages)
```

### Was it fixed? — a repeat CR after the fixes

**"Is it fixed?", or a CR asked for after an earlier one's fixes, is a
repeat CR that answers row by row, never a tick-off of the old findings.**
It starts from the earlier CR's file and reads the change as "A repeat CR"
says - a recut check when HEAD's tree is unchanged, the interdiff
otherwise. Every line changed since is new code: a fix can carry a bug of
its own, and one it opened is a finding like any other.

It is a CR in full, with one section more, right after the overview: the
earlier CR's To do, each row with what became of it.

```
# Was it fixed

| # | What was to do | Where | Now |
|---|---|---|---|
| **TD1** | decide: <the question> | **C1**'s 🟠 (A2) | 🙋 Answered (a: defaulted to 0, in **C5**) |
| **TD2** | <what the fix does> | **C3**'s 🔴 (G2) | ✅ Done (**C6**) |
| **TD3** | <what the new commit adds> | new commit (G3) | ❌ Still open (no commit adds it) |
| **TD4** | run <the run> on the branch | **C2**'s 🧪 (HA1) | 🧪 Ran (passed, <its log>) |
```

- **#**, **What was to do** and **Where** are the earlier row's, as it was
  written, so I match it to the CR I read before.
- **Now** - one of four: **✅ Done (<the commit>)**, the fix is in and what
  it answered now holds; **❌ Still open (<why>)**; **🙋 Answered (<the
  decision and its commit>)**; **🧪 Ran (<the result and its log>)**, and
  a run that failed is ❌ Still open with the failure.
- **Every section below is rebuilt for the branch as it now stands**: a
  row a fix closed reads ✅ Met, ✅ Holds or ✅ Ship it there, and the new
  To do holds only what is still open and what the fixes brought.
- **It ships on the Branch call**, as any CR: every blocking row ✅ Done,
  and nothing new that blocks.

### Review Process

**Do:**
- **Read the whole branch diff before the first commit, and judge the outcome at HEAD after the last** (see "The branch is what ships, not the commits")
- Review commits one by one (commit-by-commit)
- **When reviewing a commit, check HEAD state to verify later commits didn't break it**
- **When methods/functions/metrics are removed, verify they're not called in HEAD**
- **Read and understand new code logic** - don't just hunt for bugs, analyze whether the logic makes sense (see "Logical correctness of new code" in the checklist above)
- **Lay the CR out in the sections of "The CR's sections"**, the overview first and To do last, every section present, and one CR per repo
- **Open with the FINDINGS line and the Full Assessment, colour every finding (🔴/🟠/🟡/⚪) or mark it 🧪 UNTESTED, and split MUST HAVE from NICE TO HAVE with the divider** (see the colour section above)
- **For every 🔴, write the concrete failure scenario**: what input/state, what goes wrong, at which `file:line`
- **Say it out loud when a section is empty** - I need to hear it, not deduce it (exact wording in "Mandatory output shape per commit" above)
- **Write every SHA as its first 10 characters** (`git rev-parse --short=10`), everywhere in the CR, so one commit reads the same in every place it is named
- Order findings within each section by colour (🔴 → 🟠, then 🟡 → ⚪)
- Write out the fix for every finding and apply none (see "Writing out the fix" below)
- Be specific: show me the exact line numbers and code
- If something is wrong, say it's wrong - don't sugarcoat

**Don't:**
- Give me a recap of the findings before the findings - the FINDINGS line and the Full Assessment are the only things allowed above the details, then dive straight in
- **Mix nits in with real bugs** - if I have to guess which findings matter, the review failed
- **Colour everything 🟠 to look thorough** - that's the same trust-burning move as severity inflation
- **Call something a 🔴 BUG when you can't show it failing** - if you can still name the trigger condition it's 🟠 RISK, which blocks the merge. Only when there's no demonstrable failure and no nameable trigger does it drop to 🟡. Never let "I couldn't prove it" collapse a hazard into a nit
- **Present a clean commit as if it were dangerous** - lots of ⚪ nits is not a problem, say so
- Be vague ("there might be an issue...") - tell me what IS wrong, or tag it speculative and say why
- Skip over minor issues because "they're not critical" - report them, just below the divider
- Assume I know what you're talking about - show me the code
- Be nice if something is actually wrong - I want to know

### Example Review Flow

One commit's review, as it sits under `## In detail`:

```
### C1 · Commit 1 of 4: perf(validator): Reduce validation time by 50%

FINDINGS: 🔴 1 · 🟠 1 · 🟡 3 · ⚪ 1

- **Call:** 🔧 Needs change (crashes on an empty pod list) (⛔ Hard blocker: code)
- **Commit:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** easy
- **Fix 🔴🟠:** guard the empty list, call `record_failure()` on timeout · **Evidence:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Fix 🟡⚪:** reword the subject and body · **Evidence:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  - **1.** every lookup drops from O(n) to O(1)
- **Why Not?**
  - none beyond the findings above (checked: hashY keeps the key format)

#### MUST HAVE — 🔴🟠, blocks the merge

##### 🔴 BUG: blacklist lookup crashes on an empty pod list
`validator/hash.py:88` - `pods[0].name` runs before the empty check.
FAILS WHEN: gateway returns zero pods (happens on every cluster cold start)
→ IndexError, validator loop dies, no pod gets validated until restart.
VERIFIED: traced from `validate_all()` at line 40; nothing guards the call.
[show code]
Fix: [show fix]

##### 🟠 RISK: failure metric never fires on the timeout path
`validator/hash.py:123` - logs "pod failed" but never calls `record_failure()`.
TRIGGERS WHEN: pod times out (the most common real failure).
→ Grafana shows zero failures during an actual outage. Blind in prod.
[show code]
Fix: [show fix]

---

#### NICE TO HAVE — 🟡⚪

##### 🟡 QUALITY: subject makes a claim the diff can't back
"Reduce validation time by 50%" is an outcome, and nothing in the body shows
where 50% comes from. Fails "If applied, this commit will... reduce validation
time" (awkward). Should be: "use hashY instead of hashX for lookups" - and the
50% goes in the body with the 100ms → 50ms numbers behind it.

##### 🟡 QUALITY: body missing the WHY
Doesn't say: hashX did O(n) iteration → CPU spikes; hashY is O(1).

##### 🟡 QUALITY: past tense in body
"Changed from hashX to hashY" → "Replaces hashX with hashY".

##### ⚪ NIT: subject capitalized
"Reduce" → "reduce".

##### ✅ Correct:
- **1.** Type is right: perf
- **2.** Has scope: (validator)
- **3.** The hashY swap itself is correct - the algorithm change is sound
```

And when it's clean, the FINDINGS line says so plainly - don't make a pile of nits look like danger:

```
### C2 · Commit 2 of 4: fix(gateway): add null check to token extractor

FINDINGS: ⚪ 2

- **Call:** ✅ Ship it
- **Commit:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** super easy
- **Fix ⚪:** delete the comment, strip the whitespace · **Evidence:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  - **1.** a request with no auth header gets a 401 instead of a 500
- **Why Not?**
  - none (checked: grepped every caller, none relied on the exception)

#### MUST HAVE — 🔴🟠, blocks the merge
None - no 🔴 and no 🟠. I traced both new branches in `extract_token()` and the
null path is handled; metric fires on every path; no callers of the removed
helper remain in HEAD (grepped).

---

#### NICE TO HAVE — 🟡⚪
##### ⚪ NIT: redundant comment
`gateway/auth.py:31` - `# check if header exists` above `if not header:` - delete it.
##### ⚪ NIT: trailing whitespace
`config/models.yaml:14`
```

### Writing out the fix

**Every fix is written out under its finding and never applied**: the diff
you would apply, the new commit message, the split. Whether a finding is
fixed now, ticketed or shipped knowingly is my call, and the fix itself is
made outside the review, as `SKILL.md` says. A fix shown under a finding
carries that finding's tags, never an assessment.

### Bottom Line

I care about my commits, because they are how the branch is read - and the branch is what ships. If something is wrong or misleading, tell me, and if the branch is not fit to merge, block the merge.

**And be unmistakably clear about two things: is it broken, and do I have to fix it now.** Three failures I hate equally:
1. Burying a 🔴 BUG in a list of whitespace nits so I merge broken code.
2. Handing me a scary-looking wall of ⚪ nits with no assessment, so I waste an hour hunting a bug that was never there.
3. Giving me 12 findings with no MUST HAVE / NICE TO HAVE split, so I have to re-triage your review myself before I can do anything with it.

Thorough, clearly triaged, and explicit about what blocks the merge. All three, every time.

That's what good code review is.
