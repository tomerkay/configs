#!/usr/bin/env python3
"""Stop hook: sends a reply back when a CR's assessment breaks its shape.

It owns the assessment blocks a CR call opens - a commit's, a bycatch's - and checks them for
the frame `frame_checks.py` holds: a known call in its emoji-and-word shape, no Evidence on
the call, no retired label, field or badge, no emoji before Why Yes or Why Not. Every other
block is the assessment hook of tkay-replies', so no block is checked twice.

A blocked reply is returned once: on the retry `stop_hook_active` is set and the hook stays
quiet, so it can never hold the session in a loop. A failure exits 1, which Claude Code
reports and ignores - this hook never stops a reply from ending on its own error.
`--selftest` runs the cases.
"""

import sys

# The shared module sits beside this script; no bytecode cache is left in the skill.
sys.dont_write_bytecode = True
import frame_checks as frame  # noqa: E402

STANDARD = "the review standard's calls and Profiles, references/code-review.md"
SHAPE = ("the commit's assessment as list items: **Call:** with the call alone, then the "
         "**Commit:** Profile with Evidence, Size and Difficulty")


def problems(text):
    found = []
    for block in frame.split(frame.prose_lines(text))[1]:
        if frame.owned_by_cr(block):
            found += frame.frame_problems(block)
    return found


def selftest():
    commit = ("- **Call:** ✅ Ship it\n"
              "- **Commit:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n")
    change = ("- **Call:** ✅ Do it · **Evidence:** LIKELY\n"
              "- **Change:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n")
    cases = [
        ("a commit's call alone", commit, False),
        ("an Evidence on a commit's call",
         commit.replace("✅ Ship it", "✅ Ship it · **Evidence:** CONFIDENT"), True),
        ("the retired How sure field on a commit",
         commit.replace("**Evidence:**", "**How sure:**"), True),
        ("the retired Verdict label on a commit", commit.replace("**Call:**", "**Verdict:**"),
         True),
        ("a CR's Close call with an Evidence",
         commit.replace("✅ Ship it", "⚖️ Close call · **Evidence:** LIKELY"), True),
        ("a commit call with a reason and the badge",
         commit.replace("✅ Ship it", "🔧 Needs change (one line) (🍰 No brainer)"), False),
        ("bycatch calls",
         "- **Call:** 🗑 Drop\n- **Call:** 🗑️ Drop\n"
         "- **Call:** ⏸ Leave for now (out of scope)\n- **Call:** 🔧 Add fix\n", False),
        ("a change's block is tkay-replies'", change, False),
        ("plain text", "no assessment here\n", False),
    ]
    ok = True
    for name, text, expect_block in cases:
        got = bool(problems(text))
        if got != expect_block:
            ok = False
            print(f"FAIL {name}: blocked={got}, expected {expect_block}: {problems(text)}")
    bad = commit.replace("✅ Ship it", "✅ Ship it · **Evidence:** CONFIDENT")
    for name, payload, expect_output in [
        ("retry is never blocked", {"stop_hook_active": True,
                                    "last_assistant_message": bad}, False),
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
        print(f"cr-shape: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
