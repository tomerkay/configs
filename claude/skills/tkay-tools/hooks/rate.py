#!/usr/bin/env python3
"""PreToolUse hook on Bash: opens the call's `description` with what the command can
change, as command_parser rates it, so a permission prompt leads with the rating:

    <rating> · <description>

It never decides anything, and in auto mode it changes nothing: auto mode reviews a call
before the hooks run, and a hook that changes the input after that review risks the call
being refused, so a hook that asks there names the rating in its reason instead.
"""

import json
import re
import sys

from command_parser import AUTO_MODE, CONFIG_PATH, UNCLASSIFIED, classify_command, configure

# A rating the description already opens with is replaced, never stacked.
LABEL_RE = re.compile(
    r"^(?:🟢 READ|🟠 WRITE|🔵 RUNS CODE|🟣 UNCLASSIFIED|🔴 DANGER)\s*[·:|-]?\s*")


def rated(payload):
    """The hook's output for one call - its Bash input with the description rated - or
    None when the call is not a Bash command or runs in auto mode."""
    tool_input = payload.get("tool_input")
    if (payload.get("tool_name") != "Bash" or not isinstance(tool_input, dict)
            or not isinstance(tool_input.get("command"), str)
            or payload.get("permission_mode") == AUTO_MODE):
        return None
    # A bug in the parser rates the command unknown, never as a read.
    try:
        rating = classify_command(tool_input["command"])
    except Exception:
        rating = UNCLASSIFIED
    description = LABEL_RE.sub("", tool_input.get("description") or "").strip()
    updated = dict(tool_input)
    updated["description"] = f"{rating} · {description}" if description else rating
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}}


def main():
    configure(CONFIG_PATH)
    result = rated(json.load(sys.stdin))
    if result is not None:
        json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
