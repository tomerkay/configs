#!/usr/bin/env python3
"""Stop hook: sends a reply back when a proposal in it is missing its Full Verdict shape.

Checks, on the reply's text outside code fences:
- a ❓ line with a Verdict line nested under it is a proposal: the Verdict carries one of the
  change calls, and a Change line with Evidence, Size and Difficulty, Why Yes and Why Not
  are nested too;
- a ❓ line flagged ⚠️ has a Verdict nested under it, since only a question whose yes changes
  something can warn;
- every Verdict line carries one of the calls, so a call in an old or misspelt shape never
  passes unchecked;
- a change-call Verdict line carries no Evidence, since its call is a judgement, and every other
  Verdict line carries one;
- a reply with a change-call Verdict anywhere carries a Change line, Size, Difficulty, Why
  Yes and Why Not somewhere, so a ❓ phrased as a preference question cannot shed them;
- the old shapes are sent back: a call as a tag on the ❓ line, a `VERDICT:` header, and an
  emoji before Why Yes or Why Not.

The calls are the ones the tkay-code skill's references/verdict.md defines.

A blocked reply is returned once: on the retry `stop_hook_active` is set and the hook stays
quiet, so it can never hold the session in a loop. A failure exits 1, which Claude Code
reports and ignores - this hook never stops a reply from ending on its own error.
`--selftest` runs the cases.
"""

import io
import json
import re
import sys

FENCE_RE = re.compile(r"^\s*(```|~~~)")
# The question number is bold by the rules, but a plain one must still be checked: matching
# only one spelling leaves every ❓ in the other unchecked.
QUESTION_NUMBER = r"(?:\*\*Q\d+\*\*|Q\d+)"
QUESTION_RE = re.compile(rf"^❓ {QUESTION_NUMBER} ")
# The variation selector after ⚖, ⚠, 🗑 and ⏸ is optional: both spellings render as the same
# symbol.
WARNING_QUESTION_RE = re.compile(rf"^❓ {QUESTION_NUMBER} ⚠️? ")
TAGGED_QUESTION_RE = re.compile(rf"^❓ {QUESTION_NUMBER} (⚠️? )?\*\*.+?\*\* \[")
CHANGE_CALL = r"(💯 No brainer|✅ Do it|⚖️? Close call|❌ Don't|😱 Hell NO)"
ANY_CALL = (r"(💯 No brainer|✅ Do it|⚖️? Close call|❌ Don't|😱 Hell NO"
            r"|✅ Ship it|👌 Fixed later|🔧 Needs change"
            r"|🪓 Split|📝 Reword|🔀 Squash into|🗑️? Drop|🔧 Add fix|⏸️? Leave for now)")
VERDICT_LINE_RE = re.compile(r"^\s*(Q\d+\. )?- \*\*Verdict:\*\* ")
KNOWN_VERDICT_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*Verdict:\*\* {ANY_CALL}\b")
CHANGE_VERDICT_RE = re.compile(rf"^\s*(Q\d+\. )?- \*\*Verdict:\*\* {CHANGE_CALL}")
EVIDENCE_RE = re.compile(r" · \*\*Evidence:\*\* ")
OLD_HEADER_RE = re.compile(r"^(Q\d+\. )?VERDICT: ")
OLD_WHY_RE = re.compile(r"^\s*- \S+ \*\*Why (Yes|Not)\?\*\*")
REQUIRED = ("**Change:**", "**Evidence:**", "**Size:**", "**Difficulty:**", "**Why Yes?**",
            "**Why Not?**")


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


def missing(lines):
    joined = "\n".join(lines)
    return [item for item in REQUIRED if item not in joined]


def question_problems(lines):
    found = []
    starts = [i for i, line in enumerate(lines) if QUESTION_RE.match(line)]
    for n, start in enumerate(starts):
        head = lines[start][:60]
        if TAGGED_QUESTION_RE.match(lines[start]):
            found.append(f"{head}... carries a tag on the line; the call goes on the nested "
                         "Verdict line")
            continue
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        nested = lines[start + 1:end]
        verdicts = [line for line in nested if VERDICT_LINE_RE.match(line)]
        if not verdicts:
            if WARNING_QUESTION_RE.match(lines[start]):
                found.append(f"{head}... is flagged ⚠️ but has no Verdict nested under it")
            continue
        if not any(CHANGE_VERDICT_RE.match(line) for line in verdicts):
            found.append(f"{head}... has a Verdict whose call is not one of the change calls")
            continue
        gaps = missing(nested)
        if gaps:
            found.append(f"{head}... has nothing nested for {', '.join(gaps)}")
    return found


def problems(text):
    lines = prose_lines(text)
    found = question_problems(lines)
    for line in lines:
        if VERDICT_LINE_RE.match(line) and not KNOWN_VERDICT_RE.match(line):
            found.append(f"{line.strip()[:60]}... carries no call, or one not in its "
                         "emoji-and-word shape")
        if CHANGE_VERDICT_RE.match(line) and EVIDENCE_RE.search(line):
            found.append(f"{line.strip()[:60]}... carries an Evidence; a change's call "
                         "takes none")
        elif (KNOWN_VERDICT_RE.match(line) and not CHANGE_VERDICT_RE.match(line)
              and not EVIDENCE_RE.search(line)):
            found.append(f"{line.strip()[:60]}... carries no Evidence on the Verdict line")
        if OLD_HEADER_RE.match(line):
            found.append(f"{line[:60]}... is the old VERDICT: header; the call goes on a "
                         "**Verdict:** list item")
        if OLD_WHY_RE.match(line):
            found.append(f"{line.strip()[:60]}... carries an emoji before Why Yes or Why Not")
    if any(CHANGE_VERDICT_RE.match(line) for line in lines):
        gaps = missing(lines)
        if gaps:
            found.append(f"a proposal's Full Verdict is in the reply but {', '.join(gaps)} is not")
    return found


def main():
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active"):
        return
    message = payload.get("last_assistant_message")
    if not isinstance(message, str):
        return
    found = problems(message)
    if not found:
        return
    reason = ("The reply breaks \"EVERY PROPOSAL CARRIES YOUR VERDICT ON IT\": "
              + "; ".join(found)
              + ". Resend only what is wrong, with nothing on the ❓ line but the decision and "
                "the question, and the Full Verdict as list items under it: **Verdict:** with "
                "the call alone for a change, the call and its Evidence for a CR verdict, "
                "**Change:** with Evidence, Size and Difficulty, "
                "then **Why Yes?** and **Why Not?** with no emoji before them.")
    print(json.dumps({"decision": "block", "reason": reason}))


def selftest():
    verdict = ("  - **Verdict:** ✅ Do it\n"
               "  - **Change:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n")
    whys = "  - **Why Yes?**\n    - a\n  - **Why Not?**\n    - b\n"
    good_question = ("Q1. The proposal\n\n"
                     "❓ Q1 **Split fixes**: is that the line you want?\n" + verdict + whys)
    cases = [
        ("full proposal shape", good_question, False),
        ("two proposals, both complete",
         good_question + "\n" + good_question.split("\n\n", 1)[1].replace("Q1", "Q2"), False),
        ("second of two proposals incomplete",
         good_question + "\n❓ Q2 **Y**: ok?\n  - **Verdict:** ❌ Don't · **Size:** small\n",
         True),
        ("proposal missing Why Not",
         "❓ Q1 **X**: ok?\n" + verdict.replace("✅ Do it", "⚖️ Close call")
         + "  - **Why Yes?**\n    - a\n", True),
        ("proposal with an Evidence on the Verdict line",
         "❓ Q1 **X**: ok?\n  - **Verdict:** ✅ Do it · **Evidence:** LIKELY\n"
         "  - **Change:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n"
         + whys, True),
        ("No brainer, full shape",
         good_question.replace("✅ Do it", "💯 No brainer"), False),
        ("Hell NO, full shape",
         good_question.replace("✅ Do it", "😱 Hell NO"), False),
        ("No brainer with an Evidence",
         good_question.replace("✅ Do it", "💯 No brainer · **Evidence:** CONFIDENT"),
         True),
        ("retired Strongly do it call",
         good_question.replace("✅ Do it", "💪✅ Strongly do it"), True),
        ("retired Strongly don't call",
         good_question.replace("✅ Do it", "❌❌ Strongly don't"), True),
        ("proposal with the retired How sure field on the Change line",
         good_question.replace("**Evidence:**", "**How sure:**"), True),
        ("commit verdict with the retired How sure field",
         "- **Verdict:** ✅ Ship it · **How sure:** CONFIDENT\n"
         "- **Commit:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n", True),
        ("commit verdict with no Evidence",
         "- **Verdict:** ✅ Ship it\n"
         "- **Commit:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n", True),
        ("proposal in the old one-line shape, no Change line",
         "❓ Q1 **X**: ok?\n  - **Verdict:** ✅ Do it · **Evidence:** CONFIDENT · **Size:** small"
         " · **Difficulty:** easy\n" + whys, True),
        ("Close call with no variation selector, full shape",
         good_question.replace("✅ Do it", "⚖ Close call"), False),
        ("call with no emoji", good_question.replace("✅ Do it", "Do it"), True),
        ("old uppercase call", good_question.replace("✅ Do it", "✅ DO IT"), True),
        ("commit call under a ❓", good_question.replace("✅ Do it", "✅ Ship it"), True),
        ("old tag on the ❓ line, full nest",
         good_question.replace("**Split fixes**:", "**Split fixes** [✅ DO IT]:"), True),
        ("old VERDICT header", "VERDICT: ✅ DO IT\n\n❓ Q1 **X**: ok?\n", True),
        ("old emoji before Why Yes",
         good_question.replace("- **Why Yes?**", "- 👍 **Why Yes?**"), True),
        ("plain question, no proposal", "❓ Q1 **Cluster**: which context do I read?\n", False),
        ("warning ❓, full shape", good_question.replace("❓ Q1 **", "❓ Q1 ⚠️ **"), False),
        ("warning ❓ without the variation selector, full shape",
         good_question.replace("❓ Q1 **", "❓ Q1 ⚠ **"), False),
        ("warning ❓ with no Verdict", "❓ Q1 ⚠️ **X**: ok?\n", True),
        ("Q-part Verdict above an untagged ❓, items nowhere",
         "Q1. - **Verdict:** ❌ Don't · **Size:** small\n\n❓ Q1 **X**: ok?\n", True),
        ("standalone proposal verdict with every field",
         "- **Verdict:** ⚖️ Close call\n"
         "- **Change:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n"
         "- **Why Yes?**\n  - a\n- **Why Not?**\n  - none\n", False),
        ("review verdicts with Commit and Fix lines, table rows and install question",
         "FINDINGS: 🔴 1 · 🟡 2\n\n"
         "- **Verdict:** 🔧 Needs change (hangs on timeout) · **Evidence:** CONFIDENT\n"
         "- **Commit:** **Evidence:** VERIFIED · **Size:** medium · **Difficulty:** hard\n"
         "- **Fix 🔴🟠:** add a client timeout · **Evidence:** LIKELY · **Size:** small · "
         "**Difficulty:** easy\n"
         "- **Fix 🟡⚪:** none\n- **Why Yes?**\n  - a\n- **Why Not?**\n  - none\n\n"
         "| 1 | `a1b2c3d` thing | 🔴 1 · 🟡 2 | 🔧 Needs change (hangs) |\n"
         "| | **Commit:** **Evidence:** VERIFIED · **Size:** medium · **Difficulty:** hard | "
         "**Fix 🔴🟠:** add a timeout · **Evidence:** LIKELY · **Size:** small · **Difficulty:** "
         "easy · **Fix 🟡⚪:** none | **Verdict:** **Evidence:** CONFIDENT |\n\n"
         "❓ Q1 Install it into `x` and commit?\n", False),
        ("Drop and Leave for now, with and without the variation selector",
         "- **Verdict:** 🗑 Drop · **Evidence:** CONFIDENT\n"
         "- **Verdict:** 🗑️ Drop · **Evidence:** CONFIDENT\n"
         "- **Verdict:** ⏸ Leave for now (out of scope) · **Evidence:** LIKELY\n"
         "- **Verdict:** ⏸️ Leave for now (out of scope) · **Evidence:** LIKELY\n", False),
        ("Split, Fixed later and Reword commit verdicts",
         "- **Verdict:** 🪓 Split (the guard, the rename) · **Evidence:** CONFIDENT\n"
         "- **Verdict:** 👌 Fixed later (by `a1b2c3d`) · **Evidence:** CONFIDENT\n"
         "- **Verdict:** 📝 Reword (subject claims a speedup) · **Evidence:** CONFIDENT\n",
         False),
        ("Needs change verdict with a reason",
         "- **Verdict:** 🔧 Needs change (crashes) · **Evidence:** CONFIDENT\n", False),
        ("bold question number, full shape",
         good_question.replace("❓ Q1 ", "❓ **Q1** "), False),
        ("bold question number, second of two proposals incomplete",
         good_question + "\n❓ **Q2** **Y**: ok?\n  - **Verdict:** ❌ Don't · **Size:** small\n",
         True),
        ("bold question number, warning ❓ with no Verdict", "❓ **Q1** ⚠️ **X**: ok?\n", True),
        ("bold question number, old tag on the ❓ line",
         good_question.replace("❓ Q1 **Split fixes**:", "❓ **Q1** **Split fixes** [✅ DO IT]:"),
         True),
        ("half-bold question number is not a question", "❓ **Q1 ⚠️ **X**: ok?\n", False),
        ("broken shape inside a code fence is an example",
         "```\nVERDICT: ✅ DO IT\n❓ Q1 **X** [✅ DO IT]: ok?\n  - 👍 **Why Yes?**\n```\n", False),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}: {problems(text)}")
    bad = "❓ Q1 **X**: ok?\n  - **Verdict:** ✅ Do it\n"
    for name, payload, expect_output in [
        ("retry is never blocked", {"stop_hook_active": True,
                                    "last_assistant_message": bad}, False),
        ("missing message is quiet", {"stop_hook_active": False}, False),
        ("bad reply is blocked", {"stop_hook_active": False,
                                  "last_assistant_message": bad}, True),
    ]:
        stdin, stdout = sys.stdin, sys.stdout
        sys.stdin, sys.stdout = io.StringIO(json.dumps(payload)), io.StringIO()
        try:
            main()
            out = sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = stdin, stdout
        if bool(out) != expect_output or (out and json.loads(out)["decision"] != "block"):
            ok = False
            print(f"FAIL {name}: output={out!r}")
    print("selftest: ok" if ok else "selftest: FAILED")
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    try:
        main()
    except Exception as exc:
        print(f"question-shape: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
