#!/usr/bin/env python3
"""Stop hook: sends a reply back when an assessment in it breaks references/assessment.md.

It owns every assessment block a CR call does not open - the blocks of the change calls and
of any call it does not know - and the lines outside every block. On those it checks the
frame `frame_checks.py` holds, and on top:
- a block whose call is not a change call is sent back, so a misspelt call never passes;
- the (🍰 No brainer) badge never follows ✅ Do it, ❌ Don't or ⚖️ Close call;
- a harm badge never follows a call on the other side: (🙌 Stops harm) no Don't call, and
  (😱 Does harm) no Do it call;
- a change call is followed, before the next Call line, by a Change line with Evidence, Size
  and Difficulty, and by Why Yes and Why Not - or, for an alternative, Gains and Losses - so
  one complete assessment cannot cover for another;
- a count of Equivalent proposals stands only beside a Better proposal;
- a Better proposal's call outranks its proposal's, and an Equivalent's matches it, both
  compared on the bare call, so a reason or a badge beside either changes nothing.

A CR's blocks are left to the review skill's own hook, so no block is checked twice.

A blocked reply is returned once: on the retry `stop_hook_active` is set and the hook stays
quiet, so it can never hold the session in a loop. A failure exits 1, which Claude Code
reports and ignores - this hook never stops a reply from ending on its own error.
`--selftest` runs the cases.
"""

import re
import sys

# The shared module sits beside this script; no bytecode cache is left in the skill.
sys.dont_write_bytecode = True
import frame_checks as frame  # noqa: E402

BADGE = " (🍰 No brainer)"
# ✅ Do it, ❌ Don't and every ⚖️ Close call never take the badge: an obvious case is lopsided,
# and a close call is never obvious.
NO_BADGE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* (✅ Do it|❌ Don't|⚖️? Close call)")
# Each harm badge and the calls it never follows: those on the other side of ⚖️ Close call.
HARM_BADGES = {
    " (🙌 Stops harm)": re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* (❌❌ Strongly don't|❌ Don't)"),
    " (😱 Does harm)": re.compile(r"^\s*(Q\d+\. )?- \*\*Call:\*\* (💪✅ Strongly do it|✅ Do it)"),
}
COUNTED_EQUIVALENT_RE = re.compile(r"\*\*\d+ Equivalent proposals? (is|are) possible\*\*")
BETTER_RE = re.compile(r"\*\*\d+ Better proposals?:\*\*")
WRITTEN_OUT_RE = re.compile(r"\*\*\d+ (Better|Equivalent) proposals?:\*\*")
CALL_WORDS_RE = re.compile(rf"\*\*Call:\*\* {frame.CHANGE_CALL}")
# The change calls from the strongest yes to the strongest no; the variation selector after ⚖
# is dropped before the lookup.
RANK = {"💪✅ Strongly do it": 4, "✅ Do it": 3, "⚖ Close call": 2, "❌ Don't": 1,
        "❌❌ Strongly don't": 0}
PROFILE = ("**Change:**", "**Evidence:**", "**Size:**", "**Difficulty:**")
WHYS = ("**Why Yes?**", "**Why Not?**")
GAINS = ("**Gains:**", "**Losses:**")
STANDARD = "the assessment standard, references/assessment.md"
SHAPE = ("the Full Assessment as list items: **Call:** with the call alone, **Change:** with "
         "Evidence, Size and Difficulty, then **Why Yes?** and **Why Not?** with no emoji "
         "before them")


def missing(lines):
    joined = "\n".join(lines)
    gaps = [item for item in PROFILE if item not in joined]
    if not all(item in joined for item in GAINS):
        gaps += [item for item in WHYS if item not in joined]
    return gaps


def counted_equivalents(lines):
    found = []
    for k, line in enumerate(lines):
        if not COUNTED_EQUIVALENT_RE.search(line):
            continue
        # The count is a sibling of its proposal's Call line: the nearest Call line above it
        # at the same indent or shallower opens the proposal it belongs to.
        indent = len(line) - len(line.lstrip())
        start = next((i for i in range(k - 1, -1, -1) if frame.CALL_LINE_RE.match(lines[i])
                      and len(lines[i]) - len(lines[i].lstrip()) <= indent), 0)
        if not any(BETTER_RE.search(other) for other in lines[start:k]):
            found.append(f"{line.strip()[:60]}... counts Equivalent proposals with no Better "
                         "proposal beside them; with no Better, each Equivalent is written out")
    return found


def indent_of(line):
    return len(line) - len(line.lstrip())


def rank(line):
    match = CALL_WORDS_RE.search(line)
    return RANK[match.group(1).replace("⚖️", "⚖")] if match else None


def alternative_calls(lines):
    found = []
    for k, line in enumerate(lines):
        field = WRITTEN_OUT_RE.search(line)
        if not field:
            continue
        indent = indent_of(line)
        # The proposal is the nearest Call line above the field at its indent or shallower;
        # the field's alternatives are the Call lines nested under it.
        above = next((lines[i] for i in range(k - 1, -1, -1) if frame.CALL_LINE_RE.match(lines[i])
                      and indent_of(lines[i]) <= indent), None)
        proposal = rank(above) if above else None
        if proposal is None:
            continue
        for other in lines[k + 1:]:
            if other.strip() and indent_of(other) <= indent:
                break
            alternative = rank(other) if frame.CALL_LINE_RE.match(other) else None
            if alternative is None:
                continue
            if field.group(1) == "Better" and alternative <= proposal:
                found.append(f"{other.strip()[:60]}... is a Better proposal whose call does not "
                             "outrank the proposal's; a worse call is counted as Lesser")
            if field.group(1) == "Equivalent" and alternative != proposal:
                found.append(f"{other.strip()[:60]}... is an Equivalent proposal with a call "
                             "other than the proposal's")
    return found


def problems(text):
    lines = frame.prose_lines(text)
    outside, blocks = frame.split(lines)
    found = frame.stray_problems(outside)
    for block in blocks:
        if frame.owned_by_cr(block):
            continue
        found += frame.frame_problems(block)
        call = block[0]
        head = call.strip()[:60]
        if not frame.CHANGE_CALL_RE.match(call):
            if frame.CALL_SHAPE_RE.match(call) and not frame.RETIRED_CALL_RE.match(call):
                found.append(f"{head}... carries a call that is not one of the change calls")
            continue
        if BADGE in call and NO_BADGE_RE.match(call):
            found.append(f"{head}... carries the No brainer badge on a call that takes none")
        for badge, wrong_side_re in HARM_BADGES.items():
            if badge in call and wrong_side_re.match(call):
                found.append(f"{head}... carries{badge} on a call on the other side")
        gaps = missing(block[1:])
        if gaps:
            found.append(f"{head}... has nothing under it for {', '.join(gaps)}")
    return found + counted_equivalents(lines) + alternative_calls(lines)


def selftest():
    full = ("- **Call:** ✅ Do it\n"
            "- **Change:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n"
            "- **Why Yes?**\n  - a\n- **Why Not?**\n  - b\n")
    better = ("- **1 Better proposal:**\n  - **1. other**\n"
              "    - **Call:** 💪✅ Strongly do it\n"
              "    - **Change:** **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy\n")
    judged = "    - **Gains:**\n      - a\n    - **Losses:**\n      - b\n"

    def alternative(field, call):
        return (f"- **1 {field} proposal:**\n  - **1. other**\n    - **Call:** {call}\n"
                "    - **Change:** **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy\n"
                + judged)

    commit = ("- **Call:** ✅ Ship it\n"
              "- **Commit:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n")
    cases = [
        ("full assessment", full, False),
        ("missing Why Not", full.split("- **Why Not?**")[0], True),
        ("Evidence on the Call line",
         full.replace("✅ Do it", "✅ Do it · **Evidence:** LIKELY"), True),
        ("Strongly do it", full.replace("✅ Do it", "💪✅ Strongly do it"), False),
        ("Strongly don't", full.replace("✅ Do it", "❌❌ Strongly don't"), False),
        ("retired Hell yes call", full.replace("✅ Do it", "🙌 Hell yes"), True),
        ("retired Hell NO call", full.replace("✅ Do it", "😱 Hell NO"), True),
        ("Stops harm on Do it", full.replace("✅ Do it", "✅ Do it (🙌 Stops harm)"), False),
        ("Stops harm on Close call", full.replace("✅ Do it", "⚖️ Close call (🙌 Stops harm)"),
         False),
        ("Stops harm on Don't", full.replace("✅ Do it", "❌ Don't (🙌 Stops harm)"), True),
        ("Does harm on Strongly don't",
         full.replace("✅ Do it", "❌❌ Strongly don't (😱 Does harm)"), False),
        ("Does harm on Close call", full.replace("✅ Do it", "⚖️ Close call (😱 Does harm)"),
         False),
        ("Does harm on Strongly do it",
         full.replace("✅ Do it", "💪✅ Strongly do it (😱 Does harm)"), True),
        ("harm badge and No brainer after a reason",
         full.replace("✅ Do it",
                      "💪✅ Strongly do it (stops the leak) (🙌 Stops harm) (🍰 No brainer)"),
         False),
        ("Close call with no variation selector", full.replace("✅ Do it", "⚖ Close call"),
         False),
        ("badge on Strongly do it",
         full.replace("✅ Do it", "💪✅ Strongly do it (🍰 No brainer)"), False),
        ("badge on Strongly don't",
         full.replace("✅ Do it", "❌❌ Strongly don't (🍰 No brainer)"), False),
        ("badge on Do it", full.replace("✅ Do it", "✅ Do it (🍰 No brainer)"), True),
        ("badge on Don't", full.replace("✅ Do it", "❌ Don't (🍰 No brainer)"), True),
        ("badge on Close call", full.replace("✅ Do it", "⚖️ Close call (🍰 No brainer)"), True),
        ("retired 💯 badge",
         full.replace("✅ Do it", "💪✅ Strongly do it (💯 No brainer)"), True),
        ("retired No brainer call", full.replace("✅ Do it", "💯 No brainer"), True),
        ("retired How sure field", full.replace("**Evidence:**", "**How sure:**"), True),
        ("old one-line shape, no Change line",
         "- **Call:** ✅ Do it · **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** "
         "easy\n- **Why Yes?**\n  - a\n- **Why Not?**\n  - b\n", True),
        ("call with no emoji", full.replace("✅ Do it", "Do it"), True),
        ("old uppercase call", full.replace("✅ Do it", "✅ DO IT"), True),
        ("an unknown call", full.replace("✅ Do it", "✅ Approve it"), True),
        ("emoji before Why Yes", full.replace("- **Why Yes?**", "- 👍 **Why Yes?**"), True),
        ("a CR's block is the review hook's",
         commit.replace("✅ Ship it", "✅ Ship it · **Evidence:** CONFIDENT"), False),
        ("a CR's Close call is the review hook's",
         commit.replace("✅ Ship it", "⚖️ Close call · **Evidence:** CONFIDENT"), False),
        ("a CR's Needs test block is the review hook's",
         commit.replace("✅ Ship it", "🧪 Needs test (accepted untested) (🙌 Stops harm)"), False),
        ("a CR's Missing description block is the review hook's",
         commit.replace("✅ Ship it", "📭 Missing description"), False),
        ("broken shape inside a code fence is an example",
         "```\n- **Call:** ✅ Do it · **Evidence:** LIKELY\n```\n", False),
        ("plain text", "no assessment here\n", False),
        ("second of two assessments incomplete",
         full + "- **Call:** ❌ Don't\n- **Change:** **Evidence:** LIKELY\n", True),
        ("first of two assessments incomplete, second complete",
         "- **Call:** ❌ Don't\n" + full, True),
        ("a Better alternative judged by Gains and Losses",
         full + better + "    - **Gains:**\n      - a\n    - **Losses:**\n      - b\n", False),
        ("an alternative with no Gains or Losses", full + better, True),
        ("Equivalent counted with no Better beside it",
         full + "- **1 Equivalent proposal is possible**\n", True),
        ("Equivalent counted beside a Better",
         full + better + "    - **Gains:**\n      - a\n    - **Losses:**\n      - b\n"
         "- **2 Equivalent proposals are possible**\n", False),
        # The case that taught it: a scaling proposal judged ✅ Do it, with a "Better" way
        # written out under it that its own author called ❌ Don't.
        ("a Better proposal whose call ranks below the proposal's",
         full + "- **1 Better proposal:**\n"
         "  - **1. Scale through the scale subresource with a version precondition**\n"
         "    - **Call:** ❌ Don't\n"
         "    - **Change:** **Evidence:** 50-50 · **Size:** large · **Difficulty:** hard\n"
         "    - **Gains:**\n      - atomic by construction, the way the autoscaler works\n"
         "    - **Losses:**\n      - a rewrite of the step for a gap it cannot hit\n", True),
        ("a Better proposal with the same call", full + alternative("Better", "✅ Do it"), True),
        # The case that taught both: a guard proposed with a Why Not its author had not
        # checked, and the work that would settle it written as a "Better proposal".
        ("a Why Not point that says it was not checked",
         full.replace("  - b", "  - the split may give a cell one side only; I haven't checked "
                               "whether it can"), True),
        ("a Why Not point proved by what was checked",
         full.replace("  - b", "  - none (checked: every caller of the split)"), False),
        ("an alternative that is an addition to the proposal",
         full + "- **1 Better proposal:**\n"
         "  - **1. Also make the split never give a cell one side alone**\n"
         "    - **Call:** 💪✅ Strongly do it\n"
         "    - **Change:** **Evidence:** LIKELY · **Size:** medium · **Difficulty:** hard\n"
         "    - **Gains:**\n      - removes the permanent wait\n"
         "    - **Losses:**\n      - changes how replicas are placed\n", True),
        ("leaving it as is, the Better proposal under a Don't",
         full.replace("✅ Do it", "❌ Don't")
         + "- **1 Better proposal:**\n  - **1. Leave everything as is**\n"
         "    - **Call:** ✅ Do it\n"
         "    - **Change:** **Evidence:** CONFIDENT · **Size:** small · **Difficulty:** super easy\n"
         + judged, False),
        ("an Equivalent proposal with the same call",
         full + alternative("Equivalent", "✅ Do it"), False),
        ("an Equivalent proposal with another call",
         full + alternative("Equivalent", "⚖️ Close call"), True),
        ("an Equivalent whose call differs only by a badge and a reason",
         full.replace("✅ Do it", "⚖️ Close call (stops the leak) (🙌 Stops harm)")
         + alternative("Equivalent", "⚖ Close call"), False),
        # The cases that taught it: an install question whose Why Not was the files going live,
        # and a move whose Why Not was the root file growing.
        ("a Why Not point that is the change going live",
         full.replace("  - b", "  - **1.** The root `CLAUDE.md` and the skills are live, so any "
                      "session picks up the new text as soon as it's copied in."), True),
        ("a Why Not point that is the change's size",
         full.replace("  - b", "  - **1.** The root `CLAUDE.md` grows by a section."), True),
        ("a Why Not point on a queue that grows", full.replace(
            "  - b", "  - the retry queue grows without bound while the API is down"), False),
        ("a Why Yes point may say the change goes live",
         full.replace("  - a", "  - the fix goes live on the next restart"), False),
        ("an empty Why Not with its check",
         full.replace("  - b", "  - none (checked: every caller keeps its decision)"), False),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}: {problems(text)}")
    bad = "- **Call:** ✅ Do it\n"
    for name, payload, expect_output in [
        ("retry is never blocked", {"stop_hook_active": True,
                                    "last_assistant_message": bad}, False),
        ("missing message is quiet", {"stop_hook_active": False}, False),
        ("bad reply is blocked", {"stop_hook_active": False,
                                  "last_assistant_message": bad}, True),
    ]:
        if bool(frame.run_payload(problems, payload)) != expect_output:
            ok = False
            print(f"FAIL {name}")
    print("selftest: ok" if ok else "selftest: FAILED")
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    try:
        frame.run(problems, STANDARD, SHAPE)
    except Exception as exc:
        print(f"assessment-shape: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
