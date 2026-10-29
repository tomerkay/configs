#!/usr/bin/env python3
"""PreToolUse hook: the `LFG!` gate, plus the READ/WRITE/DANGER rating on Bash commands.

For Bash it classifies what the command can change and rewrites the tool's `description`
so a permission dialog opens with the rating:

    🟢 READ    changes nothing
    🟠 WRITE   changes local, recoverable state (files, commits, installs, helm releases)
    🔴 DANGER  destroys data or changes live cluster / remote state

Anything the classifier does not recognise is WRITE: a wrong orange costs a glance, a
wrong green is the failure this hook exists to prevent.

For Bash, Edit, Write, NotebookEdit, EnterWorktree and every MCP tool it then decides,
from the gate state lfg-state.py records per session: a change to a git repo before
`LFG!` is denied with the refusal line, while opaque code - an interpreter, a container,
a script - passes and repo-watch.py reports a repo change it makes; every command that
needs the user's words for that one command asks in every state, and so does, once per
run, a script whose text holds one; a push is denied in every state, since the user runs
it; and the pin rules for kubectl, helm and helmfile are enforced. A program the
classifier does not know asks instead of denying, so a read it has not met never gets the
refusal line. A commit, merge, cherry-pick, revert or am that lands on a repo's default
branch is denied in every state, outside the repos in DEFAULT_BRANCH_EXEMPT, which are
committed on main by design.

An `rm` whose every path is a literal under the scratch root is dropped from the command
before the permission rules see it: the org's `Bash(rm:*)` ask rule prompts on any `rm`
and no allow rule outranks an ask rule, while scratch is per session and left behind
anyway, so the delete costs a prompt and buys nothing. An `rm` that names a scratch path
alongside anything outside the scratch root is forced to prompt instead, so that
`rm -rf /private/tmp/claude/x ~/repos` or `rm -rf /private/tmp/claude/../..` never
passes as scratch cleanup.

CLI: `tool-gate.py [--open] <command>...` prints the rating and the decision for each
Bash command with the gate closed (default) or open; `--tool <name> <field>=<value>...`
does the same for another tool; `--selftest` runs the decision table's cases.
"""

import contextlib
import json
import os
import re
import shlex
import subprocess
import sys

READ, WRITE, DANGER = "🟢 READ", "🟠 WRITE", "🔴 DANGER"
RANK = {READ: 0, WRITE: 1, DANGER: 2}
LABEL_RE = re.compile(r"^(?:🟢 READ|🟠 WRITE|🔴 DANGER)\s*[·:|-]?\s*")

SEPARATORS = {";", ";;", "|", "||", "&&", "&", "(", ")", "|&"}
REDIRECT_OUT = {">", ">>", "&>", "&>>", ">|"}
# The descriptor digit of `2>&1` or `2>/dev/null`: shlex would lex it as a word of its own.
DESCRIPTOR_RE = re.compile(r"(?<![^\s();|&])\d+(?=[<>])")
HARMLESS_TARGETS = {"/dev/null", "/dev/stderr", "/dev/stdout", "/dev/tty"}
SCRATCH_PREFIXES = ("/tmp/claude/", "/private/tmp/claude/")
SCRATCH_ROOTS = tuple(os.path.realpath(p.rstrip("/")) + "/" for p in SCRATCH_PREFIXES)
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Shell words that precede the real program on a segment and carry no rating of their own.
TRANSPARENT = {"do", "then", "else", "elif", "!", "{", "}", "if", "while", "until", "time",
               "exec", "command", "builtin", "nohup", "nice", "env", "stdbuf", "caffeinate"}
# A segment made only of one of these is loop/branch syntax.
SYNTAX_ONLY = {"done", "fi", "esac", "in", "function", "then", "do", "else", "}", "{"}
# `for p in a b` names variables, not a program: the body is its own segment after `do`.
LOOP_HEADERS = {"for", "case", "select"}
# The words that open and close a compound command, whose body a pipe runs apart.
COMPOUND_OPENERS = {"if", "while", "until", "for", "case", "select", "{"}
COMPOUND_CLOSERS = {"fi", "done", "esac", "}"}
CHDIR_PROGRAMS = {"cd", "pushd", "popd"}

READ_PROGRAMS = {
    "cat", "head", "tail", "less", "more", "wc", "grep", "egrep", "fgrep", "zgrep", "rg", "ag",
    "ack", "fd", "ls", "tree", "stat", "file", "du", "df", "echo", "printf", "true", "false",
    "test", "[", "[[", "which", "whereis", "type", "whoami", "id", "hostname", "uname", "date",
    "pwd", "printenv", "jq", "sort", "uniq", "cut", "tr", "column", "diff", "cmp", "comm",
    "md5", "md5sum", "sha1sum", "sha256sum", "shasum", "base64", "xxd", "od", "strings",
    "hexdump", "realpath", "dirname", "basename", "readlink", "seq", "nl", "rev", "paste",
    "fold", "expand", "bc", "dc", "sleep", "cal", "uptime", "ps", "pgrep", "lsof", "netstat",
    "ss", "lsblk", "free", "vmstat", "iostat", "sw_vers", "getconf", "locale", "tty", "history",
    "jobs", "alias", "declare", "typeset", "export", "set", "unset", "setopt", "unsetopt",
    "bindkey", "zstyle", "cd", "pushd", "popd",
    "dirs", "local", "readonly", "shift", "wait", "hash", "umask", "read", "zcat", "gzcat",
    "bzcat", "xzcat", "dig", "nslookup", "host", "ping", "traceroute", "mtr", "whois",
    "journalctl", "kustomize", "pytest", "mypy", "pyright", "flake8", "pylint", "shellcheck",
    "yamllint", "hadolint", "glow", "bat", "fzf", "tldr", "man", "info", "cksum", "iconv",
    "look", "join", "split", "fmt", "pr", "tac", "expr", "let", "arch", "nproc", "sysctl",
    "ifconfig", "ip", "route", "arp", "ioreg", "system_profiler", "pbpaste", "mdfind",
    "gofmt", "glab-ci-view", "wrenchmark-report", "gpg",
}
# `split`, `gpg`, `iconv` write files only with explicit output options the handlers below catch.

WRITE_PROGRAMS = {
    "cp", "mv", "mkdir", "touch", "ln", "install", "patch", "tee", "truncate", "chmod", "chown",
    "chgrp", "zip", "gzip", "gunzip", "bzip2", "xz", "open", "osascript", "code", "vim", "nvim",
    "vi", "nano", "emacs", "ssh", "scp", "sftp", "source", ".", "eval", "uvx", "pipx",
    "psql", "mysql", "sqlite3", "redis-cli", "mongosh", "perl", "ruby", "node", "deno", "bun",
    "pre-commit", "kubectx", "kubens", "k9s", "pbcopy", "say", "afplay", "xattr",
    "defaults", "crontab", "ollama",
}

DANGER_PROGRAMS = {
    "rm", "rmdir", "dd", "mkfs", "shred", "diskutil", "kill", "pkill", "killall", "shutdown",
    "reboot", "halt", "sudo", "doas", "fdisk", "parted", "wipefs", "nvme", "fuser",
}

# Scripts that push images and move shared registry tags from their own subprocesses, where
# the hook never sees the push: their name is the only thing it can match.
PUBLISHING_SCRIPTS = {"build_vllm_overlay.py"}

GENERIC_READ_WORDS = {"list", "describe", "get", "show", "read", "info", "version", "help",
                      "status", "whoami", "print-access-token", "print-identity-token",
                      "get-iam-policy", "get-caller-identity", "ls", "presign", "tail", "logs",
                      "search", "lint", "validate", "explain", "cat", "tree", "diff"}
GENERIC_WRITE_WORDS = {"set", "create", "update", "add", "enable", "disable", "ssh", "scp",
                       "deploy", "run", "submit", "import", "export", "resize", "start", "stop",
                       "restart", "get-credentials", "login", "logout", "activate", "put",
                       "copy", "cp", "mv", "move", "sync", "push", "pull", "apply", "patch",
                       "scale", "edit", "attach", "exec", "init", "install", "upgrade",
                       "rollback", "cancel", "retry", "approve", "merge", "comment", "note",
                       "close", "reopen", "label", "annotate", "tag", "release"}
GENERIC_DANGER_WORDS = {"delete", "destroy", "remove", "rm", "rb", "terminate", "purge",
                        "drain", "reset", "revoke", "detach", "prune", "uninstall", "wipe",
                        "cordon", "uncordon", "taint", "evict", "kill", "force-unlock"}

# ----- the gate -----------------------------------------------------------------------

REFUSAL = 'YOU MUST WRITE "LFG!" for me to actually start implementing.'
STATE_DIR = os.path.expanduser("~/.claude/lfg-state")
OPEN_STATES = {"open", "one-turn"}
GATED_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit", "EnterWorktree"}
PATH_FIELD = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}

# Writes here never need the gate: scratch, plan mode and memory are harness bookkeeping.
GATE_SCRATCH_ROOTS = tuple(os.path.realpath(os.path.expanduser(p)) + "/"
                           for p in ("/private/tmp/claude", "~/.cache", "~/.claude/plans"))
MEMORY_ROOT_RE = re.compile(
    "^" + re.escape(os.path.realpath(os.path.expanduser("~/.claude/projects"))) + r"/[^/]+/memory/")
# GOTCHA: the lexer strips quotes, so a `~` the shell leaves literal ('~', "~", \~) reaches the
# scratch check looking like one it expands, and the shell expands `~` with its own HOME, which
# the command may set. A command holding either expands no `~` at all.
NO_HOME_EXPANSION_RE = re.compile(r"""['"\\]~|HOME""")
# Bash writers whose every positional path the script can read without path-sniffing.
SCRATCH_WRITERS = {"mkdir", "touch", "cp", "mv", "tee", "rm"}
# GOTCHA: brace expansion, a variable or a substitution can turn a relative word into an
# absolute path, so such a word is never joined to the working directory.
SHELL_EXPANSION_CHARS = set("${`")
# GOTCHA: an allowlist, because other tar options write outside -C (-P, --index-file, -c with
# -f) or run a program (--to-command, --use-compress-program). -C stays out of the short
# set so a clustered -xC never hides an extract target from the scratch check.
TAR_EXTRACT_SHORT = set("xvfzjJkopm")
TAR_EXTRACT_LONG = {"--extract", "--get", "--directory", "--file", "--gzip", "--bzip2", "--xz",
                    "--zstd", "--verbose", "--keep-old-files", "--no-same-owner",
                    "--no-same-permissions", "--strip-components", "--exclude"}
TAR_STDOUT_SHORT = TAR_EXTRACT_SHORT | {"O"}
TAR_STDOUT_LONG = TAR_EXTRACT_LONG | {"--to-stdout"}

# kubectl verbs CLAUDE.md names as writing live cluster state.
KUBECTL_WRITES_BY_CLAUDE_MD = {"apply", "delete", "create", "patch", "edit", "scale", "rollout"}
KUBECTL_ROLLOUT_READS = {"status", "history"}
# Verbs that write live cluster state the same way and that CLAUDE.md does not name.
KUBECTL_WRITES_WIDENED = {"replace", "set", "label", "annotate", "taint", "cordon", "uncordon",
                          "drain", "evict", "expose", "run", "debug", "autoscale", "certificate"}
KUBECTL_CONTEXT_SETTERS = {"use-context", "set-context"}
# Subcommands that never reach a cluster, so the pin rules do not apply.
KUBECTL_LOCAL = {"config", "kustomize", "completion", "options", "help"}
HELM_LOCAL = {"template", "lint", "show", "search", "pull", "package", "push", "registry",
              "create", "env", "verify", "repo", "dependency", "plugin", "version",
              "completion", "help"}
HELM_RELEASE_MOVES = {"uninstall", "delete", "del", "rollback"}
GIT_CONFIG_VALUE_FLAGS = {"-f", "--file", "--blob", "--default", "--type"}
GIT_CONFIG_READ_SUBCOMMANDS = {"get", "list"}
GIT_CONFIG_WRITE_SUBCOMMANDS = {"set", "unset", "edit", "rename-section", "remove-section"}
# GOTCHA: `clean` stores the object under .git/lfs/objects the way `fetch` fills .git/objects:
# no ref and no work-tree file moves, so it reads like the rest.
GIT_LFS_READ_SUBCOMMANDS = {"ls-files", "env", "status", "version", "help", "clean", "pointer",
                            "fsck", "locks"}
# Cluster-scoped commands where kubectl ignores -n; `get --raw` carries an API path instead.
NAMESPACE_FREE = {("get", "node"), ("get", "nodes"), ("describe", "node"), ("describe", "nodes"),
                  ("top", "node"), ("top", "nodes"), ("get", "crd"), ("get", "crds"),
                  ("get", "customresourcedefinitions"), ("get", "ns"), ("get", "namespace"),
                  ("get", "namespaces"), ("label", "node"), ("label", "nodes"),
                  ("annotate", "node"), ("annotate", "nodes"), ("taint", "node"),
                  ("taint", "nodes"), ("get", "clusterpolicy"), ("get", "clusterpolicies"),
                  ("get", "cpol"), ("describe", "clusterpolicy"),
                  ("describe", "clusterpolicies"), ("describe", "cpol")}
# Verbs whose only target is a node, so the second word is the node's name.
NODE_VERBS = {"cordon", "uncordon", "drain"}
KUBECTL_GLOBAL_VALUE_FLAGS = {
    "--context", "--kubeconfig", "-n", "--namespace", "--cluster", "--user", "-s", "--server",
    "--token", "--as", "--as-group", "--request-timeout", "--certificate-authority",
    "--client-certificate", "--client-key", "--tls-server-name", "--cache-dir", "--profile",
    "--profile-output", "-v", "--v", "--vmodule",
}
CRUSOE_GET_CREDENTIALS_VALUE_FLAGS = {"--project-name", "--project-id", "--kubeconfig-path",
                                      "--auth-type", "-f", "--format"}
HELM_GLOBAL_VALUE_FLAGS = {
    "--kube-context", "--kubeconfig", "-n", "--namespace", "--kube-apiserver", "--kube-token",
    "--kube-as-user", "--kube-as-group", "--kube-ca-file", "--registry-config",
    "--repository-cache", "--repository-config", "--burst-limit", "--qps",
}
HELMFILE_GLOBAL_VALUE_FLAGS = {
    "--kube-context", "-e", "--environment", "-f", "--file", "-n", "--namespace", "-l",
    "--selector", "--state-values-set", "--state-values-file", "-b", "--helm-binary",
    "--log-level", "-c", "--chart",
}
HELMFILE_RELEASE_WRITES = {"apply", "sync", "destroy", "delete"}
# Subcommands that reach the cluster, so the context pin applies; the rest render or fetch
# locally. A helmfile spreads its releases over namespaces, so -n is not required.
HELMFILE_CLUSTER = HELMFILE_RELEASE_WRITES | {"diff", "status", "test"}

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


def positionals(args):
    return [a for a in args if not a.startswith("-")]


def has_flag(args, *flags):
    return any(a in flags or any(a.startswith(f + "=") for f in flags) for a in args)


def dry_run(args):
    return any(a == "--dry-run" or (a.startswith("--dry-run=") and a != "--dry-run=none")
               for a in args)


def split_globals(args, value_flags):
    """Take a CLI's value-carrying global flags out of `args`, in `--flag X`, `--flag=X` and
    `-nX` forms, so the first positional left is the verb wherever the flags were typed."""
    rest, seen = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            rest.extend(args[i:])
            break
        name, eq, value = a.partition("=")
        if name in value_flags:
            if eq:
                seen[name] = value
            elif i + 1 < len(args):
                seen[name] = args[i + 1]
                i += 1
            else:
                seen[name] = ""
        elif len(a) > 2 and a[0] == "-" and a[1] != "-" and a[:2] in value_flags:
            seen[a[:2]] = a[2:]
        else:
            if a in ("-A", "--all-namespaces"):
                seen["-A"] = "true"
            rest.append(a)
        i += 1
    return rest, seen


def generic_verbs(args):
    """CLIs shaped `tool group... verb [flags]`: gcloud, crusoe, aws, az, argocd, flux."""
    words = set(positionals(args))
    if words & GENERIC_DANGER_WORDS or any(w.startswith(("delete-", "terminate-", "remove-"))
                                            for w in words):
        return DANGER
    if words & GENERIC_WRITE_WORDS:
        return WRITE
    if words & GENERIC_READ_WORDS or any(w.startswith(("describe-", "list-", "get-", "head-",
                                                        "batch-get-")) for w in words):
        return READ
    return WRITE


def git_subcommand_args(args):
    """The git subcommand and its arguments, with the global options ahead of it removed."""
    rest = list(args)
    while rest and rest[0] in ("-C", "-c", "--git-dir", "--work-tree", "--no-pager", "-P"):
        rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
    return [a for a in rest if not a.startswith("--git-dir=") and not a.startswith("--work-tree=")]


def classify_git(args):
    rest = git_subcommand_args(args)
    # GOTCHA: a config key can name a program git runs (core.fsmonitor, diff.external,
    # core.sshCommand, a `!` alias), so a `-c` ahead of the subcommand makes it a write.
    if "-c" in args[:len(args) - len(rest)]:
        return WRITE
    if not rest:
        return READ
    sub, rest = rest[0], rest[1:]
    pos = positionals(rest)
    force = has_flag(rest, "-f", "--force", "--force-with-lease")
    if sub == "archive":
        # -o also takes its value stuck (-ofile), which has_flag does not match.
        return WRITE if has_flag(rest, "--output") or any(a.startswith("-o") for a in rest) else READ
    if sub in {"status", "log", "show", "diff", "blame", "ls-files", "ls-tree", "ls-remote",
               "rev-parse", "rev-list", "describe", "cat-file", "name-rev", "merge-base",
               "shortlog", "grep", "for-each-ref", "show-ref", "check-ignore", "var",
               "count-objects", "diff-tree", "diff-index", "diff-files", "whatchanged",
               "range-diff", "version", "help", "cherry", "show-branch", "annotate", "bundle-verify",
               "check-attr", "check-ref-format", "fsck", "verify-commit", "verify-tag"}:
        # GOTCHA: git runs unsandboxed under the managed policy, and `log`/`diff`/`show --output`
        # write a file anywhere, so a read verb with it is a write.
        return WRITE if has_flag(rest, "--output") else READ
    if sub == "reflog":
        return READ if not pos or pos[0] == "show" else DANGER
    if sub == "branch":
        if has_flag(rest, "-l", "--list", "--contains", "--no-contains", "--merged",
                    "--no-merged", "--points-at", "--show-current"):
            return READ
        if has_flag(rest, "-D", "--delete", "-d", "-M", "-m", "-C", "-c", "-u",
                    "--set-upstream-to", "--unset-upstream", "--edit-description", "--move",
                    "--copy") or force:
            return DANGER if has_flag(rest, "-D", "--delete", "-d", "-M") or force else WRITE
        return READ if not pos else WRITE
    if sub == "tag":
        if has_flag(rest, "-d", "--delete"):
            return WRITE
        return READ if not pos or has_flag(rest, "-l", "--list", "-n", "--contains",
                                           "--points-at") else WRITE
    if sub == "remote":
        return READ if not pos or pos[0] in ("show", "get-url") else WRITE
    if sub == "stash":
        if pos and pos[0] in ("list", "show"):
            return READ
        return DANGER if pos and pos[0] in ("drop", "clear") else WRITE
    if sub == "config":
        if has_flag(rest, "--get", "--get-all", "--get-regexp", "--list", "-l",
                    "--show-origin", "--get-urlmatch"):
            return READ
        rest, _ = split_globals(rest, GIT_CONFIG_VALUE_FLAGS)
        pos = positionals(rest)
        if pos and pos[0] in GIT_CONFIG_READ_SUBCOMMANDS:
            return READ
        if pos and pos[0] in GIT_CONFIG_WRITE_SUBCOMMANDS:
            return WRITE
        # `git config <key>` alone reads; a value after the key, or an editing flag, writes.
        if len(pos) == 1 and not has_flag(rest, "--add", "--unset", "--unset-all",
                                          "--replace-all", "--remove-section"):
            return READ
        return WRITE
    if sub == "worktree":
        if pos and pos[0] == "list":
            return READ
        return DANGER if pos and pos[0] in ("remove", "prune") else WRITE
    if sub == "push":
        return DANGER
    if sub == "fetch":
        if force:
            return DANGER
        # A refspec with a local destination moves that local branch.
        return WRITE if any(":" in p for p in pos[1:]) else READ
    if sub == "reset":
        return DANGER if has_flag(rest, "--hard", "--merge") else WRITE
    if sub == "clean":
        return READ if has_flag(rest, "-n", "--dry-run") else DANGER
    if sub in ("checkout", "switch"):
        return DANGER if "--" in rest or force else WRITE
    if sub == "restore":
        return DANGER
    if sub in {"filter-branch", "filter-repo", "update-ref", "prune", "gc", "replace"}:
        return DANGER
    if sub == "lfs":
        if not pos:
            return READ
        if pos[0] == "logs":
            return WRITE if pos[1:2] in (["clear"], ["boomtown"]) else READ
        if pos[0] in ("push", "lock", "unlock"):
            return DANGER
        return READ if pos[0] in GIT_LFS_READ_SUBCOMMANDS else WRITE
    if sub in {"rebase", "cherry-pick", "merge", "am", "revert", "rm", "mv", "submodule",
               "add", "commit", "pull", "init", "clone", "apply", "notes", "bisect",
               "tag", "rerere", "sparse-checkout"}:
        return DANGER if force and sub in ("rebase", "rm", "clone", "pull") else WRITE
    return WRITE


def kubectl_exec_command(rest):
    if "--" not in rest:
        return None
    return rest[rest.index("--") + 1:]


def writes_inside_pod(verb, rest):
    """An exec that is not a read, a cp whose destination is `pod:path`, or an attach."""
    if verb == "exec":
        return classify_kubectl(rest) != READ
    if verb == "cp":
        paths = [a for i, a in enumerate(rest)
                 if not a.startswith("-") and not (i and rest[i - 1] in ("-c", "--container"))]
        return len(paths) > 2 and ":" in paths[-1]
    return verb == "attach"


def classify_kubectl(args):
    rest, _ = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if not pos:
        return READ
    verb = pos[0]
    if "$" in verb:
        return DANGER
    if dry_run(rest):
        return READ
    if verb in {"get", "describe", "logs", "log", "top", "explain", "api-resources",
                "api-versions", "version", "cluster-info", "events", "wait", "diff",
                "port-forward", "proxy", "completion", "options", "kustomize", "whoami"}:
        return READ
    if verb == "config":
        return READ if len(pos) > 1 and pos[1] in ("view", "get-contexts", "current-context",
                                                    "get-clusters", "get-users") else WRITE
    if verb == "rollout":
        return READ if len(pos) > 1 and pos[1] in KUBECTL_ROLLOUT_READS else DANGER
    if verb == "auth":
        return READ if len(pos) > 1 and pos[1] in ("can-i", "whoami") else WRITE
    if verb == "plugin":
        return READ if len(pos) > 1 and pos[1] == "list" else WRITE
    if verb == "exec":
        # An exec is whatever runs inside the pod. A shell, or stdin/tty with nothing after
        # `--`, is a write because nothing says what will be typed into it.
        before = rest[:rest.index("--")] if "--" in rest else rest
        if any(a in ("--stdin", "--tty") or re.match(r"^-[a-zA-Z]*[it]", a) for a in before):
            return WRITE
        command = kubectl_exec_command(rest)
        return classify_words(command) if command else WRITE
    if verb == "cp":
        return WRITE
    if verb in KUBECTL_WRITES_BY_CLAUDE_MD or verb in KUBECTL_WRITES_WIDENED:
        return DANGER
    return WRITE


def classify_helm(args):
    rest, _ = split_globals(args, HELM_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if not pos:
        return READ
    sub = pos[0]
    if "$" in sub:
        return DANGER
    if sub in {"list", "ls", "get", "status", "history", "show", "inspect", "template", "lint",
               "search", "env", "version", "verify", "completion", "help", "diff"}:
        return READ
    if sub == "repo":
        return READ if len(pos) > 1 and pos[1] in ("list", "index") else WRITE
    if sub == "dependency":
        return READ if len(pos) > 1 and pos[1] == "list" else WRITE
    if sub == "plugin":
        return READ if len(pos) > 1 and pos[1] == "list" else WRITE
    if sub in ("install", "upgrade"):
        if dry_run(rest):
            return READ
        return DANGER if has_flag(rest, "--force", "--force-conflicts") else WRITE
    if sub in HELM_RELEASE_MOVES:
        return DANGER
    return WRITE


def classify_helmfile(args):
    rest, _ = split_globals(args, HELMFILE_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    sub = pos[0] if pos else ""
    if sub in {"diff", "template", "lint", "status", "list", "build", "version", "help",
               "show-dag"}:
        return READ
    if sub in ("destroy", "delete"):
        return DANGER
    return WRITE


def http_method(args, short, long):
    for i, a in enumerate(args):
        if a in (short, long) and i + 1 < len(args):
            return args[i + 1].upper()
        if a.startswith(short) and len(a) > len(short) and short != "":
            return a[len(short):].upper()
        if a.startswith(long + "="):
            return a.split("=", 1)[1].upper()
    return "GET"


STDOUT_SINKS = ("/dev/null", "-")


def curl_output_targets(args):
    targets = []
    for i, a in enumerate(args):
        if a in ("-o", "--output"):
            targets.append(args[i + 1] if i + 1 < len(args) else "")
        elif a.startswith("--output="):
            targets.append(a.split("=", 1)[1])
        elif a.startswith("-o") and len(a) > 2:
            targets.append(a[2:])
    return targets


SAFE_HTTP_METHODS = {"GET", "HEAD", "OPTIONS"}
CURL_BODY_FLAGS = ("-T", "--upload-file", "-F", "--form", "--form-string", "-d", "--data",
                   "--data-raw", "--data-binary", "--data-urlencode", "--data-ascii", "--json")


def curl_sends_body(args):
    return has_flag(args, *CURL_BODY_FLAGS) or any(
        a.startswith(("-d", "-F", "-T")) and len(a) > 2 and not a.startswith("--") for a in args)


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


def classify_curl(args):
    method = http_method(args, "-X", "--request")
    if method == "DELETE":
        return DANGER
    if method not in SAFE_HTTP_METHODS:
        return WRITE
    if any(t not in STDOUT_SINKS for t in curl_output_targets(args)):
        return WRITE
    if has_flag(args, "-O", "--remote-name", "--remote-name-all") or curl_sends_body(args):
        return WRITE
    return READ


HTTP_METHODS = {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE", "TRACE", "CONNECT"}
XH_VALUE_FLAGS = {"-a", "--auth", "-A", "--auth-type", "-o", "--output", "--raw", "-p",
                  "--print", "-P", "--history-print", "--pretty", "-s", "--style", "--proxy",
                  "--timeout", "--max-redirects", "--verify", "--cert", "--cert-key", "--ssl",
                  "--http-version", "--resolve", "--interface", "--response-charset",
                  "--response-mime", "--session", "--session-read-only", "--format-options",
                  "--unix-socket", "--generate"}


def xh_request(args):
    """httpie syntax: an optional method in any case, the URL, then items; a `key=value`,
    `key:=json` or `key@file` item, or `--raw`, implies POST."""
    rest, _ = split_globals(args, XH_VALUE_FLAGS)
    pos = positionals(rest)
    method = pos[0].upper() if pos and pos[0].upper() in HTTP_METHODS else None
    url = (pos[1:2] if method else pos[:1]) or [""]
    items = pos[2:] if method else pos[1:]
    body = (any(("=" in a and "==" not in a) or "@" in a for a in items)
            or has_flag(args, "--raw"))
    return method or ("POST" if body else "GET"), url[0]


def classify_xh(args):
    method, _ = xh_request(args)
    if method == "DELETE":
        return DANGER
    if method not in SAFE_HTTP_METHODS:
        return WRITE
    if has_flag(args, "-d", "--download", "-o", "--output"):
        return WRITE
    return READ


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


GH_GLOBAL_VALUE_FLAGS = {"-R", "--repo"}


def classify_gh(args):
    args, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    pos = positionals(args)
    if not pos:
        return READ
    group = pos[0]
    sub = pos[1] if len(pos) > 1 else ""
    if group == "api":
        if sub == "graphql" and not any("mutation" in a for a in args):
            return READ
        method = http_method(args, "-X", "--method")
        if method == "DELETE":
            return DANGER
        # Fields switch the default method to POST; under an explicit GET they are query params.
        fields = has_flag(args, "-f", "-F", "--field", "--raw-field")
        if (method != "GET" or has_flag(args, "--input")
                or (fields and not any(a == "--method" or a.startswith(("-X", "--method="))
                                       for a in args))):
            return WRITE
        return READ
    if group in ("search", "status", "browse", "help", "version", "completion"):
        return READ
    if group == "auth":
        return READ if sub in ("status", "token") else WRITE
    if sub in ("view", "list", "diff", "checks", "status", "watch", "trace", "lint", "ls",
               "get", "show", "verify"):
        return READ
    if sub in ("merge", "delete", "cancel", "rerun-failed", "lock", "unlock", "transfer"):
        return DANGER
    if sub == "note" and (pos[2:3] == ["list"] or pos[2:4] == ["draft", "list"]):
        return READ
    # Every MR verb but checkout lands on the shared MR where reviewers see it.
    if group in ("pr", "mr") and sub not in ("", "checkout"):
        return DANGER
    return WRITE


GLAB_LOCAL_GROUPS = {"auth", "config", "alias"}
GLAB_LOCAL_SUBS = {"checkout", "clone"}


def classify_glab(args):
    kind = classify_gh(args)
    rest, _ = split_globals(args, GH_GLOBAL_VALUE_FLAGS)
    group, sub = (positionals(rest) + ["", ""])[:2]
    local = group in GLAB_LOCAL_GROUPS or sub in GLAB_LOCAL_SUBS
    return DANGER if kind == WRITE and not local else kind


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
# "Some commands need my words AND the prompt, every time".
ON_WORDS = ("run it only when the user's message allowed this command in words, otherwise "
            "print it as `! <command>`")
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


def classify_claude(args):
    # A print-mode call is a model call that writes nothing only once both tool surfaces are
    # off: `--tools ""` removes the built-in tools and leaves the connectors, which the
    # disallow pattern removes. Anything else can edit files or post somewhere.
    if args[:2] in (["auth", "status"], ["plugin", "list"]) or args[:3] == ["plugin", "marketplace", "list"]:
        return READ
    if has_flag(args, "-p", "--print"):
        no_builtin = any(a == "--tools=" or (a == "--tools" and args[i + 1:i + 2] == [""])
                         for i, a in enumerate(args))
        no_mcp = any(a in ("--disallowedTools", "--disallowed-tools") and args[i + 1:i + 2] == ["mcp__*"]
                     for i, a in enumerate(args))
        if no_builtin and no_mcp:
            return READ
    return WRITE


def pushes_image(args):
    pos = positionals(args)
    if pos[:1] == ["push"] or pos[:2] in (["image", "push"], ["manifest", "push"],
                                         ["compose", "push"]):
        return True
    if pos[:3] == ["buildx", "imagetools", "create"]:
        return not has_flag(args, "--dry-run")
    builds = pos[:1] == ["build"] or pos[:2] in (["buildx", "build"], ["buildx", "bake"])
    return builds and (has_flag(args, "--push")
                       or any("type=registry" in a or "push=true" in a for a in args))


def skopeo_pushes(args):
    pos = positionals(args)
    if pos[:1] == ["copy"]:
        return pos[-1].startswith("docker://")
    if pos[:1] == ["sync"]:
        dest = next((a.split("=", 1)[1] for a in args if a.startswith("--dest=")), None)
        if dest is None and "--dest" in args[:-1]:
            dest = args[args.index("--dest") + 1]
        return dest == "docker"
    return False


def classify_skopeo(args):
    pos = positionals(args)
    if skopeo_pushes(args) or pos[:1] == ["delete"]:
        return DANGER
    if pos[:1] in (["inspect"], ["list-tags"]):
        return READ
    return WRITE


def classify_docker(args):
    pos = positionals(args)
    if not pos:
        return READ
    if pushes_image(args):
        return DANGER
    sub = pos[0]
    if sub in {"ps", "images", "inspect", "logs", "version", "info", "stats", "top", "diff",
               "history", "port", "search", "events", "wait"}:
        return READ
    if sub in ("rm", "rmi", "prune", "kill"):
        return DANGER
    if sub in {"image", "container", "volume", "network", "buildx", "compose", "manifest",
               "context", "system", "service", "node", "stack", "plugin"}:
        nested = pos[1] if len(pos) > 1 else ""
        if nested in ("ls", "list", "inspect", "logs", "history", "ps", "config", "version",
                      "df", "top", "events", "port"):
            return READ
        if nested in ("rm", "rmi", "prune", "kill", "down"):
            return DANGER
    return WRITE


SED_WRITE_RE = re.compile(r"(^|[;{}\s\d$/])w\s|/w\s")


def classify_sed(args):
    if any(re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in args):
        return WRITE
    return WRITE if any(SED_WRITE_RE.search(a) for a in args if not a.startswith("-")) else READ


def classify_awk(args):
    if has_flag(args, "-i", "--in-place") or any(a.startswith("-i") for a in args):
        return WRITE
    program = next((a for a in args if not a.startswith("-") and (" " in a or "{" in a)), "")
    if re.search(r'>\s*["$]|\|\s*"|system\s*\(|close\s*\(', program):
        return WRITE
    return READ


def classify_python(args):
    if not args or args in (["--version"], ["-V"]):
        return READ
    # GOTCHA: this script's own CLI only classifies text, and CLAUDE.md tells the model to run it.
    if os.path.realpath(os.path.expanduser(args[0])) == os.path.realpath(__file__):
        return READ
    if args[0] == "-m" and len(args) > 1:
        if args[1] in ("json.tool", "unittest", "tomllib"):
            return READ
        if args[1] in ("pytest", "mypy", "pyright", "ruff", "black", "isort", "flake8", "pylint"):
            return classify_program(args[1], args[2:])
        if args[1] == "pip":
            return classify_pip(args[2:])
        return WRITE
    if os.path.basename(args[0]) in PUBLISHING_SCRIPTS:
        return DANGER
    if os.path.basename(args[0]) == "board.py":
        return classify_board(args[1:])
    return WRITE


def classify_board(args):
    """The grafana-dashboards skill's board.py: fetch and diff read the live board, publish
    writes its next version, login saves a browser session locally."""
    pos = positionals(args)
    sub = pos[0] if pos else ""
    if sub == "diff":
        return READ
    if sub == "fetch":
        out = next((a.split("=", 1)[1] for a in args if a.startswith("--out=")), None)
        if out is None and "--out" in args[:-1]:
            out = args[args.index("--out") + 1]
        return READ if out is None or inside_scratch(out) else WRITE
    if sub == "publish":
        return DANGER
    return WRITE


def classify_pip(args):
    pos = positionals(args)
    if has_flag(args, "--version", "-V") or (pos and pos[0] in ("list", "show", "freeze", "check",
                                                                 "index", "debug", "config",
                                                                 "download", "hash", "inspect")):
        return READ
    return WRITE


def uv_run_tail(args):
    """The command `uv run` runs, with uv's own options removed."""
    tail = list(args)
    tail = tail[tail.index("run") + 1:]
    while tail and tail[0].startswith("-"):
        tail = tail[2:] if tail[0] in ("--with", "--python", "-p", "--package",
                                      "--directory", "--project", "--extra") else tail[1:]
    return tail


def classify_uv(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-V"):
        return READ
    sub = pos[0]
    if sub == "run":
        tail = uv_run_tail(args)
        return classify_words(tail) if tail else WRITE
    if sub == "pip":
        return classify_pip(args[args.index("pip") + 1:])
    if sub in ("tree", "version", "help", "self") or (sub == "lock" and has_flag(args, "--check")):
        return READ
    return WRITE


def classify_formatter(args):
    return READ if has_flag(args, "--check", "--diff", "-l", "--list-different") else WRITE


def classify_ruff(args):
    pos = positionals(args)
    if pos and pos[0] == "check":
        return WRITE if has_flag(args, "--fix", "--unsafe-fixes") else READ
    if pos and pos[0] == "format":
        return classify_formatter(args)
    return READ if pos and pos[0] in ("version", "rule", "linter", "config") else WRITE


def classify_npm(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-v"):
        return READ
    sub = pos[0]
    if sub in ("test", "t", "ls", "list", "view", "info", "outdated", "why", "explain", "ping",
               "doctor", "search", "config"):
        return WRITE if sub == "config" and len(pos) > 1 and pos[1] != "get" else READ
    if sub == "audit":
        return WRITE if "fix" in pos else READ
    if sub in ("run", "run-script") and len(pos) > 1:
        return READ if pos[1] in ("test", "lint", "typecheck", "type-check", "check") else WRITE
    if sub in ("publish", "unpublish", "deprecate"):
        return DANGER
    return WRITE


def classify_npx(args):
    pos = positionals(args)
    if pos and pos[0] == "tsc":
        return READ if has_flag(args, "--noEmit") else WRITE
    return WRITE


def classify_go(args):
    pos = positionals(args)
    if not pos:
        return READ
    sub = pos[0]
    if sub in ("test", "vet", "list", "env", "version", "doc", "help", "bug"):
        return READ
    if sub == "mod":
        return READ if len(pos) > 1 and pos[1] in ("graph", "why", "verify") else WRITE
    return WRITE


def classify_cargo(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-V"):
        return READ
    sub = pos[0]
    if sub in ("check", "test", "clippy", "tree", "metadata", "doc", "version", "search",
               "verify-project", "pkgid", "locate-project", "read-manifest", "bench"):
        return READ
    if sub == "fmt":
        return classify_formatter(args)
    if sub in ("publish", "yank", "owner"):
        return DANGER
    return WRITE


def classify_make(args):
    if has_flag(args, "-n", "--dry-run", "--just-print", "-q", "--question",
                "-p", "--print-data-base"):
        return READ
    targets = [a for a in positionals(args) if "=" not in a]
    return READ if targets == ["test"] else WRITE


def classify_terraform(args):
    pos = positionals(args)
    if not pos:
        return READ
    sub = pos[0]
    nested = pos[1] if len(pos) > 1 else ""
    if sub in ("plan", "show", "validate", "output", "providers", "version", "graph", "console",
               "get", "test"):
        return READ
    if sub == "fmt":
        return classify_formatter(args)
    if sub == "state":
        return READ if nested in ("list", "show", "pull") else DANGER
    if sub == "workspace":
        return READ if nested in ("list", "show") else WRITE
    if sub in ("apply", "destroy", "import", "taint", "untaint", "force-unlock"):
        return DANGER
    return WRITE


def classify_brew(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-v"):
        return READ
    if pos[0] in ("list", "ls", "info", "search", "outdated", "deps", "doctor", "config",
                  "leaves", "uses", "home", "desc", "options", "tap-info", "--prefix",
                  "--cellar", "--repository", "commands", "help", "log", "missing", "which"):
        return READ
    return WRITE


def classify_tmux(args):
    pos = positionals(args)
    if not pos:
        return WRITE
    return READ if pos[0] in ("ls", "list-sessions", "list-windows", "list-panes", "display",
                              "display-message", "show", "show-options", "show-environment",
                              "capture-pane", "has-session", "info", "list-keys", "list-commands",
                              "list-buffers", "show-buffer") else WRITE


def classify_rsync(args):
    if has_flag(args, "-n", "--dry-run") or any(re.match(r"^-[a-zA-Z]*n", a) for a in args):
        return READ
    return DANGER if any(a.startswith("--delete") for a in args) else WRITE


def classify_tar(args):
    if has_flag(args, "--list", "-t") or tar_extracts_to_stdout(args):
        return READ
    first = args[0] if args else ""
    cluster = first.lstrip("-")
    if first and re.match(r"^-?[a-zA-Z]+$", first) and "t" in cluster and not ({"x", "c", "r", "u"} & set(cluster)):
        return READ
    return WRITE


def tar_extracts_to_stdout(args):
    """True when tar only extracts, and -O / --to-stdout sends every member to stdout."""
    extract = stdout = False
    for i, arg in enumerate(args):
        if arg.startswith("--"):
            name = arg.partition("=")[0]
            if name not in TAR_STDOUT_LONG:
                return False
            extract = extract or name in ("--extract", "--get")
            stdout = stdout or name == "--to-stdout"
        elif arg.startswith("-") or i == 0:
            if not set(arg.lstrip("-")) <= TAR_STDOUT_SHORT:
                return False
            extract = extract or "x" in arg
            stdout = stdout or "O" in arg
    return extract and stdout


def classify_unzip(args):
    return READ if has_flag(args, "-l", "-t", "-Z", "-p", "-z") else WRITE


def classify_gzip(args):
    if has_flag(args, "-l", "--list", "-t", "--test", "-c", "--stdout", "--to-stdout"):
        return READ
    if any(re.match(r"^-[a-zA-Z0-9]*[ltc]", a) for a in args):
        return READ
    return WRITE


def classify_chmod(args):
    return DANGER if has_flag(args, "-R", "--recursive") or any(re.match(r"^-[a-zA-Z]*R", a) for a in args) else WRITE


def classify_sort(args):
    return WRITE if has_flag(args, "-o", "--output") or any(a.startswith("--output=") for a in args) else READ


def find_exec_words(args):
    for i, a in enumerate(args):
        if a in ("-exec", "-execdir", "-ok", "-okdir"):
            sub = args[i + 1:]
            end = next((j for j, w in enumerate(sub) if w in (";", "+")), len(sub))
            return sub[:end]
    return None


def classify_find(args):
    if "-delete" in args:
        return DANGER
    if has_flag(args, "-fprint", "-fprint0", "-fprintf", "-fls"):
        return WRITE
    sub = find_exec_words(args)
    return classify_words(sub) if sub is not None else READ


def xargs_rest(args):
    rest = list(args)
    while rest and rest[0].startswith("-"):
        takes_value = rest[0] in ("-n", "-P", "-L", "-I", "-d", "-s", "-E", "-a", "-J")
        rest = rest[2:] if takes_value and len(rest[0]) == 2 else rest[1:]
    return rest


def classify_xargs(args):
    rest = xargs_rest(args)
    return classify_words(rest) if rest else READ


def shell_body(args):
    if has_flag(args, "--version", "-n"):
        return None
    for i, a in enumerate(args):
        if (a == "-c" or re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", a)) and i + 1 < len(args):
            return args[i + 1]
    return None


def classify_shell(args):
    if has_flag(args, "--version", "-n"):
        return READ
    body = shell_body(args)
    return classify_command(body) if body is not None else WRITE


def classify_yq(args):
    return WRITE if has_flag(args, "-i", "--inplace") else READ


def classify_launchctl(args):
    pos = positionals(args)
    return READ if pos and pos[0] in ("list", "print", "print-disabled", "blame", "dumpstate",
                                      "getenv", "version", "help", "error") else WRITE


def classify_systemctl(args):
    pos = positionals(args)
    if not pos or pos[0] in ("status", "show", "cat", "list-units", "list-unit-files",
                            "list-timers", "list-sockets", "list-dependencies", "is-active",
                            "is-enabled", "is-failed", "is-system-running", "get-default",
                            "show-environment"):
        return READ
    return DANGER if pos[0] in ("stop", "restart", "disable", "mask", "kill", "poweroff",
                                "reboot", "halt", "isolate") else WRITE


def classify_nc(args):
    return READ if has_flag(args, "-z") or any(re.match(r"^-[a-zA-Z]*z", a) for a in args) else WRITE


def classify_amtool(args):
    pos = set(positionals(args))
    if pos & {"add", "expire", "import", "update"}:
        return WRITE
    return READ


def classify_promtool(args):
    return WRITE if "create-blocks-from" in args else READ


def classify_openssl(args):
    pos = positionals(args)
    if pos and pos[0] in ("x509", "s_client", "dgst", "verify", "version", "asn1parse", "rand",
                          "pkey", "rsa", "ec", "crl", "ciphers", "list", "prime", "req",
                          "pkcs12", "enc") and not has_flag(args, "-out"):
        return READ if pos[0] not in ("req", "pkcs12", "enc") or has_flag(args, "-text", "-noout", "-d", "-info") else WRITE
    return WRITE


def classify_op(args):
    pos = set(positionals(args))
    if pos & {"create", "edit", "delete", "move", "share", "signin", "signout", "inject", "run"}:
        return WRITE
    return READ if pos & {"read", "get", "list", "whoami", "ls"} else WRITE


def classify_defaults(args):
    pos = positionals(args)
    return READ if pos and pos[0] in ("read", "read-type", "domains", "find", "export") else WRITE


def classify_crontab(args):
    return READ if has_flag(args, "-l") else WRITE


def classify_sysctl(args):
    return WRITE if has_flag(args, "-w", "--write") or any("=" in a for a in positionals(args)) else READ


def classify_nvidia_smi(args):
    return WRITE if has_flag(args, "-r", "--gpu-reset", "-pm", "-pl", "-ac", "-rac", "-c", "-e",
                             "-mig", "-lgc", "-rgc", "-lmc", "-rmc", "--applications-clocks",
                             "--power-limit", "--persistence-mode", "--compute-mode") else READ


def classify_wget(args):
    if "--spider" in args:
        return READ
    for i, a in enumerate(args):
        if re.match(r"^-[a-zA-Z]*O-$", a) or a == "--output-document=-":
            return READ
        if re.match(r"^-[a-zA-Z]*O$", a) and i + 1 < len(args) and args[i + 1] == "-":
            return READ
    return WRITE


def classify_stern(_):
    return READ


HANDLERS = {
    "git": classify_git, "git-lfs": lambda args: classify_git(["lfs", *args]),
    "kubectl": classify_kubectl, "k": classify_kubectl, "oc": classify_kubectl,
    "helm": classify_helm,
    "helmfile": classify_helmfile,
    "stern": classify_stern,
    "curl": classify_curl, "http": classify_xh, "https": classify_xh, "xh": classify_xh,
    "wget": classify_wget,
    "gh": classify_gh, "glab": classify_glab,
    "claude": classify_claude,
    "docker": classify_docker, "podman": classify_docker, "nerdctl": classify_docker,
    "buildah": classify_docker,
    "skopeo": classify_skopeo,
    "gcloud": generic_verbs, "crusoe": generic_verbs, "aws": generic_verbs, "az": generic_verbs,
    "argocd": generic_verbs, "flux": generic_verbs, "tsh": generic_verbs, "vault": generic_verbs,
    "tailscale": generic_verbs, "velero": generic_verbs, "istioctl": generic_verbs,
    "cilium": generic_verbs, "linkerd": generic_verbs, "gsutil": generic_verbs,
    "sed": classify_sed, "gsed": classify_sed,
    "awk": classify_awk, "gawk": classify_awk, "mawk": classify_awk, "nawk": classify_awk,
    "python": classify_python, "python3": classify_python,
    "pip": classify_pip, "pip3": classify_pip,
    "uv": classify_uv,
    "ruff": classify_ruff, "black": classify_formatter, "isort": classify_formatter,
    "prettier": classify_formatter, "terraform-fmt": classify_formatter,
    "npm": classify_npm, "pnpm": classify_npm, "yarn": classify_npm,
    "npx": classify_npx, "bunx": classify_npx,
    "go": classify_go,
    "cargo": classify_cargo,
    "make": classify_make, "gmake": classify_make,
    "terraform": classify_terraform, "tofu": classify_terraform,
    "brew": classify_brew,
    "tmux": classify_tmux,
    "rsync": classify_rsync,
    "tar": classify_tar,
    "unzip": classify_unzip,
    "gzip": classify_gzip, "gunzip": classify_gzip, "bzip2": classify_gzip, "xz": classify_gzip,
    "chmod": classify_chmod, "chown": classify_chmod, "chgrp": classify_chmod,
    "sort": classify_sort,
    "find": classify_find,
    "xargs": classify_xargs,
    "bash": classify_shell, "sh": classify_shell, "zsh": classify_shell, "dash": classify_shell,
    "yq": classify_yq,
    "launchctl": classify_launchctl,
    "systemctl": classify_systemctl,
    "nc": classify_nc, "ncat": classify_nc,
    "amtool": classify_amtool,
    "promtool": classify_promtool,
    "openssl": classify_openssl,
    "op": classify_op,
    "defaults": classify_defaults,
    "crontab": classify_crontab,
    "sysctl": classify_sysctl,
    "nvidia-smi": classify_nvidia_smi,
}

_unknown_level = WRITE


@contextlib.contextmanager
def unknown_programs_as(level):
    """Re-classify with unknown programs at `level`: the gate asks, instead of denying, when a
    command is WRITE only because of programs the classifier has never met."""
    global _unknown_level
    previous, _unknown_level = _unknown_level, level
    try:
        yield
    finally:
        _unknown_level = previous


# Programs that hand their arguments to another command, so a trailing `--help` is that
# command's argument and asks for no help at all.
RUNNERS = {"bash", "sh", "zsh", "dash", "python", "python3", "node", "perl", "ruby", "deno",
           "bun", "uv", "uvx", "npx", "bunx", "xargs", "find", "env", "make", "gmake"}


def help_only(prog, args):
    return (args in (["-h"], ["--help"], ["--version"], ["-V"])
            or (args[-1:] == ["--help"] and "--" not in args and prog not in RUNNERS))


def classify_program(prog, args):
    if help_only(prog, args) or args in (["version"], ["help"]):
        return READ
    if prog in DANGER_PROGRAMS or prog in PUBLISHING_SCRIPTS:
        return DANGER
    if prog in HANDLERS:
        return HANDLERS[prog](args)
    if prog in READ_PROGRAMS:
        return READ
    if prog in WRITE_PROGRAMS:
        return WRITE
    return _unknown_level


def strip_prefix(words):
    """Drop env assignments, transparent wrappers and `timeout <args>` ahead of the program."""
    words = list(words)
    # GOTCHA: shlex leaves a bare `$` behind when nested quotes split `$(...)` apart.
    while words and (ENV_ASSIGN_RE.match(words[0]) or words[0] in TRANSPARENT or words[0] == "$"):
        words = words[1:]
    if words and words[0] == "timeout":
        words = words[1:]
        while words and (words[0].startswith("-") or re.match(r"^\d+[smhd]?$", words[0])):
            words = words[1:]
    while words and words[0] in SYNTAX_ONLY:
        words = words[1:]
    return words


def program_of(words):
    return words[0].rsplit("/", 1)[-1]


def classify_words(words):
    words = strip_prefix(words)
    if not words:
        return READ
    prog = program_of(words)
    if prog in LOOP_HEADERS:
        return READ
    return classify_program(prog, words[1:])


def worst(*levels):
    return max(levels, key=lambda level: RANK[level])


def split_line(line):
    """Split one shell line into its command segments and its output-redirect targets."""
    segments, targets, _ = parse_line(line)
    return segments, targets


def parse_line(line):
    """split_line's segments and targets, and for each segment whether it runs apart from
    the line's shell: inside parentheses or a substitution, in a pipeline or in the
    background, where the shell may give it a process of its own."""
    lexer = shlex.shlex(DESCRIPTOR_RE.sub("", line), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    segments, targets, apart, segment = [], [], [], []
    # One entry per open `(`: the command a `$(` interrupts, resumed at its `)` so text
    # glued after the `)` stays that command's argument, or None for a subshell or a
    # process substitution, whose `)` ends a segment like any separator. shlex splits
    # `$(` into a token ending in `$` and a `(`.
    opened = []
    piped = False
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(" and segment and segment[-1].endswith("$"):
            opened.append(segment)
            segment = []
        elif tok == ")" and opened and opened[-1] is not None:
            if segment:
                segments.append(segment)
                apart.append(True)
            segment = opened.pop()
        elif tok in SEPARATORS:
            if segment:
                segments.append(segment)
                apart.append(bool(opened) or piped or tok in ("|", "|&", "&"))
            if tok == "(":
                opened.append(None)
            elif tok == ")" and opened:
                opened.pop()
            piped = tok in ("|", "|&")
            segment = []
        elif tok in ("<(", ">("):
            # Process substitution runs a command of its own; `)` closes it like a subshell.
            if segment:
                segments.append(segment)
                apart.append(bool(opened) or piped)
            opened.append(None)
            segment = []
        elif tok in REDIRECT_OUT or tok in (">&", "<", "<<", "<<<", "<&", "<>"):
            if tok in REDIRECT_OUT:
                targets.append(tokens[i + 1] if i + 1 < len(tokens) else "")
            i += 1
        elif tok.startswith(">") or tok.startswith("<"):
            pass
        else:
            segment.append(tok)
        i += 1
    if segment:
        segments.append(segment)
        apart.append(bool(opened) or piped)
    # GOTCHA: an escaped backtick opens a `$(` that never closes; the command it
    # interrupted still runs, so it is still a segment.
    for held in opened:
        if held:
            segments.append(held)
            apart.append(True)
    return segments, targets, apart


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


def classify_line(line):
    segments, targets = split_line(line)
    level = WRITE if any(t not in HARMLESS_TARGETS for t in targets) else READ
    for segment in segments:
        level = worst(level, classify_words(segment))
    return level


def command_lines(command):
    # A backtick pair is a substitution: turned into `$(...)`, its commands run apart.
    text = without_heredoc_bodies(command).split("`")
    text = "".join(part + ("$(" if n % 2 == 0 else ")") for n, part in enumerate(text[:-1])) \
        + text[-1]
    for line in text.splitlines():
        if line.strip() and not line.strip().startswith("#"):
            yield line


def classify_command(command):
    level = READ
    for line in command_lines(command):
        try:
            line_level = classify_line(line)
        except ValueError:
            line_level = WRITE
        level = worst(level, line_level)
    return level


def rm_paths(args):
    if "--" in args:
        end = args.index("--")
        return positionals(args[:end]) + args[end + 1:]
    return positionals(args)


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


TOP_LEVEL_SEPARATORS = ("&&", "||", ";", "|", "&", "\n")
RM_SEGMENT_RE = re.compile(r"^\s*rm\s+(.*\S)\s*$")
BLOCK_WORDS = {"if", "then", "elif", "else", "fi", "for", "while", "until", "do", "done",
               "case", "esac", "in", "select", "function", "{", "}"}
REDIRECT_WORD_RE = re.compile(r"^\d*>{1,2}&?\S*$")
# Anything the shell would expand into a path this script cannot see: variables, command
# substitution, the home directory, brace expansion.
UNRESOLVABLE_CHARS = set("$`~{")


def top_level_segments(command, bodies=None):
    """The command's top-level segments as (start, end) spans, and the separator after each.

    Quoted text, subshells and substitutions are opaque: a separator inside them splits
    nothing, so an `rm` inside a quoted argument or a `$(...)` is never a segment of its
    own. The last segment has no separator after it. When `bodies` is a list, the span
    of every heredoc body, terminator line included, is appended to it.
    """
    spans, seps = [], []
    start = i = 0
    quote, depth = None, 0
    heredocs = []
    while i < len(command):
        c = command[i]
        if quote:
            if c == "\\" and quote == '"':
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c == "\\":
            i += 2
            continue
        if c in "'\"`":
            quote = c
            i += 1
            continue
        if command.startswith("$(", i):
            depth += 1
            i += 2
            continue
        if c == "(":
            depth += 1
            i += 1
            continue
        if c == ")":
            depth = max(depth - 1, 0)
            i += 1
            continue
        if command.startswith("<<<", i):
            i += 3
            continue
        if command.startswith("<<", i):
            delimiter, i = heredoc_delimiter(command, i + 2)
            heredocs.append(delimiter)
            continue
        if depth == 0:
            sep = next((s for s in TOP_LEVEL_SEPARATORS if command.startswith(s, i)), None)
            # GOTCHA: the `&` of `2>&1`, `<&` and `&>` is a redirect, not a background job.
            if sep == "&" and ((i > 0 and command[i - 1] in "<>") or command.startswith("&>", i)):
                sep = None
            if sep == "\n" and heredocs:
                # The bodies are data for the command that opened them: the segment runs on
                # through them, and the newline after the last terminator is the split.
                end = heredoc_bodies_end(command, i + 1, heredocs)
                if bodies is not None:
                    bodies.append((i + 1, end))
                i = end
                heredocs = []
                continue
            if sep:
                spans.append((start, i))
                seps.append(sep)
                i += len(sep)
                start = i
                continue
        i += 1
    spans.append((start, len(command)))
    seps.append("")
    return spans, seps


def heredoc_delimiter(command, i):
    """The delimiter word after a `<<`, unquoted, and the index just past it."""
    if command.startswith("-", i):
        i += 1
    while i < len(command) and command[i] in " \t":
        i += 1
    if i < len(command) and command[i] in "'\"":
        end = command.find(command[i], i + 1)
        end = len(command) if end < 0 else end
        return command[i + 1:end], end + 1
    end = i
    while end < len(command) and command[end] not in " \t\n;&|()<>":
        end += 1
    return command[i:end], end


def without_heredoc_bodies(command):
    """The command with every heredoc body cut out, so a body line never reads as a program."""
    bodies = []
    top_level_segments(command, bodies)
    for start, end in reversed(bodies):
        command = command[:start] + command[end:]
    return command


def heredoc_bodies_end(command, i, delimiters):
    """The index of the newline after the last terminator line, or the end of the command."""
    for delimiter in delimiters:
        while i < len(command):
            end = command.find("\n", i)
            end = len(command) if end < 0 else end
            line = command[i:end]
            i = end + 1
            if line.lstrip("\t") == delimiter:
                break
    return min(i - 1, len(command))


def first_word(text):
    match = re.match(r"\s*(\S+)", text)
    return match.group(1) if match else ""


def scratch_rm_args(args_text):
    """True when `rm <args_text>` names only literal paths inside the session scratch root."""
    if UNRESOLVABLE_CHARS & set(args_text):
        return False
    try:
        words = shlex.split(args_text, comments=True)
    except ValueError:
        return False
    paths = rm_paths([w for w in words if not REDIRECT_WORD_RE.match(w)])
    return bool(paths) and all(inside_scratch(p) for p in paths)


def strip_scratch_rm(command):
    """The command without its scratch-only `rm` segments, and how many were dropped.

    A command that is nothing but scratch cleanup is returned unchanged: the prompt is
    the lesser surprise next to a Bash call that runs nothing.
    """
    spans, seps = top_level_segments(command)
    # parts alternates segment text and the separator after it; a dropped piece is None.
    parts = []
    for (a, b), sep in zip(spans, seps):
        parts.extend((command[a:b], sep))
    dropped = 0
    for k, (a, b) in enumerate(spans):
        match = RM_SEGMENT_RE.match(command[a:b])
        before = seps[k - 1] if k else ""
        after = seps[k]
        # A piped rm, a backgrounded one, or one whose failure branch would fall to the
        # previous command, is not cleanup to drop.
        if not match or before in ("|", "&") or after in ("|", "||", "&"):
            continue
        # GOTCHA: a block needs a body, so `then rm ...; fi` with the rm gone is a syntax
        # error. An rm next to a block keyword stays.
        neighbours = (command[slice(*spans[j])] for j in (k - 1, k + 1) if 0 <= j < len(spans))
        if any(first_word(text) in BLOCK_WORDS for text in neighbours):
            continue
        if not scratch_rm_args(match.group(1)):
            continue
        dropped += 1
        # Take the separator before the rm when one is still there, else the one after,
        # so a chain of dropped segments never leaves a dangling `&&`.
        if before in (";", "&&", "||") and parts[2 * k - 1] is not None:
            parts[2 * k - 1] = parts[2 * k] = None
            if parts[2 * k - 2] is not None:
                parts[2 * k - 2] = parts[2 * k - 2].rstrip(" \t")
        else:
            parts[2 * k] = parts[2 * k + 1] = None
            if 2 * k + 2 < len(parts) and parts[2 * k + 2] is not None:
                parts[2 * k + 2] = parts[2 * k + 2].lstrip(" \t")
    stripped = "".join(p for p in parts if p is not None).rstrip("\n \t")
    if not dropped or not stripped:
        return command, 0
    return stripped, dropped


def stripped_bash_input(tool_input):
    """The Bash tool input with scratch-only `rm` segments dropped, and how many were."""
    command, dropped = strip_scratch_rm(tool_input["command"])
    return dict(tool_input, command=command), dropped


# ----- gate decisions -----------------------------------------------------------------

def inside_gate_scratch(path):
    if not isinstance(path, str) or not os.path.isabs(path):
        return False
    real = os.path.realpath(path)
    return real.startswith(GATE_SCRATCH_ROOTS) or bool(MEMORY_ROOT_RE.match(real))


def expand_home(word):
    return os.path.expanduser(word) if word == "~" or word.startswith("~/") else word


def invocations(command):
    """Every program invocation in a command, nested ones included, as (program, args)."""
    for prog, args, _ in invocations_with_moves(command):
        yield prog, args


def invocations_with_moves(command):
    """invocations(command), each with whether it is a `cd` that moves the rest of the
    command: a nested one, run by `bash -c`, `xargs` or `find -exec`, never does."""
    for line in command_lines(command):
        try:
            segments, _, apart = parse_line(line)
        except ValueError:
            continue
        for segment, sticks in zip(segments, cd_sticks(segments, apart)):
            for n, (prog, args) in enumerate(invocations_in(segment)):
                yield prog, args, sticks and n == 0


def invocations_in(words):
    words = strip_prefix(words)
    if not words:
        return
    prog = program_of(words)
    if prog in LOOP_HEADERS:
        return
    args = words[1:]
    yield prog, args
    if prog in ("bash", "sh", "zsh", "dash"):
        body = shell_body(args)
        if body is not None:
            yield from invocations(body)
    elif prog == "xargs":
        rest = xargs_rest(args)
        if rest:
            yield from invocations_in(rest)
    elif prog == "find":
        sub = find_exec_words(args)
        if sub:
            yield from invocations_in(sub)


PYTHON_RE = re.compile(r"python(?:3(?:\.\d+)?)?")
INTERPRETERS = {"node", "deno", "bun", "npx", "bunx"}
KNOWN_PYTHON_SCRIPTS = {"board.py"} | PUBLISHING_SCRIPTS
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
        return not (args and os.path.basename(args[0]) in KNOWN_PYTHON_SCRIPTS)
    if prog in INTERPRETERS:
        return True
    if prog == "uv":
        return pos[:1] == ["run"]
    if prog in ("go", "cargo"):
        return pos[:1] == ["run"]
    if prog in CONTAINER_ENGINES:
        return pos[:1] == ["run"] or pos[:2] == ["container", "run"]
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


def passes_gate(command, cwd):
    """True when nothing in the command changes a repo by a route its text shows.

    A read, a command that needs the user's words, opaque code, a write that lands in a
    gate scratch root and git run in one all pass; any other write is held to scratch, as
    the gate held every write before it narrowed to repos. The working directory follows
    every `cd`, as for commits, and is unknown after one that may not stick.
    """
    here = cwd
    for line in command_lines(command):
        try:
            segments, targets, apart = parse_line(line)
        except ValueError:
            return False
        sticks = cd_sticks(segments, apart)
        if not NO_HOME_EXPANSION_RE.search(command):
            segments = [[expand_home(w) for w in segment] for segment in segments]
            targets = [expand_home(t) for t in targets]
        if any(t not in HARMLESS_TARGETS and not inside_gate_scratch(t) for t in targets):
            return False
        for words, moves in zip(segments, sticks):
            words = strip_prefix(words)
            if not words or program_of(words) in LOOP_HEADERS:
                continue
            prog, args = program_of(words), words[1:]
            if prog in CHDIR_PROGRAMS:
                here = cd_target(here, prog, args) if moves else None
                continue
            if classify_program(prog, args) == READ:
                continue
            # A command that needs the user's words is the words rule's, never the gate's.
            if any(decision == ASK for decision, _ in pin_decisions(prog, args)):
                continue
            if runs_opaque_code(words):
                continue
            if prog == "git":
                target = git_target_dir(here, args)
                # The directory itself may be a scratch root, so it counts as inside one.
                if target is not None and (os.path.realpath(target) + "/").startswith(
                        GATE_SCRATCH_ROOTS):
                    continue
                # Only an absolute -o is trusted: git resolves a relative one against a
                # directory that -C and its own setup decide, not the text.
                outputs = git_archive_outputs(args)
                if outputs and all(inside_gate_scratch(o) for o in outputs):
                    continue
                return False
            if prog in SCRATCH_WRITERS:
                paths = rm_paths(args) if prog == "rm" else positionals(args)
                if paths and all(inside_gate_scratch(path_from(here, p)) for p in paths):
                    continue
            if prog == "tar" and tar_extracts_into_scratch(here, args):
                continue
            return False
    return True


def path_from(here, path):
    """path as a command run in here opens it, or None when only the shell knows."""
    if os.path.isabs(path):
        return path
    if here is None or SHELL_EXPANSION_CHARS & set(path):
        return None
    return os.path.join(here, path)


def inside_repo(path):
    """True when path lies in a git work tree outside the gate scratch roots."""
    if not isinstance(path, str) or not os.path.isabs(path) or inside_gate_scratch(path):
        return False
    here = os.path.dirname(os.path.realpath(path))
    while True:
        if os.path.exists(os.path.join(here, ".git")):
            return True
        parent = os.path.dirname(here)
        if parent == here:
            return False
        here = parent


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


def only_unknown_writes(command):
    with unknown_programs_as(READ):
        return classify_command(command) == READ


def pin_decisions(prog, args):
    """The rows that apply in every gate state, for one program invocation."""
    out = []
    if help_only(prog, args):
        return out
    if ((HANDLERS.get(prog) is classify_docker and pushes_image(args))
            or (prog == "skopeo" and skopeo_pushes(args))):
        out.append((ASK, "pushes an image to a registry, where a moved tag reaches every "
                         f"deployment that pulls it: {ON_WORDS}"))
    elif prog == "glab" and creates_remote_tag(args):
        out.append((ASK, "creates a tag or release on the remote, which can start its release "
                         f"pipeline: {ON_WORDS}"))
    elif prog in PUBLISHING_SCRIPTS or (prog in ("python", "python3", "uv") and any(
            os.path.basename(a) in PUBLISHING_SCRIPTS for a in positionals(args))):
        out.append((ASK, "runs a script that pushes images and moves shared registry tags: "
                         f"{ON_WORDS}"))
    if pushes_branch(prog, args):
        out.append((DENY, PUSH_REASON))
    if moves_mr(prog, args):
        out.append((ASK, MR_MOVE_REASON))
    url = remote_http_write(prog, args)
    if url:
        out.append((ASK, f"an HTTP write to {url} changes state on a remote server: "
                         f"{ON_WORDS}"))
    if prog in ("kubectx", "kubens"):
        out.append((ASK, f"{CONTEXT_SETTER_REASON}: {ON_WORDS}"))
    elif prog in ("kubectl", "k", "oc", "stern"):
        rest, seen = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
        verb = pos[0] if pos else ""
        sub = pos[1] if len(pos) > 1 else ""
        if prog != "stern":
            if verb == "config" and sub in KUBECTL_CONTEXT_SETTERS:
                out.append((ASK, f"{CONTEXT_SETTER_REASON}: {ON_WORDS}"))
                return out
            if not pos or verb in KUBECTL_LOCAL or (verb == "version" and "--client" in rest):
                return out
            if "$" in verb:
                out.append((ASK, f"kubectl {RUNTIME_VERB_REASON}: {ON_WORDS}"))
            writes = (verb in KUBECTL_WRITES_WIDENED
                      or (verb in KUBECTL_WRITES_BY_CLAUDE_MD
                          and not (verb == "rollout" and sub in KUBECTL_ROLLOUT_READS)))
            if writes and not dry_run(rest):
                out.append((ASK, f"kubectl {verb} writes live cluster state: {ON_WORDS}"))
            elif writes_inside_pod(verb, rest):
                out.append((ASK, f"kubectl {verb} changes what runs or is stored inside a pod: "
                                 f"{ON_WORDS}"))
        if not seen.get("--context"):
            out.append((DENY, "pin the context: every cluster command carries --context <ctx>"))
        namespace_free = (prog != "stern" and ((verb, sub) in NAMESPACE_FREE
                                               or verb in NODE_VERBS
                                               or (verb == "get" and has_flag(rest, "--raw"))))
        if not (seen.get("-n") or seen.get("--namespace") or seen.get("-A")) and not namespace_free:
            out.append((DENY, "pin the namespace: every cluster command carries -n <ns>, "
                              "or -A when a cluster-wide view is the point"))
    elif prog == "helm":
        rest, seen = split_globals(args, HELM_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
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
            out.append((ASK, "--reuse-values replays the previous values onto the new chart: "
                             f"{ON_WORDS}"))
        if not seen.get("--kube-context"):
            out.append((DENY, "pin the context: every helm command carries --kube-context <ctx>"))
        if not (seen.get("-n") or seen.get("--namespace") or seen.get("-A")):
            out.append((DENY, "pin the namespace: every helm command carries -n <ns>"))
    elif prog == "helmfile":
        rest, seen = split_globals(args, HELMFILE_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
        sub = pos[0] if pos else ""
        if "$" in sub:
            out.append((ASK, f"helmfile {RUNTIME_VERB_REASON}: {ON_WORDS}"))
        if sub in HELMFILE_RELEASE_WRITES:
            out.append((ASK, f"helmfile {sub} changes what runs on the cluster: {ON_WORDS}"))
        if (sub in HELMFILE_CLUSTER or "$" in sub) and not seen.get("--kube-context"):
            out.append((DENY, "pin the context: every helmfile command that reaches a cluster "
                              "carries --kube-context <ctx>"))
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
        return args[0] if args and not args[0].startswith("-") else None
    if prog == "uv" and positionals(args)[:1] == ["run"]:
        tail = uv_run_tail(args)
        if tail and tail[0].endswith(".py"):
            return tail[0]
        return script_of(tail) if tail else None
    return words[0] if "/" in words[0] else None


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


def script_decisions(command, cwd):
    """One ask per script the command runs whose text holds a command that needs words.

    The working directory follows every `cd` in the command, as for commits; a script
    whose path is built at run time cannot be read, so it is not scanned. A relative script
    run where the directory is unknown asks, since its text could hold anything.
    """
    out = []
    here = cwd
    for line in command_lines(command):
        try:
            segments, _, apart = parse_line(line)
        except ValueError:
            continue
        for segment, moves in zip(segments, cd_sticks(segments, apart)):
            words = strip_prefix(segment)
            if words and program_of(words) in CHDIR_PROGRAMS:
                here = cd_target(here, program_of(words), words[1:]) if moves else None
                continue
            script = script_of(words)
            if not script:
                continue
            path = resolved_dir(here, script)
            if here is None and path is None and "$" not in script:
                out.append((ASK, f"runs {script} from a directory known only at run time, so "
                                 "its text could not be checked for commands that change live "
                                 "or remote state"))
                continue
            # This script's own CLI only classifies text; its selftest holds every pattern.
            if path is None or os.path.realpath(path) == os.path.realpath(__file__):
                continue
            found = script_lines_needing_words(path)
            if found:
                shown = "; ".join(found[:5]) + ("; ..." if len(found) > 5 else "")
                out.append((ASK, f"runs {script}, whose text holds commands that change live "
                                 f"or remote state - {shown}. One prompt covers the whole "
                                 "run; no words needed"))
    return out


CARGO_VALUE_FLAGS = {"-p", "--package", "--features", "-F", "--target", "-j", "--jobs",
                     "--manifest-path", "--profile", "--test", "--bench", "--bin", "--example"}
SUITE_REASON = ("runs a whole test suite: ask before it starts, and run the tests the change "
                "touches unless the user asked for the suite")


def runs_whole_suite(prog, args):
    """True for a test runner with nothing narrowing it to a file, a test or a filter."""
    pos = positionals(args)
    if prog == "uv" and pos[:1] == ["run"]:
        tail = uv_run_tail(args)
        return bool(tail) and runs_whole_suite(program_of(tail), tail[1:])
    if PYTHON_RE.fullmatch(prog) and args[:2] == ["-m", "pytest"]:
        return runs_whole_suite("pytest", args[2:])
    if prog == "pytest":
        return not (has_flag(args, "-k") or any(".py" in a or "::" in a for a in pos))
    if prog == "go":
        return pos[:1] == ["test"] and any("..." in a for a in pos) and not has_flag(args, "-run")
    if prog == "cargo":
        rest, _ = split_globals(args, CARGO_VALUE_FLAGS)
        rest = rest[:rest.index("--")] if "--" in rest else rest
        return positionals(rest) == ["test"]
    if prog in ("make", "gmake"):
        return "test" in pos
    if prog in ("npm", "pnpm", "yarn"):
        return pos[:1] in (["test"], ["t"]) or pos[:2] == ["run", "test"]
    return False


def decide_bash(tool_input, gate_open, cwd):
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise ValueError("Bash call without a command string")
    out = []
    for prog, args in invocations(command):
        out.extend(pin_decisions(prog, args))
        if runs_whole_suite(prog, args):
            out.append((ASK, SUITE_REASON))
    out.extend(default_branch_commits(command, cwd))
    out.extend(script_decisions(command, cwd))
    if not gate_open and classify_command(command) != READ and not passes_gate(command, cwd):
        if only_unknown_writes(command):
            out.append((ASK, "unclassified - fix the handler in tool-gate.py"))
        else:
            out.append((DENY, REFUSAL))
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


def decide(tool_name, tool_input, gate_open, cwd=None):
    """The strictest decision over every matching row, as (decision, reason) or None.

    cwd is the directory the tool call runs in, which a Bash commit is judged against.
    """
    if tool_name == "Bash":
        out = decide_bash(tool_input, gate_open, cwd or os.getcwd())
    elif tool_name in PATH_FIELD:
        out = []
        if not gate_open and inside_repo(tool_input.get(PATH_FIELD[tool_name])):
            out.append((DENY, REFUSAL))
    elif tool_name == "EnterWorktree":
        out = [] if gate_open else [(DENY, REFUSAL)]
    elif tool_name.startswith("mcp__"):
        out = decide_mcp(tool_name, tool_input)
    else:
        out = []
    return max(out, key=lambda d: DECISION_RANK[d[0]]) if out else None


def gate_is_open(session_id):
    if not isinstance(session_id, str) or not session_id:
        return False
    try:
        with open(os.path.join(STATE_DIR, re.sub(r"[^A-Za-z0-9_.-]", "_", session_id))) as f:
            return f.read().strip() in OPEN_STATES
    except FileNotFoundError:
        return False


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
        if tool_name == "Bash" and isinstance(tool_input.get("command"), str):
            description = LABEL_RE.sub("", tool_input.get("description") or "").strip()
            tool_input, dropped = stripped_bash_input(tool_input)
            if dropped:
                description = f"{description} (scratch rm dropped)".strip()
            updated = dict(tool_input)
            rating = classify_command(tool_input["command"])
            updated["description"] = f"{rating} · {description}" if description else rating
            output["updatedInput"] = updated
        decision = decide(tool_name, tool_input, gate_is_open(payload.get("session_id")),
                          payload.get("cwd"))
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
    note = ""
    if tool_name == "Bash":
        tool_input, dropped = stripped_bash_input(tool_input)
        note = "  (scratch rm dropped)" if dropped else ""
    decision = decide(tool_name, tool_input, gate_open)
    gate_decision = f"{decision[0]}: {decision[1]}" if decision else "-"
    if tool_name == "Bash":
        return f"{classify_command(tool_input['command'])}  {gate_decision}{note}"
    return gate_decision


def selftest():
    global GATE_SCRATCH_ROOTS
    home = os.path.expanduser("~")
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
        (True, "Bash", "kubectl delete pod p -n Y", DENY),
        # An empty kubeconfig is no pin: inside a pod client-go falls back to its service account.
        (True, "Bash", "kubectl create secret generic t --kubeconfig=/dev/null --dry-run=client "
                       "-o yaml", DENY),
        # A verb built at run time could be any of the writes above.
        (True, "Bash", "kubectl $(echo delete) pod p --context X -n Y", ASK),
        (True, "Bash", 'kubectl "$(echo delete)" pod p --context X -n Y', ASK),
        (True, "Bash", "V=delete; kubectl $V pod p --context X -n Y", ASK),
        (True, "Bash", "helm $(echo uninstall) r --kube-context X -n Y", ASK),
        (True, "Bash", "kubectl get pods -l app=$(echo x) --context X -n Y", None),
        (True, "Bash", "helm --kube-context X -n Y uninstall r", ASK),
        (False, "Bash", "helm --kube-context X -n Y uninstall r", ASK),
        (True, "Bash", "helm del r --kube-context X -n Y", ASK),
        (True, "Bash", "helm uninstall r", DENY),
        (True, "Bash", "helm rollback r 1 --kube-context X -n Y", ASK),
        (False, "Bash", "helm rollback r 1 --kube-context X -n Y", ASK),
        (True, "Bash", "helm rollback r 1 --kube-context X -n Y --force-conflicts", ASK),
        (False, "Bash", "helm list --kube-context X -n Y", None),
        (False, "Bash", "helm list -n Y", DENY),
        (False, "Bash", "kubectl get nodes --context X -L atero/user", None),
        (False, "Bash", "kubectl get --raw /api/v1/nodes/n/proxy/stats/summary --context X", None),
        (False, "Bash", "kubectl get nodes -L atero/user", DENY),
        (False, "Bash", "kubectl get pods --context X", DENY),
        (False, "Bash", "kubectl get pods -A --context X", None),
        (True, "Bash", "kubectl config get-contexts", None),
        (True, "Bash", "kubectl config current-context", None),
        (True, "Bash", "kubectl kustomize ./overlay", None),
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
        (True, "Bash", "helm dependency update ./chart", None),
        (True, "Bash", "helm plugin list", None),
        (True, "Bash", "helm version", None),
        (False, "Bash", "bash -c 'kubectl get pods'", DENY),
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
        (False, "Bash", "git stash", DENY),
        (False, "Bash", "git restore .", DENY),
        (False, "Bash", "git checkout -- .", DENY),
        (False, "Bash", "make test", ASK),
        (False, "Bash", "make test 2>&1", ASK),
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
        (False, "Bash", f"touch {scratch}x", None),
        (False, "Bash", f"rm {scratch}x", None),
        (False, "Bash", f"echo hi > {scratch}x", None),
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
        (False, "Bash", "git -C /x archive -o x.tar HEAD", DENY),
        (False, "Bash", f"git -C /x archive -o {scratch}x.tar -o {home}/x.tar HEAD", DENY),
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
        (False, "Bash", f"touch {scratch}../x", DENY),
        (True, "Bash", f"rm -rf {scratch}x {home}/.cache/x", ASK),
        (True, "Bash", f"rm -rf {scratch}x", None),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", ASK),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", ASK),
        (True, "Bash", "CRUSOE_PROFILE=p crusoe kubernetes clusters get-credentials --project-name j -y c", ASK),
        (True, "Bash", "crusoe kubernetes clusters get-credentials c --project-name j", ASK),
        (False, "Bash", "crusoe kubernetes clusters get-credentials --project-name j c", ASK),
        (True, "Bash", "crusoe kubernetes clusters list --project-name j", None),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --dry-run", None),
        (False, "Bash", "helm install r ./c --kube-context X -n Y", ASK),
        (False, "Bash", "helm install r ./c -n Y", DENY),
        (True, "Bash", "helmfile --kube-context X apply", ASK),
        (False, "Bash", "helmfile --kube-context X sync", ASK),
        (True, "Bash", "helmfile -e dev --kube-context X destroy", ASK),
        (True, "Bash", "helmfile apply", DENY),
        (True, "Bash", "helmfile --kube-context X diff", None),
        (False, "Bash", "helmfile template", None),
        (True, "Bash", "pytest", ASK),
        (False, "Bash", "pytest tests/", ASK),
        (True, "Bash", "uv run pytest -q", ASK),
        (True, "Bash", "python3 -m pytest tests", ASK),
        (True, "Bash", "go test ./...", ASK),
        (True, "Bash", "cargo test", ASK),
        (True, "Bash", "cargo test -p mycrate", ASK),
        (True, "Bash", "make test", ASK),
        (False, "Bash", "npm test", ASK),
        (True, "Bash", "pytest tests/test_x.py", None),
        (True, "Bash", "pytest -k name", None),
        (True, "Bash", "pytest x.py::test_y", None),
        (True, "Bash", "uv run pytest tests/test_x.py -q", None),
        (True, "Bash", "go test ./pkg/foo -run TestX", None),
        (True, "Bash", "go test ./pkg/foo", None),
        (True, "Bash", "cargo test name", None),
        (True, "Bash", "./scripts/run-tests.sh", None),
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
        (False, "Bash", "kubectl exec p -- sh -c 'rm -rf /data' --help", DENY),
        (False, "Bash", "python3 /x/deploy.py --help", None),
        (False, "Bash", "python3 /x/board.py fetch garbled-output --org 2", None),
        (False, "Bash", f"python3 /x/board.py fetch g --org 2 --out {scratch}g.json", None),
        (False, "Bash", "python3 /x/board.py fetch g --org 2 --out /x/g.json", DENY),
        (False, "Bash", "python3 /x/board.py diff g /x/g.json --org 2", None),
        (False, "Bash", "python3 /x/board.py login", DENY),
        (True, "Bash", "python3 /x/board.py publish g /x/g.json --org 2 --message m", None),
        (False, "Bash", "bash -c 'rm -rf /x' --help", DENY),
        (False, "Bash", "kubectl get pods --help", None),
        (False, "Bash", "helm upgrade --help", None),
        (False, "Bash", "python3 --help", None),
        (False, "Bash", "kubectl version", DENY),
        (False, "Bash", "git -c core.fsmonitor=/x.sh status", DENY),
        (False, "Bash", "git -C /x -c diff.external=/x.sh diff", DENY),
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
        (False, "Bash", "kubectl get policies --context X", DENY),
        (False, "Bash", "kubectl get pods --context X", DENY),
        (False, "Bash", "python3 -m json.tool", None),
        (False, "Bash", "python3 -m unittest", None),
        (False, "Bash", "gh api graphql -f query='{viewer{login}}'", None),
        (False, "Bash", "gh api graphql -f query='mutation{x}'", DENY),
        (True, "Bash", "kubectl config use-context x", ASK),
        (False, "Bash", "kubectl config use-context x", ASK),
        (True, "Bash", "kubectx x", ASK),
        (False, "Bash", "kubectx x", ASK),
        (True, "Bash", "kubens x", ASK),
        (True, "Bash", "kubectl label node n atero/user=x --context X", ASK),
        (True, "Bash", "kubectl label node n atero/user=x", DENY),
        (True, "Bash", "kubectl label pod p a=b --context X", DENY),
        (True, "Bash", "kubectl taint nodes n k=v:NoSchedule --context X", ASK),
        (True, "Bash", "kubectl cordon n --context X", ASK),
        (True, "Bash", "kubectl certificate approve x --context X", DENY),
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
        (False, "Bash", "stern x --context X -n Y", None),
        (False, "Bash", "stern x", DENY),
        (False, "Bash", "kubectl --help", None),
        (False, "Bash", "python3 -m pytest tests/", ASK),
        (False, "Bash", "zsh -ic 'echo $HISTFILE; setopt | grep -i hist'", None),
        (False, "Bash", 'which claude; stat -f "%Sm %N" "$(readlink -f "$(which claude)")" 2>&1', None),
        (False, "Bash", "claude auth status", None),
        (False, "Bash", "claude -p auth status", DENY),
        (False, "Bash", "claude plugin list --json --available", None),
        (False, "Bash", "claude plugin marketplace list", None),
        (False, "Bash", "claude -p plugin list", DENY),
        (False, "Bash", "claude plugin install foo", DENY),
        (False, "Bash", "claude plugin marketplace update", DENY),
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
        (False, "Bash", "kubectl get pods --context X -n 123 > /private/tmp/claude/p", None),
        (False, "Bash", "bash -lc 'touch /etc/x'", DENY),
        (False, "Bash", f"bash {scratch}check.sh", None),
        (False, "Bash", f"python3 {scratch}check.py", None),
        (True, "Bash", f"python3 {scratch}check.py", None),
        (False, "Bash", f"python3 {os.path.realpath(__file__)} --selftest", None),
        (False, "Write", {"file_path": f"{scratch}a.md"}, None),
        (False, "Write", {"file_path": "/tmp/a.md"}, None),
        (False, "Write", {"file_path": f"{home}/.claude/lfg-state/x"}, DENY),
        (False, "Edit", {"file_path": f"{home}/repos/x.py"}, None),
        (True, "Edit", {"file_path": f"{home}/repos/x.py"}, None),
        (False, "NotebookEdit", {"notebook_path": f"{scratch}n.ipynb"}, None),
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
    ]
    failures = 0
    for gate_open, tool_name, tool_input, expected in cases:
        if tool_name == "Bash":
            tool_input = {"command": tool_input}
        got = decide(tool_name, tool_input, gate_open)
        got_kind = got[0] if got else None
        ok = got_kind == expected
        failures += not ok
        shown = (tool_input["command"].replace("\n", "\\n") if tool_name == "Bash"
                 else f"{tool_name} {tool_input}")
        print(f"{'ok  ' if ok else 'FAIL'} [{'open' if gate_open else 'closed'}] "
              f"{shown} -> {got_kind}" + ("" if ok else f" (want {expected})"))
    payload_cases = [
        ({"tool_name": "Bash", "session_id": "s"}, DENY),
        ({"tool_name": "Write", "session_id": "s", "tool_input": None}, DENY),
        ({"tool_name": "Read", "session_id": "s", "tool_input": {"file_path": "/x"}}, None),
    ]
    for payload, expected in payload_cases:
        result = hook_output(payload)
        got = (result or {}).get("hookSpecificOutput", {}).get("permissionDecision")
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} payload {payload} -> {got}"
              + ("" if ok else f" (want {expected})"))
    s = SCRATCH_ROOTS[0]
    strip_cases = [
        # (command, expected command after the strip)
        (f"go list ./... > {s}deps.txt; grep x {s}deps.txt; rm -f {s}deps.txt",
         f"go list ./... > {s}deps.txt; grep x {s}deps.txt"),
        (f"rm -rf {s}build && make test", "make test"),
        (f"rm -rf /tmp/claude/build; make test", "make test"),
        (f"make test && rm -rf {s}build 2>/dev/null", "make test"),
        (f"a; rm -- {s}x {s}y; b", "a; b"),
        (f"rm -f {s}x", f"rm -f {s}x"),
        (f"a && rm {s}x || echo failed", f"a && rm {s}x || echo failed"),
        (f"a | rm {s}x", f"a | rm {s}x"),
        ("a; rm -f $TMPDIR/x", "a; rm -f $TMPDIR/x"),
        (f"a; rm -rf {s}x ~/repos", f"a; rm -rf {s}x ~/repos"),
        (f"a; rm -rf {s}../../etc", f"a; rm -rf {s}../../etc"),
        (f"a; rm -rf {s}{{x,../..}}", f"a; rm -rf {s}{{x,../..}}"),
        (f"a; rm -rf {s}x /tmp/y", f"a; rm -rf {s}x /tmp/y"),
        (f"a; rm -rf {s}x\nb", "a\nb"),
        (f"a\nrm -rf {s}x\nb", "a\nb"),
        (f"a; rm -rf {s}x 2>&1", "a"),
        ("a; rm -rf /", "a; rm -rf /"),
        ("a; rmdir x", "a; rmdir x"),
        # Quoted text and substitutions are opaque: an rm inside them is someone's argument.
        (f"python3 gate.py 'a; rm -rf {s}x'", f"python3 gate.py 'a; rm -rf {s}x'"),
        (f'bash -c "make; rm -rf {s}x"', f'bash -c "make; rm -rf {s}x"'),
        (f"git commit -m 'drop; rm -rf {s}x'", f"git commit -m 'drop; rm -rf {s}x'"),
        (f"(cd y && rm -rf {s}x)", f"(cd y && rm -rf {s}x)"),
        (f"echo $(rm -rf {s}x)", f"echo $(rm -rf {s}x)"),
        (f"a; rm -rf {s}x &", f"a; rm -rf {s}x &"),
        (f"a; rm -rf {s}x # done", "a"),
        (f"cat <<'EOF' > {s}f\nrm -rf {s}x\nEOF", f"cat <<'EOF' > {s}f\nrm -rf {s}x\nEOF"),
        (f"cat <<EOF > {s}f\nhello\nEOF\nrm -rf {s}f", f"cat <<EOF > {s}f\nhello\nEOF"),
        (f"cat <<-EOF > {s}f\n\thello\n\tEOF\nrm -rf {s}f", f"cat <<-EOF > {s}f\n\thello\n\tEOF"),
        (f"cat <<< 'rm -rf {s}x'", f"cat <<< 'rm -rf {s}x'"),
        (f"cat <<EOF\nrm -rf {s}x", f"cat <<EOF\nrm -rf {s}x"),
        # A chain of dropped segments must not leave a dangling separator.
        (f"rm -rf {s}a && rm -rf {s}b && make", "make"),
        (f"a; rm -rf {s}x; rm -rf {s}y", "a"),
        (f"make \\\n  test; rm -rf {s}x", "make \\\n  test"),
        (f"sleep 1 &\nrm -rf {s}x", "sleep 1 &"),
        # A block keeps its body.
        (f"if true; then\n  rm -rf {s}x\nfi", f"if true; then\n  rm -rf {s}x\nfi"),
        (f"for i in 1; do rm -rf {s}x; done", f"for i in 1; do rm -rf {s}x; done"),
        (f"if true; then\n  make\n  rm -rf {s}x\nfi", f"if true; then\n  make\n  rm -rf {s}x\nfi"),
    ]
    for command, expected in strip_cases:
        got, _ = strip_scratch_rm(command)
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} strip {command!r} -> {got!r}"
              + ("" if ok else f" (want {expected!r})"))
    label_cases = [
        # (command, expected rating): heredoc bodies are data, never programs
        (f"git commit -q -F - <<'EOF'\nfix: drop; rm -rf {s}x\nEOF", WRITE),
        ("cat <<EOF\nrm -rf /\nEOF", READ),
        ("cat <<EOF\nhello\nEOF\nrm -rf /", DANGER),
        # Process substitution runs its own command.
        ("cat <(rm -rf /etc)", DANGER),
        ("diff <(sort a) <(sort b)", READ),
        ("tee >(rm -rf /etc)", DANGER),
        # Command substitution runs its own command; text glued after its `)` is still
        # the outer command's argument, never a program of its own.
        ("launchctl print gui/$(id -u)/ai.example.agent", READ),
        ("git -C $(pwd) status", READ),
        ("ls $(dirname $(pwd))/x", READ),
        ("echo $(rm -rf /etc)/x", DANGER),
        ("kubectl get pods -o name $(echo x) && rm -rf /etc", DANGER),
        ("(cd /x && ls) ; launchctl print gui/$(id -u)/x", READ),
        ("glab mr update 3 --description-file d.md", DANGER),
        ("python3 /x/board.py publish g /x/g.json --org 2 --message m", DANGER),
        ("python3 /x/board.py fetch g --org 2 --out=/x/g.json", WRITE),
        ("gh pr edit 3 --body-file d.md", DANGER),
        ("glab mr create --fill", DANGER),
        ("glab mr note 3 -m x", DANGER),
        ("glab mr note list 3", READ),
        ("glab -R g/p mr note draft list 3", READ),
        ("gh pr checkout 3", WRITE),
        ("glab mr view 3", READ),
        ("gh repo clone o/r", WRITE),
        ("glab api -X PUT projects/p/merge_requests/3 -f title=x", DANGER),
        ("glab api projects/p/merge_requests/3/notes -f body=x", DANGER),
        ("glab api graphql -f query='mutation{x}'", DANGER),
        ("glab api projects/p/merge_requests/3", READ),
        ("glab api -X GET projects/p/merge_requests -f state=opened", READ),
        ("git lfs", READ),
        ("git lfs clean x.tgz", READ),
        ("git lfs status", READ),
        ("git lfs migrate import --everything", WRITE),
        ("git lfs push origin main", DANGER),
        ("git lfs lock x.bin", DANGER),
        ("git lfs unlock --force x.bin", DANGER),
        ("git lfs locks", READ),
        ("glab issue create -t x", DANGER),
        ("glab ci retry 5", DANGER),
        ("glab -R g/p mr update 3 -d x", DANGER),
        ("glab config set editor vim", WRITE),
        ("glab alias set v 'mr view'", WRITE),
        ("glab auth login", WRITE),
        ("glab repo clone g/r", WRITE),
        ("glab mr checkout 3", WRITE),
        ("glab -R g/p mr checkout 3", WRITE),
        ("glab --repo=g/p mr checkout 3", WRITE),
        ("glab -Rg/p repo clone g/r", WRITE),
        ("glab api -XGET projects/p/merge_requests -f state=opened", READ),
        ("glab api --method=GET projects/p/merge_requests -f state=opened", READ),
        ("glab api -XPUT projects/p/merge_requests/3 -f title=x", DANGER),
        ("glab release create v1.2.3", DANGER),
        ("docker push registry.example/x:t", DANGER),
        ("docker buildx build --push -t registry.example/x:t .", DANGER),
        ("buildah push registry.example/x:t", DANGER),
        ("docker build -t x .", WRITE),
        ("docker compose push", DANGER),
        ("docker buildx imagetools create -t registry.example/x:t registry.example/x:a", DANGER),
        ("skopeo copy docker://a/x:t docker://b/x:t", DANGER),
        ("skopeo copy docker://a/x:t dir:/x/out", WRITE),
        ("skopeo inspect docker://a/x:t", READ),
        ("skopeo delete docker://a/x:t", DANGER),
        ("python3 /x/scripts/build_vllm_overlay.py --branch b", DANGER),
        ("uv run /x/scripts/build_vllm_overlay.py --branch b", DANGER),
        ("/x/scripts/build_vllm_overlay.py --branch b", DANGER),
        ("gh api -X PATCH repos/o/r/pulls/1 -f body=x", WRITE),
    ]
    for command, expected in label_cases:
        got = classify_command(command)
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} rating {command!r} -> {got}"
              + ("" if ok else f" (want {expected})"))
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
        saved_roots = GATE_SCRATCH_ROOTS
        scratch_dir = os.path.join(root, "scratch")
        os.makedirs(scratch_dir)
        GATE_SCRATCH_ROOTS = (os.path.realpath(scratch_dir) + "/",)
        gate_cases = [
            # (tool, input, expected decision with the gate closed), run from on_main
            ("Bash", {"command": "python3 -c 'print(1)'"}, None),
            ("Bash", {"command": "uv run --with pyyaml python3 -c 'print(1)'"}, None),
            ("Bash", {"command": "docker run --rm img amtool template render"}, None),
            ("Bash", {"command": f"echo x > {scratch_dir}/out"}, None),
            ("Bash", {"command": f"echo x > {on_main}/out"}, DENY),
            ("Bash", {"command": f"sed -i '' s/a/b/ {on_main}/README.md"}, DENY),
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
            ("Bash", {"command": "touch x"}, DENY),
            ("Bash", {"command": f"cp a.txt {scratch_dir}/"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && touch ../x"}, DENY),
            ("Bash", {"command": f"cd {scratch_dir} && touch $X"}, DENY),
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
            ("Bash", {"command": f"{not_repo}/tool.sh"}, None),
            ("Edit", {"file_path": f"{on_main}/README.md"}, DENY),
            ("Write", {"file_path": f"{on_main}/sub/new.py"}, DENY),
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
            ok = got is None
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} gate EnterWorktree, gate open -> {got}")
        finally:
            GATE_SCRATCH_ROOTS = saved_roots
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
        }
        for name, text in scripts.items():
            with open(os.path.join(not_repo, name), "w") as f:
                f.write(text)
        script_cases = [
            # (command, expected decision with the gate open), run from the scripts' directory
            ("./deploy.sh", ASK),
            ("bash deploy.sh", ASK),
            ("python3 cleanup.py", ASK),
            ("uv run --with x python cleanup.py", ASK),
            ("./mock.sh", None),
            ("sh remote.sh", ASK),
            ("./read.sh", None),
            ("./built.sh", None),
            ("./kubeconfig.sh", None),
            ("./mixed.sh", ASK),
            (f"cd {root} && ./plain/deploy.sh", ASK),
            (f"(cd {root} && ./plain/deploy.sh)", ASK),
            (f"(cd {root} && ./plain/read.sh)", ASK),
            ("bash -c 'echo deploy.sh'", None),
            ("./missing.sh", None),
        ]
        for command, expected in script_cases:
            got = decide("Bash", {"command": command}, True, not_repo)
            got = got[0] if got else None
            ok = got == expected
            failures += not ok
            print(f"{'ok  ' if ok else 'FAIL'} script {command!r} -> {got}"
                  + ("" if ok else f" (want {expected})"))
    total = (len(cases) + len(payload_cases) + len(strip_cases) + len(label_cases)
             + len(branch_cases) + len(script_cases) + len(gate_cases) + 1)
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
