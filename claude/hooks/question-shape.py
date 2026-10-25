#!/usr/bin/env python3
"""Stop hook: sends a reply back when a proposal in it is missing its verdict shape.

Three checks, on the reply's text outside code fences:
- a ❓ line carrying a verdict tag has Size, Difficulty, Why Yes and Why Not nested under it;
- a ❓ line flagged ⚠️ carries a verdict tag, since only a question whose yes changes something
  can warn;
- a reply that opens a proposal VERDICT block carries Size, Difficulty, Why Yes and Why Not
  somewhere, so a ❓ phrased as a preference question cannot shed them.

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
QUESTION_RE = re.compile(r"^❓ Q\d+ ")
# The variation selector after ⚖ and ⚠ is optional: both spellings render as the same symbol.
WARNING_QUESTION_RE = re.compile(r"^❓ Q\d+ ⚠️? ")
TAGGED_QUESTION_RE = re.compile(
    r"^❓ Q\d+ (⚠️? )?\*\*.+?\*\* \[(✅|⚖️?|❌) (VERIFIED|CONFIDENT|LIKELY|50-50)\]")
# Unindented only: a review's branch summary nests its verdicts under bullets.
PROPOSAL_VERDICT_RE = re.compile(
    r"^(Q\d+\. )?VERDICT: (✅ DO IT|⚖️? JUDGEMENT CALL|❌ DON'T) — ")
REQUIRED = ("**Size:**", "**Difficulty:**", "Why Yes?", "Why Not?")


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


def problems(text):
    lines = prose_lines(text)
    found = []
    starts = [i for i, line in enumerate(lines) if QUESTION_RE.match(line)]
    for n, start in enumerate(starts):
        if not TAGGED_QUESTION_RE.match(lines[start]):
            if WARNING_QUESTION_RE.match(lines[start]):
                found.append(f"{lines[start][:60]}... is flagged ⚠️ but carries no verdict tag")
            continue
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        gaps = missing(lines[start + 1:end])
        if gaps:
            found.append(f"{lines[start][:60]}... has nothing nested for {', '.join(gaps)}")
    if any(PROPOSAL_VERDICT_RE.match(line) for line in lines):
        gaps = missing(lines)
        if gaps:
            found.append(f"a proposal VERDICT block is in the reply but {', '.join(gaps)} is not")
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
    reason = ("The reply breaks \"EVERY PROPOSAL OPENS WITH YOUR VERDICT ON IT\": "
              + "; ".join(found)
              + ". Resend only the ❓ block, with the verdict tag on the line and Size, "
                "Difficulty, Why Yes and Why Not as list items under it.")
    print(json.dumps({"decision": "block", "reason": reason}))


def selftest():
    good_question = (
        "VERDICT: ✅ DO IT — CONFIDENT\nDoubt: x\n\n"
        "❓ Q1 **Split fixes** [✅ CONFIDENT]: is that the line you want?\n"
        "  - **Size:** small · **Difficulty:** easy\n"
        "  - 👍 **Why Yes?**\n    - a\n  - 👎 **Why Not?**\n    - b\n")
    cases = [
        ("untagged ❓ under a proposal with no Why Yes or Why Not",
         "VERDICT: ✅ DO IT — CONFIDENT\n**Difficulty:** easy\nDoubt: x\n\n"
         "❓ Q1 **Split fixes**: is that the line you want?\n", True),
        ("tagged ❓ with nothing nested", "❓ Q1 **Split fixes** [✅ LIKELY]: ok?\n", True),
        ("tagged ❓ missing only Why Not",
         "❓ Q1 **X** [⚖️ 50-50]: ok?\n  - **Size:** small · **Difficulty:** easy\n"
         "  - 👍 **Why Yes?**\n    - a\n", True),
        ("Q-part heading verdict, items nowhere",
         "Q1. VERDICT: ❌ DON'T — LIKELY\n\n❓ Q1 **X**: ok?\n", True),
        ("full proposal shape", good_question, False),
        ("two tagged ❓, both complete", good_question + "\n" + good_question.split("\n\n", 1)[1],
         False),
        ("second of two tagged ❓ incomplete",
         good_question + "\n❓ Q2 **Y** [✅ VERIFIED]: ok?\n", True),
        ("plain question, no proposal", "❓ Q1 **Cluster**: which context do I read?\n", False),
        ("tagged ❓ with ⚖ and no variation selector, nothing nested",
         "❓ Q1 **X** [⚖ LIKELY]: ok?\n", True),
        ("VERDICT block with ⚖ and no variation selector, items nowhere",
         "VERDICT: ⚖ JUDGEMENT CALL — LIKELY\n\n❓ Q1 **X**: ok?\n", True),
        ("warning ❓, full shape", good_question.replace("❓ Q1 **", "❓ Q1 ⚠️ **"), False),
        ("warning ❓ without the variation selector, full shape",
         good_question.replace("❓ Q1 **", "❓ Q1 ⚠ **"), False),
        ("warning ❓ with nothing nested", "❓ Q1 ⚠️ **X** [✅ LIKELY]: ok?\n", True),
        ("warning ❓ with no verdict tag", "❓ Q1 ⚠️ **X**: ok?\n", True),
        ("review verdicts and install question",
         "VERDICT: ✅ NO REAL ISSUES — 0 MUST HAVE — SHIP IT\n\n"
         "- thing\n  VERDICT: ✅ DO IT — CONFIDENT\n\n"
         "❓ Q1 Install it into `x` and commit?\n", False),
        ("broken shape inside a code fence is an example",
         "```\nVERDICT: ✅ DO IT — LIKELY\n❓ Q1 **X** [✅ LIKELY]: ok?\n```\n", False),
        ("proposal with items under the VERDICT block and no ❓",
         "VERDICT: ⚖️ JUDGEMENT CALL — LIKELY\n**Size:** small · **Difficulty:** easy\n"
         "- 👍 **Why Yes?**\n  - a\n- 👎 **Why Not?**\n  - none\n", False),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}")
    for name, payload, expect_output in [
        ("retry is never blocked", {"stop_hook_active": True,
                                    "last_assistant_message": "❓ Q1 **X** [✅ LIKELY]: ok?"}, False),
        ("missing message is quiet", {"stop_hook_active": False}, False),
        ("bad reply is blocked", {"stop_hook_active": False,
                                  "last_assistant_message": "❓ Q1 **X** [✅ LIKELY]: ok?"}, True),
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
