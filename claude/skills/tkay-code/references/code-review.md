# Code Review Standards

**Read `references/clean-code.md` before the first finding.** It defines clean
code; this file says how to report a departure from it and how bad each one is.

## How I Want Code Reviews Done

When I ask for a code review (CR), I want you to be **thorough as fuck** because this is serious production code. Don't hold back, don't be nice - if something is wrong, tell me straight up.

## THE BRANCH IS WHAT SHIPS, NOT THE COMMITS

**The target of a review is the final outcome: the tree at the top of the
branch, merged into its base.** Commits are how that outcome is reached and
read; they are never a target of their own. The worst review I can get is
every commit marked `✅ SHIP IT` while the branch as a whole is broken - each
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
  at HEAD is broken, at least one row of the closing table is not `✅ SHIP IT`.
- **Squash when it makes the outcome clearer.** When reading the commits apart
  hides what the branch does - steps that only make sense together, a commit
  that is broken until a later one lands, a split that leaves the reader to
  assemble the change in their head - recommend `🔀 SQUASH INTO` even when no
  commit got anything wrong. A commit earns its place by making the outcome
  easier to understand or to bisect, not by existing.

## CRITICAL: IS IT A REAL BUG OR A NIT — AND MUST I FIX IT NOW?

**Two questions I must be able to answer about every single finding, without reading between the lines:**
1. **Is this code BROKEN or merely IMPERFECT?** → the severity tag
2. **Does it BLOCK THE MERGE or can I ship without it?** → the MUST HAVE / NICE TO HAVE label

A wall of findings where I can't answer both is a USELESS review, no matter how thorough it is.

Every finding MUST carry both tags. Findings MUST be split into two hard-separated buckets. No exceptions, no mixing.

### The severity tags (use the exact emoji + word)

| Tag | Meaning | Bar to qualify |
|-----|---------|----------------|
| 🔴 **BUG** | Code is wrong. It will misbehave, crash, corrupt data, hang, or produce the wrong result. | You can state a concrete failure: *"input/state X → wrong output or crash at `file:line`"* |
| 🟠 **RISK** | Not provably broken today, but a real hazard: race window, unbounded growth, missing error path, perf regression on the hot path, silent failure, broken observability. | You can name the condition that triggers it (concurrency, scale, empty input, upstream error) |
| 🟡 **QUALITY** | Behaves correctly. Structure, naming, DRY, missing log, stale docs, weak commit message. | Code is right, but whoever maintains it pays a price |
| ⚪ **NIT** | Cosmetic. Whitespace, comment wording, ordering, style preference. | If I ignore it forever, nothing bad happens |

**🔴 and 🟠 are REAL ISSUES. 🟡 and ⚪ are NOT.** That distinction is the whole point of this section.

### The SECOND axis: MUST HAVE vs NICE TO HAVE

Severity says **how broken** it is. Policy says **whether I have to act before merging**. Every finding carries BOTH, on the same line:

```
### 🔴 BUG · MUST HAVE: <one-line claim>
### 🟡 QUALITY · NICE TO HAVE: <one-line claim>
```

| Policy | Meaning |
|--------|---------|
| **MUST HAVE** | Blocks the merge. I fix this now, or I don't ship. |
| **NICE TO HAVE** | Ship without it. Worth doing when I'm in there anyway; a real judgment call, not a demand. |

**Default mapping** — 🔴 → MUST HAVE · 🟠 → MUST HAVE · 🟡 → NICE TO HAVE · ⚪ → NICE TO HAVE

**🔴 BUG is ALWAYS MUST HAVE. That one has no override.** For every other tag you may deviate from the default, but ONLY with the reason on the same line in brackets. No bare deviation:

- `🟠 RISK · NICE TO HAVE [pre-existing on main, this commit didn't introduce it - ticket it]`
- `🟠 RISK · NICE TO HAVE [only triggers above ~10k RPS, we're at 800 - track it]`
- `🟡 QUALITY · MUST HAVE [commit message falsely claims X changed to Y; history is permanent]`
- `🟡 QUALITY · MUST HAVE [violates an explicit rule in the repo's CLAUDE.md - name the rule]`

**Legitimate reasons to promote 🟡/⚪ → MUST HAVE:** false or misleading commit message (git history is permanent), a violation of a rule stated explicitly in the repo's `CLAUDE.md`, docs that now actively lie about behavior, a bug fix with no test that reproduces it when a unit test could (see "Tests" under "Where the borderline cases land"), or a label value (enum, metric label, status word) that is false for some case producing it and has not shipped yet - after it ships, renaming it breaks every dashboard and alert that reads it. A departure from `references/clean-code.md` keeps the severity and policy the checklist below gives it; being written down there is not on its own a reason to promote.
**Legitimate reasons to demote 🟠 → NICE TO HAVE:** pre-existing condition this commit didn't introduce, a trigger threshold we are provably nowhere near, or a 🟠 RISK (UNVERIFIED) I accepted as untested. Say which.

**Never demote to dodge an argument.** If you're unsure whether it blocks, it's MUST HAVE and you say you're unsure. NICE TO HAVE is a claim that shipping without it is safe - own it.

### Mandatory output shape per commit

Open each commit's review with the VERDICT line plus the MUST-HAVE roll-up, then dive straight into details. (This is NOT the banned "recap of the findings before the findings" - it's a verdict and an action list, not a recap.)

```
VERDICT: 🔴 2 BUGS + 🟠 1 RISK — 3 MUST HAVE, 4 NICE TO HAVE — DO NOT MERGE
MUST HAVE: (1) empty-pod IndexError at hash.py:88  (2) failure metric never fires on timeout  (3) commit body claims a 50ms win the diff can't deliver
```

```
VERDICT: 🟠 2 RISKS, no outright bugs — 2 MUST HAVE, 1 NICE TO HAVE — DO NOT MERGE
MUST HAVE: (1) blacklist write races the read on concurrent validation  (2) cache grows unbounded, no eviction
```

```
VERDICT: ✅ NO REAL ISSUES — 0 MUST HAVE, 5 NICE TO HAVE — SHIP IT
MUST HAVE: none.
```

**Verdict vocabulary is fixed, don't improvise it:**
- `✅ NO REAL ISSUES` — **only** when 🔴 and 🟠 are BOTH zero. "No real bugs" is a banned phrasing on its own: it's technically true with three 🟠 open and it reads as all-clear.
- `🟠 N RISKS, no outright bugs` — the 0-🔴-but-hazards case. Say it in exactly these terms so I can't misread it as clean.
- **Never `✅` and never `SHIP IT` while the MUST HAVE count is above zero** - including when every MUST HAVE is a promoted 🟡.

The MUST-HAVE roll-up lists EVERY MUST HAVE item, including any 🟡/⚪ you promoted - that's the whole reason the roll-up exists, so a promoted item below the divider can't hide from me.

Then exactly two sections, in this order, with the divider. **The buckets split on BROKEN vs NOT BROKEN - severity, not importance.** Importance is what the MUST HAVE tag decides, and a promoted MUST HAVE lives in the second bucket while still blocking the merge. Within each bucket, MUST HAVE items come first:

```
## 🔴🟠 REAL ISSUES — the code is wrong or hazardous
...MUST HAVE first, worst first...

---

## 🟡⚪ NOT BROKEN — code is correct (some may still block)
...any promoted MUST HAVE first, then NICE TO HAVE...
```

**If a bucket is empty, SAY IT OUT LOUD** - and say what you actually checked, not that correctness is proven: "REAL ISSUES: none - I traced both new branches and grepped every caller in HEAD." An empty bucket means you found nothing, so don't write "the code is correct" as if you'd proved it. Never make me infer emptiness from absence. Same for the roll-up: "MUST HAVE: none."

### The branch summary — right above the closing table, every CR

After the last commit's review, say in plain words what the branch does as a
whole at HEAD - what someone who never opens the diff gets when it merges.
No file, function, flag or SHA: sentences a teammate reading release notes
would follow. Under its own heading:

## What the branch does

```
- <one thing the branch does, in plain words>
  VERDICT: ✅ DO IT — LIKELY
  Doubt: <what keeps it from VERIFIED>
```

- **One bullet per distinct thing the branch does.** A branch that does one
  thing gets one bullet; several changes get one each, never folded into one
  bullet where a weak part hides behind a strong one.
- **Each bullet carries your verdict on that change as it stands at HEAD**, one
  of three, never improvised: `✅ DO IT` - the change is right and does what it
  claims; `⚖️ JUDGEMENT CALL` - defensible both ways, and the line says which
  way you lean and why; `❌ DON'T` - the branch is better without it, and the
  line says what you would do instead.
- **The confidence level is how sure you are that the change is right and
  works at HEAD**, not how sure you are that I will agree. One of four, each
  defined by what backs it: `VERIFIED` - you ran it or tested the exact
  behaviour; `CONFIDENT` - not run, but you traced every step in the code or
  the docs; `LIKELY` - one unchecked inference carries it; `50-50` - more
  than one unchecked inference, or you do not know. Anything short of
  `VERIFIED` is followed by a `Doubt:` line naming what keeps it from
  `VERIFIED`.
- **These verdicts judge the outcome, so a broken branch shows up here.** A
  `❌ DON'T`, or a doubt that the change works at HEAD, under a closing table
  of nothing but `✅ SHIP IT` means the commits above are missing a finding or
  a `🗑 DROP`: find it and put it on the commit that should carry it.

### The closing table — the last thing in every CR

After the branch summary, end the CR with one table: one row per commit,
in branch order, three columns, under its own heading so it never reads as part
of the last commit's review.

## Commits

| What the commit does | Score | Verdict |
|---|---|---|
| `<short-sha>` <one sentence> | <n>/10 | <verdict> |

- **What the commit does** — one sentence on what the diff actually does,
  verified against it. Never the subject line pasted in: the subject may be the
  very claim the review flagged as false.
- **Score** — the same number as that commit's `Score:` line.
- **Verdict** — exactly one of these, followed by the reason in a few words for
  anything other than SHIP IT:

| Verdict | When |
|---|---|
| `✅ SHIP IT` | 0 MUST HAVE |
| `🔧 NEEDS CHANGE` | at least one MUST HAVE, and amending this commit fixes it |
| `🔀 SQUASH INTO <short-sha>` | it only exists because an earlier commit on the branch got something wrong or left it half done, or the two read better as one — apart they hide what the branch does — the squash rule in `references/commits.md`. Never a fix for a bug that reached the default branch or a release, which stands alone in either direction |
| `🗑 DROP` | the branch is better without it: nothing needs it, a later commit undoes it, or it is out of scope |

The verdict agrees with that commit's VERDICT line: never `✅ SHIP IT` while its
MUST HAVE count is above zero. A single-commit CR still ends with a one-row
table. The branch summary, the closing table and the leftovers table below are
the only summaries allowed in a CR.

### The leftovers table — right after the closing table, every CR

The closing table judges the commits. The leftovers table holds what the review
turned up on the way that is NOT a finding against a commit: a pre-existing bug
in a file the branch touched, a stale or false doc next to the change, a trap
the diff happened to expose. Three columns, under its own heading:

## Issues found on the way

| Issue and how bad | Introduced by this branch? | Verdict |
|---|---|---|
| <what it is, with `file`, and its severity tag> | `yes <short-sha>` / `no, pre-existing` | 🔧 ADD FIX / ⏸ LEAVE FOR NOW (why) |

- **Issue and how bad** — one sentence plus the severity tag, so I can tell a
  lying doc from a typo without re-reading the findings.
- **Introduced by this branch?** — `yes <short-sha>` or `no, pre-existing`.
  Blame it; never guess. A `yes` means the finding also belongs in that
  commit's review above, and this row points at it.
- **Verdict** — what you think I should do, as a recommendation I can
  overrule: 🔧 ADD FIX (a new commit on this branch, or amend the commit that
  introduced it) or ⏸ LEAVE FOR NOW with the reason in a few words - out of the
  branch's scope, another owner's file, not worth the review cost today.

When nothing came up, the heading stays and the table is one line instead:
"None found on the way." Never skip it silently - an absent section reads as
"did not look".

### Rules that keep the tags honest

- **No severity inflation.** If you cannot write the concrete failure scenario, it is NOT a 🔴 BUG - downgrade it. Dressing a nit up as a bug wastes my time and destroys my trust in every other tag in the review.
- **No severity deflation.** Never bury a 🔴 inside a nit list and never soften it ("might be worth considering..."). If it's broken, the first words are "🔴 **BUG** · MUST HAVE:".
- **Verify before tagging 🔴.** Read the code path, grep the callers, check HEAD. If you couldn't verify, tag it **🔴 BUG (UNVERIFIED) · MUST HAVE** and state exactly what you couldn't check.
- **SHIP IT needs executed evidence, not reasoning.** Every runtime claim a commit's correctness rests on - a path resolving, a command working, a permission rule firing, a script running from another directory - is proven by running or rendering it before the verdict, and the review names the command that proved it. "The docs say so" is a reason to expect it works, not proof that it does. A command that changes state is proven by its dry run or render, or handed to me to run - never run to prove it.
  **Every test you can run yourself, you run - without asking and without reporting it as a finding.** A local command, a render, a dry run, a script run from a scratch directory, a read against something already reachable: run it, and the review names the command and what it showed. **🟠 RISK (UNVERIFIED) · MUST HAVE** is reserved for a claim whose proof genuinely needs me: something only I can supply (a cluster, a machine, a credential, a setting), a command that would change state with no dry run, or a test long or costly enough that it is worth my decision. It names the claim and the command that would prove it, and blocks SHIP IT until it is run or I accept it as untested. An UNVERIFIED finding for a test you could have run in seconds is a review you did not finish.
  Every UNVERIFIED finding carries three lines, so I can decide whether the test is worth running or the claim is safe to accept untested:
  - **Cost** - moderate or hard, and what it needs: the command, how long it takes, and what I have to supply or what it would change.
  - **Sure without it** - a confidence level (one of the four under "The branch summary") and the reason: which parts of the claim are already proven and what rests on reasoning alone.
  - **Sure with it** - a confidence level, and what would still be unproven after the test passes.
- **State confidence when you're unsure**, as one of the four levels under "The branch summary" and what backs it: "🟠 RISK · MUST HAVE (CONFIDENT)" vs "🟠 RISK · MUST HAVE (50-50 - couldn't reproduce)". Never hide uncertainty behind vague wording, and never let low confidence silently become NICE TO HAVE.
- **Where the borderline cases land:**
  - Weak/vague commit message → 🟡 · NICE TO HAVE. Commit message making a FALSE CLAIM about behavior → still 🟡 on severity (the code works) but **MUST HAVE** on policy - it lies to whoever bisects this later, and history is permanent. This is the textbook case for why the two axes exist.
  - Missing log, or wrong log level → 🟡. Metric defined but never called, or called on only some code paths → 🟠 (blind in prod).
  - Redundant comment, YAML whitespace/blank lines, ordering, style preference → ⚪. Genuinely misleading name or a DRY violation someone will trip over → 🟡.
  - A name that holds more than its words say, is named for a cause instead of a meaning, or kept its name after its meaning changed (see "A NAME MEANS ONE THING, LITERALLY" in `references/clean-code.md`) → 🟡. A reader already acting on the literal word and doing the wrong thing → 🔴 for that reader, with the rename as the fix. A label (enum, metric label value, status word) whose words are false for some case that produces it → 🟡.
  - Clever code a plain version replaces with the same behaviour → 🟡. Clever code hiding a bug you traced → 🔴 for the bug, and the plain version is the fix.
  - Suspicious logic you traced and it's genuinely wrong → 🔴. Suspicious logic you can't prove either way → 🟠, and say what would prove it.
  - Perf: measurable regression on the per-request path → 🟠 minimum. Cold path → 🟡.
  - Tests: a test coupled to the implementation (private state, mocked internals, a whole-object snapshot), or a test of nothing the component promises → 🟡. A bug fix with no test that reproduces it → 🟡 · MUST HAVE when a unit test through the component's public interface could fail on the unfixed code. When none could - a race, a failure only a live cluster shows, a fix to config alone - it stays NICE TO HAVE, and the bracket names which of those it is. A test that cannot fail on the bug it is named for (the expected value computed with the code's own formula, the unit under test mocked out) → 🟠: it reports green while the thing it guards is broken. "TESTS CHECK THE CONTRACT, NOT THE CODE" in `references/clean-code.md` says what a good one checks.
- **Still report the nits.** "NOT BROKEN" ≠ "don't mention". Put them below the divider where they can't be mistaken for real problems.
- **Every finding gets both tags.** A finding with no policy label is an incomplete finding - I can't act on "here's a thing" without knowing if it blocks me.
- **MUST HAVE is not a wish list.** If everything is MUST HAVE, the label means nothing and I'll start ignoring it. Be willing to write NICE TO HAVE and stand behind it.
- **Score reflects severity, not count.** 20 nits and zero bugs is still 8/10. The caps, applied worst-first no matter how clean the rest is: any 🔴 → max 4/10 · any 🟠 → max 6/10 · MUST HAVE items but no 🔴/🟠 (i.e. promoted 🟡s) → max 7/10 · nothing but NICE TO HAVE → 8-10/10.

### What to Review (inspect in this order - but REPORT by severity, never in this order)

This is the checklist order for *looking*, not for *writing the review*. Commit messages are first to inspect and nearly last to report - a lowercase-subject nit never appears above an IndexError.

Each category below has a **default severity** - deviate only with a stated reason. Policy follows the default mapping above unless the bracket says otherwise.

1. **Commit Messages & Descriptions** [default: 🟡 · NICE TO HAVE, false claims about behavior: 🟡 · MUST HAVE]
   - **The full standard is in `references/commits.md` — read it before judging a commit message.** Subject line rules, body structure, accuracy checks and format all live there.
   - The accuracy checks are the ones that promote to MUST HAVE: does the message match what the code actually does, are there false claims, is the explanation backwards or misleading, does it mention all significant files changed?

2. **Critical Bugs** [default: 🔴 · MUST HAVE if you can show the failure, 🟠 · MUST HAVE if you can only name the trigger condition]
   - Will this break production?
   - Are there metrics defined but never called?
   - **When functions/methods/metrics are REMOVED: verify they're not called anywhere in HEAD**
   - **Check if later commits on the same branch broke what this commit did correctly**
   - Are there function calls with wrong parameters?
   - Any nil pointer risks?
   - Race conditions or concurrency issues?

3. **Security** [default: 🟠 · MUST HAVE, a leak or bypass you can show: 🔴 · MUST HAVE]
   - **Ask every question in "SECURITY" in `references/clean-code.md`** of the diff and of the component it lands in.
   - An exposure the branch did not introduce goes into the leftovers table - never dropped because it is pre-existing.

4. **Metrics & Observability** [default: 🟠 · MUST HAVE for missing/partial metric calls and wrong metric type, 🟡 · NICE TO HAVE for naming]
   - Is every bad path counted, and the unit of work too? "EVERY BAD PATH IS COUNTED, THEN LOGGED" in `references/clean-code.md` says what counts as one
   - Are metrics called BEFORE logs? (metric-first pattern)
   - Are metric names/labels correct?
   - Right metric type? (Counter vs Gauge vs Histogram)
   - Any missing metric calls?

5. **Logging** [default: 🟡 · NICE TO HAVE, missing context on an error path that would block debugging prod: 🟠 · MUST HAVE]
   - Is every metric accompanied by a log?
   - Log levels correct? (INFO vs WARNING vs ERROR)
   - Consistent formatting across similar log messages?
   - Include all necessary context (pod_name, pod_ip, model_name)?

6. **Code Quality** [default: 🟡 · NICE TO HAVE, EXCEPT "logical correctness of NEW code" below - wrong logic is 🔴/🟠 · MUST HAVE]
   - Duplicated logic or values? "ONE SOURCE OF TRUTH" in `references/clean-code.md` says what counts
   - Ordering issues? (should things be grouped differently?)
   - Naming clarity? Does each name mean one thing, literally, that a cold reader gets from the name alone? A name that only a comment explains is the wrong name: make it longer or split it. Any state that hides a compound condition, is named for its cause, or kept its name when a change shifted its meaning? When a diff changes what a field means, grep every reader of it.
   - Any TODOs or FIXMEs that shouldn't be there?
   - **Redundant comments**: the comment rules and their worked examples are in `references/clean-code.md`. Flag ANY comment that states the obvious or repeats what code/logs say. When in doubt, the comment should be DELETED.
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

7. **Nits** [default: ⚪ · NICE TO HAVE - always below the divider]
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

### Review Process

**DO:**
- **Read the whole branch diff before the first commit, and judge the outcome at HEAD after the last** (see "THE BRANCH IS WHAT SHIPS, NOT THE COMMITS")
- Review commits ONE BY ONE (commit-by-commit)
- **When reviewing a commit, check HEAD state to verify later commits didn't break it**
- **When methods/functions/metrics are removed, verify they're not called in HEAD**
- **Read and understand NEW code logic** - don't just hunt for bugs, analyze whether the logic makes sense (see "Logical correctness of NEW code" in the checklist above)
- Give each commit a score out of 10
- **End the CR with the branch summary, the closing table, then the leftovers table** (see "The branch summary", "The closing table" and "The leftovers table" above)
- **Open with the VERDICT line + MUST-HAVE roll-up, tag every finding with BOTH axes (🔴/🟠/🟡/⚪ · MUST HAVE/NICE TO HAVE), and split REAL ISSUES from NOT BROKEN with the divider** (see the two-axis section above - this is non-negotiable)
- **For every 🔴, write the concrete failure scenario**: what input/state, what goes wrong, at which `file:line`
- **Say it out loud when a bucket is empty** - I need to hear it, not deduce it (exact wording in "Verdict vocabulary is fixed" above)
- Order findings within each bucket: MUST HAVE first, then by severity (🔴 → 🟠 → 🟡 → ⚪)
- Fix issues IMMEDIATELY when I ask (don't ask for permission) - but until I ask, report and wait, even for a 🔴 (see "When to Fix vs When to Ask" below)
- Be specific: show me the exact line numbers and code
- If something is wrong, say it's wrong - don't sugarcoat

**DON'T:**
- Give me a recap of the findings before the findings - the VERDICT line and the MUST-HAVE roll-up are the ONLY things allowed above the details, then dive straight in
- **Mix nits in with real bugs** - if I have to guess which findings matter, the review failed
- **Leave a finding without a MUST HAVE / NICE TO HAVE label** - or deviate from the default mapping without the reason in brackets
- **Label everything MUST HAVE to look thorough** - that's the same trust-burning move as severity inflation
- **Call something a 🔴 BUG when you can't show it failing** - if you can still name the trigger condition it's 🟠 RISK, which is a REAL ISSUE and MUST HAVE. Only when there's no demonstrable failure AND no nameable trigger does it drop to 🟡. Never let "I couldn't prove it" collapse a hazard into a nit
- **Present a clean commit as if it were dangerous** - lots of ⚪ nits is not a problem, say so
- Be vague ("there might be an issue...") - tell me what IS wrong, or tag it speculative and say why
- Skip over minor issues because "they're not critical" - report them, just below the divider
- Assume I know what you're talking about - show me the code
- Be nice if something is actually wrong - I want to know

### Example Review Flow

```
## Commit 1 of 4: perf(validator): Reduce validation time by 50%

VERDICT: 🔴 1 BUG + 🟠 1 RISK — 3 MUST HAVE, 3 NICE TO HAVE — DO NOT MERGE
MUST HAVE: (1) empty-pod IndexError at hash.py:88  (2) failure metric never fires
on timeout  (3) subject claims an outcome the body never substantiates
Score: 4/10

## 🔴🟠 REAL ISSUES — the code is wrong or hazardous

### 🔴 BUG · MUST HAVE: blacklist lookup crashes on an empty pod list
`validator/hash.py:88` - `pods[0].name` runs before the empty check.
FAILS WHEN: gateway returns zero pods (happens on every cluster cold start)
→ IndexError, validator loop dies, no pod gets validated until restart.
VERIFIED: traced from `validate_all()` at line 40; nothing guards the call.
[show code]
Fix: [show fix]

### 🟠 RISK · MUST HAVE: failure metric never fires on the timeout path
`validator/hash.py:123` - logs "pod failed" but never calls `record_failure()`.
TRIGGERS WHEN: pod times out (the most common real failure).
→ Grafana shows zero failures during an actual outage. Blind in prod.
[show code]
Fix: [show fix]

---

## 🟡⚪ NOT BROKEN — code is correct (some may still block)

### 🟡 QUALITY · MUST HAVE [subject makes a claim the diff can't back; history is permanent]
"Reduce validation time by 50%" is an OUTCOME, and nothing in the body shows
where 50% comes from. Fails "If applied, this commit will... reduce validation
time" (awkward). Should be: "use hashY instead of hashX for lookups" - and the
50% goes in the BODY with the 100ms → 50ms numbers behind it.

### 🟡 QUALITY · NICE TO HAVE: body missing the WHY
Doesn't say: hashX did O(n) iteration → CPU spikes; hashY is O(1).

### 🟡 QUALITY · NICE TO HAVE: past tense in body
"Changed from hashX to hashY" → "Replaces hashX with hashY".

### ⚪ NIT · NICE TO HAVE: subject capitalized
"Reduce" → "reduce".

### ✅ Correct:
- Type is right: perf
- Has scope: (validator)
- The hashY swap itself is correct - the algorithm change is sound
```

And when it's clean, the verdict says so plainly - don't make a pile of nits look like danger:

```
## Commit 2 of 4: fix(gateway): add null check to token extractor

VERDICT: ✅ NO REAL ISSUES — 0 MUST HAVE, 2 NICE TO HAVE — SHIP IT
MUST HAVE: none.
Score: 9/10

## 🔴🟠 REAL ISSUES
None - no 🔴 and no 🟠. I traced both new branches in `extract_token()` and the
null path is handled; metric fires on every path; no callers of the removed
helper remain in HEAD (grepped).

---

## 🟡⚪ NOT BROKEN
### ⚪ NIT · NICE TO HAVE: redundant comment
`gateway/auth.py:31` - `# check if header exists` above `if not header:` - delete it.
### ⚪ NIT · NICE TO HAVE: trailing whitespace
`config/models.yaml:14`
```

Then wait for me to say "fix it" or "its ok" or "next commit" before continuing.

### When to Fix vs When to Ask

**The default for every review is: report it, write out the fix, and WAIT** - same as "Then wait for me to say 'fix it' or 'its ok' or 'next commit'" at the end of the example flow. Finding a 🔴 is not permission to edit my files. I review commit-by-commit, so unbidden edits land while I'm still reading the finding.

**Fix on sight, no permission needed - only when I've already told you to:**
- When I say "fix description" or "fix commit message"
- When I explicitly say "fix it"
- When I say "fix the must haves" - fix every MUST HAVE item in the roll-up, including promoted 🟡 ones, and nothing else
- When I set a target for the fixes - within the limits of "Fixing toward a target" below

**Show me the exact fix, then wait for my word:**
- **🔴 BUG · MUST HAVE and 🟠 RISK · MUST HAVE** - show me the diff you'd apply, don't apply it. Whether a merge-blocker gets fixed now, ticketed, or shipped knowingly is my call
- Design choices (Gauge vs Histogram) where both are valid
- Large refactors that change behavior
- Anything that might be intentional

**Never touch unless I say so:**
- Everything labelled NICE TO HAVE - that label means it's my call by definition

### Fixing toward a target

When I set a target for the fixes - "fix until the score is 8+ and the verdict is SHIP IT", in whatever words - the target is a correct branch, and the score only measures it. A fix that brings a bug of its own is worse than the finding it closed: the finding was named and visible, the new bug is neither.

- **Every fix is the smallest, plainest change that closes its finding** - delete, reorder, rename, add the missing guard or the missing call: a change a reader verifies at a glance. A fix that needs a new mechanism, a new code path or a restructure, or that touches code the finding never named, is not easy: show it and wait, whatever the target says.
- **Every fix answers two questions as it is made: does it do what it claims, and did it break anything around it?** Read its diff against this standard, trace what it touches - its callers, the paths beside it, the rest of the branch - and run what can be run. Re-scoring the finding it closed answers neither.
- **A fix that fails either question gets an easy fix of its own, or it stops.** When no easy fix makes both answers yes, stop and ask me: name the finding, what the fix failed to do or broke, and the options as you see them. Never stack a hard fix on top of it to reach the target.
- **One round of fixes, then one more review of the whole branch at HEAD** - not only the findings it fixed: a fix lands in code the rest of the branch depends on. When that review still finds anything the target needs fixed, stop and ask me before a second round, even in the middle of a goal: the goal is why the fixes run, never permission to keep going past this point.
- **The score moves only because the code got better.** Never reach the target by demoting a tag, softening a finding, or deleting the test, check or log that exposed the problem.
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
