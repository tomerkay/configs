"""The assessment frame every assessment hook checks, shared by symlink between skills.

An assessment block starts at its Call line and runs to the next one. Each skill's hook owns
the blocks its own calls open and checks only those, so no block is checked twice when
several skills are loaded. This module holds what every block is checked for, whoever owns
it, and runs a hook on top of it; it is imported by its bare name from the hook's own folder.
"""

import io
import json
import re
import sys

FENCE_RE = re.compile(r"^\s*(```|~~~)")
# The variation selector after ⚖, 🗑 and ⏸ is optional: both spellings render as the same
# symbol.
CHANGE_CALL = r"(💪✅ Strongly do it|✅ Do it|⚖️? Close call|❌❌ Strongly don't|❌ Don't)"
CR_CALL = (r"(✅ Ship it|👌 Fixed later|🔧 Needs change|🪓 Split|📝 Reword|🔀 Squash into"
           r"|🗑️? Drop|✅ Merge it|🔧 Merge after fixes|✂️? Split first|⚖️? Close call|❌ Don't merge"
           r"|✅ Keep it|🔧 Needs fixes|✂️? Carve out|❌ Drop it|🔧 Add fix|⏸️? Leave for now"
           r"|🧪 Needs test|🧪 Merge after tests)")
# The retired Verdict label opens a block too, so whoever owns its call sends the label back.
CALL_LINE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* ")
CHANGE_CALL_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* {CHANGE_CALL}")
# A CR's ⚖️ Close call shares its words with a change's; `owned_by_cr` tells them apart by the
# Profile under it.
CR_CALL_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* {CR_CALL}")
CR_PROFILE_RE = re.compile(r"^\s*- \*\*(Commit|Bycatch|Fix [🔴🟠🟡⚪]+|Test 🧪):\*\*")
# A call is an emoji, then a word that opens with a capital and goes on in lower case, so
# "DO IT" or a bare "Do it" fails.
CALL_SHAPE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* [^\w\s*]+ [A-Z][a-z']")
EVIDENCE_RE = re.compile(r" · \*\*Evidence:\*\* ")
RETIRED_CALL_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* 💯 No brainer")
RETIRED_FIELD = "**How sure:**"
RETIRED_LABEL = "**Verdict:**"
RETIRED_BADGE = "(💯 No brainer)"
OLD_HEADER_RE = re.compile(r"^(Q\d+\. )?VERDICT: ")
OLD_WHY_RE = re.compile(r"^\s*- \S+ \*\*Why (Yes|Not)\?\*\*")


def prose_lines(text):
    lines = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


def split(lines):
    """The lines before the first Call line, and each block from a Call line to the next."""
    starts = [i for i, line in enumerate(lines) if CALL_LINE_RE.match(line)]
    if not starts:
        return lines, []
    blocks = [lines[s:e] for s, e in zip(starts, starts[1:] + [len(lines)])]
    return lines[:starts[0]], blocks


CLOSE_CALL_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*(Call|Verdict):\*\* ⚖️? Close call")


def owned_by_cr(block):
    """A block opened by a CR call; a Close call is the CR's only beside a CR Profile."""
    if CLOSE_CALL_RE.match(block[0]):
        return any(CR_PROFILE_RE.match(line) for line in block[1:])
    return bool(CR_CALL_RE.match(block[0]))


def stray_problems(lines):
    """What a line can break wherever it stands, in or out of a block."""
    found = []
    for line in lines:
        head = line.strip()[:60]
        if RETIRED_FIELD in line:
            found.append(f"{head}... carries the retired How sure field; it is Evidence")
        if RETIRED_BADGE in line:
            found.append(f"{head}... carries the retired 💯 badge; it is 🍰")
        if OLD_HEADER_RE.match(line):
            found.append(f"{line[:60]}... is the old VERDICT: header; the call goes on a "
                         "**Call:** list item")
        if OLD_WHY_RE.match(line):
            found.append(f"{head}... carries an emoji before Why Yes or Why Not")
    return found


def frame_problems(block):
    """What every assessment block is checked for, whoever owns it."""
    call = block[0]
    head = call.strip()[:60]
    found = []
    if RETIRED_LABEL in call:
        found.append(f"{head}... carries the retired Verdict label; it is Call")
    if RETIRED_CALL_RE.match(call):
        found.append(f"{head}... is the retired 💯 No brainer call; it is a (🍰 No brainer) "
                     "badge on a call")
    elif not CALL_SHAPE_RE.match(call):
        found.append(f"{head}... carries no call, or one not in its emoji-and-word shape")
    if EVIDENCE_RE.search(call):
        found.append(f"{head}... carries an Evidence; a call takes none")
    return found + stray_problems(block)


def run(problems, standard, shape):
    """The Stop hook around `problems(text)`: quiet on the retry, sends a reply back once."""
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return
    message = payload.get("last_assistant_message")
    if not isinstance(message, str):
        return
    found = problems(message)
    if found:
        reason = (f"The reply breaks {standard}: " + "; ".join(found)
                  + f". Resend only what is wrong, with {shape}.")
        print(json.dumps({"decision": "block", "reason": reason}))


def run_payload(problems, payload):
    """`run` on one payload, for a selftest: the decision printed, or empty."""
    stdin, stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = io.StringIO(json.dumps(payload)), io.StringIO()
    try:
        run(problems, "the standard", "the shape")
        return sys.stdout.getvalue()
    finally:
        sys.stdin, sys.stdout = stdin, stdout
