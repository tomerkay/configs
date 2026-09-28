# Writing Project CLAUDE.md Files

When creating or updating a project's `.claude/CLAUDE.md` file, whether I asked
for it or it is a side effect of a code change:

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

Which file owns what - values.yaml, the repo CLAUDE.md, README.md - and the ban
on a doc restating a value live in the global CLAUDE.md, "One source of truth",
the "Docs are copies too" paragraph. They are always in force and are not
repeated here; this file only covers the shape of a good CLAUDE.md, above.
