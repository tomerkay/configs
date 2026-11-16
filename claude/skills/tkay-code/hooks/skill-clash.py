#!/usr/bin/env python3
"""PreToolUse hook: asks before the code skill and the review skill end up in one session.

The skill that registered this hook is loaded, so a Skill call for the other one, or a Read
of a file in the other one's folder, would put both in the session. Code written with the
review rubric in context is written to the rubric, and a review by the code's author is not
independent, so the hook asks, and the person decides. A session whose working directory
holds the skills themselves is editing them, and is never asked.

Both skills carry this script, one as a symlink, and each registers it; which one it runs
for is read from CLAUDE_PLUGIN_ROOT. A failure exits 1, which Claude Code reports and
ignores - this hook never blocks a call on its own error. `--selftest` runs the cases.
"""

import json
import os
import pathlib
import sys

PAIR = {"tkay-code": "tkay-review", "tkay-review": "tkay-code"}
KIND = {"tkay-code": "code", "tkay-review": "CR"}
OVERFIT = {"code": "code overfit to the CR", "CR": "CR overfit to the code"}


def other_skill_loading(payload, plugin_root):
    """The other skill's name when this call would load it, else None."""
    if not plugin_root:
        return None
    root = pathlib.Path(os.path.abspath(plugin_root))
    other = PAIR.get(root.name)
    if other is None:
        return None
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and root.is_relative_to(os.path.abspath(cwd)):
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    tool = payload.get("tool_name")
    if tool == "Skill":
        skill = tool_input.get("skill")
        if isinstance(skill, str) and skill.split(":")[-1] == other:
            return other
    if tool == "Read":
        path = tool_input.get("file_path")
        # The path as written, never resolved: a file this skill carries as a symlink into
        # the other one is its own, not a load of the other skill.
        if isinstance(path, str) and pathlib.Path(
                os.path.abspath(os.path.expanduser(path))).is_relative_to(root.parent / other):
            return other
    return None


def decision(payload, plugin_root):
    other = other_skill_loading(payload, plugin_root)
    if other is None:
        return None
    kind, loaded = KIND[other], KIND[PAIR[other]]
    reason = (f"⚠️ The {kind} skill is about to load, although the {loaded} skill already is "
              f"in this session. That can make the {OVERFIT[kind]}. A fresh session avoids it; "
              "proceed anyway?")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                   "permissionDecisionReason": reason}}


def main():
    out = decision(json.load(sys.stdin), os.environ.get("CLAUDE_PLUGIN_ROOT"))
    if out:
        print(json.dumps(out))


def selftest():
    code, review = "/s/skills/tkay-code", "/s/skills/tkay-review"
    repo = "/r/project"

    def skill(name, cwd=repo):
        return {"tool_name": "Skill", "tool_input": {"skill": name}, "cwd": cwd}

    def read(path, cwd=repo):
        return {"tool_name": "Read", "tool_input": {"file_path": path}, "cwd": cwd}

    cases = [
        ("review loads beside code", skill("tkay-review"), code, True),
        ("plugin-scoped review loads beside code", skill("x:tkay-review"), code, True),
        ("code loads beside review", skill("tkay-code"), review, True),
        ("code loads again beside itself", skill("tkay-code"), code, False),
        ("an unrelated skill", skill("tkay-replies"), code, False),
        ("a read of the review's files beside code",
         read("/s/skills/tkay-review/references/code-review.md"), code, True),
        ("a read of code's SKILL.md beside review", read("/s/skills/tkay-code/SKILL.md"), review,
         True),
        ("the review reads its own symlinked clean-code",
         read("/s/skills/tkay-review/references/clean-code.md"), review, False),
        ("an unrelated read", read("/x"), code, False),
        ("a session editing the skills", skill("tkay-review", cwd="/s"), code, False),
        ("no plugin root", skill("tkay-review"), None, False),
        ("a skill outside the pair", skill("tkay-review"), "/s/skills/other", False),
    ]
    ok = True
    for name, payload, root, expect in cases:
        out = decision(payload, root)
        got = bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "ask"
        if got != expect:
            ok = False
            print(f"FAIL {name}: asked={got}, expected {expect}")
    print("selftest: ok" if ok else "selftest: FAILED")
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    try:
        main()
    except Exception as exc:
        print(f"skill-clash: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
