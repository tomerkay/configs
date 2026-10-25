#!/usr/bin/env python3
"""PreToolUse, PostToolUse and PostToolUseFailure hook on Bash: reports a repo change
made before `LFG!`.

tool-gate.py denies the repo changes it can read from a command's text. A script, an
interpreter or a container runs past it, since nothing in its text says what it writes.
While the gate is closed, this hook records the working repo's state before each Bash
command - `git status`, each dirty file's mtime and size, HEAD and every branch, tag
and stash ref - and compares it after, whether the command succeeded or failed. A
difference is reported to the user and to Claude: it is a broken gate, and git holds
the undo.

Only the repo the command starts in is watched; a script that writes into a second repo
is not seen. A repo under a gate scratch root is outside the gate and never watched.

The gate state and the scratch roots are tool-gate.py's, loaded from the file next to
this one. A failure exits 1, which Claude Code reports and ignores.

`--selftest` runs the cases.
"""

import contextlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

HOOK_DIR = os.path.dirname(os.path.realpath(__file__))
WATCH_DIR = os.path.expanduser("~/.claude/repo-watch")
STALE_SECONDS = 24 * 3600


def load_tool_gate():
    path = os.path.join(HOOK_DIR, "tool-gate.py")
    spec = importlib.util.spec_from_file_location("tool_gate", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tool_gate = load_tool_gate()


def git_out(repo, *args):
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                          timeout=10)
    return proc.stdout if proc.returncode == 0 else None


def watched_repo(cwd):
    """The top of the repo cwd is in, or None outside a repo or inside scratch."""
    if not cwd:
        return None
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    if not top:
        return None
    top = os.path.realpath(top.strip())
    return None if (top + "/").startswith(tool_gate.GATE_SCRATCH_ROOTS) else top


def dirty_paths(status_lines):
    """The paths `git status --porcelain=v1` lists that still exist, renames by new name."""
    paths = []
    for line in status_lines:
        path = line[3:].split(" -> ")[-1]
        if "D" not in line[:2]:
            paths.append(path)
    return paths


def snapshot(repo):
    """The repo's state: status, every dirty file's mtime and size, HEAD and its refs.

    The modification time and size of each dirty file catch a second edit to a file
    that is already modified, which leaves its status line as it was.
    """
    status = (git_out(repo, "status", "--porcelain=v1", "--untracked-files=all") or "")
    status = status.splitlines()
    content = []
    for path in dirty_paths(status):
        try:
            st = os.stat(os.path.join(repo, path))
        except OSError:
            continue
        content.append(f"{path} {st.st_mtime_ns} {st.st_size}")
    refs = git_out(repo, "for-each-ref", "--format=%(refname) %(objectname)",
                   "refs/heads", "refs/tags", "refs/stash")
    head = git_out(repo, "rev-parse", "--symbolic-full-name", "HEAD")
    head_oid = git_out(repo, "rev-parse", "--verify", "--quiet", "HEAD")
    return {"status": status, "content": content, "refs": (refs or "").splitlines(),
            "head": f"{(head or '').strip()} {(head_oid or '').strip()}"}


def changes(before, after):
    """What differs between two snapshots, one line per change."""
    out = []
    if before["head"] != after["head"]:
        out.append(f"HEAD {before['head'].strip()} -> {after['head'].strip()}")
    for key in ("refs", "status", "content"):
        gone = [line for line in before[key] if line not in after[key]]
        new = [line for line in after[key] if line not in before[key]]
        out += [f"- {line}" for line in gone] + [f"+ {line}" for line in new]
    return out


def state_path(watch_dir, payload):
    """One file per tool call, so parallel Bash calls never read each other's snapshot."""
    name = f"{payload['session_id']}-{payload.get('tool_use_id', '')}"
    return os.path.join(watch_dir, re.sub(r"[^A-Za-z0-9_.-]", "_", name))


def prune(watch_dir):
    """Drop snapshots no PostToolUse consumed: a call the gate denied never runs one."""
    try:
        names = os.listdir(watch_dir)
    except FileNotFoundError:
        return
    cutoff = time.time() - STALE_SECONDS
    for name in names:
        path = os.path.join(watch_dir, name)
        with contextlib.suppress(FileNotFoundError):
            if os.path.getmtime(path) < cutoff:
                os.remove(path)


def handle(payload, gate_open, watch_dir):
    """The hook's JSON output for one event, or None."""
    path = state_path(watch_dir, payload)
    if payload["hook_event_name"] == "PreToolUse":
        repo = None if gate_open else watched_repo(payload.get("cwd"))
        if repo is None:
            return None
        prune(watch_dir)
        os.makedirs(watch_dir, exist_ok=True)
        with open(path, "w") as f:
            json.dump({"repo": repo, "before": snapshot(repo)}, f)
        return None
    try:
        with open(path) as f:
            recorded = json.load(f)
    except FileNotFoundError:
        return None
    os.remove(path)
    found = changes(recorded["before"], snapshot(recorded["repo"]))
    if not found:
        return None
    shown = "\n".join(found[:10]) + ("\n..." if len(found) > 10 else "")
    return {
        "systemMessage": f"⚠️ Before LFG!, a Bash command changed {recorded['repo']}:\n{shown}",
        "hookSpecificOutput": {
            "hookEventName": payload["hook_event_name"],
            "additionalContext": (
                f"The repo watch saw this command change {recorded['repo']} while the LFG! "
                f"gate is closed:\n{shown}\nThat is a broken gate: say so in one sentence, "
                "stop, and tell the user exactly what changed, as CLAUDE.md's \"If you break "
                "this gate\" says."),
        },
    }


def main():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return
    result = handle(payload, tool_gate.gate_is_open(payload.get("session_id")), WATCH_DIR)
    if result:
        print(json.dumps(result))


def selftest():
    import tempfile
    failures = 0
    total = 0

    def check(name, got, expected):
        nonlocal failures, total
        total += 1
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name} -> {got}"
              + ("" if ok else f" (want {expected})"))

    # Under a scratch root whether or not the sandbox sets TMPDIR to one.
    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.cache")) as root:
        repo = os.path.join(root, "repo")
        watch_dir = os.path.join(root, "watch")
        plain = os.path.join(root, "plain")
        os.makedirs(plain)
        subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
        with open(os.path.join(repo, "a.txt"), "w") as f:
            f.write("a\n")
        subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", "-c",
                        "commit.gpgsign=false", "add", "a.txt"], check=True)
        subprocess.run(["git", "-C", repo, "-c", "user.email=t@t", "-c", "user.name=t", "-c",
                        "commit.gpgsign=false", "commit", "-q", "-m", "x"], check=True)

        def run(cwd, gate_open, action, after="PostToolUse"):
            base = {"session_id": "s", "tool_use_id": "t", "tool_name": "Bash", "cwd": cwd}
            handle({**base, "hook_event_name": "PreToolUse"}, gate_open, watch_dir)
            action()
            result = handle({**base, "hook_event_name": after}, gate_open, watch_dir)
            return "reported" if result else None

        def edit_tracked():
            with open(os.path.join(repo, "a.txt"), "a") as f:
                f.write("b\n")

        def write_outside():
            with open(os.path.join(plain, "x"), "w") as f:
                f.write("x")

        def branch():
            subprocess.run(["git", "-C", repo, "branch", "feat"], check=True)

        # A repo under a scratch root is never watched; the cases that expect a report run
        # with the scratch roots emptied.
        check("repo under a scratch root", run(repo, False, edit_tracked), None)
        saved_roots = tool_gate.GATE_SCRATCH_ROOTS
        setattr(tool_gate, "GATE_SCRATCH_ROOTS", ())
        try:
            check("edit of a tracked file, gate closed", run(repo, False, edit_tracked),
                  "reported")
            check("write outside the repo, gate closed", run(repo, False, write_outside), None)
            check("new branch, gate closed", run(repo, False, branch), "reported")
            check("edit by a command that then failed, gate closed",
                  run(repo, False, edit_tracked, "PostToolUseFailure"), "reported")
            check("edit of a tracked file, gate open", run(repo, True, edit_tracked), None)
            check("cwd outside any repo", run(plain, False, edit_tracked), None)
            check("no state left behind", os.listdir(watch_dir), [])
        finally:
            setattr(tool_gate, "GATE_SCRATCH_ROOTS", saved_roots)
    print(f"\n{total - failures}/{total} passed")
    return failures == 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    try:
        main()
    except Exception as exc:
        print(f"repo-watch: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
