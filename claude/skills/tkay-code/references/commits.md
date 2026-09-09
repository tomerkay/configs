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
backup first, do it, then prove it with `git diff <backup> HEAD` returning empty -
and say the backup's name so I can drop it.

**Whether the branch is already pushed is NOT an input to this decision - ever.**
Do not check it, do not ask about it, do not mention it as a factor. I force-push
my branches, so a commit that is already on the remote squashes and amends exactly
like one that is not. "It's already pushed" is never a reason to make a new commit
instead of amending, and it is never a reason to leave a bad message standing.
Other reasons to prefer a new commit still hold; that one does not exist.

**When I ask whether the branch is ready and the answer is yes, ask in the same
message whether to delete the backup branches you made** - by name. Lead with the
yes, then the question. A branch I am about to ship should not leave
`pre-squash-backup` and friends sitting in my branch list, and I am the one who
decides when the safety net comes down - never delete one on your own
initiative, and never quietly leave one behind either.

## Documentation Sync on Every Commit

**Before creating ANY commit, check whether the change makes existing documentation stale:**

1. **Repo `CLAUDE.md` / `.claude/CLAUDE.md`**: Does the commit change architecture, design decisions, flows, config structure, metrics, gotchas, or any behavior documented there?
2. **Any `README.md`** in the repo (root or subdirectories near the changed files): Does the commit change usage, setup, configuration, endpoints, or behavior documented there?

If yes → first ask WHY it went stale. If the doc restated a value, a default
or a list that lives in values.yaml or the code, the fix is to DELETE the
restatement and point at the source - not to update the number, which keeps
three copies alive (see the one-source-of-truth rule in my global CLAUDE.md).
Only content with no other home - design rationale, gotchas, the operator guide,
a contract consumers depend on - is updated in place. Either way, in the SAME
commit. If the docs are already accurate, say so briefly and move on - don't
update docs just to touch them.

This applies to every commit, not just when I explicitly ask for documentation updates.

## Git Commit Message Standards (Conventional Commits 1.0.0)

**Structure:**
```
<type>(<scope>): <subject>

[body: WHY this change + OUTCOME/IMPACT]

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

**The Body (wrap at 72 chars):**

**START with this structure whenever it's relevant (i.e. the commit changes
existing behavior — most feat/fix/perf/refactor commits):**
1. **What used to be** — the previous state/behavior and its problem
2. **What this changes** — what the commit does about it
3. **Why** — the motivation / rationale for this approach
Then, after that narrative, add implementation details (bullets, technical
rationale, impact numbers). Skip the structure only where it genuinely
doesn't apply (e.g. a trivial chore/docs commit with no "before").

- Explain WHY the change was necessary (the problem)
- Detail the OUTCOME/IMPACT (benchmarks, behavior, architecture wins)
- Contrast old vs new behavior
- Include technical rationale

**Examples (WRONG vs RIGHT):**

**Performance (perf):**
- ❌ `perf(validator): reduce validation time by 50%` (outcome in subject)
- ❌ `perf(validator): swapped out hashX because it was slow` (past tense, vague)
- ✅ `perf(validator): use hashY instead of hashX for lookups`
  ```
  Reduces validation latency by 50% (from 100ms to 50ms per pod)
  under peak traffic loads.

  Previous implementation used hashX with O(n) array iteration.
  Replacing with hashY enforces O(1) direct key lookups, preventing
  CPU spikes when handling large blacklist payloads.
  ```

**Bug Fix (fix):**
- ❌ `fix(auth): application crashes when users hit submit` (symptom focused)
- ❌ `fix(auth): clean up auth flow bugs` (vague, actionless)
- ✅ `fix(auth): add null coalescing to token extractor`
  ```
  Prevents unhandled ReferenceErrors when incoming requests omit
  Authorization headers.

  Previously headers.authorization.split(' ')[1] threw crashes when
  headers.authorization was undefined. Now returns empty string fallback.
  ```

**New Feature (feat):**
- ❌ `feat(billing): unblock international expansion launch` (business milestone)
- ❌ `feat(billing): add a bunch of stripe stuff` (vague)
- ✅ `feat(billing): implement multi-currency stripe webhooks`
  ```
  Adds support for capturing and persisting non-USD transaction events
  from Stripe API gateway.

  Processes invoice.payment_succeeded payloads with ISO currency codes,
  runs real-time conversion via ledger service before updating balances.
  ```

**Refactor (refactor):**
- ❌ `refactor(db): make query logic look cleaner` (subjective, opinionated)
- ❌ `refactor(db): modify user queries` (too generic)
- ✅ `refactor(db): extract user query pipeline to repository class`
  ```
  Decouples raw SQL compilation from HTTP controllers, isolating data
  hydration in /repositories.

  Enables easier unit testing by mocking data interfaces without spinning
  up PostgreSQL test containers.
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
