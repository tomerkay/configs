# Doc review

A doc review judges a change to markdown that instructs or documents - a
`CLAUDE.md`, a README, a design doc, a `SKILL.md`, a skill's reference - on
a branch or staged for one. It is the doc's version of a code review: the
same colours, the same findings, and a call that ends it, held to the
writing standards instead of the code ones.

`writing-mds.md` and `copied-stale-and-personal.md`, beside this file, are
the standards the change is held to. The colours, the 🧪 UNTESTED finding,
the FINDINGS line, the MUST HAVE and NICE TO HAVE sections, the commit
calls, the bycatch table and "Rules that keep the tags honest" are
`code-review.md`'s, and hold here as written there; this file says what
changes when the thing judged is a doc instead of code.

## Markdown only, or it is a CR

**A doc review is for a change that touches markdown alone.** A change that
touches anything that runs - code, a script, a hook, a config or settings
file, a `SKILL.md` frontmatter line that registers a hook or a tool - gets a
CR, whole: one change gets one review, the heavier one, so code never passes
under a doc review. A doc review is written when I ask for one by that name,
or when a repo's own procedure names it; a CR I ask for is a CR, whatever
the branch holds.

## A cold read

**The reviewer reads the diff against the whole file it lands in, and against
every file that speaks of the same thing, never the conversation that
produced it.** A doc is read by people and sessions that were not there. A
line that only makes sense to someone who was is a finding.

## What is checked

Each check is run before the first finding, and the review names the command
or the read that ran it:

1. **Each fact sits in its one home**, by the homes `writing-mds.md` gives,
   and reads there as that kind of file should.
2. **Nothing copied, nothing stale, nothing personal**: the rules of
   `copied-stale-and-personal.md`, asked of every line the diff adds.
3. **Every place that names what the diff renames, moves or removes is
   changed with it**: searched across the repo, and across the whole catalog
   for a skill.
4. **Every pointer the diff adds or touches lands**: the file exists, and so
   does the name inside it.
5. **No rule is stated twice, and none contradicts another**: the rules
   beside it in the file, and the ones on the same topic in every file that
   loads with it.
6. **A command or an example a reader would run is run or rendered**, as a
   commit's runtime claims are.
7. **The commit message matches the diff**, by `commits.md`.

## What each colour means in a doc

| Tag | In a doc |
|-----|----------|
| 🔴 **BUG** | A reader who follows it does the wrong thing, in a case you can state: a command that fails or hits the wrong target as written, two rules that cannot both be kept. |
| 🟠 **RISK** | The trigger for harm can be named: a pointer that lands nowhere, a rule that leaves open a case it claims to cover, a thing still named the old way where a reader acts on the name, something personal in a tracked file. |
| 🟡 **QUALITY** | It reads right and costs upkeep: a rule or a value written twice, a value that goes stale, a fact in the wrong home, a line for nobody. |
| ⚪ **NIT** | Wording, ordering, formatting. |

## The shape of a doc review

Under a title that names the repo and the branch, `# Repo <repo> branch
<branch> doc review`, the repo named as `code-review.md` names it in a CR's
title, these sections and the ending:

1. `# Commits` - `## In short` and `## In detail`, as `code-review.md` gives
   them: every commit in one line, then every commit's review. A staged diff
   stands in for its commit.
2. `# 🎣 Bycatch` - the table `code-review.md` gives.
3. The ending - the branch call, then the line naming the review's file,
   last, as a CR's ending puts it. It
   has no section calls: its commits are its one section of calls. With no
   To do, the call's bracket names the commits that hold it.

**The branch call follows the commits**, by the rule `code-review.md` gives
a change's call under "The call follows the commits it names", read with
the branch's calls for the change's: ✅ Merge it, 🧪 Merge after tests,
🙋 Merge after your call, 🔧 Merge after fixes. A doc that should not go in
at all is ❌ Don't merge.
