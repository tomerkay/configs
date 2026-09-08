# Writing Project CLAUDE.md Files

When I ask you to update or create a project's `.claude/CLAUDE.md` file:

**CRITICAL RULES:**

1. **NEVER include code implementations** - they go stale immediately and become false documentation
2. **NEVER reference line numbers** - they change with every code edit
3. **NEVER show actual code snippets** - describe patterns and concepts instead
4. **NEVER INCLUDE USER-SPECIFIC PATHS** - no `/Users/<name>/`, no `~/<name>/`, no absolute paths with usernames. Project CLAUDE.md files go into the repository and will be read by other developers. Use relative paths from repo root or generic examples only.

**DO:**
- Document design decisions and WHY they were made
- Explain architecture patterns and how components interact
- Capture non-obvious behaviors, gotchas, edge cases
- Describe algorithms/flows at a high level
- Note important configuration patterns
- Keep it concise - engineering notes, not essays

**DON'T:**
- Copy/paste code (it will be wrong tomorrow)
- Reference specific line numbers
- Include user-specific file paths
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

**Focus on:**
- Why things work this way (design rationale)
- How components interact (architecture)
- What happens in edge cases (gotchas)
- Trade-offs made (and why)

**Avoid:**
- What the code does (that's what code is for)
- How to use it (that's what docs/examples are for)
- Implementation details (they change constantly)

## Each file has one job

Applying the one-source-of-truth rule to a repo's documentation:

- **values.yaml** is the config reference: what can be set, what it means, what
  it is. It earns that by carrying a comment on every key.
- **The repo CLAUDE.md** is design: why it works this way, gotchas, edge cases -
  no key-by-key listings, no values.
- **README.md** is the operator guide: what it is, how to deploy, the metrics or
  API contract consumers depend on, troubleshooting.

Something that fits two of them is written in one and pointed at from the other.

**Docs never restate a value.** No "(default 15)", no example block pasted with
the current numbers, no table with a Default column, no "the threshold is 0.4".
Name the key and point at values.yaml. Three files agreeing today is not a
defence: I have had values.yaml, README.md and CLAUDE.md each stating the same
defaults in one chart, two of them stale.
