#!/usr/bin/env python3
"""Stop hook: sends a reply back when a CR's assessment or one of its tables breaks its shape.

It owns the assessment blocks a CR call opens - a commit's, a bycatch's, a plan's
call - and checks them for the frame `frame_checks.py` holds: a known call in its
emoji-and-word shape, no Evidence on the call, no retired field or badge, no emoji
before Why Yes or Why Not. Every other block is the assessment hook of tkay-replies', so no
block is checked twice.

It also checks every table of a CR - Goals, Contract, Readiness, Incidents, Code quality,
In short, Bycatch, the two of To do and Was it fixed: each opens with the header row the standard gives, and each row
is numbered with its table's letters, or is the Profile row under one in the two tables that
have one.

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
# Each table: its header row, the letters its rows are numbered with, and whether a row may
# be the unnumbered Profile row under the one above it.
TABLES = {
    "Goals": ("| # | Goal | How we know | Work | Call |", "G", False),
    "Contract": ("| # | The promise | How we know | Work | Call |", "A|IV", False),
    "Readiness": ("| # | The claim | How we know | Work | Call |", "SE|HA|OP", False),
    "Incidents": ("| # | Incident | The spec says | How we know | Work | Call |", "IN", False),
    "Code quality": ("| # | Rule | How we know | Work | Call |", "CQ", False),
    "In short": ("| # | What the commit does | Findings | Call |", "C", True),
    "🎣 Bycatch": ("| # | What the bycatch is | Findings | Call |", "B", True),
    "Before it merges": ("| # | What to do | Where | Who | Fix Profile |", "TD", False),
    "Optional": ("| # | What to do | Where | Who | Fix Profile |", "TD", False),
    "Was it fixed": ("| # | What was to do | Where | Now |", "TD", False),
}
HEADING_RE = re.compile(r"^#{1,4} (.+?)\s*$")
SEPARATOR_RE = re.compile(r"^\|[\s|:-]+\|$")


def row_re(letters, profile_rows):
    """A row numbered with one of the letters, or - where allowed - the Profile row under it."""
    number = rf"\*\*({letters})\d+\*\*"
    return re.compile(rf"^\|\s*({number})?\s*\|" if profile_rows else rf"^\|\s*{number}\s*\|")


def table_problems(lines):
    """Each CR table whose header or row numbers depart from the standard."""
    found = []
    for i, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if not heading or heading.group(1) not in TABLES:
            continue
        name = heading.group(1)
        want, letters, profile_rows = TABLES[name]
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
        numbered = row_re(letters, profile_rows)
        found += [f"a row under '{name}' is not numbered **{letters.replace('|', '<n>** or **')}<n>**: `{row}`"
                  for row in rows[1:] if not SEPARATOR_RE.match(row) and not numbered.match(row)]
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
                     "| **C1** | adds a check | ✨ Gucci | ✅ Ship it |\n"
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
        ("a CR's Close call with an Evidence",
         commit.replace("✅ Ship it", "⚖️ Close call · **Evidence:** LIKELY"), True),
        ("a commit call with a reason and the badge",
         commit.replace("✅ Ship it", "🔧 Needs change (one line) (🍰 No brainer)"), False),
        ("an Evidence on a Needs test call",
         commit.replace("✅ Ship it", "🧪 Needs test (the nightly suite) · **Evidence:** CONFIDENT"),
         True),
        ("an Evidence on the branch call that waits for tests",
         commit.replace("✅ Ship it", "🧪 Merge after tests (1) · **Evidence:** LIKELY"), True),
        ("an Evidence on the branch call that waits for the work",
         commit.replace("✅ Ship it", "⏳ Finish the work first (G3) · **Evidence:** LIKELY"),
         True),
        ("a commit that waits on my call",
         commit.replace("✅ Ship it", "🙋 Needs your call (required or defaulted)"), False),
        ("an Evidence on the branch call that waits on my call",
         commit.replace("✅ Ship it", "🙋 Merge after your call (TD1) · **Evidence:** LIKELY"),
         True),
        ("bycatch calls",
         "- **Call:** 🗑 Drop\n- **Call:** 🗑️ Drop\n"
         "- **Call:** ⏸ Leave for now (out of scope)\n- **Call:** 🔧 Add fix\n", False),
        ("plan calls",
         "- **Call:** ✅ Build it\n- **Call:** 🔧 Build after fixes (Section 5)\n"
         "- **Call:** 🧪 Build after a spike (the cache hit rate)\n"
         "- **Call:** ❌ Back to design (the architecture)\n", False),
        ("an Evidence on a plan's call",
         commit.replace("✅ Ship it", "✅ Build it · **Evidence:** CONFIDENT"), True),
        ("a change's block is tkay-replies'", change, False),
        ("plain text", "no assessment here\n", False),
        ("the In short table in shape", f"# Commits\n\n## In short\n\n{commits_table}", False),
        ("the In short table with made-up columns",
         "## In short\n\n| # | Commit | Notes |\n|---|---|---|\n| **C1** | x | y |\n", True),
        ("an In short row numbered without its C",
         f"## In short\n\n{commits_table}| **2** | a fix | ✨ Gucci | ✅ Ship it |\n", True),
        ("the goals table in shape",
         "# Goals\n\n| # | Goal | How we know | Work | Call |\n|---|---|---|---|---|\n"
         "| **G1** | users see no error | the retry test | **C2** | ✅ Met |\n", False),
        ("a contract table with an API and an invariant row",
         "# Contract\n\n| # | The promise | How we know | Work | Call |\n|---|---|---|---|---|\n"
         "| **A1** | a header | read | **C3** | ✅ Additive |\n"
         "| **IV1** | one retry | the test | **C2** | ✅ Met |\n", False),
        ("a goals row with another table's letter",
         "# Goals\n\n| # | Goal | How we know | Work | Call |\n|---|---|---|---|---|\n"
         "| **A1** | users see no error | the retry test | **C2** | ✅ Met |\n", True),
        ("a goals row with no number, which only a two-row table allows",
         "# Goals\n\n| # | Goal | How we know | Work | Call |\n|---|---|---|---|---|\n"
         "| | users see no error | the retry test | **C2** | ✅ Met |\n", True),
        ("the To do tables in shape",
         "# To do\n\n## Before it merges\n\n| # | What to do | Where | Who | Fix Profile |\n"
         "|---|---|---|---|---|\n| **TD1** | stop retries | **C3**'s 🔴 | 🔧 Fix | x |\n\n"
         "## Optional\n\nNothing optional.\n", False),
        ("a To do table that still has a Blocks column",
         "## Before it merges\n\n| # | What to do | Where | Who | Blocks | Fix Profile |\n"
         "|---|---|---|---|---|---|\n| **TD1** | stop retries | **C3**'s 🔴 | 🔧 Fix | yes | x |\n",
         True),
        ("the Was it fixed table in shape",
         "# Was it fixed\n\n| # | What was to do | Where | Now |\n|---|---|---|---|\n"
         "| **TD1** | stop retries | **C3**'s 🔴 | ✅ Done (**C6**) |\n", False),
        ("a Was it fixed table with a made-up column",
         "# Was it fixed\n\n| # | What was to do | Status |\n|---|---|---|\n"
         "| **TD1** | stop retries | done |\n", True),
        ("an empty section's line is no table", "# Incidents\n\nThe spec states no incidents.\n",
         False),
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
