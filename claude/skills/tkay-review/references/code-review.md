# Code Review Standards

tkay-code's `clean-code.md`, `verdict.md` and `commits.md` are the shared
references this skill's SKILL.md lists with their full paths; read them from
there.

**Read tkay-code's `clean-code.md` before the first finding.** It defines clean
code; this file says how to report a departure from it and how bad each one is.

## How I Want Code Reviews Done

When I ask for a code review (CR), I want you to be **thorough as fuck** because this is serious production code. Don't hold back, don't be nice - if something is wrong, tell me straight up.

## THE BRANCH IS WHAT SHIPS, NOT THE COMMITS

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
  the review of the commit that should carry the fix, so that commit's verdict
  blocks.
- **The commit verdicts never read greener than the outcome.** If the branch
  at HEAD is broken, at least one row of the commits table is none of
  `✅ Ship it`, `👌 Fixed later`, `🪓 Split` and `📝 Reword`: a fix that
  HEAD does not hold is no fix.
- **Squash when it makes the outcome clearer.** When reading the commits apart
  hides what the branch does - steps that only make sense together, a commit
  that is broken until a later one lands, a split that leaves the reader to
  assemble the change in their head - recommend `🔀 Squash into` even when no
  commit got anything wrong. A commit earns its place by making the outcome
  easier to understand or to bisect, not by existing. The review recommends
  every squash and split; the rewrite itself waits for my word, as
  tkay-code's `commits.md` says.

## ONE CR PER REPO

**A CR over more than one repo is one CR per repo, one after the other,
never interleaved.** Each repo gets its own four sections under a heading
that names the repo, its own branch line, and its own numbering, so
"atero-charts row 2" names one row and no row carries a repo tag. One line
above the first repo says whether the branches merge independently or in
which order. A CR Summary over several repos is split the same way.

## THE CR IS FOUR SECTIONS

**Every CR is laid out as four sections, in this order, each under its own
top-level heading:**

1. `# Findings` - every commit's review, in branch order, in the shape
   "Mandatory output shape per commit" gives.
2. `# Repo <repo> branch <branch> Overview` - what the branch does as a
   whole at HEAD; see "The branch overview".
3. `# Commits` - the verdict table, one row per commit; see "The commits
   table".
4. `# 🎣 Bycatch` - what the review turned up on the way; see "The bycatch
   table".

The last three are built from the findings: the overview and the commits
table judge what the findings found, and the bycatch is what they set
aside. A CR in the session that wrote the code opens with the ⚠️ line
this skill's `SKILL.md` gives, above everything else.

### The CR Summary

**When I ask for the "CR Summary", the reply is the last three sections,
with no `# Findings`** - and only when the CR it summarises is already
done in this session.

- **This session already reviewed the branch**: the three sections are
  rebuilt from that review under "A repeat CR in the same session". A
  commit whose review is carried stays off the screen; a commit that needs
  a fresh review brings its section back under `# Findings`, because its
  findings are new to me.
- **No CR of the branch in this session**: the summary is a full CR. Every
  commit is reviewed, and the reply is all four sections.

```
"CR Summary", after this session's CR of the branch, nothing changed since:
❌ # Findings, # Repo … Overview, # Commits, # 🎣 Bycatch - the CR again
✅ # Repo … Overview, # Commits, # 🎣 Bycatch

"CR Summary", no CR of the branch yet:
❌ # Repo … Overview, # Commits, # 🎣 Bycatch - verdicts no finding stands under
✅ # Findings, # Repo … Overview, # Commits, # 🎣 Bycatch
```

## CRITICAL: IS IT A REAL BUG OR A NIT — AND MUST I FIX IT NOW?

**One question I must be able to answer about every single finding, without reading between the lines: is this code BROKEN or merely IMPERFECT?** The colour answers it, and the colour alone decides whether the merge waits:

- **MUST HAVE** is 🔴 and 🟠. It blocks the merge: I fix it now, or I don't ship.
- **NICE TO HAVE** is 🟡 and ⚪. I ship without it; worth doing when I'm in there anyway, and my call by definition.

Nothing moves between the two: no promotion, no demotion, no bracket that makes a 🟡 block or lets a 🟠 through. A finding is headed by its colour and its claim, and the section it sits in says whether it blocks:

```
#### 🔴 BUG: <one-line claim>
#### 🟡 QUALITY: <one-line claim>
```

A wall of findings where I can't tell the colours apart is a USELESS review, no matter how thorough it is.

### The severity tags (use the exact emoji + word)

| Tag | Meaning | Bar to qualify |
|-----|---------|----------------|
| 🔴 **BUG** | Code is wrong. It will misbehave, crash, corrupt data, hang, or produce the wrong result. | You can state a concrete failure: *"input/state X → wrong output or crash at `file:line`"* |
| 🟠 **RISK** | Not provably broken today, but a real hazard: race window, unbounded growth, missing error path, perf regression on the hot path, silent failure, broken observability. Two that look like quality and are hazards: a bug fix with no test that reproduces it when a unit test could, and a label value (enum, metric label, status word) that is false for some case producing it and has not shipped yet - after it ships, renaming it breaks every dashboard and alert that reads it. | You can name the condition that triggers it (concurrency, scale, empty input, upstream error) |
| 🟡 **QUALITY** | Behaves correctly. Structure, naming, DRY, missing log, stale docs, a weak or false commit message, a broken rule of the repo's `CLAUDE.md`. | Code is right, but whoever maintains it pays a price |
| ⚪ **NIT** | Cosmetic. Whitespace, comment wording, ordering, style preference. | If I ignore it forever, nothing bad happens |

**The colour is picked on the hazard, never on the kind of thing.** Docs that now lie are 🟡 - the same as a false commit message - until the lie makes someone do harm: a wrong runbook step, an API contract a caller acts on, and then they are a 🟠 on their own merits, as a silent failure. A broken repo rule is 🟡; when breaking it created a hazard - a secret in a log, a missing pin - that hazard is the 🟠. A departure from tkay-code's `clean-code.md` keeps the colour the checklist below gives it.

**Who introduced it does not change the colour, and only sometimes where it goes:**

- **The branch introduced it**: a finding on that commit, whatever the colour.
- **It is pre-existing and stops what the branch delivers from working well**: a finding on the commit that should carry the fix, headed `#### 🟠 RISK [pre-existing; <what of the branch it breaks>]: <claim>`, so nobody looks for it in that commit's diff. It blocks: whether the branch works does not depend on who wrote the bug.
- **It is pre-existing and the branch does not depend on it**: 🎣 bycatch, see "The bycatch table".

**Never pick 🟡 to dodge an argument.** If you're unsure whether it is a hazard, it's 🟠 and you say you're unsure. 🟡 is a claim that shipping without it is safe - own it.

### Mandatory output shape per commit

Open each commit's review with the FINDINGS line and its Full Verdict, then dive straight into details. (This is NOT the banned "recap of the findings before the findings" - it's a count and a verdict, not a recap.)

**The FINDINGS line counts each colour**, in the order 🔴 🟠 🟡 ⚪, only the colours with a finding, and `none` when nothing was found:

```
FINDINGS: 🔴 2 · 🟠 1 · 🟡 4
FINDINGS: 🟠 2 · ⚪ 1
FINDINGS: none
```

A 🔴 or 🟠 count on the line means the commit blocks; a line with only 🟡 and ⚪ means it ships. Nothing else goes on it.

**The commit's Full Verdict** follows the FINDINGS line, in the shape and with the commit calls of tkay-code's `verdict.md`:

- **Its call is the one its commits-table row gives**, under the rules in "The commits table" below. The row is this verdict's TL;DR, so the two never disagree.
- **The Commit line is the commit as it is**: how sure you are it does what it claims at HEAD, apart from its findings, and how big and hard it is.
- **The Fix lines are the work the findings ask for.** `Fix 🔴🟠` names what unblocks the merge and what it costs; `Fix 🟡⚪` names the clean-up and what it costs, and is mine to take or leave. One whose colours have no finding is left out.
- **Every finding has a fix that changes something.** A finding whose fix would be to leave the code as it is is not a finding: drop it before the verdict, never write it with a Fix line that says to leave it. A bycatch row's `⏸ Leave for now` is different: its fix exists, and the call defers it. The case that taught it, a ⚪ on a heading that repeated the repo name the change was asked to add:

  ```
  ❌ FINDINGS: ⚪ 1 · Fix 🟡⚪: none needed; leave the repeat
  ✅ FINDINGS: none - the repeat is what the change is for
  ```
- **Why Yes and Why Not hold what the change gains and costs** - behaviour it introduces, alerts it shifts, doors it closes - never its findings, which the sections below list. When nothing is left beyond them, Why Not says "none beyond the findings above (checked: <what was checked>)".

Then exactly two sections, in this order, with the divider, each under a `###` heading inside its commit, worst colour first within each:

```
### MUST HAVE — 🔴🟠, blocks the merge
...🔴 first, then 🟠...

---

### NICE TO HAVE — 🟡⚪
...🟡 first, then ⚪...
```

**If a section is empty, SAY IT OUT LOUD** - and say what you actually checked, not that correctness is proven: "MUST HAVE: none - I traced both new branches and grepped every caller in HEAD." An empty section means you found nothing, so don't write "the code is correct" as if you'd proved it. Never make me infer emptiness from absence.

### The branch overview — the second section, every CR

After the last commit's review, say in plain words what the branch does as a
whole at HEAD - what someone who never opens the diff gets when it merges.
No file, function, flag or SHA: sentences a teammate reading release notes
would follow. Under its own heading, which names the repo by its directory
and the branch by its full name, so a CR read on its own says what it
judged:

# Repo <repo> branch <branch> Overview

```
✂️ Split first (carve out 2) · **How sure:** CONFIDENT

• 1 <one thing the branch does, in plain words>
✅ Keep it · **How sure:** LIKELY
**Commits:** `<sha>`, `<sha>`

• 2 <the next thing the branch does>
✂️ Carve out · **How sure:** CONFIDENT
**Commits:** `<sha>`
```

- **One line for the whole branch comes first**: a TL;DR Verdict with the
  branch calls of tkay-code's `verdict.md`, answering whether the branch
  merges. It follows from the entries below it and is never a judgement of
  its own: the worst entry decides it, in the order ❌, ✂️, ⚖️, 🔧, ✅, and
  its bracket names the entries that decided it.
- **One entry per distinct thing the branch does.** A branch that does one
  thing gets one entry; several changes get one each, never folded into one
  entry where a weak part hides behind a strong one.
- **Each entry is a `•` paragraph opening with its number, never a markdown
  list item**: `• 1`, the sentence, then the TL;DR Verdict, then the Commits
  line, one per line, and a blank line before the next entry. A terminal
  drops the blank line between list items, and the entries run together;
  the number is how I answer an entry.
- **Each entry carries a TL;DR Verdict on that change as it stands at HEAD**,
  in the shape and with the entry calls of tkay-code's `verdict.md`: what to
  do with this part, never whether the branch merges. The call and its How
  sure, nothing else: what the change needs is in the call's bracket, and
  what the fix costs is in the commit's row.
- **The call follows the commits it names.** `✅ Keep it` only when every
  one of them is `✅ Ship it`, `👌 Fixed later`, `🪓 Split` or
  `📝 Reword`; any other commit call makes it `🔧 Needs fixes`, naming the
  commit and what it needs, unless the change itself earns
  `⚖️ Close call`, `✂️ Carve out` or `❌ Drop it`. An entry never reads
  greener than a commit it lives in, even when that commit changes nothing
  in the tree. The case that taught it, a branch whose only extra commit
  was a back-merge of the default branch that carried no change:

  ```
  ❌ ✅ Do it · **How sure:** LIKELY
     with `<sha>` 🗑 Drop (carries no change) in the commits table
  ✅ 🔧 Needs fixes (drop the back-merge `<sha>`) · **How sure:** LIKELY
  ```

- **✂️ Carve out is the split recommendation.** Work that is sound but does
  not land with this branch moves to a branch of its own, and the rest
  merges once it is moved. The review recommends the split; whether to make
  it is mine.

- **The Commits line names every commit the change lives in**, in branch
  order. A commit that serves two entries is on both lines.
- **These verdicts judge the outcome, so a broken branch shows up here.** A
  `❌ Drop it`, or How sure below `CONFIDENT`, under a commits table of
  nothing but `✅ Ship it` means the commits above are missing a finding or a
  `🗑 Drop`: find it on the commits the entry names and put it on the one
  that should carry it.

### The commits table — the third section, every CR

After the branch overview comes one table: two rows per commit, in branch
order, four columns, under its own heading so it never reads as part of the
last commit's review.

# Commits

| # | What the commit does | Findings | Verdict |
|---|---|---|---|
| 1 | `<sha>` <one sentence> | 🔴 1 · 🟡 2 | <call> |
| | **How sure:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **Fix 🔴🟠:** <the fix> · **How sure:** <level> · **Size:** <size> · **Difficulty:** <difficulty> · **Fix 🟡⚪:** <the fix> · **How sure:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **How sure:** <level> |

- **The head row** is the commit, its findings and its call, nothing else.
  **The second row** puts the Commit line under the commit, the Fix
  lines under the findings they answer, and the call's How sure under the
  call; its `#` cell stays empty, which is what makes it read as part of the
  row above. A table cell cannot hold a line break, so the lines are rows.
  The column names what a cell holds, so the Commit, Bycatch and Verdict
  lines drop their label there; the two Fix lines keep theirs, since they
  share one cell.
- **#** — `1`, `2`, `3` down the table in branch order, so I answer a row by
  its number.
- **What the commit does** — one sentence on what the diff actually does,
  verified against it. Never the subject line pasted in: the subject may be the
  very claim the review flagged as false.
- **Findings** — the commit's FINDINGS line without the word: `🔴 1 · 🟡 2`,
  or `none`.
- **Verdict** — the call of that commit's Full Verdict on the head row, with
  the reason in a few words for anything other than ✅ Ship it, and
  `**How sure:** <level>` on the second row, in the shape of
  tkay-code's `verdict.md`. The commit call is picked by these rules:

| Call | When |
|---|---|
| `✅ Ship it` | no 🔴 or 🟠, and it does one thing |
| `👌 Fixed later (by <sha>)` | its 🔴 or 🟠 are fixed by a later commit on the branch, named in the bracket |
| `🔧 Needs change` | a 🔴 or 🟠 in the code, and amending this commit fixes it |
| `🪓 Split (<the parts>)` | no 🔴 or 🟠, but it does more than one thing a reader, a revert or a bisect would want apart - the one-thing test in tkay-code's `commits.md`. It works as it is, so it blocks nothing. A `Bycatch:` bullet that is not one simple line is the usual sign. A commit that also has a 🔴 or 🟠 is `🔧 Needs change`, and its reason names the split too |
| `📝 Reword (<the reason>)` | no 🔴 or 🟠, but its message is false or misleading - a 🟡 in the message with the code right. Only the message changes, so it blocks nothing. When the message and the code disagree, the review says which side is wrong before it picks the call: the code right and the message not is this call; the message describing what the code should have done and the code not doing it is a 🔴 or 🟠 on the code and `🔧 Needs change`; and no way to tell which was meant is a 🟠 on the commit and `🔧 Needs change (message and code disagree)`, the finding stating both readings, what would settle it, and a fix for each |
| `🔀 Squash into <sha>` | it only exists because an earlier commit on the branch got something wrong or left it half done, or the two read better as one — apart they hide what the branch does — the squash rule in tkay-code's `commits.md`. Never a fix for a bug that reached the default branch or a release, which stands alone in either direction |
| `🗑 Drop` | the branch is better without it: nothing needs it, a later commit undoes it, or it is out of scope |

The later commit's call is picked by its own row of this table: carrying the
fix makes it neither a squash nor a ship. It is `🔀 Squash into` the earlier
commit only when it exists because that one got something wrong, and
`✅ Ship it` when it stands on its own and fixes the earlier one along the way.

The verdict agrees with that commit's FINDINGS line: never `✅ Ship it`,
`🪓 Split` or `📝 Reword` while the line counts a 🔴 or a 🟠. `👌 Fixed
later` is the one call that carries one, the one its named commit fixes. A
single-commit CR still has a two-row table. The branch overview, the
commits table and the bycatch table below are the only summaries allowed
in a CR: no prose under a table.

### The bycatch table — the last section, every CR

The commits table judges the commits. The bycatch table holds what the review
turned up on the way that the branch neither introduced nor depends on, and
that is still open at HEAD: a pre-existing bug in a file the branch touched,
a stale or false doc next to the change, a trap the diff happened to expose.
Two tests decide it, and only what fails both is bycatch:

1. **The branch introduced it** - blame it, never guess: a finding on that
   commit, whatever it touches. The branch's own work is always judged.
2. **It stops what the branch delivers from working well**, whoever
   introduced it: a 🔴 or 🟠 finding on the commit that should carry the
   fix, marked pre-existing, as "Who introduced it" says above.

The same two rows per item as the commits table, under its own heading:

# 🎣 Bycatch

| # | What the bycatch is | Findings | Verdict |
|---|---|---|---|
| B1 | <what it is, with `file`> | 🟠 1 | <call> |
| | **How sure:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **Fix 🔴🟠:** <the fix> · **How sure:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **How sure:** <level> |

- **#** — `B1`, `B2`, `B3` down the table, so I answer a row by its number
  instead of describing it back to you. The letter keeps it apart from every
  other number in the reply, and `B2` in my message names that row and
  nothing else. A repeat CR in the same session keeps a carried row's number
  and gives a new row the next free one, so my earlier answers still point
  at the right rows.
- **What the bycatch is** — one sentence with the file, so I can tell a
  lying doc from a typo without re-reading the findings.
- **Findings** — its colour and a count of one, in the commits table's
  form: `🟠 1`.
- **Verdict** — what you think I should do, as a recommendation I can
  overrule: the bycatch calls of tkay-code's `verdict.md` on the head row,
  and the call's How sure on the second. 🔧 Add fix is a new commit on this
  branch; ⏸ Leave for now carries the reason in a few words - out of the
  branch's scope, another owner's file, not worth the review cost today.
- **The second row**: the Bycatch line is the problem as it sits in the
  code - how sure you are it is real as described, how much it touches,
  how hard it is to understand; the Fix lines are the fix, as in the
  commits table, and the one whose colours the finding is not in is left
  out.

**A problem the branch already fixes is not bycatch.** Its fix is part of
the commit that carries it - a commit of its own, or a `Bycatch:` line in
another commit's message, the bycatch rule in tkay-code's `commits.md` - and
is reviewed in that commit's findings. It never gets a row, and "fixed" is
never a Verdict - both calls are work still to do. A row the branch fixes
in part keeps only the part still open, worded as though the fixed part
was never there. A repeat CR drops a row the branch has fixed since; the
rows left keep their numbers.

The case that taught it, a CR whose branch had already fixed two of its
three rows:

```
❌ | B1 | Panel 12 double-counted during a pod overlap. | 🟡 1 | Fixed by `<sha>`. |
   | B3 | Standby passes stamp the last-pass timestamp. The board side is now covered by tile 30. The code half is still open. | 🟠 1 | ⏸ Leave for now (...) |
✅ | B3 | Standby passes stamp the last-pass timestamp (`internal/looprun/metrics.go`). | 🟠 1 | ⏸ Leave for now (...) |
```

When nothing is open, the heading stays and the table is one line instead:
"No bycatch." Never skip it silently - an absent section reads as
"did not look".

### Rules that keep the tags honest

- **No severity inflation.** If you cannot write the concrete failure scenario, it is NOT a 🔴 BUG - downgrade it. Dressing a nit up as a bug wastes my time and destroys my trust in every other tag in the review.
- **No severity deflation.** Never bury a 🔴 inside a nit list and never soften it ("might be worth considering..."). If it's broken, the first words are "🔴 **BUG**:".
- **Verify before tagging 🔴.** Read the code path, grep the callers, check HEAD. If you couldn't verify, tag it **🔴 BUG (UNVERIFIED)** and state exactly what you couldn't check.
- **✅ Ship it, 🪓 Split and 📝 Reword need executed evidence, not reasoning.** Every runtime claim a commit's correctness rests on - a path resolving, a command working, a permission rule firing, a script running from another directory - is proven by running or rendering it before the verdict, and the review names the command that proved it. "The docs say so" is a reason to expect it works, not proof that it does. A command that changes state is proven by its dry run or render, or handed to me to run - never run to prove it.
  **Every test you can run yourself is run before the verdict, as tkay-code's `verdict.md` says - without asking and without reporting it as a finding.** A local command, a render, a dry run, a script run from a scratch directory, a read against something already reachable: run it, and the review names the command and what it showed. **🟠 RISK (UNVERIFIED)** is reserved for a claim whose proof genuinely needs me: something only I can supply (a cluster, a machine, a credential, a setting), a command that would change state with no dry run, or a test long or costly enough that it is worth my decision. It names the claim and the command that would prove it, and blocks ✅ Ship it until it is run or I accept it as untested - and accepting it changes no colour: it stays a 🟠 I chose to merge past. An UNVERIFIED finding for a test you could have run in seconds is a review you did not finish.
  Every UNVERIFIED finding carries three lines, so I can decide whether the test is worth running or the claim is safe to accept untested:
  - **Cost** - moderate or hard, and what it needs: the command, how long it takes, and what I have to supply or what it would change.
  - **Sure without it** - a How sure level from tkay-code's `verdict.md` and the reason: which parts of the claim are already proven and what rests on reasoning alone.
  - **Sure with it** - a How sure level, and what would still be unproven after the test passes.
- **State confidence when you're unsure**, as a How sure level from tkay-code's `verdict.md` and what backs it: "🟠 RISK (CONFIDENT)" vs "🟠 RISK (50-50 - couldn't reproduce)". Never hide uncertainty behind vague wording, and never let low confidence silently turn a 🟠 into a 🟡.
- **Where the borderline cases land:**
  - Weak/vague commit message → 🟡. Commit message making a FALSE CLAIM about behavior → 🟡 too, the code works; the commit's call is 📝 Reword, and the Fix 🟡⚪ line names the new message. A message the code disagrees with is coloured by which side is wrong - the 📝 Reword row of the commits table says how - and when you cannot tell, the doubt is a 🟠 on the commit. Docs that now lie about behaviour → 🟡, unless the lie makes someone do harm, which is a 🟠 as a silent failure.
  - Missing log, or wrong log level → 🟡. Metric defined but never called, or called on only some code paths → 🟠 (blind in prod).
  - Redundant comment, YAML whitespace/blank lines, ordering, style preference → ⚪. Genuinely misleading name or a DRY violation someone will trip over → 🟡.
  - A name that holds more than its words say, is named for a cause instead of a meaning, or kept its name after its meaning changed (see "A NAME MEANS ONE THING, LITERALLY" in tkay-code's `clean-code.md`) → 🟡. A reader already acting on the literal word and doing the wrong thing → 🔴 for that reader, with the rename as the fix. A label (enum, metric label value, status word) whose words are false for some case that produces it → 🟡.
  - Clever code a plain version replaces with the same behaviour → 🟡. Clever code hiding a bug you traced → 🔴 for the bug, and the plain version is the fix.
  - Suspicious logic you traced and it's genuinely wrong → 🔴. Suspicious logic you can't prove either way → 🟠, and say what would prove it.
  - Perf: measurable regression on the per-request path → 🟠 minimum. Cold path → 🟡.
  - Tests: a test coupled to the implementation (private state, mocked internals, a whole-object snapshot), or a test of nothing the component promises → 🟡. A bug fix with no test that reproduces it → 🟠 when a unit test through the component's public interface could fail on the unfixed code: the bug can come back and nothing will notice. When none could - a race, a failure only a live cluster shows, a fix to config alone - it is 🟡, and the bracket names which of those it is. A test that cannot fail on the bug it is named for (the expected value computed with the code's own formula, the unit under test mocked out) → 🟠: it reports green while the thing it guards is broken. "TESTS CHECK THE CONTRACT, NOT THE CODE" in tkay-code's `clean-code.md` says what a good one checks.
- **Still report the nits.** NICE TO HAVE ≠ "don't mention". Put them below the divider where they can't be mistaken for real problems.
- **🟠 is not a wish list.** If everything is 🟠, the colour means nothing and I'll start ignoring it. Be willing to write 🟡 and stand behind it.

### What to Review (inspect in this order - but REPORT by severity, never in this order)

This is the checklist order for *looking*, not for *writing the review*. Commit messages are first to inspect and nearly last to report - a lowercase-subject nit never appears above an IndexError.

Each category below has a **default severity** - deviate only with a stated reason.

1. **Commit Messages & Descriptions** [default: 🟡; a false claim about behavior is 🟡 too, and makes the commit's call 📝 Reword]
   - **The full standard is in tkay-code's `commits.md` — read it before judging a commit message.** Subject line rules, body structure, accuracy checks and format all live there.
   - The accuracy checks are the ones that make a message false: does the message match what the code actually does, are there false claims, is the explanation backwards or misleading, does it mention all significant files changed?

2. **Critical Bugs** [default: 🔴 if you can show the failure, 🟠 if you can only name the trigger condition]
   - Will this break production?
   - Are there metrics defined but never called?
   - **When functions/methods/metrics are REMOVED: verify they're not called anywhere in HEAD**
   - **Check if later commits on the same branch broke what this commit did correctly**
   - Are there function calls with wrong parameters?
   - Any nil pointer risks?
   - Race conditions or concurrency issues?

3. **Security** [default: 🟠, a leak or bypass you can show: 🔴]
   - **Ask every question in "SECURITY" in tkay-code's `clean-code.md`** of the diff and of the component it lands in.
   - An exposure the branch did not introduce goes into the bycatch table, unless it stops what the branch delivers from working well - then it is a pre-existing finding on the commit that should carry the fix. Never dropped because it is pre-existing.

4. **Metrics & Observability** [default: 🟠 for missing/partial metric calls and wrong metric type, 🟡 for naming]
   - Is every bad path counted, and the unit of work too? "EVERY BAD PATH IS COUNTED, THEN LOGGED" in tkay-code's `clean-code.md` says what counts as one
   - Are metrics called BEFORE logs? (metric-first pattern)
   - Are metric names/labels correct?
   - Right metric type? (Counter vs Gauge vs Histogram)
   - Any missing metric calls?

5. **Logging** [default: 🟡, missing context on an error path that would block debugging prod: 🟠]
   - Is every metric accompanied by a log?
   - Log levels correct? (INFO vs WARNING vs ERROR)
   - Consistent formatting across similar log messages?
   - Include all necessary context (pod_name, pod_ip, model_name)?

6. **Code Quality** [default: 🟡, EXCEPT "logical correctness of NEW code" below - wrong logic is 🔴/🟠]
   - Duplicated logic or values? "ONE SOURCE OF TRUTH" in tkay-code's `clean-code.md` says what counts
   - Ordering issues? (should things be grouped differently?)
   - Naming clarity? Does each name mean one thing, literally, that a cold reader gets from the name alone? A name that only a comment explains is the wrong name: make it longer or split it. Any state that hides a compound condition, is named for its cause, or kept its name when a change shifted its meaning? When a diff changes what a field means, grep every reader of it.
   - Any TODOs or FIXMEs that shouldn't be there?
   - **Redundant comments**: the comment rules and their worked examples are in tkay-code's `clean-code.md`. Flag ANY comment that states the obvious or repeats what code/logs say. When in doubt, the comment should be DELETED.
   - **Inconsistent spacing/indentation in YAML/config files**:
     - Check for extra blank lines between similar sections (e.g., model entries in config)
     - Flag trailing whitespace (spaces after content on a line)
     - Verify consistent indentation (2 spaces for YAML, not tabs or 4 spaces)
     - Example violations: random blank line between two model entries, trailing space after `checkImage: true `
   - **Unused parameters**: Flag function parameters that are defined but never used in the body (YAGNI violation)
   - **Logical correctness of NEW code**: Don't just check for bugs, analyze if the logic makes sense:
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
  into a ref without checking it out - `git fetch origin
  refs/merge-requests/<iid>/head` on GitLab, `refs/pull/<n>/head` on GitHub -
  and review `FETCH_HEAD` with `git log`, `git show` and `git diff` against
  its target branch. The current branch and the working tree stay as they
  are. If no checkout of that repo is open, ask where it is.
- **Nothing goes back to the link.** No note, no draft note, no inline
  comment, no suggestion, no approval, no resolved thread, no label, and no
  review tool's commenting mode. Each of those runs only when my message
  asks for that one in plain words.

### A repeat CR in the same session

**A commit this session already reviewed keeps that review while its code is
unchanged - even when I ask for the CR "from scratch".** Its code is
unchanged when its tree and its parent's tree are the ones the earlier review
saw: together they pin its diff and everything below it, so a fresh read has
nothing new to find. Carry its section over as it was written, with one line
naming the review it comes from, and spend the effort on what changed.
Compare `git rev-parse <sha>^{tree} <sha>~1^{tree}` for each commit with the
same for the commit in its place in the earlier commits table.

- **The same SHA is carried as it is.**
- **A new SHA over the same trees changed only commit messages** - a reword
  of it or of a commit below it, a rebase that moved nothing else. Its code
  review is carried; a message that changed is reviewed again, and its
  findings and verdict follow the new message.
- **A new tree is a new commit**: an amend that changed content, a fixup
  folded into it or below it, a rebase onto a moved base. It gets a full
  review, tests included, even when its own diff reads the same as before.
- **Only a review still in the context is carried.** One that was
  summarised away, or that came from another session, has lost the findings
  it would carry; review that commit again.
- **The outcome is judged afresh every time.** Each new or rewritten commit
  is read against the carried ones, and a carried commit that a later change
  breaks gets the finding. The branch overview, the commits table and the
  bycatch table are rebuilt for the branch as it now stands.

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

### Review Process

**DO:**
- **Read the whole branch diff before the first commit, and judge the outcome at HEAD after the last** (see "THE BRANCH IS WHAT SHIPS, NOT THE COMMITS")
- Review commits ONE BY ONE (commit-by-commit)
- **When reviewing a commit, check HEAD state to verify later commits didn't break it**
- **When methods/functions/metrics are removed, verify they're not called in HEAD**
- **Read and understand NEW code logic** - don't just hunt for bugs, analyze whether the logic makes sense (see "Logical correctness of NEW code" in the checklist above)
- **Lay the CR out in the four sections of "THE CR IS FOUR SECTIONS"**, the findings first and the bycatch table last, and one CR per repo
- **Open with the FINDINGS line and the Full Verdict, colour every finding (🔴/🟠/🟡/⚪), and split MUST HAVE from NICE TO HAVE with the divider** (see the colour section above - this is non-negotiable)
- **For every 🔴, write the concrete failure scenario**: what input/state, what goes wrong, at which `file:line`
- **Say it out loud when a section is empty** - I need to hear it, not deduce it (exact wording in "Mandatory output shape per commit" above)
- **Write every SHA as its first 10 characters** (`git rev-parse --short=10`), everywhere in the CR, so one commit reads the same in every place it is named
- Order findings within each section by colour (🔴 → 🟠, then 🟡 → ⚪)
- Fix issues IMMEDIATELY when I ask (don't ask for permission) - but until I ask, report and wait, even for a 🔴 (see "When to Fix vs When to Ask" below)
- Be specific: show me the exact line numbers and code
- If something is wrong, say it's wrong - don't sugarcoat

**DON'T:**
- Give me a recap of the findings before the findings - the FINDINGS line and the Full Verdict are the ONLY things allowed above the details, then dive straight in
- **Mix nits in with real bugs** - if I have to guess which findings matter, the review failed
- **Colour everything 🟠 to look thorough** - that's the same trust-burning move as severity inflation
- **Call something a 🔴 BUG when you can't show it failing** - if you can still name the trigger condition it's 🟠 RISK, which blocks the merge. Only when there's no demonstrable failure AND no nameable trigger does it drop to 🟡. Never let "I couldn't prove it" collapse a hazard into a nit
- **Present a clean commit as if it were dangerous** - lots of ⚪ nits is not a problem, say so
- Be vague ("there might be an issue...") - tell me what IS wrong, or tag it speculative and say why
- Skip over minor issues because "they're not critical" - report them, just below the divider
- Assume I know what you're talking about - show me the code
- Be nice if something is actually wrong - I want to know

### Example Review Flow

```
# Findings

## Commit 1 of 4: perf(validator): Reduce validation time by 50%

FINDINGS: 🔴 1 · 🟠 1 · 🟡 3 · ⚪ 1

- **Verdict:** 🔧 Needs change (crashes on an empty pod list) · **How sure:** CONFIDENT
- **Commit:** **How sure:** CONFIDENT · **Size:** small · **Difficulty:** easy
- **Fix 🔴🟠:** guard the empty list, call `record_failure()` on timeout · **How sure:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Fix 🟡⚪:** reword the subject and body · **How sure:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  - every lookup drops from O(n) to O(1)
- **Why Not?**
  - none beyond the findings above (checked: hashY keeps the key format)

### MUST HAVE — 🔴🟠, blocks the merge

#### 🔴 BUG: blacklist lookup crashes on an empty pod list
`validator/hash.py:88` - `pods[0].name` runs before the empty check.
FAILS WHEN: gateway returns zero pods (happens on every cluster cold start)
→ IndexError, validator loop dies, no pod gets validated until restart.
VERIFIED: traced from `validate_all()` at line 40; nothing guards the call.
[show code]
Fix: [show fix]

#### 🟠 RISK: failure metric never fires on the timeout path
`validator/hash.py:123` - logs "pod failed" but never calls `record_failure()`.
TRIGGERS WHEN: pod times out (the most common real failure).
→ Grafana shows zero failures during an actual outage. Blind in prod.
[show code]
Fix: [show fix]

---

### NICE TO HAVE — 🟡⚪

#### 🟡 QUALITY: subject makes a claim the diff can't back
"Reduce validation time by 50%" is an OUTCOME, and nothing in the body shows
where 50% comes from. Fails "If applied, this commit will... reduce validation
time" (awkward). Should be: "use hashY instead of hashX for lookups" - and the
50% goes in the BODY with the 100ms → 50ms numbers behind it.

#### 🟡 QUALITY: body missing the WHY
Doesn't say: hashX did O(n) iteration → CPU spikes; hashY is O(1).

#### 🟡 QUALITY: past tense in body
"Changed from hashX to hashY" → "Replaces hashX with hashY".

#### ⚪ NIT: subject capitalized
"Reduce" → "reduce".

#### ✅ Correct:
1. Type is right: perf
2. Has scope: (validator)
3. The hashY swap itself is correct - the algorithm change is sound
```

And when it's clean, the FINDINGS line says so plainly - don't make a pile of nits look like danger:

```
## Commit 2 of 4: fix(gateway): add null check to token extractor

FINDINGS: ⚪ 2

- **Verdict:** ✅ Ship it · **How sure:** CONFIDENT
- **Commit:** **How sure:** CONFIDENT · **Size:** small · **Difficulty:** super easy
- **Fix 🟡⚪:** delete the comment, strip the whitespace · **How sure:** VERIFIED · **Size:** small · **Difficulty:** super easy
- **Why Yes?**
  - a request with no auth header gets a 401 instead of a 500
- **Why Not?**
  - none (checked: grepped every caller, none relied on the exception)

### MUST HAVE — 🔴🟠, blocks the merge
None - no 🔴 and no 🟠. I traced both new branches in `extract_token()` and the
null path is handled; metric fires on every path; no callers of the removed
helper remain in HEAD (grepped).

---

### NICE TO HAVE — 🟡⚪
#### ⚪ NIT: redundant comment
`gateway/auth.py:31` - `# check if header exists` above `if not header:` - delete it.
#### ⚪ NIT: trailing whitespace
`config/models.yaml:14`
```

Then wait for me to say "fix it" or "its ok" or "next commit" before continuing.

### When to Fix vs When to Ask

**The default for every review is: report it, write out the fix, and WAIT** - same as "Then wait for me to say 'fix it' or 'its ok' or 'next commit'" at the end of the example flow. Finding a 🔴 is not permission to edit my files. I review commit-by-commit, so unbidden edits land while I'm still reading the finding.

**Fix on sight, no permission needed - only when I've already told you to:**
- When I say "fix description" or "fix commit message"
- When I explicitly say "fix it"
- When I say "fix the must haves" - fix every 🔴 and 🟠, and nothing else
- When I set a target for the fixes - within the limits of "Fixing toward a target" below

**Show me the exact fix, then wait for my word:**
- **🔴 BUG and 🟠 RISK** - show me the diff you'd apply, don't apply it. Whether a merge-blocker gets fixed now, ticketed, or shipped knowingly is my call
- Design choices (Gauge vs Histogram) where both are valid
- Large refactors that change behavior
- Anything that might be intentional

**Never touch unless I say so:**
- Every 🟡 and ⚪ - NICE TO HAVE means it's my call by definition

### Fixing toward a target

When I set a target for the fixes - "fix until no 🔴 or 🟠 is left and the verdict is ✅ Ship it", in whatever words - the target is a correct branch, and the FINDINGS line only measures it. A fix that brings a bug of its own is worse than the finding it closed: the finding was named and visible, the new bug is neither.

- **Every fix is the smallest, plainest change that closes its finding** - delete, reorder, rename, add the missing guard or the missing call: a change a reader verifies at a glance. A fix that needs a new mechanism, a new code path or a restructure, or that touches code the finding never named, is not easy: show it and wait, whatever the target says.
- **Every fix answers two questions as it is made: does it do what it claims, and did it break anything around it?** Read its diff against this standard, trace what it touches - its callers, the paths beside it, the rest of the branch - and run what can be run. Striking the finding it closed answers neither.
- **A fix that fails either question gets an easy fix of its own, or it stops.** When no easy fix makes both answers yes, stop and ask me: name the finding, what the fix failed to do or broke, and the options as you see them. Never stack a hard fix on top of it to reach the target.
- **One round of fixes, then one more review of the whole branch at HEAD** - not only the findings it fixed: a fix lands in code the rest of the branch depends on. When that review still finds anything the target needs fixed, stop and ask me before a second round, even in the middle of a goal: the goal is why the fixes run, never permission to keep going past this point.
- **A finding closes only because the code got better.** Never reach the target by recolouring a finding, softening it, or deleting the test, check or log that exposed the problem.
- **Fix only what the target needs.** A NICE TO HAVE outside it stays my call, and every extra fix is another chance at a new bug.

### Tools to Use

- `git show <hash>` to review commits
- `git show <hash>~1:<file>` to see previous version
- Read the actual files to verify claims
- Check if metrics are actually called (grep for the function name)
- Verify log levels haven't changed when commit claims they did
- **When methods/metrics are removed: `git show HEAD:<file> | grep "method_name"` to verify no calls remain in HEAD**
- **When reviewing a commit, check if later commits broke it: `git diff <commit> HEAD -- <file>`**
- **For removed functions: grep the entire codebase in HEAD state to find any remaining calls**

### Bottom Line

I care about my commits and want them to be perfect, because they are how the branch is read - and the branch is what ships. Be thorough, be direct, and don't hold back. If something is wrong, tell me. If something is misleading, tell me. If I'm about to merge garbage, BLOCK ME.

**And be unmistakably clear about two things: is it BROKEN, and do I have to fix it NOW.** Three failures I hate equally:
1. Burying a 🔴 BUG in a list of whitespace nits so I merge broken code.
2. Handing me a scary-looking wall of ⚪ nits with no verdict, so I waste an hour hunting a bug that was never there.
3. Giving me 12 findings with no MUST HAVE / NICE TO HAVE split, so I have to re-triage your review myself before I can do anything with it.

Thorough, clearly triaged, and explicit about what blocks the merge. All three, every time.

That's what good code review is.
