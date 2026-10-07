#!/usr/bin/env python3
"""PreToolUse hook: the `LFG!` gate, plus the READ/WRITE/DANGER label on Bash commands.

For Bash it classifies what the command can change and rewrites the tool's `description`
so a permission dialog opens with the verdict:

    🟢 READ    changes nothing
    🟠 WRITE   changes local, recoverable state (files, commits, installs, helm releases)
    🔴 DANGER  destroys data or changes live cluster / remote state

Anything the classifier does not recognise is WRITE: a wrong orange costs a glance, a
wrong green is the failure this hook exists to prevent.

For Bash, Edit, Write, NotebookEdit and every MCP tool it then decides, from the gate
state lfg-state.py records per session: a write before `LFG!` is denied with the refusal
line, the permanently excluded git and cluster operations are denied in every state, and
the pin rules for kubectl and helm are enforced. A program the classifier does not know
asks instead of denying, so a read it has not met never gets the refusal line.

An `rm` whose every path is a literal under the scratch root is dropped from the command
before the permission rules see it: the org's `Bash(rm:*)` ask rule prompts on any `rm`
and no allow rule outranks an ask rule, while scratch is per session and left behind
anyway, so the delete costs a prompt and buys nothing. An `rm` that names a scratch path
alongside anything outside the scratch root is forced to prompt instead, so that
`rm -rf /private/tmp/claude/x ~/repos` or `rm -rf /private/tmp/claude/../..` never
passes as scratch cleanup.

CLI: `tool-gate.py [--open] <command>...` prints the label and the decision for each
Bash command with the gate closed (default) or open; `--tool <name> <field>=<value>...`
does the same for another tool; `--selftest` runs the decision table's cases.
"""

import contextlib
import json
import os
import re
import shlex
import sys

READ, WRITE, DANGER = "🟢 READ", "🟠 WRITE", "🔴 DANGER"
RANK = {READ: 0, WRITE: 1, DANGER: 2}
LABEL_RE = re.compile(r"^(?:🟢 READ|🟠 WRITE|🔴 DANGER)\s*[·:|-]?\s*")

SEPARATORS = {";", ";;", "|", "||", "&&", "&", "(", ")", "|&"}
REDIRECT_OUT = {">", ">>", "&>", "&>>", ">|"}
HARMLESS_TARGETS = {"/dev/null", "/dev/stderr", "/dev/stdout", "/dev/tty"}
SCRATCH_PREFIXES = ("/tmp/claude/", "/private/tmp/claude/")
SCRATCH_ROOTS = tuple(os.path.realpath(p.rstrip("/")) + "/" for p in SCRATCH_PREFIXES)
ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Shell words that precede the real program on a segment and carry no verdict of their own.
TRANSPARENT = {"do", "then", "else", "elif", "!", "{", "}", "if", "while", "until", "time",
               "exec", "command", "builtin", "nohup", "nice", "env", "stdbuf", "caffeinate"}
# A segment made only of one of these is loop/branch syntax.
SYNTAX_ONLY = {"done", "fi", "esac", "in", "function", "then", "do", "else", "}", "{"}
# `for p in a b` names variables, not a program: the body is its own segment after `do`.
LOOP_HEADERS = {"for", "case", "select"}

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
    "gofmt", "helmfile", "glab-ci-view", "wrenchmark-report", "gpg",
}
# `split`, `gpg`, `iconv` write files only with explicit output options the handlers below catch.

WRITE_PROGRAMS = {
    "cp", "mv", "mkdir", "touch", "ln", "install", "patch", "tee", "truncate", "chmod", "chown",
    "chgrp", "zip", "gzip", "gunzip", "bzip2", "xz", "open", "osascript", "code", "vim", "nvim",
    "vi", "nano", "emacs", "ssh", "scp", "sftp", "source", ".", "eval", "uvx", "pipx",
    "psql", "mysql", "sqlite3", "redis-cli", "mongosh", "perl", "ruby", "node", "deno", "bun",
    "pre-commit", "kubectx", "kubens", "k9s", "git-lfs", "pbcopy", "say", "afplay", "xattr",
    "defaults", "crontab", "ollama",
}

DANGER_PROGRAMS = {
    "rm", "rmdir", "dd", "mkfs", "shred", "diskutil", "kill", "pkill", "killall", "shutdown",
    "reboot", "halt", "sudo", "doas", "fdisk", "parted", "wipefs", "nvme", "fuser",
}

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
GATED_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit"}
PATH_FIELD = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}

# Writes here never need the gate: scratch, plan mode and memory are harness bookkeeping.
GATE_SCRATCH_ROOTS = tuple(os.path.realpath(os.path.expanduser(p)) + "/"
                           for p in ("/private/tmp/claude", "~/.cache", "~/.claude/plans"))
MEMORY_ROOT_RE = re.compile(
    "^" + re.escape(os.path.realpath(os.path.expanduser("~/.claude/projects"))) + r"/[^/]+/memory/")
# Bash writers whose every positional path the script can read without path-sniffing.
SCRATCH_WRITERS = {"mkdir", "touch", "cp", "mv", "tee", "rm"}

# kubectl verbs CLAUDE.md excludes from the gate: never run by the model, printed for the user.
KUBECTL_EXCLUDED_BY_CLAUDE_MD = {"apply", "delete", "create", "patch", "edit", "scale", "rollout"}
KUBECTL_ROLLOUT_READS = {"status", "history"}
# Verbs that write live cluster state the same way and that CLAUDE.md does not name.
KUBECTL_EXCLUDED_WIDENED = {"replace", "set", "label", "annotate", "taint", "cordon", "uncordon",
                            "drain", "evict", "expose", "run", "debug", "autoscale", "certificate"}
KUBECTL_CONTEXT_SETTERS = {"use-context", "set-context"}
# Subcommands that never reach a cluster, so the pin rules do not apply.
KUBECTL_LOCAL = {"config", "kustomize", "completion", "options", "help"}
HELM_LOCAL = {"template", "lint", "show", "search", "pull", "package", "push", "registry",
              "create", "env", "verify", "repo", "dependency", "plugin", "version",
              "completion", "help"}
HELM_EXCLUDED = {"uninstall", "delete", "del", "rollback"}
# Cluster-scoped reads where kubectl ignores -n; `get --raw` carries an API path instead.
NAMESPACE_FREE = {("get", "node"), ("get", "nodes"), ("describe", "node"), ("describe", "nodes"),
                  ("top", "node"), ("top", "nodes")}
KUBECTL_GLOBAL_VALUE_FLAGS = {
    "--context", "--kubeconfig", "-n", "--namespace", "--cluster", "--user", "-s", "--server",
    "--token", "--as", "--as-group", "--request-timeout", "--certificate-authority",
    "--client-certificate", "--client-key", "--tls-server-name", "--cache-dir", "--profile",
    "--profile-output", "-v", "--v", "--vmodule",
}
HELM_GLOBAL_VALUE_FLAGS = {
    "--kube-context", "--kubeconfig", "-n", "--namespace", "--kube-apiserver", "--kube-token",
    "--kube-as-user", "--kube-as-group", "--kube-ca-file", "--registry-config",
    "--repository-cache", "--repository-config", "--burst-limit", "--qps",
}

# The TL;DR into a fired alert's thread and the reaction marking the alert as under investigation
# are ungated; these are the alert channels, comma-separated in TOOL_GATE_ALERT_CHANNEL_IDS, which
# the shell rc exports from its private block so the IDs stay out of this file's public copy. A
# copy of what the alertmanager config owns: a channel added there and not here asks instead, and
# with the variable unset every alert-thread post asks.
ALERT_CHANNEL_IDS = set(filter(None, os.environ.get("TOOL_GATE_ALERT_CHANNEL_IDS", "").split(",")))

# MCP tools match on the name after the last `__`: connectors show up under two server-name
# forms. Anything in neither set asks while the gate is closed.
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
MCP_WRITE_PREFIXES = (
    "create", "update", "edit", "add", "delete", "remove", "transition", "send", "schedule",
    "write", "post", "put", "dispatch", "slack_send", "slack_create", "slack_update",
    "slack_add", "slack_schedule", "plumber_dispatch", "agent_browser_click",
    "agent_browser_fill", "agent_browser_type", "agent_browser_press", "agent_browser_select",
    "agent_browser_check", "agent_browser_uncheck", "agent_browser_eval",
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


def classify_git(args):
    rest = list(args)
    while rest and rest[0] in ("-C", "-c", "--git-dir", "--work-tree", "--no-pager", "-P"):
        rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
    rest = [a for a in rest if not a.startswith("--git-dir=") and not a.startswith("--work-tree=")]
    if not rest:
        return READ
    sub, rest = rest[0], rest[1:]
    pos = positionals(rest)
    force = has_flag(rest, "-f", "--force", "--force-with-lease")
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
        return READ if has_flag(rest, "--get", "--get-all", "--get-regexp", "--list", "-l",
                                "--show-origin", "--get-urlmatch") else WRITE
    if sub == "worktree":
        if pos and pos[0] == "list":
            return READ
        return DANGER if pos and pos[0] in ("remove", "prune") else WRITE
    if sub == "push":
        return DANGER
    if sub == "fetch":
        return DANGER if force else READ
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
    if sub in {"rebase", "cherry-pick", "merge", "am", "revert", "rm", "mv", "submodule",
               "add", "commit", "pull", "init", "clone", "apply", "notes", "bisect",
               "tag", "rerere", "sparse-checkout", "lfs"}:
        return DANGER if force and sub in ("rebase", "rm", "clone", "pull") else WRITE
    return WRITE


def kubectl_exec_command(rest):
    if "--" not in rest:
        return None
    return rest[rest.index("--") + 1:]


def classify_kubectl(args):
    rest, _ = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if not pos:
        return READ
    verb = pos[0]
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
    if verb in KUBECTL_EXCLUDED_BY_CLAUDE_MD or verb in KUBECTL_EXCLUDED_WIDENED:
        return DANGER
    return WRITE


def classify_helm(args):
    rest, _ = split_globals(args, HELM_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if not pos:
        return READ
    sub = pos[0]
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
    if sub in HELM_EXCLUDED:
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


def classify_curl(args):
    method = http_method(args, "-X", "--request")
    if method == "DELETE":
        return DANGER
    if method not in ("GET", "HEAD", "OPTIONS"):
        return WRITE
    if any(t not in STDOUT_SINKS for t in curl_output_targets(args)):
        return WRITE
    if has_flag(args, "-O", "--remote-name", "--remote-name-all", "-T",
                "--upload-file", "-F", "--form", "--form-string", "-d", "--data", "--data-raw",
                "--data-binary", "--data-urlencode", "--data-ascii", "--json"):
        return WRITE
    if any(a.startswith(("-d", "-F", "-T")) and len(a) > 2 and not a.startswith("--")
           for a in args):
        return WRITE
    return READ


HTTP_METHODS = {"GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE", "TRACE", "CONNECT"}
XH_VALUE_FLAGS = {"-a", "--auth", "-A", "--auth-type", "-o", "--output", "--raw", "-p",
                  "--print", "-P", "--history-print", "--pretty", "-s", "--style", "--proxy",
                  "--timeout", "--max-redirects", "--verify", "--cert", "--cert-key", "--ssl",
                  "--http-version", "--resolve", "--interface", "--response-charset",
                  "--response-mime", "--session", "--session-read-only", "--format-options",
                  "--unix-socket", "--generate"}


def classify_xh(args):
    """httpie syntax: an optional method in any case, the URL, then items; a `key=value`,
    `key:=json` or `key@file` item, or `--raw`, implies POST."""
    rest, _ = split_globals(args, XH_VALUE_FLAGS)
    pos = positionals(rest)
    method = pos[0].upper() if pos and pos[0].upper() in HTTP_METHODS else None
    items = pos[2:] if method else pos[1:]
    if method == "DELETE":
        return DANGER
    body = (any(("=" in a and "==" not in a) or "@" in a for a in items)
            or has_flag(args, "--raw"))
    if method not in (None, "GET", "HEAD", "OPTIONS") or (method is None and body):
        return WRITE
    if has_flag(args, "-d", "--download", "-o", "--output"):
        return WRITE
    return READ


def classify_gh(args):
    pos = positionals(args)
    if not pos:
        return READ
    group = pos[0]
    sub = pos[1] if len(pos) > 1 else ""
    if group == "api":
        method = http_method(args, "-X", "--method")
        if method == "DELETE":
            return DANGER
        if method != "GET" or has_flag(args, "-f", "-F", "--field", "--raw-field", "--input"):
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
    return WRITE


def classify_claude(args):
    # A print-mode call is a model call that writes nothing only once both tool surfaces are
    # off: `--tools ""` removes the built-in tools and leaves the connectors, which the
    # disallow pattern removes. Anything else can edit files or post somewhere.
    pos = positionals(args)
    if pos[:2] == ["auth", "status"]:
        return READ
    if has_flag(args, "-p", "--print"):
        no_builtin = any(a == "--tools=" or (a == "--tools" and args[i + 1:i + 2] == [""])
                         for i, a in enumerate(args))
        no_mcp = any(a in ("--disallowedTools", "--disallowed-tools") and args[i + 1:i + 2] == ["mcp__*"]
                     for i, a in enumerate(args))
        if no_builtin and no_mcp:
            return READ
    return WRITE


def classify_docker(args):
    pos = positionals(args)
    if not pos:
        return READ
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


def classify_sed(args):
    if any(re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in args):
        return WRITE
    return READ


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
        if args[1] in ("pytest", "json.tool", "unittest", "mypy", "pyright", "ruff", "black",
                       "isort", "flake8", "pylint", "tomllib"):
            return classify_program(args[1], args[2:])
        if args[1] == "pip":
            return classify_pip(args[2:])
        return WRITE
    return WRITE


def classify_pip(args):
    pos = positionals(args)
    if has_flag(args, "--version", "-V") or (pos and pos[0] in ("list", "show", "freeze", "check",
                                                                 "index", "debug", "config",
                                                                 "download", "hash", "inspect")):
        return READ
    return WRITE


def classify_uv(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-V"):
        return READ
    sub = pos[0]
    if sub == "run":
        tail = list(args)
        tail = tail[tail.index("run") + 1:]
        while tail and tail[0].startswith("-"):
            tail = tail[2:] if tail[0] in ("--with", "--python", "-p", "--package",
                                          "--directory", "--project", "--extra") else tail[1:]
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
    if has_flag(args, "--list", "-t"):
        return READ
    first = args[0] if args else ""
    cluster = first.lstrip("-")
    if first and re.match(r"^-?[a-zA-Z]+$", first) and "t" in cluster and not ({"x", "c", "r", "u"} & set(cluster)):
        return READ
    return WRITE


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
    "git": classify_git,
    "kubectl": classify_kubectl, "k": classify_kubectl, "oc": classify_kubectl,
    "helm": classify_helm,
    "stern": classify_stern,
    "curl": classify_curl, "http": classify_xh, "https": classify_xh, "xh": classify_xh,
    "wget": classify_wget,
    "gh": classify_gh, "glab": classify_gh,
    "claude": classify_claude,
    "docker": classify_docker, "podman": classify_docker, "nerdctl": classify_docker,
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


def classify_program(prog, args):
    if "--help" in args or args in (["-h"], ["--version"], ["-V"], ["version"], ["help"]):
        return READ
    if prog in DANGER_PROGRAMS:
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
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    tokens = list(lexer)
    segments, targets, segment = [], [], []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in SEPARATORS:
            if segment:
                segments.append(segment)
            segment = []
        elif tok in ("<(", ">("):
            # Process substitution runs a command of its own; `)` closes it like a subshell.
            if segment:
                segments.append(segment)
            segment = []
        elif tok in REDIRECT_OUT or tok in (">&", "<", "<<", "<<<", "<&", "<>"):
            # GOTCHA: shlex splits `2>&1` into `2`, `>&`, `1`; after a `)` or `;` the
            # descriptor digit is a segment of its own and would read as a program.
            if len(segment) == 1 and segment[0].isdigit():
                segment.pop()
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
    return segments, targets


def classify_line(line):
    segments, targets = split_line(line)
    level = WRITE if any(t not in HARMLESS_TARGETS for t in targets) else READ
    for segment in segments:
        level = worst(level, classify_words(segment))
    return level


def command_lines(command):
    for line in without_heredoc_bodies(command).replace("`", " ; ").splitlines():
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


def invocations(command):
    """Every program invocation in a command, nested ones included, as (program, args)."""
    for line in command_lines(command):
        try:
            segments, _ = split_line(line)
        except ValueError:
            continue
        for segment in segments:
            yield from invocations_in(segment)


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


def bash_scratch_exempt(command):
    """True when every write in the command lands in a gate scratch root."""
    for line in command_lines(command):
        try:
            segments, targets = split_line(line)
        except ValueError:
            return False
        if any(t not in HARMLESS_TARGETS and not inside_gate_scratch(t) for t in targets):
            return False
        for words in segments:
            words = strip_prefix(words)
            if not words or program_of(words) in LOOP_HEADERS:
                continue
            prog, args = program_of(words), words[1:]
            if classify_program(prog, args) == READ:
                continue
            if prog in SCRATCH_WRITERS:
                paths = rm_paths(args) if prog == "rm" else positionals(args)
                if paths and all(inside_gate_scratch(p) for p in paths):
                    continue
            return False
    return True


def only_unknown_writes(command):
    with unknown_programs_as(READ):
        return classify_command(command) == READ


def pin_decisions(prog, args):
    """The rows that apply in every gate state, for one program invocation."""
    out = []
    if "--help" in args or args in (["-h"], ["--version"], ["-V"]):
        return out
    if prog == "git":
        rest = [a for a in args if not a.startswith("-")]
        if rest and rest[0] == "push":
            out.append((DENY, "git push is never run by the model: say the branch is ready "
                              "and print the command"))
    elif prog in ("kubectx", "kubens"):
        out.append((DENY, "never set the target: pin every command with --context and -n"))
    elif prog in ("kubectl", "k", "oc", "stern"):
        rest, seen = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
        pos = positionals(rest)
        verb = pos[0] if pos else ""
        sub = pos[1] if len(pos) > 1 else ""
        if prog != "stern":
            if verb == "config" and sub in KUBECTL_CONTEXT_SETTERS:
                out.append((DENY, "never set the target: pin every command with --context and -n"))
                return out
            if not pos or verb in KUBECTL_LOCAL or (verb == "version" and "--client" in rest):
                return out
            excluded = (verb in KUBECTL_EXCLUDED_WIDENED
                        or (verb in KUBECTL_EXCLUDED_BY_CLAUDE_MD
                            and not (verb == "rollout" and sub in KUBECTL_ROLLOUT_READS)))
            if excluded and not dry_run(rest):
                out.append((DENY, f"kubectl {verb} is yours to run: print it as `! <command>`"))
        if not seen.get("--context"):
            out.append((DENY, "pin the context: every cluster command carries --context <ctx>"))
        namespace_free = (prog != "stern" and ((verb, sub) in NAMESPACE_FREE
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
        if sub in HELM_EXCLUDED or has_flag(rest, "--force-conflicts"):
            out.append((DENY, f"helm {sub}{' --force-conflicts' if has_flag(rest, '--force-conflicts') else ''}"
                              " is yours to run: print it as `! <command>`"))
        if sub in ("install", "upgrade") and has_flag(rest, "--reuse-values"):
            out.append((ASK, "--reuse-values replays the previous values onto the new chart: "
                             "ask every time"))
        if not seen.get("--kube-context"):
            out.append((DENY, "pin the context: every helm command carries --kube-context <ctx>"))
        if not (seen.get("-n") or seen.get("--namespace") or seen.get("-A")):
            out.append((DENY, "pin the namespace: every helm command carries -n <ns>"))
    return out


def mcp_kind(tool_name):
    tool = tool_name.rsplit("__", 1)[-1].lower()
    if tool.startswith(MCP_WRITE_PREFIXES):
        return "write"
    if tool.startswith(MCP_READ_PREFIXES):
        return "read"
    return None


def decide_bash(tool_input, gate_open):
    command = tool_input.get("command")
    if not isinstance(command, str):
        raise ValueError("Bash call without a command string")
    out = []
    for prog, args in invocations(command):
        out.extend(pin_decisions(prog, args))
    if not gate_open and classify_command(command) != READ and not bash_scratch_exempt(command):
        if only_unknown_writes(command):
            out.append((ASK, "unclassified - fix the handler in tool-gate.py"))
        else:
            out.append((DENY, REFUSAL))
    if rm_escapes_scratch(command):
        out.append((ASK, "rm names a path outside the scratch root next to a scratch path"))
    return out


def decide_mcp(tool_name, tool_input, gate_open):
    tool = tool_name.rsplit("__", 1)[-1]
    if tool == SLACK_SEND:
        if tool_input.get("thread_ts") and tool_input.get("channel_id") in ALERT_CHANNEL_IDS:
            return []
        return [(ASK, "a Slack message outside the linked alert thread: show the text and ask")]
    if (tool == SLACK_REACT and tool_input.get("channel_id") in ALERT_CHANNEL_IDS
            and tool_input.get("emoji") == ALERT_REACTION):
        return []
    if gate_open:
        return []
    kind = mcp_kind(tool_name)
    if kind == "write":
        return [(DENY, REFUSAL)]
    if kind is None:
        return [(ASK, "unclassified - fix the handler in tool-gate.py")]
    return []


def decide(tool_name, tool_input, gate_open):
    """The strictest decision over every matching row, as (decision, reason) or None."""
    if tool_name == "Bash":
        out = decide_bash(tool_input, gate_open)
    elif tool_name in PATH_FIELD:
        out = []
        if not gate_open and not inside_gate_scratch(tool_input.get(PATH_FIELD[tool_name])):
            out.append((DENY, REFUSAL))
    elif tool_name.startswith("mcp__"):
        out = decide_mcp(tool_name, tool_input, gate_open)
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
            label = classify_command(tool_input["command"])
            updated["description"] = f"{label} · {description}" if description else label
            output["updatedInput"] = updated
        decision = decide(tool_name, tool_input, gate_is_open(payload.get("session_id")))
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
    verdict = f"{decision[0]}: {decision[1]}" if decision else "-"
    if tool_name == "Bash":
        return f"{classify_command(tool_input['command'])}  {verdict}{note}"
    return verdict


def selftest():
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
        (True, "Bash", "kubectl --context X -n Y delete pod p", DENY),
        (True, "Bash", "helm --kube-context X -n Y uninstall r", DENY),
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
        (False, "Bash", "kubectl exec p --context X -n Y -- rm -rf /data", DENY),
        (False, "Bash", "kubectl exec -it p --context X -n Y -- sh", DENY),
        (False, "Bash", "kubectl cp p:/x /tmp/y --context X -n Y", DENY),
        (True, "Bash", "kubectl cp p:/x /tmp/y --context X -n Y", None),
        (False, "Bash", f"git log -1 --output={home}/.claude/lfg-state/abc", DENY),
        (False, "Bash", "git log -1", None),
        (False, "Bash", "git stash", DENY),
        (False, "Bash", "git restore .", DENY),
        (False, "Bash", "git checkout -- .", DENY),
        (False, "Bash", "make test", None),
        (False, "Bash", "make build", DENY),
        (False, "Bash", "git fetch", None),
        (False, "Bash", "git fetch --force", DENY),
        (False, "Bash", "uv sync", DENY),
        (False, "Bash", f"touch {scratch}x", None),
        (False, "Bash", f"rm {scratch}x", None),
        (False, "Bash", f"echo hi > {scratch}x", None),
        (False, "Bash", f"touch {home}/.cache/x", None),
        (False, "Bash", f"touch {home}/.claude/plans/x.md", None),
        (False, "Bash", f"touch {home}/.claude/projects/p/memory/x.md", None),
        (False, "Bash", f"mkdir -p {scratch}d && cp a.txt {scratch}d/", DENY),
        (False, "Bash", f"touch {home}/repos/probe", DENY),
        (False, "Bash", "touch /tmp/probe.md", DENY),
        (False, "Bash", f"touch {scratch}../x", DENY),
        (True, "Bash", f"rm -rf {scratch}x {home}/.cache/x", ASK),
        (True, "Bash", f"rm -rf {scratch}x", None),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", DENY),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --force-conflicts", DENY),
        (False, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", DENY),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --reuse-values", ASK),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y", None),
        (True, "Bash", "helm upgrade r ./c --kube-context X -n Y --dry-run", None),
        (True, "Bash", "git push origin main", DENY),
        (True, "Bash", "git push --dry-run", DENY),
        (True, "Bash", "kubectl config use-context x", DENY),
        (True, "Bash", "kubectx x", DENY),
        (True, "Bash", "kubens x", DENY),
        (True, "Bash", "kubectl label node n atero/user=x --context X", DENY),
        (True, "Bash", "kubectl certificate approve x --context X", DENY),
        (False, "Bash", "kubectl rollout status deploy/x --context X -n Y", None),
        (True, "Bash", "kubectl rollout restart deploy/x --context X -n Y", DENY),
        (True, "Bash", "kubectl apply -f x.yaml --context X -n Y", DENY),
        (False, "Bash", "kubectl apply -f x.yaml --dry-run=server --context X -n Y", None),
        (True, "Bash", "kubectl drain n --context X --ignore-daemonsets", DENY),
        (False, "Bash", "frobnicate --flag", ASK),
        (False, "Bash", "frobnicate | grep x", ASK),
        (False, "Bash", "frobnicate && touch /etc/x", DENY),
        (False, "Bash", "stern x --context X -n Y", None),
        (False, "Bash", "stern x", DENY),
        (False, "Bash", "kubectl --help", None),
        (False, "Bash", "python3 -m pytest tests/", None),
        (False, "Bash", "zsh -ic 'echo $HISTFILE; setopt | grep -i hist'", None),
        (False, "Bash", 'which claude; stat -f "%Sm %N" "$(readlink -f "$(which claude)")" 2>&1', None),
        (False, "Bash", "claude auth status", None),
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
        (False, "Bash", "xh -a u:p http://host/x k=v", DENY),
        (False, "Bash", "xh --verify no 'host/x?y=1'", None),
        (False, "Bash", "kubectl get pods --context X -n 123 > /private/tmp/claude/p", None),
        (False, "Bash", "bash -lc 'touch /etc/x'", DENY),
        (False, "Bash", f"bash {scratch}check.sh", DENY),
        (False, "Bash", f"python3 {scratch}check.py", DENY),
        (True, "Bash", f"python3 {scratch}check.py", None),
        (False, "Bash", f"python3 {os.path.realpath(__file__)} --selftest", None),
        (False, "Write", {"file_path": f"{scratch}a.md"}, None),
        (False, "Write", {"file_path": "/tmp/a.md"}, DENY),
        (False, "Write", {"file_path": f"{home}/.claude/lfg-state/x"}, DENY),
        (False, "Edit", {"file_path": f"{home}/repos/x.py"}, DENY),
        (True, "Edit", {"file_path": f"{home}/repos/x.py"}, None),
        (False, "NotebookEdit", {"notebook_path": f"{scratch}n.ipynb"}, None),
        (False, "NotebookEdit", {"notebook_path": f"{home}/repos/n.ipynb"}, DENY),
        (False, "Write", {}, DENY),
        (False, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": alert, "thread_ts": "1.2", "message": "tl;dr"}, None),
        (False, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": "C0OTHER", "thread_ts": "1.2", "message": "x"}, ASK),
        (True, "mcp__claude_ai_Slack__slack_send_message",
         {"channel_id": alert, "message": "no thread"}, ASK),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": alert, "message_ts": "1.2", "emoji": "claude"}, None),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": alert, "message_ts": "1.2", "emoji": "eyes"}, DENY),
        (False, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": "C0OTHER", "message_ts": "1.2", "emoji": "claude"}, DENY),
        (True, "mcp__claude_ai_Slack__slack_add_reaction",
         {"channel_id": "C0OTHER", "message_ts": "1.2", "emoji": "eyes"}, None),
        (False, "mcp__claude_ai_Slack__slack_read_thread", {"channel_id": alert}, None),
        (False, "mcp__Slack__slack_read_thread", {"channel_id": alert}, None),
        (False, "mcp__claude_ai_Atlassian_Rovo__getConfluencePage", {"pageId": "1"}, None),
        (False, "mcp__data-mcp__live_promql_query", {"query": "up"}, None),
        (False, "mcp__claude_ai_Atlassian_Rovo__createJiraIssue", {}, DENY),
        (True, "mcp__claude_ai_Atlassian_Rovo__createJiraIssue", {}, None),
        (False, "mcp__plugin_plumber-claude_plumber__plumber_dispatch", {}, DENY),
        (False, "mcp__x__frob", {}, ASK),
        (True, "mcp__x__frob", {}, None),
    ]
    failures = 0
    for gate_open, tool_name, tool_input, expected in cases:
        if tool_name == "Bash":
            tool_input = {"command": tool_input}
        got = decide(tool_name, tool_input, gate_open)
        got_kind = got[0] if got else None
        ok = got_kind == expected
        failures += not ok
        shown = tool_input["command"] if tool_name == "Bash" else f"{tool_name} {tool_input}"
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
        # (command, expected label): heredoc bodies are data, never programs
        (f"git commit -q -F - <<'EOF'\nfix: drop; rm -rf {s}x\nEOF", WRITE),
        ("cat <<EOF\nrm -rf /\nEOF", READ),
        ("cat <<EOF\nhello\nEOF\nrm -rf /", DANGER),
        # Process substitution runs its own command.
        ("cat <(rm -rf /etc)", DANGER),
        ("diff <(sort a) <(sort b)", READ),
        ("tee >(rm -rf /etc)", DANGER),
    ]
    for command, expected in label_cases:
        got = classify_command(command)
        ok = got == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} label {command!r} -> {got}"
              + ("" if ok else f" (want {expected})"))
    total = len(cases) + len(payload_cases) + len(strip_cases) + len(label_cases)
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
