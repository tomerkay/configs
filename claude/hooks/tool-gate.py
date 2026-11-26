#!/usr/bin/env python3
"""PreToolUse hook: the `LFG!` gate.

What a Bash command can change - READ, WRITE, RUNS CODE, UNCLASSIFIED or DANGER - is the
tkay-tools skill's command parser's to say, which this hook imports and never copies; that
skill's own hook writes the rating into the call's `description`. This hook only allows,
asks or denies, and never changes a call's input: a second hook's change to the input
replaces the first's whole. The gate holds an UNCLASSIFIED command like a write. The
workplace tables it decides by load from RATING_EXTENSION, never from the rating hook's
config, whose every change the command spells out asks; when that file fails to load,
every call it guards is denied, as when the hook itself raises.

For Bash, Edit, Write, NotebookEdit, EnterWorktree and every MCP tool it decides,
from the gate state lfg-state.py records per session: a change to a git repo before
`LFG!` is denied with the refusal line, while opaque code - an interpreter, a container,
a script, a test run - passes and repo-watch.py reports a repo change it makes, unless a
test run's own flags write beside the tests; every command that needs the user's words
for that one command asks in every state, and so does, once per run, a script whose text
holds one; and a push is denied in every state, since the user runs it. A program the
classifier does not know asks instead of denying, so a read it has not met never gets
the refusal line. A commit, merge,
cherry-pick, revert or am that lands on a repo's default branch is denied in every state,
outside the repos in DEFAULT_BRANCH_EXEMPT, which are committed on main by design. A
rebase in any form, a pull that rebases and a reset that moves the branch back ask in
every state: history below HEAD is rewritten only on the user's words, while amending
HEAD is free. A new worktree - `git worktree add` or the EnterWorktree tool - asks, since
it is made only on the user's words; before `LFG!` the gate denies one in a repo.

An `rm` whose every path is a literal under the scratch root is denied, alone or chained,
before the permission rules see it: the org's `Bash(rm:*)` ask rule prompts on any `rm`
and no allow rule outranks an ask rule, while scratch is per session and left behind
anyway, so the delete costs a prompt and buys nothing. An `rm` that names a scratch path
alongside anything outside the scratch root is not scratch cleanup, so
`rm -rf /private/tmp/claude/x ~/repos` or `rm -rf /private/tmp/claude/../..` is left to the other rules and the prompt. A write
under /tmp is denied in every state, since a file there can vanish mid-session, unless
it lands in a path the user's message named, as scratch-paths.py records it: the
session's handoff directory holds what is written. A path a command assigns to a variable in its first statement, unquoted and absolute, is
read in place of every `$NAME` after it, so `D=/abs && mkdir -p $D` is judged on the
path; any other word the shell builds at run time holds the gate, since it cannot tell
where the write lands.

CLI: `tool-gate.py [--open] <command>...` prints the rating and the decision for each
Bash command with the gate closed (default) or open; `--tool <name> <field>=<value>...`
does the same for another tool; `--selftest` runs the decision table's cases.
"""

import json
import os
import re
import shlex
import subprocess
import sys

# The gate judges a command with the parser that rates it, so the rating and the decision
# never read one command two ways. A missing or broken parser fails this import, and the
# hook's `|| exit 2` blocks the call.
sys.path.insert(0, os.path.expanduser("~/.claude/skills/tkay-tools/hooks"))
import command_parser  # noqa: E402
from command_parser import (  # noqa: E402
    AUTO_MODE, DANGER_PROGRAMS, ENV_ASSIGN_RE, GH_GLOBAL_VALUE_FLAGS, HANDLERS, HARMLESS_TARGETS,
    HELM_LOCAL, HELM_RELEASE_MOVES, HELMFILE_GLOBAL_VALUE_FLAGS, HELMFILE_RELEASE_WRITES,
    KUBECTL_GLOBAL_VALUE_FLAGS, KUBECTL_LIVE_WRITES, KUBECTL_LOCAL, KUBECTL_ROLLOUT_READS,
    LOOP_HEADERS, PUBLISHING_SCRIPTS, PYTHON_RE, READ, READ_PROGRAMS, RUNS_CODE,
    SAFE_HTTP_METHODS, SCRIPT_HANDLERS, SCRIPT_OUTPUTS, TAR_EXTRACT_LONG, TAR_EXTRACT_SHORT,
    TRANSPARENT, UV_GLOBAL_VALUE_FLAGS, WRITE, WRITE_PROGRAMS, classify_command,
    classify_docker, classify_gh, classify_kubectl, classify_program, classify_words,
    command_lines, curl_sends_body, dry_run, edits_in_place, fuser_kills,
    git_merge_file_writes, git_subcommand_args, go_may_rewrite_module, go_without_dir,
    has_flag, help_only, helm_words, http_method, invocations, invocations_in, parse_line,
    positionals, program_of, pushes_image, python_run, python_script, shell_body,
    skopeo_pushes, split_globals, split_line, split_prefix, strip_prefix,
    unknown_programs_as, uv_run_invocations, uv_run_options, uv_run_tail, uv_runs,
    uv_short_flags, uv_subcommand, with_assigned_path, xargs_rest, xh_request,
)

# The words rule and the repo checks decide by the workplace tables of this one file, a
# tracked file under ~/.claude that the gate guards like any repo; the rating config under
# ~/.config, which a session can write, never reaches a decision.
RATING_EXTENSION = os.path.expanduser("~/.claude/personal/rating_extensions.py")


def load_rating_extension(path):
    """Merge the extension at path into the parser's tables: None once it loaded, or why it
    did not, in which case every call this hook guards is denied."""
    try:
        command_parser.load_extension(path)
    except Exception as exc:
        return f"the rating extension {path} did not load: {type(exc).__name__}: {exc}"
    return None


def start():
    """Load the workplace tables the gate decides by, as the hook does when it starts."""
    global EXTENSION_ERROR
    EXTENSION_ERROR = load_rating_extension(RATING_EXTENSION)


start()

SCRATCH_PREFIXES = ("/tmp/claude/", "/private/tmp/claude/")
SCRATCH_ROOTS = tuple(os.path.realpath(p.rstrip("/")) + "/" for p in SCRATCH_PREFIXES)
TMP_ROOT = os.path.realpath("/tmp") + "/"

# The words that open and close a compound command, whose body a pipe runs apart.
COMPOUND_OPENERS = {"if", "while", "until", "for", "case", "select", "{"}
COMPOUND_CLOSERS = {"fi", "done", "esac", "}"}
CHDIR_PROGRAMS = {"cd", "pushd", "popd"}
# Wrappers that run the program as a process of its own, so a `cd` behind one moves no
# directory of the shell's.
CHILD_WRAPPERS = {"env", "nohup", "nice", "stdbuf", "caffeinate", "timeout"}

# ----- the gate -----------------------------------------------------------------------

REFUSAL = 'YOU MUST WRITE "LFG!" for me to actually start implementing.'
# A Bash command's write target is often not in its text, so the gate can deny a command
# that changes no repo, and a session that only takes another route leaves the misread unfixed.
BASH_REFUSAL = (REFUSAL + " If this command changes no repo, the hook misread it: record "
                "that as a bycatch row before anything else.")
CLAUDE_HOME = os.path.realpath(os.path.expanduser("~/.claude")) + "/"
STATE_DIR = os.path.expanduser("~/.claude/lfg-state")
SCRATCH_PATHS_DIR = os.path.expanduser("~/.claude/scratch-paths")
OPEN_STATES = {"open", "one-turn"}
GATED_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit", "EnterWorktree"}
PATH_FIELD = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}

# Writes here never need the gate: scratch, plan mode and memory are harness bookkeeping.
GATE_SCRATCH_ROOTS = tuple(os.path.realpath(os.path.expanduser(p)) + "/"
                           for p in ("/private/tmp/claude", "~/.cache", "~/.claude/plans"))
# The gate guards only the repos under these roots: a clone a tool keeps for itself elsewhere
# (Homebrew, plugin marketplaces, oh-my-zsh) is that tool's state, not the user's work.
REPO_ROOT_NAMES = ("~/repos", "~/.claude", "~/misc")
REPO_ROOTS = tuple(os.path.realpath(os.path.expanduser(p)) + "/" for p in REPO_ROOT_NAMES)
CLONE_OUTSIDE_ROOTS = (f"clones a repo outside {', '.join(REPO_ROOT_NAMES)}, where the gate "
                       "would not guard it")
CLONE_VALUE_FLAGS = {"-u", "--upstream-remote-name", "-g", "--group"}
MEMORY_ROOT_RE = re.compile(
    "^" + re.escape(os.path.realpath(os.path.expanduser("~/.claude/projects"))) + r"/[^/]+/memory/")
# GOTCHA: the lexer strips quotes, so a `~` the shell leaves literal ('~', "~", \~) reaches the
# scratch check looking like one it expands, and the shell expands `~` with its own HOME, which
# the command may set. A command holding either expands no `~` at all.
NO_HOME_EXPANSION_RE = re.compile(r"""['"\\]~|HOME""")
# Bash writers whose every positional path the script can read without path-sniffing.
SCRATCH_WRITERS = {"mkdir", "touch", "cp", "mv", "tee", "rm"}
# Writers of a mode or an owner, never of content: their first positional is the mode or
# the owner, and the paths follow it.
MODE_WRITERS = {"chmod", "chown", "chgrp"}
# GOTCHA: brace expansion, a variable or a substitution can turn a relative word into an
# absolute path, so such a word is never joined to the working directory.
SHELL_EXPANSION_CHARS = set("${`")
# A glob can expand into a repo whatever the literal path around it says.
GLOB_CHARS = set("*?[")

KUBECTL_CONTEXT_SETTERS = {"use-context", "set-context"}
CRUSOE_GET_CREDENTIALS_VALUE_FLAGS = {"--project-name", "--project-id", "--kubeconfig-path",
                                      "--auth-type", "-f", "--format"}

# The TL;DR into a fired alert's thread and the reaction marking the alert as under investigation
# are ungated; these are the alert channels, one ID per line in ALERT_CHANNELS_FILE. A file and
# not an environment variable because a desktop-launched session sources no shell rc, and a path
# outside ~/.claude because this directory is published. The file is a copy of what the On-Call
# SLA page owns: a channel added there and not here asks instead, and with the file missing every
# alert-thread post asks.
ALERT_CHANNELS_FILE = os.path.expanduser("~/.config/tool-gate/alert-channels")


def read_alert_channels():
    try:
        with open(ALERT_CHANNELS_FILE) as f:
            return {line.strip() for line in f if line.strip() and not line.startswith("#")}
    except FileNotFoundError:
        return set()


ALERT_CHANNEL_IDS = read_alert_channels()

# MCP tools match on the name after the last `__`: connectors show up under two server-name
# forms. A tool outside this set may write, so one that names an MR or a review thread asks.
MCP_READ_PREFIXES = (
    "read", "get", "search", "list", "fetch", "lookup", "browse", "resolve", "describe",
    "compare", "verify", "live_", "dbt_", "metric_", "grafana_", "sigma_", "entity_", "cells_",
    "clusters_", "deployments_", "endpoints_", "presets_", "releases_", "scaling_", "schema_",
    "slack_read", "slack_search", "slack_get", "slack_list", "plumber_capacity", "plumber_run",
    "atlassianuserinfo", "agent_browser_get", "agent_browser_snapshot", "agent_browser_read",
    "agent_browser_screenshot", "agent_browser_wait", "agent_browser_tab_list",
    "agent_browser_tools", "agent_browser_open", "agent_browser_back", "agent_browser_forward",
    "agent_browser_reload", "agent_browser_scroll", "agent_browser_tab_new",
    "agent_browser_tab_switch", "agent_browser_tab_close", "agent_browser_close",
)
SLACK_SEND = "slack_send_message"
SLACK_REACT = "slack_add_reaction"
ALERT_REACTION = "claude"

DENY, ASK = "deny", "ask"
DECISION_RANK = {None: 0, ASK: 1, DENY: 2}


def writes_inside_pod(verb, rest):
    """An exec that is not a read, a cp whose destination is `pod:path`, or an attach."""
    if verb == "exec":
        return classify_kubectl(rest) != READ
    if verb == "cp":
        paths = [a for i, a in enumerate(rest)
                 if not a.startswith("-") and not (i and rest[i - 1] in ("-c", "--container"))]
        return len(paths) > 2 and ":" in paths[-1]
    return verb == "attach"


def curl_request(args):
    """The method curl sends and its URL: a body makes a POST unless -G turns it into a query."""
    explicit = has_flag(args, "-X", "--request") or any(
        a.startswith("-X") and len(a) > 2 for a in args)
    if explicit:
        method = http_method(args, "-X", "--request")
    elif curl_sends_body(args) and not has_flag(args, "-G", "--get"):
        method = "POST"
    else:
        method = "GET"
    url = next((args[i + 1] for i, a in enumerate(args[:-1]) if a == "--url"), None)
    if url is None:
        url = next((a for a in args if SCHEME_URL_RE.match(a) or LOOPBACK_BARE_RE.match(a)),
                   "")
    return method, url


WGET_BODY_FLAGS = ("--post-data", "--post-file", "--body-data", "--body-file")


def wget_request(args):
    method = next((a.split("=", 1)[1].upper() for a in args if a.startswith("--method=")), None)
    if method is None and "--method" in args[:-1]:
        method = args[args.index("--method") + 1].upper()
    if method is None:
        method = "POST" if has_flag(args, *WGET_BODY_FLAGS) else "GET"
    url = next((a for a in args if SCHEME_URL_RE.match(a)), None)
    if url is None:
        pos = positionals(args)
        url = pos[-1] if pos else ""
    return method, url


# A URL, as opposed to a header or a field whose value merely holds one.
SCHEME_URL_RE = re.compile(r"^[A-Za-z][\w+.-]*://")
# xh's `:<port>/path` shorthand, and a bare loopback host curl accepts without a scheme.
LOOPBACK_BARE_RE = re.compile(r"^(?::\d+|localhost|[\w.-]+\.localhost|127\.\d+\.\d+\.\d+"
                              r"|\[::1\])(?::\d+)?(?:/|$)")


def url_is_loopback(url):
    """Loopback per RFC 6761 section 6.3 and RFC 1122: a URL built at run time is not."""
    if "$" in url or not url:
        return False
    if url.startswith(":"):
        return True
    host = url.split("://", 1)[-1].split("/", 1)[0].rsplit("@", 1)[-1]
    if host.startswith("["):
        return host.split("]", 1)[0] == "[::1"
    host = host.split(":", 1)[0].lower()
    return (host == "localhost" or host.endswith(".localhost")
            or bool(re.fullmatch(r"127\.\d+\.\d+\.\d+", host)))


def remote_http_write(prog, args):
    """The URL of an HTTP write this invocation sends to a host that is not loopback, or None."""
    if prog == "curl":
        method, url = curl_request(args)
    elif prog in ("xh", "http", "https"):
        if has_flag(args, "--offline"):
            return None
        method, url = xh_request(args)
    elif prog == "wget":
        method, url = wget_request(args)
    else:
        return None
    if method in SAFE_HTTP_METHODS or url_is_loopback(url):
        return None
    return url or "a URL the hook cannot read"


def creates_remote_tag(args):
    rest, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if pos[:2] == ["release", "create"]:
        return True
    return (pos[:1] == ["api"] and classify_gh(args) == WRITE
            and any(re.search(r"/(repository/tags|releases)\b", a) for a in pos[1:]))


# What the user alone decides to run: opening, closing, merging or approving an MR/PR, and
# posting to, resolving or reopening its review threads. A rebase or branch update of an MR
# pushes to its branch, so it counts too. `new` and glab's `for` create an MR, and glab's
# `accept` merges one.
MR_MOVES = {"create", "new", "for", "reopen", "close", "merge", "accept", "approve", "rebase",
            "update-branch", "comment", "review"}
# The user's words for this one command AND this prompt, every time: CLAUDE.md's
# "Some commands need my words and the prompt, every time".
ON_WORDS = ("run it only when the user's message allowed this command in words, otherwise "
            "print it as `! <command>`")
WORKTREE_REASON = ("adds a worktree, which keeps its branch checked out and undeletable until "
                   f"the worktree is removed: {ON_WORDS}")
CONTEXT_SETTER_REASON = ("sets the current context or namespace, which every command that "
                         "relies on it then hits; it never replaces --context and -n")
MR_MOVE_REASON = ("opens, closes, merges or approves an MR/PR, writes to its branch, or posts "
                  f"to, resolves or reopens its review threads: {ON_WORDS}")
# A push is never Claude's to run, whatever the user's words: CLAUDE.md's rule that a
# branch never ends in an offer to push.
PUSH_REASON = ("a push is the user's to run: print the exact command for them as a bracketed "
               "`! <command>` and attempt nothing else - no remote lookup, no other route")
MCP_MR_MOVE_WORDS = ("merge_request", "pull_request", "push")
MCP_CODE_HOSTS = ("gitlab", "github")
MCP_THREAD_WORDS = ("comment", "note", "discussion", "review", "thread")
MR_API_MOVE_RES = (
    re.compile(r"/(?:merge_requests|pulls)/?$"),
    re.compile(r"/(?:merge_requests|pulls)/[^/]+/(?:merge|approve|auto_merge"
               r"|merge_when_pipeline_succeeds|rebase|update-branch)/?$"),
    # Branch writes that skip `git push`: GitLab's commit, file and branch API, GitHub's
    # refs, merges and contents API.
    re.compile(r"/(?:repository/(?:commits|files|branches)|git/refs|merges|contents)(?:/|$)"),
    # Review threads. A GitLab draft note stays private until it is published. GitHub files a
    # PR's conversation under the issues API, so issue comments count too.
    re.compile(r"/merge_requests/[^/]+/(?:notes|discussions"
               r"|draft_notes/(?:bulk_publish|[^/]+/publish))(?:/|$)"),
    re.compile(r"/(?:pulls/[^/]+/(?:comments|reviews)|pulls/comments|issues/[^/]+/comments)"
               r"(?:/|$)"),
)
MR_ITEM_RE = re.compile(r"/(?:merge_requests|pulls)/[^/]+/?$")
MR_STATE_FIELD_RE = re.compile(r"(?:-[fF]|--(?:raw-)?field=)?(?:state|state_event)=")
GRAPHQL_MOVE_RE = re.compile(r"(?i)mutation[\s\S]*(?:merge|approve|close|reopen|pullrequest"
                             r"|createref|updateref|commitonbranch|note|discussion"
                             r"|reviewthread|addcomment)")


def mr_api_moves(args, pos):
    if pos[1:2] == ["graphql"]:
        return any(GRAPHQL_MOVE_RE.search(a) for a in args)
    if classify_gh(args) == READ:
        return False
    paths = [a.split("?", 1)[0] for a in pos[1:]]
    if any(r.search(p) for r in MR_API_MOVE_RES for p in paths):
        return True
    # A body from --input can carry the state where no argument shows it.
    return (any(MR_ITEM_RE.search(p) for p in paths)
            and (has_flag(args, "--input") or any(MR_STATE_FIELD_RE.match(a) for a in args)))


# Writes on an MR that CLAUDE.md leaves free: its title or description, and a draft note.
MR_DRAFT_NOTE_RE = re.compile(r"/merge_requests/[^/]+/draft_notes(?:/[^/]+)?/?$")
API_WRITE_REASON = f"writes to GitLab or GitHub through its API on the user's behalf: {ON_WORDS}"


def api_write_needs_words(prog, args):
    if prog not in ("gh", "glab"):
        return False
    rest, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if pos[:1] != ["api"] or classify_gh(rest) == READ or mr_api_moves(rest, pos):
        return False
    if http_method(rest, "-X", "--method") == "DELETE":
        return True
    paths = [a.split("?", 1)[0] for a in pos[1:]]
    return not any(MR_ITEM_RE.search(p) or MR_DRAFT_NOTE_RE.search(p) for p in paths)


# gh and glab groups whose writes land on GitLab or GitHub alone, and the verbs in them that
# write a checkout, a branch or files here instead.
GH_REMOTE_GROUPS = {"api", "mr", "pr", "issue", "ci", "run", "label", "variable", "secret",
                    "workflow", "schedule", "cache"}
GH_LOCAL_SUBS = {"checkout", "clone", "download", "sync", "artifact", "develop"}


def gh_writes_remote_only(args):
    rest, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    group, sub = (positionals(rest) + ["", ""])[:2]
    return group in GH_REMOTE_GROUPS and sub not in GH_LOCAL_SUBS


def pushes_branch(prog, args):
    if prog == "git":
        sub = git_subcommand_args(args)
        return sub[:1] == ["push"] or sub[:2] == ["lfs", "push"]
    return prog == "git-lfs" and positionals(args)[:1] == ["push"]


def moves_mr(prog, args):
    if prog not in ("gh", "glab"):
        return False
    rest, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if pos[:1] == ["api"]:
        return mr_api_moves(rest, pos)
    if pos[:1] not in (["mr"], ["pr"]):
        return False
    sub = pos[1] if len(pos) > 1 else ""
    if sub == "note":
        return pos[2:3] != ["list"] and (pos[2:3] != ["draft"] or pos[3:4] == ["publish"])
    return sub in MR_MOVES


def uv_runs_module(args):
    """True when uv run's own options ask it to run a module: --module, or an m in a bundle
    of short flags, which takes no value of its own."""
    return any(a == "--module" or (not a.startswith("--") and "m" in uv_short_flags(a)[0])
               for a in uv_run_options(args) if a.startswith("-"))


def defaults_writes_a_named_domain(args):
    """True when a defaults verb that changes only its domain names that domain, which
    cfprefsd keeps in the user's Library, in no repo.

    A domain may also be a path to any plist, with or without the extension, so one with
    a `/`, a `.plist` or a shell expansion is left to the rules for a path.
    """
    pos = positionals(split_globals(args, {"-host"})[0])
    if len(pos) < 2 or pos[0] not in ("write", "delete", "rename", "import"):
        return False
    domain = pos[1]
    return not ("/" in domain or domain.endswith(".plist")
                or (SHELL_EXPANSION_CHARS | {"~"}) & set(domain))


def env_chdir(here, segment):
    """here, moved by every -C or --chdir an env ahead of the segment's program gives, or
    None when only the shell knows where."""
    prefix, _ = split_prefix(segment)
    after_env = False
    for k, w in enumerate(prefix):
        if w == "env":
            after_env = True
            continue
        if not after_env:
            continue
        value = None
        if w in ("-C", "--chdir") and k + 1 < len(prefix):
            value = prefix[k + 1]
        elif w.startswith("--chdir="):
            value = w.split("=", 1)[1]
        elif w.startswith("-C") and len(w) > 2:
            value = w[2:]
        if value is not None:
            here = resolved_dir(here, value)
    return here


def cd_sticks(segments, apart):
    """For each segment, whether a `cd` in it moves the rest of the line.

    Only a `cd` the line's own shell runs does: not one apart from it, and not one inside
    a compound command, which the shell runs in a process of its own when it is piped or
    sent to the background.
    """
    sticks, depth = [], 0
    for segment, alone in zip(segments, apart):
        for word in segment:
            if word in COMPOUND_OPENERS:
                depth += 1
            elif word in COMPOUND_CLOSERS:
                depth = max(depth - 1, 0)
            elif word not in TRANSPARENT:
                break
        sticks.append(not alone and depth == 0)
    return sticks


def cd_target(here, prog, args):
    """The directory a `cd`, `pushd` or `popd` with these args moves to, or None when it is
    known only at run time.

    A `popd`, and a `pushd` with no directory or with +N / -N, land on a directory stack
    entry, which may predate this command.
    """
    pos = positionals(args)
    if prog == "cd":
        return resolved_dir(here, pos[0] if pos else "~")
    if prog == "pushd" and pos and not pos[0].startswith("+"):
        return resolved_dir(here, pos[0])
    return None


def rm_paths(args):
    if "--" in args:
        end = args.index("--")
        return positionals(args[:end]) + args[end + 1:]
    return positionals(args)


def cp_paths(args):
    """The paths a cp may write: its last operand, or with a -t every operand and every value
    inside a -t flag word, since the target can then stand anywhere on the line."""
    end = args.index("--") if "--" in args else len(args)
    operands = positionals(args[:end]) + args[end + 1:]
    targets = []
    for a in args[:end]:
        if a.startswith("--t"):
            targets.append(a.partition("=")[2])
        elif a[:1] == "-" and a[1:2] != "-" and "t" in a[1:]:
            targets.append(a[a.index("t", 1) + 1:])
    if not targets:
        return operands[-1:]
    return operands + [t for t in targets if t]


def ln_paths(args):
    """The paths an ln may write: the links it makes, which stand where cp's target does. With
    one operand the link lands in the working directory under the target's name, so nothing
    is returned and the gate holds it."""
    end = args.index("--") if "--" in args else len(args)
    if len(positionals(args[:end]) + args[end + 1:]) < 2:
        return []
    return cp_paths(args)


def mode_paths(args):
    """The paths a chmod, chown or chgrp changes: every operand after the mode or the
    owner, which `--reference` replaces. A mode that starts with `-`, such as `-x`,
    reads as a flag, so the first path is dropped as the mode and the rest still hold."""
    operands = rm_paths(args)
    if has_flag(args, "--reference"):
        return operands
    return operands[1:]


def inside_scratch(path):
    # GOTCHA: a relative path, `~` or `$VAR` is not resolvable here, so it counts as outside.
    return os.path.isabs(path) and os.path.realpath(path).startswith(SCRATCH_ROOTS)


def rm_escapes_scratch(command):
    for line in command_lines(command):
        try:
            segments, _ = split_line(line)
        except ValueError:
            return any(p in line for p in SCRATCH_PREFIXES)
        for words in segments:
            words = strip_prefix(words)
            if not words or program_of(words) != "rm":
                continue
            paths = rm_paths(words[1:])
            if (any(p.startswith(SCRATCH_PREFIXES) for p in paths)
                    and not all(inside_scratch(p) for p in paths)):
                return True
    return False


RM_CHAINED_REASON = ("rm runs in a call of its own: the org policy prompts on every rm, so an rm "
                     "chained with other work puts the whole command behind that prompt")


def rm_chained(command):
    """True when an rm shares the command with a program other than rm, a cd or a no-op."""
    progs = [prog for prog, _ in invocations(command)
             if prog not in CHDIR_PROGRAMS | {"true", ":"}]
    return "rm" in progs and any(prog != "rm" for prog in progs)


TMP_WRITE_REASON = ("/tmp can vanish mid-session: write the file under this session's "
                    "~/.cache/claude-handoff/<YYYY-MM-DD>-<slug>/ directory, or pipe it into "
                    "the next command")


def unnamed_tmp(path, named):
    """True when path lands under /tmp and inside no path the user named."""
    if not os.path.isabs(path):
        return False
    real = os.path.realpath(path)
    if not real.startswith(TMP_ROOT):
        return False
    return not any(real == n or real.startswith(n.rstrip("/") + "/") for n in named)


def writes_unnamed_tmp(command, named):
    """True when a redirect, or a cp/mv destination or a mkdir/touch/tee path, lands under
    /tmp outside the paths the user named. An `rm` there is cleanup."""
    for line in command_lines(command):
        try:
            segments, targets = split_line(line)
        except ValueError:
            return "/tmp/" in line
        if any(unnamed_tmp(t, named) for t in targets):
            return True
        for words in segments:
            words = strip_prefix(words)
            if not words or program_of(words) not in SCRATCH_WRITERS - {"rm"}:
                continue
            paths = positionals(words[1:])
            if program_of(words) in ("cp", "mv"):
                paths = paths[-1:]
            if any(unnamed_tmp(p, named) for p in paths):
                return True
    return False


ENV_WRITE_REASON = ("changes a .env file: git keeps no copy of an ignored one, so an "
                    "overwrite is permanent, and the managed Edit deny covers only the "
                    f"session's own directory: {ON_WORDS}")
IN_PLACE_EDITORS = {"sed", "gsed", "perl", "ruby"}


def env_file(path):
    """True when path names a .env file: `.env` itself or `.env.<anything>`."""
    name = os.path.basename(path.rstrip("/"))
    return name == ".env" or name.startswith(".env.")


def changes_env_file(command, cwd):
    return changes_file(command, env_file, ".env", cwd)


RATING_CONFIG = os.path.realpath(command_parser.CONFIG_PATH)
RATING_CONFIG_NAME = os.path.basename(RATING_CONFIG)
RATING_CONFIG_REASON = (f"changes {RATING_CONFIG_NAME}, whose extension the rating hook runs "
                        f"outside the sandbox on every Bash call: {ON_WORDS}")


def rating_config(path):
    """True when path is the rating hook's config file, or a relative path of its name,
    whose folder only the shell knows."""
    path = os.path.expanduser(path.rstrip("/"))
    if os.path.basename(path) != RATING_CONFIG_NAME:
        return False
    return not os.path.isabs(path) or os.path.realpath(path) == RATING_CONFIG


def changes_rating_config(command, cwd):
    return changes_file(command, rating_config, RATING_CONFIG_NAME, cwd)


# Writers that copy, move or link sources to a target, by the targets each may write. An
# ln of one operand makes its link in the working directory.
COPY_WRITERS = {"cp": cp_paths, "mv": cp_paths, "install": cp_paths,
                "ln": lambda args: ln_paths(args) or ["."],
                "rsync": lambda args: positionals(args)[-1:]}
# The options of those writers that take a value, which is no source.
COPY_VALUE_FLAGS = {
    "install": {"-m", "--mode", "-o", "--owner", "-g", "--group", "--suffix"},
    "rsync": {"-e", "--rsh", "-f", "--filter", "--exclude", "--include",
              "--exclude-from", "--include-from", "--files-from", "--rsync-path"},
}


def split_value_cluster(args, value_flags):
    """args with each short-flag cluster whose last letter alone takes a value split before
    that letter, so `-Dm 644` reads as `-D -m 644`; an earlier value letter takes the rest
    of the cluster as its value, as getopt reads it."""
    out = []
    for k, a in enumerate(args):
        if a == "--":
            return out + args[k:]
        if (len(a) > 2 and a[0] == "-" and a[1] != "-" and "-" + a[-1] in value_flags
                and not any("-" + c in value_flags for c in a[1:-1])):
            out += [a[:-1], "-" + a[-1]]
        else:
            out.append(a)
    return out


def may_be_folder(here, path):
    """True when path names a folder from where the command stands, or where that is is
    known only once the command runs."""
    if os.path.basename(path.rstrip("/")) in (".", ".."):
        return True
    full = resolved_dir(here, path)
    return full is None or os.path.isdir(full)


def changes_file(command, matches, name, cwd):
    """True when a redirect, or a writer the command names, changes a file `matches` takes:
    the target of a cp, mv, ln, install or rsync, and the file each source lands as when
    that target is a folder; the sources of an mv; the of= of a dd; the path of a tee,
    touch, truncate or rm; or a file an in-place editor rewrites. A copy from one only reads
    it. A relative folder target counts from where the writer runs: the line's working
    directory, which follows every cd the line's own shell runs, never one a child wrapper
    runs, and is unknown after one that may not stick, then moved by any env -C ahead of the
    writer. A line the lexer cannot split changes one when it holds `name`."""
    here = cwd
    for line in command_lines(command):
        try:
            segments, targets, apart, _ = parse_line(line)
        except ValueError:
            return name in line
        if any(matches(t) for t in targets):
            return True
        for words, moves in zip(segments, cd_sticks(segments, apart)):
            raw, at = words, env_chdir(here, words)
            words = strip_prefix(words)
            if not words:
                continue
            prog, args = program_of(words), words[1:]
            if prog in CHDIR_PROGRAMS:
                if not CHILD_WRAPPERS & set(split_prefix(raw)[0]):
                    here = cd_target(here, prog, args) if moves else None
                continue
            if prog in COPY_WRITERS:
                value_flags = COPY_VALUE_FLAGS.get(prog, ())
                args = split_globals(split_value_cluster(args, value_flags), value_flags)[0]
                paths = COPY_WRITERS[prog](args)
                sources = [s for s in positionals(args) if s not in paths]
                # A source copied into a folder lands there under its own name.
                paths += [os.path.join(p, os.path.basename(s.rstrip("/")))
                          for p in paths if p.endswith("/") or len(sources) > 1
                          or may_be_folder(at, p)
                          for s in sources]
                # A move also takes its sources away.
                if prog == "mv":
                    paths += sources
            elif prog == "dd":
                paths = [a[len("of="):] for a in args if a.startswith("of=")]
            elif prog in SCRATCH_WRITERS | {"truncate"}:
                paths = rm_paths(args) if prog == "rm" else positionals(args)
            elif prog in IN_PLACE_EDITORS and edits_in_place(args):
                paths = positionals(args)
            else:
                continue
            if any(matches(p) for p in paths):
                return True
    return False


# Anything the shell would expand into a path this script cannot see: variables, command
# substitution, the home directory, brace expansion.
UNRESOLVABLE_CHARS = set("$`~{")


def scratch_rm_count(command):
    """How many rm invocations in the command, nested ones included, delete only literal
    paths inside the harness scratch root."""
    count = 0
    for prog, args in invocations(command):
        if prog != "rm" or UNRESOLVABLE_CHARS & set("".join(args)):
            continue
        paths = rm_paths(args)
        count += bool(paths) and all(inside_scratch(p) for p in paths)
    return count


SCRATCH_RM_REASON = ("the harness scratch under /tmp/claude is per session and left behind "
                     "anyway: drop the rm and run the rest, since an rm here only raises the "
                     "org policy's prompt")


# ----- gate decisions -----------------------------------------------------------------

def inside_gate_scratch(path):
    """True when path is a literal absolute path under a gate scratch root. A word the
    shell expands at run time is never inside one: `$X` after a scratch root can carry
    `..` back out of it."""
    if (not isinstance(path, str) or not os.path.isabs(path)
            or SHELL_EXPANSION_CHARS & set(path)):
        return False
    real = os.path.realpath(path)
    return real.startswith(GATE_SCRATCH_ROOTS) or bool(MEMORY_ROOT_RE.match(real))


def inside_roots(path):
    return (os.path.realpath(path) + "/").startswith(REPO_ROOTS)


def writes_outside_roots(here, args):
    """True when the working directory and every path among args lie outside the repo roots.

    A program the gate cannot read may write to its working directory or to any path it is
    given, so both must be known; a word built at run time could point anywhere.
    """
    if here is None or inside_roots(here):
        return False
    for arg in args:
        # A word with a space in it is an inline script, which can write anywhere.
        if (SHELL_EXPANSION_CHARS & set(arg)) or any(c.isspace() for c in arg):
            return False
        value = arg.partition("=")[2] if "=" in arg else arg
        if "/" in value or value.startswith(("~", ".")):
            path = resolved_dir(here, value)
            if path is None or inside_roots(path):
                return False
    return True


def claude_plugin_user_scope(args):
    """True for `claude plugin`, which writes ~/.claude/plugins, unless its scope is the
    project's or the local one, which write the working directory's .claude/settings."""
    rest, seen = split_globals(args, {"-s", "--scope"})
    scope = seen.get("-s", seen.get("--scope", "user"))
    return rest[:1] == ["plugin"] and scope == "user"


def clone_destination(here, prog, args):
    """The directory a git, gh or glab clone lands in, None when it is known only at run
    time, or "" when the command clones nothing."""
    if prog == "git":
        return git_target_dir(here, args) if git_subcommand_args(args)[:1] == ["clone"] else ""
    if prog not in ("gh", "glab"):
        return ""
    rest = args[:args.index("--")] if "--" in args else args
    rest, seen = split_globals(rest, GH_GLOBAL_VALUE_FLAGS | CLONE_VALUE_FLAGS)
    pos = positionals(rest)
    if pos[:2] != ["repo", "clone"]:
        return ""
    if here is None:
        return None
    if len(pos) > 3:
        return resolved_dir(here, pos[3])
    # glab clones every repo of a group into the working directory.
    if "-g" in seen or "--group" in seen:
        return here
    return resolved_dir(here, pos[2].rstrip("/").rsplit("/", 1)[-1]) if len(pos) == 3 else None


def clone_decisions(command, cwd):
    """An ask for each clone that lands outside the repo roots and outside scratch.

    The working directory follows every `cd`, as for commits.
    """
    out = []
    here = cwd
    for line in command_lines(command):
        try:
            segments, _, apart, _ = parse_line(line)
        except ValueError:
            continue
        for segment, moves in zip(segments, cd_sticks(segments, apart)):
            words = strip_prefix(segment)
            if not words:
                continue
            prog = program_of(words)
            if prog in CHDIR_PROGRAMS:
                here = cd_target(here, prog, words[1:]) if moves else None
                continue
            dest = clone_destination(here, prog, words[1:])
            if dest == "":
                continue
            if dest is None or not (inside_roots(dest) or inside_gate_scratch(dest)):
                out.append((ASK, CLONE_OUTSIDE_ROOTS))
    return out


def expand_home(word):
    return os.path.expanduser(word) if word == "~" or word.startswith("~/") else word


def invocations_with_moves(command):
    """invocations(command), each with whether it is a `cd` that moves the rest of the
    command: a nested one, run by `bash -c`, `xargs` or `find -exec`, never does."""
    for line in command_lines(command):
        try:
            segments, _, apart, _ = parse_line(line)
        except ValueError:
            continue
        for segment, sticks in zip(segments, cd_sticks(segments, apart)):
            for n, (prog, args) in enumerate(invocations_in(segment)):
                yield prog, args, sticks and n == 0


INTERPRETERS = {"node", "deno", "bun", "npx", "bunx"}
CONTAINER_ENGINES = {"docker", "podman", "nerdctl"}


def runs_opaque_code(words):
    """True for an interpreter, a container or a script: what it writes is not in its text.

    The gate lets these run, and the repo watch reports a repo change one makes. A known
    in-place editor such as `perl -i` or `sed -i` is not one: its target is in its text.
    """
    prog, args = program_of(words), words[1:]
    pos = positionals(args)
    if PYTHON_RE.fullmatch(prog):
        # A script the hook has its own handler for writes where its arguments say.
        script = python_script(args)
        return not (script and os.path.basename(script) in set(SCRIPT_HANDLERS) | PUBLISHING_SCRIPTS)
    if prog in INTERPRETERS:
        return True
    if prog == "uv":
        return uv_runs(args)
    if prog == "go":
        return positionals(go_without_dir(args))[:1] == ["run"]
    if prog == "cargo":
        return pos[:1] == ["run"]
    if prog in CONTAINER_ENGINES:
        return pos[:1] == ["run"] or pos[:2] == ["container", "run"]
    # Each runs the plugin's own install, update or delete hook.
    if prog == "helm":
        _, _, helm_pos = helm_words(args)
        return helm_pos[:1] == ["plugin"] and helm_pos[1:2] in (
            ["install"], ["add"], ["update"], ["up"], ["uninstall"], ["rm"], ["remove"])
    if prog in ("bash", "sh", "zsh", "dash"):
        return script_of(words) is not None
    # A known program called by its path, such as /bin/cp, keeps its own rating.
    return "/" in words[0] and not known_program(prog)


def known_program(prog):
    return (prog in HANDLERS or prog in READ_PROGRAMS or prog in WRITE_PROGRAMS
            or prog in DANGER_PROGRAMS)


GIT_CLONE_VALUE_FLAGS = {"--depth", "-b", "--branch", "-o", "--origin", "--filter",
                         "--reference", "-c", "--config", "--separate-git-dir", "-j", "--jobs",
                         "--shallow-since", "--shallow-exclude", "-u", "--upload-pack",
                         "--template", "--bundle-uri"}


def git_target_dir(here, args):
    """The directory a git invocation changes: the clone's destination for `clone`, the
    `-C` directory or the working directory otherwise, or None when built at run time."""
    repo_dir, rest = here, list(args)
    while rest and rest[0] in ("-C", "-c", "--git-dir", "--work-tree", "--no-pager", "-P"):
        if rest[0] == "-C" and len(rest) > 1:
            repo_dir = resolved_dir(repo_dir, rest[1])
        rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
    if rest[:1] != ["clone"] or repo_dir is None:
        return repo_dir
    clone_args, _ = split_globals(rest[1:], GIT_CLONE_VALUE_FLAGS)
    pos = positionals(clone_args)
    if not pos:
        return None
    dest = pos[1] if len(pos) > 1 else pos[0].rstrip("/").rsplit("/", 1)[-1]
    dest = re.sub(r"\.git$", "", dest) if len(pos) == 1 else dest
    return resolved_dir(repo_dir, dest)


def git_archive_outputs(args):
    """The files a `git archive` invocation writes with -o / --output, or [] for any other git."""
    rest = git_subcommand_args(args)
    if rest[:1] != ["archive"]:
        return []
    outputs, i = [], 1
    while i < len(rest):
        arg = rest[i]
        if arg in ("-o", "--output"):
            outputs.append(rest[i + 1] if i + 1 < len(rest) else "")
            i += 2
            continue
        if arg.startswith("--output="):
            outputs.append(arg.partition("=")[2])
        elif arg.startswith("-o"):
            outputs.append(arg[2:])
        i += 1
    return outputs


def git_merge_file_outputs(args):
    """The file a `git merge-file` invocation overwrites, or [] for any other git and for
    one the gate holds unread."""
    rest = git_subcommand_args(args)
    if rest[:1] != ["merge-file"]:
        return []
    return git_merge_file_writes(rest[1:]) or []


GO_MODULE_FILES = ("go.mod", "go.work")
# The subcommands whose own writes are the module files, vendor/ and a build's binary, and
# nothing a directive or a script decides. `go work sync` rewrites the go.mod of every
# module in the workspace, wherever it sits.
GO_SCRATCH_SUBCOMMANDS = {"mod", "get", "build", "vet", "list", "test"}
GO_PATH_FLAGS = {"-C", "-o", "-modfile"}


def test_run_of(prog, args):
    """The runner and its arguments when the command is a test run, by itself or through
    python -m or uv run, or None."""
    pos = positionals(args)
    if prog == "uv" and uv_runs(args):
        tail = uv_run_tail(args)
        return test_run_of(program_of(tail), tail[1:]) if tail else None
    if PYTHON_RE.fullmatch(prog) and args[:2] == ["-m", "pytest"]:
        return "pytest", args[2:]
    if prog == "go" and positionals(go_without_dir(args))[:1] == ["test"]:
        return prog, args
    if prog == "pytest" or (prog == "cargo" and pos[:1] == ["test"]):
        return prog, args
    return None


# A test rewrites its golden files or snapshots behind a flag named for the update:
# Go's -update, syrupy's --snapshot-update, a crate's own flag after `--`.
UPDATE_FLAG_RE = re.compile(r"--?[A-Za-z0-9_-]*update")


def test_run_writes_beside_tests(here, prog, args):
    """True for a test run whose own flags make it write files beside the tests, outside a
    gate scratch root: an update flag, or Go's -mod=mod rewriting go.mod and go.sum."""
    run = test_run_of(prog, args)
    if run is None:
        return False
    runner, run_args = run
    if not (any(UPDATE_FLAG_RE.match(a) for a in run_args)
            or (runner == "go" and go_may_rewrite_module(run_args))):
        return False
    if runner == "go":
        return not go_writes_into_scratch(here, run_args)
    return here is None or not inside_gate_scratch(os.path.join(here, "."))


def go_writes_into_scratch(here, args):
    """True for a go module or build command whose every write lands in a gate scratch root.

    Go writes go.mod, go.sum and vendor/ in the module root and go.work in the workspace
    root, both found by walking up from the working directory, and a build's binary there
    or at -o. -C moves the working directory, so it is never trusted.
    """
    if here is None or not inside_gate_scratch(os.path.join(here, "go.mod")):
        return False
    pos = positionals(args)
    if not pos or pos[0] not in GO_SCRATCH_SUBCOMMANDS:
        return False
    paths = []
    for i, a in enumerate(args):
        if not a.startswith("-"):
            continue
        name, eq, value = a.partition("=")
        name = "-" + name.lstrip("-")
        if name == "-C":
            return False
        if name in GO_PATH_FLAGS:
            paths.append(value if eq else (args[i + 1] if i + 1 < len(args) else ""))
    if pos[:2] == ["mod", "edit"]:
        paths.extend(pos[2:])
    if not all(p and inside_gate_scratch(path_from(here, p)) for p in paths):
        return False
    d = here
    while True:
        if any(os.path.exists(os.path.join(d, f)) and not inside_gate_scratch(os.path.join(d, f))
               for f in GO_MODULE_FILES):
            return False
        parent = os.path.dirname(d)
        if parent == d:
            return True
        d = parent


# Flags of helm dependency build and update that take no value. A value flag's word reads
# as a positional, so it could pose as the chart path.
HELM_DEPENDENCY_BOOL_FLAGS = {"--skip-refresh", "--verify", "--insecure-skip-tls-verify",
                              "--plain-http", "--debug", "--kube-insecure-skip-tls-verify"}
# A HELM_* variable can move any file helm writes, and the words of a command never show it.
HELM_ENV_RE = re.compile(r"\bHELM_[A-Za-z0-9_]*=")


def helm_dependency_writes_into_scratch(here, args):
    """True for a helm dependency build or update whose every write lands in a gate scratch
    root: the chart's charts/ and Chart.lock, and the repository index and chart caches
    wherever a flag moves them."""
    rest, seen, pos = helm_words(args)
    if pos[:1] != ["dependency"] or pos[1:2] not in (["build"], ["update"], ["up"]) \
            or len(pos) > 3:
        return False
    written = [pos[2] if len(pos) == 3 else "."]
    if "--repository-cache" in seen:
        written.append(seen["--repository-cache"])
    for a in rest:
        name, eq, value = a.partition("=")
        if not a.startswith("-") or name in HELM_DEPENDENCY_BOOL_FLAGS:
            continue
        if not eq:
            return False
        if name == "--content-cache":
            written.append(value)
    return all(inside_gate_scratch(path_from(here, p)) for p in written)


HELM_REPO_STATE_WRITES = {"add", "update", "up", "remove", "rm"}


def helm_repo_writes_outside_repos(here, args):
    """True for a helm repo add, update or remove, which writes only helm's repositories file
    and its caches, when no flag moves one of them outside a gate scratch root."""
    rest, seen, pos = helm_words(args)
    if pos[:1] != ["repo"] or len(pos) < 2 or pos[1] not in HELM_REPO_STATE_WRITES:
        return False
    for a in rest:
        name, eq, value = a.partition("=")
        if name == "--content-cache" and not (eq and inside_gate_scratch(path_from(here, value))):
            return False
    return all(inside_gate_scratch(path_from(here, seen[f]))
               for f in ("--repository-config", "--repository-cache") if f in seen)


def uv_directory(words):
    """The directory uv's --directory moves to before it runs anything, as typed, or None.
    The last one given wins, before the subcommand or among `uv run`'s options."""
    words = strip_prefix(words)
    if not words or program_of(words) != "uv":
        return None
    args = words[1:]
    i = uv_subcommand(args)
    options = args if i is None else args[:i]
    if i is not None and args[i] == "run":
        options = options + uv_run_options(args)
    value = None
    for k, a in enumerate(options):
        if a == "--directory" and k + 1 < len(options):
            value = options[k + 1]
        elif a.startswith("--directory="):
            value = a.split("=", 1)[1]
    return value


def uv_here(here, words):
    """The directory a uv command runs in: here, moved by its --directory, or None when
    only the shell knows it."""
    directory = uv_directory(words)
    return here if directory is None else resolved_dir(here, directory)


def uv_run_command(here, words):
    """Where and what a `uv run` runs, through every `uv run` the words start with, or here
    and the words as they are: uv runs it as the segment's own command, in the directory
    its --directory names, so its writes are that command's, from there."""
    while words and program_of(words) == "uv" and uv_runs(words[1:]):
        raw = uv_run_tail(words[1:])
        tail = strip_prefix(raw)
        if not tail:
            break
        here, words = env_chdir(uv_here(here, words), raw), tail
    return here, words


def gate_blockers(command, cwd, run_time_dir=None):
    """The words of each program the gate holds, a `tee` of each redirect target outside
    scratch, or [None] for a line it cannot parse; empty when nothing changes a repo by a
    route the text shows.

    A read, a command that needs the user's words, opaque code, a write that lands in a
    gate scratch root, git run in one or outside the repo roots, an `rm` or a mode change
    of literal files outside every repo, and any other write whose working directory and
    every named path lie outside the repo roots all pass, except a redirect, a mkdir,
    touch, cp, mv or tee, a patch, and a go other than `go env`, each held to scratch
    wherever it writes; every write left is held to scratch. The working directory follows
    every `cd`, as for commits, and is unknown after one that may not stick; a relative
    redirect target counts from it as it stands where the redirect opens.
    run_time_dir, when given, stands for the directory a `cd` moves to when only the shell
    knows it.
    """
    # base is the shell's working directory; here is where the segment's command runs,
    # which uv's --directory can move.
    blockers, base = [], cwd
    for line in command_lines(command):
        try:
            segments, targets, apart, target_at = parse_line(line)
        except ValueError:
            return [None]
        sticks = cd_sticks(segments, apart)
        if not NO_HOME_EXPANSION_RE.search(command):
            segments = [[expand_home(w) for w in segment] for segment in segments]
            targets = [expand_home(t) for t in targets]
        targets_of = {}
        for t, at in zip(targets, target_at):
            targets_of.setdefault(at, []).append(t)
        for index, (words, moves) in enumerate(zip(segments, sticks)):
            # The shell opens a segment's redirects before it runs, so a `cd` in the
            # segment itself moves nothing for them.
            blockers.extend(["tee", t] for t in targets_of.pop(index, ())
                            if t not in HARMLESS_TARGETS
                            and not inside_gate_scratch(path_from(base, t)))
            stripped = strip_prefix(words)
            wrappers = set(split_prefix(words)[0])
            here, words = uv_run_command(env_chdir(base, words), stripped)
            child = words != stripped or bool(CHILD_WRAPPERS & wrappers)
            if not words or program_of(words) in LOOP_HEADERS:
                continue
            prog, args = program_of(words), words[1:]
            if prog in CHDIR_PROGRAMS:
                if not child:
                    base = (cd_target(base, prog, args) or run_time_dir) if moves else None
                continue
            level = classify_program(prog, args)
            if level == READ:
                continue
            # A command that needs the user's words is the words rule's, never the gate's.
            if any(decision == ASK for decision, _ in every_state_decisions(prog, args)):
                continue
            if test_run_writes_beside_tests(here, prog, args):
                blockers.append(words)
                continue
            if level == RUNS_CODE or runs_opaque_code(words):
                continue
            if prog in ("gh", "glab") and gh_writes_remote_only(args):
                continue
            # xargs adds its input's words to the command it runs, so the files a write
            # through it reaches are not in the text.
            if prog == "xargs":
                blockers.append(words)
                continue
            if prog == "git":
                target = git_target_dir(here, args)
                # The directory itself may be a scratch root, so it counts as inside one.
                if target is not None and (os.path.realpath(target) + "/").startswith(
                        GATE_SCRATCH_ROOTS):
                    continue
                # A clone outside the roots is the clone check's to ask about.
                if target is not None and not inside_roots(target):
                    continue
                # Only an absolute output path - archive's -o, merge-file's <current> - is
                # trusted: git resolves a relative one against a directory that -C and its own
                # setup decide, not the text.
                outputs = git_archive_outputs(args) or git_merge_file_outputs(args)
                if outputs and all(inside_gate_scratch(o) for o in outputs):
                    continue
                blockers.append(words)
                continue
            if prog in SCRATCH_WRITERS | MODE_WRITERS:
                paths = rm_paths(args) if prog == "rm" else positionals(args)
                # A cp only reads its sources, so a source inside a repo changes nothing there.
                if prog == "cp":
                    paths = cp_paths(args)
                if prog in MODE_WRITERS:
                    paths = mode_paths(args)
                if paths and all(inside_gate_scratch(path_from(here, p)) for p in paths):
                    continue
                # An rm or a mode change leaves no file behind to hold to scratch, so
                # outside every repo it is not the gate's.
                if prog in MODE_WRITERS | {"rm"} and paths and all(
                        outside_repos(path_from(here, p)) for p in paths):
                    continue
            # An ln only reads its targets, so a target inside a repo changes nothing there.
            if prog == "ln":
                paths = ln_paths(args)
                if paths and all(inside_gate_scratch(path_from(here, p)) for p in paths):
                    continue
            if prog == "tar" and tar_extracts_into_scratch(here, args):
                continue
            if prog in ("sed", "gsed") and sed_edits_only_scratch(here, args):
                continue
            script = python_script(args) if PYTHON_RE.fullmatch(prog) else None
            output_of = SCRIPT_OUTPUTS.get(os.path.basename(script)) if script else None
            if output_of:
                # A script with a known output writes no other file in a repo.
                out = output_of(args[args.index(script) + 1:])
                if out is None or inside_gate_scratch(path_from(here, out)):
                    continue
            if prog == "go" and go_writes_into_scratch(here, args):
                continue
            if prog == "patch":
                files = patch_writes(here, args)
                if files and all(inside_gate_scratch(path_from(here, f)) for f in files):
                    continue
            if prog == "helm" and not HELM_ENV_RE.search(command) \
                    and (helm_dependency_writes_into_scratch(here, args)
                         or helm_repo_writes_outside_repos(here, args)):
                continue
            if prog == "defaults" and defaults_writes_a_named_domain(args):
                continue
            # go env -w and -u write Go's own user config file, which sits in no repo.
            if prog == "go" and positionals(args)[:1] == ["env"]:
                continue
            # A signal reaches a process, never a file, and ssh-add changes only the agent's keys.
            if prog in ("kill", "pkill", "killall", "ssh-add"):
                continue
            # Both write only under their own prefix, whose clones are the tool's state; brew
            # bundle is the exception, writing a Brewfile into the working directory.
            if prog == "brew" and positionals(args)[:1] != ["bundle"]:
                continue
            # krew writes only under its own root, which KREW_ROOT can move.
            if prog in ("kubectl", "k") and "KREW_ROOT=" not in command and positionals(
                    split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)[0])[:1] == ["krew"]:
                continue
            if prog == "claude" and claude_plugin_user_scope(args):
                continue
            # go generate and go work sync write where directives and the workspace say, so
            # go keeps the rules above.
            if prog not in SCRATCH_WRITERS | MODE_WRITERS | {"go", "patch"} \
                    and writes_outside_roots(here, args):
                continue
            blockers.append(words)
        # A redirect with no command of its own opens where the line ends.
        blockers.extend(["tee", t] for ts in targets_of.values() for t in ts
                        if t not in HARMLESS_TARGETS
                        and not inside_gate_scratch(path_from(base, t)))
    return blockers


# The options of patch a pass is decided for, spelled in full: any other one, an
# abbreviation included, holds the patch, since it may move where patch writes.
PATCH_FLAGS = {"-b", "--backup", "-c", "--context", "-e", "--ed", "-E", "--remove-empty-files",
               "-f", "--force", "-l", "--ignore-whitespace", "-n", "--normal", "-N", "--forward",
               "-R", "--reverse", "-s", "--quiet", "--silent", "-t", "--batch", "-u", "--unified"}
PATCH_VALUE_OPTS = {"-p": "-p", "--strip": "-p", "-i": "-i", "--input": "-i", "-o": "-o",
                    "--output": "-o", "-r": "-r", "--reject-file": "-r", "-z": "-z",
                    "--suffix": "-z", "-F": "-F", "--fuzz": "-F", "-V": "-V",
                    "--version-control": "-V"}
# A line that starts a file's changes in a patch file, past the indentation patch skips.
PATCH_START_RE = re.compile(r"[ \tX]*(?:(\+\+\+|---) |\*\*\* |Index:|diff |Prereq:"
                            r"|\d+(?:,\d+)?[acd](?:\d+(?:,\d+)?)?\s*$)")


def patch_writes(here, args):
    """The files a patch writes, as typed, or [] when the hook cannot name them all: the -o
    file, else the file it is given, and a -r reject file. patch applies every other file's
    changes the patch file holds to the file it names, so the patch file must be readable
    and hold one unified diff of one file."""
    options, files, i = {}, [], 0
    while i < len(args):
        a = args[i]
        name, eq, value = a.partition("=")
        if a.startswith("--") and eq and name in PATCH_VALUE_OPTS:
            options[PATCH_VALUE_OPTS[name]] = value
        elif a in PATCH_VALUE_OPTS and i + 1 < len(args):
            options[PATCH_VALUE_OPTS[a]] = args[i + 1]
            i += 1
        elif not a.startswith("--") and len(a) > 2 and a[:2] in PATCH_VALUE_OPTS:
            options[a[:2]] = a[2:]
        elif a in PATCH_FLAGS:
            pass
        elif a.startswith("-"):
            return []
        else:
            files.append(a)
        i += 1
    patch_file = options.get("-i") or (files[1] if len(files) > 1 else None)
    path = patch_file and path_from(here, patch_file)
    if not path:
        return []
    try:
        with open(path, errors="replace") as f:
            starts = sorted(m.group(1) or "other" for m in map(PATCH_START_RE.match, f) if m)
    except OSError:
        return []
    # One unified diff of one file: patch writes each other file a header names, in any
    # diff format and at any indentation.
    if starts != ["+++", "---"]:
        return []
    out = options.get("-o")
    target = [out] if out else files[:1]
    reject = options.get("-r")
    return target + [reject] if target and reject else target


def path_from(here, path):
    """path as a command run in here opens it, or None when only the shell knows."""
    if os.path.isabs(path):
        return path
    if here is None or SHELL_EXPANSION_CHARS & set(path):
        return None
    return os.path.join(here, path)


def outside_repos(path):
    """True when path is a literal file in no git work tree.

    An existing directory never is: `rm -r` of one takes any repo inside it along.
    """
    if path is None or (SHELL_EXPANSION_CHARS | GLOB_CHARS) & set(path):
        return False
    real = os.path.realpath(path)
    return not os.path.isdir(real) and not inside_repo(real)


def inside_repo(path):
    """True when path lies in a git work tree under a repo root, outside the scratch roots,
    unless it is an ignored file the session does not trust."""
    if (not isinstance(path, str) or not os.path.isabs(path) or inside_gate_scratch(path)
            or not inside_roots(path)):
        return False
    real = os.path.realpath(path)
    here = os.path.dirname(real)
    while True:
        if os.path.exists(os.path.join(here, ".git")):
            return not untrusted_ignored(here, real)
        parent = os.path.dirname(here)
        if parent == here:
            return False
        here = parent


def untrusted_ignored(repo, path):
    """True when the repo ignores path and the session trusts nothing kept there.

    GOTCHA: the gate's own state lives in ignored files under ~/.claude, which ignores all
    it does not track, and a repo's .claude/ holds settings.local.json, whose rules grant
    permissions; an ignored file in either would let the session open its own gate.
    """
    if (path + "/").startswith(CLAUDE_HOME) or ".claude" in os.path.relpath(
            path, repo).split(os.sep):
        return False
    return git_ignores(repo, path)


def git_ignores(repo, path):
    """True when the repo ignores path. git check-ignore never counts a file the index holds,
    so a tracked file stays guarded whatever the ignore rules say; a git that cannot answer
    counts as not ignoring it."""
    try:
        done = subprocess.run(["git", "-C", repo, "check-ignore", "-q", "--", path],
                              capture_output=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def tar_extracts_into_scratch(here, args):
    """True when tar only extracts, and every -C / --directory lands in a gate scratch root.

    Each one is taken from the directory the one before it left, as tar applies them.
    """
    dirs, extract, i = [], False, 0
    while i < len(args):
        arg = args[i]
        if arg in ("-C", "--directory"):
            if i + 1 == len(args):
                return False
            dirs.append(args[i + 1])
            i += 2
            continue
        if arg.startswith("--"):
            name, _, value = arg.partition("=")
            if name not in TAR_EXTRACT_LONG:
                return False
            if name == "--directory":
                dirs.append(value)
            extract = extract or name in ("--extract", "--get")
        elif arg.startswith("-"):
            if not set(arg[1:]) <= TAR_EXTRACT_SHORT:
                return False
            extract = extract or "x" in arg
        i += 1
    if not extract or not dirs:
        return False
    for d in dirs:
        here = path_from(here, d)
        if not inside_gate_scratch(here):
            return False
    return True


SED_SAFE_SHORT_FLAGS = set("nrEsuz")
SED_SAFE_LONG_FLAGS = {"--regexp-extended", "--quiet", "--silent", "--separate", "--null-data",
                       "--posix", "--sandbox"}
SED_SAFE_SUBSTITUTE_FLAGS = set("gIipmM0123456789")
# A line number or a range of them (`3`, `3,7`, `5,$`) only narrows where an s command runs.
SED_LINE_ADDRESS_RE = re.compile(r"^(?:\d+|\$)(?:,(?:\d+|\$))?")


def sed_edits_only_its_file(script):
    """True when script is one or more s or d commands, apart by `;` or a newline, each on
    every line or on a line number or range, an s whose flags neither write (w) nor run (e)
    anything: a d only drops lines from the file sed edits."""
    rest = script
    while True:
        rest = SED_LINE_ADDRESS_RE.sub("", rest.lstrip(), count=1)
        if rest[:1] == "d":
            tail = rest[1:]
            stop = re.search(r"[;\n]", tail)
            if (tail[:stop.start()] if stop else tail).strip():
                return False
            if not stop or not tail[stop.end():].strip():
                return True
            rest = tail[stop.end():]
            continue
        if len(rest) < 4 or rest[0] != "s" or rest[1] in "\\\n":
            return False
        delim, seen, i = rest[1], 0, 2
        while i < len(rest) and seen < 2:
            if rest[i] == "\\":
                i += 2
                continue
            seen += rest[i] == delim
            i += 1
        if seen < 2:
            return False
        tail = rest[i:]
        stop = re.search(r"[;\n]", tail)
        flags = tail[:stop.start()] if stop else tail
        if not set(flags.rstrip()) <= SED_SAFE_SUBSTITUTE_FLAGS:
            return False
        if not stop or not tail[stop.end():].strip():
            return True
        rest = tail[stop.end():]


def sed_edits_only_scratch(here, args):
    """True when sed edits in place with substitutions and deletes alone, and every file it
    edits lies in a gate scratch root.

    GOTCHA: BSD sed, the one macOS ships, takes the word after a bare -i (or after a flag
    cluster ending in i) as the backup suffix, and GNU sed does not. Only '' or a word
    that starts with a dot is taken as that suffix; any other word there holds the gate,
    since the two seds would read it differently. A suffix with a / in it would put the
    backup in another directory, so it holds the gate too.
    """
    scripts, pos, in_place, i = [], [], False, 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            pos.extend(args[i + 1:])
            break
        if arg in ("-e", "--expression"):
            if i + 1 == len(args):
                return False
            scripts.append(args[i + 1])
            i += 2
            continue
        if arg.startswith("--expression="):
            scripts.append(arg.partition("=")[2])
        elif arg == "--in-place" or arg.startswith("--in-place="):
            in_place = True
            if "/" in arg.partition("=")[2]:
                return False
        elif arg.startswith("--"):
            if arg not in SED_SAFE_LONG_FLAGS:
                return False
        elif arg.startswith("-") and len(arg) > 1:
            flags, has_i, suffix = arg[1:].partition("i")
            if not set(flags) <= SED_SAFE_SHORT_FLAGS or "/" in suffix:
                return False
            if has_i:
                in_place = True
                if not suffix:
                    if i + 1 == len(args):
                        return False
                    suffix = args[i + 1]
                    if not (suffix == "" or suffix.startswith(".")) or "/" in suffix:
                        return False
                    i += 2
                    continue
        else:
            pos.append(arg)
        i += 1
    if not scripts and pos:
        scripts.append(pos.pop(0))
    return (in_place and bool(scripts) and bool(pos)
            and all(sed_edits_only_its_file(s) for s in scripts)
            and all(inside_gate_scratch(path_from(here, p)) for p in pos))


def held_for_shell_paths(blockers):
    """True when every program the gate holds would pass with each word the shell builds at
    run time standing for a path in a gate scratch root, so only those words stop it."""
    if any(words is None for words in blockers):
        return False
    stand_in = GATE_SCRATCH_ROOTS[0] + "x"
    rewritten = [[stand_in if SHELL_EXPANSION_CHARS & set(w) else w for w in words]
                 for words in blockers]
    return rewritten != blockers and not gate_blockers(
        "\n".join(shlex.join(words) for words in rewritten), None)


def held_for_shell_dir(command, cwd):
    """True when the command would pass with every `cd` the shell resolves at run time
    landing in a gate scratch root, and with every write path the shell builds standing for
    one, so only words the shell builds stop it."""
    rest = gate_blockers(command, cwd, GATE_SCRATCH_ROOTS[0] + "x")
    return not rest or held_for_shell_paths(rest)


def only_unknown_writes(blockers):
    """True when every program the gate holds is a write only because the classifier has
    never met it; a known write, an unparsed line or an untrusted redirect is not."""
    with unknown_programs_as(READ):
        return all(words is not None and classify_words(words) == READ for words in blockers)


# A rewrite below HEAD changes commits the user has already read; amending HEAD is free, and
# so is finishing or abandoning a rebase already begun, which the words that started it cover.
REWRITE_REASON = ("rewrites commits below HEAD: run it only when the user's message allowed "
                  "this rewrite in words, with their answer to one ❓ on whether it may reword, "
                  "squash and split; otherwise print it as `! <command>`")
REBASE_CONTINUATIONS = {"--continue", "--abort", "--quit", "--skip"}
RESET_MODES = {"--soft", "--mixed", "--hard", "--merge", "--keep"}
# What a reset target looks like when it is a commit and not a path: a ref with a ~ or ^
# step, a reflog entry, a bare HEAD or a SHA.
REF_LIKE_RE = re.compile(r"^(?:HEAD|ORIG_HEAD|FETCH_HEAD|@)(?:[~^].*|@\{.*\})?$"
                         r"|^[0-9a-f]{7,40}$|^.+[~^]\d*$|^.+@\{.*\}$")


def rewrites_history(prog, args):
    """True for a git command that rewrites commits below HEAD: a rebase in any form, a
    pull that rebases, a reset that moves the branch back, a history filter."""
    if prog != "git":
        return False
    rest = git_subcommand_args(args)
    if not rest:
        return False
    sub, rest = rest[0], rest[1:]
    if sub == "rebase":
        return not any(a in REBASE_CONTINUATIONS for a in rest)
    if sub == "pull":
        return has_flag(rest, "-r", "--rebase") or any(a.startswith("--rebase=") for a in rest)
    if sub in ("filter-branch", "filter-repo"):
        return True
    if sub == "reset":
        before_paths = rest[:rest.index("--")] if "--" in rest else rest
        if any(a in RESET_MODES for a in before_paths):
            return True
        pos = positionals(before_paths)
        return "--" not in rest and bool(pos) and REF_LIKE_RE.match(pos[0]) is not None
    return False


def adds_worktree(prog, args):
    if prog != "git":
        return False
    rest = git_subcommand_args(args)
    return rest[:1] == ["worktree"] and positionals(rest[1:])[:1] == ["add"]


def every_state_decisions(prog, args):
    """The rows that apply in every gate state, for one program invocation."""
    out = []
    if help_only(prog, args):
        return out
    if rewrites_history(prog, args):
        out.append((ASK, REWRITE_REASON))
    if ((HANDLERS.get(prog) is classify_docker and pushes_image(args))
            or (prog == "skopeo" and skopeo_pushes(args))):
        out.append((ASK, "pushes an image to a registry, where a moved tag reaches every "
                         f"deployment that pulls it: {ON_WORDS}"))
    elif prog == "glab" and creates_remote_tag(args):
        out.append((ASK, "creates a tag or release on the remote, which can start its release "
                         f"pipeline: {ON_WORDS}"))
    elif prog in PUBLISHING_SCRIPTS or ((PYTHON_RE.fullmatch(prog) or prog == "uv") and any(
            os.path.basename(a) in PUBLISHING_SCRIPTS for a in positionals(args))):
        out.append((ASK, "runs a script that pushes images and moves shared registry tags: "
                         f"{ON_WORDS}"))
    if pushes_branch(prog, args):
        out.append((DENY, PUSH_REASON))
    if prog in ("pkill", "killall") or (prog == "fuser" and fuser_kills(args)):
        out.append((ASK, "kills every process its name, pattern or file matches, other "
                         f"sessions' included: {ON_WORDS}"))
    if moves_mr(prog, args):
        out.append((ASK, MR_MOVE_REASON))
    elif api_write_needs_words(prog, args):
        out.append((ASK, API_WRITE_REASON))
    url = remote_http_write(prog, args)
    if url:
        out.append((ASK, f"an HTTP write to {url} changes state on a remote server: "
                         f"{ON_WORDS}"))
    if prog in ("kubectx", "kubens"):
        out.append((ASK, f"{CONTEXT_SETTER_REASON}: {ON_WORDS}"))
    elif prog in ("kubectl", "k", "oc"):
        rest, _ = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
        verb = pos[0] if pos else ""
        sub = pos[1] if len(pos) > 1 else ""
        if verb == "config" and sub in KUBECTL_CONTEXT_SETTERS:
            out.append((ASK, f"{CONTEXT_SETTER_REASON}: {ON_WORDS}"))
            return out
        if not pos or verb in KUBECTL_LOCAL or (verb == "version" and "--client" in rest):
            return out
        if "$" in verb:
            out.append((ASK, f"kubectl {RUNTIME_VERB_REASON}: {ON_WORDS}"))
        writes = (verb in KUBECTL_LIVE_WRITES
                  and not (verb == "rollout" and sub in KUBECTL_ROLLOUT_READS))
        if writes and not dry_run(rest):
            out.append((ASK, f"kubectl {verb} writes live cluster state: {ON_WORDS}"))
        elif writes_inside_pod(verb, rest):
            out.append((ASK, f"kubectl {verb} changes what runs or is stored inside a pod: "
                             f"{ON_WORDS}"))
    elif prog == "helm":
        rest, _, pos = helm_words(args)
        sub = pos[0] if pos else ""
        if not pos or sub in HELM_LOCAL:
            return out
        if "$" in sub:
            out.append((ASK, f"helm {RUNTIME_VERB_REASON}: {ON_WORDS}"))
        if has_flag(rest, "--force-conflicts"):
            out.append((ASK, f"helm {sub} --force-conflicts takes field ownership from every "
                             f"other manager: {ON_WORDS}"))
        if sub in HELM_RELEASE_MOVES:
            out.append((ASK, f"helm {sub} deletes or rewinds a live release: {ON_WORDS}"))
        if sub in ("install", "upgrade") and not dry_run(rest):
            out.append((ASK, f"helm {sub} changes what runs on the cluster: {ON_WORDS}"))
        if sub in ("install", "upgrade") and has_flag(rest, "--reuse-values"):
            out.append((ASK, "--reuse-values keeps the old chart's defaults and the previous "
                             f"values, dropping the new chart's defaults: {ON_WORDS}"))
        if sub in ("install", "upgrade") and has_flag(rest, "--reset-then-reuse-values"):
            out.append((ASK, "--reset-then-reuse-values carries the previous values onto the "
                             f"new chart: {ON_WORDS}"))
    elif prog == "helmfile":
        rest, _ = split_globals(args, HELMFILE_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
        sub = pos[0] if pos else ""
        if "$" in sub:
            out.append((ASK, f"helmfile {RUNTIME_VERB_REASON}: {ON_WORDS}"))
        if sub in HELMFILE_RELEASE_WRITES:
            out.append((ASK, f"helmfile {sub} changes what runs on the cluster: {ON_WORDS}"))
    elif prog == "crusoe":
        rest, _ = split_globals(args, CRUSOE_GET_CREDENTIALS_VALUE_FLAGS)
        pos = positionals(rest)
        if pos[:3] == ["kubernetes", "clusters", "get-credentials"]:
            cluster = pos[3] if len(pos) > 3 else "<cluster>"
            out.append((ASK, f"adds a kubeconfig context for {cluster}: {ON_WORDS}"))
    return out


# Commands that record a commit on whatever branch is checked out. Committing on a
# repo's default branch is never right outside the repos committed on main by design.
COMMIT_MAKERS = {"commit", "merge", "cherry-pick", "revert", "am"}
COMMIT_MAKER_NON_COMMITS = {"--abort", "--quit", "--skip", "--dry-run"}
DEFAULT_BRANCH_EXEMPT = tuple(os.path.realpath(os.path.expanduser(p))
                              for p in ("~/.claude", "~/repos/configs",
                                        "~/repos/approve-no-look"))
DEFAULT_BRANCH_REASON = ("commits on {branch}, the default branch of {repo}: create a branch "
                         "first (CLAUDE.md: never work on the default branch)")
RUNTIME_VERB_REASON = ("verb is built at run time, so the hook cannot tell a read from a "
                       "write to live cluster state")
UNRESOLVED_REPO_REASON = ("commits in a repo whose path is built at run time, so the hook "
                          "cannot tell whether it is a default branch")


def git_out(repo_dir, *args):
    """A git read in repo_dir, or None when git cannot answer it."""
    try:
        proc = subprocess.run(["git", "-C", repo_dir, *args], capture_output=True,
                              text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def default_branch(repo_dir):
    remote_head = git_out(repo_dir, "symbolic-ref", "--quiet", "--short",
                          "refs/remotes/origin/HEAD")
    if remote_head:
        return remote_head.split("/", 1)[-1]
    for name in ("main", "master"):
        if git_out(repo_dir, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}"):
            return name
    return None


def switched_to(sub, rest):
    """The branch a `git switch` or `git checkout` in the same command moves to, or None."""
    pos = positionals(rest)
    for flag in ("-c", "-C", "--create", "--force-create", "-b", "-B", "--orphan"):
        if flag in rest:
            i = rest.index(flag)
            return rest[i + 1] if i + 1 < len(rest) else None
    if "--" in rest or len(pos) != 1:
        return None
    return pos[0] if sub in ("switch", "checkout") else None


def resolved_dir(base, path):
    """base joined with path, or None when either is known only once the command runs."""
    path = os.path.expanduser(path)
    if "$" in path:
        return None
    if os.path.isabs(path):
        return path
    return None if base is None else os.path.join(base, path)


def default_branch_commits(command, cwd):
    """A deny row for each commit the command makes on a repo's default branch.

    The working directory follows every `cd` and `git -C` in the command, and a branch
    switched to earlier in the same command counts as checked out. A git or filesystem
    lookup that fails adds no row: the hook denies everything when it raises. A path
    built by a substitution or a variable cannot be resolved here, so a commit made
    there asks instead.
    """
    out = []
    here = cwd
    switched = {}
    for prog, args, moves in invocations_with_moves(command):
        if prog in CHDIR_PROGRAMS:
            here = cd_target(here, prog, args) if moves else None
            continue
        if prog != "git":
            continue
        repo_dir, rest = here, list(args)
        while rest and rest[0] in ("-C", "-c", "--git-dir", "--work-tree", "--no-pager", "-P"):
            if rest[0] == "-C" and len(rest) > 1:
                repo_dir = resolved_dir(repo_dir, rest[1])
            rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
        if not rest:
            continue
        sub, rest = rest[0], rest[1:]
        if repo_dir is None:
            if sub in COMMIT_MAKERS and not COMMIT_MAKER_NON_COMMITS & set(rest):
                out.append((ASK, UNRESOLVED_REPO_REASON))
            continue
        top = git_out(repo_dir, "rev-parse", "--show-toplevel")
        if not top:
            continue
        top = os.path.realpath(top)
        if sub in ("switch", "checkout"):
            target = switched_to(sub, rest)
            created = any(f in rest for f in ("-c", "-C", "--create", "--force-create",
                                              "-b", "-B", "--orphan"))
            # A bare `checkout <name>` restores a file unless <name> is a branch.
            if target and (created or git_out(repo_dir, "rev-parse", "--verify", "--quiet",
                                              f"refs/heads/{target}")):
                switched[top] = target
            continue
        if sub not in COMMIT_MAKERS or COMMIT_MAKER_NON_COMMITS & set(rest):
            continue
        if top in DEFAULT_BRANCH_EXEMPT:
            continue
        branch = switched.get(top) or git_out(repo_dir, "symbolic-ref", "--quiet", "--short", "HEAD")
        if branch and branch == default_branch(repo_dir):
            out.append((DENY, DEFAULT_BRANCH_REASON.format(branch=branch, repo=top)))
    return out


def mcp_reads(tool_name):
    return tool_name.rsplit("__", 1)[-1].lower().startswith(MCP_READ_PREFIXES)


# What a script's text can hold that needs the user's words when typed as a command. Plain
# text over any language: the separator also covers a Python or JSON argument list.
WORD_SEP = r"""[\s"',\[\]]+"""
SCRIPT_WORDS_RES = (
    re.compile(rf"\bhelm{WORD_SEP}(?:install|upgrade|uninstall|delete|del|rollback)(?![\w-])"),
    re.compile(r"\bhelmfile\b.*\b(?:apply|sync|destroy|delete)\b"),
    re.compile(rf"\bkubectl\b.*?{WORD_SEP}(?:apply|delete|create|patch|scale|edit|replace"
               rf"|label|annotate|taint|cordon|uncordon|drain|evict|expose|autoscale|exec"
               rf"|attach|cp|rollout{WORD_SEP}(?:restart|undo))(?![\w-])"),
    re.compile(rf"\bgit{WORD_SEP}push\b"),
    re.compile(rf"\bgit{WORD_SEP}(?:rebase(?!{WORD_SEP}--(?:continue|abort|quit|skip))"
               rf"|pull{WORD_SEP}(?:-r|--rebase)|filter-(?:branch|repo)"
               rf"|reset{WORD_SEP}--(?:soft|mixed|hard|merge|keep))\b"),
    re.compile(rf"\b(?:docker|podman|buildah){WORD_SEP}push\b|\bbuildx\b.*--push\b"),
    re.compile(rf"\bglab{WORD_SEP}(?:release{WORD_SEP}create"
               rf"|mr{WORD_SEP}(?:create|merge|approve|note))\b"),
    re.compile(rf"\bgh{WORD_SEP}pr{WORD_SEP}(?:create|merge|review|comment)\b"),
)
SCRIPT_HTTP_WRITE_RES = (
    re.compile(r"(?:-X|--request)[\s=]*['\"]?(?:POST|PUT|PATCH|DELETE)\b"),
    re.compile(rf"\b(?:xh|http|https){WORD_SEP}(?:POST|PUT|PATCH|DELETE)\b"),
    re.compile(r"\bcurl\b.*\s(?:-d|--data(?:-raw|-binary|-urlencode)?|--json|-F|--form)\b"),
    re.compile(r"--post-data\b|--method[\s=]+['\"]?(?:POST|PUT|PATCH|DELETE)\b"),
    re.compile(r"\b(?:requests|httpx|session|client)\.(?:post|put|patch|delete)\("),
    # A field, a form or a body makes gh and glab api send a POST unless the line says GET.
    re.compile(r"\b(?:gh|glab)\s+api\b(?!.*(?:-X|--method)[\s=]*['\"]?GET\b)"
               r".*\s(?:-[fF]|--(?:raw-)?field|--form|--input)\b"),
)
LOOPBACK_IN_TEXT_RE = re.compile(r"\b(?:localhost|127\.\d+\.\d+\.\d+)\b|\[::1\]")
URL_IN_TEXT_RE = re.compile(r"[A-Za-z][\w+.-]*://[^\s'\"]+")
SCRIPT_SCAN_LIMIT = 2 * 1024 * 1024


def script_of(words):
    """The script file an invocation runs, as typed, or None when it runs no script file."""
    words = strip_prefix(words)
    if not words:
        return None
    prog, args = program_of(words), words[1:]
    if prog in ("bash", "sh", "zsh", "dash"):
        if shell_body(args) is not None:
            return None
        pos = positionals(args)
        return pos[0] if pos else None
    if PYTHON_RE.fullmatch(prog):
        return python_script(args)
    if prog == "uv" and uv_runs(args):
        tail = uv_run_tail(args)
        if tail and tail[0].endswith(".py"):
            return tail[0]
        return script_of(tail) if tail else None
    return words[0] if "/" in words[0] else None


def module_of(words):
    """The module a Python invocation runs with -m, with the letters among I, P and E given
    before it, or None."""
    words = strip_prefix(words)
    if not words:
        return None
    prog, args = program_of(words), words[1:]
    if PYTHON_RE.fullmatch(prog):
        run = python_run(args)
        return run[1:] if run and run[0] == "module" else None
    if prog == "uv" and uv_runs(args):
        tail = uv_run_tail(args)
        if tail and uv_runs_module(args):
            return tail[0], frozenset()
        return module_of(tail) if tail else None
    return None


# The environment variables the scans read, followed through export and unset.
TRACKED_ENV = ("PYTHONPATH", "UV_PYTHON")


def prefix_assignments(segment):
    """The NAME=value words ahead of the program, through every `uv run` layer, in order."""
    found, words = split_prefix(segment)
    while words and program_of(words) == "uv" and uv_runs(words[1:]):
        prefix, words = split_prefix(uv_run_tail(words[1:]))
        found = found + prefix
    return [w for w in found if ENV_ASSIGN_RE.match(w)]


def env_value(name, segment, exported):
    """The value the program a segment runs sees for name: the last assignment ahead of it,
    else what an earlier segment exported, else None."""
    value = exported.get(name)
    for w in prefix_assignments(segment):
        if w.startswith(name + "="):
            value = w.split("=", 1)[1]
    return value


def track_exports(words, shell_vars, exported):
    """Follow a bare assignment, an export or an unset of a tracked name. True when the
    segment was one of them, which runs no program to scan."""
    if not words:
        return True
    prog = program_of(words)
    if prog not in ("export", "unset"):
        return False
    for w in words[1:]:
        name, _, value = w.partition("=")
        if name not in TRACKED_ENV:
            continue
        if prog == "unset":
            exported.pop(name, None)
            shell_vars.pop(name, None)
        elif "=" in w:
            exported[name] = value
        elif name in shell_vars:
            exported[name] = shell_vars[name]
    return True


def import_roots(here, segment, letters, exported):
    """The directories Python searches for a -m module before its own library, as
    (shown, path) pairs, path None when only the shell knows it: the working directory
    unless -I or -P, then each PYTHONPATH entry the program sees unless -I or -E."""
    roots = [] if letters & {"I", "P"} else [("", here)]
    value = None if letters & {"I", "E"} else env_value("PYTHONPATH", segment, exported)
    if value is not None:
        roots = roots[:1] + [(e, resolved_dir(here, e) if e else here)
                             for e in value.split(":")]
    return roots


# The options of `uv python find` that take a value, besides uv's global ones.
UV_PYTHON_FIND_VALUE_FLAGS = ("--script", "--python-downloads-json-url")


def uv_interpreter_of(segment, exported):
    """The interpreter a uv or uvx command is given, which uv runs to query it: the value of
    -p or --python, the request `uv python find` names, else the UV_PYTHON the command sees,
    or None when none is given. The option wins over the environment, as it does in uv."""
    words = strip_prefix(segment)
    if not words or program_of(words) not in ("uv", "uvx"):
        return None
    args = words[1:]
    fallback = env_value("UV_PYTHON", segment, exported) or None
    if program_of(words) == "uvx":
        options = args
    elif uv_runs(args):
        options = uv_run_options(args)
    else:
        i = uv_subcommand(args)
        if i is None:
            return None
        if args[i] == "python" and args[i + 1:i + 2] == ["find"]:
            rest = args[i + 2:]
            k = 0
            while k < len(rest) and rest[k].startswith("-"):
                k += 2 if rest[k] in UV_GLOBAL_VALUE_FLAGS + UV_PYTHON_FIND_VALUE_FLAGS else 1
            if k < len(rest):
                return rest[k]
        options = args
    for i, a in enumerate(options):
        nxt = options[i + 1] if i + 1 < len(options) else ""
        if a.startswith("--python="):
            value = a.split("=", 1)[1]
        elif a == "--python":
            value = nxt
        # Only a word that starts with a dash is a bundle of short options.
        elif (a.startswith("-") and not a.startswith("--")
              and uv_short_flags(a)[0].endswith("p")):
            letters, next_word = uv_short_flags(a)
            value = nxt if next_word else a[len(letters) + 1:].lstrip("=")
        else:
            continue
        return value or None
    return fallback


def uv_interpreter_file(here, value):
    """The file uv runs to query the interpreter it is given: a directory's bin/python, the
    file itself for a path, or None for a version or a name uv looks up on PATH."""
    path = resolved_dir(here, value)
    if path is not None and os.path.isdir(path):
        return os.path.join(value, "bin", "python")
    return value if "/" in value else None


def module_files(name):
    """The files, relative to the working directory, that `python -m <name>` runs when the
    module is found there: each part of the name as a package's __init__.py or a module
    file - Python imports every parent before the last part - then a package's
    __main__.py."""
    parts = name.split(".")
    path = "/".join(parts)
    return (["/".join(parts[:k]) + "/__init__.py" for k in range(1, len(parts) + 1)]
            + ["/".join(parts[:k]) + ".py" for k in range(1, len(parts) + 1)]
            + [path + "/__main__.py"])


def listed(found):
    """The first lines a scan found, for a prompt's reason."""
    return "; ".join(found[:5]) + ("; ..." if len(found) > 5 else "")


def module_decisions(roots, name):
    """One ask when `python -m <name>` would load a file from one of the import roots whose
    text holds a command that needs words."""
    if "$" in name or "/" in name or "" in name.split(".") or not roots:
        return []
    if any(path is None for _, path in roots):
        return [(ASK, f"runs module {name} from a directory known only at run time, so the "
                      "file it loads from there could not be checked for commands that "
                      "change live or remote state")]
    found = [f"{os.path.join(shown, rel)}:{line}" for shown, path in roots
             for rel in module_files(name)
             for line in script_lines_needing_words(os.path.join(path, rel))]
    if not found:
        return []
    return [(ASK, f"runs module {name}, whose file on its import path holds commands "
                  f"that change live or remote state - {listed(found)}. One prompt covers "
                  "the whole run; no words needed")]


def script_lines_needing_words(path):
    """The lines of a script that hold a command needing the user's words, numbered."""
    try:
        with open(path, "rb") as f:
            data = f.read(SCRIPT_SCAN_LIMIT)
    except OSError:
        return []
    if b"\0" in data[:1024]:
        return []
    found = []
    for number, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
        # Loopback only when the line names no other URL: a loopback header beside a
        # remote target is still a remote write.
        loopback_only = (LOOPBACK_IN_TEXT_RE.search(line) is not None and all(
            url_is_loopback(u) for u in URL_IN_TEXT_RE.findall(line)))
        http_write = (any(r.search(line) for r in SCRIPT_HTTP_WRITE_RES)
                      and not loopback_only)
        if http_write or any(r.search(line) for r in SCRIPT_WORDS_RES):
            found.append(f"{number}: {line.strip()[:120]}")
    return found


def own_cli_copy(path, words, script):
    """True for a copy of this hook in a gate scratch root, run by Python as its own CLI:
    --selftest, or one command to classify after an optional --open. A staged copy's selftest
    holds every pattern the scan looks for, so scanning it would ask on every run."""
    real = os.path.realpath(path)
    if (not PYTHON_RE.fullmatch(program_of(words))
            or os.path.basename(real) != os.path.basename(__file__)
            or not inside_gate_scratch(real)):
        return False
    tail = words[words.index(script) + 1:] if script in words else []
    if tail[:1] == ["--open"]:
        tail = tail[1:]
    return tail == ["--selftest"] or (len(tail) == 1 and not tail[0].startswith("-"))


def script_decisions(command, cwd, exported=None):
    """One ask per script the command runs whose text holds a command that needs words.

    The working directory follows every `cd` in the command, as for commits; a script
    whose path is built at run time cannot be read, so it is not scanned. A relative script
    run where the directory is unknown asks, since its text could hold anything. exported
    holds the tracked variables the shell running the command already exports.
    """
    out = []
    here = cwd
    # What an export reaches is taken for the whole command, a subshell's included, which
    # can only add an ask.
    exported, shell_vars = dict(exported or {}), {}
    for line in command_lines(command):
        try:
            segments, _, apart, _ = parse_line(line)
        except ValueError:
            continue
        for segment, moves in zip(segments, cd_sticks(segments, apart)):
            words = strip_prefix(segment)
            if words and program_of(words) in CHDIR_PROGRAMS:
                here = cd_target(here, program_of(words), words[1:]) if moves else None
                continue
            if not words:
                shell_vars.update(w.split("=", 1) for w in segment if ENV_ASSIGN_RE.match(w))
            if track_exports(words, shell_vars, exported):
                continue
            # xargs runs the command after its own options, with the input's words added.
            while words and program_of(words) == "xargs":
                segment = xargs_rest(words[1:])
                words = strip_prefix(segment)
            # A shell's -c body runs as commands of its own, in a shell of its own, so its
            # scripts and modules are scanned like the line's, with the variables it is
            # handed, and its cd moves nothing here.
            # env's -C moves where the program runs, not the shell.
            seg_here = env_chdir(here, segment)
            inner_at, inner = uv_run_command(seg_here, words)
            if inner and program_of(inner) in ("bash", "sh", "zsh", "dash"):
                body = shell_body(inner[1:])
                if body is not None:
                    handed = dict(exported)
                    for w in prefix_assignments(segment):
                        name, _, value = w.partition("=")
                        if name in TRACKED_ENV:
                            handed[name] = value
                    out.extend(script_decisions(body, inner_at, handed))
            # uv's --directory moves where the segment's files are found, not the shell: the
            # command uv runs is found from every --directory down to it, and the interpreter
            # uv queries from the outer uv's own.
            ran_at, _ = uv_run_command(seg_here, words)
            at = uv_here(seg_here, words)
            module = module_of(words)
            if module:
                name, letters = module
                out.extend(module_decisions(import_roots(ran_at, segment, letters, exported),
                                            name))
            script = script_of(words)
            if script:
                out.extend(script_file_decisions(ran_at, words, script))
            # Each uv a `uv run` runs queries its own interpreter, from its own directory.
            layer, layer_at = segment, at
            while True:
                interpreter = uv_interpreter_of(layer, exported)
                interpreter_file = interpreter and uv_interpreter_file(layer_at, interpreter)
                if interpreter_file:
                    out.extend(script_file_decisions(layer_at, words, interpreter_file))
                layer_words = strip_prefix(layer)
                if not (layer_words and program_of(layer_words) == "uv"
                        and uv_runs(layer_words[1:])):
                    break
                layer = uv_run_tail(layer_words[1:])
                if not strip_prefix(layer):
                    break
                layer_at = uv_here(env_chdir(layer_at, layer), layer)
    return out


def script_file_decisions(here, words, script):
    """One ask when a file the segment runs holds a command that needs words."""
    path = resolved_dir(here, script)
    if here is None and path is None and "$" not in script:
        return [(ASK, f"runs {script} from a directory known only at run time, so its text "
                      "could not be checked for commands that change live or remote state")]
    # This script's own CLI only classifies text; its selftest holds every pattern.
    if path is None or os.path.realpath(path) == os.path.realpath(__file__):
        return []
    if own_cli_copy(path, words, script):
        return []
    found = script_lines_needing_words(path)
    if not found:
        return []
    return [(ASK, f"runs {script}, whose text holds commands that change live or remote "
                  f"state - {listed(found)}. One prompt covers the whole run; no words needed")]


SHELL_PATH_REASON = ("a write path, or the directory a cd before it moves to, is built by the "
                     "shell at run time, so the gate cannot tell whether it lands in a repo: "
                     "write it out literally")
NAMED_REF_FETCH_REASON = ("a fetch into a named ref leaves the ref in the repo: drop the "
                          "`:<dst>` and pin the commit with `git rev-parse FETCH_HEAD`")


def named_ref_fetch(words):
    """True for a git fetch with a destination, every one a full ref outside refs/heads and
    refs/tags: it parks a commit under a ref of its own and moves no branch or tag."""
    words = strip_prefix(words)
    if not words or program_of(words) != "git":
        return False
    rest = git_subcommand_args(words[1:])
    if not rest or rest[0] != "fetch":
        return False
    dests = [p.split(":", 1)[1] for p in positionals(rest[1:])[1:] if ":" in p]
    return bool(dests) and all(d.startswith("refs/")
                               and not d.startswith(("refs/heads/", "refs/tags/"))
                               for d in dests)


def decide_bash(tool_input, gate_open, cwd, named):
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise ValueError("Bash call without a command string")
    command = with_assigned_path(command)
    out = []
    if scratch_rm_count(command):
        out.append((DENY, SCRATCH_RM_REASON))
    elif rm_chained(command):
        out.append((DENY, RM_CHAINED_REASON))
    if writes_unnamed_tmp(command, named):
        out.append((DENY, TMP_WRITE_REASON))
    if changes_env_file(command, cwd):
        out.append((ASK, ENV_WRITE_REASON))
    if changes_rating_config(command, cwd):
        out.append((ASK, RATING_CONFIG_REASON))
    for prog, args in (inner for outer in invocations(command)
                       for inner in uv_run_invocations(*outer)):
        out.extend(every_state_decisions(prog, args))
        # Not an every-state decision: gate_blockers passes a command one of those asks
        # about, which would turn the closed gate's deny into an ask.
        if adds_worktree(prog, args):
            out.append((ASK, WORKTREE_REASON))
    out.extend(default_branch_commits(command, cwd))
    out.extend(script_decisions(command, cwd))
    out.extend(clone_decisions(command, cwd))
    blockers = gate_blockers(command, cwd) if not gate_open and \
        classify_command(command) != READ else []
    if blockers:
        if only_unknown_writes(blockers):
            out.append((ASK, "unclassified - fix the handler in the tkay-tools command parser"))
        elif held_for_shell_paths(blockers) or held_for_shell_dir(command, cwd):
            out.append((DENY, SHELL_PATH_REASON))
        elif all(words is not None and named_ref_fetch(words) for words in blockers):
            out.append((DENY, NAMED_REF_FETCH_REASON))
        else:
            out.append((DENY, BASH_REFUSAL))
    if rm_escapes_scratch(command):
        out.append((ASK, "rm names a path outside the scratch root next to a scratch path"))
    return out


def decide_mcp(tool_name, tool_input):
    tool = tool_name.rsplit("__", 1)[-1]
    if tool == SLACK_SEND:
        if tool_input.get("thread_ts") and tool_input.get("channel_id") in ALERT_CHANNEL_IDS:
            return []
        return [(ASK, "a Slack message outside the linked alert thread: send it only when the "
                      "user's message allowed this message in words, otherwise show its full "
                      "text")]
    if (tool == SLACK_REACT and tool_input.get("channel_id") in ALERT_CHANNEL_IDS
            and tool_input.get("emoji") == ALERT_REACTION):
        return []
    reads = mcp_reads(tool_name)
    lower = tool.lower()
    server = tool_name.split("__")[1].lower() if tool_name.count("__") >= 2 else ""
    # `resolve` is a read prefix elsewhere, but on a code host it resolves a review thread.
    thread_move = (any(h in server for h in MCP_CODE_HOSTS)
                   and (not reads or lower.startswith("resolve"))
                   and any(w in lower for w in MCP_THREAD_WORDS))
    if thread_move or (not reads and any(w in lower for w in MCP_MR_MOVE_WORDS)):
        return [(ASK, MR_MOVE_REASON)]
    # The server name carries the environment under both forms a connector shows up as.
    if lower == "api_call" and "backoffice" in server:
        if "prod" in server:
            return [(ASK, "a write to the prod backoffice changes live deployments and "
                          f"scaling: {ON_WORDS}")]
        return []
    return []


def decide(tool_name, tool_input, gate_open, cwd=None, named=()):
    """The strictest decision over every matching row, as (decision, reason) or None.

    cwd is the directory the tool call runs in, which a Bash commit is judged against;
    named holds the paths under /tmp the user's messages named.
    """
    if EXTENSION_ERROR is not None:
        return (DENY, f"tool-gate.py failed closed: {EXTENSION_ERROR}")
    if tool_name == "Bash":
        out = decide_bash(tool_input, gate_open, cwd or os.getcwd(), named)
    elif tool_name in PATH_FIELD:
        path = tool_input.get(PATH_FIELD[tool_name])
        out = [(DENY, TMP_WRITE_REASON)] if isinstance(path, str) and unnamed_tmp(path, named) \
            else []
        if isinstance(path, str) and env_file(path):
            out.append((ASK, ENV_WRITE_REASON))
        if isinstance(path, str) and rating_config(path):
            out.append((ASK, RATING_CONFIG_REASON))
        if not gate_open and inside_repo(path):
            out.append((DENY, REFUSAL))
    elif tool_name == "EnterWorktree":
        out = [(ASK, WORKTREE_REASON)] if gate_open else [(DENY, REFUSAL)]
    elif tool_name.startswith("mcp__"):
        out = decide_mcp(tool_name, tool_input)
    else:
        out = []
    return max(out, key=lambda d: DECISION_RANK[d[0]]) if out else None


def session_file(directory, session_id):
    return os.path.join(directory, re.sub(r"[^A-Za-z0-9_.-]", "_", session_id))


def gate_is_open(session_id):
    if not isinstance(session_id, str) or not session_id:
        return False
    try:
        with open(session_file(STATE_DIR, session_id)) as f:
            return f.read().strip() in OPEN_STATES
    except FileNotFoundError:
        return False


def named_scratch_paths(session_id):
    if not isinstance(session_id, str) or not session_id:
        return ()
    try:
        with open(session_file(SCRATCH_PATHS_DIR, session_id)) as f:
            return tuple(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return ()


def hook_output(payload):
    tool_name = payload.get("tool_name")
    gated = tool_name in GATED_TOOLS or (isinstance(tool_name, str) and tool_name.startswith("mcp__"))
    if not gated:
        return None
    output: dict = {"hookEventName": "PreToolUse"}
    try:
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            raise ValueError("tool_input missing")
        session_id = payload.get("session_id")
        decision = decide(tool_name, tool_input, gate_is_open(session_id), payload.get("cwd"),
                          named_scratch_paths(session_id))
        # The rating hook leaves auto mode's calls as written, so a prompt the gate raises
        # there carries the rating in its reason instead; the reason never changes the call.
        if decision and decision[0] == ASK and payload.get("permission_mode") == AUTO_MODE \
                and tool_name == "Bash" and isinstance(tool_input.get("command"), str):
            decision = (ASK, f"{classify_command(tool_input['command'])} · {decision[1]}")
    except Exception as exc:
        decision = (DENY, f"tool-gate.py failed closed: {type(exc).__name__}: {exc}")
    if decision:
        output["permissionDecision"], output["permissionDecisionReason"] = decision
    return {"hookSpecificOutput": output}


def main():
    payload = json.load(sys.stdin)
    result = hook_output(payload)
    if result is not None:
        json.dump(result, sys.stdout)


# ----- CLI ----------------------------------------------------------------------------

def describe(tool_name, tool_input, gate_open):
    decision = decide(tool_name, tool_input, gate_open)
    gate_decision = f"{decision[0]}: {decision[1]}" if decision else "-"
    if tool_name == "Bash":
        return f"{classify_command(tool_input['command'])}  {gate_decision}"
    return gate_decision


def selftest():
    global GATE_SCRATCH_ROOTS, TMP_ROOT, REPO_ROOTS, SCRATCH_ROOTS, SCRATCH_PREFIXES, EXTENSION_ERROR
    home = os.path.expanduser("~")
    # A directory under a repo root, standing in for a repo the gate guards.
    rx = os.path.join(REPO_ROOTS[0], "x")
    scratch = GATE_SCRATCH_ROOTS[0]
    alert = "C0ALERT"
    ALERT_CHANNEL_IDS.add(alert)
    cases = [
        # (gate_open, tool_name, tool_input, expected decision)
        (False, "Bash", "kubectl get pods --context X -n Y", None),
        (False, "Bash", "kubectl get pods --context=X --namespace=Y", None),
        (False, "Bash", "kubectl get pods -nY --context X", None),
        (False, "Bash", "kubectl --context X -n Y get pods", None),
        (True, "Bash", "kubectl --context X -n Y delete pod p", ASK),
        (False, "Bash", "kubectl --context X -n Y delete pod p", ASK),
        # A verb built at run time could be any of the writes above.
        (True, "Bash", "kubectl $(echo delete) pod p --context X -n Y", ASK),
        (True, "Bash", 'kubectl "$(echo delete)" pod p --context X -n Y', ASK),
        (True, "Bash", "V=delete; kubectl $V pod p --context X -n Y", ASK),
        (True, "Bash", "helm $(echo uninstall) r --kube-context X -n Y", ASK),
        (True, "Bash", "kubectl get pods -l app=$(echo x) --context X -n Y", None),
        # A substitution closed right before an operator hides nothing after it.
        (True, "Bash", "echo $(ls); kubectl delete pod p --context X -n Y", ASK),
        (True, "Bash", "echo $(ls)&&helm uninstall r --kube-context X -n Y", ASK),
        (True, "Bash", "echo `ls`|kubectl delete pod p --context X -n Y", ASK),
        (True, "Bash", "helm --kube-context X -n Y uninstall r", ASK),
        (False, "Bash", "helm --kube-context X -n Y uninstall r", ASK),
        (True, "Bash", "helm del r --kube-context X -n Y", ASK),
        (True, "Bash", "helm rollback r 1 --kube-context X -n Y", ASK),
        (False, "Bash", "helm rollback r 1 --kube-context X -n Y", ASK),
        (True, "Bash", "helm rollback r 1 --kube-context X -n Y --force-conflicts", ASK),
        (False, "Bash", "helm list --kube-context X -n Y", None),
        (False, "Bash", "kubectl get nodes --context X -L atero/user", None),
        (False, "Bash", "kubectl get --raw /api/v1/nodes/n/proxy/stats/summary --context X", None),
        (False, "Bash", "kubectl get pods -A --context X", None),
        (True, "Bash", "kubectl config get-contexts", None),
        (True, "Bash", "kubectl config current-context", None),
        (True, "Bash", "kubectl kustomize ./overlay", None),
        # krew installs kubectl plugins under its own root and never reaches a cluster.
        (True, "Bash", "kubectl krew install ctx", None),
        (False, "Bash", "kubectl krew list", None),
        (False, "Bash", "kubectl krew install ctx", None),
        (False, "Bash", "kubectl krew upgrade", None),
        (False, "Bash", f"KREW_ROOT={rx}/k kubectl krew install ctx", DENY),
        (True, "Bash", "kubectl completion zsh", None),
        (True, "Bash", "kubectl version --client", None),
        (True, "Bash", "helm template r ./chart -f values.yaml", None),
        (True, "Bash", "helm lint ./chart", None),
        (True, "Bash", "helm show values ./chart", None),
        (True, "Bash", "helm search repo x", None),
        (True, "Bash", "helm pull oci://x/y --version 1", None),
        (True, "Bash", "helm package ./chart", None),
        (True, "Bash", "helm push x.tgz oci://registry/charts", None),
        (True, "Bash", "helm registry login registry", None),
        (True, "Bash", "helm create chart", None),
        (True, "Bash", "helm env", None),
        (True, "Bash", "helm verify x.tgz", None),
        (True, "Bash", "helm repo list", None),
        (False, "Bash", "helm repo list", None),
        (False, "Bash", f"helm repo index {rx}/charts", DENY),
        # helm's aliases of a subcommand are the subcommand.
        (False, "Bash", "helm dep list ./chart", None),
        (False, "Bash", "helm dependencies list ./chart", None),
        (False, "Bash", f"helm dep build {scratch}c", None),
        (False, "Bash", "helm dep build ./chart", DENY),
        # helm repo add, update and remove write only helm's repositories file and caches.
        (False, "Bash", "helm repo add x https://charts.example.com", None),
        (False, "Bash", "helm repo up", None),
        (False, "Bash", "helm repo rm x", None),
        (False, "Bash", f"helm repo add x u --repository-config {scratch}r.yaml", None),
        (False, "Bash", f"helm repo add x u --repository-config={rx}/r.yaml", DENY),
        (False, "Bash", f"helm repo update --repository-cache {rx}/c", DENY),
        (False, "Bash", f"helm repo update --content-cache={scratch}c", None),
        (False, "Bash", f"helm repo update --content-cache {scratch}c", DENY),
        (False, "Bash", f"helm repo update --content-cache={rx}/c", DENY),
        (False, "Bash", f"HELM_REPOSITORY_CONFIG={rx}/r.yaml helm repo add x u", DENY),
        # A plugin's hooks are code the hook cannot read; plugin package writes where it runs.
        (False, "Bash", "helm plugin install https://github.com/x/y", None),
        (False, "Bash", "helm plugin rm x", None),
        (False, "Bash", f"helm plugin package {rx}/p", DENY),
        (True, "Bash", "helm dependency update ./chart", None),
        (True, "Bash", "helm plugin list", None),
        (True, "Bash", "helm version", None),
        (False, "Bash", "kubectl get pods -o name --context X -n Y | xargs kubectl delete", DENY),
        (False, "Bash", "kubectl exec p --context X -n Y -- curl localhost:8000/health", None),
        (False, "Bash", "kubectl exec p --context X -n Y -- rm -rf /data", ASK),
        (False, "Bash", "kubectl exec -it p --context X -n Y -- sh", ASK),
        (False, "Bash", "kubectl cp p:/x /tmp/y --context X -n Y", DENY),
        (True, "Bash", "kubectl cp p:/x /tmp/y --context X -n Y", None),
        (True, "Bash", "kubectl cp ./f p:/x --context X -n Y", ASK),
        (True, "Bash", "kubectl cp -c ctr ./f ns/p:/x --context X -n Y", ASK),
        (True, "Bash", "kubectl cp ns/p:/x ./f -c ctr --context X -n Y", None),
        (True, "Bash", "kubectl exec p --context X -n Y -- rm -rf /data", ASK),
        (True, "Bash", "kubectl exec -it p --context X -n Y -- sh", ASK),
        (True, "Bash", "kubectl exec p --context X -n Y -- curl localhost:8000/health", None),
        (True, "Bash", "kubectl attach p -it --context X -n Y", ASK),
        (False, "Bash", "kubectl attach p -it --context X -n Y", ASK),
        (False, "Bash", f"git log -1 --output={home}/.claude/lfg-state/abc", DENY),
        (False, "Bash", "git log -1", None),
        (False, "Bash", "git merge-tree --write-tree a b", None),
        (False, "Bash", "git merge a", DENY),
        (False, "Bash", "git stash", DENY),
        (False, "Bash", "git restore .", DENY),
        (False, "Bash", "git checkout -- .", DENY),
        (False, "Bash", "git worktree add ../y b", DENY),
        (True, "Bash", "git worktree add ../y b", ASK),
        (True, "Bash", "git -C /x worktree add -b n ../y", ASK),
        (True, "Bash", "git worktree list", None),
        (True, "Bash", "git worktree remove ../y", None),
        (False, "Bash", "git -C /x worktree add ../y", ASK),
        (False, "Bash", "make test", None),
        (False, "Bash", "make test 2>&1", None),
        (False, "Bash", "crusoe kubernetes clusters get-credentials --help 2>/dev/null | head", None),
        (False, "Bash", "ls; 2>&1 ls", None),
        (False, "Bash", "(ls)2>&1", None),
        (False, "Bash", "head -n 5 2>&1 > out.txt", DENY),
        (False, "Bash", "make build", DENY),
        (False, "Bash", "git fetch", None),
        (False, "Bash", "git fetch --force", DENY),
        (False, "Bash", "git fetch origin main:main", DENY),
        (False, "Bash", "git fetch origin main", None),
        (False, "Bash", "git lfs ls-files", None),
        (False, "Bash", "git lfs env", None),
        (False, "Bash", "git lfs pointer --file=x.tgz", None),
        (False, "Bash", "git lfs logs last", None),
        (False, "Bash", "git lfs logs clear", DENY),
        (False, "Bash", "git lfs track '*.tgz'", DENY),
        (False, "Bash", "git-lfs ls-files", None),
        (False, "Bash", "git-lfs install", DENY),
        (False, "Bash", "uv sync", DENY),
        (False, "Bash", f"touch {scratch}x", DENY),
        (True, "Bash", f"touch {scratch}x", DENY),
        (False, "Bash", f"rm {scratch}x", DENY),
        (False, "Bash", f"echo hi > {scratch}x", DENY),
        (True, "Bash", "echo hi > /tmp/claude/x 2>/dev/null", DENY),
        (True, "Bash", f"git show HEAD | tee {scratch}x", DENY),
        (True, "Bash", f"mkdir -p {scratch}d", DENY),
        (True, "Bash", f"cp {home}/x {scratch}x", DENY),
        (True, "Bash", f"cp {scratch}x {home}/.cache/x", None),
        (False, "Bash", f"D={home}/.cache/d && mkdir -p $D && git archive HEAD | tar -x -C $D",
         None),
        (False, "Bash", f"D={home}/.cache/d\nmkdir -p ${{D}}/m", None),
        (True, "Bash", f"diff -q {scratch}x {home}/.cache/x", None),
        (False, "Bash", f"touch {home}/.cache/x", None),
        (False, "Bash", "mkdir -p ~/.cache/claude-handoff/d", None),
        (False, "Bash", "git -C /x archive HEAD | tar -x -C ~/.cache/claude-handoff/d", None),
        (False, "Bash", "echo hi > ~/.cache/x", None),
        (False, "Bash", "mkdir -p '~/.cache/d'", DENY),
        (False, "Bash", 'mkdir -p "~"/.cache/d', DENY),
        (False, "Bash", "mkdir -p \\~/.cache/d", DENY),
        (False, "Bash", "mkdir -p ''~/.cache/d", DENY),
        (False, "Bash", "echo '~' && mkdir -p ~/.cache/d", DENY),
        (False, "Bash", "echo '~'\nmkdir -p ~/.cache/d", DENY),
        (False, "Bash", "export HOME=/x; mkdir -p ~/.cache/d", DENY),
        (False, "Bash", "HOME=/x\nmkdir -p ~/.cache/d", DENY),
        (False, "Bash", "mkdir -p ~/repos/d", DENY),
        (False, "Bash", "mkdir -p ~other/.cache/d", DENY),
        (False, "Bash", "tar -x -C ~/repo", DENY),
        (False, "Bash", f"touch {home}/.claude/plans/x.md", None),
        (False, "Bash", f"touch {home}/.claude/projects/p/memory/x.md", None),
        (False, "Bash", "git -C /x archive origin/b", None),
        (False, "Bash", f"git archive HEAD -o {home}/x.tar", DENY),
        (False, "Bash", f"git archive HEAD -o{home}/x.tar", DENY),
        (False, "Bash", f"git archive HEAD --output={home}/x.tar", DENY),
        (False, "Bash", f"git -C /x archive origin/b | tar -x -C {scratch}d", None),
        (False, "Bash", f"git -C /x archive -o {scratch}d/x.tar HEAD", None),
        (False, "Bash", f"git -C /x archive HEAD -o{scratch}d/x.tar", None),
        (False, "Bash", f"git -C /x archive HEAD --output={scratch}d/x.tar", None),
        (False, "Bash", f"git archive -o --work-tree=x {scratch}y.tar HEAD", DENY),
        (False, "Bash", f"git --git-dir={rx}/.git archive -o {scratch}y.tar HEAD", None),
        (False, "Bash", f"git merge-file {scratch}s.md {scratch}b.md {scratch}n.md", None),
        (False, "Bash", f"git merge-file -L a -L b -L c {scratch}s.md {home}/b.md {home}/n.md",
         None),
        (False, "Bash", f"git merge-file -p {home}/s.md {home}/b.md {home}/n.md", None),
        (False, "Bash", f"git merge-file --stdout {home}/s.md {home}/b.md {home}/n.md", None),
        (False, "Bash", f"git merge-file {home}/s.md {scratch}b.md {scratch}n.md", DENY),
        (False, "Bash", "git merge-file s.md b.md n.md", DENY),
        (False, "Bash", f"git merge-file -L {scratch}s.md {home}/s.md {home}/b.md {home}/n.md",
         DENY),
        (False, "Bash", f"git merge-file --object-id -p {scratch}s {scratch}b {scratch}n", DENY),
        (False, "Bash", f"git merge-file -L -p -L b -L c {rx}/s.md {rx}/b.md {rx}/n.md", DENY),
        (False, "Bash", f"git merge-file -p --no-stdout {rx}/s.md {rx}/b.md {rx}/n.md", DENY),
        (False, "Bash", f"git merge-file -p --no-std {rx}/s.md {rx}/b.md {rx}/n.md", DENY),
        (False, "Bash", f"git -C {rx} merge-file -- -p {scratch}b.md {scratch}n.md", DENY),
        (False, "Bash", f"git merge-file -qL {scratch}s.md {rx}/s.md {rx}/b.md {rx}/n.md", DENY),
        (False, "Bash", f"git merge-file -p -L --work-tree=x --no-stdout {rx}/s.md {rx}/b.md "
                        f"{rx}/n.md", DENY),
        (False, "Bash", f"git merge-file --marker-size 9 --diff-algorithm histogram "
                        f"{scratch}s.md {rx}/b.md {rx}/n.md", None),
        (False, "Bash", f"git -C {rx} archive -o x.tar HEAD", DENY),
        (False, "Bash", f"git -C {rx} symbolic-ref --short refs/remotes/origin/HEAD", None),
        (False, "Bash", f"git -C {rx} symbolic-ref -q HEAD", None),
        (False, "Bash", f"git -C {rx} symbolic-ref HEAD refs/heads/x", DENY),
        (False, "Bash", f"git -C {rx} symbolic-ref -d refs/remotes/origin/HEAD", DENY),
        (False, "Bash", f"git -C {rx} symbolic-ref -m why HEAD refs/heads/x", DENY),
        (False, "Bash", f"git -C {rx} symbolic-ref -qd refs/remotes/origin/HEAD", DENY),
        (False, "Bash", f"git -C {rx} symbolic-ref --del refs/remotes/origin/HEAD", DENY),
        (False, "Bash", f"git -C {rx} archive -o {scratch}x.tar -o {home}/x.tar HEAD", DENY),
        (False, "Bash", f"tar -xzf a.tgz --directory={scratch}d", None),
        (False, "Bash", f"tar -x --strip-components=1 -C {scratch}d -f a.tar", None),
        (False, "Bash", f"tar -x -C {home}/repo", DENY),
        (False, "Bash", "tar -x", DENY),
        (False, "Bash", f"tar -xP -C {scratch}d", DENY),
        (False, "Bash", f"tar -x --absolute-names -C {scratch}d", DENY),
        (False, "Bash", f"tar -c -C {scratch}d -f {home}/x.tar .", DENY),
        (False, "Bash", f"tar -x --to-command=sh -C {scratch}d", DENY),
        (False, "Bash", f"tar -xC {home}/repo -C {scratch}d", DENY),
        (False, "Bash", f"tar -x -C {scratch}d -C rel", None),
        (False, "Bash", f"tar -x -C {scratch} -C ../x", DENY),
        (False, "Bash", "tar -xzOf a.tgz common/x.tpl | diff - x.tpl", None),
        (False, "Bash", "tar xzOf a.tgz common/x.tpl", None),
        (False, "Bash", "tar -x --to-stdout --file=a.tgz m", None),
        (False, "Bash", "tar -xzf a.tgz m", DENY),
        (False, "Bash", "tar -xO --to-command=sh -f a.tgz", DENY),
        (False, "Bash", "tar -xOP -f a.tgz", DENY),
        (False, "Bash", f"tar -xO -C {home}/repo -f a.tgz", DENY),
        (False, "Bash", "tar -cOf a.tar .", DENY),
        (False, "Bash", f"touch {home}/repos/probe", DENY),
        (False, "Bash", "touch /tmp/probe.md", DENY),
        (False, "Bash", "tmux list-clients -F '#{client_name} #{client_width}x#{client_height}'", None),
        (False, "Bash", "tmux showw -g aggressive-resize", None),
        (False, "Bash", "tmux lsp -a", None),
        (False, "Bash", "tmux kill-server", DENY),
        (False, "Bash", "tmux capture-pane -p -t x", None),
        (False, "Bash", "tmux capturep -pJS - -t x", None),
        (False, "Bash", "tmux capture-pane -t x", DENY),
        (False, "Bash", "tmux capture-pane -tp", DENY),
        (False, "Bash", "tmux capture-pane -S -p", DENY),
        (False, "Bash", "tmux capture-pane -e -p -S -50", None),
        (False, "Bash", "time ssh -v -o BatchMode=yes -o ConnectTimeout=15 -T git@gitlab.com", None),
        (False, "Bash", "ssh -T -p 22 -l git gitlab.com", None),
        (False, "Bash", "ssh -G gitlab.com", None),
        (False, "Bash", "ssh git@gitlab.com personal_access_token t api 30", DENY),
        (False, "Bash", "ssh -T host", DENY),
        (False, "Bash", "ssh -O exit git@gitlab.com", DENY),
        (False, "Bash", f"touch {scratch}../x", DENY),
        (True, "Bash", f"rm -rf {scratch}x {home}/.cache/x", ASK),
        (True, "Bash", f"rm -rf {scratch}x", DENY),
        (True, "Bash", "make test; rm /x/a", DENY),
        (True, "Bash", "cd /x && rm a", None),
        (True, "Bash", "rm /x/a; rm /x/b", None),
        (True, "Bash", "rm -f /x/a || true", None),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", ASK),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --reset-then-reuse-values --dry-run", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values --dry-run", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --dry-run", None),
        (True, "Bash", "CRUSOE_PROFILE=p crusoe kubernetes clusters get-credentials --project-name j -y c", ASK),
        (True, "Bash", "crusoe kubernetes clusters get-credentials c --project-name j", ASK),
        (False, "Bash", "crusoe kubernetes clusters get-credentials --project-name j c", ASK),
        (True, "Bash", "crusoe kubernetes clusters list --project-name j", None),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --dry-run", None),
        (False, "Bash", "helm install r ./c --kube-context X -n Y", ASK),
        (True, "Bash", "helmfile --kube-context X apply", ASK),
        (False, "Bash", "helmfile --kube-context X sync", ASK),
        (True, "Bash", "helmfile -e dev --kube-context X destroy", ASK),
        (True, "Bash", "helmfile --kube-context X diff", None),
        (False, "Bash", "helmfile template", None),
        # A whole suite is asked about in chat, never by the hook, so a goal can run one.
        (True, "Bash", "pytest", None),
        (False, "Bash", "pytest tests/", None),
        (True, "Bash", "uv run pytest -q", None),
        (True, "Bash", "python3 -m pytest tests", None),
        (True, "Bash", "go test ./...", None),
        (True, "Bash", "cargo test", None),
        (True, "Bash", "cargo test -p mycrate", None),
        (True, "Bash", "make test", None),
        (False, "Bash", "npm test", None),
        (False, "Bash", "npm run lint", None),
        (True, "Bash", "pytest tests/test_x.py", None),
        (True, "Bash", "pytest -k name", None),
        (True, "Bash", "pytest x.py::test_y", None),
        (True, "Bash", "uv run pytest tests/test_x.py -q", None),
        (True, "Bash", "go test ./pkg/foo -run TestX", None),
        (True, "Bash", "go test ./pkg/foo", None),
        (True, "Bash", "cargo test name", None),
        (True, "Bash", "./scripts/run-tests.sh", None),
        # -mod=mod lets a build command rewrite go.mod and go.sum where it runs.
        (False, "Bash", "go test -mod=mod ./pkg/foo", DENY),
        (False, "Bash", "GOFLAGS=-mod=mod go test ./pkg/foo", DENY),
        (False, "Bash", "GOFLAGS=-mod=mod go vet ./pkg/foo", DENY),
        (False, "Bash", "go list -mod=mod ./...", DENY),
        (False, "Bash", f"cd {scratch}d && GOFLAGS=-mod=mod go vet ./...", None),
        # A test run passes the gate like other opaque code, unless its own flags write
        # beside the tests: an update flag, or Go's -mod=mod.
        (False, "Bash", "go test ./pkg/foo", None),
        (False, "Bash", "uv run pytest tests/test_x.py", None),
        (False, "Bash", f"cd {scratch}d && go test -mod=mod ./pkg/foo", None),
        (False, "Bash", "go test ./pkg/foo -update", DENY),
        # -C names the module's directory; the subcommand after it decides the rating.
        (False, "Bash", f"go -C {rx} test ./pkg/foo", None),
        (False, "Bash", f"go -C={rx} test ./pkg/foo", None),
        (False, "Bash", f"go --C {rx} vet ./...", None),
        (False, "Bash", f"go -C {rx} build ./...", None),
        (False, "Bash", f"go -C {rx} build -o bin/x ./cmd/x", DENY),
        (False, "Bash", f"go -C {rx} mod tidy", DENY),
        (False, "Bash", f"go -C {rx} test -update ./pkg/foo", DENY),
        (False, "Bash", f"caffeinate -i go -C {rx} test ./pkg/foo > {home}/.cache/claude-handoff/s/t.log 2>&1", None),
        (True, "Bash", "go test ./pkg/foo -update", None),
        (False, "Bash", "pytest tests/test_x.py --snapshot-update", DENY),
        (False, "Bash", "python3 -m pytest tests/test_x.py --snapshot-update", DENY),
        (False, "Bash", "uv run pytest tests/test_x.py --snapshot-update", DENY),
        (False, "Bash", "cargo test name -- --update", DENY),
        (False, "Bash", f"cd {scratch}d && go test ./pkg/foo -update", None),
        (False, "Bash", f"cd {scratch}d && pytest tests/test_x.py --snapshot-update", None),
        # A script's flags are its own.
        (False, "Bash", "python3 /x/run.py --update", None),
        (True, "Bash", "xh PUT https://example.com/x a:=1", ASK),
        (True, "Bash", "xh https://example.com/x a=1", ASK),
        (True, "Bash", "curl -X DELETE https://example.com/x", ASK),
        (True, "Bash", "curl -d x https://example.com/x", ASK),
        (True, "Bash", "curl -sS -H 'Accept: x' --json '{}' https://example.com/x", ASK),
        (True, "Bash", 'xh PUT "$URL" a:=1', ASK),
        (False, "Bash", "xh PUT https://example.com/x a:=1", ASK),
        (True, "Bash", "wget --post-data=a=1 https://example.com/x", ASK),
        (True, "Bash", "xh PUT :8081/x a:=1", None),
        (True, "Bash", "xh PUT http://localhost:8081/x a:=1", None),
        (True, "Bash", "xh PUT http://127.0.0.1:8081/x a:=1", None),
        (True, "Bash", "curl -X PUT localhost:8081/x -d a", None),
        (True, "Bash", "curl -H 'Origin: http://localhost' -X POST https://example.com/x", ASK),
        (True, "Bash", "wget --header='Referer: http://localhost' --post-data=a https://e.com/x",
         ASK),
        (True, "Bash", "curl -X PUT 'http://[::1]:8081/x' -d a", None),
        (True, "Bash", "xh --offline PUT https://example.com/x a:=1", None),
        (True, "Bash", "curl -G -d q=1 https://example.com/x", None),
        (False, "Bash", "xh GET https://example.com/x", None),
        (False, "Bash", "curl https://example.com/x", None),
        (True, "Bash", "git push origin main", DENY),
        (False, "Bash", "git push origin main", DENY),
        (True, "Bash", "git lfs push origin main", DENY),
        (False, "Bash", "git lfs push origin main", DENY),
        (True, "Bash", "git lfs push --all origin", DENY),
        (True, "Bash", "git-lfs push origin main", DENY),
        (False, "Bash", "git lfs lock x.bin", DENY),
        (True, "Bash", "git lfs unlock x.bin", None),
        (True, "Bash", "git push --dry-run", DENY),
        (True, "Bash", "git -C /x push origin main", DENY),
        (True, "Bash", "git -c user.name=x --no-pager push", DENY),
        (True, "Bash", "git --git-dir=/x/.git push", DENY),
        (True, "Bash", "git push origin v1.2.3", DENY),
        (True, "Bash", "git commit -m 'push it' && git push -f", DENY),
        (True, "Bash", "git commit -m 'git push later'", None),
        (True, "Bash", "git rebase main", ASK),
        (True, "Bash", "git rebase -i HEAD~3", ASK),
        (True, "Bash", "GIT_SEQUENCE_EDITOR=true git rebase -S -i abc1234~1", ASK),
        (True, "Bash", "git -C /x rebase main", ASK),
        (True, "Bash", "git rebase --continue", None),
        (True, "Bash", "git rebase --abort", None),
        (True, "Bash", "git pull --rebase", ASK),
        (True, "Bash", "git pull -r origin main", ASK),
        (True, "Bash", "git pull", None),
        (True, "Bash", "git reset --soft HEAD~1", ASK),
        (True, "Bash", "git reset HEAD~2", ASK),
        (True, "Bash", "git reset abc1234def", ASK),
        (True, "Bash", "git reset -- file.py", None),
        (True, "Bash", "git reset file.py", None),
        (True, "Bash", "git reset", None),
        (True, "Bash", "git commit --amend --no-edit", None),
        (True, "Bash", "git filter-repo --path x", ASK),
        (True, "Bash", "glab mr create --fill", ASK),
        (False, "Bash", "glab mr create --fill", ASK),
        (True, "Bash", "glab -R g/p mr merge 3", ASK),
        (True, "Bash", "glab mr approve 3", ASK),
        (True, "Bash", "glab mr close 3", ASK),
        (True, "Bash", "glab mr reopen 3", ASK),
        (True, "Bash", "glab mr rebase 3", ASK),
        (True, "Bash", "glab mr accept 3", ASK),
        (True, "Bash", "glab mr new --fill", ASK),
        (True, "Bash", "glab mr for 12", ASK),
        (True, "Bash", "gh pr new --fill", ASK),
        (True, "Bash", "gh pr create --fill", ASK),
        (True, "Bash", "gh pr merge 3 --squash", ASK),
        (True, "Bash", "gh pr close 3", ASK),
        (True, "Bash", "gh pr review 3 --approve", ASK),
        (True, "Bash", "gh pr review 3 -a", ASK),
        (True, "Bash", "gh pr review 3 --comment -b x", ASK),
        (True, "Bash", "gh pr review 3 -r -b x", ASK),
        (True, "Bash", "gh pr comment 3 -b x", ASK),
        (False, "Bash", "gh pr comment 3 -b x", ASK),
        (True, "Bash", "glab mr update 3 --description-file d.md", None),
        (True, "Bash", "glab mr note 3 -m x", ASK),
        (False, "Bash", "glab mr note 3 -m x", ASK),
        (True, "Bash", "glab mr note 3 --resolve abc", ASK),
        (True, "Bash", "glab mr note create 3 -m x", ASK),
        (True, "Bash", "glab mr note resolve abc 3", ASK),
        (True, "Bash", "glab mr note reopen abc 3", ASK),
        (True, "Bash", "glab -R g/p mr note update 9 3 -m x", ASK),
        (True, "Bash", "glab mr note delete 9 3", ASK),
        (True, "Bash", "glab mr note draft publish 3", ASK),
        (True, "Bash", "glab mr note draft create 3 -m x", None),
        (False, "Bash", "glab mr note list 3", None),
        (False, "Bash", "glab mr note draft list 3", None),
        (True, "Bash", "glab mr view 3", None),
        (True, "Bash", "glab mr checkout 3", None),
        (True, "Bash", "glab api -X POST projects/p/merge_requests -f source_branch=b", ASK),
        (True, "Bash", "glab api -X PUT projects/p/merge_requests/3/merge", ASK),
        (True, "Bash", "glab api -X POST projects/p/merge_requests/3/approve", ASK),
        (True, "Bash", "glab api -X PUT projects/p/merge_requests/3 -f state_event=close", ASK),
        (True, "Bash", "glab api -X PUT projects/p/merge_requests/3 -f title=x", None),
        (True, "Bash", "glab api projects/p/merge_requests/3/notes -f body=x", ASK),
        (True, "Bash", "glab api projects/p/merge_requests/3/discussions/abc/notes -f body=x", ASK),
        (True, "Bash", "glab api -X PUT projects/p/merge_requests/3/discussions/abc -f resolved=true", ASK),
        (True, "Bash", "glab api -X POST projects/p/merge_requests/3/draft_notes/bulk_publish", ASK),
        (True, "Bash", "glab api projects/p/merge_requests/3/draft_notes -f note=x", None),
        (False, "Bash", "glab api 'projects/p/merge_requests/3/discussions?per_page=100'", None),
        (True, "Bash", "gh api repos/o/r/pulls/1/comments/5/replies -f body=x", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/comments/5 -f body=x", ASK),
        (True, "Bash", "gh api repos/o/r/issues/1/comments -f body=x", ASK),
        (False, "Bash", "gh api repos/o/r/pulls/1/comments", None),
        (True, "Bash", "gh api graphql -f query='mutation{resolveReviewThread(input:{}){x}}'", ASK),
        (True, "Bash", "glab api graphql -f query='mutation{discussionToggleResolve(input:{}){x}}'", ASK),
        (True, "Bash", "glab api graphql -f query='mutation{createNote(input:{}){x}}'", ASK),
        (True, "Bash", "glab api -X POST projects/p/repository/commits --input c.json", ASK),
        (True, "Bash", "glab api -X DELETE projects/p/repository/branches/b", ASK),
        (True, "Bash", "glab api projects/p/merge_requests/3", None),
        (True, "Bash", "glab api projects/p/repository/branches", None),
        (True, "Bash", "glab api graphql -f query='mutation{mergeRequestAccept(input:{}){x}}'", ASK),
        (True, "Bash", "glab api graphql -f query='{project(fullPath:\"g/p\"){mergeRequests{x}}}'", None),
        (True, "Bash", "glab api --method POST projects/p/uploads --form file=@f.png", ASK),
        (False, "Bash", "glab api --method POST projects/p/uploads --form file=@f.png", ASK),
        (True, "Bash", "glab api projects/p/uploads --form file=@f.png", ASK),
        (True, "Bash", "gh api repos/o/r/labels -f name=x", ASK),
        (False, "Bash", "gh api repos/o/r/labels -f name=x", ASK),
        (False, "Bash", "glab mr update 3 --description-file d.md", None),
        (False, "Bash", "glab -R g/p mr update 3 -d x", None),
        (False, "Bash", "glab api -X PUT projects/p/merge_requests/3 -f title=x", None),
        (False, "Bash", "glab api projects/p/merge_requests/3/draft_notes -f note=x", None),
        (False, "Bash", "glab issue create -t x", None),
        (False, "Bash", "glab ci retry 5", None),
        (False, "Bash", "gh pr edit 3 --body-file d.md", None),
        (False, "Bash", "glab mr update 3 -d x > d.md", DENY),
        (False, "Bash", "glab mr checkout 3", DENY),
        (False, "Bash", "gh pr checkout 3", DENY),
        (False, "Bash", "gh run download 5", DENY),
        (False, "Bash", "glab ci artifact main build", DENY),
        (False, "Bash", "gh issue develop 3 --checkout", DENY),
        (False, "Bash", "gh repo clone o/r", DENY),
        (True, "Bash", "glab api -X DELETE projects/p/labels/x", ASK),
        (True, "Bash", "glab api -X DELETE projects/p/merge_requests/3", ASK),
        (True, "Bash", "glab api graphql -f query='mutation{labelCreate(input:{}){x}}'", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/3 -f title=x", None),
        (True, "Bash", "glab api -X PUT projects/p/merge_requests/3/draft_notes/9 -f note=x", None),
        (True, "Bash", "glab api -X GET projects/p/labels -f search=x", None),
        (True, "Bash", "gh api -X PUT repos/o/r/pulls/1/merge", ASK),
        (True, "Bash", "gh api repos/o/r/pulls -f title=x -f head=b -f base=main", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/1 -f state=closed", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/1 -f body=x", None),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/1 --field=state=closed", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/pulls/1 --input b.json", ASK),
        (True, "Bash", "gh api repos/o/r/pulls/1/reviews --input r.json", ASK),
        (True, "Bash", "gh api repos/o/r/pulls/1/reviews -f event=APPROVE", ASK),
        (True, "Bash", "gh api repos/o/r/pulls/1/reviews -f event=COMMENT -f body=x", ASK),
        (True, "Bash", "gh api -X PATCH repos/o/r/git/refs/heads/b -f sha=abc", ASK),
        (True, "Bash", "gh api repos/o/r/pulls?state=open", None),
        (True, "Bash", "git tag v1.2.3", None),
        (True, "Bash", "glab release create v1.2.3", ASK),
        (True, "Bash", "glab -R g/p release create dev-x", ASK),
        (False, "Bash", "glab release create v1.2.3", ASK),
        (True, "Bash", "glab api -X POST projects/1/repository/tags -f tag_name=v1 -f ref=main", ASK),
        (True, "Bash", "glab api projects/1/releases -f tag_name=v1", ASK),
        (True, "Bash", "glab api projects/1/repository/tags", None),
        (True, "Bash", "glab release list", None),
        (True, "Bash", "docker push registry.example/x:t", ASK),
        (True, "Bash", "docker image push registry.example/x:t", ASK),
        (True, "Bash", "docker buildx build --push -t registry.example/x:t .", ASK),
        (True, "Bash", "docker buildx build --output type=registry -t registry.example/x:t .", ASK),
        (True, "Bash", "docker build -t registry.example/x:t --push .", ASK),
        (True, "Bash", "podman push registry.example/x:t", ASK),
        (True, "Bash", "buildah push registry.example/x:t", ASK),
        (False, "Bash", "docker push registry.example/x:t", ASK),
        (True, "Bash", "docker compose push", ASK),
        (True, "Bash", "docker buildx imagetools create -t registry.example/x:t registry.example/x:a", ASK),
        (True, "Bash", "docker buildx imagetools create --dry-run -t registry.example/x:t registry.example/x:a", None),
        (True, "Bash", "docker buildx imagetools inspect registry.example/x:t", None),
        (True, "Bash", "skopeo copy --dest-creds u:p docker://a/x:t docker://b/x:t", ASK),
        (True, "Bash", "skopeo sync --src docker --dest docker a/x b", ASK),
        (True, "Bash", "skopeo sync --src docker --dest=dir a/x /x/out", None),
        (True, "Bash", "skopeo copy docker://a/x:t dir:/x/out", None),
        (True, "Bash", "skopeo inspect docker://a/x:t", None),
        (True, "Bash", "docker build -t x .", None),
        (True, "Bash", "docker buildx build -t x --load .", None),
        (True, "Bash", "python3 /x/scripts/build_vllm_overlay.py --branch b --context c --namespace n", ASK),
        (True, "Bash", "uv run /x/scripts/build_vllm_overlay.py --branch b", ASK),
        (True, "Bash", "uv run python3 /x/scripts/build_vllm_overlay.py --branch b", ASK),
        (True, "Bash", "/x/scripts/build_vllm_overlay.py --branch b --context c --namespace n", ASK),
        (False, "Bash", "kubectl exec p -- sh -c 'rm -rf /data' --help", ASK),
        (False, "Bash", "python3 /x/deploy.py --help", None),
        (False, "Bash", "python3 /x/board.py fetch garbled-output --org 2", None),
        (False, "Bash", f"python3 /x/board.py fetch g --org 2 --out {scratch}g.json", None),
        (False, "Bash", "python3 /x/board.py fetch g --org 2 --out /x/g.json", DENY),
        (False, "Bash",
         f"python3 /x/board.py fetch g --org 2 --out {home}/.cache/claude-handoff/d/g.json", None),
        (False, "Bash", f"cd {scratch}d && python3 /x/board.py fetch g --org 2 --out g.json", None),
        # go module and build commands write the module files and the binary where they run.
        (False, "Bash", f"cd {scratch}d && go mod tidy", None),
        (False, "Bash", f"cd {scratch}d && export GOFLAGS=-mod=mod && go mod download", None),
        (False, "Bash", f"cd {scratch}d; go get example.com/m@v1.0.0", None),
        (False, "Bash", f"cd {scratch}d && go build -o out .", None),
        (False, "Bash", f"cd {scratch}d && go build -o={scratch}d/bin/out .", None),
        (False, "Bash", f"cd {scratch}d && go mod edit -require=example.com/m@v1.0.0", None),
        (False, "Bash", f"cd {scratch}d && go build -o /x/out .", DENY),
        (False, "Bash", f"cd {scratch}d && go build -o", DENY),
        (False, "Bash", f"cd {scratch}d && go get C o", None),
        (False, "Bash", f"cd {scratch}d && go mod tidy -modfile=/x/go.mod", DENY),
        (False, "Bash", f"cd {scratch}d && go mod edit -require=example.com/m@v1.0.0 /x/go.mod",
         DENY),
        (False, "Bash", f"cd {scratch}d && go -C /x mod tidy", DENY),
        (False, "Bash", f"cd {scratch}d && go mod tidy -C=/x", DENY),
        (False, "Bash", f"cd {scratch}d && go generate ./...", DENY),
        (False, "Bash", f"cd {scratch}d && go work sync", DENY),
        (False, "Bash", f"cd {scratch}d && go install example.com/m@v1.0.0", DENY),
        (False, "Bash", f"cd $(echo {scratch}d) && go mod tidy", DENY),
        (False, "Bash", "cd /x && go mod tidy", DENY),
        # helm dependency build and update write only under the chart and helm's caches.
        (False, "Bash", f"helm dependency build {scratch}c/model/pd-model", None),
        (False, "Bash", f"helm dependency update --skip-refresh {scratch}c/chart", None),
        (False, "Bash", f"cd {scratch}c && helm dependency build model/pd-model", None),
        (False, "Bash", f"cd {scratch}c && helm dependency up --keyring=/x/k", None),
        (False, "Bash", f"helm dependency build {rx}/chart", DENY),
        (False, "Bash", "helm dependency build", DENY),
        (False, "Bash", "helm dependency build ./chart", DENY),
        (False, "Bash", "helm dependency build $D/chart", DENY),
        (False, "Bash", f"helm dependency build --keyring {scratch}k", DENY),
        (False, "Bash", f"helm dependency build {scratch}c {rx}/chart", DENY),
        (False, "Bash", f"helm dependency build --repository-cache {rx}/c {scratch}c", DENY),
        (False, "Bash", f"helm dependency build --content-cache={rx}/c {scratch}c", DENY),
        (False, "Bash", f"helm dependency build --repository-cache={scratch}r {scratch}c", None),
        (False, "Bash", f"HELM_REPOSITORY_CACHE={rx}/c helm dependency build {scratch}c", DENY),
        (False, "Bash", f"export HELM_CONTENT_CACHE={rx}/c && helm dependency build {scratch}c",
         DENY),
        # go mod download adds the go.sum entries it verifies, read-only flags or not.
        (False, "Bash", "go mod download", DENY),
        (False, "Bash", "GOFLAGS=-mod=readonly go mod download example.com/m", DENY),
        # go env -w writes Go's user config file, outside every repo.
        (False, "Bash", "go env -w GOFLAGS=-mod=mod", None),
        # A defaults write to a named domain lands in the user's Library; a domain given as
        # a plist path may land in a repo.
        (False, "Bash", "defaults write com.googlecode.iterm2 K -float 4102444800", None),
        (False, "Bash", "defaults -currentHost delete com.apple.dock K", None),
        (False, "Bash", "defaults -host h write com.apple.dock K -bool true", None),
        (False, "Bash", "defaults write -g K -bool false", None),
        (False, "Bash", f"defaults write {rx}/a.plist K -bool true", DENY),
        (False, "Bash", "defaults write a.plist K -bool true", DENY),
        (False, "Bash", "defaults write ~/x K -bool true", DENY),
        (False, "Bash", "defaults write $D K -bool true", DENY),
        (False, "Bash", "defaults write", DENY),
        # defaults export writes the plist file it names.
        (False, "Bash", f"defaults export com.apple.dock {rx}/a.plist", DENY),
        (False, "Bash", "defaults export com.apple.dock -", None),
        # A build of several packages discards its output, so it changes no repo.
        (False, "Bash", "go build ./...", None),
        (False, "Bash", "go build ./cmd/a", DENY),
        (False, "Bash", "go build -o /dev/null ./cmd/a", None),
        # A signal reaches a process, never a file.
        (False, "Bash", "kill 12345", None),
        (False, "Bash", "kill 12345 && echo x > /x/f", DENY),
        (False, "Bash", "ssh-add -l", None),
        (False, "Bash", "ssh-add -L", None),
        (False, "Bash", "ssh-add ~/.ssh/id_ed25519", None),
        (False, "Bash", "ssh-add -D && echo x > /x/f", DENY),
        # A kill by name hides its targets, so it needs the user's words in every state.
        (True, "Write", {"file_path": "/x/.env.local"}, ASK),
        (False, "Edit", {"file_path": "/x/.env"}, ASK),
        (True, "Edit", {"file_path": "/x/env.py"}, None),
        (True, "Edit", {"file_path": "/x/.envrc"}, None),
        (True, "Bash", "echo X=1 > /x/.env.local", ASK),
        (True, "Bash", "echo X=1 >> /x/.env", ASK),
        (True, "Bash", "printf x | tee -a /x/.env.dev", ASK),
        (True, "Bash", "cp /y/a /x/.env", ASK),
        (True, "Bash", "cp /x/.env.local /y/backup", None),
        (True, "Bash", "mv /x/.env.local /y/b", ASK),
        (True, "Bash", "mv /y/b /x/.env.local", ASK),
        (True, "Bash", "sed -i '' s/a/b/ /x/.env.local", ASK),
        (True, "Bash", "perl -pi -e s/a/b/ /x/.env", ASK),
        (True, "Bash", "ruby -pi -e 'x' /x/.env", ASK),
        (True, "Bash", "sed -n 1p /x/.env.local", None),
        (True, "Bash", "cat /x/.env.local", None),
        (True, "Bash", "rm -f /x/.env.local", ASK),
        (True, "Bash", "truncate -s 0 /x/.env", ASK),
        (True, "Bash", "ln -s /x/e .env", ASK),
        (True, "Bash", "install -m 600 /x/e /x/app/.env", ASK),
        (True, "Bash", "dd if=/x/e of=/x/app/.env", ASK),
        (True, "Bash", "rsync /x/e /x/app/.env.local", ASK),
        (True, "Bash", "cp /x/.env ./", ASK),
        # A relative folder counts from where the writer runs, which follows every cd the
        # line's own shell runs, never one a child wrapper runs, is unknown after one that
        # may not stick, and moves with an env -C.
        (True, "Bash", "cd /x/app && cp /x/.env .", ASK),
        (True, "Bash", "cd / && cp /x/.env usr", ASK),
        (True, "Bash", "cd /x/app && ln -s /x/shared/.env", ASK),
        (True, "Bash", "(cd /x) && cp /x/.env usr", ASK),
        (True, "Bash", "env -C / cp /x/.env usr", ASK),
        (True, "Bash", "cd / && nohup cd /x; cp /x/.env usr", ASK),
        (True, "Bash", "cp /x/.env.local backup", None),
        # An option's value is no source.
        (True, "Bash", "rsync -a --exclude .env /x/src/ /x/dst/", None),
        (True, "Bash", "install -m 644 /x/.env.example /x/app/settings", None),
        (True, "Bash", "install -Dm 644 /x/.env.example /x/app/settings", None),
        (True, "Bash", "rsync -a -e ssh /x/.env /x/dst/", ASK),
        (False, "Bash", "pkill -f temporal", ASK),
        (True, "Bash", "pkill -f temporal", ASK),
        (True, "Bash", "killall temporal", ASK),
        (True, "Bash", "sleep 1 && pkill temporal", ASK),
        (False, "Bash", "fuser -k 8080/tcp", ASK),
        (True, "Bash", "fuser -km /mnt/x", ASK),
        (False, "Bash", "fuser -v 8080/tcp", None),
        (True, "Bash", "pgrep -fl temporal", None),
        (False, "Bash", f"cd {rx} && python3 /x/board.py fetch g --org 2 --out g.json", DENY),
        (False, "Bash", f"cd {scratch}d && python3 /x/board.py fetch g --org 2 --out $u.json",
         DENY),
        (False, "Bash", "python3 /x/board.py diff g /x/g.json --org 2", None),
        (False, "Bash", "python3 /x/board.py login", None),
        (False, "Bash", "python3 /x/board.py publish g /x/g.json --org 2 --message m", None),
        (False, "Bash", f"python3 /x/board.py shot g --org 2 --out {scratch}g.png", None),
        (False, "Bash", "python3 /x/board.py shot g --org 2 --out /x/g.png", DENY),
        (False, "Bash", f"cd {rx} && python3 /x/board.py shot g --org 2 --out g.png", DENY),
        (False, "Bash", "bash -c 'rm -rf /x' --help", DENY),
        (False, "Bash", "kubectl get pods --help", None),
        (False, "Bash", "helm upgrade --help", None),
        (False, "Bash", "python3 --help", None),
        # A logical line runs on through a quoted or an escaped newline.
        (False, "Bash", 'python3 -c "\nimport json\nprint(1)\n"', None),
        # perl and ruby code runs as python's does; only an in-place edit names its target.
        (False, "Bash", f"cd {rx} && perl -e 'print 1'", None),
        (False, "Bash", f"cd {rx} && ruby -e 'puts 1'", None),
        (False, "Bash", f"cd {rx} && perl -e 'alarm 12; exec @ARGV' pomerium-cli version", None),
        (False, "Bash", f"cd {rx} && perl -pi -e s/a/b/ f", DENY),
        (False, "Bash", f"cd {rx} && perl -i.bak -pe s/a/b/ f", DENY),
        (False, "Bash", f"cd {rx} && ruby -pi -e 'x' f", DENY),
        (False, "Bash", "kubectl get pods \\\n  --context X -n Y", None),
        (False, "Bash", f'echo "a\nb"\ngit -C {rx} add f', DENY),
        (False, "Bash", f"git -C {rx} \\\n  stash", DENY),
        (False, "Bash", "( cd /x\n  git stash )", DENY),
        (False, "Bash", f"echo a # don't\ngit -C {rx} stash", DENY),
        (False, "Bash", "git -c core.fsmonitor=/x.sh status", DENY),
        (False, "Bash", f"git -C {rx} -c diff.external=/x.sh diff", DENY),
        (False, "Bash", "git --config-env=core.pager=X log", DENY),
        (False, "Bash", "git grep -c foo", None),
        (False, "Bash", "git log -c -1", None),
        (False, "Bash", "sed -n 'w /x/out' f", DENY),
        (False, "Bash", "sed 's/a/b/w /x/out' f", DENY),
        (False, "Bash", "sed -n '1,5p' f", None),
        (False, "Bash", "sed 's/new world/x/' f", None),
        (False, "Bash", "git branch -a --contains abc", None),
        (False, "Bash", "git branch --list 'x/*'", None),
        (False, "Bash", "git branch new-branch", DENY),
        (False, "Bash", "git reflog -n 40 --date=iso", None),
        (False, "Bash", "git -C /x reflog -n 60 HEAD", None),
        (False, "Bash", "git reflog show main", None),
        (False, "Bash", "git reflog exists main", None),
        (False, "Bash", "git reflog expire --all", DENY),
        (False, "Bash", "git reflog delete HEAD@{1}", DENY),
        (False, "Bash", "git reflog drop main", DENY),
        (False, "Bash", "git reflog write main abc def msg", DENY),
        (False, "Bash", "git config user.email", None),
        (False, "Bash", "git config --global user.email", None),
        (False, "Bash", "git config user.email x", DENY),
        (False, "Bash", "git config --unset user.email", DENY),
        (False, "Bash", "git config get user.email", None),
        (False, "Bash", "git config list", None),
        (False, "Bash", "git config set user.email x", DENY),
        (False, "Bash", "git config edit", DENY),
        (False, "Bash", "git config -f .gitconfig user.email", None),
        (False, "Bash", "git config --file .gitconfig user.email x", DENY),
        (False, "Bash", "kubectl get crd --context X", None),
        (False, "Bash", "kubectl get namespaces --context X", None),
        (False, "Bash", "kubectl get clusterpolicies --context X", None),
        (False, "Bash", "kubectl get clusterpolicy cell-pin --context X -o yaml", None),
        (False, "Bash", "kubectl describe cpol cell-pin --context X", None),
        (False, "Bash", "python3 -m json.tool", None),
        (False, "Bash", "python3 -m unittest", None),
        (False, "Bash", "gh api graphql -f query='{viewer{login}}'", None),
        (False, "Bash", "gh api graphql -f query='mutation{x}'", ASK),
        (True, "Bash", "kubectl config use-context x", ASK),
        (False, "Bash", "kubectl config use-context x", ASK),
        (True, "Bash", "kubectx x", ASK),
        (False, "Bash", "kubectx x", ASK),
        (True, "Bash", "kubens x", ASK),
        (True, "Bash", "kubectl label node n atero/user=x --context X", ASK),
        (True, "Bash", "kubectl taint nodes n k=v:NoSchedule --context X", ASK),
        (True, "Bash", "kubectl cordon n --context X", ASK),
        (False, "Bash", "kubectl rollout status deploy/x --context X -n Y", None),
        (True, "Bash", "kubectl rollout restart deploy/x --context X -n Y", ASK),
        (True, "Bash", "kubectl apply -f x.yaml --context X -n Y", ASK),
        (False, "Bash", "kubectl apply -f x.yaml --context X -n Y", ASK),
        (False, "Bash", "kubectl apply -f x.yaml --dry-run=server --context X -n Y", None),
        (True, "Bash", "kubectl drain n --context X --ignore-daemonsets", ASK),
        (False, "Bash", "kubectl drain n --context X --ignore-daemonsets", ASK),
        (False, "Bash", "frobnicate --flag", ASK),
        (False, "Bash", "frobnicate | grep x", ASK),
        (False, "Bash", "frobnicate && touch /etc/x", DENY),
        # Deny or ask is judged on what the gate holds: a known write it lets through, such as
        # brew, leaves an unknown program beside it an ask.
        (False, "Bash", "brew upgrade x; frobnicate", ASK),
        (False, "Bash", "HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade -y x 2>&1 >/dev/null\n"
                        "bash -c 'gvm use go0.0.0' 2>&1", ASK),
        # Sourcing a script runs its text in the shell, a known write wherever it sits.
        (False, "Bash", "brew upgrade x; bash -c '. \"$HOME/.gvm/scripts/gvm\" && gvm use g'",
         DENY),
        (False, "Bash", "frobnicate > out.txt", DENY),
        (False, "Bash", "frobnicate; git stash", DENY),
        (False, "Bash", "stern x --context X -n Y", None),
        (False, "Bash", "kubectl --help", None),
        (False, "Bash", "python3 -m pytest tests/", None),
        (False, "Bash", "zsh -ic 'echo $HISTFILE; setopt | grep -i hist'", None),
        (False, "Bash", 'which claude; stat -f "%Sm %N" "$(readlink -f "$(which claude)")" 2>&1', None),
        (False, "Bash", "claude auth status", None),
        (False, "Bash", "claude -p auth status", DENY),
        (False, "Bash", "claude plugin list --json --available", None),
        (False, "Bash", "claude plugin marketplace list", None),
        (False, "Bash", "claude -p plugin list", DENY),
        # claude plugin writes only ~/.claude/plugins, unless scoped to the working directory.
        (False, "Bash", "claude plugin install foo", None),
        (False, "Bash", "claude plugin marketplace update", None),
        (False, "Bash", "claude plugin install foo --scope project", DENY),
        (False, "Bash", "claude plugin install foo -s local", DENY),
        (False, "Bash", '"$HOME/.local/bin/claude" plugin update a@b 2>/dev/null', None),
        # brew writes only its own prefix, except bundle, which writes a Brewfile here.
        (False, "Bash", "HOMEBREW_NO_AUTO_UPDATE=1 /opt/homebrew/bin/brew upgrade -y x 2>&1 "
                        ">/dev/null", None),
        (False, "Bash", "brew bundle dump", DENY),
        # Only repos under the roots are the gate's: a write elsewhere passes, unless it
        # names a path into a root or runs an inline script.
        (False, "Bash", "cd /opt/x && make install", None),
        (False, "Bash", f"cd /opt/x && make install PREFIX={rx}", DENY),
        (False, "Bash", "cd /opt/x && bash -lc 'touch /etc/y'", DENY),
        (False, "Bash", "cd /opt/x && git stash", None),
        (False, "Bash", "cd /opt/x && go generate ./...", DENY),
        (False, "Bash", f"cd {home} && pip install x", None),
        (False, "Edit", {"file_path": f"{home}/.oh-my-zsh/custom/x.zsh"}, None),
        # A clone outside the roots asks in every gate state; inside one it is the gate's.
        (False, "Bash", "git clone https://example.com/r.git /opt/r", ASK),
        (True, "Bash", "git clone https://example.com/r.git /opt/r", ASK),
        (True, "Bash", "cd /opt && gh repo clone o/r", ASK),
        (True, "Bash", "cd /opt && glab repo clone -g grp", ASK),
        (True, "Bash", "git clone https://example.com/r.git $D", ASK),
        (False, "Bash", f"git clone https://example.com/r.git {rx}", DENY),
        (True, "Bash", f"git clone https://example.com/r.git {rx}", None),
        (True, "Bash", f"cd {rx} && gh repo clone o/r -- --depth 1", None),
        (True, "Bash", f"git clone https://example.com/r.git {scratch}r", None),
        (False, "Bash", "claude -p 'Review' --tools \"\" --disallowedTools 'mcp__*'", None),
        (False, "Bash", "claude -p 'Review' --tools \"\"", DENY),
        (False, "Bash", "claude -p 'Review'", DENY),
        (False, "Bash", "claude", DENY),
        (False, "Bash", "xh :8081/api/clusters", None),
        (False, "Bash", "xh GET localhost:8081/api/clusters Authorization:x | jq .", None),
        (False, "Bash", "xh POST localhost:8081/api/clusters name=x", DENY),
        (False, "Bash", "xh localhost:8081/api/clusters name=x", DENY),
        (False, "Bash", "xh localhost:8081/api/clusters q==x", None),
        (False, "Bash", "xh -d localhost:8081/file", DENY),
        (True, "Bash", "xh DELETE localhost:8081/api/clusters/1", None),
        (False, "Bash", "xh post localhost:8081/api/clusters", DENY),
        (False, "Bash", "xh put localhost:8081/api/clusters/1 --raw '{}'", DENY),
        (False, "Bash", "xh --form localhost:8081/upload f@/etc/hosts", DENY),
        (False, "Bash", "xh 'localhost:8081/api/clusters?name=x'", None),
        (False, "Bash", "xh -a u:p http://user@host/x", None),
        (False, "Bash", "xh -a u:p http://host/x k=v", ASK),
        (False, "Bash", "xh --verify no 'host/x?y=1'", None),
        (False, "Bash", "kubectl get pods --context X -n 123 > /private/tmp/claude/p", DENY),
        (False, "Bash", "bash -lc 'touch /etc/x'", DENY),
        (False, "Bash", f"bash {scratch}check.sh", None),
        (False, "Bash", f"python3 {scratch}check.py", None),
        (True, "Bash", f"python3 {scratch}check.py", None),
        (False, "Bash", f"python3 {os.path.realpath(__file__)} --selftest", None),
        (False, "Write", {"file_path": f"{scratch}a.md"}, DENY),
        (True, "Write", {"file_path": f"{scratch}a.md"}, DENY),
        (True, "Edit", {"file_path": "/tmp/claude/a.md"}, DENY),
        (True, "Write", {"file_path": f"{home}/.cache/claude-handoff/d/a.md"}, None),
        (False, "Write", {"file_path": "/tmp/a.md"}, DENY),
        (True, "Write", {"file_path": "/private/tmp/a.md"}, DENY),
        (True, "Bash", "echo x > /tmp/a.diff", DENY),
        (True, "Bash", "rm -f /tmp/a.diff", None),
        (False, "Write", {"file_path": f"{home}/.claude/lfg-state/x"}, DENY),
        (False, "Write", {"file_path": f"{home}/.claude/scratch-paths/x"}, DENY),
        (False, "Write", {"file_path": f"{home}/.claude/plugins/installed_plugins.json"}, DENY),
        (False, "Edit", {"file_path": f"{home}/repos/x.py"}, None),
        (True, "Edit", {"file_path": f"{home}/repos/x.py"}, None),
        (False, "NotebookEdit", {"notebook_path": f"{scratch}n.ipynb"}, DENY),
        (False, "NotebookEdit", {"notebook_path": f"{home}/repos/n.ipynb"}, None),
        (False, "Write", {}, None),
        (False, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": alert, "thread_ts": "1.2", "message": "tl;dr"}, None),
        (False, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": "C0OTHER", "thread_ts": "1.2", "message": "x"}, ASK),
        (True, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": alert, "message": "no thread"}, ASK),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": alert, "message_ts": "1.2", "emoji": "claude"}, None),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": alert, "message_ts": "1.2", "emoji": "eyes"}, None),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": "C0OTHER", "message_ts": "1.2", "emoji": "claude"}, None),
        (True, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": "C0OTHER", "message_ts": "1.2", "emoji": "eyes"}, None),
        (False, "mcp__claude_ai_Slack__slack_read_thread", {"channel_id": alert}, None),
        (False, "mcp__Slack__slack_read_thread", {"channel_id": alert}, None),
        (False, "mcp__claude_ai_Atlassian_Rovo__getConfluencePage", {"pageId": "1"}, None),
        (False, "mcp__data-mcp__live_promql_query", {"query": "up"}, None),
        (False, "mcp__claude_ai_Atlassian_Rovo__createJiraIssue", {}, None),
        (True, "mcp__claude_ai_Atlassian_Rovo__createJiraIssue", {}, None),
        (False, "mcp__plugin_plumber-claude_plumber__plumber_dispatch", {}, None),
        (False, "mcp__x__frob", {}, None),
        (True, "mcp__x__frob", {}, None),
        (True, "mcp__claude_ai_gitlab__merge_merge_request", {}, ASK),
        (False, "mcp__claude_ai_gitlab__merge_merge_request", {}, ASK),
        (True, "mcp__claude_ai_gitlab__create_merge_request", {}, ASK),
        (True, "mcp__github__create_pull_request_review", {}, ASK),
        (True, "mcp__github__push_files", {}, ASK),
        (True, "mcp__claude_ai_gitlab__get_merge_request", {}, None),
        (True, "mcp__claude_ai_gitlab__create_note", {}, ASK),
        (True, "mcp__github__add_comment_to_pending_review", {}, ASK),
        (True, "mcp__github__resolve_review_thread", {}, ASK),
        (False, "mcp__github__resolve_review_thread", {}, ASK),
        (True, "mcp__backoffice-prod__api_call", {"method": "PUT"}, ASK),
        (False, "mcp__backoffice-prod__api_call", {"method": "PUT"}, ASK),
        (True, "mcp__claude_ai_backoffice_prod__api_call", {}, ASK),
        (True, "mcp__backoffice-dev__api_call", {"method": "PUT"}, None),
        (False, "mcp__backoffice-dev__api_call", {"method": "PUT"}, None),
        (False, "mcp__backoffice-prod__scaling_get", {}, None),
        (True, "mcp__github__unresolve_review_thread", {}, ASK),
        (False, "mcp__github__get_review_comments", {}, None),
        (True, "mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue", {}, None),
        (False, "mcp__github__list_pull_requests", {}, None),
        # The rating hook's config names code that hook runs, so every change to it asks.
        (False, "Write", {"file_path": f"{home}/.config/tkay-tools.json"}, ASK),
        (True, "Edit", {"file_path": f"{home}/.config/tkay-tools.json"}, ASK),
        (True, "Bash", f"printf '{{}}' > {home}/.config/tkay-tools.json", ASK),
        (True, "Bash", "cp /x/c.json ~/.config/tkay-tools.json", ASK),
        (True, "Bash", "mv ~/.config/tkay-tools.json /x/old.json", ASK),
        (True, "Bash", "sed -i '' s/a/b/ ~/.config/tkay-tools.json", ASK),
        (False, "Bash", "cat ~/.config/tkay-tools.json", None),
        (True, "Bash", "cp ~/.config/tkay-tools.json /x/c.json", None),
        (True, "Bash", "ln -sf /x/c.json ~/.config/tkay-tools.json", ASK),
        (True, "Bash", "install -m 600 /x/c.json ~/.config/tkay-tools.json", ASK),
        (True, "Bash", f"dd if=/x/c.json of={home}/.config/tkay-tools.json", ASK),
        (True, "Bash", "rsync -a /x/c.json ~/.config/tkay-tools.json", ASK),
        (True, "Bash", "cp /x/tkay-tools.json ~/.config/", ASK),
        (True, "Bash", "mv /x/tkay-tools.json ~/.config/", ASK),
        (True, "Bash", "cd ~/.config && cp /x/c.json tkay-tools.json", ASK),
        (True, "Bash", "cd ~/.config && ln -s /x/tkay-tools.json", ASK),
        (True, "Bash", "env -C ~ cp /x/tkay-tools.json .config", ASK),
        (True, "Bash", "cp /x/c.json /x/staged/tkay-tools.json", None),
        (True, "Write", {"file_path": "/x/staged/tkay-tools.json"}, None),
        (True, "Bash", "cp /x/a /x/b /x/dir", None),
    ]
    failures = 0
    for gate_open, tool_name, tool_input, expected in cases:
        if tool_name == "Bash":
            tool_input = {"command": tool_input}
        # A command with no directory of its own is judged against the working directory,
        # so the table is judged from one under a repo root that is neither a repo nor a
        # scratch root.
        got = decide(tool_name, tool_input, gate_open, os.path.join(REPO_ROOTS[0], "no-repo"))
        got_kind = got[0] if got else None
        ok = got_kind == expected
        failures += not ok
        shown = (tool_input["command"].replace("\n", "\\n") if tool_name == "Bash"
                 else f"{tool_name} {tool_input}")
        print(f"{'ok  ' if ok else 'FAIL'} [{'open' if gate_open else 'closed'}] "
              f"{shown} -> {got_kind}" + ("" if ok else f" (want {expected})"))
    reason_cases = [
        # (command, expected reason) with the gate closed
        # The path a first statement assigns is read in place of its variable, so the gate
        # judges the path - a repo path gets the refusal - and every other shape holds.
        (f"D={rx}; mkdir -p $D/old", BASH_REFUSAL),
        (f"D={rx}; cd $D && printf a > mod/go.mod", BASH_REFUSAL),
        (f'D="{home}/.cache/d"; mkdir -p $D', SHELL_PATH_REASON),
        (f"D={home}/.cache/d mkdir -p $D", SHELL_PATH_REASON),
        (f"D={home}/.cache/d | mkdir -p $D", SHELL_PATH_REASON),
        (f"D={home}/.cache/d; D={rx}; mkdir -p $D", SHELL_PATH_REASON),
        (f"D={home}/.cache/d; read D; mkdir -p $D", SHELL_PATH_REASON),
        (f"D={home}/.cache/d; mkdir -p $D '$D'", SHELL_PATH_REASON),
        (f"D={home}/.cache/d; mkdir -p $DIR", SHELL_PATH_REASON),
        (f"D={home}/.cache/d; mkdir -p $D$(echo /x)", SHELL_PATH_REASON),
        (f"cd {rx} && git archive HEAD | tar -x -C $D/old", SHELL_PATH_REASON),
        (f"cp $SRC {rx}/f", BASH_REFUSAL),
        ('git commit -m "$MSG"', BASH_REFUSAL),
        (f"git -C $D commit -m m && touch {rx}/f", BASH_REFUSAL),
        ("echo hi > $TMPDIR/x", SHELL_PATH_REASON),
        ("echo hi > out.txt", BASH_REFUSAL),
        (f"echo hi > $D/x; echo hi > {rx}/f", BASH_REFUSAL),
        (f"go test ./x; rm {rx}/zz_test.go; git status --short", RM_CHAINED_REASON),
        (f"rm {rx}/a && echo done", RM_CHAINED_REASON),
        (f"find {rx} -name '*.orig' -exec rm {{}} +", RM_CHAINED_REASON),
        ("mkdir -p $D/m && cd $D && printf a > m/f", SHELL_PATH_REASON),
        (f"cd $D && printf a > {rx}/f", BASH_REFUSAL),
        (f"cd {rx} || cd /x; printf a > f", BASH_REFUSAL),
        # A fetch into a ref of its own is told to read FETCH_HEAD; one that moves a branch
        # or a tag, or comes with another repo write, keeps the refusal.
        ("git fetch origin refs/merge-requests/1/head:refs/cr/mr-1", NAMED_REF_FETCH_REASON),
        ("git fetch origin main:main", BASH_REFUSAL),
        ("git fetch origin x:refs/tags/t", BASH_REFUSAL),
        ("git fetch origin x:refs/cr/a main:main", BASH_REFUSAL),
        (f"git fetch origin x:refs/cr/a && touch {rx}/f", BASH_REFUSAL),
    ]
    for command, expected in reason_cases:
        got = decide("Bash", {"command": command}, False, os.path.join(REPO_ROOTS[0], "no-repo"))
        ok = got == (DENY, expected)
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} reason {command} -> {got}"
              + ("" if ok else f" (want {expected})"))
    # In auto mode the rating hook leaves the call as written, so the gate's own ask names
    # the rating in its reason; outside auto mode the description carries it.
    for mode, opens_with_rating in (("auto", True), ("default", False)):
        result = hook_output({"tool_name": "Bash", "session_id": "s", "permission_mode": mode,
                              "tool_input": {"command": "helm uninstall r --kube-context X -n Y"}})
        reason = result["hookSpecificOutput"].get("permissionDecisionReason", "")
        ok = reason.startswith("🔴 DANGER · ") == opens_with_rating
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} ask reason in {mode} mode -> {reason[:40]!r}")
    payload_cases = [
        ({"tool_name": "Bash", "session_id": "s"}, DENY),
        ({"tool_name": "Write", "session_id": "s", "tool_input": None}, DENY),
        ({"tool_name": "Read", "session_id": "s", "tool_input": {"file_path": "/x"}}, None),
        # An rm of only harness scratch is denied, alone or chained, before the org's rm
        # prompt; the count cases below pin that one also naming another path is not.
        ({"tool_name": "Bash", "session_id": "s",
          "tool_input": {"command": "rm -rf /tmp/claude/build"}}, DENY),
        ({"tool_name": "Bash", "session_id": "s",
          "tool_input": {"command": "ls && rm -rf /private/tmp/claude/build"}}, DENY),
    ]
    for payload, expected in payload_cases:
        result = hook_output(payload)
        got = (result or {}).get("hookSpecificOutput", {}).get("permissionDecision")
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} payload {payload} -> {got}"
              + ("" if ok else f" (want {expected})"))
    s = SCRATCH_ROOTS[0]
    count_cases = [
        # (command, whether it holds an rm of only harness scratch, which is denied)
        (f"go list ./... > {s}deps.txt; grep x {s}deps.txt; rm -f {s}deps.txt", True),
        (f"rm -rf {s}build && make test", True),
        ("rm -rf /tmp/claude/build; make test", True),
        (f"make test && rm -rf {s}build 2>/dev/null", True),
        (f"a; rm -- {s}x {s}y; b", True),
        (f"rm -f {s}x", True),
        (f"a && rm {s}x || echo failed", True),
        (f"a | rm {s}x", True),
        (f"a; rm -rf {s}x\nb", True),
        (f"a; rm -rf {s}x 2>&1", True),
        (f"a; rm -rf {s}x # done", True),
        (f"a; rm -rf {s}x &", True),
        (f"(cd y && rm -rf {s}x)", True),
        (f"echo $(rm -rf {s}x)", True),
        (f'bash -c "make; rm -rf {s}x"', True),
        (f"cat <<EOF > {s}f\nhello\nEOF\nrm -rf {s}f", True),
        (f"rm -rf {s}a && rm -rf {s}b && make", True),
        (f"make \\\n  test; rm -rf {s}x", True),
        (f"sleep 1 &\nrm -rf {s}x", True),
        (f"if true; then\n  rm -rf {s}x\nfi", True),
        (f"for i in 1; do rm -rf {s}x; done", True),
        (f"rm -rf {s}x || true", True),
        (f"rm -rf {s}x 2>/dev/null || true", True),
        (f"{{ rm -rf {s}x; }}", True),
        (f"(rm -rf {s}x)", True),
        (f"rm -rf {s}x > /dev/null 2>&1", True),
        (f"time rm -rf {s}x", True),
        # Anything outside the scratch root, or a path only the shell resolves, is not
        # scratch cleanup.
        ("a; rm -f $TMPDIR/x", False),
        (f"a; rm -rf {s}x ~/repos", False),
        (f"a; rm -rf {s}../../etc", False),
        (f"a; rm -rf {s}{{x,../..}}", False),
        (f"a; rm -rf {s}x /tmp/y", False),
        ("a; rm -rf /", False),
        ("a; rmdir x", False),
        # Quoted text is someone's argument, not an rm.
        (f"python3 gate.py 'a; rm -rf {s}x'", False),
        (f"git commit -m 'drop; rm -rf {s}x'", False),
        (f"cat <<'EOF' > {s}f\nrm -rf {s}x\nEOF", False),
        (f"cat <<< 'rm -rf {s}x'", False),
        (f"cat <<EOF\nrm -rf {s}x", False),
    ]
    for command, expected in count_cases:
        got = bool(scratch_rm_count(command))
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} scratch rm {command!r} -> {got}"
              + ("" if ok else f" (want {expected})"))
    # Only the rating hook changes a call's input; the gate allows, asks or denies.
    for mode, command in (("default", "ls"), (None, "ls"), ("auto", "ls"),
                          ("auto", "kubectl delete pod x --context c -n n")):
        payload = {"tool_name": "Bash", "session_id": "s", "permission_mode": mode,
                   "tool_input": {"command": command, "description": "lists files"}}
        got = "updatedInput" in (hook_output(payload) or {}).get("hookSpecificOutput", {})
        failures += got
        print(f"{'FAIL' if got else 'ok  '} input unchanged {mode} {command!r}")
    # A commit on a repo's default branch is denied in every gate state; throwaway repos
    # stand in for the real ones, and one is exempted the way ~/.claude is.
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        def repo(name, branch, remote_head=True):
            path = os.path.join(root, name)
            for args in (["init", "-q", "-b", branch], ["-c", "user.email=t@t", "-c", "user.name=t",
                         "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "x"]):
                subprocess.run(["git", "-C", path, *args] if args[0] != "init"
                               else ["git", *args, path], check=True, capture_output=True)
            if remote_head:
                subprocess.run(["git", "-C", path, "update-ref", f"refs/remotes/origin/{branch}",
                                "HEAD"], check=True)
                subprocess.run(["git", "-C", path, "symbolic-ref", "refs/remotes/origin/HEAD",
                                f"refs/remotes/origin/{branch}"], check=True)
            return path

        on_main = repo("on-main", "main")
        with open(os.path.join(on_main, ".gitignore"), "w") as f:
            f.write("ignored/\n*.log\n.claude/settings.local.json\n")
        with open(os.path.join(on_main, "tracked.log"), "w") as f:
            f.write("x\n")
        subprocess.run(["git", "-C", on_main, "add", "-f", "tracked.log"], check=True)
        on_feature = repo("on-feature", "main")
        subprocess.run(["git", "-C", on_feature, "switch", "-q", "-c", "feat"], check=True)
        on_master = repo("on-master", "master", remote_head=False)
        exempt = repo("exempt", "main")
        not_repo = os.path.join(root, "plain")
        os.makedirs(not_repo)
        global DEFAULT_BRANCH_EXEMPT
        saved_exempt = DEFAULT_BRANCH_EXEMPT
        DEFAULT_BRANCH_EXEMPT = (os.path.realpath(exempt),)
        branch_cases = [
            # (cwd, command, expected decision with the gate open)
            (not_repo, f"git -C {on_main} commit -m x", DENY),
            (on_main, "git commit -m x", DENY),
            (not_repo, f"cd {on_main} && git add -A && git commit -m x", DENY),
            (not_repo, f"git -C {on_main} merge feat", DENY),
            (not_repo, f"git -C {on_master} commit -m x", DENY),
            (on_feature, "git commit -m x", None),
            (not_repo, f"git -C {on_main} switch -c feat2 && git -C {on_main} commit -m x", None),
            (not_repo, f"git -C {on_feature} switch main && git -C {on_feature} commit -m x", DENY),
            (not_repo, f"git -C {on_main} merge --abort", None),
            (not_repo, f"git -C {on_main} checkout README.md && git -C {on_main} commit -m x", DENY),
            (not_repo, f"git -C {on_feature} checkout main && git -C {on_feature} commit -m x", DENY),
            (not_repo, f"git -C {on_main} log --oneline", None),
            (not_repo, f"git -C {exempt} commit -m x", None),
            (not_repo, f"git -C $(echo {on_main}) commit -m x", ASK),
            (not_repo, f"cd $(echo {on_main}) && git commit -m x", ASK),
            (not_repo, f"cd $(echo x) && git -C {on_main} commit -m x", DENY),
            (on_main, f"(cd {on_feature}) && git commit -m x", ASK),
            (on_main, f"bash -c 'cd {on_feature}' && git commit -m x", ASK),
            (on_main, f"cd {on_feature} && git commit -m x", None),
            (on_feature, f"pushd {on_main} && git commit -m x", DENY),
            (on_main, f"pushd {on_feature} && popd && git commit -m x", ASK),
            (not_repo, f"git -C $(echo {on_main}) merge --abort", None),
            (not_repo, f"git -C $(echo {on_main}) status", None),
            (not_repo, "git commit -m x", None),
        ]
        try:
            for cwd, command, expected in branch_cases:
                got = decide("Bash", {"command": command}, True, cwd)
                got = got[0] if got else None
                ok = got == expected
                failures += not ok
                print(f"{'ok  ' if ok else 'FAIL'} branch {command!r} in {os.path.basename(cwd)} "
                      f"-> {got}" + ("" if ok else f" (want {expected})"))
        finally:
            DEFAULT_BRANCH_EXEMPT = saved_exempt
        # The gate holds repo changes only: the throwaway repos stand in for real ones, and
        # the scratch roots narrow to one directory so the repos sit outside them.
        saved_roots = (GATE_SCRATCH_ROOTS, TMP_ROOT, REPO_ROOTS, SCRATCH_ROOTS,
                       SCRATCH_PREFIXES)
        scratch_dir = os.path.join(root, "scratch")
        os.makedirs(scratch_dir)
        with open(os.path.join(scratch_dir, "p.diff"), "w") as f:
            f.write("--- f.md\n+++ f.md\n@@ -1 +1 @@\n-a\n+b\n")
        with open(os.path.join(scratch_dir, "multi.diff"), "w") as f:
            f.write("--- f.md\n+++ f.md\n@@ -1 +1 @@\n-a\n+b\n"
                    "--- README.md\n+++ README.md\n@@ -1 +1 @@\n-a\n+b\n")
        with open(os.path.join(scratch_dir, "mixed.diff"), "w") as f:
            f.write("--- f.md\n+++ f.md\n@@ -1 +1 @@\n-a\n+b\n*** README.md\n--- README.md\n"
                    "***************\n*** 1 ****\n! a\n--- 1 ----\n! b\n")
        with open(os.path.join(scratch_dir, "indent.diff"), "w") as f:
            f.write("--- f.md\n+++ f.md\n@@ -1 +1 @@\n-a\n+b\n"
                    " --- README.md\n +++ README.md\n @@ -1 +1 @@\n -a\n +b\n")
        GATE_SCRATCH_ROOTS = (os.path.realpath(scratch_dir) + "/",)
        REPO_ROOTS = (os.path.realpath(root) + "/",)
        TMP_ROOT = os.path.realpath(root) + "/harness/"
        SCRATCH_PREFIXES = SCRATCH_ROOTS = (TMP_ROOT + "claude/",)
        gate_cases = [
            # (tool, input, expected decision with the gate closed), run from on_main
            ("Bash", {"command": "python3 -c 'print(1)'"}, None),
            ("Bash", {"command": "uv run --with pyyaml python3 -c 'print(1)'"}, None),
            ("Bash", {"command": "docker run --rm img amtool template render"}, None),
            ("Bash", {"command": f"echo x > {scratch_dir}/out"}, None),
            ("Bash", {"command": f"echo x > {on_main}/out"}, DENY),
            ("Bash", {"command": f"sed -i '' s/a/b/ {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"sed -i '' 's/a b/c d/g' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' -e 's/a/b/' -e 's|c|d|g' {scratch_dir}/f.md"},
             None),
            ("Bash", {"command": f"cd {scratch_dir} && sed -i '' 's/a b/c/' f.md"}, None),
            ("Bash", {"command": f"sed -i.bak 's/a/b/' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -Ei '' 's/a+/b/' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' -e '3s/a/b/' -e '5,$s|c|d|g' {scratch_dir}/f.md"},
             None),
            ("Bash", {"command": f"sed -i '' 's#x#y#; s#a b#c d#g' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' 's/a/b/;' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' 's/a/b/; w {on_main}/out' {scratch_dir}/f.md"},
             DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/; s/c/d/w {on_main}/out' {scratch_dir}/f.md"},
             DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/; 3d' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' '62,151d' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' '$d' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' '62,151d' {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '/x/d' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '3dw {on_main}/out' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '3d; w {on_main}/out' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/; s/c/d/e' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/; s/c/d/' {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"ln -s ../../x/a.md {scratch_dir}/a.md"}, None),
            ("Bash", {"command": f"ln -sf {on_main}/README.md {scratch_dir}/r.md"}, None),
            ("Bash", {"command": f"ln -s {scratch_dir}/a.md {on_main}/a.md"}, DENY),
            ("Bash", {"command": f"ln -s {scratch_dir}/a.md"}, DENY),
            ("Bash", {"command": f"ln -s ../x/a.md ../x/b.md {scratch_dir}/d"}, None),
            ("Bash", {"command": f"sed -i '' 3s/a/b/ {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '3s/a/b/w {on_main}/out' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '3d' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' '/x/s/a/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i 's/a/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -Ei 's/a+/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i -e 's/a/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/' {scratch_dir}/f.md {on_main}/README.md"},
             DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/w {on_main}/out' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' 's/a/b/e' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '' '1d' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"sed -i '' -f {scratch_dir}/s.sed {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed -i '/x/' 's/a/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"sed --in-place=../x 's/a/b/' {scratch_dir}/f.md"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && sed -i '' 's/a/b/' ../f.md"}, DENY),
            ("Bash", {"command": "git commit -m x"}, DENY),
            ("Bash", {"command": f"git -C {on_main} stash"}, DENY),
            ("Bash", {"command": f"git -C {scratch_dir} init -q"}, None),
            ("Bash", {"command": f"git clone https://example.com/r.git {scratch_dir}/r"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && git clone https://example.com/r.git"},
             None),
            ("Bash", {"command": f"git clone https://example.com/r.git {root}/r"}, DENY),
            # A relative path counts from the directory the command reached.
            ("Bash", {"command": f"cd {scratch_dir}/d && git archive HEAD | tar -x -C ."}, None),
            ("Bash", {"command": f"cd {scratch_dir} && mkdir -p d && touch d/x && cp d/x d/y"},
             None),
            ("Bash", {"command": f"cd {scratch_dir} && echo x > out"}, None),
            ("Bash", {"command": f"cd {scratch_dir}; echo x > out"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && cat > out <<'EOF'\nx\nEOF"}, None),
            ("Bash", {"command": "echo x > out"}, DENY),
            ("Bash", {"command": f"echo x > out && cd {scratch_dir}"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && echo x > {on_main}/out"}, DENY),
            ("Bash", {"command": f"cd $(echo {scratch_dir}) && echo x > out"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} | echo x > out"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} > out"}, DENY),
            ("Bash", {"command": "touch x"}, DENY),
            ("Bash", {"command": f"cp {scratch_dir}/a.txt b.txt"}, DENY),
            ("Bash", {"command": f"cp a.txt {scratch_dir}/d/"}, None),
            ("Bash", {"command": f"cp -t {scratch_dir}/d {scratch_dir}/a"}, None),
            ("Bash", {"command": f"cp -t {scratch_dir}/d {on_main}/a"}, DENY),
            ("Bash", {"command": f"cp -t{on_main} {scratch_dir}/a"}, DENY),
            ("Bash", {"command": f"cp --target={on_main} {scratch_dir}/a"}, DENY),
            ("Bash", {"command": f"cp -r {on_main}/d {scratch_dir}/d"}, None),
            ("Bash", {"command": f"cp {scratch_dir}/a {on_main}/x"}, DENY),
            ("Bash", {"command": f"cp -t {on_main} {scratch_dir}/a"}, DENY),
            ("Bash", {"command": f"cp -rt {on_main} {scratch_dir}/a"}, DENY),
            ("Bash", {"command": f"cp --target-directory={on_main} {scratch_dir}/a"}, DENY),
            ("Bash", {"command": f"cp -- {scratch_dir}/a -x"}, DENY),
            ("Bash", {"command": f"mv {on_main}/README.md {scratch_dir}/r"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && touch ../x"}, DENY),
            # An rm outside every repo passes, unless its path may reach into one.
            ("Bash", {"command": f"rm {not_repo}/x.txt"}, None),
            # A mode or owner change names no content: the mode is not a path, and like
            # an rm it passes in scratch or outside every repo.
            ("Bash", {"command": f"chmod +x {scratch_dir}/x.sh"}, None),
            ("Bash", {"command": f"chmod 755 {scratch_dir}/x.sh"}, None),
            ("Bash", {"command": f"chmod -R u+x {scratch_dir}/d"}, None),
            ("Bash", {"command": f"chmod --reference={scratch_dir}/a {scratch_dir}/b"}, None),
            ("Bash", {"command": f"chown u:g {scratch_dir}/x.sh"}, None),
            ("Bash", {"command": f"chmod +x {not_repo}/x.txt"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && chmod +x x.sh"}, None),
            ("Bash", {"command": f"chmod +x {on_main}/x.sh"}, DENY),
            ("Bash", {"command": "chmod +x x.sh"}, DENY),
            ("Bash", {"command": f"chmod +x {scratch_dir}/a {on_main}/b"}, DENY),
            ("Bash", {"command": f"chmod -R +x {root}"}, DENY),
            ("Bash", {"command": f"chmod +x {scratch_dir}/$X"}, DENY),
            ("Bash", {"command": "chmod +x"}, DENY),
            ("Bash", {"command": f"cd {not_repo} && rm -f x.txt"}, None),
            ("Bash", {"command": f"rm -f {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"rm -rf {root}"}, DENY),
            ("Bash", {"command": f"rm {not_repo}/*.txt"}, DENY),
            ("Bash", {"command": f"rm {not_repo}/$X"}, DENY),
            ("Bash", {"command": f"touch {not_repo}/x.txt"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && touch $X"}, DENY),
            # A run-time word under a scratch root can carry `..` back out of it.
            ("Bash", {"command": f"touch {scratch_dir}/$X"}, DENY),
            ("Bash", {"command": f"rm {scratch_dir}/$X"}, DENY),
            ("Bash", {"command": f"cp a.txt {scratch_dir}/$X"}, DENY),
            ("Bash", {"command": f"echo x > {scratch_dir}/$X"}, DENY),
            ("Bash", {"command": f"git -C {on_main} archive -o {scratch_dir}/$X.tar HEAD"},
             DENY),
            ("Bash", {"command": f"tar -x -C {scratch_dir}/$D"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && touch {{{on_main}/x,a}}"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && mv {on_main}/README.md ."}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && tar -x -C d -C ../.."}, DENY),
            ("Bash", {"command": f"(cd {scratch_dir}) && touch x"}, DENY),
            # A `cd` that may run in a process of its own leaves the directory unknown.
            ("Bash", {"command": f"cd {scratch_dir} && git init -q"}, None),
            ("Bash", {"command": f"(cd {scratch_dir}) && git commit -m x"}, DENY),
            ("Bash", {"command": f"echo $(cd {scratch_dir}) && git commit -m x"}, DENY),
            ("Bash", {"command": f"echo `cd {scratch_dir}` && git commit -m x"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} | cat && git commit -m x"}, DENY),
            ("Bash", {"command": f"cat x | cd {scratch_dir} && git commit -m x"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} & git commit -m x"}, DENY),
            ("Bash", {"command": f"{{ cd {scratch_dir}; }} | cat; git commit -m x"}, DENY),
            ("Bash", {"command": f"if cd {scratch_dir}; then true; fi | cat; git commit -m x"},
             DENY),
            ("Bash", {"command": f"bash -c 'cd {scratch_dir}' && git commit -m x"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && ls | wc -l && git init -q"}, None),
            ("Bash", {"command": f"pushd {scratch_dir} && git init -q"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && pushd {on_main} && git commit -m x"},
             DENY),
            ("Bash", {"command": f"pushd {scratch_dir} && popd && git commit -m x"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && pushd +1 && git commit -m x"}, DENY),
            ("Bash", {"command": f"rm -rf {on_main}/README.md \\`"}, DENY),
            ("Bash", {"command": f"git clone --depth 1 -b v1 https://example.com/r.git "
                                 f"{scratch_dir}/r2"}, None),
            ("Bash", {"command": f"/bin/cp a {on_main}/x"}, DENY),
            ("Bash", {"command": f"/usr/bin/sed -i '' s/a/b/ {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"uv run sed -i '' s/a/b/ {on_main}/README.md"}, DENY),
            ("Bash", {"command": f"uv run --with x cp a {on_main}/x"}, DENY),
            ("Bash", {"command": f"uv run -q uv run touch {on_main}/x"}, DENY),
            ("Bash", {"command": f"uv run cd {scratch_dir} && touch x"}, DENY),
            ("Bash", {"command": f"env cd {scratch_dir}; touch x"}, DENY),
            ("Bash", {"command": f"patch {scratch_dir}/f.md {scratch_dir}/p.diff"}, None),
            ("Bash", {"command": f"patch {scratch_dir}/f.md {scratch_dir}/multi.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && patch f.md multi.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && xargs patch f.md mixed.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && echo {on_main}/README.md "
                                 "| xargs sed -i '' s/a/b/"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && echo f.md | xargs cat"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && patch f.md mixed.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && patch f.md indent.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && patch f.md p.diff"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && patch --out={on_main}/README.md f.md p.diff"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && patch -b -B {on_main}/x- f.md p.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && patch -g 1 {on_main}/README.md p.diff"}, DENY),
            ("Bash", {"command": f"patch -p1 -o {scratch_dir}/out.md -i {scratch_dir}/p.diff "
                                 f"{on_main}/README.md"}, None),
            ("Bash", {"command": f"patch {on_main}/README.md {scratch_dir}/p.diff"}, DENY),
            ("Bash", {"command": f"patch -p1 < {scratch_dir}/p.diff"}, DENY),
            ("Bash", {"command": f"patch -d {scratch_dir} -p1 -i {scratch_dir}/p.diff"}, DENY),
            ("Bash", {"command": f"patch -r {on_main}/x.rej {scratch_dir}/f.md "
                                 f"{scratch_dir}/p.diff"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env -C {on_main} sed -i '' s/a/b/ README.md"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env -C {on_main} -S 'sed -i s/a/b/ README.md'"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && caffeinate -i env -C {on_main} "
                                 "-S 'sed -i s/a/b/ README.md'"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && GOFLAGS=-v env -C {on_main} go mod tidy"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env --chdir={on_main} touch README.md"},
             DENY),
            ("Bash", {"command": f"env -C {scratch_dir} sed -i '' 's/a b/c/' f.md"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && env -iC {on_main} sed -i '' s/a/b/ README.md"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env -iC{on_main} sed -i '' s/a/b/ README.md"},
             DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env -S '-C{on_main} touch README.md'"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && env -i -S '-C {on_main} touch README.md'"},
             DENY),
            ("Bash", {"command": f"env -iC{scratch_dir} sed -i '' 's/a b/c/' f.md"}, None),
            ("Bash", {"command": f"cd {scratch_dir} && uv run --directory {on_main} "
                                 "sed -i '' s/a/b/ README.md"}, DENY),
            ("Bash", {"command": f"cd {on_main} && uv --directory {scratch_dir} run "
                                 "sed -i '' 's/a b/c/' f.md"}, None),
            ("Bash", {"command": f"uv --color never run sed -i '' s/a/b/ {on_main}/README.md"},
             DENY),
            ("Bash", {"command": f"uv run sed -i '' 's/a b/c/' {scratch_dir}/f.md"}, None),
            ("Bash", {"command": f"uv run python3 {not_repo}/tool.py"}, None),
            ("Bash", {"command": f"{not_repo}/tool.sh"}, None),
            ("Edit", {"file_path": f"{on_main}/README.md"}, DENY),
            ("Write", {"file_path": f"{on_main}/sub/new.py"}, DENY),
            ("Write", {"file_path": f"{on_main}/ignored/new.txt"}, None),
            ("Edit", {"file_path": f"{on_main}/build.log"}, None),
            ("Edit", {"file_path": f"{on_main}/tracked.log"}, DENY),
            ("Edit", {"file_path": f"{on_main}/.gitignore"}, DENY),
            ("Write", {"file_path": f"{on_main}/.claude/settings.local.json"}, DENY),
            ("Edit", {"file_path": f"{on_main}/.git/config"}, DENY),
            ("Bash", {"command": f"rm -f {on_main}/build.log"}, None),
            ("Bash", {"command": f"rm -f {on_main}/tracked.log"}, DENY),
            ("Bash", {"command": f"echo x > {on_main}/build.log"}, DENY),
            ("Write", {"file_path": f"{scratch_dir}/note.md"}, None),
            ("Write", {"file_path": f"{not_repo}/note.md"}, None),
            ("EnterWorktree", {}, DENY),
        ]
        try:
            for tool, tool_input, expected in gate_cases:
                got = decide(tool, tool_input, False, on_main)
                got = got[0] if got else None
                ok = got == expected
                failures += not ok
                print(f"{'ok  ' if ok else 'FAIL'} gate {tool} {tool_input} -> {got}"
                      + ("" if ok else f" (want {expected})"))
            got = decide("EnterWorktree", {}, True, on_main)
            got = got[0] if got else None
            ok = got == ASK
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} gate EnterWorktree, gate open -> {got}")
        finally:
            (GATE_SCRATCH_ROOTS, TMP_ROOT, REPO_ROOTS, SCRATCH_ROOTS,
             SCRATCH_PREFIXES) = saved_roots
        # A script whose text holds a command that needs words asks once, in every state.
        scripts = {
            "deploy.sh": "#!/bin/sh\nhelm upgrade r ./c --kube-context X -n Y\n",
            "cleanup.py": 'import subprocess\nsubprocess.run(["kubectl", "delete", "pod", "p"])\n',
            "mock.sh": "curl -X PUT http://localhost:8081/x -d a\n",
            "remote.sh": 'curl -X POST "$URL" -d a\n',
            "read.sh": "kubectl get pods --context X -n Y\n",
            "built.sh": 'helm "$1" r ./c\n',
            "kubeconfig.sh": 'kubectl config --kubeconfig="$kc" delete-context x\n',
            "mixed.sh": "curl -H 'Origin: http://localhost' -X POST https://example.com/x\n",
            "upload.sh": 'glab api "projects/p/uploads" --form "file=@$f"\n',
            "label.sh": "gh api repos/o/r/labels -f name=x\n",
            "query.sh": "glab api --method GET projects/p/labels -f search=x\n",
        }
        for name, text in scripts.items():
            with open(os.path.join(not_repo, name), "w") as f:
                f.write(text)
        script_cases = [
            # (command, expected decision with the gate open), run from the scripts' directory
            ("./deploy.sh", ASK),
            ("bash deploy.sh", ASK),
            ("python3 cleanup.py", ASK),
            ("python3 -u cleanup.py", ASK),
            ("python3 -uB cleanup.py", ASK),
            ("python3 -I -W ignore cleanup.py", ASK),
            ("python3 -Wignore -X dev cleanup.py", ASK),
            ("python3 --check-hash-based-pycs never cleanup.py", ASK),
            ("python3 -- cleanup.py", ASK),
            ("python3 -c 'print(1)' cleanup.py", None),
            ("uv run --with x python cleanup.py", ASK),
            ("./mock.sh", None),
            ("sh remote.sh", ASK),
            ("./read.sh", None),
            ("./built.sh", None),
            ("./kubeconfig.sh", None),
            ("./mixed.sh", ASK),
            ("./upload.sh", ASK),
            ("./label.sh", ASK),
            ("./query.sh", None),
            (f"cd {root} && ./plain/deploy.sh", ASK),
            (f"(cd {root} && ./plain/deploy.sh)", ASK),
            (f"(cd {root} && ./plain/read.sh)", ASK),
            ("bash -c 'echo deploy.sh'", None),
            ("./missing.sh", None),
        ]
        # python -m loads a module from the working directory first, unless -I or -P.
        for rel in ("evilmod.py", "evilpkg/__main__.py", "initpkg/__init__.py",
                    "initpkg/sub.py", "readmod.py", "evilenv/bin/python", "pyp/evilpp.py"):
            os.makedirs(os.path.dirname(os.path.join(not_repo, rel)), exist_ok=True)
            with open(os.path.join(not_repo, rel), "w") as f:
                f.write(scripts["read.sh" if rel in ("initpkg/sub.py", "readmod.py")
                                else "deploy.sh"])
        script_cases += [
            ("python3 -m evilmod", ASK),
            ("python3 -mevilmod", ASK),
            ("python3 -u -m evilmod x", ASK),
            ("python3 -m evilpkg", ASK),
            ("python3 -m initpkg.sub", ASK),
            ("uv run python3 -m evilmod", ASK),
            ("uv run -m evilmod", ASK),
            ("uv run -m evilmod.py", ASK),
            ("python3 -m evilmod.py", ASK),
            ("python3 -m evilmod.sub", ASK),
            ("python3 -I -m evilmod.py", None),
            ("uv run -qm evilmod", ASK),
            ("uv run --with x --module evilmod", ASK),
            ("uv run --python 3.12 -m evilmod", ASK),
            ("uv run -p ./cleanup.py", ASK),
            ("uv run --python ./cleanup.py python3 -c 'x'", ASK),
            ("uv run -p 3.12 -m readmod", None),
            ("uv run -p evilenv pytest", ASK),
            ("uv run --python ./evilenv/ pytest", ASK),
            ("uv run -w x -m evilmod", ASK),
            ("uv run -qw x -m evilmod", ASK),
            ("uv run -wnumpy python3 -m evilmod", ASK),
            ("uv run -qw x python3 cleanup.py", ASK),
            ("uv run --color never -m evilmod", ASK),
            ("uv run --env-file e python3 cleanup.py", ASK),
            ("uv run --group dev python3 cleanup.py", ASK),
            ("uv run -qp ./cleanup.py", ASK),
            ("uv run --python-preference only-system python3 cleanup.py", ASK),
            ("uv run --max-recursion-depth 9 -m evilmod", ASK),
            ("uv --color never run python3 cleanup.py", ASK),
            ("uv --cache-dir c run -m evilmod", ASK),
            ("uv --preview-features x run python3 cleanup.py", ASK),
            ("uv -q --project p run -p ./cleanup.py", ASK),
            ("UV_PYTHON=./cleanup.py uv run pytest", ASK),
            ("env UV_PYTHON=evilenv uv run pytest", ASK),
            ("UV_PYTHON=./cleanup.py uv run -p 3.12 pytest", None),
            ("UV_PYTHON=3.12 uv run -m readmod", None),
            ("export UV_PYTHON=./cleanup.py && uv run pytest", ASK),
            ("export UV_PYTHON=./cleanup.py; unset UV_PYTHON; uv run pytest", None),
            ("UV_PYTHON=./cleanup.py; export UV_PYTHON; uv run pytest", ASK),
            ("export UV_PYTHON=./cleanup.py; bash -c 'uv run pytest'", ASK),
            ("UV_PYTHON=./cleanup.py bash -c 'uv run pytest'", ASK),
            ("uv sync -p ./cleanup.py", ASK),
            ("uv venv --python evilenv", ASK),
            ("uv pip install -p ./cleanup.py x", ASK),
            ("uv python find ./cleanup.py", ASK),
            ("uv python find --color never ./cleanup.py", ASK),
            ("uvx -p ./cleanup.py ruff", ASK),
            ("uvx --from x -p ./cleanup.py ruff", ASK),
            ("UV_PYTHON=./cleanup.py uv sync", ASK),
            ("uv run --with xp -p ./cleanup.py pytest", ASK),
            ("uv sync -p 3.12", None),
            ("uv run uv run -p ./cleanup.py pytest", ASK),
            ("python3.12 build_vllm_overlay.py", ASK),
            ("PYTHONPATH=pyp python3 -m evilpp", ASK),
            ("env PYTHONPATH=x:pyp python3 -P -m evilpp", ASK),
            ("PYTHONPATH=pyp uv run -m evilpp", ASK),
            ("PYTHONPATH=$D python3 -m readmod", ASK),
            ("PYTHONPATH=pyp python3 -E -m evilpp", None),
            ("PYTHONPATH=pyp python3 -I -m evilpp", None),
            ("python3 -m evilpp", None),
            ("uv run env PYTHONPATH=pyp python3 -m evilpp", ASK),
            ("export PYTHONPATH=pyp; python3 -m evilpp", ASK),
            ("PYTHONPATH=pyp; export PYTHONPATH; python3 -m evilpp", ASK),
            ("export PYTHONPATH=pyp; unset PYTHONPATH; python3 -m evilpp", None),
            ("uv run --directory pyp -m evilpp", ASK),
            ("uv --directory=pyp run python3 evilpp.py", ASK),
            ("uv --directory $D run python3 x.py", ASK),
            ("uv run --directory pyp python3 cleanup.py", None),
            ("uv run uv run --directory pyp python3 evilpp.py", ASK),
            ("bash -c 'python3 cleanup.py'", ASK),
            ("sh -c 'cd pyp && python3 -m evilpp'", ASK),
            ("uv run bash -c 'python3 -m evilmod'", ASK),
            ("bash -c 'cd pyp' && python3 cleanup.py", ASK),
            ("bash -c 'python3 -m readmod'", None),
            ("uv run -p ./cleanup.py bash -c 'true'", ASK),
            ("PYTHONPATH=pyp bash -c 'python3 -m evilpp'", ASK),
            ("export PYTHONPATH=pyp; bash -c 'python3 -m evilpp'", ASK),
            ("env -i python3 cleanup.py", ASK),
            ("env -u HOME PYTHONPATH=pyp python3 -m evilpp", ASK),
            ("env -S 'python3 cleanup.py'", ASK),
            ("echo x | xargs python3 cleanup.py", ASK),
            ("echo x | xargs -n 1 python3 -m evilmod", ASK),
            ("echo x | xargs -I{} python3 readmod.py {}", None),
            ("echo x | xargs -R 1 -I{} python3 cleanup.py {}", ASK),
            ("echo x | xargs -S 255 -I{} python3 cleanup.py {}", ASK),
            ("echo x | xargs -0n 1 python3 cleanup.py", ASK),
            ("echo x | xargs --max-args 1 python3 cleanup.py", ASK),
            ("env -C pyp python3 evilpp.py", ASK),
            ("env -C pyp -S 'python3 evilpp.py x y'", ASK),
            ("env -S 'PYTHONPATH=pyp python3 -m evilpp'", ASK),
            ("caffeinate -i env -S 'PYTHONPATH=pyp python3 -m evilpp'", ASK),
            ("env -iC pyp python3 evilpp.py", ASK),
            ("env -S '-i PYTHONPATH=pyp python3 -m evilpp'", ASK),
            (f"cd {root} && python3 -m plain.evilmod", ASK),
            ("python3 -I -m evilmod", None),
            ("python3 -Pm evilmod", None),
            ("python3 -c 'x' -m evilmod", None),
            ("python3 -m readmod", None),
            ("python3 -m json.tool", None),
        ]
        # A copy of this hook in a scratch root runs its own CLI unscanned; any other run of
        # it, or a copy outside scratch, is scanned like any script.
        own_dir = os.path.join(root, "own-scratch")
        os.makedirs(own_dir)
        own = os.path.join(own_dir, os.path.basename(__file__))
        loose = os.path.join(not_repo, os.path.basename(__file__))
        for copy in (own, loose):
            with open(copy, "w") as f:
                f.write(scripts["deploy.sh"])
        script_cases += [
            (f"python3 {own} --selftest", None),
            (f"python3 {own} 'git status'", None),
            (f"python3 {own} --open 'git status'", None),
            (f"python3 {own} --other x", ASK),
            (f"python3 {own} a b", ASK),
            (f"bash {own} 'git status'", ASK),
            (f"{own} --selftest", ASK),
            (f"python3 {loose} --selftest", ASK),
        ]
        saved_scratch = GATE_SCRATCH_ROOTS
        GATE_SCRATCH_ROOTS = (os.path.realpath(own_dir) + "/",)
        try:
            for command, expected in script_cases:
                got = decide("Bash", {"command": command}, True, not_repo)
                got = got[0] if got else None
                ok = got == expected
                failures += not ok
                print(f"{'ok  ' if ok else 'FAIL'} script {command!r} -> {got}"
                      + ("" if ok else f" (want {expected})"))
        finally:
            GATE_SCRATCH_ROOTS = saved_scratch
    # A write under the scratch root lands only in a path the user named.
    named = (os.path.realpath("/tmp/claude/a.diff"), os.path.realpath("/tmp/claude/out"),
             os.path.realpath("/tmp/n.txt"))
    named_cases = [
        ("Bash", {"command": "git show x > /tmp/claude/a.diff"}, None),
        ("Bash", {"command": "git show x > /private/tmp/claude/a.diff"}, None),
        ("Write", {"file_path": "/tmp/claude/out/x.md"}, None),
        ("Bash", {"command": "mkdir -p /tmp/claude/out/d"}, None),
        ("Write", {"file_path": "/tmp/claude/outside.md"}, DENY),
        ("Write", {"file_path": "/tmp/claude/out-of/x.md"}, DENY),
        ("Bash", {"command": "git show x > /tmp/claude/a.diff2"}, DENY),
        ("Write", {"file_path": "/tmp/n.txt"}, None),
        # A relative folder target counts from the call's own working directory, here /.
        ("Bash", {"command": "cp /x/.env usr"}, ASK),
    ]
    for tool, tool_input, expected in named_cases:
        got = decide(tool, tool_input, True, "/", named)
        got = got[0] if got else None
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} named {tool} {tool_input} -> {got}"
              + ("" if ok else f" (want {expected})"))
    # The gate decides by RATING_EXTENSION whatever the rating config holds: with each config
    # state set where a config load reads it - no config, or one repointed at an extension
    # that drops every workplace entry - and the rating hook's load run first in this
    # process, the gate's own startup puts its tables back, and the whole table decides as
    # before.
    def table_matches():
        return all((decide(tool, {"command": tin} if tool == "Bash" else tin, gate_open,
                           os.path.join(REPO_ROOTS[0], "no-repo")) or (None,))[0] == expected
                   for gate_open, tool, tin, expected in cases)

    with tempfile.TemporaryDirectory() as root:
        def write(name, text):
            path = os.path.join(root, name)
            with open(path, "w") as f:
                f.write(text)
            return path

        config_states = {
            "no config": os.path.join(root, "no-config.json"),
            "repointed config": write("config.json", json.dumps(
                {command_parser.CONFIG_KEY: write("empty_ext.py", "")})),
        }
        saved_config = command_parser.CONFIG_PATH
        for label, config in config_states.items():
            command_parser.CONFIG_PATH = config
            command_parser.configure(config)
            start()
            ok = EXTENSION_ERROR is None and table_matches()
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} {label}: every decision as before")
        command_parser.CONFIG_PATH = saved_config
        # An extension that fails to load denies every call the hook guards, naming why.
        EXTENSION_ERROR = load_rating_extension(write("broken_ext.py", "HANDLERS = {"))
        denied = [decide(tool, {"command": tin} if tool == "Bash" else tin, gate_open)
                  for gate_open, tool, tin, _ in cases]
        ok = all(d is not None and d[0] == DENY and "SyntaxError" in d[1] for d in denied)
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} broken extension: every call denied -> {denied[0]}")
        unguarded = hook_output({"tool_name": "Read", "session_id": "s",
                                 "tool_input": {"file_path": "/x"}})
        failures += unguarded is not None
        print(f"{'ok  ' if unguarded is None else 'FAIL'} broken extension: Read left alone")
        start()
    total = (len(cases) + len(payload_cases) + len(count_cases) + len(branch_cases)
             + len(script_cases) + len(gate_cases) + len(named_cases) + len(config_states)
             + 2 + 1)
    print(f"\n{total - failures}/{total} passed")
    return failures == 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    if argv:
        gate_open = "--open" in argv
        argv = [a for a in argv if a != "--open"]
        if argv and argv[0] == "--tool":
            tool_name = argv[1]
            tool_input = dict(a.split("=", 1) for a in argv[2:])
            print(describe(tool_name, tool_input, gate_open))
        else:
            for cmd in argv:
                print(f"{describe('Bash', {'command': cmd}, gate_open)}  {cmd}")
        sys.exit(0)
    try:
        main()
    except Exception as exc:
        print(f"tool-gate.py: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(2)
