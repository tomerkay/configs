---
name: tkay-writing-mds
description: Standards for the markdown files that live in a repo or a skill - a repo CLAUDE.md, a README, a design doc, a SKILL.md. Covers where a fact goes (code, skill, CLAUDE.md or README) and the tiebreak, the ban on a doc restating a value or pasting code, what a pointer may target and the one line that may repeat, the two jobs of a CLAUDE.md, the shape of a README, which copy of a skill to edit and how to write one. Use before creating or editing any of them, including a doc touched on the way through a code change.
---

# Writing markdown files

Two rules bind every file below.

**Nothing that goes stale silently.** A specific value the next change
invalidates never gets written down: a count of things, a reading of live
state ("currently disabled"), a date stamped on a claim, a measurement quoted
as fact, a line number or position in a file. Name the owner instead - the
function, the config key, the command that answers the question. The test:
would this sentence need editing after a change nobody will connect to this
file? A commit body is the exception, because the diff it describes is frozen.
A deletion is not content - delete the entry, do not record what used to be
there - but a rejected decision ("tried X, do not go back") stays.

**Nothing personal in a repo.** No person's name, user label, namespace,
cluster or context name, node hostname, pod IP or branch-built image tag in
anything tracked - manifests, values, script defaults, docs, tests, examples.
Anything that names a person or an environment is an install-time input (a
`--set`, a required script argument, a variable defined once at the top), and
where a file must carry the key it carries a placeholder no node or cluster
has. The one exception is the production deploy config that owns a cluster.

## Docs are copies too

This binds every doc. A README, a design doc and a repo `CLAUDE.md` - ANY repo,
whether I asked you to write it or you are touching it on the way through a code
change - never restate a value and never paste code. No "(default 15)", no
example block carrying the current numbers, no table with a Default column, no
function body, no snippet that is wrong after the next edit. Name the key, the
function or the file and point at the one that owns it; describe the pattern, do
not copy it.

## Where a fact goes

Four homes, tried in this order. The first that fits is where the fact is
written, once; every other file that needs it points there.

1. **The code**, when the code can say it: a name, a WHY comment, a `required`
   in a template, the header a generator stamps on its output. A doc never
   says what the code says.
2. **A skill**, when one kind of task needs it. Its body loads only when its
   description matches the task, so a procedure, a convention or an inventory
   for one job costs nothing in every other session. The `CLAUDE.md` names the
   skill and when to load it, and nothing more.
3. **The repo `CLAUDE.md`**, when every session needs it before the first tool
   call. It is loaded whole into every session, so every line is paid for on
   every turn, and the harness warns at startup when it grows past its size
   target. It holds why the code works the way it does, where it bites, and how
   Claude behaves in this repo - see "A repo CLAUDE.md".
4. **The README**, when a human operating the thing needs it: setup, the
   commit or deploy steps, the contract consumers depend on, troubleshooting.

Most "fits both" cases are two facts. The bite is the `CLAUDE.md`'s, the steps
that work around it are the README's, and each points at the other. When one
fact truly fits two homes, the earlier one wins.

**The split is by topic, never by reader.** Claude follows the README when it
commits, and a human opens the `CLAUDE.md` to find the gotcha that just bit
them. A README "for humans" and a `CLAUDE.md` "for Claude" ends with the commit
steps written twice.

**A fact that holds for every consumer lives in the shared doc.** Every team's
directory, every chart a repo deploys: the shared README or `CLAUDE.md` owns
it, and a per-team or per-component doc keeps only what is its own and points
up. A shared fact written in one team's README is a copy by the time the
second team needs it.

**Two docs pointing at each other is not the failure; the same content in
both is.** A pointer each way is fine when each is for a different topic and
following it lands on that topic's one home. So when I ask whether docs are
"circular", audit what each file *states*, not what it links - the duplicate
hides behind the pointers, and it has usually drifted already. Three copies
agreeing today is not a defence - I have had values.yaml, README and
`CLAUDE.md` each state the same defaults, two of them stale, and nobody noticed
because only values.yaml was ever deployed.

A design doc takes its content rules from here.

## A pointer

A pointer names the file and a name inside it that survives an edit - a key, a
function, a flag, a filename, a metric - and stops. "The commit steps are the
root README's" is a pointer. The moment it goes on to say what those steps
are, it is a copy.

A section heading is not a name that survives: markdown has no anchor that
outlives a rename, and nothing tells the pointing file. Point at a heading only
inside a directory one owner edits. Across an ownership boundary - a CODEOWNERS
line, another team's skill - point at the file and the topic, so a
reorganisation on their side strands nothing on yours.

**The one line that may repeat is a warning with no value in it** - "these
three files are generated, never edit them" at every place a reader could
otherwise act wrongly. Nothing in it moves, so it cannot drift. A value, a
list, a snippet or a procedure never repeats.

## A repo CLAUDE.md

Two jobs. **Engineering notes:** why the code works the way it does and where
it bites. **Behaviour:** how Claude works in this repo. Never what the code
does - the code says that - and never how to operate it - that is the README.

The engineering notes carry design decisions and the reason behind them, the
trade-offs, and each gotcha with the mechanism behind it. A flow or an
architecture line earns its place only as the frame for the decision or gotcha
that follows it; on its own it is a retelling of the code, and the harness's
own `/doctor` trims exactly that kind of content from a `CLAUDE.md` while
keeping pitfalls, rationale and conventions.

The behaviour half is instructions: the evidence a reply owes after a commit, a
warning or reply whose wording matters, written verbatim, which skill to load
before which task. Only what every session needs - a protocol for one kind of
task goes in that task's skill.

Name files relative to the repo root, never an absolute path into anyone's
machine. No generic explanation, no tutorial voice ("let's explore", "as you
can see"), nothing the code or its comments already say.

**Example - BAD (code implementation):**
````markdown
## Validation Flow

```python
def validate(pod):
    if pod.status == "Ready":
        return True
    return False
```

This function validates the pod by checking if it's ready...
````

**Example - GOOD (design and architecture):**
````markdown
## Validation Flow

**Design:** Fail-fast at startup, zero defensive checks at runtime.

**Flow:** Health check (fail immediately if unhealthy) → Skip prefill/multi-node
pods → Validate text/audio/vision based on config.

**Key decision:** Separate transient errors (timeouts, network) from validation
failures (wrong output, corrupted response). Only validation failures trigger
blacklisting - prevents pods being blacklisted during temporary infrastructure issues.

**Gotcha:** Multi-node workers skip ALL endpoint validation because leader handles
inference. Only health check runs.
````

The Flow line stays because the Gotcha below it needs it.

**Structure per section:**
1. Problem/context (1 sentence)
2. Design decision or architecture
3. Key insights or trade-offs
4. Gotchas or edge cases

## A README

The reader has a task and has not read the code.

- **The first screen is the common path**: what this is, in a line, then the
  steps most readers came for. Recovery, edge cases and opting in come after,
  never as step one.
- **A procedure is commands the reader runs in order**, with nothing to decide
  in the middle. A decision is a sentence before the block, not a comment
  inside it.
- **What never to do is one list**, each line stating the fact and pointing at
  the file that explains the mechanism.
- **A README below the root keeps only what is that directory's own** and
  points up for the rest.

"Docs are copies too" binds here hardest: a README is where a setup snippet
gets pasted and then forgotten. Name the file and the key, and give the command
that reads it.

## A SKILL.md

**Edit a skill at its source.** Every other copy is overwritten on its next
update, so an edit there is either lost or lives just long enough to diverge.

- **A plugin skill** is edited in the repo that publishes the plugin. The
  marketplace checkout and the plugin cache under `~/.claude/plugins` are build
  artifacts, and a copy of the skill under any other repo's `.claude/skills` is
  drift to delete, not a source.
- **A public skill** installed from an upstream belongs to that upstream. Do
  not edit it.

**A skill name** is lowercase letters, digits and hyphens only, which is all the
[Agent Skills spec](https://agentskills.io/specification) allows.

**The description is the only part loaded in every session**, so it says when
to load the skill, not what is in it. The body is read only after the
description matched.

**A skill never records the current state of something it doesn't control** - a
dead alert, a blank field, an unfixed bug, a lagging deploy. Somebody fixes it
without ever opening the skill, and from that day the skill states a false fact
with nothing to show it went wrong; the defect belongs in a ticket. **A
workaround the procedure depends on stays, but names its trigger and its
expiry**: the upstream issue or version it waits on, and the check that shows it
still applies.
