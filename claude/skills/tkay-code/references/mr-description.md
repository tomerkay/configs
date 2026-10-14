# MR Descriptions

**A repo that documents its own MR description template overrides the format
here.** See "The repo's conventions win" in `SKILL.md`. Keep the spirit below
inside its sections.

**Pushing the branch and opening the MR are mine.** Never offer, suggest or
do either unless I ask for it in so many words. A description is written
only after I said yes to one.

## Finding the MR

Look it up by the current branch - `glab mr list --source-branch <branch>` on
GitLab, `gh pr list --head <branch>` on GitHub. The glab TLS fix in
`references/gitlab.md` applies.

**No MR found: ask me for its link** and wait. Never open one to have
somewhere to write, and never guess between several.

## The description

**Human readable, concise and simple.** The reader is a reviewer who never saw
the work and has two minutes.

- **Open with what changes and why**, in one to three plain sentences. No
  heading is needed for a description that fits in a paragraph.
- **Then only what the reviewer needs**: what to look at closely, how it was
  verified, anything a consumer must do or will notice - a renamed key, a
  metric whose meaning changed. Short bullets, each one line where possible.
- **Plain words.** Explain an internal term in a few words or leave it out.
- **No retelling of the commits and no file list** - the MR shows both.
- **If it scrolls, cut it.**

The commit messages are input, not a template: read them for the why, then
write it once for the whole MR.

## Writing it

My yes to a description is the ask `references/gitlab.md` requires before a
write to the MR, so do not ask again: show me the text and write it from a
file with `glab mr update <iid> --description-file <file>` (`gh pr edit <n>
--body-file <file>` on GitHub). **An MR that already has a description is
not overwritten without asking**: show me the current one next to the new one
and let me choose. Finish with the MR link.
