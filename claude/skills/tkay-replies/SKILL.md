---
name: tkay-replies
description: The shape of a reply in chat - how an answer is held to the truth, the assessment a proposal or a judgement carries, proposals and questions that stop the reply as numbered ❓ lines, the reading list that opens a reply to a message about several things, the issue tree, the bycatch list, numbered lists and tables, bracketed copy-paste blocks, before-and-after snippets, the TL;DR that closes a long reply, and the human-readable prose every text a person reads is held to. Use before the first reply of a session, and whenever a reply proposes a change or gives an assessment of a change, an option or an idea, stops for an answer, answers a message about several things, shows where we stand, reports something found on the way, hands over something to copy, shows how a change will look, or runs long - and whenever writing prose a person reads anywhere else: a commit message, a plan, a doc, an MR, a chat post.
hooks:
  Stop:
    - hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/question-shape.py"'
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/assessment-shape.py"'
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/fence-shape.py"'
---

# Reply shapes

How a reply to me in chat is laid out, so I can answer any part of it by its
number and see at a glance where it stops for me. Each shape is in its own
reference; they refer to each other by file name.

**The shapes are generic, not about code.** They hold for a reply about any
work - writing, research, planning, operations, code - and assume no
codebase, so someone who never writes code uses them as they are. An example
drawn from code illustrates a rule and never narrows it.

| When the reply | Read |
|---|---|
| answers anything - every reply | `references/answers.md` |
| holds prose a person reads - and any such prose written elsewhere | `references/human-readable.md` |
| proposes a change, or gives an assessment of a change, an option or an idea | `references/assessment.md` |
| stops for my answer - a proposal or a question | `references/questions.md` |
| answers a message of mine about several things | `references/reading-list.md` |
| shows where we stand, or answers whether we are done | `references/issue-tree.md` |
| reports something found on the way, outside the change in hand | `references/bycatch.md` |
| colours a finding or a bycatch row | `references/severity.md` |
| holds a list or a table | `references/numbered-lists.md` |
| hands me something to copy, paste or run | `references/copy-blocks.md` |
| shows how a change will look | `references/before-and-after.md` |
| runs long enough that I would scroll to read it | `references/tldr.md` |

**Read the reference before the reply that needs it.** Never answer from
memory of a reference you have not read this session.

The hooks in this skill's frontmatter check every reply's ❓ lines,
assessments and code fences once the skill is loaded, and send a reply
back once when one breaks its shape.

**A reply sent back is corrected, never repeated.** A hook runs when the
reply ends, so the reply it objects to is already on my screen. The next
reply is the correction alone: one line saying what was wrong, then only
the lines that change, each under the `Q<n>`, the row or the heading it
belongs to. The block or the table is not printed again, and the rest of
the first reply stands as I read it. The case that taught it, a Why Not
point a hook sent back:

```
❌ ❓ **Q53** <the whole proposal again, with its Call, Change, Why Yes
   and the one corrected Why Not>
✅ Correction to **Q53**: its Why Not point was the change taking effect.
   - **Why Not?**
     - **1.** a cheap fix made at night can bring a bug of its own
```

**A broken fence is the one exception**: every line after it rendered as
raw text, so I never read them. The correction says in one line that a
fence broke, then prints everything from the broken block to the end of
the reply again, each block fenced longer than any fence line it holds.

These shapes are for replies in chat only - never a commit message, a chat
post or a file, whose own conventions hold. The one exception is
`references/human-readable.md`, which binds every text it names, wherever
it lands.
