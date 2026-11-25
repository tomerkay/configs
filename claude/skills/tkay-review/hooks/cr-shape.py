#!/usr/bin/env python3
"""Stop hook: sends a reply back when a CR's assessment or one of its tables breaks its shape.

It owns the assessment blocks a CR call opens - a commit's, a bycatch's, a plan's
call - and checks them for the frame `frame_checks.py` holds: a known call in its
emoji-and-word shape, no Evidence on the call, no retired field or badge, no emoji
before Why Yes or Why Not. Every other block is left to the reply skill's assessment hook,
so no block is checked twice.

It also checks every table of a CR - Goals, Contract, Readiness, Incidents, Design,
Implementation, In short, Bycatch, the two of To do, Was it fixed, Summary, and the Seams and
Version mismatch of the shared part of a CR over several repos - and of a plan
review, which shares them but for its own In short and its Before it is built: each opens
with the header row the standard gives, and each row is numbered with its table's letters, or
is the Profile row under one in the tables that have one.

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

# A heading of any level, so a table under a sub-heading - To do's two, or a CR nested in a
# reply - is held too.
# Each table: its header row, the letters its rows are numbered with, and whether a row may
# be the unnumbered Profile row under the one above it.
TABLES = {
    "Goals": ("| # | Goal | How we know | Work | Call | Blocker |", "G", False),
    "Contract": ("| # | The promise | How we know | Work | Call | Blocker |", "A|IV", False),
    "Readiness": ("| # | The claim | How we know | Work | Call | Blocker |", "SE|HA|OP", False),
    "Incidents": ("| # | Incident | The spec says | How we know | Work | Call | Blocker |", "IN",
                  False),
    "Design": ("| # | Rule | How we know | Work | Call | Blocker |", "DS", False),
    "Implementation": ("| # | Rule | How we know | Work | Call | Blocker |", "IM", False),
    "In short": ("| # | What the commit does | Findings | Call | Blocker |", "C", True),
    "🎣 Bycatch": ("| # | What the bycatch is | Findings | Call |", "B", True),
    "Before it merges": ("| # | What to do | Where | Who | Fix Profile | Blocker |", "TD", False),
    "Before it is built": ("| # | What to do | Where | Who | Fix Profile | Blocker |", "TD", False),
    "Optional": ("| # | What to do | Where | Who | Fix Profile |", "TD", False),
    "Was it fixed": ("| # | What was to do | Where | Now |", "TD", False),
    "Summary": ("| # | Section | Calls | Blocker |", "SC", False),
    "Seams": ("| # | Between | The promise | How we know | Work | Call | Blocker |", "SM", False),
    "Version mismatch": ("| # | The mix | How we know | Work | Call | Blocker |", "VM", False),
}
# Headings other replies use too: a table under one is held only when it opens the way a CR's
# does.
CR_ONLY = {"Summary": "| # | Section | Calls |", "Design": "| # | Rule |",
           "Implementation": "| # | Rule |", "Seams": "| # | Between |",
           "Version mismatch": "| # | The mix |"}
# A heading a plan review shares with a CR, holding a table of its own there: either shape
# passes, and its own letters number its rows.
PLAN_REVIEW_TABLES = {
    "In short": ("| # | What the section says | Findings | Call | Blocker |", "S", True),
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
        if not rows or not rows[0].startswith(CR_ONLY.get(name, "|")):
            continue
        plan = PLAN_REVIEW_TABLES.get(name)
        if plan and rows[0] == plan[0]:
            want, letters, profile_rows = plan
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
    commits_table = ("| # | What the commit does | Findings | Call | Blocker |\n"
                     "|---|---|---|---|---|\n"
                     "| **C1** | adds a check | ✨ Gucci | ✅ Ship it | - |\n"
                     "| | **Evidence:** VERIFIED · **Size:** small · **Difficulty:** easy | | | |\n")
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
        ("a commit with nothing under its subject line",
         commit.replace("✅ Ship it", "📭 Missing description"), False),
        ("an Evidence on the call of a commit with no description",
         commit.replace("✅ Ship it", "📭 Missing description · **Evidence:** LIKELY"), True),
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
        ("a change's block is the reply hook's", change, False),
        ("plain text", "no assessment here\n", False),
        ("the In short table in shape", f"# Commits\n\n## In short\n\n{commits_table}", False),
        ("the In short table with made-up columns",
         "## In short\n\n| # | Commit | Notes |\n|---|---|---|\n| **C1** | x | y |\n", True),
        ("an In short row numbered without its C",
         f"## In short\n\n{commits_table}| **2** | a fix | ✨ Gucci | ✅ Ship it | - |\n", True),
        ("an In short table without its Blocker column",
         "## In short\n\n| # | What the commit does | Findings | Call |\n|---|---|---|---|\n"
         "| **C1** | adds a check | ✨ Gucci | ✅ Ship it |\n", True),
        ("the goals table in shape",
         "# Goals\n\n| # | Goal | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **G1** | users see no error | the retry test | **C2** | ✅ Met | - |\n", False),
        ("a goals table without its Blocker column",
         "# Goals\n\n| # | Goal | How we know | Work | Call |\n|---|---|---|---|---|\n"
         "| **G1** | users see no error | the retry test | **C2** | ✅ Met |\n", True),
        ("a contract table with an API and an invariant row",
         "# Contract\n\n| # | The promise | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **A1** | a header | read | **C3** | ✅ Additive | - |\n"
         "| **IV1** | one retry | the test | **C2** | ✅ Met | - |\n", False),
        ("the incidents table in shape",
         "# Incidents\n\n| # | Incident | The spec says | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|---|\n"
         "| **IN1** | a hung pool | Solved | the test | **C1** | ✅ Met | - |\n", False),
        ("the design table in shape",
         "# Design\n\n| # | Rule | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **DS1** | responsibilities | read | **C1** | 🟠 Broken (x) | ⛔ Hard: code |\n", False),
        ("the implementation table in shape",
         "# Implementation\n\n| # | Rule | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **IM4** | comments | read | **C1** | ✅ Holds | - |\n", False),
        ("an implementation row numbered as a design row",
         "# Implementation\n\n| # | Rule | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **DS4** | comments | read | **C1** | ✅ Holds | - |\n", True),
        ("the old code quality heading is no longer a CR table",
         "# Code quality\n\n| # | Rule | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **CQ1** | comments | read | **C1** | ✅ Holds | - |\n", False),
        ("a Design table that is not a CR's is left alone",
         "## Design\n\n| # | Option | Cost |\n|---|---|---|\n| 1 | a cache | low |\n", False),
        ("a goals row with another table's letter",
         "# Goals\n\n| # | Goal | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **A1** | users see no error | the retry test | **C2** | ✅ Met | - |\n", True),
        ("a goals row with no number, which only a two-row table allows",
         "# Goals\n\n| # | Goal | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| | users see no error | the retry test | **C2** | ✅ Met | - |\n", True),
        ("the To do tables in shape",
         "# To do\n\n## Before it merges\n\n"
         "| # | What to do | Where | Who | Fix Profile | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **TD1** | stop retries | **C3**'s 🔴 | 🔧 Fix | x | ⛔ Hard: code |\n\n"
         "## Optional\n\n| # | What to do | Where | Who | Fix Profile |\n|---|---|---|---|---|\n"
         "| **TD2** | rename | **C3**'s ⚪ | 🔧 Fix (rename) | x |\n", False),
        ("a Before it merges table whose Blocker is not the last column",
         "## Before it merges\n\n| # | What to do | Where | Who | Blocker | Fix Profile |\n"
         "|---|---|---|---|---|---|\n"
         "| **TD1** | stop retries | **C3**'s 🔴 | 🔧 Fix | ⛔ Hard: code | x |\n", True),
        ("an Optional table with a Blocker column",
         "## Optional\n\n| # | What to do | Where | Who | Fix Profile | Blocker |\n"
         "|---|---|---|---|---|---|\n| **TD2** | rename | **C3**'s ⚪ | 🔧 Fix | x | - |\n", True),
        ("the Was it fixed table in shape",
         "# Was it fixed\n\n| # | What was to do | Where | Now |\n|---|---|---|---|\n"
         "| **TD1** | stop retries | **C3**'s 🔴 | ✅ Done (**C6**) |\n", False),
        ("a Was it fixed table with a made-up column",
         "# Was it fixed\n\n| # | What was to do | Status |\n|---|---|---|\n"
         "| **TD1** | stop retries | done |\n", True),
        ("the Summary table in shape",
         "# Summary\n\n| # | Section | Calls | Blocker |\n|---|---|---|---|\n"
         "| **SC1** | Commits | 🔧 Needs change 1 | ⛔ Hard: code |\n", False),
        ("a Summary table with the old Holds the merge column",
         "# Summary\n\n| # | Section | Calls | Holds the merge |\n|---|---|---|---|\n"
         "| **SC1** | Commits | 🔧 Needs change 1 | hard |\n", True),
        ("a plan review's In short table in shape",
         "## In short\n\n| # | What the section says | Findings | Call | Blocker |\n"
         "|---|---|---|---|---|\n"
         "| **S6** | The fix | 🟠 1 | 🔧 Needs fix (x) | ⛔ Hard: design |\n"
         "| | **Evidence:** LIKELY · **Size:** small · **Difficulty:** easy | | | |\n", False),
        ("a plan review's In short row numbered as a commit",
         "## In short\n\n| # | What the section says | Findings | Call | Blocker |\n"
         "|---|---|---|---|---|\n| **C6** | The fix | none | ✅ Holds | - |\n", True),
        ("a plan review's Before it is built table in shape",
         "## Before it is built\n\n| # | What to do | Where | Who | Fix Profile | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **TD1** | one source | **S6**'s 🟠 | 🔧 Fix (plan) | x | ⛔ Hard: design |\n", False),
        ("a Summary table that is not a CR's is left alone",
         "## Summary\n\n| # | What changed | Where |\n|---|---|---|\n| 1 | a hook | x |\n", False),
        ("an empty section's line is no table", "# Incidents\n\nThe spec states no incidents.\n",
         False),
        ("the bycatch table in shape", f"# 🎣 Bycatch\n\n{bycatch_table}", False),
        ("a CR nested a level down keeps its tables",
         f"## 🎣 Bycatch\n\n{bycatch_table}", False),
        ("the bycatch table with made-up columns",
         "# 🎣 Bycatch\n\n| # | What | Where |\n|---|---|---|\n| **B1** | a folder | x |\n", True),
        ("a bycatch row numbered without its B",
         f"# 🎣 Bycatch\n\n{bycatch_table}| **2** | a doc | 🟡 1 | ⏸ Leave for now |\n", True),
        ("no bycatch, no table", "# 🎣 Bycatch\n\nNo bycatch.\n", False),
        ("the seams table in shape",
         "# Seams\n\n| # | Between | The promise | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|---|\n"
         "| **SM1** | a and b | a flag | read | a **C2** | ✅ Met | - |\n", False),
        ("a seams row numbered as a contract row",
         "# Seams\n\n| # | Between | The promise | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|---|\n"
         "| **A1** | a and b | a flag | read | a **C2** | ✅ Met | - |\n", True),
        ("a seams table without its Between column",
         "# Seams\n\n| # | Between | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **SM1** | a flag | read | a **C2** | ✅ Met | - |\n", True),
        ("the version mismatch table in shape",
         "# Version mismatch\n\n| # | The mix | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| **VM1** | **SM1**, new a, old b, rollout | read | **SF1** | ❌ Missed (x) | "
         "⛔ Hard: code |\n", False),
        ("a version mismatch row with no number",
         "# Version mismatch\n\n| # | The mix | How we know | Work | Call | Blocker |\n"
         "|---|---|---|---|---|---|\n"
         "| | new a, old b, rollout | read | **SF1** | ✅ Met | - |\n", True),
        ("a Seams table that is not a CR's is left alone",
         "## Seams\n\n| # | Fabric | Width |\n|---|---|---|\n| 1 | linen | 2 cm |\n", False),
        ("a Version mismatch table that is not a CR's is left alone",
         "## Version mismatch\n\n| # | Library | Pinned |\n|---|---|---|\n"
         "| 1 | numpy | 1.26 |\n", False),
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
