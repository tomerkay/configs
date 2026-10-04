# Commit Standards

GPG signing config is in my global CLAUDE.md and applies to every commit here —
it is not restated in this file.

## Squash or New Commit - Decide Every Time, and Say Which

**Before every commit, work out which of the two it is and tell me in one line.**
Do not default to a new commit.

- **Squash it into the earlier commit** when the change only exists because that
  commit got something wrong or left it half done: it corrects a claim that commit
  made, rewrites prose that commit added, or finishes what it should have carried.
  Nothing is published, so there is nothing to preserve - my history must not
  record you writing a rationale badly and then rewriting it three commits later.
- **Make it a new commit** when it stands on its own: a different change for a
  different reason, one that would still make sense if the earlier commit were
  reverted.

**Doc edits are where this goes wrong most.** A doc fix to wording an earlier
commit on this branch introduced belongs IN that commit - see "Documentation Sync
on Every Commit" below. A standalone `docs:` commit for it is the very drift that
rule exists to prevent.

**Never choose "new commit" because rewriting history is inconvenient for you.**
That is my history, not your convenience. When a squash needs a rewrite: branch a
backup first, do it, then prove it with `git diff <backup> HEAD` returning empty.
An empty diff means the rewrite is proven: **delete the backup branch straight
away, WITHOUT asking permission** - no question in chat, no offer, no backup left
behind for me to clean up - with `git branch -D` (squashed commits never count as
merged, so `-d` refuses), and report the `Deleted branch ... (was <sha>)` line.
A non-empty diff means the rewrite changed content: stop, keep the backup, and
show me the diff.

**The rewrite itself is scripted, because no interactive editor exists in this
harness.** `git rebase -S -i <base>` works once `GIT_SEQUENCE_EDITOR` names a
script that edits the todo and `GIT_EDITOR` one that overwrites the message
file it is handed. Edit the todo by SHA - `s/^pick <sha>/reword <sha>/` - never
by subject: the todo line may carry a comment marker between SHA and subject,
and a pattern that matches nothing leaves every `pick` in place, so the rebase
"succeeds" with nothing changed. Verify the new SHAs appeared before trusting
it. `git commit --fixup=amend:<sha>` and `--fixup=reword:<sha>` refuse `-m` and
`-F`, so a prepared message cannot ride on them; the `GIT_EDITOR` script is
how it gets in. `-S` re-signs every rewritten commit - confirm with
`git log --format='%h %G? %s'` before deleting the backup.

**Whether the branch is already pushed is NOT an input to this decision - ever.**
Do not check it, do not ask about it, do not mention it as a factor. I force-push
my branches, so a commit that is already on the remote squashes and amends exactly
like one that is not. "It's already pushed" is never a reason to make a new commit
instead of amending, and it is never a reason to leave a bad message standing.
Other reasons to prefer a new commit still hold; that one does not exist.

## Documentation Sync on Every Commit

**Before creating ANY commit, check whether the change makes the repo
`CLAUDE.md` or any `README.md` near the changed files stale.** Which file owns
what, and whether a stale line is deleted or updated in place, is the
`tkay-writing-mds` skill's - load it before touching the doc. Either way the
doc change lands in the SAME commit. If the docs are already accurate, say so
briefly and move on - don't update docs just to touch them.

This applies to every commit, not just when I explicitly ask for documentation updates.

## Git Commit Message Standards (Conventional Commits 1.0.0)

**Structure:**
```
<type>(<scope>): <subject>

[body: Before / Change / Why - see "The Body"]

[footers: BREAKING CHANGE, Closes #123, Co-authored-by]
```

**The Header (≤72 chars, ≤50 preferred):**
- **Subject line test**: "If applied, this commit will... `<your subject>`"
- **Describe the ACTION, not the outcome**: State what code structure changed
- **Use imperative mood**: "add" not "added", "fix" not "fixed"
- **Lowercase, no period**: `feat(auth): add login` not `Add login.`

**Types (SemVer impact):**
- `feat:` - new feature (Minor)
- `fix:` - bug fix (Patch)
- `perf:` - performance improvement (Patch)
- `refactor:` - code change, no behavior change (None)
- `test:` - add/fix tests (None)
- `docs:` - documentation only (None)
- `style:` - formatting only (None)
- `ci:` - CI config changes (None)
- `chore:` - deps, build tools (None)

**The Body (wrap at 72 chars): three labelled sections, short**

Every body is exactly these three sections, in this order, each its own
paragraph opening with its label:

```
Before: what the code did or lacked, and the problem that caused.

Change: what this commit does about it.

Why: why this is the right fix - the failure it prevents, the outcome
it delivers.
```

- **Concise.** Each section is one to three sentences. A section that runs
  longer is carrying something that belongs in the diff, a code comment or
  the MR description.
- **Before is never empty.** For something new, it says what was missing or
  what had to be done by hand.
- **Change describes behavior, not files.** "The bundle loads every skill
  under .claude/skills", not "edit plugin.json and .gitlab-ci.yml" - the diff
  already lists the files. A commit that spans several areas may use one
  short bullet per area inside Change.
- **Why is the argument, not a restatement.** Never "this makes it better":
  name the failure it prevents, the number it moves, or the rule it
  satisfies. Impact numbers and how it was verified go here, in a clause. A
  rejected alternative goes here too, in one clause, when the next person
  would otherwise retry it.
- **Nothing after Why** except the footers.

**Examples (WRONG vs RIGHT):**

**Performance (perf):**
- ❌ `perf(validator): reduce validation time by 50%` (outcome in subject)
- ❌ `perf(validator): swapped out hashX because it was slow` (past tense, vague)
- ✅ `perf(validator): use hashY instead of hashX for lookups`
  ```
  Before: blacklist lookups went through hashX, iterating the whole
  array per key, so large blacklist payloads spiked CPU at peak traffic.

  Change: lookups use hashY, a direct O(1) key lookup.

  Why: validation latency per pod halves at peak (100ms to 50ms), and
  CPU no longer grows with the size of the blacklist.
  ```

**Bug Fix (fix):**
- ❌ `fix(auth): application crashes when users hit submit` (symptom focused)
- ❌ `fix(auth): clean up auth flow bugs` (vague, actionless)
- ✅ `fix(auth): add null coalescing to token extractor`
  ```
  Before: headers.authorization.split(' ')[1] threw a ReferenceError
  whenever a request omitted the Authorization header.

  Change: the token extractor falls back to an empty string when the
  header is missing.

  Why: a missing header is the client's mistake; the request now fails
  authentication instead of crashing the handler.
  ```

**New Feature (feat):**
- ❌ `feat(billing): unblock international expansion launch` (business milestone)
- ❌ `feat(billing): add a bunch of stripe stuff` (vague)
- ✅ `feat(billing): implement multi-currency stripe webhooks`
  ```
  Before: Stripe webhooks carrying a non-USD currency were dropped, so
  those payments never reached customer balances.

  Change: invoice.payment_succeeded payloads with any ISO currency code
  are converted through the ledger service before balances update.

  Why: non-USD payments land in the ledger with no manual
  reconciliation.
  ```

**Refactor (refactor):**
- ❌ `refactor(db): make query logic look cleaner` (subjective, opinionated)
- ❌ `refactor(db): modify user queries` (too generic)
- ✅ `refactor(db): extract user query pipeline to repository class`
  ```
  Before: HTTP controllers compiled raw SQL and hydrated users inline,
  so testing a controller meant starting a PostgreSQL container.

  Change: user queries move into a repository class under
  /repositories, and controllers only call it.

  Why: controllers are unit-tested against a mocked repository, with no
  database.
  ```

**Footers:**
- Breaking changes: `BREAKING CHANGE: uuid field renamed to id`
- Issue tracking: `Closes #1234`
- Co-authors: `Co-authored-by: <the model that actually wrote the commit> <noreply@anthropic.com>` - use the model you actually are, never a model name copied from a config file

## CRITICAL: Commit Message Verification Protocol

**MANDATORY PROCESS when writing/amending commit messages:**

When I ask you to "amend" or create a commit message, you MUST follow this exact process:

1. **Run `git show HEAD` or `git diff HEAD~1 HEAD`** - Actually look at the REAL changes
2. **Verify EVERY SINGLE CLAIM** in the commit message against the actual diff:
   - For EACH bullet point, find the corresponding code change
   - If you claim "rename X → Y", find the line that shows `-  label: 'X'` and `+  label: 'Y'`
   - If you claim "remove column Z", find the line that shows `-  { id: 'Z', ...` being removed
   - If you claim "add feature W", find the lines showing W being added
3. **Flag MISSING changes** - Check if significant changes in the diff aren't mentioned in the message
4. **Remove FALSE claims** - Delete any claim you can't find evidence for in the actual diff
5. **Be SPECIFIC about what changed** - Use actual old/new values from the diff

**BANNED commit message patterns:**

❌ **Accumulated leftovers from session discussion:**
```
- Fix "/GPU" spacing (remove space before slash)
```
When the actual change is: `'QPS Per GPU'` → `'Avg Achieved QPS/GPU'` (not removing a space!)

❌ **Claiming changes from earlier commits:**
```
- Reorder columns
```
When you just DISCUSSED reordering but didn't actually do it in THIS commit.

❌ **Vague claims without verification:**
```
- Improve performance
```
Without showing what specifically changed in the code.

**CORRECT approach:**

✅ **Verify each claim:**
```
- Rename "Type" → "Benchmark Type"
  VERIFIED: git show HEAD shows:
  -  { id: 'benchmark_type', label: 'Type', ...
  +  { id: 'benchmark_type', label: 'Benchmark Type', ...
```

✅ **Accurate description:**
```
- Change "QPS Per GPU" notation to "Avg Achieved QPS/GPU" (use /GPU format)
  NOT "Fix /GPU spacing" (misleading - there was no space before slash to fix)
```

**The Test:**

Before finalizing ANY commit message, ask yourself:
- "Can I show the exact line in `git show HEAD` that proves this claim?"
- "Is this claim about THIS commit or something we discussed earlier?"
- "Am I being precise about what OLD value changed to what NEW value?"

If you can't answer "YES" to all three, DELETE that claim or rewrite it accurately.

**When I catch you with false claims in commit messages:**

This is a CRITICAL failure. It means you didn't actually verify the diff. I will call you out harshly because commit history is permanent and I care deeply about accurate git history.
