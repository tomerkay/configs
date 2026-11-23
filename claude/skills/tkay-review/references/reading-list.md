# A message about several things opens with the reading list

**When my message talks about several things, not one, the reply opens with
the reading list: how you read each thing I said**, whatever shape I wrote
it in - a list, outline numbers or plain prose. A misreading is caught on
its first lines, before any work rests on it. A message about one thing
gets no reading list. Nothing goes above it: a line another rule puts at
the top of a reply comes right after it.

The reply then reads, top to bottom:

- **1.** `### How I read your items`, the reading list under it, and a `---`
  line that ends it, with a blank line above, or markdown turns the
  last line of the list into a heading.
- **2.** The issue tree, when one is due - `issue-tree.md` says when.
- **3.** The rest of the reply, with the ❓ block last.

- **A bulleted list, numbered `R1`, `R2`, `R3` afresh in each reply** - R
  for reading - with `a`, `b`, `c` bulleted under a line for separate parts
  of one thing, so `R3.a` names one line. Bare lines fold into one
  paragraph; the R keeps a line apart from a `Q<n>` and from the tree's
  outline numbers.
- **One short line per thing I said, keyed by what I named.** A thing that
  names a tree item or a `Q<n>` carries that number inside the line
  (`**R1.** **2.e**: ...`). One that names nothing gets a line of its own, and a
  principle that settles other items lists them as its sub-lines.
- **A reading, not a reply.** Each line says what you took me to mean - a
  decision, a correction, a question I asked. What you say about it comes
  after the `---`, headed by the same `R<n>`; a line that needs nothing
  more gets no part of its own.
- **In your own words, never mine copied back**, so we see we are really on
  the same page. A line that pastes my phrasing proves only that you can
  copy it; a reading in your words shows what you understood, and a
  misreading shows in it. The case that taught it:

  ```
  I wrote: "q24 remove them, the review only should write out the fixes"
  ❌ **R1.** **Q24**: remove them, the review only should write out the fixes.
  ✅ **R1.** **Q24**: take both fix sections out; a review lists fixes and
     never makes one.
  ```
- **Two readings that lead to different work are asked** as a ❓ question;
  the line says it reads two ways and names both.
- **It is for replies to me in chat** - never a chat post, a commit
  message or a file.

The case that taught it: a message in prose that answered several plan
items by their outline numbers and stated, unnumbered, that only managed
endpoints are enforced:

```
### How I read your items

- **R1.** **2.e**: manage-on checks only the live deployments; the others can be anything.
- **R2.** **4.k**: you're asking what the stamp is.
- **R3.** The general principle: outside managed endpoints, nothing is enforced. It drops:
  - **a.** **2.d**
  - **b.** **3.b**
- **R4.** **8.e**: you're correcting me: it works after unmanage and re-manage too.

---
```
