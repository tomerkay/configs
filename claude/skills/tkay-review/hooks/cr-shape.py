#!/usr/bin/env python3
"""Stop hook: sends a reply back when a CR's assessment or one of its tables breaks its shape.

It owns the assessment blocks a CR call opens - a commit's, a bycatch's - and checks them for
the frame `frame_checks.py` holds: a known call in its emoji-and-word shape, no Evidence on
the call, no retired label, field or badge, no emoji before Why Yes or Why Not. Every other
block is the assessment hook of tkay-replies', so no block is checked twice.

It also checks the commits table and the bycatch table: each opens with the header row the
standard gives, and a bycatch row is numbered B<n> or is the Profile row under one.

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

STANDARD = "the review standard's calls, Profiles and tables, references/code-review.md"
SHAPE = ("the commit's assessment as list items: **Call:** with the call alone, then the "
         "**Commit:** Profile with Evidence, Size and Difficulty; and each table with the "
         "standard's header row")

# A heading of any level, so a CR split by repo, whose sections sit one level down, is held too.
TABLE_HEADERS = {
    "Commits": "| # | What the commit does | Findings | Call |",
    "🎣 Bycatch": "| # | What the bycatch is | Findings | Call |",
}
HEADING_RE = re.compile(r"^#{1,4} (.+?)\s*$")
BYCATCH_ROW_RE = re.compile(r"^\|\s*(\*\*B\d+\*\*)?\s*\|")
SEPARATOR_RE = re.compile(r"^\|[\s|:-]+\|$")


def table_problems(lines):
    """Each commits or bycatch table whose header or row numbers depart from the standard."""
    found = []
    for i, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if not heading or heading.group(1) not in TABLE_HEADERS:
            continue
        name, want = heading.group(1), TABLE_HEADERS[heading.group(1)]
        rows = []
        for row in (row.strip() for row in lines[i + 1:]):
            if not row and not rows:
                continue
            if not row.startswith("|"):
                break
            rows.append(row)
        if not rows:
            continue
        if rows[0] != want:
            found.append(f"the table under '{name}' opens with `{rows[0]}`, not `{want}`")
        if name == "🎣 Bycatch":
            found += [f"a bycatch row is not numbered **B<n>**: `{row}`" for row in rows[1:]
                      if not SEPARATOR_RE.match(row) and not BYCATCH_ROW_RE.match(row)]
    return found


def problems(text):
    found = []
    lines = frame.prose_lines(text)
    for block in frame.split(lines)[1]:
        if frame.owned_by_cr(block):
            found += frame.frame_problems(block)
    return found + table_problems(lines)


def selftest():
    commit = ("- **Call:** ✅ Ship it\n"
              "- **Commit:** **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy\n")
    commits_table = ("| # | What the commit does | Findings | Call |\n|---|---|---|---|\n"
                     "| **1** | adds a check | ✨ Gucci | ✅ Ship it |\n"
                     "| | **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy | | |\n")
    bycatch_table = ("| # | What the bycatch is | Findings | Call |\n|---|---|---|---|\n"
                     "| **B1** | a stale doc (`README.md`) | 🟡 1 | ⏸ Leave for now (scope) |\n"
                     "| | **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy | "
                     "**Fix 🟡:** reword it | |\n")
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
        ("an Evidence on a Needs test call",
         commit.replace("✅ Ship it", "🧪 Needs test (the nightly suite) · **Evidence:** CONFIDENT"),
         True),
        ("an Evidence on the branch call that waits for tests",
         commit.replace("✅ Ship it", "🧪 Merge after tests (1) · **Evidence:** LIKELY"), True),
        ("bycatch calls",
         "- **Call:** 🗑 Drop\n- **Call:** 🗑️ Drop\n"
         "- **Call:** ⏸ Leave for now (out of scope)\n- **Call:** 🔧 Add fix\n", False),
        ("a change's block is tkay-replies'", change, False),
        ("plain text", "no assessment here\n", False),
        ("the commits table in shape", f"# Commits\n\n{commits_table}", False),
        ("the commits table with made-up columns",
         "# Commits\n\n| # | Commit | Notes |\n|---|---|---|\n| **1** | x | y |\n", True),
        ("the bycatch table in shape", f"# 🎣 Bycatch\n\n{bycatch_table}", False),
        ("a CR split by repo keeps the tables a level down",
         f"## 🎣 Bycatch\n\n{bycatch_table}", False),
        ("the bycatch table with made-up columns",
         "# 🎣 Bycatch\n\n| # | What | Where |\n|---|---|---|\n| **B1** | a folder | x |\n", True),
        ("a bycatch row numbered without its B",
         f"# 🎣 Bycatch\n\n{bycatch_table}| **2** | a doc | 🟡 1 | ⏸ Leave for now |\n", True),
        ("no bycatch, no table", "# 🎣 Bycatch\n\nNo bycatch.\n", False),
        ("a table inside a fence is an example",
         "```\n# 🎣 Bycatch\n\n| # | What | Where |\n```\n", False),
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
