# The shape of a full plan

## The problem comes first. Always.

**Open with what is broken, in plain language.** Not the branch, not commit hashes, not
what you verified, not caveats about your method. I cannot evaluate any of that before I
know what we are fixing, and if I have to scroll to find the problem, the document has
failed no matter how correct it is.

Structure:

1. What the thing does and what is broken - a few lines
2. **Goals and non-goals** - see below
3. **Glossary** - every term the plan gives a specific meaning, one line each, so a
   word means one thing from the first section to the last. Terms that a reader of the
   code would mix up go here first: two layers with similar names, a count that has
   two sources, a word the codebase uses loosely.
4. One section per problem, with the evidence for it
5. **The contract: the API, the constraints and invariants, the black-box tests** -
   the most important section of the plan, see below
6. The fix, opening with the known architecture it follows, giving the design
   note of each new responsibility, and saying what an auditor would find in it, how it
   survives a failure, and how it is watched, rolled out and turned off - see
   below
7. **Known incidents** - see below
8. The commits
9. **Questions and answers** - see below
10. **TBD** - see below
11. **A divider, then reference material** - how to reproduce the numbers, decisions
    already settled, branch state, things found but not chased

Anything I would read once goes below the divider. Say at the top which sections are the
plan and which are reference, so I know where to stop.

## Goals and non-goals

**The plan says what it sets out to achieve, and what it leaves out on purpose.** A
goal is an outcome a reader can check once the work ships, never a step of the work. A
non-goal is something a reader could reasonably expect this plan to do and that it
deliberately does not - in the words of
[Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/),
"non-goals aren't negated goals". Each non-goal says why in a few words. The
brainstorm's in-scope and out-of-scope items land here.

**Each goal names the check that proves it**: a black-box test of the contract, named
as the contract names it, or, when no test can, the run or the read that shows it. A
goal with no check is written as unchecked, never left silent. A goal only production
can confirm takes as its check what shows it before the merge - a test or a run of
the mechanism - and what confirms it after it ships is the answer to "How do we know
it works?" under "Check operability".

A non-goal is not deferred work: work I agreed to do later is TBD's, and a non-goal
is not planned at all.

## The contract is the most important section

**The API, the constraints and invariants, and the black-box tests are the
component's interface: what it stands for to everyone outside it.** A reader who
reads only this section knows what the component promises and why they can rely on
it, whatever the code inside looks like. Everything else in the plan is how that
promise is kept. It is never folded into the fix, never below the divider, and
never left for the code to tell.

Three parts, each its own subsection:

- **The API**: every way in and out that someone outside depends on - an
  endpoint, a function, a CLI, a CRD, a message, a metric another team alerts on.
  For each, its inputs, its outputs and its errors. What this plan adds, changes
  or removes is marked as such, and a breaking change is named as breaking.
- **Constraints and invariants**: what is always true, stated as a property, never
  as one example - "at most one replica writes the scaling decision", "a request
  never reaches a pod outside its tenant", "every failure reason is counted from
  zero". Constraints sit beside them: limits, ordering, idempotency, timing bounds.
  Each one names what enforces it - a type, a check at the boundary, a test.
- **The black-box tests**: the tests that pin the contract through the public
  interface alone - an input, and what a caller observes. Every API behaviour and
  every invariant names the test that pins it, by a name that states the
  behaviour. One with no test is written as unpinned, never left silent. They
  cover the failures the API promises, not only its happy behaviours. How a test
  reaches a failure path - a fake that fails at the boundary, a failpoint compiled
  out of production, faults at the network or process level, deterministic
  simulation - depends on the language and the component, so the plan lays out
  the ones that fit, with their cost here, and the choice is mine.

**The contract is written and agreed before the internals.** A design that cannot
state its invariants is not ready to be designed further, and the tests can be
written from this section before any code exists. Once agreed, a change to it is
a decision of mine like any other.

## Start from a known architecture

**The idiomatic architecture is the core motivation of every design discussion.** A
design is chosen from known architectures out in the world, not invented: a pattern
of a mature system, a documented controller or protocol, the way a well-known
project handles the same failure. Inventing a mechanism is a cost the plan has to
justify; following a known one hands the reader its documentation, its failure modes
and its track record.

**Without it, the design is built from the symptom outward.** Each hole found gets
its own patch, each patch opens the next hole, and the result is a hand-made copy of
a mechanism some mature system already ships - with none of its documentation and
all of its early bugs. Starting from the architecture means understanding the whole
problem before the first decision, so every later decision is placed in a design
that already has a place for it. Proper preparation and planning prevent piss poor
performance.

**Search first, then discuss it with me, before the design is written.** Look
outward - the documentation and source of the systems that solved the same problem,
not only this codebase - and bring me what you found:

- **The candidates**: each known architecture that is relevant, with a link, and how
  it matches and does not match our needs.
- **Which one you recommend**, and why it suits us better than the others.
- **When none is relevant, say so** and say what you searched, so I can point you
  at one you missed. Never present an invented design as if no search were needed.

The choice of architecture is mine, like any other decision in the plan. Every later
question in the discussion - a race, a failure mode, a limit - is argued from that
reference first: what it does in the same case, and whether we follow it.

Once it is chosen, the plan carries it:

- **The fix opens by naming it**: "this follows X, because it suits us in A and B",
  with a link to where X is documented - or, when none fit, the ones considered.
- **Every decision names the design it resembles and the approach it rejected**:
  "Z resembles X's design; over W it gives <advantage>, and it costs
  <disadvantage>." In a decision table, that sentence is the reason column.
- **Every new responsibility gets its design note**, in the shape
  `design-note.md`, beside this file, gives - its owner, its state, its
  interface and its departures - under the fix: "the decision to retry lives in
  the router, not in each handler: the router already owns pod choice".
- **A departure from the reference is stated where it happens**, with why: a state
  the reference keeps reversible that this design makes final, a check it runs that
  this one skips.
- **The same holds for a decision taken while implementing** (see "Executing a
  plan"): a fix that changes the design names the known design it moves toward.

## Check security

**Read the design as an outside auditor would.** Ask every question in
`references/security.md` of the design and of the component it lands in,
and write each answer into the fix - "not exposed, because <reason>"
included.

## Check high availability

**Read the design as the on-call engineer would on the night a piece of it dies.**
A plan that says nothing about failure reads as one that never asked. Ask these of
the design and of the component it lands in, and write each answer into the fix -
"not needed, because <reason>" included:

- **What happens when one replica, pod or node dies?** Whether the work stops,
  slows down or carries on elsewhere, and what brings it back.
- **Is there a single point of failure?** One replica, one node, one zone, or one
  dependency every request goes through.
- **What happens when a dependency is down or slow** - the database, the API it
  calls, the cluster it reads? Whether the component fails, serves stale data or
  hangs.
- **Is the state safe when a process dies mid-step?** Whether a restart redoes the
  step safely or finds a half-done write.
- **Does any result rest on two writes that cannot commit together?** Two
  stores, or a row and a cluster object, behind one result. The plan splits
  what need not hold together, puts what must into one transaction of one
  store or records the intent and reconciles it across systems, and names
  any rollback it cannot avoid.
- **Does a rollout or a node drain keep it serving?** More than one replica, a
  PodDisruptionBudget, readiness that gates traffic.

### A leader for work that must run once

**Replicas give availability; a leader keeps work that must run once from running
on every replica.** A reconcile loop, a scaling decision, a scheduled job, anything
that writes shared state from a loop: give it more than one replica and every
replica acts. Kubernetes runs its own controller manager and scheduler this way -
one instance holds a [Lease](https://kubernetes.io/docs/concepts/architecture/leases/)
and acts, the others stand by. Wherever the design has such work, the plan says:

- **Which mechanism elects the leader**: a Lease through client-go's
  [leaderelection](https://pkg.go.dev/k8s.io/client-go/tools/leaderelection) or
  its equivalent in the component's language, never a hand-made lock.
- **What happens when two replicas both act as leader.** Election is not fencing:
  client-go's own docs say it "does not guarantee that only one client is acting
  as a leader", and a paused process can wake up still believing it leads. The
  writes are idempotent, carry a [fencing
  token](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)
  the store checks, or the leader stops acting the moment it loses the lease.
- **How long the work stands still when the leader dies**, named by the setting
  that bounds it - the lease duration - and whether that gap is acceptable.
- **When one replica is enough**: the work tolerates the gap a restart leaves.
  Then say so and leave the election out - it is a mechanism to justify like any
  other.

## Check operability

**Read the design as the engineer who rolls it out and has to tell whether it
works.** These are the questions Kubernetes asks in its
[production readiness review](https://github.com/kubernetes/community/blob/master/sig-architecture/production-readiness.md):
whether a change is observable and supportable, and whether it can be disabled or
rolled back. Ask them of the design and of the component it lands in, and write each
answer into the fix - "not needed, because <reason>" included:

- **How do we know it works?** The metric, log line or alert that shows it doing its
  job, and the one that shows it failing - never only that the process is up.
- **How does it reach production?** All at once, behind a flag, or one instance or
  one region first - and what is watched before the next step.
- **How is it turned off?** A flag, a config value or a rollback to the previous
  release, and whether turning it off takes a deploy.
- **What does a rollback leave behind?** State, a schema, a wire format or a stored
  object the old version cannot read, and what keeps the old and new versions
  working side by side during a rollout.

## Known incidents, each with a status

When the plan replaces, rewrites or fixes something that has failed before, it lists
every incident it knows about - from the code's comments and tests, the rules a team
wrote after an outage, commit bodies, postmortems, tickets - and says what the change
does to each. The section is there whether the change is a redesign, a feature or a
bug fix; an incident the plan never names is one the reader assumes it handles.

**The section opens with a summary table**: one row per incident, numbered in bold, with
the incident, its status, and in one line how it is fixed or why it is not. A
reader sees the state of every incident before reading any of them.

**Then one block per incident, in a fixed shape, its heading carrying the status**,
so the answer is never buried in a paragraph:

- **The status**, one word, in the heading: **Solved** (the cause cannot occur by
  construction), **Mitigated** (it can still occur and is handled another way),
  **Not solved** (it can still occur and nothing new handles it), or **Gone** (the
  mechanism that failed no longer exists). No other word.
- **What happened**: the symptom, with the numbers, the date and the system when the
  source has them. A detail the source does not state is written as not stated, never
  filled in.
- **Cause**, in the old code.
- **Fix**: the mechanism in the new code, naming the function, the rule or the
  section that carries it, and the test that pins it. For **Not solved**, this line
  is **Why not**: what still lets it happen, and what covers it meanwhile - a TBD
  entry, a known gap, an operator action. For **Gone**, it names the mechanism that
  no longer exists.
- **Source**: the file and the function or test, or the commit subject.

**A status is a claim about the new code, so it is checked against the new code, not
taken from the plan's own prose.** Solved without a named mechanism is not a status
it may claim.
A not solved is written as plainly as a solved: it is the entry the reviewer most needs,
and it pairs with a TBD entry that I agreed to.

## TBD holds only what we agreed to defer

The TBD section lists work I agreed, with you, to leave out of this plan: a follow-up,
a cleanup after it ships, a decision we postponed on purpose. Each entry says what and
when or why later.

**An entry is deferred work the plan does not depend on.** With the entry undone, every
claim in the plan stays true: the contract holds, each commit leaves the tests passing,
each incident keeps its status. When I ask to defer something the plan depends on, that
is not a deferral but a cut, and a cut changes what the plan claims. Say what it
changes - the invariant that goes unpinned, the incident that turns Not solved, the
commit that no longer stands on its own - and ask whether I want the cut. If I do, the
sections it touches say so, and the TBD entry names what the plan now lacks.

**Never add a TBD entry on your own.** Something you find that this plan does not do is
a finding: it goes below the divider, and you raise it with me. It moves to TBD only
after I agree to defer it. A TBD you invented reads as a commitment I never made.

**Nothing raised or found falls out of the plan unasked.** Along the way, keep what
landed nowhere: an item of the brainstorm no section carries, a thing I raised and never
settled, something you found and we did not chase. A finding that changes what we want
is raised the moment it is found, as a hole found while implementing is. Everything
else is floated once, before the full plan is written: a numbered list in chat, each
number in bold as in the brainstorm, one line per item with why it matters, and for each I pick its bucket - in scope, a non-goal, TBD, or
a rejected decision below the divider. Only then is the plan written, with every item
in its bucket.

## Divide it into commits

**Read the code each commit will touch before cutting the list**, so a
refactor it needs is found while planning, not while executing.

Not a pile of edits. **Read `references/commits.md` before the first commit
section**, and write one section per commit, cut and ordered as its section
"Two Suits: a Fix Stands Alone, a Feature Is a Series" says. For each one: the subject
line, the files, the tests, and **what the commit body has to say**. Each black-box
test of the contract, and each goal's check, is listed under the commit section that
delivers what it pins or proves. A goal whose check no commit section lists means the
list is not done.

Call out whatever a commit touches that is easy to miss: a doc whose wording it
invalidates, a rule it deliberately reverses, a config list it has to join.

## End the plan with questions and answers

A design plan gets read by people who were not in the review: the component's owner,
the reviewer, the next engineer. Before the divider, add a "Questions and answers"
section with the questions the review raised and the ones those readers will ask -
why not the obvious alternative, what happens in a race, what breaks in the next
planned feature. Group them by topic. Answer each in a few sentences with a concrete
example where one helps, and point to the section that holds the detail.

**A question belongs here only if a design reviewer would ask it.** Judge each one
yourself, from the questions I ask during the review and from the decisions taken
while executing, and never ask me whether to add one. The test: would someone reading
the plan cold, who was not in the discussion, ask it and be better off for the
answer? A decision's "why this and not the obvious alternative", a race, a failure
mode and a limit pass. A question I asked only to understand something for myself,
or one whose answer is common knowledge, stays out.

Answer with the current plan, never with how we got there: a question whose answer
changed the plan is answered as the plan now stands.

## Every line is for a human reader

A plan is read by a person who wants to know what is broken, what we will do and why.
A line that does not help them with that is noise, and noise buries the lines that
matter. Cut it:

- **Dates and timestamps** - "as of", "verified on", "last updated", a date heading a
  section. A date says when a sentence was typed, not whether it is still true. Keep
  one only when the date is itself the fact: when an incident happened, a deadline,
  the window a measurement covers.
- **The plan's own history** - "v2", "updated after review", "this section used to
  say". The plan describes the design as it stands; how it got there is the commit
  bodies' and the chat's.
- **Narration of the work** - "I checked", "as discussed", "per your request", "after
  reading the code". State the finding. A method worth keeping is a reproduction
  recipe, and it goes below the divider.
- **Machine coordinates** - an absolute path into someone's machine, a scratch path,
  a line number. Name the file relative to the repo and the function in it.
- **Raw output** - a pasted log, a whole command output, a dumped config. Quote the
  line that proves the point and give the command that produces the rest.

The test: would a reader who was not in the session lose anything if the line were
gone? If not, cut it.

## Rules that keep a plan usable

- **No `§`.** Write "Section 4". Same for any notation I have to stop and decode.
- **Cite commits by subject line, never by hash.** I rebase constantly - every hash in a
  plan goes stale within a day. Give me `git log --oneline --grep '<subject>'` instead.
- **Every number must be reproducible.** Put the exact query beside it and name the data
  source. A number I cannot re-derive is one I cannot trust a week later.
- **Measurement windows expire.** Say so, and give the recipe for picking a fresh one.
- **Say what is not a problem.** If you checked something and it is fine, write that down
  so I stop wondering about it.
- **Name the decisions that are mine** and ask them.
- **Flag what rests on an inference rather than a measurement**, say what would falsify
  it, and if a cheap check exists, make it a step in the plan. Do not let a chain of
  reasoning quietly become a stated fact - I will press on exactly that.
