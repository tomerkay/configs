# Worked examples behind the always-on code rules

The rules themselves are in my global CLAUDE.md and are in force whether or not
you read this file. This is the evidence behind them — read it when you are
unsure whether a specific comment, mechanism, default or config key is
acceptable.

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

**PRODUCTION CODE IS SACRED.** Every comment I add wastes the reader's time. The log message, function name, or variable name should make the intent clear. If you catch yourself writing a comment that just restates the code, STOP and delete it immediately.

---

# OVER-ENGINEERING

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
  justify the mechanism
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

# ONE SOURCE OF TRUTH - CONFIG, DEFAULTS, AND EVERYTHING ELSE

I am obsessive about single source of truth. A value that lives in two places
WILL drift, and then one change means hunting every copy — that is how config
bugs are born.

- **Binaries and services carry NO config defaults.** Every setting comes from
  the deployment (the chart), written down exactly once. A missing or
  unparseable setting fails startup LOUDLY and reports EVERY missing key at
  once — never fall back to a number the deployment didn't choose, and never
  fail one-key-at-a-time so I redeploy five times to find five problems.
  models-monitor is the reference implementation of this pattern; mailroom
  follows it.
- **Charts set every value explicitly in values.yaml.** I want to open ONE
  file and see the complete configuration of the thing. No defaults popping
  out of code, templates, or helpers and surprising me at runtime. Templates
  guard values with `required` so a nulled key fails the render, not the pod.
- **values.yaml holds ONLY what is meant to be changed.** A setting earns a
  key there because some deployment legitimately wants a different value:
  intervals, thresholds, endpoints, selectors, replica counts, image tags.
  A constant that must NEVER change — a protocol magic number, a wire-format
  field name, a hash salt, a parameter the algorithm's correctness rests on —
  is a named constant in the code and appears NOWHERE in the chart. That is
  not a gap in configurability, it is the point: a key in values.yaml is a
  knob, and a knob nobody should ever turn is a knob someone WILL turn at
  3am. If the only correct value is the current one, do not expose it.
- An empty environment variable reads as unset — an empty string default is
  still a default.
- When you spot a default hiding in code for a value the chart also sets (or
  should set), FLAG IT — it is a bug in my book even while the two copies
  happen to agree. Same in the other direction: a constant nobody should ever
  change sitting in values.yaml is a bug too, FLAG IT.
- **Fixing drift means deleting the copy, not updating it.** When a change
  makes you edit the same value in a second file, STOP: the second copy is
  the bug. Replace it with a pointer to the source in that same commit.
  Updating it in place cures today's symptom and keeps the disease.
- The same instinct applies beyond config: dashboards, constants,
  contracts - one authoritative place, everything else points at it.

Documentation's share of this rule — which file carries what — is in
`project-claude-md.md`.

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
