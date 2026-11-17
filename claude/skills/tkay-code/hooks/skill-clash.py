#!/usr/bin/env python3
"""PreToolUse hook: asks before the code skill and the review skill end up in one session.

The skill that registered this hook is loaded, so a Skill call for the other one, or a Read
of a file in the other one's folder, would put both in the session. Code written with the
review rubric in context is written to the rubric, and a review by the code's author is not
independent, so the hook asks, and the person decides. A session whose working directory
is inside the git repo that holds the skills is editing them, and is never asked; a folder
above that repo, such as the home directory, is not inside it. Neither is a session inside a
repo that marks itself as theirs with a MARKER file at its root - a published copy of the
skills, say - which the repo opts into by name, never by its layout.

A skill's hooks stay registered for the rest of the session once it loads, even when it loaded
inside a subagent, so the hook asks only when the conversation it runs in - the main one, or
the subagent named by agent_id - loaded the skill that registered it: its transcript holds the
"Base directory for this skill" line Claude Code writes on that load. A transcript that cannot
be read counts as loaded, so the hook asks as it would without the check.

Both skills carry this script, one as a symlink, and each registers it; which one it runs
for is read from CLAUDE_PLUGIN_ROOT. A failure exits 1, which Claude Code reports and
ignores - this hook never blocks a call on its own error. `--selftest` runs the cases.
"""

import json
import os
import pathlib
import sys
import tempfile

PAIR = {"tkay-code": "tkay-review", "tkay-review": "tkay-code"}
KIND = {"tkay-code": "code", "tkay-review": "CR"}
OVERFIT = {"code": "code overfit to the CR", "CR": "CR overfit to the code"}
MARKER = ".claude-skills-repo"


def repo_of(path):
    """The git repo that holds path - the nearest folder at or above it with a .git - or None."""
    for folder in (path, *path.parents):
        if (folder / ".git").exists():
            return folder
    return None


def works_on_skills(cwd, root):
    """True when cwd is inside the repo that holds the skill at root, or inside a repo with
    the MARKER file at its root."""
    here = pathlib.Path(os.path.abspath(cwd))
    repo = repo_of(root)
    if repo is not None and here.is_relative_to(repo):
        return True
    marked = repo_of(here)
    return marked is not None and (marked / MARKER).is_file()


def transcript_of(payload):
    """The transcript of the conversation the hook runs in, or None when the payload names none:
    a subagent's own when agent_id is set, the session's otherwise."""
    path = payload.get("transcript_path")
    if not isinstance(path, str):
        return None
    path = pathlib.Path(path)
    agent, session = payload.get("agent_id"), payload.get("session_id")
    if isinstance(agent, str) and agent and isinstance(session, str) and session:
        return path.parent / session / "subagents" / f"agent-{agent}.jsonl"
    return path


def loaded_here(payload, root):
    """False only when the conversation's transcript shows no load of the skill at root."""
    path = transcript_of(payload)
    if path is None:
        return True
    marker = f'"text":"Base directory for this skill: {root}\\n'.encode()
    try:
        with open(path, "rb") as transcript:
            return any(marker in line for line in transcript)
    except OSError:
        return True


def other_skill_loading(payload, plugin_root):
    """The other skill's name when this call would load it, else None."""
    if not plugin_root:
        return None
    root = pathlib.Path(os.path.abspath(plugin_root))
    other = PAIR.get(root.name)
    if other is None:
        return None
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and works_on_skills(cwd, root):
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
    # Read last: the transcript can be large, and only a call that would ask needs it.
    if other is None or not loaded_here(payload, os.path.abspath(plugin_root)):
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
    with tempfile.TemporaryDirectory() as tmp:
        home = pathlib.Path(os.path.realpath(tmp))
        s, marked, copy = home / "config", home / "published", home / "lookalike"
        bare = home / "cache" / "skills"
        for repo in (s, marked, copy):
            (repo / ".git").mkdir(parents=True)
        (marked / MARKER).touch()
        for folder in (s / "skills" / "tkay-review" / "references", bare / "tkay-code",
                       marked / "bin", copy / "skills" / "tkay-code"):
            folder.mkdir(parents=True)
        # A main transcript that loaded the code skill, one that did not, and two subagents.
        logs = home / "projects"
        (logs / "loaded" / "subagents").mkdir(parents=True)
        load = f'{{"text":"Base directory for this skill: {s}/skills/tkay-code\\n\\n# Code"}}\n'
        (logs / "loaded.jsonl").write_text(load)
        (logs / "unloaded.jsonl").write_text('{"text":"no skill here"}\n')
        (logs / "loaded" / "subagents" / "agent-a1.jsonl").write_text(load)
        (logs / "loaded" / "subagents" / "agent-a2.jsonl").write_text('{"text":"none"}\n')
        return run_cases(str(home), str(s), str(bare), str(marked), str(copy), str(logs))


def run_cases(home, s, bare, marked, copy, logs):
    code, review = f"{s}/skills/tkay-code", f"{s}/skills/tkay-review"
    repo = "/r/project"

    def logged(payload, transcript, agent=None):
        session = os.path.basename(transcript).removesuffix(".jsonl")
        payload = {**payload, "transcript_path": transcript, "session_id": session}
        if agent:
            payload["agent_id"] = agent
        return payload

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
         read(f"{s}/skills/tkay-review/references/code-review.md"), code, True),
        ("a read of code's SKILL.md beside review", read(f"{s}/skills/tkay-code/SKILL.md"),
         review, True),
        ("the review reads its own symlinked clean-code",
         read(f"{s}/skills/tkay-review/references/clean-code.md"), review, False),
        ("an unrelated read", read("/x"), code, False),
        ("a session editing the skills", skill("tkay-review", cwd=s), code, False),
        ("a session editing the skills from a folder inside their repo",
         read(f"{s}/skills/tkay-review/references/code-review.md",
              cwd=f"{s}/skills/tkay-review/references"), code, False),
        ("a session in a folder above the skills' repo", skill("tkay-review", cwd=home), code,
         True),
        ("a session in a repo with the marker", skill("tkay-review", cwd=marked), code, False),
        ("a session in a folder of that repo", skill("tkay-review", cwd=f"{marked}/bin"), code,
         False),
        ("a repo holding a copy of the skills but no marker", skill("tkay-review", cwd=copy),
         code, True),
        ("skills in no repo, the session above them",
         skill("tkay-review", cwd=os.path.dirname(bare)), f"{bare}/tkay-code", True),
        ("the conversation loaded the code skill itself",
         logged(skill("tkay-review"), f"{logs}/loaded.jsonl"), code, True),
        ("only a subagent loaded the code skill, the main conversation reads on",
         logged(read(f"{s}/skills/tkay-review/references/code-review.md"),
                f"{logs}/unloaded.jsonl"), code, False),
        ("a subagent that loaded the code skill itself",
         logged(skill("tkay-review"), f"{logs}/loaded.jsonl", "a1"), code, True),
        ("a subagent that did not, in a session whose main conversation did",
         logged(skill("tkay-review"), f"{logs}/loaded.jsonl", "a2"), code, False),
        ("a transcript that cannot be read",
         logged(skill("tkay-review"), f"{logs}/missing.jsonl"), code, True),
        ("no plugin root", skill("tkay-review"), None, False),
        ("a skill outside the pair", skill("tkay-review"), f"{s}/skills/other", False),
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
