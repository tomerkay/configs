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
CR_CALL = (r"(✅ Ship it|👌 Fixed later|🔧 Needs change|🪓 Split|📝 Reword|📭 Missing description"
           r"|🔀 Squash into"
           r"|🗑️? Drop|✅ Merge it|🔧 Merge after fixes|✂️? Split first|⚖️? Close call|❌ Don't merge"
           r"|✅ Keep it|🔧 Needs fixes|✂️? Carve out|❌ Drop it|🔧 Add fix|⏸️? Leave for now"
           r"|🧪 Needs test|🧪 Merge after tests|⏳ Finish the work first"
           r"|🙋 Needs your call|🙋 Merge after your call"
           r"|✅ Build it|🔧 Build after fixes|🧪 Build after a spike|❌ Back to design)")
CALL_LINE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* ")
CHANGE_CALL_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*Call:\*\* {CHANGE_CALL}")
# A CR's ⚖️ Close call shares its words with a change's; `owned_by_cr` tells them apart by the
# Profile under it.
CR_CALL_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*Call:\*\* {CR_CALL}")
CR_PROFILE_RE = re.compile(r"^\s*- \*\*(Commit|Bycatch|Fix [🔴🟠🟡⚪]+|Test 🧪):\*\*")
# A call is an emoji, then a word that opens with a capital and goes on in lower case, so
# "DO IT" or a bare "Do it" fails.
CALL_SHAPE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* [^\w\s*]+ [A-Z][a-z']")
EVIDENCE_RE = re.compile(r" · \*\*Evidence:\*\* ")
RETIRED_CALL_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* 💯 No brainer")
RETIRED_FIELD = "**How sure:**"
RETIRED_BADGE = "(💯 No brainer)"
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


CLOSE_CALL_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* ⚖️? Close call")


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
        if OLD_WHY_RE.match(line):
            found.append(f"{head}... carries an emoji before Why Yes or Why Not")
    return found


def frame_problems(block):
    """What every assessment block is checked for, whoever owns it."""
    call = block[0]
    head = call.strip()[:60]
    found = []
    if RETIRED_CALL_RE.match(call):
        found.append(f"{head}... is the retired 💯 No brainer call; it is a (🍰 No brainer) "
                     "badge on a call")
    elif not CALL_SHAPE_RE.match(call):
        found.append(f"{head}... carries no call, or one not in its emoji-and-word shape")
    if EVIDENCE_RE.search(call):
        found.append(f"{head}... carries an Evidence; a call takes none")
    return (found + stray_problems(block) + padded_why_not(block) + unchecked_why_not(block)
            + additions(block))


# A Why Not point that is the change taking effect, or its size - the first two of the four
# tests in references/assessment.md. It matches wordings, not meaning: "grows" counts only
# after a file or a section, so a queue that grows - a real hazard - passes.
PADDED_WHY_NOT_RE = re.compile(
    r"\b(goes live|go live|(is|are) live\b|live the moment|picks? up the (new|change)"
    r"|takes? effect|as soon as (it|they)\S* (is |are )?(copied|saved|installed)"
    r"|one more (section|file|line|rule|commit))"
    r"|(root|file|section|skill|doc|\.md`?)\s+grows", re.IGNORECASE)


def why_not_points(block):
    """The lines nested under a block's Why Not label."""
    points = []
    for k, line in enumerate(block):
        if "**Why Not?**" not in line:
            continue
        indent = len(line) - len(line.lstrip())
        for other in block[k + 1:]:
            if not other.strip():
                continue
            if len(other) - len(other.lstrip()) <= indent:
                break
            points.append(other)
    return points


def padded_why_not(block):
    return [f"{point.strip()[:60]}... is a Why Not point that is the change taking effect or "
            "its size; cut it, and an empty list says none (checked: <what was checked>)"
            for point in why_not_points(block) if PADDED_WHY_NOT_RE.search(point)]


# A Why Not point that admits it was never checked. "none (checked: ...)" is the proof of an
# empty list, so "checked" alone is not the mark: the negation is.
UNCHECKED_RE = re.compile(
    r"\b(have ?n[o']t|did ?n[o']t|could ?n[o']t|not yet) (checked|verified|tested|traced)\b",
    re.IGNORECASE)


def unchecked_why_not(block):
    return [f"{point.strip()[:60]}... is a Why Not point that says it was not checked; check "
            "it before the assessment, or say what checking it costs"
            for point in why_not_points(block) if UNCHECKED_RE.search(point)]


# An alternative that opens with "Also" adds to the proposal, where an alternative replaces it.
ADDITION_RE = re.compile(r"^\s*- \*\*\d+\. (Also|Additionally|In addition|Plus)\b", re.IGNORECASE)


def additions(block):
    return [f"{line.strip()[:60]}... is work done as well as the proposal, not another way to "
            "do it; it is a proposal of its own, on a ❓ line of its own"
            for line in block if ADDITION_RE.match(line)]


# What a session sends after a reply is sent back: the changed lines alone. The reply it
# corrects is already on my screen, so printing its block again shows me the same paragraph
# twice.
CORRECTION = ("Reply with the correction alone: one line saying what was wrong, then only the "
              "lines that change, each under the Q number, row or heading it belongs to. Do not "
              "print the block or the table again: the rest of the reply stands as it was read.")


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
                  + ". " + CORRECTION + f" A corrected line reads as {shape}.")
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
