#!/usr/bin/env python3
"""PreToolUse hook for the Bash tool.

Reads the tool call on stdin, classifies what the command can change, and rewrites the
tool's `description` so the permission dialog opens with the verdict:

    🟢 READ    changes nothing
    🟠 WRITE   changes local, recoverable state (files, commits, installs, helm releases)
    🔴 DANGER  destroys data or changes live cluster / remote state

Anything the classifier does not recognise is WRITE: a wrong orange costs a glance, a
wrong green is the failure this hook exists to prevent.

It also forces a permission prompt for an `rm` that names a scratch path alongside
anything outside the scratch root. The `rm ... /tmp/claude/*` allow rules match on
prefix and their `*` swallows every argument after it, so without this check
`rm -rf /private/tmp/claude/x ~/repos` or `rm -rf /private/tmp/claude/../..` would run
unprompted.
"""

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
    "jobs", "alias", "declare", "typeset", "export", "set", "unset", "cd", "pushd", "popd",
    "dirs", "local", "readonly", "shift", "wait", "hash", "umask", "read", "zcat", "gzcat",
    "bzcat", "xzcat", "dig", "nslookup", "host", "ping", "traceroute", "mtr", "whois", "stern",
    "journalctl", "kustomize", "pytest", "mypy", "pyright", "flake8", "pylint", "shellcheck",
    "yamllint", "hadolint", "glow", "bat", "fzf", "tldr", "man", "info", "cksum", "iconv",
    "look", "join", "split" , "fmt", "pr", "tac", "expr", "let", "arch", "nproc", "sysctl",
    "ifconfig", "ip", "route", "arp", "ioreg", "system_profiler", "pbpaste", "mdfind",
    "gofmt", "helmfile", "glab-ci-view", "wrenchmark-report", "gpg",
}
# `split`, `gpg`, `iconv` write files only with explicit output options the handlers below catch.

WRITE_PROGRAMS = {
    "cp", "mv", "mkdir", "touch", "ln", "install", "patch", "tee", "truncate", "chmod", "chown",
    "chgrp", "zip", "gzip", "gunzip", "bzip2", "xz", "open", "osascript", "code", "vim", "nvim",
    "vi", "nano", "emacs", "ssh", "scp", "sftp", "source", ".", "eval", "claude", "uvx", "pipx",
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


def positionals(args):
    return [a for a in args if not a.startswith("-")]


def has_flag(args, *flags):
    return any(a in flags or any(a.startswith(f + "=") for f in flags) for a in args)


def dry_run(args):
    return any(a == "--dry-run" or (a.startswith("--dry-run=") and a != "--dry-run=none")
               for a in args)


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
        return READ
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
               "add", "commit", "fetch", "pull", "init", "clone", "apply", "notes", "bisect",
               "tag", "rerere", "sparse-checkout", "lfs"}:
        return DANGER if force and sub in ("rebase", "rm", "clone", "fetch", "pull") else WRITE
    return WRITE


def classify_kubectl(args):
    pos = positionals(args)
    if not pos:
        return READ
    verb = pos[0]
    if dry_run(args):
        return READ
    if verb in {"get", "describe", "logs", "log", "top", "explain", "api-resources",
                "api-versions", "version", "cluster-info", "events", "wait", "diff",
                "port-forward", "proxy", "completion", "options", "kustomize", "whoami"}:
        return READ
    if verb == "config":
        return READ if len(pos) > 1 and pos[1] in ("view", "get-contexts", "current-context",
                                                    "get-clusters", "get-users") else WRITE
    if verb == "rollout":
        return READ if len(pos) > 1 and pos[1] in ("status", "history") else DANGER
    if verb == "auth":
        return READ if len(pos) > 1 and pos[1] in ("can-i", "whoami") else WRITE
    if verb == "plugin":
        return READ if len(pos) > 1 and pos[1] == "list" else WRITE
    if verb in {"delete", "drain", "cordon", "uncordon", "taint", "apply", "create", "patch",
                "scale", "replace", "edit", "set", "label", "annotate", "expose", "run",
                "debug", "exec", "cp", "evict", "certificate", "autoscale"}:
        return DANGER
    return WRITE


def classify_helm(args):
    pos = positionals(args)
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
        if dry_run(args):
            return READ
        return DANGER if has_flag(args, "--force", "--force-conflicts") else WRITE
    if sub in ("uninstall", "delete", "del", "rollback"):
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


def classify_curl(args):
    method = http_method(args, "-X", "--request")
    if method == "DELETE":
        return DANGER
    if method not in ("GET", "HEAD", "OPTIONS"):
        return WRITE
    if has_flag(args, "-o", "--output", "-O", "--remote-name", "--remote-name-all", "-T",
                "--upload-file", "-F", "--form", "--form-string", "-d", "--data", "--data-raw",
                "--data-binary", "--data-urlencode", "--data-ascii", "--json"):
        return WRITE
    if any(a.startswith(("-d", "-F", "-T", "-o")) and len(a) > 2 and not a.startswith("--")
           for a in args):
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
    return READ if has_flag(args, "-n", "--dry-run", "--just-print", "-q", "--question",
                            "-p", "--print-data-base") else WRITE


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


def classify_find(args):
    if "-delete" in args:
        return DANGER
    if has_flag(args, "-fprint", "-fprint0", "-fprintf", "-fls"):
        return WRITE
    for i, a in enumerate(args):
        if a in ("-exec", "-execdir", "-ok", "-okdir"):
            sub = args[i + 1:]
            end = next((j for j, w in enumerate(sub) if w in (";", "+")), len(sub))
            return classify_words(sub[:end])
    return READ


def classify_xargs(args):
    rest = list(args)
    while rest and rest[0].startswith("-"):
        takes_value = rest[0] in ("-n", "-P", "-L", "-I", "-d", "-s", "-E", "-a", "-J")
        rest = rest[2:] if takes_value and len(rest[0]) == 2 else rest[1:]
    return classify_words(rest) if rest else READ


def classify_shell(args):
    if has_flag(args, "--version", "-n"):
        return READ
    for i, a in enumerate(args):
        if a == "-c" and i + 1 < len(args):
            return classify_command(args[i + 1])
    return WRITE


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


HANDLERS = {
    "git": classify_git,
    "kubectl": classify_kubectl, "k": classify_kubectl, "oc": classify_kubectl,
    "helm": classify_helm,
    "curl": classify_curl, "http": classify_curl, "https": classify_curl, "xh": classify_curl,
    "wget": classify_wget,
    "gh": classify_gh, "glab": classify_gh,
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
    return WRITE


def classify_words(words):
    words = list(words)
    while words and (ENV_ASSIGN_RE.match(words[0]) or words[0] in TRANSPARENT):
        words = words[1:]
    if words and words[0] == "timeout":
        words = words[1:]
        while words and (words[0].startswith("-") or re.match(r"^\d+[smhd]?$", words[0])):
            words = words[1:]
    if not words:
        return READ
    prog = words[0].rsplit("/", 1)[-1]
    if prog in LOOP_HEADERS:
        return READ
    if prog in SYNTAX_ONLY:
        return classify_words(words[1:]) if len(words) > 1 else READ
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
        elif tok in REDIRECT_OUT:
            targets.append(tokens[i + 1] if i + 1 < len(tokens) else "")
            i += 1
        elif tok in (">&", "<", "<<", "<<<", "<&", "<>"):
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
    for line in command.replace("`", " ; ").splitlines():
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
            while words and (ENV_ASSIGN_RE.match(words[0]) or words[0] in TRANSPARENT):
                words = words[1:]
            if not words or words[0].rsplit("/", 1)[-1] != "rm":
                continue
            paths = rm_paths(words[1:])
            if (any(p.startswith(SCRATCH_PREFIXES) for p in paths)
                    and not all(inside_scratch(p) for p in paths)):
                return True
    return False


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        return
    label = classify_command(command)
    description = LABEL_RE.sub("", tool_input.get("description") or "").strip()
    updated = dict(tool_input)
    updated["description"] = f"{label} · {description}" if description else label
    output = {"hookEventName": "PreToolUse", "updatedInput": updated}
    if rm_escapes_scratch(command):
        output["permissionDecision"] = "ask"
        output["permissionDecisionReason"] = (
            "rm names a path outside the scratch root next to a scratch path")
    json.dump({"hookSpecificOutput": output}, sys.stdout)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for cmd in sys.argv[1:]:
            ask = "  [ASK]" if rm_escapes_scratch(cmd) else ""
            print(f"{classify_command(cmd)}{ask}  {cmd}")
    else:
        main()
