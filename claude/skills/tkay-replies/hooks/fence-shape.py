#!/usr/bin/env python3
"""Stop hook: sends a reply back when one of its code fences breaks references/before-and-after.md.

Reads the reply's fences the way markdown does - a fence closes on the first line of the same
character, at least as long and with nothing after it, indented at most three spaces past the
block it sits in - and finds two breaks:
- a fence that closes at another indent than it opened at: the closing line was content, such
  as a diff's context line holding a fence, and every fence after it flips;
- a reply that ends inside an open fence, which an early close leaves behind.

A blocked reply is returned once: on the retry `stop_hook_active` is set and the hook stays
quiet, so it can never hold the session in a loop. A failure exits 1, which Claude Code
reports and ignores - this hook never stops a reply from ending on its own error.
`--selftest` runs the cases.
"""

import io
import json
import re
import sys

FENCE_RE = re.compile(r"^( *)(`{3,}|~{3,})(.*)$")
# A fence may open on a list item's marker line; its indent is then the item's content indent.
ITEM_FENCE_RE = re.compile(r"^( *(?:[-*+]|\d{1,9}[.)]) +)(`{3,}|~{3,})(.*)$")
# A closing fence may sit up to three spaces past its block's indent, which a fence in a list
# item does not tell; reading three either way of the opener covers both.
CLOSE_SLACK = 3


def closes(line, opener_indent, opener_fence):
    match = FENCE_RE.match(line)
    if not match:
        return False
    indent, fence, rest = match.groups()
    return (fence[0] == opener_fence[0] and len(fence) >= len(opener_fence)
            and not rest.strip() and abs(len(indent) - opener_indent) <= CLOSE_SLACK)


def problems(text):
    """The first break only: every fence after it flips, so later ones are its echo."""
    opener = None
    for number, line in enumerate(text.splitlines(), start=1):
        if opener is None:
            match = FENCE_RE.match(line) or ITEM_FENCE_RE.match(line)
            # A backtick fence's info string holds no backtick, so "```x```" is inline code.
            if match and not (match.group(2)[0] == "`" and "`" in match.group(3)):
                opener = (number, len(match.group(1)), match.group(2))
            continue
        opened_at, indent, fence = opener
        if closes(line, indent, fence):
            closing_indent = len(line) - len(line.lstrip(" "))
            if closing_indent != indent:
                return [f"the fence opened on line {opened_at} closes on line {number}, "
                        f"{closing_indent} spaces in where it opened at {indent}: that line "
                        "is content, so the block needs a longer fence"]
            opener = None
    if opener is not None:
        return [f"the fence opened on line {opener[0]} is never closed"]
    return []


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
    reason = ("The reply breaks the tkay-replies fence rule, references/before-and-after.md: "
              + "; ".join(found)
              + ". Everything after the break rendered as raw text, so reply with one line "
                "saying a fence broke, then print again everything from the broken block to "
                "the end of the reply, each block fenced longer than any fence line it holds.")
    print(json.dumps({"decision": "block", "reason": reason}))


def selftest():
    ticks = "`" * 3
    four = "`" * 4
    cases = [
        ("one block", f"text\n{ticks}diff\n-a\n+b\n{ticks}\nmore\n", False),
        ("tilde block", "~~~\nx\n~~~\n", False),
        ("block in a list item", f"- **1.** x\n  {ticks}\n  y\n  {ticks}\n", False),
        ("longer fence holds a fence line", f"{four}diff\n {ticks}\n-a\n{four}\n", False),
        ("tilde fence holds a backtick line", f"~~~\n {ticks}\n~~~\n", False),
        ("a line deeper than the slack is content", f"{ticks}\n    {ticks}\n{ticks}\n", False),
        ("a fence line with an info string is content", f"{ticks}\n{ticks}python\n{ticks}\n",
         False),
        ("inline code on its own line is no fence", f"{ticks}x{ticks} said\n", False),
        ("diff context line closes the fence early",
         f"{ticks}diff\n {ticks}\n-a\n{ticks}\n\n**after**\n\n{ticks}\nmsg\n{ticks}\n", True),
        ("reply ends in an open fence", f"text\n{ticks}\ncode\n", True),
        ("shorter fence inside a longer one is content", f"{four}\n{ticks}\n{four}\n", False),
        ("fence opened on a bullet line", f"- {ticks}\n  code\n  {ticks}\n", False),
        ("fence opened on a numbered line", f"1. {ticks}bash\n   ls\n   {ticks}\n", False),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}: {problems(text)}")
    bad = f"{ticks}\nopen\n"
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
        print(f"fence-shape: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
