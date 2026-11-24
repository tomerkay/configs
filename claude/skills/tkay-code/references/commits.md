# Commit Standards

**A repo that documents its own commit convention overrides this file**, and
the override is named to me in one line - with one exception, under "Every
commit carries a body" below.

**Every commit is signed, on a machine set up to sign**: one where
`git config commit.gpgsign` is true or `git config user.signingkey` names a
key. There, never `--no-gpg-sign`, and a rebase or cherry-pick re-signs
with `-S`. Inside a sandbox gpg cannot reach its agent or open its key
database, so signing fails and a signature check reports `%G?` as `E`
(cannot check) on a good signature. Run both the commit and the check
outside the sandbox, and never commit without the signature.

**On a machine with neither set, commits go in unsigned**, with no `-S`
anywhere, and the first commit of the session says so in one line. A
signature that fails on a machine set up to sign is never this case: it
stops the commit.

**How commits are cut is `commit-boundaries.md`'s**, beside this file. This file is how each
commit's message is written, and how a branch is named.

## The Message

**Structure:**
```
<type>(<scope>): <subject>

[body: Before / Change / Why - see "The Body"]

[footers: BREAKING CHANGE, Closes #123, Co-authored-by]
```

**The Header (≤72 chars, ≤50 preferred):**
- **Subject line test**: "If applied, this commit will... `<your subject>`"
- **Describe the action, not the outcome**: State what code structure changed
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

**The Body (wrap at 72 chars): three labelled sections, short, and Bycatch
when the commit carries one**

**Every commit carries a body.** A repo convention about the subject line,
its prefix or its format never removes it; only a repo rule that a commit
must carry no body does, and that one is never silently followed: quote it to
me and ask before the first commit whether to follow it.

Every body is exactly these three sections, in this order, each its own
paragraph opening with its label - plus a fourth, Bycatch, only when the
commit carries one (see "Bycatch in a Commit" below):

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
- **Nothing after Why** except the Bycatch section and the footers.

**Bycatch in a Commit**

**Bycatch - a fix found on the way, outside the change the commit is for -
that rides along in another commit is written down, never left for the
reader to find in the diff**: a section after Why, its label on a line of
its own, one bullet per item.

```
Bycatch:
- <what was fixed, in one short line>
```

- **Bullets only.** No Before / Change / Why per item.
- **A bullet that is not one simple line is a sign to apply the one-thing
  test** of `commit-boundaries.md`: an item that needs a reason, a second line or a sub-bullet is
  probably a change a reader, a bisect or a revert would want apart. When
  one of them would, it is a commit of its own; when none would, the longer
  bullet is the cheaper cut.
- **No bycatch, no section.** A fix for a shipped bug never has one: it
  stands alone, as `commit-boundaries.md` says.

```
❌ Bycatch:
   - the retry loop now backs off exponentially instead of retrying at a
     fixed interval, because the fixed one hammered the API on outages
✅ Bycatch:
   - fix a typo in the retry log message
```

The ❌ bullet is a behaviour change with its own reason: it gets a commit of
its own.

**Examples (Wrong vs right):**

**Performance (perf):**
- ❌ `perf(validator): reduce validation time by 50%` (outcome in subject)
- ❌ `perf(validator): swapped out hashX because it was slow` (past tense,
  vague)
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
- ❌ `feat(billing): unblock international expansion launch` (business
  milestone)
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

**Two commits whose message says more:**
- **A fix for a shipped bug**: Before names the trigger, the symptom and the
  root cause; Why says why this is the root and not the symptom, and how it
  was verified; and a `Fixes: <sha> ("<subject>")` footer names the commit
  that introduced the bug, when it can be found.
- **A version bump**: its body names the commits it releases as "the commits
  below this one", not by hash, and its type is `chore`.

**Footers:**
- Breaking changes: `BREAKING CHANGE: uuid field renamed to id`
- Issue tracking: `Closes #1234`
- Co-authors: `Co-authored-by: <the model that actually wrote the commit>
  <noreply@anthropic.com>` - use the model you actually are, never a model name
  copied from a config file

## Verifying a commit message

Writing or amending a commit message follows this process:

1. **Run `git show HEAD` or `git diff HEAD~1 HEAD`** - look at the real
   changes
2. **Verify every claim** in the commit message against the actual diff:
   - For each bullet point, find the corresponding code change
   - If you claim "rename X → Y", find the line that shows `-  label: 'X'` and
     `+  label: 'Y'`
   - If you claim "remove column Z", find the line that shows `-  { id: 'Z',
     ...` being removed
   - If you claim "add feature W", find the lines showing W being added
3. **Flag missing changes** - check whether significant changes in the diff
   are left out of the message
4. **Remove false claims** - delete any claim you can't find evidence for in
   the actual diff
5. **Be specific about what changed** - use actual old/new values from the diff

**Commit message patterns that fail the check:**

❌ **Accumulated leftovers from session discussion:**
```
- Fix "/GPU" spacing (remove space before slash)
```
When the actual change is: `'QPS Per GPU'` → `'Avg Achieved QPS/GPU'` (not
removing a space!)

❌ **Claiming changes from earlier commits:**
```
- Reorder columns
```
When the reordering was only discussed, and this commit does not do it.

❌ **Vague claims without verification:**
```
- Improve performance
```
Without showing what specifically changed in the code.

**What passes it:**

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
  not "Fix /GPU spacing" (misleading - there was no space before slash to fix)
```

**The Test:**

Before finalizing any commit message, ask of each claim:
- "Can I show the exact line in `git show HEAD` that proves this claim?"
- "Is this claim about this commit, or something we discussed earlier?"
- "Am I precise about which old value changed to which new value?"

A claim that fails any of the three is deleted or rewritten accurately. A
false claim in a commit message stays in history for good, so no claim goes
in that the diff does not show.

## Branch Names

**Before naming a new branch, read the convention of the repo it lives in and
follow it.** The remote branches show it - `git for-each-ref
--sort=-committerdate --count=30 --format='%(refname:short)' refs/remotes` -
whether names carry a person, a type (`feat/`, `fix/`), a ticket key, and which
separator. Check the repo's `CONTRIBUTING.md`, `CLAUDE.md` and README too, and
any CI rule that matches on the branch name: a name that misses such a rule
runs a different pipeline without saying so.

**When the convention puts a person in the name, that person is me**, spelled
as the handle I have given you, whatever older branches of mine use. With no
handle given, spell it the way my own recent branches in this repo do; with
none of those either, the local part of `git config user.email`. When the
convention carries no person, do not add one.

**The rest of the name is the change, in kebab case** - what the branch does,
never who asked for it or what wrote it (`fix-by-claude` says nothing). A
ticket key goes in when the convention has one and the task has one.
