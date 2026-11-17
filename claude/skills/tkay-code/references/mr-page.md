# MR Titles and Descriptions

**A repo that documents its own MR title or description template overrides
the format here.** See "The repo's conventions win" in `SKILL.md`. Keep the
spirit below inside its sections.

**Pushing the branch and opening the MR are mine.** Never offer or suggest
either. Never run a push; open the MR only when I ask for it in so many
words. A title and a description are written only when I ask for one.

**The title and the description are one piece of work.** A request for
either one is a request for both. Write them together, and write them to the
MR together. They are two parts of one summary for the same reader, so a
title updated alone describes a different MR than the description under it.

## Finding the MR

Look it up by the current branch - `glab mr list --source-branch <branch>` on
GitLab, `gh pr list --head <branch>` on GitHub. The glab TLS fix in
`references/gitlab.md` applies.

**No MR found: ask me for its link** and wait. Never open one to have
somewhere to write, and never guess between several.

## The title

**One line that says what the whole branch does**, in the repo's style for a
commit subject: what a reviewer reads in a list of MRs before opening one.

- **Never the subject of the first commit.** GitLab and GitHub fill the
  title from it when an MR is opened, and on a branch of several commits it
  names one of them. Write it again for the whole MR.
- **Keep the `Draft:` prefix while the MR is a draft.** It is the MR's
  state, not part of the wording.

The case that taught it, a branch of seventeen commits opened as a draft:

```
❌ Draft: Refuse an operator pin on a managed self-serve endpoint
✅ Draft: Manage a self-serve endpoint's replicas through the self-serve API
```

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

**The title and the description describe what the remote holds, so the push
is checked first.** Before writing or updating them, compare the branch's
remote tip with local HEAD - `git ls-remote origin refs/heads/<branch>`
against `git rev-parse HEAD`. When they differ, the MR still shows the old
commits, and text written now describes work it does not have: stop and
tell me the remote is behind HEAD. The push is mine, so it is not offered
or asked about. Nothing is written until the remote tip matches HEAD.

My request for a title or a description is the ask `references/gitlab.md`
requires before a write to the MR, so do not ask again: show me both texts
and write them in one call from a file, with `glab mr update <iid> --title
"<title>" --description-file <file>` (`gh pr edit <n> --title "<title>"
--body-file <file>` on GitHub). **What the MR already has is not
overwritten without asking**: show me its current title and description
next to the new ones and let me choose. A title that GitLab or GitHub
filled in from the first commit is not one of those: replace it without
asking. Finish with the MR link.
