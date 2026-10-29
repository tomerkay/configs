#!/usr/bin/env python3
"""UserPromptSubmit, SessionStart and SessionEnd hook: records the paths under /tmp that the
user's messages name.

One file per session under ~/.claude/scratch-paths/, one resolved path per line, read by
tool-gate.py: a write under /tmp lands only inside a path listed there. Nothing
is ever written to stdout: on UserPromptSubmit, stdout is added to the prompt as context.
Exit 2 is never used either, because on UserPromptSubmit it erases the prompt; a failure
exits 1 and records nothing.
"""

import json
import os
import re
import sys

STATE_DIR = os.path.expanduser("~/.claude/scratch-paths")

# A `<tag …>…</tag>` block is text the user did not type: pasted text arrives wrapped in
# pasted_content, and the harness wraps scheduled prompts, subagent reports and messages
# from other sessions the same way. A path inside one is not the user asking for it.
TAG_BLOCK_RE = re.compile(r"<([A-Za-z_][\w.-]*)\b[^>]*>.*?</\1\b[^>]*>", re.S)
# A path below /tmp. Naming /tmp or the harness scratch root while talking about them
# unlocks nothing.
TMP_PATH_RE = re.compile(r"(?<![\w/.-])(?:/private)?/tmp/[^\s`'\"<>()\[\]]+")
NEVER_NAMED = {os.path.realpath("/tmp"), os.path.realpath("/tmp/claude")}
KEEPS_STATE_SOURCES = {"compact"}


def state_path(session_id):
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))
    if not name:
        raise ValueError("empty session_id")
    return os.path.join(STATE_DIR, name)


def remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def record(path, prompt):
    named = {os.path.realpath(m.rstrip(".,:;!?"))
             for m in TMP_PATH_RE.findall(TAG_BLOCK_RE.sub(" ", prompt))} - NEVER_NAMED
    if not named:
        return
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "a") as f:
        f.writelines(p + "\n" for p in sorted(named))


def main():
    payload = json.load(sys.stdin)
    event = payload["hook_event_name"]
    path = state_path(payload["session_id"])
    if event == "SessionStart":
        if payload.get("source") not in KEEPS_STATE_SOURCES:
            remove(path)
        return
    if event == "SessionEnd":
        remove(path)
        return
    if event != "UserPromptSubmit":
        return
    prompt = payload.get("prompt")
    if isinstance(prompt, str):
        record(path, prompt)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"scratch-paths: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
