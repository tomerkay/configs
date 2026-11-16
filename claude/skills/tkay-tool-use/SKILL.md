---
name: tkay-tool-use
description: How tool calls run - shell commands, file reads and MCP tools alike: every read runs without asking, a refused command is re-tested once, a long run in the background with its log and the Mac held awake, a background watcher that fails on a poll it cannot read, JSON piped into jq straight from what produced it, and what to do while a /goal waits. Use before the first tool call of a session, when handed something to investigate, and whenever a command may run longer than a few minutes, a loop polls for a state, JSON goes into jq, or a /goal is set.
---

# Tool use

| When | Read |
|---|---|
| the first change of a task, to find the steps this session cannot run | `references/protections.md` |
| writing a file for your own work - scratch, a script, a staged copy | `references/scratch-files.md` |
| something to investigate, a question about whether to read, or a refused command | `references/reads.md` |
| a command may run longer than a few minutes, or I ask whether a run is stuck | `references/long-runs.md` |
| a loop or a background script polls until a state arrives | `references/watchers.md` |
| JSON goes into jq | `references/jq.md` |
| a Go CLI fails TLS with `OSStatus -26276` inside the sandbox | `references/go-tls-in-sandbox.md` |
| a git command that may reach the remote or a path the sandbox blocks | `references/git-in-sandbox.md` |
| a `/goal` is set, or its Stop hook fires | `references/goals.md` |

**Read the reference before the call that needs it.** Never answer from
memory of a reference you have not read this session.
