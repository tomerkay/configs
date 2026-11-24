# Doc review

A doc review judges a change to markdown that instructs or documents - a
`CLAUDE.md`, a README, a design doc, a `SKILL.md`, a skill's reference - on
a branch or staged for one.

**It is the CR with one cut, and nothing added**: everything
`code-review.md` gives, but for every section "The CR's sections" tags
*judges running code*, and the rules that judge only code -
`clean-code.md` and `security.md`, which a doc review does not read. Every
other section, the doc checks of "Docs in the change" and the Summary with
its section calls included, is written as `code-review.md` gives it, so a
section the CR gains or loses is gained or lost here too.

## Markdown only, or it is a CR

**A doc review is for a change that touches markdown alone.** A change that
touches anything that runs - code, a script, a hook, a config or settings
file, a `SKILL.md` frontmatter line that registers a hook or a tool - gets a
CR, whole: one change gets one review, the heavier one, so code never passes
under a doc review. A doc review is written when I ask for one by that name,
or when a repo's own procedure names it; a CR I ask for is a CR, whatever
the branch holds.

## Its title and its findings

**Its title names the repo and the branch**, `# Repo <repo> branch
<branch> doc review`, the repo named as `code-review.md` names it in a CR's
title. A staged diff stands in for its commit. Its findings come from the
doc checks and the commit checks of `code-review.md`, since the rules the cut leaves out are
not read.
