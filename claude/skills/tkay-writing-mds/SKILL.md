---
name: tkay-writing-mds
description: Tomer's standards for the markdown files that live in a repo or a skill - a repo CLAUDE.md, a README, a design doc, a SKILL.md. Covers which file owns what, the ban on a doc restating a value or pasting code, the shape of a good CLAUDE.md, which copy of a skill to edit and how to name a new one. Use before creating or editing any of them, including a doc touched on the way through a code change.
---

# Writing markdown files

"Nothing that goes stale silently" and "Nothing personal in a repo" in my global
CLAUDE.md bind every file below and are not repeated here.

## Docs are copies too

This binds every doc. A README, a design doc and a repo `CLAUDE.md` - ANY repo,
whether I asked you to write it or you are touching it on the way through a code
change - never restate a value and never paste code. No "(default 15)", no
example block carrying the current numbers, no table with a Default column, no
function body, no snippet that is wrong after the next edit. Name the key, the
function or the file and point at the one that owns it; describe the pattern, do
not copy it.

## Each file has one job

values.yaml is what can be set and what it means, and earns that with a comment
on every key; the repo `CLAUDE.md` is why it works that way and where it bites;
the README is how to operate it - deploy, the contract consumers depend on,
troubleshooting. Anything that fits two of them is written in one and pointed at
from the other. Three copies agreeing today is not a defence - I have had
values.yaml, README and CLAUDE.md each state the same defaults, two of them
stale, and nobody noticed because only values.yaml was ever deployed.

**Two docs pointing at each other is not the failure; the same content in
both is.** A pointer each way is fine when each is for a different topic and
following it lands on that topic's one home. So when I ask whether docs are
"circular", audit what each file *states*, not what it links - the duplicate
hides behind the pointers, and it has usually drifted already. A pointer names
the home and stops; the moment it summarises what it points at, it is a copy.

**A fact that holds for every consumer lives in the shared doc.** Every team's
directory, every chart a repo deploys: the shared README or `CLAUDE.md` owns
it, and a per-team or per-component doc keeps only what is its own and points
up. A shared fact written in one team's README is a copy by the time the
second team needs it.

## A repo CLAUDE.md

Why the code works the way it does and where it bites. Never what the code
does - the code says that - and never how to use it - that is the README.

**DO:**
- Document design decisions and WHY they were made
- Explain architecture patterns and how components interact
- Capture non-obvious behaviors, gotchas, edge cases
- Describe algorithms/flows at a high level
- Note important configuration patterns
- Name the trade-offs made, and why
- Keep it concise - engineering notes, not essays

**DON'T:**
- Write an absolute path into anyone's machine - name files relative to the repo root
- Be verbose with generic explanations
- Repeat information obvious from code/comments
- Use tutorial language ("let's explore", "as you can see")

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

**Structure per section:**
1. Problem/context (1 sentence)
2. Design decision or architecture
3. Key insights or trade-offs
4. Gotchas or edge cases

## A SKILL.md

**Edit a skill at its source.** Every other copy is overwritten on its next
update, so an edit there is either lost or lives just long enough to diverge.

- **A plugin skill** is edited in the repo that publishes the plugin. The
  marketplace checkout and the plugin cache under `~/.claude/plugins` are build
  artifacts. `atero-skills:investigate-alert` lives in
  `~/repos/atero-skills/.claude/skills/investigate-alert/SKILL.md`, the only
  copy the team edits; a copy under any other repo's `.claude/skills` is drift
  to delete, not a source.
- **A public skill** - a symlink into `~/.agents/skills`, or a directory named
  in `~/.agents/.skill-lock.json` - belongs to its upstream. Do not edit it.
- **My own skills** are edited under `~/.claude/skills`.
  `~/repos/configs/claude/skills` is a copy the configs sync overwrites.

**A skill I own is named `tkay-<topic>`**: lowercase letters, digits and hyphens
only, which is all the [Agent Skills spec](https://agentskills.io/specification)
allows, and the prefix keeps it from reading as an installed public skill.

**A skill never records the current state of something it doesn't control** - a
dead alert, a blank field, an unfixed bug, a lagging deploy. Somebody fixes it
without ever opening the skill, and from that day the skill states a false fact
with nothing to show it went wrong; the defect belongs in a ticket. **A
workaround the procedure depends on stays, but names its trigger and its
expiry**: the upstream issue or version it waits on, and the check that shows it
still applies.

**The `LFG!` gate is mine alone.** It lives in my global CLAUDE.md, and nobody
else works under it. A skill anyone else loads - one in a repo, a plugin or a
team catalog - never names it: write "the user's go-ahead" or "approval to make
changes" instead.
