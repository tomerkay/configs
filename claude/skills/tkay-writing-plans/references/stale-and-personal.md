# Nothing stale, nothing personal

Two rules bind every line written into a repo or a skill - code, a chart, a
config, a doc, a comment, a test.

## Nothing that goes stale silently

**A specific value that the next change invalidates is a landmine, wherever it
is written** - a skill, a README, a `CLAUDE.md`, a design doc, a code comment.
It goes on reading as authoritative and nothing ever tells the reader it
stopped being true. A line number is the obvious case and far from the only
one. This is the volatility half of "one source of truth": that rule bans the
second copy, this one bans the copy that rots.

**A commit body is the exception**, because it describes a diff that is frozen.
An exact count, an old value or a measurement there stays accurate forever, and
naming them precisely is what verifying a commit message asks for. What still
does not belong in one is live state written as though it were permanent:
"this commit removes two policies" is right, "the project has 83 policies" is
not.

**So is the record of an incident** - when it happened and the numbers it
showed - **and a design doc's measurement given as the reason for a
decision**, with the query that reproduces it and no date: each records what
happened or why the decision was taken, not a value in force.

Never write down: a count of things ("all seven", "83 policies", "the eight
scaling jobs"), a point-in-time reading of live state ("currently disabled",
"`enabled: false` as of <date>"), a date stamp attached to a claim, a
measurement or benchmark figure quoted as fact, or a pointer to a line, offset
or position in a file.

**Numbers and snippets as a CONCEPT are fine** - the shape of a query, the
mechanism behind a gotcha, an illustrative threshold, "a day-long rate limit
collapses a flood into roughly one message". What is banned is the exact
current value presented as the truth, when that value is owned somewhere else
and moves. Name the owner instead: the function, the metric, the config key,
the command that answers the question. A reader who can re-derive the number
never needed the copy.

**A deletion is not content.** When something goes away, delete its entry - do
not leave a record of what used to be there and why it went. Git history is
that record, and someone reading to find out what exists should not have to
read past what does not.

**A rejected decision is not a deletion.** A line saying "we tried this, do not
go back to it" belongs in the file: the ban is on describing what no longer
exists, and a conclusion about what not to do still holds. Without it the next
person re-derives the same dead end from the same arguments. In a doc it is
written as the conclusion; in a code comment, as the hazard in the present
tense - never as the story of the attempt.

The test, before you write any specific value: **would this sentence need
editing after a change nobody will connect to this file?** If yes, it does not
go in.

## Nothing personal in a repo

**No dev setup ever goes into a repository - mine or anyone's.** Not a
person's name, not a user label, not a namespace, not a cluster or context
name of ANY cluster, not a node hostname, not a pod IP, not an image tag built
from somebody's branch - not in a manifest, a values file, a script default, a
README, a skill, a code comment, a test fixture or an example. Nothing that is
tracked, in ANY repo, whether I asked you to write it or you are touching it on
the way through a change. Test kits, dev overlays, recorded fixtures and
examples are the usual offenders: they get written against one person's
cluster and committed as if they were general, and the next engineer's run
lands on my node or on nothing, with the manifests looking deployed either
way. The one place a cluster name belongs is the production deploy config that
owns that cluster - a topology file, a values file for one environment - and
nowhere that describes how to develop.

**Anything that names a person or an environment is an install-time input** - a
`--set` flag, an argument the script requires, a variable the doc defines once
at the top. Where a file must carry the key, it carries a placeholder no node
or cluster has, so a forgotten input fails or schedules nothing rather than
landing on somebody else's machine. An example namespace is `$NS` or `<ns>`,
never mine.

**When you find one, remove it in that same change** and say so in one line.
Never carry one into anything new you write.

A commit body that records where a change was verified is the one exception,
for the same reason stale values are allowed there: it describes a frozen fact.
