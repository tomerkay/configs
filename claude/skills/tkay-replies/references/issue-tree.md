# The issue tree: issues and plans are a table of contents, never a table

**Whenever I ask where we stand - "open issues", "open questions", "a
table", "a list", "what's left", in whatever words - or for a plan we are
still brainstorming, the answer is the issue tree below, shaped like a document's
table of contents.** A plan's items say what we want, never how it is built:
no tests, commits or contract until I ask for the full plan. Never a markdown
table with columns, and never a list whose items run to sentences: not when
another part of the same reply is a table, and not when each item has several
things worth saying. Whatever does not fit on the item's one line is left out.
The shape, with its outline numbers and states:

```
- **1.** Release branch ⏳
  - **a.** rebase onto main 👉
  - **b.** MR description ⏳
- **2.** Detector change 🤝 kept as one commit (just now)
- **3.** Board panel 🙅 left as it is
```

**When issues pile up in a session, a reply that moves to
another item opens with a short tree of them**, right after the reading list
when the reply has one, so I can see where we stand and that we are still on
track. The tree is kept from the moment two or more threads are open at
once, an issue nests inside another, I say "one by one" or the like, or I
ask for it; a single-topic exchange has none.

**It appears only when the item in hand changes**: a new issue opens, which
grows the tree, or one is settled and we move to the next - and whenever I ask
to see it, or ask whether we are done while anything is still open. While we
are still talking about the same item - a follow-up, a
clarification, another round on it - the reply has no tree.

**When I ask whether we are done, the answer is checked, never given from
memory**: every proposal or question with no answer, every step staged or
waiting on me, every drawback I have not answered, every change left
uncommitted, every background run still going. While any is open, the reply
opens with the tree, written in full whatever its size. An item I have
answered - accepted, waved off, told you to leave - is closed, and so is a
question a later one replaced.

**When nothing is open, the closing comes in two steps:**

- **Something left to clean up** - scratch files, a working directory, test
  leftovers you made: the reply opens with "Yes - nothing open left, only
  <the cleanup> to delete.", says what it holds, and ends with deleting it as
  a ❓ line with no assessment under it, as `assessment.md` says, since
  deleting what the session left behind has nothing to weigh.
  The cleanup is not open work, so the answer to "are we done?" is yes.
- **Nothing to clean up**, or I have answered the cleanup either way: the
  reply opens with "Yes, you can exit now." Under it comes "Here's a short
  summary of the session:" and a few plain-language bullets on what we did,
  what changed and where it landed - a recap for a person, not a report: no
  file dumps, no command output, no findings given again, one line each.

The case that taught the first step:

```
❌ Not quite. Everything is closed except the handoff directory:
✅ Yes - nothing open left, only the handoff directory to delete.
```

- **An indented list, one item per line under its parent**, as a document's
  table of contents reads: a table with columns flattens the nesting it exists
  to show.
- **Topics, not details: the wood, not the trees.** Each line names a
  subject in plain words a person who was not in the session would follow -
  "commit authorship", "the TLS question" - never a commit SHA, file, line,
  function, flag, value or count. A step taken on a topic is not an item:
  "squashed into the first commit" is the work, and the topic it served gets
  one line. A line that only makes sense after reading the conversation is a
  detail; cut it or lift it to its topic.
- **One line per item, nested under its parent**, a few words that make it
  clear what it is, then its state: ⏳ open; 👉 the one this reply is on;
  🤝 decided, with what was decided in a few words, and not carried out yet -
  staged, planned, or waiting on a step; ✅ done, carried out - committed,
  installed, posted, or settled with nothing to carry out, such as a
  question answered; 🙅 declined, a change I turned down, such as "left as
  it is". Nest only where the sub-items are separate decisions, never to
  list how a decided item was done.
- **Only what my latest answer sealed ends with `(just now)`**, after its
  state - decided, declined or done - so I see what we just sealed: one
  item, or each item that one answer sealed together. An item an earlier
  answer sealed never carries it, and the next tree drops it. The case
  that taught it, a tree where the first item was sealed answers earlier:

  ```
  ❌ - **g.** The retry budget 🤝 (just now)
     - **h.** The alert threshold 🤝 (just now)
  ✅ - **g.** The retry budget 🤝
     - **h.** The alert threshold 🤝 (just now)
  ```
- **Every item carries an outline number I can answer by**, in bold: `1`,
  `2`, `3` at the top, `a`, `b`, `c` under them, `i`, `ii`, `iii` below
  that - so "**1.b.ii**" names one item. An outline number never changes for the rest of the
  session: a settled or collapsed item keeps its outline number, and a new
  item takes the next free one. The words after it are free to change.
- **A branch whose items are all done or declined collapses** into one line - 🙅
  when every item was declined, ✅ otherwise - and the tree stops appearing
  once nothing in it is open.
- **It is navigation, not a recap.** No reasoning, no repeated findings, no
  question text: the proposals and questions still end the reply as ❓ lines.
  A code review in the same reply keeps its own shape below the tree.
