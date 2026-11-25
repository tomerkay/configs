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

## Before a CR starts

**The session that takes a CR request asks two things before the review
starts, each on a line of its own and both in one reply**: whether the
CR also runs tests, and, when no plan or spec was given, whether there is
one.

**Whether it runs tests is asked whatever record is at hand**, worded by
what is at hand:

- **No record, and no CI on the commit under review:**

  ```
  ⚠️ Should this CR read the code only, or also run the tests? No test record was given and no CI ran on this commit, so running them means running all of them. Read only, every claim that needs a run stays untested, and the merge waits on tests.
  ```

- **A record or CI that covers the commit under review**, with the count
  of the runs it holds:

  ```
  ⚠️ Should this CR read the code only, or also run the tests? <The test record | CI> covers this commit with <n> passing runs, which it will read, not repeat; running adds only the new test against the parent commit and anything <the record | CI> misses. Read only, those stay untested.
  ```

- **A record whose runs do not match the commit under review**, found by
  comparing each entry's tree with the commit's, with the counts:

  ```
  ⚠️ Should this CR read the code only, or also run the tests? The test record given doesn't match this commit: <n> of its <m> runs are on another version of the code, so running means running those again. Read only, every claim that needs a run stays untested, and the merge waits on tests.
  ```

**The plan is asked about only when none was given:**

```
⚠️ No plan or spec was given for this CR, so it can only judge the branch against itself: no goal, contract or incident is checked. Is there one to give, or should it review the branch only?
```

- **A line is skipped when its answer is already known.** The tests line
  only when the request says which ("read only", "with tests"); the plan
  line when the request says there is none ("no plan", "branch only"),
  names the plan or spec, or the session wrote the work from a plan and
  hands it over itself.
- **It is asked once per session**, so a review in a fresh agent is handed
  the answers.
- **"Read only" runs nothing**: every claim that needs a run is a 🧪
  untested finding, or a 🟠 when the review doubts it, and the branch
  call waits on tests.
- **A review another agent started never asks**: nobody is there to
  answer. It runs tests, reading what its record covers, unless its
  prompt says to read only, and names what it was not given on its Given
  line.
- **Only a CR asks**: a plan review judges the plan itself, and a doc
  review runs no tests.

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
it and was not told to read the code only, as though the record did not
hold it.

**Two other sources count, each on its own terms:**

- **A goal run's runs are read from its test record**, as above; its
  report's suite lines only point there.
- **A CI pipeline that passed on a commit whose tree is the one under
  review**: a CI checkout is clean by construction, and the pipeline names
  the commit it ran on, which stands in for the log's first line. A job
  counts only for the tests it ran.

**What a review still runs itself**, record or not, unless it was told
to read the code only - the runs no writer makes:

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
