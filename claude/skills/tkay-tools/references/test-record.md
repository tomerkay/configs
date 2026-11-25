# The test record

**The session that writes code keeps a record of every test it runs on
that code, so a review reads a run that already passed and never makes
it again.** A test the writer, a goal run or CI already passed on the
exact code under review proves nothing new when it runs a second time,
and a flaky one only adds noise.

## Where it lives

- **Beside the plan the work follows**, named after it: `<plan>.tests.md`
  next to `<plan>.md`.
- **In the session's scratch directory when there is no plan, or the plan
  sits inside a repo**: the record is never committed, and a file of the
  session's own inside a repo is one a commit can sweep in.
- **Whoever starts a review in another agent hands it the record's path**,
  with the plan's. A review in a session I open myself gets the paths from
  me.

## An entry

**One line per run, added when the run ends, never edited afterwards:**

```
<when> · <the command, in full> · <the code it ran on> · <passed | failed> · <the log's full path>
```

- **The code it ran on is named by what its content is, never by a
  commit**, so a reworded commit keeps its runs:
  - **In a git checkout**, the tree of the commit checked out
    (`git rev-parse 'HEAD^{tree}'`), followed by `clean` when `git status
    --porcelain --untracked-files=all` printed nothing as the run started,
    or `dirty` when it printed anything. A dirty run is recorded and is
    never trusted as a pass: what it ran on is in no commit.
  - **For files outside git** - staged copies - the path and the
    `shasum -a 256` hash of every staged copy the run reads.
- **The log opens with that same name**, printed by the command that runs
  the test, then a line that marks where the test's own output starts, so
  the log on its own shows what the run tested. The tree argument is
  quoted: zsh's extended globbing reads an unquoted `^` as a pattern.

  ```
  { git -C <checkout> rev-parse 'HEAD^{tree}'; git -C <checkout> status --porcelain --untracked-files=all; echo '--- test output'; <the test command>; } > <log> 2>&1
  ```

  ```
  { shasum -a 256 <each staged copy>; echo '--- test output'; <the test command>; } > <log> 2>&1
  ```

- **A failed run is recorded too**: the record says what was tried, not
  only what passed.

## What a review does with it

**A review reads a run, and does not repeat it, when all of these hold:**

1. it passed;
2. it is `clean`, and its tree is the tree of the commit under review
   (`git rev-parse '<commit>^{tree}'`) - or, for files outside git, every
   hash it lists is the hash of that copy under review;
3. its log exists and opens with that same tree or those same hashes,
   with no line between them and `--- test output` but, for a checkout,
   the tree.

A run that fails any of them is run again by the review, when it can run
it, as though the record did not hold it.

**Two other sources count, each on its own terms:**

- **A goal run's runs are read from its test record**, as above; its
  report's suite lines only point there.
- **A CI pipeline that passed on a commit whose tree is the one under
  review**: a CI checkout is clean by construction, and the pipeline names
  the commit it ran on, which stands in for the log's first line. A job
  counts only for the tests it ran.

**What a review still runs itself**, record or not - the runs no writer
makes:

- **A new test against the parent commit**, unless the record holds a
  failed run of it there: its log opens with the parent's tree, lists only
  the new test's files as changed, and shows the new test's own assertion
  failing - not a build, import or setup error. A test that passes on the
  code before the fix pins nothing.
- **A repro of a bug the review suspects**, which turns a doubt into a
  failure or into nothing.
- **Any run no trusted entry covers.**

**The review says where each result came from**: a run it read from the
record or CI is named as read from there, beside the runs it made itself,
so I see which claims rest on someone else's run.
