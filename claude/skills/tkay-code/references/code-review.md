# Code Review Standards

## How I Want Code Reviews Done

When I ask for a code review (CR), I want you to be **thorough as fuck** because this is serious production code. Don't hold back, don't be nice - if something is wrong, tell me straight up.

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
- `🟡 QUALITY · MUST HAVE [violates an explicit rule in this skill or the repo's CLAUDE.md - name the rule]`

**Legitimate reasons to promote 🟡/⚪ → MUST HAVE:** false or misleading commit message (git history is permanent), a violation of a rule stated explicitly in this skill or the repo's `CLAUDE.md`, or docs that now actively lie about behavior.
**Legitimate reasons to demote 🟠 → NICE TO HAVE:** pre-existing condition this commit didn't introduce, or a trigger threshold we are provably nowhere near. Say which.

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

### The closing table — the last thing in every CR

After the last commit's review, end the CR with one table: one row per commit,
in branch order, three columns.

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
| `🔀 SQUASH INTO <short-sha>` | it only exists because an earlier commit on the branch got something wrong or left it half done — the squash rule in `references/commits.md` |
| `🗑 DROP` | the branch is better without it: nothing needs it, a later commit undoes it, or it is out of scope |

The verdict agrees with that commit's VERDICT line: never `✅ SHIP IT` while its
MUST HAVE count is above zero. A single-commit CR still ends with a one-row
table. The closing table and the leftovers table below are the only summaries
allowed in a CR.

### The leftovers table — right after the closing table, every CR

The closing table judges the commits. The leftovers table holds what the review
turned up on the way that is NOT a finding against a commit: a pre-existing bug
in a file the branch touched, a stale or false doc next to the change, a trap
the diff happened to expose. Three columns:

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

When nothing came up, the table is one line instead: "Leftovers: none found on
the way." Never skip it silently - an absent table reads as "did not look".

### Rules that keep the tags honest

- **No severity inflation.** If you cannot write the concrete failure scenario, it is NOT a 🔴 BUG - downgrade it. Dressing a nit up as a bug wastes my time and destroys my trust in every other tag in the review.
- **No severity deflation.** Never bury a 🔴 inside a nit list and never soften it ("might be worth considering..."). If it's broken, the first words are "🔴 **BUG** · MUST HAVE:".
- **Verify before tagging 🔴.** Read the code path, grep the callers, check HEAD. If you couldn't verify, tag it **🔴 BUG (UNVERIFIED) · MUST HAVE** and state exactly what you couldn't check.
- **State confidence when you're unsure.** "🟠 RISK · MUST HAVE (high confidence)" vs "🟠 RISK · MUST HAVE (speculative - couldn't reproduce)". Never hide uncertainty behind vague wording, and never let low confidence silently become NICE TO HAVE.
- **Where the borderline cases land:**
  - Weak/vague commit message → 🟡 · NICE TO HAVE. Commit message making a FALSE CLAIM about behavior → still 🟡 on severity (the code works) but **MUST HAVE** on policy - it lies to whoever bisects this later, and history is permanent. This is the textbook case for why the two axes exist.
  - Missing log, or wrong log level → 🟡. Metric defined but never called, or called on only some code paths → 🟠 (blind in prod).
  - Redundant comment, YAML whitespace/blank lines, ordering, style preference → ⚪. Genuinely misleading name or a DRY violation someone will trip over → 🟡.
  - Suspicious logic you traced and it's genuinely wrong → 🔴. Suspicious logic you can't prove either way → 🟠, and say what would prove it.
  - Perf: measurable regression on the per-request path → 🟠 minimum. Cold path → 🟡.
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

3. **Metrics & Observability** [default: 🟠 · MUST HAVE for missing/partial metric calls and wrong metric type, 🟡 · NICE TO HAVE for naming]
   - Is every significant event tracked with a metric?
   - Are metrics called BEFORE logs? (metric-first pattern)
   - Are metric names/labels correct?
   - Right metric type? (Counter vs Gauge vs Histogram)
   - Any missing metric calls?

4. **Logging** [default: 🟡 · NICE TO HAVE, missing context on an error path that would block debugging prod: 🟠 · MUST HAVE]
   - Is every metric accompanied by a log?
   - Log levels correct? (INFO vs WARNING vs ERROR)
   - Consistent formatting across similar log messages?
   - Include all necessary context (pod_name, pod_ip, model_name)?

5. **Code Quality** [default: 🟡 · NICE TO HAVE, EXCEPT "logical correctness of NEW code" below - wrong logic is 🔴/🟠 · MUST HAVE]
   - DRY violations? (Don't Repeat Yourself)
   - Ordering issues? (should things be grouped differently?)
   - Naming clarity? (are variables/functions named clearly?)
   - Any TODOs or FIXMEs that shouldn't be there?
   - **Redundant comments**: the comment rules and their worked examples are in `references/code-examples.md`. Flag ANY comment that states the obvious or repeats what code/logs say. When in doubt, the comment should be DELETED.
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

6. **Nits** [default: ⚪ · NICE TO HAVE - always below the divider]
   - Minor style issues
   - Comment quality
   - Documentation gaps

### Review Process

**DO:**
- Review commits ONE BY ONE (commit-by-commit)
- **When reviewing a commit, check HEAD state to verify later commits didn't break it**
- **When methods/functions/metrics are removed, verify they're not called in HEAD**
- **Read and understand NEW code logic** - don't just hunt for bugs, analyze whether the logic makes sense (see "Logical correctness of NEW code" in the checklist above)
- Give each commit a score out of 10
- **End the CR with the closing table, then the leftovers table** (see "The closing table" and "The leftovers table" above)
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

### Code and metrics expectations

**Code must:**
- Follow metric-first, log-second pattern
- Not repeat logic (DRY)
- Have consistent ordering (related code grouped together)
- Handle all edge cases (nil checks, empty collections, etc.)

**Metrics must:**
- Cover every significant log event
- Use correct types (Histogram for durations, not Gauge)
- Be called in every code path (not just happy path)
- Have clear labels that enable useful queries

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

**Show me the exact fix, then wait for my word:**
- **🔴 BUG · MUST HAVE and 🟠 RISK · MUST HAVE** - show me the diff you'd apply, don't apply it. Whether a merge-blocker gets fixed now, ticketed, or shipped knowingly is my call
- Design choices (Gauge vs Histogram) where both are valid
- Large refactors that change behavior
- Anything that might be intentional

**Never touch unless I say so:**
- Everything labelled NICE TO HAVE - that label means it's my call by definition

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

I care about my commits and want them to be perfect. Be thorough, be direct, and don't hold back. If something is wrong, tell me. If something is misleading, tell me. If I'm about to merge garbage, BLOCK ME.

**And be unmistakably clear about two things: is it BROKEN, and do I have to fix it NOW.** Three failures I hate equally:
1. Burying a 🔴 BUG in a list of whitespace nits so I merge broken code.
2. Handing me a scary-looking wall of ⚪ nits with no verdict, so I waste an hour hunting a bug that was never there.
3. Giving me 12 findings with no MUST HAVE / NICE TO HAVE split, so I have to re-triage your review myself before I can do anything with it.

Thorough, clearly triaged, and explicit about what blocks the merge. All three, every time.

That's what good code review is.
