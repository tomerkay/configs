# Bycatch is kept in one file, and shown only in a CR and at the close

**Something found on the way that does not bear on the work in hand - a
bug, a stale doc, a misleading rule, a tool that got a call wrong, in any
repo, document or tool - is bycatch, and every find is a row of the session's
bycatch file.** Three things it never is:

- **A blocker**: what stops the work in hand is part of the task, raised
  in the reply that hits it, whoever owns it.
- **Harm happening now** - a leak, data being lost, a hole letting
  dangerous calls through: raised at once, whatever it bears on.
- **Something that bears on the work in hand**, by your judgement: a find
  worth talking about during the session is part of the work, raised in
  the reply that finds it as a ❓ proposal or question of its own, never
  under a bycatch heading.

**Bycatch is how a session leaves the next one faster and better.** Ask
it of every snag the session hit, in the work and in the setup it runs
on - its instructions, skills and hooks - not only of a defect in the work:
a rule that sent it the wrong way, a fact it had to dig up, a tool or a
hook that cost a retry. Each snag whose fix would spare the next session
the same one is a row.

**A refusal or a rating that stops a command the session meant to run is
a row the moment it stops it**, whatever the session does next - another
route, the claim left untested, or nothing - and before anyone judges
whether the tool was right: the colour it has if the tool was wrong, and
Evidence UNKNOWN. It leaves the file only when a read of the tool's own
rule shows the tool right. A judgement in your head that the tool was
being reasonably careful is no read. The cases that taught it, a hook
that refused a build during a review, and one that refused a read-only
probe:

```
❌ the build refused, `go vet` run instead, and no row: "the hook is
   being careful"
✅ a row written at the refusal; a read of the hook's rule then found a
   build it refuses that writes nothing

❌ the probe refused, its claim left untested, and no row: "nothing was
   worked around"
✅ a row written at the refusal; a read of the hook's rule then found a
   one-line script it refuses that writes nothing
```

## When it is shown

- **Only in two places, and always as the bycatch table below**: a CR's
  bycatch section, and the closing `issue-tree.md` gives once nothing is
  open. No reply in between shows it - no bycatch heading or line, no ❓,
  no fix proposed or staged.
- **A CR's table holds what that review turns up**, and every row of the
  session's file about the repo it reviews.
- **A row that comes to bear on the work later leaves the file**, and is
  raised then as part of the work.
- **Numbered `B<n>` across the whole session**, so "add the B2 fix" names
  one. A new item takes the next free number, and one shown again keeps
  its number. After a context summary, numbering goes on from the highest
  `B<n>` still in the context or the file.
- **Shown, never fixed.** Its fix is made only when I ask for it in words
  that name it; `questions.md` says why it never rides inside another
  proposal.

The case that taught it: a gap in a rule the session had already shown
me, put under a bycatch heading below the change it was found beside.

```
❌ ### 🎣 Bycatch
   - **B1.** the new rule covers what a session starts, not state it
     changes ... say "add the B1 fix" to have it staged.
✅ ❓ **Q1** **Extend the rule to state a session changes**: add it?
```

## The bycatch file

**It lives in a scratch directory that outlives the session**, never in a
repo: a `# 🎣 Bycatch` heading over `## ⏳ Still open` and `## 🙅 Set
aside`, each a bycatch table as below, with "None." under one that is
empty. A row I tell you to forget moves to Set aside, and is not shown
again while we work.

## The bycatch table

Two rows per item, under its heading:

| # | What the bycatch is | Findings | Call |
|---|---|---|---|
| **B1** | <what it is, with `file`> | 🟠 1 | <call> |
| | **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | **Fix 🔴🟠:** <the fix> · **Evidence:** <level> · **Size:** <size> · **Difficulty:** <difficulty> | |

- **#** — the row's `B<n>`, in bold, so I answer a row by its number
  instead of describing it back to you.
- **What the bycatch is** — one sentence with the file, so I can tell a
  lying doc from a typo without re-reading anything.
- **Findings** — its colour, from `severity.md`, and a count of one: `🟠 1`.
- **Call** — what you think I should do, as a recommendation I can
  overrule, in the frame of `assessment.md`:
  - **🔧 Add fix** - you recommend fixing it as part of this work. It stays
    a recommendation: the fix is made only when I say so in words that name
    it, never folded into another change or its approval.
  - **⏸ Leave for now** - not in this work, with the reason in a few words:
    out of scope, another owner's file, not worth the cost today.
- **The second row**: the Bycatch Profile is the problem as it sits in the
  work - the Evidence that it is real as described, how much it touches,
  how hard it is to understand - and the Fix Profile under Findings is the
  fix, as `severity.md` gives it. The cell under the call stays empty,
  since a call carries no Evidence; its `#` cell stays empty, which is what
  makes it read as part of the row above.

**Bycatch is a finding, so what has no colour gets no row.** Something with
nothing to fix in the work - a folder a tool left behind, state the harness
keeps for itself, a leftover the session made, a change going live, such as
a running session still holding a hook it loaded before a commit removed
it - is no defect. It is named in a line of prose if at all, never as a
row.

The cases that taught it, a row with no colour and no call, in columns made
up for it, and a row whose only fix was a new session:

```
❌ | **B1** | An empty `.claude/.cc-writes` folder the harness created. | skills/<skill>/hooks/.claude |
✅ no row

❌ | **B1** | A skill's hook entry, loaded before a commit deleted its script, blocks every Read in this session. | ⚪ 1 | ⏸ Leave for now |
   | | ... | **Fix ⚪:** a new session loads the skill without it · ... | |
✅ no row
```
