#!/usr/bin/env python3
"""UserPromptSubmit, SessionStart and SessionEnd hook: records whether the `LFG!` gate is open.

One file per session under ~/.claude/lfg-state/, read by tool-gate.py. The file holds
"open" or "one-turn". Nothing is ever written to stdout: on UserPromptSubmit, stdout is
added to the prompt as context. Exit 2 is never used either, because on UserPromptSubmit
it erases the prompt; a failure exits 1 and leaves the gate as it was.
"""

import json
import os
import re
import sys

STATE_DIR = os.path.expanduser("~/.claude/lfg-state")
OPEN, ONE_TURN = "open", "one-turn"

# A `<tag …>…</tag>` block is text the user did not type: pasted text arrives wrapped in
# pasted_content, and the harness wraps scheduled prompts, subagent reports and messages
# from other sessions the same way. Nothing inside one opens, closes or spends the gate.
TAG_BLOCK_RE = re.compile(r"<([A-Za-z_][\w.-]*)\b[^>]*>.*?</\1\b[^>]*>", re.S)
QUOTED_RE = re.compile(r"`[^`]*`|\"[^\"]*\"|'[^']*'")
TOKEN_RE = re.compile(r"\bLFG!")
SCOPED_PHRASES = ("for this one only", "one-shot", "just this")
SPENT_PHRASES = ("lfg is spent", "lfg! is spent", "lfg was spent", "lfg! was spent",
                 "make it spent", "close the gate", "gate it again",
                 "back to asking me each time")
CALL_OFF = {"stop", "halt", "abort"}
KEEPS_GATE_SOURCES = {"compact"}


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


def write(path, value):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "w") as f:
        f.write(value)


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def on_prompt(path, prompt):
    without_tags = TAG_BLOCK_RE.sub(" ", prompt)
    if TAG_BLOCK_RE.search(prompt) and not without_tags.strip():
        return
    text = QUOTED_RE.sub(" ", without_tags)
    low = text.lower()
    if any(phrase in low for phrase in SPENT_PHRASES):
        remove(path)
        return
    if re.sub(r"[^a-z]", "", prompt.lower()) in CALL_OFF:
        remove(path)
        return
    if TOKEN_RE.search(text):
        write(path, ONE_TURN if any(p in low for p in SCOPED_PHRASES) else OPEN)
        return
    if read(path) == ONE_TURN:
        remove(path)


def main():
    payload = json.load(sys.stdin)
    event = payload["hook_event_name"]
    path = state_path(payload["session_id"])
    if event == "SessionStart":
        if payload.get("source") not in KEEPS_GATE_SOURCES:
            remove(path)
        return
    if event == "SessionEnd":
        remove(path)
        return
    if event != "UserPromptSubmit":
        return
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return
    print(f"lfg-state: {payload['session_id']} prompt={prompt[:300]!r}", file=sys.stderr)
    on_prompt(path, prompt)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"lfg-state: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
