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

## Commits Serve the Branch - One Thing Each, and No More Cuts Than That

**Commits serve the branch's final outcome, never the other way round.** What
ships is the tree at the top of the branch; the commits are how a reader
understands it, how a bisect finds a fault in it and how a revert takes one
change out of it. A commit is never a target of its own.

**A commit does one thing when a reader, a bisect and a revert each want it
whole.** A reader follows the branch commit by commit without assembling a
change from several; a bisect that lands on it finds one cause; a revert
takes out one change and nothing else. That is the test for every boundary,
squash and split alike - never the size of the diff, the number of files or
the length of a bullet.

**Every boundary costs something, so it must earn itself.** One more commit
is one more message to write and verify, one more commit for a code review
to read, and one more place a change is spread across. A cut none of the three wants is that cost
with no return: a branch of twenty immaculate two-line commits is harder to
read than one of five that each mean something. Both halves of the test
bite - a commit that mixes two things a revert would want apart, and two
commits that are one thing a reader has to reassemble.

**Which commit a change belongs in is judged by the test, and said in one
line before the commit.** The three cases:

- **It belongs in an earlier commit** when it only exists because that commit
  got something wrong or left it half done: it corrects a claim that commit
  made, rewrites prose that commit added, or finishes what it should have
  carried. A doc fix to wording an earlier commit introduced is the usual
  case - see "Documentation Sync on Every Commit".
- **Two commits are one thing** when apart they hide what the branch does:
  one is broken or meaningless until the other lands, or the reader has to
  assemble the change from both. The version bump keeps its own commit
  regardless; see "A Version Bump Is Its Own Commit, at the Top of the
  Branch". A fix for a shipped bug is never one of the two; see "A Fix for a
  Shipped Bug Stands Alone".
- **It stands on its own** when it is a different change for a different
  reason, one that would still make sense if the earlier commit were reverted.

## Two Suits: a Fix Stands Alone, a Feature Is a Series

**A commit is cut by what it is for.** A fix for a shipped bug is one commit
built to travel - the next section. A feature is a series, in this order,
each commit leaving the build and the tests green so any prefix of it is
correct on its own - the shape of the Linux kernel's
[Submitting patches](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)
("Separate your changes") and git's own
[SubmittingPatches](https://git-scm.com/docs/SubmittingPatches):

1. **Preparatory refactors**, one per commit, `refactor:` - each changes no
   behaviour, so a reader checks it by eye and a bisect never lands on it.
   Make the change easy before making the easy change.
2. **The behaviour**, `feat:` (or `fix:`, `perf:`), with the tests that pin
   it in the same commit. Several behaviour commits when a reader, a bisect
   or a revert would want them apart - the one-thing test above - and one
   when they would not.
3. **Docs** the behaviour makes true, `docs:` - or inside the behaviour
   commit when the two lines of a README would stand on their own in no
   reader's eyes.
4. **The version bump**, last - see "A Version Bump Is Its Own Commit, at the
   Top of the Branch".

**A refactor and a behaviour change never share a commit.** The one
exception is a rename the behaviour change cannot land without, and then the
body's Change names the rename as such.

A code review flags a mixed commit as one to split, and a series out of
order as a quality issue: the branch works either way, and the cost is the
reader's. `chore:`, `ci:`, `style:`
and `test:` commits are neither suit and stand alone as they do today.

## A Fix for a Shipped Bug Stands Alone

**A fix for a bug that reached the default branch or a release is its own
commit, and nothing is ever squashed into it or it into anything** - not a
feature, not a refactor, not another fix. It must revert on its own,
cherry-pick to a release branch without dragging anything along, and be the
one commit a bisect lands on. Check where the bug came from before the first
line of the fix: `git merge-base --is-ancestor <introducing-sha>
<default-branch>` exits 0 when it shipped - against the remote copy of the
default branch whenever the repo has a remote.

- **One bug per commit.** No cleanup, no refactor, no second fix, no test
  for anything else.
- **The smallest diff that removes the root cause**, not one that hides the
  symptom.
- **The test that fails without the fix lands in the same commit.**
- **Before names the trigger, the symptom and the root cause. Why says why
  this is the root and not the symptom, and how it was verified.**
- **A `Fixes: <sha> ("<subject>")` footer names the commit that introduced
  the bug**, when it can be found.

**A bug introduced earlier on this unmerged branch is not a shipped-bug
fix.** It never ran anywhere, so its fix belongs in the commit that
introduced it, as the first case of "Commits Serve the Branch" says, and a
code review recommends folding a commit that carries it elsewhere into it.
A follow-up to a shipped-bug fix while that fix is still unmerged belongs
in the fix the same way.

The case that taught it: one fix commit to a shipped hook carried a second,
unrelated selftest with it.

```
❌ fix(gate): expand a bare ~ in the scratch exemption
   Change: a leading bare ~ is expanded for the scratch exemption only ...
   A selftest case pins the denial of an unpinned kubectl that passes an
   empty kubeconfig.

✅ fix(gate): expand a bare ~ in the scratch exemption
   Change: a leading bare ~ is expanded for the scratch exemption only ...
   Fixes: <sha> ("<subject of the commit that added the exemption>")
✅ test(gate): deny an unpinned kubectl with an empty kubeconfig
```

Reverting the ❌ commit to undo a bad `~` expansion also drops a guard
nobody meant to touch.

## Documentation Sync on Every Commit

**Before creating any commit, check whether the change makes the repo
`CLAUDE.md` or any `README.md` near the changed files stale.** A line about
something that no longer exists is deleted, never turned into a record of what
used to be there; a line that is now wrong is corrected in place. Either way
the doc change lands in the same commit. If the docs are already accurate, say
so briefly and move on - don't update docs just to touch them.

This applies to every commit, not just when I explicitly ask for documentation
updates.

## A Version Bump Is Its Own Commit, at the Top of the Branch

**When a repo requires a version bump for a change - a plugin manifest, a
chart version, a package version - the bump is a dedicated `chore` commit,
the last one on the branch, and never folded into the commit that made the
change.** One bump at the top says it releases every commit under it, so a
reader sees at a glance which commits ship together; a bump inside the first
change says nothing about the commits that came after it, and a bump inside
the last one hides which earlier commits it covers. Its body names the
commits it releases as "the commits below this one", not by hash.

A prefix of the branch without the bump then fails a CI version guard on
purpose: that prefix is not a release, and the guard saying so is correct.

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
  test**: an item that needs a reason, a second line or a sub-bullet is
  probably a change a reader, a bisect or a revert would want apart. When
  one of them would, it is a commit of its own; when none would, the longer
  bullet is the cheaper cut.
- **No bycatch, no section.** A fix for a shipped bug never has one - see
  "A Fix for a Shipped Bug Stands Alone".

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
