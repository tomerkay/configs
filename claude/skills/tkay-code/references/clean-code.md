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

**DO NOT ADD COMMENTS THAT STATE THE OBVIOUS OR REPEAT WHAT THE CODE/LOG ALREADY SAYS.**

Examples of BANNED comments:
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

**The ONLY acceptable comments are:**
1. **WHY comments**: Explain non-obvious reasoning, design decisions, or business logic
   - Example: `# Use cached state on FETCH_ERROR to avoid marking all pods as healthy during transient gateway issues`
2. **GOTCHA comments**: Warn about subtle bugs or edge cases
   - Example: `# IMPORTANT: must call record_metric BEFORE logging to ensure metrics are recorded even if logging fails`
3. **TODO/FIXME with ticket reference**: `# TODO(JIRA-123): Optimize this query`

**When in doubt, DELETE THE COMMENT.** If the code is unclear, improve the code (better naming, structure), don't add a comment.

## NEVER LEAVE CONVERSATION ARTIFACTS IN THE CODE

**A comment must make sense to someone who reads the file cold, having never seen our discussion.** If a comment only exists because of something that happened in our conversation — a code review finding, a rejected alternative, a bug I introduced and fixed, a design I argued for — it does NOT belong in the code. Answer me in chat; leave the file clean.

**BANNED — arguing a case, defending a choice, or narrating history:**
- `# Named rather than a bare tuple because three of the five are int/float: transposing the epoch count with the idle seconds would type-check and quietly report...` — defending a design against an alternative that was never in the file
- `# Fixed rather than configurable: nothing has asked to tune it` — justifying a decision to a reviewer
- `# Gated here rather than relying on X, which happens to be true today but is a coincidence` — arguing against a rejected approach
- `# so they cannot drift apart the way three parallel lists could` — referencing code that no longer exists
- `# without this, a skipped write would still log as published` — describing the bug I just fixed
- Anything containing "rather than", "instead of", "we could have", "previously", "this used to", "deliberately not", or a justification for why the code isn't something else

**The test:** delete every trace of our conversation from your memory, then read the comment. If it now reads as a defence of a decision, or refers to code/bugs/alternatives that aren't in the file, DELETE IT.

**Where that content DOES belong:** the commit message body (which is exactly where "previously X, now Y" is required), or my chat. Not the source.

**What survives:** a comment stating a fact about the code as it exists that a careful reader could not deduce — a non-obvious invariant, an ordering requirement, a gotcha that will bite them. `# MUST NOT await: the loop is single-threaded, so yielding here allows a torn read` is fine. `# MUST NOT await, because I originally wrote this with an await and it broke` is not.

**PRODUCTION CODE IS SACRED.** Every needless comment wastes the reader's time. The log message, function name, or variable name should make the intent clear. If you catch yourself writing a comment that just restates the code, STOP and delete it immediately.

---

# OVER-ENGINEERING

**The smallest change that fixes the actual problem is ALWAYS the right one**
until I say otherwise. Every line nothing asked for is a line I read, maintain
and debug forever.

## Before adding ANY mechanism, answer these

1. **What breaks in production TODAY without it?** Name the concrete scenario -
   input, state, resulting failure. "It'd be safer" / "it's good practice" /
   "for robustness" are NOT answers.
2. **Did I ask for it?** If not, it is out of scope.
3. **What is the smallest thing that fixes the problem I actually reported?**

**If you cannot answer 1 with a real scenario, DO NOT ADD IT.** Tell me in one
sentence that you considered it and moved on. I decide, not you.

## The usual suspects - NEVER add these unprompted

- **Rate limiting / throttling / backpressure** - is it REALLY fucking needed?
  What's the actual request rate? If you can't tell me the number, you can't
  justify the mechanism. **One case you raise instead of staying silent:** a
  log line that can fire per request or per failure on a hot path, where a
  failure storm becomes a log storm. Tell me in one sentence - the path and
  the rate it could reach - and build nothing until I decide
- **Retries, backoff, jitter, circuit breakers** - a failed call is allowed to
  just fail and be logged
- **Caching / memoisation / pooling** - measure first. No numbers, no cache
- **New config knobs** - every knob is another number someone must keep in step
  with the rest. Derive it from an existing value, or hardcode it and say why
- **Interfaces, factories or abstractions with ONE implementation**
- **Generic "future-proof" helpers** for a second caller that doesn't exist
- **Feature flags** for behaviour nobody asked to switch off
- **Metrics or logs for states that cannot occur**
- **Defensive fallbacks and validation of what the system already guarantees** -
  see YAGNI below. Fail loudly instead

## Effort must be proportional to the change

Over-engineering isn't only code - it's spending an hour on a five-line fix.
**Match the depth of the investigation to the size of the change.**

- A log-level fix does NOT get a source-dive into the library's internals, a
  matrix of manual runs, or a multi-paragraph code comment
- Verify the ONE thing the change actually depends on, then commit
- Small fix → short commit body. Save the long ones for real behaviour changes
- If you're on the fourth verification step of something cosmetic, STOP and ship

**Don't over-engineer the explanation either.** Long comments, layered
docstrings and essay-length commit bodies on small changes are the same disease.
So is a wall of analysis in chat when one sentence would do.

## When you genuinely believe something is needed

Say it in ONE sentence with the concrete failure it prevents, and let me decide.
**Do NOT build it and then tell me.** I would rather ship the small version and
add the mechanism the day it actually hurts.

## YAGNI: You Aren't Gonna Need It

The defensive-code case of over-engineering.

**NEVER add defensive code for scenarios that cannot happen in practice.**

**Examples of BANNED defensive programming:**

1. **Dynamic config handling when config is read-once at startup:**
   ```python
   # ❌ WRONG: Dead code - validator restarts on config changes
   if len(window) != window_size:
       # Window size changed - resize the deque
       new_window = deque(window, maxlen=window_size)
       self._recent_results[pod_name] = new_window
   ```
   **Why it's wrong:**
   - Config is read once at __init__
   - Helm upgrades restart pods (clearing in-memory state)
   - No hot-reload support
   - This code path NEVER executes

   **Right approach:** Just create deque with current windowSize. No resize logic needed.

2. **Handling state transitions that can't occur:**
   ```python
   # ❌ WRONG: If pod can't change models without restart
   if pod.model_name != last_model_name:
       reset_state()
   ```

3. **Validating data that's guaranteed by the system:**
   ```python
   # ❌ WRONG: If Kubernetes guarantees pod.metadata.name exists
   if pod.metadata.name is None:
       raise ValueError("Pod name missing")
   ```

**When defensive code IS appropriate:**
- Validating external inputs (user data, API responses, config files)
- Handling known transient failures (network timeouts, temporary unavailability)
- Type safety at system boundaries

**The YAGNI test:**
1. Can this scenario actually occur in production?
2. If yes, how? Trace the execution path.
3. If it requires conditions that never happen (hot reload when there's no hot reload), DELETE IT.

**Code review checkpoint:**
When reviewing code, flag ANY logic that handles scenarios impossible under current system constraints. Dead code wastes reader time and creates false complexity.

---

# ONE SOURCE OF TRUTH - CONFIG, DEFAULTS, LOGIC AND EVERYTHING ELSE

A value that lives in two places WILL drift, and then one change means hunting
every copy.

- **Binaries and services carry NO config defaults.** Every setting comes from
  the chart, written down exactly once. A missing or unparseable setting fails
  startup LOUDLY, reporting EVERY missing key at once, not one per redeploy. An
  empty environment variable reads as unset; an empty-string default is still a
  default.
- **A limit that is safe to lift has an explicit off, and "off" is never a
  huge number.** When running without a limit is a choice a deployment can
  legitimately make (a trimming cap, a size cap a consumer may decline), the
  knob accepts a stated value that switches it off: `0`, or a word like
  `unlimited` where `0` is itself a legal limit. The code skips the check or
  the cut on that value. Switching a limit off by setting it above anything
  that could reach it is banned: that number is a hidden copy of some other
  limit, and it stops meaning "off" the day the other limit grows. Off is
  stated, never assumed, so the binary tells "not set" from "set to off" (a
  pointer, the `ok` of the lookup) and an absent key still fails startup.
  **Most knobs have no off**, and their range check rejects the values that
  hurt: an amount the process needs to work at all - a worker count, a
  buffer, an interval - and a guard that keeps one input from taking the
  process down - a body or request size limit, a memory bound, a timeout. In
  a review, a liftable limit with no off, an off spelled as a sentinel
  number, or an off added to a guard, is a finding.
- **values.yaml holds ONLY what is meant to be changed.** A knob nobody should
  ever turn is a knob someone WILL turn at 3am.
- **Fixing drift means deleting the copy, not updating it.** When a change
  makes you edit the same value in a second file, STOP - the second copy is the
  bug. Replace it with a pointer to the source in that same commit.
- **Flag both directions**: a default hiding in code for a value the chart also
  sets, and a never-change constant sitting in values.yaml. The same instinct
  applies to dashboards, constants, contracts and docs.
- **The same logic in two places is the same bug as the same value in two
  places.** When two blocks must change together - one rule, one formula, one
  parse of one format - one is the owner and the other calls it.
- **Code that only looks alike is not duplication.** Two blocks that change for
  different reasons stay apart. Extract when a second real caller exists and
  both must change together, never for a caller that might come - see
  "OVER-ENGINEERING". A wrong shared helper costs more than the copy it
  replaced.
- **A copy that cannot drift is cheaper than a pipe that carries the value.**
  Before you add an API field, a parameter or a lookup so that a consumer can
  follow a configurable rule, find who sets that config. When only a dev
  script or a local override sets it, it does not shape a production
  interface: the consumer keeps a named constant that names its owner. The
  test is what a change of the value costs - when the change is a migration
  anyway, the second copy does not drift.

What that looks like in practice:

- **No config defaults in a binary:** models-monitor is the reference
  implementation - every setting read from the chart, startup fails listing
  every missing key at once. mailroom follows it.
- **Every value explicit in values.yaml**, so one file shows the complete
  configuration of the thing, and templates guard each key with `required` so
  a nulled key fails the render, not the pod.
- **What earns a values.yaml key:** intervals, thresholds, endpoints,
  selectors, replica counts, image tags - anything some deployment
  legitimately sets differently. **What never does:** a protocol magic number,
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
  return early, put the two halves side by side - never explain the route
  in a comment.

---

# FAILURES ARE COUNTED, THEN LOGGED

A failure I cannot alert on is a failure I find out about from a customer.

- **Every failure is counted, then logged.** Each failure path - raised,
  returned, or caught and swallowed - increments a counter, then logs one line
  with the context needed to debug it (pod name, pod IP, model name, whatever
  identifies the thing that failed). Metric first, so the count survives a
  logging failure. A failure with no metric is invisible to an alert; one with
  no log is undebuggable when the alert fires.
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
- **A per-request failure log can flood.** See the rate-limiting bullet in
  "OVER-ENGINEERING": raise it with me, build nothing.

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

# TESTS CHECK THE CONTRACT, NOT THE CODE

**A unit test earns its place by catching a real regression.** It pins
something the component promises - its API, an invariant, the intent behind a
rule - so it fails when that promise breaks and stays green through any
refactor that keeps it.

- **Test through the public interface.** Call what the callers call, assert on
  what they observe: the return value, the error raised, the counter
  incremented, the message sent. Never reach into a private helper, an internal
  attribute or the order of internal calls.
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

**Banned, because they mirror the implementation instead of checking it:**
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

# Type Safety: Prefer Enums Over Strings

**ALWAYS use enums instead of string literals for representing a fixed set of values.**

**DO:**
```python
class ValidationResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"

result = ValidationResult.SUCCESS
```

**DON'T:**
```python
result = "success"  # Type-unsafe, typos won't be caught
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

**DRY: NEVER list enum values in docstrings:**

**WRONG:**
```python
def foo(result: str):
    """
    Args:
        result: Result type. One of:
            - "success": Success
            - "failed": Failed
            - "error": Error
    """
```

**RIGHT:**
```python
def foo(result: str):
    """
    Args:
        result: Result type (see MyResultEnum for possible values).
    """
```

The enum already defines all values - don't duplicate them in docstrings. Just reference the enum class.
