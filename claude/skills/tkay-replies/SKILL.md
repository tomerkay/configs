---
name: tkay-replies
description: The shape of a reply in chat - how an answer is held to the truth, the assessment a proposal or a judgement carries, proposals and questions that stop the reply as numbered ❓ lines, the reading list that opens a reply to a message about several things, the issue tree, numbered lists and tables, bracketed copy-paste blocks, and before-and-after snippets. Use before the first reply of a session, and whenever a reply proposes a change or gives an assessment of a change, an option or an idea, stops for an answer, answers a message about several things, shows where we stand, hands over something to copy, or shows how a change will look.
hooks:
  Stop:
    - hooks:
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/question-shape.py"'
        - type: command
          command: 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/assessment-shape.py"'
---

# Reply shapes

How a reply to me in chat is laid out, so I can answer any part of it by its
number and see at a glance where it stops for me. Each shape is in its own
reference; they refer to each other by file name.

| When the reply | Read |
|---|---|
| answers anything - every reply | `references/answers.md` |
| proposes a change, or gives an assessment of a change, an option or an idea | `references/assessment.md` |
| stops for my answer - a proposal or a question | `references/questions.md` |
| answers a message of mine about several things | `references/reading-list.md` |
| shows where we stand, or answers whether we are done | `references/issue-tree.md` |
| holds a list or a table | `references/numbered-lists.md` |
| hands me something to copy and paste | `references/copy-blocks.md` |
| shows how a change will look | `references/before-and-after.md` |

**Read the reference before the reply that needs it.** Never answer from
memory of a reference you have not read this session.

The hooks in this skill's frontmatter check every reply's ❓ lines and
assessments once the skill is loaded, and send a reply back once when one
breaks its shape.

These shapes are for replies in chat only - never a commit message, a chat
post or a file, whose own conventions hold.
