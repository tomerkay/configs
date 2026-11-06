# Clean code: the rules and the worked examples behind them

These rules apply to every line of code, chart, dashboard or config written for
me. Read this file before writing code, before the first finding of a code
review, and again whenever you are unsure whether a specific comment,
mechanism, default or config key is acceptable.

---

# SECURITY: WHAT WOULD AN AUDITOR WRITE ABOUT THIS?

**Read every component as an outside auditor, a security researcher or an
analyst writing about the company would - when writing it and when reviewing
it.** Anything they could write down that makes us look careless is a
finding, whether or not anyone has exploited it. The company is judged on what
that report says, not on whether the hole was ever used.

Ask these of every change, and of the component it lands in:

- **Does anything cross a network in plaintext?** HTTP where HTTPS exists, an
  insecure gRPC channel, TLS verification switched off (`verify=False`,
  `InsecureSkipVerify`, `curl -k`). Inside the cluster counts too: "it is an
  internal network" is the first line such a report quotes.
- **Can a secret leak?** A token, key or password in source, a values file, an
  image layer, a URL or query string, a log line, an error message, a metric
  label or a startup dump of the environment. A secret comes from a secret
  store at run time and is never printed.
- **Does customer data go where the customer did not send it?** Prompts,
  completions, request bodies or user identifiers in logs, traces, metrics,
  crash dumps or a third-party service. Log a request's ID and shape, never
  its content.
- **Can one tenant reach another?** A shared cache, queue, volume or namespace
  through which one customer's data or traffic reaches another's, or a lookup
  keyed on something the caller controls.
- **Is every endpoint authenticated, and reachable only by who needs it?** An
  admin, debug, metrics or profiling endpoint exposed past its users, a
  default credential, a firewall rule open to `0.0.0.0/0`, a LoadBalancer
  where a ClusterIP would do.
- **Does it run with more than it needs?** Root in the container,
  `privileged`, `hostNetwork`, a wildcard RBAC rule, a cloud role broader than
  its one job.
- **Can input reach a shell, a query or a path?** A shell command, SQL, file
  path or template built from anything the caller sends.
- **Is what it pulls in trusted?** An unpinned image or dependency, a
  `curl | sh`, a package from an unknown source, a dependency with a known
  CVE, home-grown crypto, MD5 or SHA-1 used for security.

**Closing one of these exposures is not over-engineering.** It passes the
"What breaks in production TODAY" test in "OVER-ENGINEERING": the scenario is
the report that names it. A control for an exposure nobody can reach still
fails that test.

**An exposure found on the way is always reported**, never left unmentioned
because the change at hand did not cause it.

---

# COMMENTS IN CODE

**A comment that states the obvious, or repeats what the code or the log
already says, is noise.** Every needless comment costs the reader time; the
log message, the function name or the variable name carries the intent.

Comments that go:
- `# Validate config: gateway requires management URL` right before code that logs "GATEWAY_ENABLED=true but GATEWAY_MANAGEMENT_URL is empty"
- `# Check if pod is ready` right before `if pod.status == "Ready":`
- `# Loop through results` right before `for result in results:`
- `# Return the value` right before `return value`
- `# Set flag to false` right before `flag = False`
- `# healthPath validation (exists when checkHealth is true after merge)` - states the obvious about code structure
- `# Get configured text endpoint path (default: /v1/chat/completions)` right before `text_path = model_config["textPath"]`
- `# textPrompts required when checkText is true` right before validating textPrompts
- `# Validate each prompt item has required fields` right before a loop that validates prompt items
- `# Cross-validation: checkHealth: false + healthCheckOnly: true is contradictory` right before error saying "checkHealth: false and healthCheckOnly: true is contradictory"
- `# Failed - log error and fail immediately` right before logging error and returning False
- `# Auto-correct short form` right before code that auto-corrects and logs "auto-corrected X to Y"
- Any comment that duplicates what an error message, log line, or function name already says
- Any comment that describes WHAT the next line does instead of WHY
- Section header comments like `# Step 1:`, `# Step 2:` unless the steps are non-obvious and need context

**The comments that stay:**
1. **WHY comments**: Explain non-obvious reasoning, design decisions, or business logic
   - Example: `# Use cached state on FETCH_ERROR to avoid marking all pods as healthy during transient gateway issues`
2. **GOTCHA comments**: Warn about subtle bugs or edge cases
   - Example: `# IMPORTANT: must call record_metric BEFORE logging to ensure metrics are recorded even if logging fails`
3. **TODO/FIXME with ticket reference**: `# TODO(JIRA-123): Optimize this query`

**A doubt resolves toward deleting the comment.** If the code is unclear, improve the code (better naming, structure) rather than add a comment.

## CONVERSATION ARTIFACTS STAY OUT OF THE CODE

**A comment must make sense to someone who reads the file cold, having never seen our discussion.** If a comment only exists because of something that happened in our conversation — a code review finding, a rejected alternative, a bug I introduced and fixed, a design I argued for — it does NOT belong in the code. Answer me in chat; leave the file clean.

**What goes — arguing a case, defending a choice, or narrating history:**
- `# Named rather than a bare tuple because three of the five are int/float: transposing the epoch count with the idle seconds would type-check and quietly report...` — defending a design against an alternative that was never in the file
- `# Fixed rather than configurable: nothing has asked to tune it` — justifying a decision to a reviewer
- `# Gated here rather than relying on X, which happens to be true today but is a coincidence` — arguing against a rejected approach
- `# so they cannot drift apart the way three parallel lists could` — referencing code that no longer exists
- `# without this, a skipped write would still log as published` — describing the bug I just fixed
- Anything containing "rather than", "instead of", "we could have", "previously", "this used to", "deliberately not", or a justification for why the code isn't something else

**The test:** delete every trace of our conversation from your memory, then read the comment. If it now reads as a defence of a decision, or refers to code/bugs/alternatives that aren't in the file, it goes.

**Where that content does belong:** the commit message body (which is exactly where "previously X, now Y" is required), or my chat. Not the source.

**What survives:** a comment stating a fact about the code as it exists that a careful reader could not deduce — a non-obvious invariant, an ordering requirement, a gotcha that will bite them. `# MUST NOT await: the loop is single-threaded, so yielding here allows a torn read` is fine. `# MUST NOT await, because I originally wrote this with an await and it broke` is not. An approach that looks right and is not gets the same form: `# MUST NOT batch these: the API rejects more than one per call` names the hazard, not the attempt.

---

# OVER-ENGINEERING

**The smallest change that fixes the actual problem is the right one**
until I say otherwise. Every line nothing asked for is a line I read, maintain
and debug forever.

## Before adding any mechanism, answer these

1. **What breaks in production today without it?** Name the concrete scenario -
   input, state, resulting failure. "It'd be safer" / "it's good practice" /
   "for robustness" are not answers.
2. **Did I ask for it?** If not, it is out of scope.
3. **What is the smallest thing that fixes the problem I actually reported?**

**If you cannot answer 1 with a real scenario, do not add it.** Tell me in one
sentence that you considered it and moved on. I decide, not you.

## The usual suspects - none of these is added unprompted

- **Rate limiting / throttling / backpressure** - is it really needed? What's
  the actual request rate? If you can't tell me the number, you can't
  justify the mechanism. **One case you raise instead of staying silent:** a
  log line that can fire per request or per failure on a hot path, where a
  failure storm becomes a log storm. Tell me in one sentence - the path and
  the rate it could reach - and build nothing until I decide
- **Retries, backoff, jitter, circuit breakers** - a failed call is allowed to
  just fail, counted and logged
- **Caching / memoisation / pooling to speed up a read that must be fresh** -
  measure first. No numbers, no cache. A reader that need not be fresh reads
  a cached copy by "A CHECK COSTS WHAT ITS ANSWER IS WORTH", with no number
  asked for
- **New config knobs** - every knob is another number someone must keep in step
  with the rest. Derive it from an existing value, or hardcode it and say why
- **Interfaces, factories or abstractions with one implementation**
- **Generic "future-proof" helpers** for a second caller that doesn't exist
- **Feature flags** for behaviour nobody asked to switch off
- **Metrics or logs for states that cannot occur**
- **Defensive fallbacks and validation of what the system already guarantees** -
  see YAGNI below, and "Fail fast" under it for what a bad state gets instead

## Effort must be proportional to the change

Over-engineering isn't only code - it's spending an hour on a five-line fix.
**Match the depth of the investigation to the size of the change.**

- A log-level fix does not get a source-dive into the library's internals, a
  matrix of manual runs, or a multi-paragraph code comment
- Verify the one thing the change actually depends on, then commit
- Small fix → short commit body. Save the long ones for real behaviour changes
- If you're on the fourth verification step of something cosmetic, stop and ship

**Don't over-engineer the explanation either.** Long comments, layered
docstrings and essay-length commit bodies on small changes are the same disease.
So is a wall of analysis in chat when one sentence would do.

## When you genuinely believe something is needed

Say it in one sentence with the concrete failure it prevents, and let me decide.
**Do not build it and then tell me.** I would rather ship the small version and
add the mechanism the day it actually hurts.

## YAGNI: You Aren't Gonna Need It

The defensive-code case of over-engineering.

**Defensive code for a scenario that cannot happen in practice is dead code,
and dead code is deleted.**

**The usual shapes:**

1. **Dynamic config handling when config is read-once at startup:**
   ```python
   # ❌ dead code - the validator restarts on config changes
   if len(window) != window_size:
       # Window size changed - resize the deque
       new_window = deque(window, maxlen=window_size)
       self._recent_results[pod_name] = new_window
   ```
   **Why it's wrong:**
   - Config is read once at __init__
   - Helm upgrades restart pods (clearing in-memory state)
   - No hot-reload support
   - This code path never executes

   **Right approach:** Just create deque with current windowSize. No resize logic needed.

2. **Handling state transitions that can't occur:**
   ```python
   # ❌ a pod can't change models without a restart
   if pod.model_name != last_model_name:
       reset_state()
   ```

3. **Validating data that's guaranteed by the system:**
   ```python
   # ❌ Kubernetes guarantees pod.metadata.name exists
   if pod.metadata.name is None:
       raise ValueError("Pod name missing")
   ```

**Where defensive code belongs:**
- Validating external inputs (user data, API responses, config files) - see
  "PARSE AT THE BOUNDARY"
- Failing cleanly on a known transient failure (a network timeout, a
  temporary unavailability): the call fails, counted and logged. A retry is
  on the suspects' list above
- Type safety at system boundaries

**The YAGNI test:**
1. Can this scenario actually occur in production?
2. If yes, how? Trace the execution path.
3. If it requires conditions that never happen (hot reload when there's no hot reload), it is dead code.

**Code review checkpoint:**
When reviewing code, flag any logic that handles scenarios impossible under current system constraints. Dead code wastes reader time and creates false complexity.

## Fail fast: rule the state out, then refuse what remains

Fail fast means the unit of work that meets a bad state stops immediately
and visibly, instead of carrying on with the value. YAGNI deletes the
handling of a state that cannot occur. A state that can occur but should
never happen in practice gets no recovery path of its own. In order:

- **First, make it unrepresentable.** A check in the middle of the code is
  a boundary that let something through; the fix is in "PARSE AT THE
  BOUNDARY", where the type the boundary produces has no way to hold the
  state, not one more check downstream. Many invariants to check is the
  smell that the boundary is too weak.
- **What remains is refused at the smallest scope that contains it**: the
  request fails for its caller, the item is dropped from the pass, counted
  and logged ("EVERY BAD PATH IS COUNTED, THEN LOGGED"). The process dies
  only for a state that is process-wide - a config it cannot parse, a
  corrupt store - and the supervisor restarts it. That is
  [fail fast](https://martinfowler.com/ieeeSoftware/failFast.pdf) as
  Shore defines it, and Erlang's
  [let it crash](https://erlang.org/download/armstrong_thesis_2003.pdf),
  whose point is the size of what crashes, not the crash.
- **The counter is the alert.** It says what happened and how often;
  nothing more is built until it says it happens.
- **A Python `assert` is never the refusal**: `-O` strips it
  (https://docs.python.org/3/using/cmdline.html#cmdoption-O). Raise.

```python
# ❌ the loop meets a pod record with no node, which its writer never
#    produces, and gets a recovery of its own
for pod in pods:
    if pod.node is None:
        node = self._guess_node(pod)
        if node is None:
            self._requeue(pod, delay=self._backoff.next())
        ...

# ✅ the boundary refuses the record, counted; the loop's type has no
#    pod without a node, so the loop checks nothing
def parse_pod(raw: dict) -> Pod:
    if raw.get("node") is None:
        bad_records.labels(reason=BadRecord.POD_WITHOUT_NODE).inc()
        raise BadRecordError(raw["name"])
    return Pod(name=raw["name"], node=raw["node"])
```

---

# ONE SOURCE OF TRUTH - CONFIG, DEFAULTS, LOGIC AND EVERYTHING ELSE

A value that lives in two places will drift, and then one change means hunting
every copy.

- **Binaries and services carry no config defaults.** Every setting comes from
  the chart, written down exactly once. A missing or unparseable setting fails
  startup loudly, reporting every missing key at once, not one per redeploy. An
  empty environment variable reads as unset; an empty-string default is still a
  default.
- **A limit that is safe to lift has an explicit off, and "off" is never a
  huge number.** When running without a limit is a choice a deployment can
  legitimately make (a trimming cap, a size cap a consumer may decline), the
  knob accepts a stated value that switches it off, and the code skips the
  check or the cut on that value. Switching a limit off by setting it above
  anything that could reach it is a smell: that number is a hidden copy of
  some other limit, and it stops meaning "off" the day the other limit grows.
  Off is stated, never assumed, so the binary tells "not set" from "set to
  off" (a pointer, the `ok` of the lookup) and an absent key still fails
  startup.
- **Choose the off value in its context, from three candidates, and never
  `null`.** Weigh each against the knob before deciding:
  - `0`, when zero can never be a real limit for this knob - a cap of zero
    replicas per step would block everything, so zero is free to mean "no
    cap". The first choice whenever it holds: it reads as "no limit" with no
    convention to learn.
  - a word such as `unlimited`, when `0` is itself a legal limit and the
    value can be a string or an enum - "keep 0 items" is a real setting, so
    zero cannot also mean off.
  - `-1`, when `0` is a legal limit and the value must stay a number - a
    numeric flag or API, or an upstream tool whose own convention is `-1`.
    It is a stated off, not a huge number, but a reader has to know it, and
    the range check must reject every other negative value.
  - never `null`: in Helm values it deletes the key, so the `required` guard
    fails the render, and in Go it reads as a missing value, which merges
    "not set" with "off" - the exact distinction the rule above keeps.
- **Name the off value at the key when the name and the value do not say it
  themselves.** One line in values.yaml and in the flag's help text - "0
  turns the cap off" - is a gotcha comment, the kind "COMMENTS IN CODE"
  allows: a reader cannot deduce which value switches the limit off. Leave it
  out when it is self-evident, such as a word `unlimited` among the allowed
  values.
- **Most knobs have no off**, and their range check rejects the values that
  hurt: an amount the process needs to work at all - a worker count, a
  buffer, an interval - and a guard that keeps one input from taking the
  process down - a body or request size limit, a memory bound, a timeout. In
  a review, a liftable limit with no off, an off spelled as a huge number,
  `null` used as off, an off value nobody can find without reading the code,
  or an off added to a guard, is a finding.
- **values.yaml holds only what is meant to be changed.** A knob nobody should
  ever turn is a knob someone will turn at 3am.
- **Fixing drift means deleting the copy, not updating it.** When a change
  makes you edit the same value in a second file, stop - the second copy is the
  bug. Replace it with a pointer to the source in that same commit.
- **Flag both directions**: a default hiding in code for a value the chart also
  sets, and a never-change constant sitting in values.yaml. The same instinct
  applies to dashboards, constants, contracts and docs.
- **The same logic in two places is the same bug as the same value in two
  places.** When two blocks must change together - one rule, one formula, one
  parse of one format - one is the owner and the other calls it.
- **Code that only looks alike is not duplication.** Two blocks that change for
  different reasons stay apart. Extract when a second real caller exists and
  both must change together, not for a caller that might come - see
  "OVER-ENGINEERING". A wrong shared helper costs more than the copy it
  replaced.
- **A copy that cannot drift is cheaper than a pipe that carries the value.**
  Before you add an API field, a parameter or a lookup so that a consumer can
  follow a configurable rule, find who sets that config. When only a dev
  script or a local override sets it, it does not shape a production
  interface: the consumer keeps a named constant that names its owner. The
  test is what a change of the value costs - when the change is a migration
  anyway, the second copy does not drift.
- **This rule is the commonest case of "SOLID VS FRAGILE".** A second copy
  is a line that a change to the first leaves standing and false, the silent
  form of fragility. That section's test decides the cases this one does not
  name - a count, a path, an example, a rule written in two places - and
  explains the copy above that cannot drift: it is solid, because the only
  change that could break it is the migration that rewrites it.

What that looks like in practice:

- **No config defaults in a binary:** every setting read from the chart, and a
  startup that fails listing every missing key at once.
- **Every value explicit in values.yaml**, so one file shows the complete
  configuration of the thing, and templates guard each key with `required` so
  a nulled key fails the render, not the pod.
- **What earns a values.yaml key:** intervals, thresholds, endpoints,
  selectors, replica counts, image tags - anything some deployment
  legitimately sets differently. **What does not:** a protocol magic number,
  a wire-format field name, a hash salt, a parameter the algorithm's
  correctness rests on. Each of those is a named constant in code and appears
  nowhere in the chart.

Docs fall under the same rule: a README or `CLAUDE.md` names the key and the
file that owns it, and never restates the value.

---

# ONE REASON TO CHANGE

The mirror of "ONE SOURCE OF TRUTH": what changes together lives in one place,
and what changes for different reasons lives apart.

- **One reason to change per function, class or module.** Code that changes for
  different reasons - the wire format and the retry policy, the parse and the
  business rule - lives apart. A boolean parameter that switches what a
  function does is two functions.
- **Not "make it small".** Splitting a function that changes for one reason
  into five that always change together adds indirection and nothing else.
- **Related code is grouped together.** Whatever changes for the same reason
  sits side by side, in the order a reader needs it.
- **No spaghetti.** One request is followed from entry to exit without
  doubling back, and every input to a step is visible where the step is
  called. What hides the path is spaghetti: a flag set in one place and
  read in another, a value carried through shared mutable state instead of
  a parameter or a return, an exception thrown to escape a loop, a module
  importing the module that imports it, branches nested so deep that the
  condition that led here is off the screen. Untangle it - pass the value,
  return early, put the two halves side by side - rather than explain the
  route in a comment.

---

# SOLID VS FRAGILE

**Before writing a line, ask what one small change elsewhere does to it.**
Fragility is one of the design smells Robert C. Martin named next to the
SOLID principles: a change in one place breaks something in another, often
somewhere nobody connected to it. It comes in two forms, and the second is
the one that reaches production:

- **Loud fragility: the change breaks something far from it.** A rename
  that fails a test in another package, a new field that breaks a parser
  three services away, one caller's timeout tweaked and another caller's
  retry tripped. The break is visible, but it lands where nobody was
  looking, and whoever made the change could not see it coming. The fix
  cuts the coupling: the value read from one place, the behaviour behind
  one interface, the dependency pointing one way. "ONE REASON TO CHANGE"
  keeps the blast radius of a change to the one place that changes for
  that reason.
- **Silent fragility: the change leaves something standing and false.** A
  copied value, a count, a path, a line number, a "currently", an example
  that mirrors the real config, a values file for a chart another repo
  owns. Nothing breaks and nothing tells the reader; the line goes on
  reading as true. The fix names the owner or derives from it, and when
  neither is possible, writes the trigger next to the line, so the reader
  knows what to re-check and when.

**A solid line answers the same question with nothing to fix:** the change
cannot reach it, or the line follows it, or it breaks loudly at the point
of the change - a `required` key, a lookup by name, a test that calls the
real thing. Loud at the change is solid; loud far away is fragile.

The test, for a value, a rule, a comment, a line of logic or a module
boundary: name the change elsewhere that would affect it, then say what
happens. Nothing, it follows, or it breaks where the change is made:
solid. It breaks somewhere else, or it stays and lies: fragile, and it is
rewritten before it is written.

**Worked example.** A consumer repo carried a values file for a chart it
did not own. The chart renamed a key, Helm ignores a key the chart does
not know, and the copy kept rendering while the setting it carried did
nothing. The solid version is the chart repo's own example, rendered by
its CI on every change, with the consumer pointing at a checkout of it:
the rename then breaks at the commit that causes it.

---

# THE PLAIN VERSION WINS

**When two versions do the same job, write the one a reader follows on the
first pass.** Clever code is paid for by every reader, every change and every
bisect, and buys nothing when the plain version is as correct and fast enough.

- **Plain is the obvious control flow and the idioms every reader knows, not
  the fewest lines.** A two-level loop with a named variable at each level
  beats a comprehension with two `for` clauses, a `reduce` over a lambda or a
  chain of iterator adaptors a reader has to unpick.
- **A known idiom is already plain**: a one-level comprehension, `any()` /
  `all()`, `dict.get` with a default, `?` in Rust. Unrolling it into a
  hand-written loop is not simpler.
- **Past two levels, nesting is the spaghetti "ONE REASON TO CHANGE" names**:
  the inner level becomes a named function, and early returns flatten the
  branches.
- **Performance buys complexity only with a measurement** on a path that
  matters - per token or per request. The WHY comment names what it buys;
  without the measurement, the plain version stays.

---

# A NAME MEANS ONE THING, LITERALLY

**A reader who never saw the code before must know what a variable, field,
function, state or label holds from its name alone, without a comment and
without tracing where it is set.** A name that holds more than its words
say makes every reader rebuild the hidden condition, and the one who gets
it wrong ships the bug.

- **A name that needs a comment to be understood is the wrong name.** Make
  it longer (`reason` -> `frozenReason`, `t` -> `requestTimeout`) or split
  it into two names. A comment is for what no name can carry - why it is
  so, a gotcha, an invariant - not for what the name holds.
- **The literal word is the meaning.** `unread` is true for everything that
  was not read, `ready` for everything that is ready. A name that is true
  only for part of what its word covers - `unread` that is really "unread
  and admitted to the split" - is a lie to every reader who takes the word
  at its meaning.
- **One fact per name.** Two facts are two names. A compound condition
  that readers need goes into its own named state, not into the belly of
  one of the facts it is built from.
- **One record, one fact.** A row, a file or a flag whose mere presence is
  read as a fact follows the same rule. A row written for one reason - to
  carry a status - cannot also stand as proof of another - that some step
  happened - because the code that writes it for the first reason knows
  nothing of the reader relying on the second. Read each fact from the
  record that only that fact writes.
- **A state is named for what it means, not for what causes it.** `frozen`
  means "held as it is this pass"; why it is frozen is decided once, where
  it is set, and the readers act on the state alone. The next cause is one
  more line at that one place, and no reader changes.
- **A change that shifts what a name means renames it.** Keeping the old
  name over a new meaning leaves every existing reader on the old one, and
  the reader nobody re-checked is where the bug lands. Grep every reader of
  the old name, and give each the name it actually means.
- **Labels follow the same rule**: an enum value, a metric label value, a
  log key or a status word must be literally true for every case that
  produces it. A `cluster_unread` count that also counts reads of something
  else on a cluster that was read is false data on a dashboard.
- **A word that sounds final is written only when the state is final.**
  `failed`, `done`, `deleted`, `succeeded` tell every reader the state will
  never change again, and readers act on it: stop retrying, alert, clean
  up, tell the customer. A state that can still move gets a word that says
  so - `retrying`, `pending`, `attempt_failed` - and the final word is
  written once, by the one place that decides nothing else can happen. A
  transition out of a final state is the sign the word was written early.
- **One word, one meaning, everywhere.** The code, its comments, the docs,
  the metrics and the chat use the codebase's word for a thing. A new
  synonym in a doc or a review ("dark" for what the code calls "serves no
  traffic") is a second name a reader must map, so use the existing word or
  define the new one once, where the thing is defined.

**Worked example.** A scaling loop held one field for "this deployment's
cluster could not be read". A fix made it skip deployments the database
already excludes, and added a second field for the plain fact:

```go
// ❌ the word "unread" holds a hidden "and the rows admit it"
type deployment struct {
	unread string // set only when not read AND admitted to the split
	blind  bool   // not read - the field that actually means unread
}

// a restart guard written when unread still meant unread:
case !dep.obs.DeployRunning && dep.unread == "":
	restart(task) // runs on a cluster nobody could read when the rows exclude it
```

Every reader written before the fix kept the old meaning, and the restart
guard started a task on a cluster the loop could not see. The fix gives
each name one meaning, and decides the cause of a state where it is set:

```go
// ✅ one literal meaning per name, and no comment needed to read either
type deployment struct {
	unreadReason string
	frozenReason string
}

// the one place that decides why a deployment is frozen
if dep.unreadReason != "" && admittedBySplitRule(dep) {
	dep.frozenReason = dep.unreadReason
}

case !dep.obs.DeployRunning && dep.unreadReason == "":
	restart(task)
if dep.frozenReason != "" {
	sum += dep.share
}
```

The labels of the same loop had the same flaw:

```go
SkipClusterUnread = "cluster_unread" // ❌ also counted a deploy check that failed on a cluster that was read
SkipFrozen        = "frozen"         // ✅ says what the endpoint is, whatever made it so
```

**The same flaw in a row.** The loop held its first split of an endpoint
while a deploy ran, and took "the endpoint has no target row" to mean "it
was never split". But a pass that skips an endpoint still writes that row,
to carry the endpoint's status, so after one skipped pass the next one
split it in the middle of the deploy:

```go
// ❌ the target row is also written by a pass that splits nothing
_, exists := targets[id]
if !exists && deployInFlight(e) {
	waitForTheDeploy(e)
}
```

Only a split writes a deployment's share row, so the share rows are the
record of that one fact:

```go
// ✅ "never split" read from the record only a split writes
neverSplit := !slices.ContainsFunc(e.members, func(d *member) bool { return d.hasShareRow })
if neverSplit && deployInFlight(e) {
	waitForTheDeploy(e)
}
```

---

# ONE RESULT, ALL OR NOTHING

**A step that returns one result never leaves half of it done.** Two
writes behind one result - two tables, a row and a cluster object, a row
and a message - either commit together or are not one step. A caller that
gets an error cannot tell which half landed, and every reader in between
sees a state nobody meant to write.

Ask of every pair of writes behind one result, in this order:

- **Must they be true together?** When not, split them: each its own step,
  its own error, its own counter, so one failing neither undoes nor blocks
  the other.
- **Same store?** Then one transaction, and nothing outside the store
  inside it - no HTTP call, no cluster write, no message, no counter, no
  log line. A rollback undoes the transaction's own writes, never a call
  made from inside it.
- **Different systems?** No transaction spans them, so one request never
  writes both. Record the intent in one atomic write and let an idempotent
  loop carry out the other side until it matches - the [reconcile
  loop](https://kubernetes.io/docs/concepts/architecture/controller/)
  Kubernetes is built on, or a [transactional
  outbox](https://microservices.io/patterns/data/transactional-outbox.html)
  for a message. A crash then leaves a pending record the loop picks up,
  never an effect nobody recorded.
- **A rollback is the last resort, not the plan.** Undoing the first write
  when the second fails - by hand or as a
  [saga](https://microservices.io/patterns/data/saga.html)'s compensation -
  can itself fail, and the half state was visible until it ran. Design so
  no step needs undoing; when one truly does, raise it with me.

**Read before you write, and keep the read a step of its own where the step
is retried.** A write that first reads whether its work is already done -
the row settled, the object at the wanted spec - finds a repeat and skips
it. The read alone is not the guard: two callers can both read "not done",
so the write carries its own condition (`WHERE status = 'pending'`, a
create that fails on an existing key) and the read only saves the attempt.
Where something re-runs a failed step - a workflow engine, a queue that
redelivers, a reconcile loop - the read and the write are separate steps,
so a failed read retries alone and never re-runs a write. Temporal re-runs
a whole Activity when any step in it fails, and suggests splitting it so
only the failed step retries, at the cost of a longer event history
([error handling](https://docs.temporal.io/develop/python/best-practices/error-handling),
[Activities](https://docs.temporal.io/activities)).

In a review, a function that makes two writes to two places and returns
one error is a finding.

**Worked example.** The verdict loop under "EVERY BAD PATH IS COUNTED,
THEN LOGGED" settled verdicts and filed new requests in one transaction.
A verdict is settled whether or not the next request files, and filing
reads nothing the settle writes, so a request that failed to file rolled
back verdicts with nothing wrong with them, and the next pass settled them
again:

```go
// ❌ one result for two independent jobs
err := dbh.Transaction(func(tx *gorm.DB) error {
	if err := settleAll(tx, verdicts); err != nil {
		return err
	}
	return fileRequests(tx, requests)
})
```

```go
// ✅ each job commits and fails on its own
settleErr := dbh.Transaction(func(tx *gorm.DB) error { return settleAll(tx, verdicts) })
fileErr := dbh.Transaction(func(tx *gorm.DB) error { return fileRequests(tx, requests) })
return errors.Join(settleErr, fileErr)
```

---

# EVERY BAD PATH IS COUNTED, THEN LOGGED

A bad path I cannot alert on is one I find out about from a customer. The
counter is what lets someone write the alert the day it matters.

- **A bad path is wider than an exception.** Anything the code does because
  something went wrong: a failure raised, returned, or caught and swallowed; a
  fallback or default used in place of the real value; a retry; input dropped,
  truncated or skipped; a limit hit; stale data served. A recovery is still a
  bad path - one that fires constantly is an outage nobody sees.
- **Only paths that can occur.** A state the system rules out gets no handler
  and no counter - see "Metrics or logs for states that cannot occur" under
  "OVER-ENGINEERING".
- **Every bad path is counted, then logged.** Each one increments a counter,
  then logs one line with the context needed to debug it (pod name, pod IP,
  model name, whatever identifies the thing that went wrong). Metric first, so
  the count survives a logging failure. A bad path with no metric is invisible
  to an alert; one with no log is undebuggable when the alert fires.
- **What a transaction did is counted after it commits.** Inside the
  transaction, collect the outcomes; once it commits, count and log them. A
  counter bumped inside a transaction that a later write rolls back counts
  an event that never happened, and the retry counts it again, so one
  failure reads as two on the dashboard and in the log.
- **Only what a write changed is counted.** A write guarded by a state
  (`WHERE status = 'pending'`) reports whether it changed a row. Count the
  outcome only when it did: a result thrown away with `_` counts every
  attempt, including one that found the work already done.
- **The happy path is counted per unit of work, not per step.** One counter at
  the level the service is judged on - a request, a validation, a job run -
  either total attempts or outcomes labelled by result. It is the denominator
  that turns a failure count into an error rate, and the only signal of a
  stall: a service that stopped working raises no failure at all. A counter
  on every internal step of a success is noise.
- **A counter makes an alert possible, it does not make one.** Which counters
  get an alert, and at what threshold, is decided per service.
- **The scope is a long-running service.** A CLI or a one-shot script has no
  scrape target; its exit code and its log are the signal.
- **A counter, labelled by a reason enum.** Alerts are `rate()` or
  `increase()` over a counter. The reason label comes from an enum, so its
  cardinality is bounded - never an error string, an ID or a pod name.
- **Every reason starts at zero.** Pre-initialise each label combination at
  startup. A series that first appears at 1 makes `increase()` miss that first
  failure, and the alert stays silent.
- **Every code path, not just the happy one.** A metric called on some failure
  paths and not others reads as zero during the outage it should have shown.
- **The right type.** A counter for events, a histogram for durations, a gauge
  only for a level that goes up and down.
- **A bad-path log on a per-request path can flood.** The counter is never
  cut - it is the signal at any volume. The log line is what gets raised: see
  the rate-limiting bullet in "OVER-ENGINEERING", raise it with me, build
  nothing.

**Worked example.** One pass of a loop settled its verdicts and filed new
requests in one transaction, counting each verdict as it settled it:

```go
// ❌ counted inside the transaction, and the "changed" result thrown away
err := dbh.Transaction(func(tx *gorm.DB) error {
	for _, v := range verdicts {
		if _, err := settle(tx, v); err != nil {
			return err
		}
		verdictsTotal.WithLabelValues(v.Status).Inc()
		log.Warn().Str("verdict", v.Status).Msg("request failed")
	}
	return fileRequests(tx, requests) // fails: the verdicts roll back
})
```

A request that failed to file rolled the pass back, the next pass settled
the same verdict and counted it again, and the alert on failed verdicts
saw two failures for one. The counting moves after the commit, and counts
only a settle that changed a row:

```go
// ✅ collected inside, counted and logged once it commits
var settled []Verdict
err := dbh.Transaction(func(tx *gorm.DB) error {
	for _, v := range verdicts {
		changed, err := settle(tx, v)
		if err != nil {
			return err
		}
		if changed {
			settled = append(settled, v)
		}
	}
	return fileRequests(tx, requests)
})
if err != nil {
	passRollbacksTotal.Inc()
	log.Error().Err(err).Msg("verdict pass rolled back")
	return err
}
for _, v := range settled {
	verdictsTotal.WithLabelValues(v.Status).Inc()
	log.Warn().Str("verdict", v.Status).Msg("request failed")
}
```

Counting after the commit fixes the count; two independent jobs sharing
one transaction is a bug of its own - see "ONE RESULT, ALL OR NOTHING".

---

# PARSE AT THE BOUNDARY

Raw input - a request body, a config file, an API response, an environment
variable - is turned into a typed struct or an enum once, where it enters.
Everything past that point takes the typed value and never re-checks it.

- **A validated value has a type that says so.** A function that checks a
  string and passes the same string on leaves every caller to wonder whether it
  was checked. A function that returns a parsed type answers that for good.
- **This is where defensive code belongs** (see "When defensive code IS
  appropriate" under YAGNI), and the reason the code inside needs none.

---

# A CHECK COSTS WHAT ITS ANSWER IS WORTH

**Before a check runs, ask who reads the answer and what a cheaper one
would cost them.** A hint - a greyed button, a status column, a dashboard
tile, a precondition shown before the click - is served by an answer that
is a minute old, the first page, an estimate, or one computed when the row
is shown rather than on every pass. Only the action itself, at the click or
the write, needs the full fresh answer, and it is the one place the check
runs at full cost. The smell is a check on the hot path at full fidelity
whose only reader is a hint. The database world calls the move
[tunable consistency](https://queue.acm.org/detail.cfm?id=1466448): each
read picks the level it needs.

- **One owner.** The action's check is the truth; a hint that computes its
  own copy drifts from it ("ONE SOURCE OF TRUTH"). The hint calls the same
  function with a cheaper input - the cached value, the partial set - or
  shows the control live and lets the click refuse with the reason. OWASP
  says the same of a client-side check: it is for the person, and the
  server checks regardless
  (https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).
- **Stale is a fidelity, with a bound.** A reader that accepts a stale
  answer reads a cached copy with a TTL named for that reader - Cosmos DB
  calls the level [bounded staleness](https://learn.microsoft.com/en-us/azure/cosmos-db/consistency-levels).
  Who fills the cache - read-through, a refresher, a watch - is a decision
  of its own; HTTP standardised the refresher shape as
  [stale-while-revalidate](https://www.rfc-editor.org/rfc/rfc5861). A value
  past the TTL is unknown, not a fetch from inside the reader.
- **Partial and approximate are fidelities too.** The first N rows, a count
  from the index, a sample, with the hint saying which it shows. "The Tail
  at Scale" calls them good-enough results
  (https://research.google/pubs/the-tail-at-scale/).
- **A fresh full answer is a cost named per reader**: a quota before a
  charge, ownership before a write, the leader before an action. Those
  read live, and the WHY says why.

The Kubernetes API is the worked example. A GET or LIST picks its freshness
with `resourceVersion`: unset is a quorum read, `"0"` is served from the
apiserver's cache
([semantics for get and list](https://kubernetes.io/docs/reference/using-api/api-concepts/#semantics-for-get-and-list)).
A controller reads from an informer cache, never the apiserver, and the
write still carries the version it read, so the apiserver refuses it when
the object has moved.

```python
# a hint: the board's node count may be seconds old, so it reads the cache
nodes = core.list_node(resource_version="0")

# the action: a fresh read, and the write carries the version it read -
# the apiserver answers 409 Conflict if the node changed in between
node = core.read_node(name)
node.spec.unschedulable = True
core.replace_node(name, node)
```

---

# ASYNCIO

- **Every task has an owner.** The result of `asyncio.create_task` is kept and
  awaited, or held by a `TaskGroup` or a set the owner drains. The event loop
  keeps only a weak reference, so an unreferenced task can be garbage-collected
  mid-execution, and an exception it raised surfaces only as a stray
  "never retrieved" log line, if at all.
- **Nothing blocks the event loop.** A blocking call - sync I/O, a sync HTTP
  client, `time.sleep`, heavy CPU work - stalls every coroutine on the loop.
  Use the async equivalent, or `asyncio.to_thread` for what has none.

---

# ONE LOCK AT A TIME

**A lock taken while another is held is a design smell, whatever the two
guard.** Two locks held at once is the one ingredient a deadlock needs, and
a deadlock is the worst failure a service can have: nothing crashes, nothing
logs, no counter moves, the health check keeps passing, and the process sits
until someone kills it. Nested locking is named in review before the order
is argued safe, because an order is checked by nobody and broken by the next
caller.

- **Nesting says two things that change together got separate locks, or one
  lock guards too much.** State that must change together is one lock
  ("ONE REASON TO CHANGE"); state that changes apart is two regions, each
  released before the next is taken.
- **A call made under a lock is a nested lock you cannot see.** The callee
  may take its own lock today or after its next change - a callback, a
  logger, a client, another component's method. Under a lock run only the
  reads and writes it guards; I/O, an `await`, a callback or a call into
  another component under it is each a nested lock in waiting. The same rule
  "ONE RESULT, ALL OR NOTHING" gives a transaction.
- **A documented lock order is a workaround, not a design.** When two locks
  truly must be held together the split was wrong: one lock, a queue drained
  by the one owner of the state, or an actor that owns it.
- **A reentrant lock hides the smell instead of fixing it.** It lets a
  function take a lock it already holds, so the nesting leaves no trace,
  and the same call from a second thread deadlocks.
- **asyncio is not exempt.** An `asyncio.Lock` held across an `await` that
  takes another deadlocks the loop the same way, with no thread dump to show
  it.
- **A race the design cannot remove is better healed than locked harder.** A
  race between two processes, a process and the cluster, or a writer and a
  reader is out of any lock's reach: another lock narrows the window and
  leaves the bug, and brings the nesting above with it. Make the state
  converge instead: an idempotent write, a reconcile loop that reads the
  truth and repairs the copy, a reader that takes a stale value as a retry.
  The race then costs one repair and never a hang.
- **Row locks in a database fall outside this section: the database finds
  the deadlock.** It aborts one side with an error instead of hanging, so
  the silent hang this section guards against never happens. One atomic
  statement, or a write that checks a version column, comes before a
  transaction that holds row locks across statements. Where a transaction
  must, keep it short and retry it whole on a deadlock or serialization
  error (SQLSTATE `40001`, and `40P01` in PostgreSQL), counted by reason:
  the retry is the healing above, and locking rows in key order only makes
  it rarer. An in-process lock held around the transaction brings the
  section back, since no detector sees a deadlock that spans the two.

```python
# ❌ the cache lock is taken while the registry lock is held
async with self._registry_lock:
    pod = self._registry[name]
    async with self._cache_lock:
        self._cache[name] = pod.snapshot()

# ✅ the registry and its cache change together, so one lock owns both,
#    and nothing else runs under it
async with self._lock:
    pod = self._registry[name]
    self._cache[name] = pod.snapshot()
```

---

# TESTS CHECK THE CONTRACT, NOT THE CODE

**A unit test earns its place by catching a real regression.** It pins
something the component promises - its API, an invariant, the intent behind a
rule - so it fails when that promise breaks and stays green through any
refactor that keeps it.

- **Test through the public interface.** Call what the callers call, assert on
  what they observe: the return value, the error raised, the counter
  incremented, the message sent. Reaching into a private helper, an internal
  attribute or the order of internal calls is the white-box smell below.
- **An invariant is a property, not one example.** "Every reason label starts
  at zero", "the window never holds more than its size", "parse(render(x)) ==
  x" - check it across the inputs that matter: empty, the boundary, the one
  that hit the bug. Where the input space is wide, generate the inputs
  (Hypothesis in Python, proptest in Rust).
- **Intent is tested by the case that tells it apart.** A rule like "timeouts
  are transient, wrong output blacklists" gets a test for each side of the
  line, so a change that blurs it fails.
- **The name states the behaviour.**
  `test_timeout_is_transient_and_never_blacklists`, not `test_validate_3`. A
  red test's name says which promise broke.
- **Mock only the boundary**: network, clock, filesystem, cluster, another
  service. A mocked collaborator inside the component, asserted to have been
  called with these arguments, tests the wiring - it breaks on every refactor
  and passes through every bug.
- **A bug fix carries the test that reproduces it**, red before the fix.

## Black box by default: the code may pick the inputs, not the assertions

- **A black-box test knows only the contract**: the public interface, what it
  documents, and the invariants it promises. It could be written from the spec
  before the code exists, and it survives every refactor that keeps the
  contract. Every test starts as one.
- **A white-box test knows the internals**: it asserts on private state, on
  which internal calls ran, or on the path the code took. It breaks on a
  refactor that keeps the behaviour, and it agrees with whatever the code does,
  bug included.
- **Reading the code to choose inputs is allowed.** A boundary the
  implementation has, a branch no obvious input reaches, the input that hit
  the bug: knowing the code finds them. The test still calls the public
  interface and asserts what a caller observes.
- **A behaviour no input from outside can reach means the unit is too big.**
  Split that part into its own unit with its own public interface, and test it
  black-box there, rather than by reaching inside the bigger one.
- **The check, in a review: could the assertions be written from the contract
  alone?** If they need the code to be written, the test is white-box.

```python
# ❌ white box: asserts how the window is stored
assert validator._recent_results["pod-a"].maxlen == 5

# ✅ black box: asserts what a caller observes
for _ in range(6):
    validator.record("pod-a", ValidationResult.FAILED)
assert validator.failure_count("pod-a") == 5
```

## Reaching the failure paths: weigh it, then ask me

A black-box test reaches only the paths its inputs reach, and against
dependencies that never fail that is the happy path. How a test reaches the
failure paths has no default: it depends on the language, the component and
what it has to survive. Before writing the failure tests, weigh the options
for the case in hand and raise it with me - what each would cost here and
which you lean to. Once a component's way is settled - by its existing
tests, its plan or my answer - follow it and do not raise it again. The ones
known out there:

- **A fake that fails, at the boundary.** The dependencies - store, HTTP
  client, cluster client, clock - are injected, and the test's fake can be
  told to fail one call: client-go's fake clientset with a reactor that
  returns an error, respx for httpx, an in-memory store that fails the nth
  write. The test stays black-box: the failure comes from outside, and the
  assertion is what a caller observes. It costs a fake per dependency, and
  it cannot express a crash between two of the component's own steps.
- **Named failpoints compiled out of production.** A marker in the code that
  a test build can make fail, panic or pause: fail-rs in Rust behind its
  `failpoints` feature, pingcap/failpoint or gofail in Go, which rewrite the
  markers into checks only for a test build. It reaches a crash or a pause
  between two steps. The markers live in the production source, and Python
  has no compile-out, so a hook there runs in production.
- **Faults at the network or process level.** Toxiproxy between real
  processes, Chaos Mesh on a cluster: latency, resets, a killed pod, a
  partition. No code changes, and it tests the deployed whole - slowly, and
  not on every commit.
- **Deterministic simulation.** Network, disk and clock simulated, faults
  injected from a seed, every failure replayable: FoundationDB, TigerBeetle,
  turmoil for tokio. The strongest coverage for distributed logic, and an
  investment in how the component is built.
- **A test-only branch inside the logic** - an `if TESTING`, a private method
  patched out - is the option to argue against: the code under test is no
  longer the code that ships.

**Smells, because they mirror the implementation instead of checking it:**
- asserting a private attribute or an intermediate state
- a snapshot of a whole object or log line when one field is the contract
- the expected value computed with the same formula the code uses - the test
  then agrees with the bug
- a test per getter, constructor or dataclass field, or of what the language
  or a library already guarantees
- a test written to raise coverage

**The test for a test:** would it fail if the behaviour broke, and would it
still pass after a refactor that keeps the behaviour? Both must be yes. A
behaviour-preserving refactor that breaks it means it is coupled to the
implementation; no plausible bug that breaks it means it is noise. Delete
either. A few sharp tests beat many shallow ones - "Effort must be
proportional to the change" applies to tests too.

---

# ENUMS OVER STRINGS

**A fixed set of values is an enum; a string literal standing for one of
them is a smell.**

```python
# ✅ the set has a type
class ValidationResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"

result = ValidationResult.SUCCESS

# ❌ a typo is a new value nothing catches
result = "success"
```

**Why enums are better:**
- Catch typos at development time (IDE autocomplete, type checking)
- Self-documenting (all possible values visible in one place)
- Refactoring-safe (rename once in enum, not scattered string literals)
- Type-safe (can't accidentally pass wrong value)

**When to use enums:**
- Status codes (SUCCESS, FAILED, PENDING)
- Result types (validation results, error types, response codes)
- Fixed categories (pod types, validation modes, alert levels)
- Configuration options with limited choices

**Implementation pattern:**
```python
from enum import Enum

class MyEnum(Enum):
    VALUE_ONE = "value_one"  # Use lowercase with underscores for enum values
    VALUE_TWO = "value_two"

# Usage
my_value = MyEnum.VALUE_ONE
if my_value == MyEnum.VALUE_ONE:
    ...

# Get string value when needed (e.g., for metrics/logs)
my_value.value  # Returns "value_one"
```

**A docstring that lists the enum's values is a copy of the enum**, and the
parameter typed as the enum needs no list at all:

```python
# ❌ the values are written twice, and the parameter still takes any string
def foo(result: str):
    """
    Args:
        result: Result type. One of:
            - "success": Success
            - "failed": Failed
            - "error": Error
    """

# ✅ the type says it
def foo(result: ValidationResult):
    ...
```
