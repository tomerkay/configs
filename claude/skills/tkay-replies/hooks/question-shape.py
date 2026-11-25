#!/usr/bin/env python3
"""Stop hook: sends a reply back when a ❓ line in it breaks references/questions.md.

Checks, on the reply's text outside code fences:
- no ❓ line carries a ⚠️: a risk is named in the judgement under it;
- no ❓ line carries a tag in brackets after its decision: a judgement nests under the line.

A blocked reply is returned once: on the retry `stop_hook_active` is set and the hook stays
quiet, so it can never hold the session in a loop. A failure exits 1, which Claude Code
reports and ignores - this hook never stops a reply from ending on its own error.
`--selftest` runs the cases.
"""

import io
import json
import re
import sys

# The shared module sits beside this script; no bytecode cache is left in the skill.
sys.dont_write_bytecode = True
import frame_checks as frame  # noqa: E402

# The number is bold by the rules, but a plain one must still be checked: matching only one
# spelling leaves every ❓ in the other unchecked.
QUESTION_NUMBER = r"(?:\*\*Q\d+\*\*|Q\d+)"
# The variation selector after ⚠ is optional: both spellings render as the same symbol.
WARNING_RE = re.compile(rf"^\s*❓ {QUESTION_NUMBER} ⚠️? ")
TAGGED_RE = re.compile(rf"^\s*❓ {QUESTION_NUMBER} (⚠️? )?\*\*.+?\*\* \[")


def problems(text):
    found = []
    for line in frame.prose_lines(text):
        head = line.strip()[:60]
        if WARNING_RE.match(line):
            found.append(f"{head}... carries a ⚠️; a risk goes in the judgement under it")
        if TAGGED_RE.match(line):
            found.append(f"{head}... carries a tag on the line; the judgement nests under it")
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
    reason = ("The reply breaks the tkay-replies question shape, references/questions.md: "
              + "; ".join(found)
              + ". " + frame.CORRECTION + " A corrected ❓ line holds nothing but the "
                "decision and the question.")
    print(json.dumps({"decision": "block", "reason": reason}))


def selftest():
    good = "❓ Q1 **Split fixes**: is that the line you want?\n  - **Call:** ✅ Do it\n"
    cases = [
        ("plain line", good, False),
        ("bold number", good.replace("❓ Q1 ", "❓ **Q1** "), False),
        ("question, nothing nested", "❓ Q1 **Cluster**: which context do I read?\n", False),
        ("warning", good.replace("❓ Q1 **", "❓ Q1 ⚠️ **"), True),
        ("warning without the variation selector", good.replace("❓ Q1 **", "❓ Q1 ⚠ **"),
         True),
        ("warning, bold number", "❓ **Q1** ⚠️ **X**: ok?\n", True),
        ("tag on the line", good.replace("**Split fixes**:", "**Split fixes** [✅ DO IT]:"),
         True),
        ("tag on the line, bold number",
         good.replace("❓ Q1 **Split fixes**:", "❓ **Q1** **Split fixes** [✅ DO IT]:"), True),
        ("half-bold number is not a ❓ line", "❓ **Q1 ⚠️ **X**: ok?\n", False),
        ("indented ❓ line", "   ❓ Q2 ⚠️ **X**: ok?\n", True),
        ("broken shape inside a code fence is an example",
         "```\n❓ Q1 ⚠️ **X** [✅ DO IT]: ok?\n```\n", False),
        ("a fence line inside a longer fence keeps the block closed to the prose after it",
         "````\n```\n````\n❓ Q1 ⚠️ **X**: ok?\n", True),
        ("a block opened on a list item's line ends at its closing line",
         "1. ```bash\n   ls\n   ```\n❓ Q1 ⚠️ **X**: ok?\n", True),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}: {problems(text)}")
    bad = "❓ Q1 ⚠️ **X**: ok?\n"
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
