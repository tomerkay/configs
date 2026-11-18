# What only my setup blocks

These are the steps to look for:

- a write the sandbox denies - its config, shown at session start, lists the
  protected paths, `~/.claude/hooks` and the settings among them; my root
  `CLAUDE.md`, the `tkay-*` skills, the hooks and the published home files
  are the exception, each installed by the staged-change procedure of
  `~/.claude/.claude/CLAUDE.md`;
- an edit auto mode refuses as self-modification - the settings, the
  permission rules, and a hook by any route other than the `cp` its install
  rule names;
- a history rewrite below HEAD, which needs my words in any case - see
  "Some commands need my words and the prompt, every time" - and which auto
  mode judges by the command's text, not its effect: the plain
  sequence-editor shape in `branches.md`'s rewrite section, run as its own
  call with nothing chained to it, has passed where a rebase bundled with
  other mutations, or driven by a script that deletes `pick` lines, was
  refused as destructive. A fix to HEAD is an amend and needs none of this;
  when a rewrite I allowed does arise, shape it the plain way first, and a
  refusal of that shape is then mine.

What I am to apply is staged in the session's handoff directory - "Every
file you write goes under ~/.cache/claude-handoff" says why there and when
it is cleared.
