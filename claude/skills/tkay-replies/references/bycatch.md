# Bycatch is reported where it is found, by number

**Something found on the way - a bug, a stale doc, an exposure outside the
change in hand - is reported in the reply of the step that found it**,
never saved for the end of the task, where a long run buries it and a
summary drops it.

- **Under a `### 🎣 Bycatch` heading, above the ❓ block**, one line each:
  what it is, with its file.
- **Numbered `B<n>` across the whole session**, so "add the B2 fix" names
  one. A new item takes the next free number, and one reported again keeps
  its number. A code review's bycatch table takes its rows from the same
  count. After a context summary, numbering goes on from the highest `B<n>`
  still in the context.
- **Reported, never fixed.** Its fix is made only when I ask for it in words
  that name it; `questions.md` says why it never rides inside another
  proposal.
- **It is for replies to me in chat** - never a commit message, a chat post
  or a file, whose own conventions hold.

The case that taught it: outside a code review, a session mentioned what it
found wherever it happened to, with nothing to answer it by.

```
❌ ...the retry now backs off. By the way, the README still names the old
   --legacy flag.
✅ ### 🎣 Bycatch

   - **B3.** `README.md` still names the old `--legacy` flag.
```
