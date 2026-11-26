"""What a shell command can change: classify_command rates a whole Bash command as

    🟢 READ    changes nothing
    🟠 WRITE   changes local, recoverable state (files, commits, installs, helm releases)
    🔵 RUNS CODE  a known program running code the rating cannot read: a test run, a Python
                  script
    🟣 UNCLASSIFIED  a program or a line the classifier does not recognise
    🔴 DANGER  destroys data or changes live cluster / remote state

Anything the classifier does not recognise is UNCLASSIFIED, never READ: a wrong purple
costs a glance, a wrong green is the failure the rating exists to prevent. A known
program's handler still rates an argument it does not know as WRITE.

Tools of one person's or one workplace's own are rated by an extension file, named in
~/.config/tkay-tools.json as {"rating_extensions": "<path>"}. With no config, or no key,
the rating is the generic one. Importing this module loads no extension: its caller loads
one, by configure(<config file>) or load_extension(<extension file>). The extension adds
to the tables below and never replaces an entry; every name in it is optional:

    HANDLERS            {program: rate(args)}, args being the words after the program
    GENERIC_VERB_CLIS   {program}: CLIs shaped `tool group... verb`, rated by their verbs
    READ_PROGRAMS       {program}: programs that only read
    PUBLISHING_SCRIPTS  {script file name}: scripts that publish what the rating cannot
                        see, rated DANGER whether run directly or by Python
    SCRIPT_HANDLERS     {script file name: rate(args)}: Python scripts, args being the
                        words after the script
    SCRIPT_OUTPUTS      {script file name: out(args)}: the one local file a script's run
                        writes, or None, for a caller that judges where writes land
    READ_ONLY_SCRIPTS   {path}: Python scripts that change nothing, READ unless Python's
                        -i follows the script with stdin's code

A config or an extension that fails to load - unreadable, a clash with a built-in entry,
a value of the wrong type - leaves every rating UNCLASSIFIED: a personal tool rated
generically could read green.
"""

import contextlib
import importlib.util
import json
import os
import re
import shlex

READ, WRITE, RUNS_CODE, UNCLASSIFIED, DANGER = (
    "🟢 READ", "🟠 WRITE", "🔵 RUNS CODE", "🟣 UNCLASSIFIED", "🔴 DANGER")
# The permission mode a hook payload names for auto mode, where a call is rated only in a
# hook's reason, never in its input.
AUTO_MODE = "auto"
# Code the hook cannot read may write anything, so it outranks a known local write; an unknown
# program is less known still, and neither outranks a known danger.
RANK = {READ: 0, WRITE: 1, RUNS_CODE: 2, UNCLASSIFIED: 3, DANGER: 4}

SEPARATORS = {";", ";;", "|", "||", "&&", "&", "(", ")", "|&"}
REDIRECT_OUT = {">", ">>", "&>", "&>>", ">|"}
# The descriptor digit of `2>&1` or `2>/dev/null`: shlex would lex it as a word of its own.
DESCRIPTOR_RE = re.compile(r"(?<![^\s();|&])\d+(?=[<>])")
HARMLESS_TARGETS = {"/dev/null", "/dev/stderr", "/dev/stdout", "/dev/tty"}

ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Shell words that precede the real program on a segment and carry no rating of their own.
TRANSPARENT = {"do", "then", "else", "elif", "!", "{", "}", "if", "while", "until", "time",
               "exec", "command", "builtin", "nohup", "nice", "env", "stdbuf", "caffeinate"}
# The options of caffeinate that take a value; its other options are flags of their own.
CAFFEINATE_VALUE_OPTS = {"-t", "-w"}
# A segment made only of one of these is loop/branch syntax.
SYNTAX_ONLY = {"done", "fi", "esac", "in", "function", "then", "do", "else", "}", "{"}
# `for p in a b` names variables, not a program: the body is its own segment after `do`.
LOOP_HEADERS = {"for", "case", "select"}

READ_PROGRAMS = {
    "cat", "head", "tail", "less", "more", "wc", "grep", "egrep", "fgrep", "zgrep", "rg", "ag",
    "ack", "fd", "ls", "tree", "stat", "file", "du", "df", "echo", "printf", "true", "false",
    "exit", "return",
    "test", "[", "[[", "which", "whereis", "type", "whoami", "id", "hostname", "uname", "date",
    "pwd", "printenv", "jq", "sort", "uniq", "cut", "tr", "column", "diff", "diff3", "cmp", "comm",
    "md5", "md5sum", "sha1sum", "sha256sum", "shasum", "base64", "xxd", "od", "strings",
    "hexdump", "realpath", "dirname", "basename", "readlink", "seq", "nl", "rev", "paste",
    "fold", "expand", "bc", "dc", "sleep", "cal", "uptime", "ps", "pgrep", "lsof", "netstat",
    "ss", "lsblk", "free", "vmstat", "iostat", "sw_vers", "getconf", "locale", "tty", "history",
    "jobs", "alias", "declare", "typeset", "export", "set", "unset", "setopt", "unsetopt",
    "bindkey", "zstyle", "cd", "pushd", "popd",
    "dirs", "local", "readonly", "shift", "wait", "hash", "umask", "read", "zcat", "gzcat",
    "bzcat", "xzcat", "dig", "nslookup", "host", "ping", "traceroute", "mtr", "whois",
    "journalctl", "kustomize", "mypy", "pyright", "flake8", "pylint", "shellcheck",
    "yamllint", "hadolint", "glow", "bat", "fzf", "tldr", "man", "info", "cksum", "iconv",
    "look", "join", "split", "fmt", "pr", "tac", "expr", "let", "arch", "nproc", "sysctl",
    "ifconfig", "ip", "route", "arp", "ioreg", "system_profiler", "pbpaste", "mdfind",
    "gofmt", "gpg",
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
    "reboot", "halt", "sudo", "doas", "fdisk", "parted", "wipefs", "nvme",
}

# Scripts that push images and move shared registry tags from their own subprocesses, where
# the rating never sees the push: their name is the only thing it can match. The tables
# below that an extension alone fills start empty.
PUBLISHING_SCRIPTS = set()
SCRIPT_HANDLERS = {}
SCRIPT_OUTPUTS = {}
READ_ONLY_SCRIPTS = set()

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

# GOTCHA: an allowlist, because other tar options write outside -C (-P, --index-file, -c with
# -f) or run a program (--to-command, --use-compress-program). -C stays out of the short
# set so a clustered -xC never hides an extract target from the scratch check.
TAR_EXTRACT_SHORT = set("xvfzjJkopm")
TAR_EXTRACT_LONG = {"--extract", "--get", "--directory", "--file", "--gzip", "--bzip2", "--xz",
                    "--zstd", "--verbose", "--keep-old-files", "--no-same-owner",
                    "--no-same-permissions", "--strip-components", "--exclude"}
TAR_STDOUT_SHORT = TAR_EXTRACT_SHORT | {"O"}
TAR_STDOUT_LONG = TAR_EXTRACT_LONG | {"--to-stdout"}

# kubectl verbs that write live cluster state; rollout's status and history only read it.
KUBECTL_LIVE_WRITES = {"apply", "delete", "create", "patch", "edit", "scale", "rollout",
                       "replace", "set", "label", "annotate", "taint", "cordon", "uncordon",
                       "drain", "evict", "expose", "run", "debug", "autoscale", "certificate"}
KUBECTL_ROLLOUT_READS = {"status", "history"}
# kubectl subcommands that never reach a cluster.
KUBECTL_LOCAL = {"config", "kustomize", "completion", "options", "help", "krew"}

KREW_READS = {"list", "search", "info", "version", "help"}

HELM_RELEASE_MOVES = {"uninstall", "delete", "del", "rollback"}
# helm subcommands that never reach a cluster.
HELM_LOCAL = {"template", "lint", "show", "search", "pull", "package", "push", "registry",
              "create", "env", "verify", "repo", "dependency", "plugin", "version",
              "completion", "help"}
# helmfile subcommands that change what runs on the cluster.
HELMFILE_RELEASE_WRITES = {"apply", "sync", "destroy", "delete"}
GIT_CONFIG_VALUE_FLAGS = {"-f", "--file", "--blob", "--default", "--type"}
GIT_CONFIG_READ_SUBCOMMANDS = {"get", "list"}
GIT_SYMBOLIC_REF_READ_FLAGS = {"-q", "--quiet", "--short", "--no-short", "--recurse",
                               "--no-recurse"}
SSH_VALUE_FLAGS = {"-B", "-b", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L", "-l", "-m",
                   "-O", "-o", "-p", "-Q", "-R", "-S", "-W", "-w"}
GIT_CONFIG_WRITE_SUBCOMMANDS = {"set", "unset", "edit", "rename-section", "remove-section"}
# GOTCHA: `clean` stores the object under .git/lfs/objects the way `fetch` fills .git/objects:
# no ref and no work-tree file moves, so it reads like the rest.
GIT_LFS_READ_SUBCOMMANDS = {"ls-files", "env", "status", "version", "help", "clean", "pointer",
                            "fsck", "locks"}

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
HELMFILE_GLOBAL_VALUE_FLAGS = {
    "--kube-context", "-e", "--environment", "-f", "--file", "-n", "--namespace", "-l",
    "--selector", "--state-values-set", "--state-values-file", "-b", "--helm-binary",
    "--log-level", "-c", "--chart",
}


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


HELM_SUBCOMMAND_ALIASES = {"dep": "dependency", "dependencies": "dependency"}


def helm_words(args):
    """helm's arguments with its global flags taken out, and the subcommand among the
    positionals read by its name whichever alias was typed."""
    rest, seen = split_globals(args, HELM_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    if pos:
        pos[0] = HELM_SUBCOMMAND_ALIASES.get(pos[0], pos[0])
    return rest, seen, pos


def generic_verbs(args):
    """CLIs shaped `tool group... verb [flags]`: gcloud, aws, az, argocd, flux."""
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
    # GOTCHA: only the words ahead of the subcommand are git's own. After it, a word shaped
    # like --git-dir= is the subcommand's: archive's -o value, merge-file's -L label.
    while rest and (rest[0] in ("-C", "-c", "--git-dir", "--work-tree", "--no-pager", "-P")
                    or rest[0].startswith(("--git-dir=", "--work-tree="))):
        rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
    return rest


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
               "check-attr", "check-ref-format", "fsck", "verify-commit", "verify-tag",
               "merge-tree"}:
        # merge-tree stores its result as unreachable objects: no ref, index or file moves.
        # GOTCHA: git runs unsandboxed under the managed policy, and `log`/`diff`/`show --output`
        # write a file anywhere, so a read verb with it is a write.
        return WRITE if has_flag(rest, "--output") else READ
    if sub == "merge-file":
        return READ if git_merge_file_writes(rest) == [] else WRITE
    if sub == "symbolic-ref":
        # One name with only these flags reads the ref it points at. Anything else may write:
        # a second name repoints it, and git takes a bundled -qd or an abbreviated --del as a
        # delete.
        flags = [a for a in rest if a.startswith("-")]
        if len(pos) == 1 and all(f in GIT_SYMBOLIC_REF_READ_FLAGS for f in flags):
            return READ
        return WRITE
    if sub == "reflog":
        # Any positional that is not one of these subcommands is a ref to show, or the value of
        # a show option such as `-n 40`.
        if set(pos) & {"expire", "delete", "drop"}:
            return DANGER
        return WRITE if "write" in pos else READ
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
    if verb == "krew":
        return READ if len(pos) > 1 and pos[1] in KREW_READS else WRITE
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
    if verb in KUBECTL_LIVE_WRITES:
        return DANGER
    return WRITE


def classify_helm(args):
    rest, _, pos = helm_words(args)
    if not pos:
        return READ
    sub = pos[0]
    if "$" in sub:
        return DANGER
    if sub in {"list", "ls", "get", "status", "history", "show", "inspect", "template", "lint",
               "search", "env", "version", "verify", "completion", "help", "diff"}:
        return READ
    if sub == "repo":
        return READ if len(pos) > 1 and pos[1] == "list" else WRITE
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
        fields = has_flag(args, "-f", "-F", "--field", "--raw-field", "--form")
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
    if args[0] == "-m" and len(args) > 1:
        if args[1] in ("json.tool", "tomllib"):
            return READ
        if args[1] in ("pytest", "mypy", "pyright", "ruff", "black", "isort", "flake8", "pylint"):
            return classify_program(args[1], args[2:])
        if args[1] == "pip":
            return classify_pip(args[2:])
        return RUNS_CODE
    # The script is read past Python's own flags, so `python3 -u x.py` is rated as x.py.
    script = python_script(args)
    if script is None:
        return RUNS_CODE
    # GOTCHA: Python's -i runs whatever code standard input holds once the script is done,
    # so a read-only script is a read only without it.
    if (os.path.realpath(os.path.expanduser(script)) in READ_ONLY_SCRIPTS
            and not any(a.startswith("-") and not a.startswith("--") and "i" in a
                        for a in args[:args.index(script)])):
        return READ
    name = os.path.basename(script)
    if name in PUBLISHING_SCRIPTS:
        return DANGER
    if name in SCRIPT_HANDLERS:
        return SCRIPT_HANDLERS[name](args[args.index(script) + 1:])
    return RUNS_CODE


def classify_perl(args):
    """perl and ruby: an in-place edit names its target and is a write; anything else runs
    code, as python does."""
    return WRITE if edits_in_place(args) else RUNS_CODE


def classify_pip(args):
    pos = positionals(args)
    if has_flag(args, "--version", "-V") or (pos and pos[0] in ("list", "show", "freeze", "check",
                                                                 "index", "debug", "config",
                                                                 "download", "hash", "inspect")):
        return READ
    return WRITE


# Every global option uv takes a value for, typed before the subcommand or after it: the
# ones `uv --help` lists and the hidden ones uv still reads.
UV_GLOBAL_VALUE_FLAGS = ("--cache-dir", "--color", "--allow-insecure-host", "--directory",
                         "--project", "--config-file", "--python-preference", "--python-fetch",
                         "--preview-features")


# Every option `uv run` takes a value for, written as a separate word: the ones
# `uv run --help` lists and the hidden ones uv still reads.
UV_RUN_VALUE_FLAGS = (
    "--extra", "--no-extra", "--group", "--no-group", "--only-group", "--no-editable-package",
    "--env-file", "-w", "--with", "--with-editable", "--with-requirements", "--package",
    "--python-platform", "--index", "--default-index", "-i", "--index-url", "--extra-index-url",
    "-f", "--find-links", "--index-strategy", "--keyring-provider", "-P", "--upgrade-package",
    "--upgrade-group", "--resolution", "--prerelease", "--prerelease-package", "--fork-strategy",
    "--exclude-newer", "--exclude-newer-package", "--no-sources-package", "--reinstall-package",
    "--link-mode", "-C", "--config-setting", "--config-settings-package",
    "--no-build-isolation-package", "--no-build-package", "--no-binary-package",
    "--refresh-package", "-p", "--python", "--config-settings", "--max-recursion-depth",
) + UV_GLOBAL_VALUE_FLAGS


UV_RUN_SHORT_VALUE_FLAGS = "".join(o[1] for o in UV_RUN_VALUE_FLAGS if not o.startswith("--"))


def uv_short_flags(word):
    """The letters of a bundle of uv's short options up to the first that takes a value, and
    whether that value is the next word: the rest of the bundle is the value otherwise."""
    for j, ch in enumerate(word[1:], 1):
        if ch in UV_RUN_SHORT_VALUE_FLAGS:
            return word[1:j + 1], j == len(word) - 1
    return word[1:], False


def uv_subcommand(args):
    """The index in uv's arguments of its subcommand, past uv's own global options, or None
    when there is none."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in UV_GLOBAL_VALUE_FLAGS else 1
    return i if i < len(args) else None


def uv_run_options(args):
    """uv run's own options, the words between `run` and the command it runs."""
    rest = args[uv_subcommand(args) + 1:]
    i = 0
    while i < len(rest) and rest[i].startswith("-"):
        a = rest[i]
        if a.startswith("--") or a == "-":
            i += 2 if a in UV_RUN_VALUE_FLAGS else 1
        else:
            i += 2 if uv_short_flags(a)[1] else 1
    return rest[:i]


def uv_run_tail(args):
    """The command `uv run` runs, with uv's own options removed."""
    return args[uv_subcommand(args) + 1 + len(uv_run_options(args)):]


def uv_runs(args):
    """True when uv's subcommand is `run`."""
    i = uv_subcommand(args)
    return i is not None and args[i] == "run"


def classify_uv(args):
    i = uv_subcommand(args)
    # Only uv's own options ahead of the subcommand ask for its version: after it, the
    # words are the subcommand's, and after `run` the command's it runs.
    if i is None or has_flag(args[:i], "--version", "-V"):
        return READ
    sub = args[i]
    if sub == "run":
        tail = uv_run_tail(args)
        return classify_words(tail) if tail else WRITE
    if sub == "pip":
        return classify_pip(args[i + 1:])
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
    if sub in ("test", "t") or (sub in ("run", "run-script") and pos[1:2] == ["test"]):
        return RUNS_CODE
    if sub in ("ls", "list", "view", "info", "outdated", "why", "explain", "ping",
               "doctor", "search", "config"):
        return WRITE if sub == "config" and len(pos) > 1 and pos[1] != "get" else READ
    if sub == "audit":
        return WRITE if "fix" in pos else READ
    # A check script passes like a test, but its name never makes it a read: a lint script
    # can run eslint --fix.
    if sub in ("run", "run-script") and len(pos) > 1:
        return RUNS_CODE if pos[1] in ("lint", "typecheck", "type-check", "check") else WRITE
    if sub in ("publish", "unpublish", "deprecate"):
        return DANGER
    return WRITE


def classify_npx(args):
    pos = positionals(args)
    if pos and pos[0] == "tsc":
        return READ if has_flag(args, "--noEmit") else WRITE
    return WRITE


# The go build flags that take a value, so the value is never read as a package.
GO_BUILD_VALUE_FLAGS = {"-C", "-o", "-p", "-asmflags", "-buildmode", "-compiler", "-gccgoflags",
                        "-gcflags", "-installsuffix", "-ldflags", "-mod", "-modfile", "-overlay",
                        "-pgo", "-pkgdir", "-tags", "-toolexec", "-coverpkg", "-covermode"}


def go_build_discards_output(args):
    """True for a go build that writes nothing but the build cache.

    Go keeps the binary only of a build of one main package, or at -o; a build of several
    packages compiles them and discards the result
    (https://pkg.go.dev/cmd/go#hdr-Compile_packages_and_dependencies). Several means two
    distinct package arguments, or the whole module as ./... . -toolexec runs a program of
    its own, so a build that names one is never a read. Go writes nothing at -o /dev/null,
    for one package or several (base.IsNull in cmd/go/internal/work/build.go).
    """
    # Go takes --flag for -flag.
    args = ["-" + a.lstrip("-") if a.startswith("--") and a != "--" else a for a in args]
    if has_flag(args, "-toolexec"):
        return False
    rest, seen = split_globals(args, GO_BUILD_VALUE_FLAGS)
    if has_flag(args, "-o"):
        return seen.get("-o") == os.devnull
    packages = set(positionals(rest)[1:])
    return len(packages) > 1 or "./..." in packages


def go_may_rewrite_module(args):
    """True for a go command run with -mod=mod, which lets any build command rewrite go.mod
    and go.sum (https://go.dev/ref/mod#build-commands). strip_prefix puts a GOFLAGS
    assignment's flags among the arguments."""
    return any(re.fullmatch(r"--?mod=mod", a) for a in args) or any(
        re.fullmatch(r"--?mod", a) and nxt == "mod" for a, nxt in zip(args, args[1:]))


def go_without_dir(args):
    """The go arguments with a leading -C <dir> taken off, so the first positional left is the
    subcommand. Go takes -C only as the first flag
    (https://pkg.go.dev/cmd/go#hdr-Build__test__and_run), in -C dir or -C=dir form, and --C
    for -C."""
    if args and re.fullmatch(r"--?C", args[0]):
        return args[2:]
    if args and re.match(r"--?C=", args[0]):
        return args[1:]
    return args


def classify_go(args):
    args = go_without_dir(args)
    pos = positionals(args)
    if not pos:
        return READ
    sub = pos[0]
    if sub == "env":
        return WRITE if has_flag(args, "-w", "-u") else READ
    if sub == "test":
        return RUNS_CODE
    if sub in ("vet", "list") or (sub == "build" and go_build_discards_output(args)):
        return WRITE if go_may_rewrite_module(args) else READ
    if sub in ("version", "doc", "help", "bug"):
        return READ
    if sub == "mod":
        return READ if len(pos) > 1 and pos[1] in ("graph", "why", "verify") else WRITE
    return WRITE


def classify_cargo(args):
    pos = positionals(args)
    if not pos or has_flag(args, "--version", "-V"):
        return READ
    sub = pos[0]
    if sub in ("test", "bench"):
        return RUNS_CODE
    if sub in ("check", "clippy", "tree", "metadata", "doc", "version", "search",
               "verify-project", "pkgid", "locate-project", "read-manifest"):
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
    return RUNS_CODE if targets == ["test"] else WRITE


def classify_terraform(args):
    pos = positionals(args)
    if not pos:
        return READ
    sub = pos[0]
    nested = pos[1] if len(pos) > 1 else ""
    if sub in ("plan", "show", "validate", "output", "providers", "version", "graph", "console",
               "get"):
        return READ
    if sub == "fmt":
        return classify_formatter(args)
    if sub == "state":
        return READ if nested in ("list", "show", "pull") else DANGER
    if sub == "workspace":
        return READ if nested in ("list", "show") else WRITE
    # test applies every run block's configuration and destroys it after, unless the block
    # says `command = plan`, which the command line does not show.
    if sub in ("apply", "destroy", "import", "taint", "untaint", "force-unlock", "test"):
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
    if pos[0] in ("capturep", "capture-pane"):
        return READ if tmux_capture_prints(args[args.index(pos[0]) + 1:]) else WRITE
    # GOTCHA: tmux accepts a short alias for every command, and the aliases are what gets typed.
    return READ if pos[0] in ("ls", "list-sessions", "lsc", "list-clients", "lsw", "list-windows",
                              "lsp", "list-panes", "lsk", "list-keys", "lscm", "list-commands",
                              "lsb", "list-buffers", "showb", "show-buffer", "show",
                              "show-options", "showw", "show-window-options", "showenv",
                              "show-environment", "showmsgs", "show-messages", "show-hooks",
                              "display", "display-message", "has", "has-session") else WRITE


def tmux_capture_prints(args):
    # Without -p, capture-pane writes the pane into a paste buffer instead of stdout.
    takes_value = False
    for arg in args:
        if takes_value or not arg.startswith("-") or arg.startswith("--"):
            takes_value = False
            continue
        for i, letter in enumerate(arg[1:], start=1):
            if letter == "p":
                return True
            if letter in "bESt":
                takes_value = i == len(arg) - 1
                break
    return False


def classify_ssh(args):
    rest, seen = split_globals(args, SSH_VALUE_FLAGS)
    if has_flag(rest, "-G", "-V"):
        return READ
    pos = positionals(rest)
    if "-O" in seen or len(pos) != 1:
        return WRITE
    dest = pos[0].removeprefix("ssh://")
    user = dest.rpartition("@")[0] if "@" in dest else seen.get("-l", "")
    # A forge's git user has no shell: with no remote command it only prints the auth greeting,
    # while a remote command can mint a token (GitLab's personal_access_token).
    return READ if user == "git" else WRITE


def classify_ssh_add(args):
    return READ if has_flag(args, "-l", "-L") else WRITE


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


# The letters of xargs's short options that take a value, BSD's and GNU's, and GNU's long ones.
XARGS_VALUE_LETTERS = "EIJLPRSadns"
XARGS_VALUE_OPTS = {"--arg-file", "--delimiter", "--max-args", "--max-chars", "--max-lines",
                    "--max-procs", "--process-slot-var"}


def xargs_rest(args):
    """The command xargs runs, past its options as its getopt reads them: short options
    bundle, and one that takes a value ends its word, taking the rest of it or the next."""
    rest = list(args)
    while rest and rest[0].startswith("-"):
        a = rest.pop(0)
        if a == "--":
            break
        if a.startswith("--"):
            if a in XARGS_VALUE_OPTS and rest:
                rest.pop(0)
            continue
        for k, letter in enumerate(a[1:], 2):
            if letter in XARGS_VALUE_LETTERS:
                if k == len(a) and rest:
                    rest.pop(0)
                break
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
    # export writes the plist file it names; only `-` sends it to stdout.
    if pos[:1] == ["export"]:
        return READ if len(pos) == 2 and args[-1:] == ["-"] else WRITE
    return READ if pos and pos[0] in ("read", "read-type", "domains", "find") else WRITE


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


def fuser_kills(args):
    """True when fuser signals the processes it finds: psmisc's -k / --kill. macOS has neither."""
    return any(a == "--kill" or (a.startswith("-") and not a.startswith("--") and "k" in a)
               for a in args)


def classify_fuser(args):
    return DANGER if fuser_kills(args) else READ


HANDLERS = {
    "fuser": classify_fuser,
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
    "gcloud": generic_verbs, "aws": generic_verbs, "az": generic_verbs,
    "argocd": generic_verbs, "flux": generic_verbs, "tsh": generic_verbs, "vault": generic_verbs,
    "tailscale": generic_verbs, "velero": generic_verbs, "istioctl": generic_verbs,
    "cilium": generic_verbs, "linkerd": generic_verbs, "gsutil": generic_verbs,
    "sed": classify_sed, "gsed": classify_sed,
    "awk": classify_awk, "gawk": classify_awk, "mawk": classify_awk, "nawk": classify_awk,
    "python": classify_python, "python3": classify_python,
    "perl": classify_perl, "ruby": classify_perl,
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
    "ssh": classify_ssh,
    "ssh-add": classify_ssh_add,
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
    "pytest": lambda _: RUNS_CODE,
}

# The rating of a program no table knows; `unknown_programs_as` changes it for a block.
_unknown_level = UNCLASSIFIED


@contextlib.contextmanager
def unknown_programs_as(level):
    """Rate a program no table knows at `level` inside the block: READ shows whether only
    such programs keep a command from being a read."""
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
    # python3.N is the same interpreter as python3, as the script scan already reads it.
    if PYTHON_RE.fullmatch(prog):
        return classify_python(args)
    if prog in READ_PROGRAMS:
        return READ
    if prog in WRITE_PROGRAMS:
        return WRITE
    return _unknown_level


# The long options of env that take a value, and the letters of its short ones that do;
# -S's value is the command line itself.
ENV_VALUE_OPTS = {"--unset", "--chdir"}
ENV_VALUE_LETTERS = "uCPS"


def env_options_split(words):
    """env's own options and the words after them, read as env's getopt reads them: short
    options bundle, and -u, -C and -P take their value, attached or next, each listed as an
    option word and a value word; -S's value is split into words that are read again from
    the start, options included; `--` ends them. The -S word and its value are in neither
    list, since the words they stand for are."""
    options, words = [], list(words)
    while words and words[0].startswith("-"):
        a = words.pop(0)
        value = None
        if a.startswith("--"):
            name, eq, rest = a.partition("=")
            if name == "--split-string":
                value = rest if eq else (words.pop(0) if words else "")
            else:
                options.append(a)
                if a == "--":
                    break
                if not eq and a in ENV_VALUE_OPTS and words:
                    options.append(words.pop(0))
                continue
        elif a == "-":
            options.append(a)
        else:
            for k, letter in enumerate(a[1:], 2):
                if letter not in ENV_VALUE_LETTERS:
                    options.append("-" + letter)
                    continue
                arg = a[k:] or (words.pop(0) if words else "")
                if letter == "S":
                    value = arg
                else:
                    options += ["-" + letter, arg]
                break
        if value is not None:
            try:
                words = shlex.split(value) + words
            except ValueError:
                words = [value] + words
    return options, words


def split_prefix(words):
    """The words ahead of the program and the words from the program on: env assignments,
    transparent wrappers with their options, and `timeout <args>`, with an env -S value split
    into the words it stands for, and GOFLAGS kept for a go command."""
    prefix, words = [], list(words)
    goflags = []
    # GOTCHA: shlex leaves a bare `$` behind when nested quotes split `$(...)` apart.
    while words and (ENV_ASSIGN_RE.match(words[0]) or words[0] in TRANSPARENT or words[0] == "$"):
        wrapper = words.pop(0)
        prefix.append(wrapper)
        if wrapper.startswith("GOFLAGS="):
            goflags = wrapper.split("=", 1)[1].split()
        if wrapper == "caffeinate":
            while words and words[0].startswith("-"):
                n = 2 if words[0] in CAFFEINATE_VALUE_OPTS else 1
                prefix, words = prefix + words[:n], words[n:]
        if wrapper == "env":
            options, words = env_options_split(words)
            prefix = prefix + options
    if words and words[0] == "timeout":
        prefix.append(words.pop(0))
        while words and (words[0].startswith("-") or re.match(r"^\d+[smhd]?$", words[0])):
            prefix.append(words.pop(0))
    while words and words[0] in SYNTAX_ONLY:
        prefix.append(words.pop(0))
    # Go reads GOFLAGS as flags given before its own, so they are judged as arguments.
    if goflags and words and program_of(words) == "go":
        words = words[:1] + goflags + words[1:]
    return prefix, words


def strip_prefix(words):
    """Drop env assignments, transparent wrappers and `timeout <args>` ahead of the program,
    keeping GOFLAGS for a go command."""
    return split_prefix(words)[1]


def program_of(words):
    return words[0].rsplit("/", 1)[-1]


# A non-empty PYTHON* variable, as assigned or exported.
PYTHON_ENV_ASSIGN_RE = re.compile(r"PYTHON[A-Z0-9_]*=.")


def exports_python_env(command):
    """True when the command exports a non-empty PYTHON* variable, which reaches every Python
    run after it as an assignment ahead of it does."""
    for line in command_lines(command):
        try:
            segments, _ = split_line(line)
        except ValueError:
            continue
        for segment in segments:
            words = strip_prefix(segment)
            if words and program_of(words) == "export" and any(
                    PYTHON_ENV_ASSIGN_RE.match(w) for w in words[1:]):
                return True
    return False


def classify_words(words):
    prefix, words = split_prefix(words)
    if not words:
        return READ
    prog = program_of(words)
    if prog in LOOP_HEADERS:
        return READ
    level = classify_program(prog, words[1:])
    # env's -P finds the program on a path the command names, so any file can run.
    if "env" in prefix and "-P" in prefix[prefix.index("env"):]:
        level = worst(level, RUNS_CODE)
    # GOTCHA: Python reads its PYTHON* variables before any script: PYTHONPATH shadows a module
    # it imports and PYTHONUSERBASE adds .pth files it runs, so a run rated a read - a read-only
    # script, json.tool - or what a uv run or a shell runs with one set can run any code.
    if level == READ and any(PYTHON_ENV_ASSIGN_RE.match(w) for w in prefix):
        return RUNS_CODE
    return level


def worst(*levels):
    return max(levels, key=lambda level: RANK[level])


def split_line(line):
    """Split one shell line into its command segments and its output-redirect targets."""
    segments, targets, _, _ = parse_line(line)
    return segments, targets


SHLEX_PUNCTUATION = set("();<>|&")


def split_closing_paren(tok):
    """A shlex token split so a leading `)` stands alone: `);` is `)` then `;`.

    GOTCHA: shlex with punctuation_chars glues adjacent punctuation into one token, so the
    `)` closing `$(ls);` arrives as `);`, which is neither a `)` nor a separator: the
    substitution would never close, and every command after it would read as its argument.
    """
    if len(tok) > 1 and tok[0] == ")" and set(tok) <= SHLEX_PUNCTUATION:
        return [")"] + split_closing_paren(tok[1:])
    return [tok]


def parse_line(line):
    """split_line's segments and targets, for each segment whether it runs apart from
    the line's shell: inside parentheses or a substitution, in a pipeline or in the
    background, where the shell may give it a process of its own; and for each target
    the index of the segment it belongs to, len(segments) for one past the last."""
    lexer = shlex.shlex(DESCRIPTOR_RE.sub("", line), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    tokens = [part for tok in lexer for part in split_closing_paren(tok)]
    segments, targets, apart, segment, target_at = [], [], [], [], []
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
                target_at.append(len(segments))
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
    return segments, targets, apart, target_at


def classify_line(line):
    segments, targets = split_line(line)
    level = WRITE if any(t not in HARMLESS_TARGETS for t in targets) else READ
    for segment in segments:
        level = worst(level, classify_words(segment))
    return level


def command_lines(command):
    """The command's logical lines, heredoc bodies cut out.

    A newline inside quotes, or escaped by a backslash, ends no line: a `python3 -c` body
    over several lines and a `\\`-continued command are one line each. A backtick pair
    is a substitution: turned into `$(...)`, its commands run apart.
    """
    text = without_heredoc_bodies(command).split("`")
    text = "".join(part + ("$(" if n % 2 == 0 else ")") for n, part in enumerate(text[:-1])) \
        + text[-1]
    for line in logical_lines(text):
        if line.strip() and not line.strip().startswith("#"):
            yield line


def logical_lines(text):
    """text split at the newlines the shell takes as line ends.

    A newline inside quotes is part of its line. A backslash before a newline outside
    single quotes joins the two lines, and both characters are dropped as the shell drops
    them, so the word after the join parses as the word it is. A comment runs to its
    newline whatever quotes it holds, as in the shell.
    """
    lines, pieces, quote = [], [], None
    start = i = 0
    while i < len(text):
        c = text[i]
        if c == "#" and not quote and (i == 0 or text[i - 1] in " \t;&|()\n"):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        if c == "\\" and quote != "'" and i + 1 < len(text):
            if text[i + 1] == "\n":
                pieces.append(text[start:i])
                start = i + 2
            i += 2
            continue
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == "\n":
            pieces.append(text[start:i])
            lines.append("".join(pieces))
            pieces, start = [], i + 1
        i += 1
    pieces.append(text[start:])
    lines.append("".join(pieces))
    return lines


def classify_command(command):
    if extension_error is not None:
        return UNCLASSIFIED
    level = READ
    for line in command_lines(command):
        try:
            line_level = classify_line(line)
        except ValueError:
            line_level = UNCLASSIFIED
        level = worst(level, line_level)
    if level == READ and exports_python_env(command):
        return RUNS_CODE
    return level


def invocations(command):
    """Every program invocation in a command, nested ones included, as (program, args)."""
    for line in command_lines(command):
        try:
            segments, _, _, _ = parse_line(line)
        except ValueError:
            continue
        for segment in segments:
            yield from invocations_in(segment)


def invocations_in(words):
    """The invocation one segment's words make, then each one it runs: a `bash -c` body,
    the command `xargs` runs, a `find -exec`."""
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


def uv_run_invocations(prog, args):
    """prog and args, then, for a `uv run`, every invocation of the command it runs."""
    yield prog, args
    if prog == "uv" and uv_runs(args):
        tail = uv_run_tail(args)
        if tail:
            for inner_prog, inner_args in invocations_in(tail):
                yield from uv_run_invocations(inner_prog, inner_args)


# A statement of its own, ending the way the shell ends one, whose value is an absolute path
# holding nothing the shell expands: no quote, no `$`, no backtick, no glob, no `~`.
ASSIGNED_PATH_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)=(/[A-Za-z0-9_./+@%:,-]*)\s*(?:;|&&|\n)\s*")


def with_assigned_path(command):
    """The command with the path its first statement assigns to a variable written in
    place of every `$NAME` and `${NAME}` after it, or the command as it is.

    The shell puts that path wherever the variable stands, so a check judges the command
    the shell runs. Only when it is sure: the name recurs nowhere but as the variable - not
    reassigned, exported, read or looped over - and no single quote is in the command,
    since inside one the shell expands nothing.
    """
    m = ASSIGNED_PATH_RE.match(command)
    if not m:
        return command
    name, path, rest = m.group(1), m.group(2), command[m.end():]
    if "'" in rest or re.search(rf"(?<![$A-Za-z0-9_{{]){name}(?![A-Za-z0-9_])", rest):
        return command
    # The assignment stays: a variable the shell itself reads, HOME among them, changes
    # how the rest of the command runs, and the checks that know it look for the name.
    return command[:m.end()] + re.sub(rf"\$\{{{name}\}}|\${name}(?![A-Za-z0-9_])", path, rest)


def edits_in_place(args):
    return any(a.startswith("--in-place") or (a[:1] == "-" and a[1:2] != "-" and "i" in a[1:])
               for a in args)


TOP_LEVEL_SEPARATORS = ("&&", "||", ";", "|", "&", "\n")


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


PYTHON_RE = re.compile(r"python(?:3(?:\.\d+)?)?")

GIT_MERGE_FILE_VALUE_FLAGS = {"-L", "--diff-algorithm", "--marker-size"}
# GOTCHA: git also takes an abbreviated long option (--no-std) and a bundle of short ones
# (-qL <label>), so a flag outside these two sets is held unread, never skipped.
GIT_MERGE_FILE_FLAGS = {"-p", "--stdout", "--no-stdout", "-q", "--quiet", "--no-quiet",
                        "--diff3", "--no-diff3", "--zdiff3", "--no-zdiff3", "--ours",
                        "--no-ours", "--theirs", "--no-theirs", "--union", "--no-union",
                        "--object-id", "--no-object-id", "--no-marker-size"}


def last_switch(flags, on, off):
    """Whether the last of `flags` found in `on` or `off` is in `on`."""
    state = False
    for f in flags:
        state = True if f in on else False if f in off else state
    return state


def git_merge_file_writes(rest):
    """What `git merge-file <rest>` writes: [<current>] when it overwrites that file, [] when
    it prints the merge, None when it writes the object store or its words cannot be read."""
    words, _ = split_globals(rest, GIT_MERGE_FILE_VALUE_FLAGS)
    cut = words.index("--") if "--" in words else len(words)
    flags = [w for w in words[:cut] if w.startswith("-")]
    paths = [w for w in words[:cut] if not w.startswith("-")] + words[cut + 1:]
    if len(paths) != 3 or any(f not in GIT_MERGE_FILE_FLAGS for f in flags):
        return None
    if last_switch(flags, {"--object-id"}, {"--no-object-id"}):
        return None
    return [] if last_switch(flags, {"-p", "--stdout"}, {"--no-stdout"}) else paths[:1]


PYTHON_VALUE_LONG_FLAGS = {"--check-hash-based-pycs"}


def python_run(args):
    """What a Python invocation runs, past Python's own flags: ("script", <path>), or
    ("module", <name>, <letters>) for -m, with the letters among I, P and E given before
    it, which decide where Python looks for the module. None for -c, a script read from
    standard input, or nothing."""
    letters = set()
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            return ("script", args[i + 1]) if i + 1 < len(args) else None
        if a == "-" or not a.startswith("-"):
            return None if a == "-" else ("script", a)
        if a.startswith("--"):
            i += 2 if a in PYTHON_VALUE_LONG_FLAGS else 1
            continue
        # A bundle of short flags: -c and -m end Python's options, -m with the module as the
        # rest of the word or the next word; -W and -X take their value the same way.
        for j, ch in enumerate(a[1:], 1):
            if ch == "c":
                return None
            if ch == "m":
                name = a[j + 1:] or (args[i + 1] if i + 1 < len(args) else "")
                return ("module", name, frozenset(letters)) if name else None
            if ch in "IPE":
                letters.add(ch)
            if ch in "WX":
                i += 1 if a[j + 1:] else 2
                break
        else:
            i += 1
    return None


def python_script(args):
    """The script file a Python invocation runs, past Python's own flags, or None."""
    run = python_run(args)
    return run[1] if run and run[0] == "script" else None


# ----- the extension ------------------------------------------------------------------

CONFIG_PATH = os.path.expanduser("~/.config/tkay-tools.json")
CONFIG_KEY = "rating_extensions"

# Why the configured extension failed to load, or None; while it is set, every rating is
# UNCLASSIFIED.
extension_error = None

# The tables an extension adds to, each put back to its generic entries before one loads.
_EXTENDED = {"HANDLERS": HANDLERS, "READ_PROGRAMS": READ_PROGRAMS,
             "PUBLISHING_SCRIPTS": PUBLISHING_SCRIPTS, "SCRIPT_HANDLERS": SCRIPT_HANDLERS,
             "SCRIPT_OUTPUTS": SCRIPT_OUTPUTS, "READ_ONLY_SCRIPTS": READ_ONLY_SCRIPTS}
_GENERIC = {name: table.copy() for name, table in _EXTENDED.items()}


def load_extension(path):
    """Rate with the generic tables plus the extension at path, or the generic tables alone
    when path is None. Raises when the extension fails to load, leaving the generic
    tables."""
    global extension_error
    extension_error = None
    for name, table in _EXTENDED.items():
        table.clear()
        table.update(_GENERIC[name])
    if path is not None:
        _merge(_load(path))


def configure(config_path):
    """Rate with the generic tables plus the extension the config file names: the generic
    tables alone when the file or its key is missing, and every rating UNCLASSIFIED when
    the config or the extension fails to load."""
    global extension_error
    load_extension(None)
    try:
        load_extension(_extension_path(config_path))
    except Exception as exc:
        extension_error = f"{type(exc).__name__}: {exc}"


def _extension_path(config_path):
    try:
        with open(config_path) as f:
            config = json.load(f)
    except FileNotFoundError:
        return None
    path = config.get(CONFIG_KEY)
    if path is None:
        return None
    if not isinstance(path, str):
        raise TypeError(f"{CONFIG_KEY} in {config_path} is not a path")
    return os.path.expanduser(path)


def _load(path):
    spec = importlib.util.spec_from_file_location("rating_extensions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _names(module, attr):
    value = getattr(module, attr, set())
    if not isinstance(value, (set, frozenset)) or not all(isinstance(v, str) for v in value):
        raise TypeError(f"{attr} is not a set of names")
    return set(value)


def _callables(module, attr):
    value = getattr(module, attr, {})
    if not isinstance(value, dict) or not all(
            isinstance(k, str) and callable(v) for k, v in value.items()):
        raise TypeError(f"{attr} is not a dict of names to functions")
    return dict(value)


def _merge(module):
    """Add the extension's entries to the tables, all or none: one that names a program the
    generic tables already rate is refused, so an extension only ever adds."""
    handlers = _callables(module, "HANDLERS")
    handlers.update(dict.fromkeys(_names(module, "GENERIC_VERB_CLIS"), generic_verbs))
    read_programs = _names(module, "READ_PROGRAMS")
    known = set(HANDLERS) | READ_PROGRAMS | WRITE_PROGRAMS | DANGER_PROGRAMS
    clash = ((set(handlers) | read_programs) & known) | (set(handlers) & read_programs)
    if clash:
        raise ValueError(f"rates programs already rated: {', '.join(sorted(clash))}")
    publishing = _names(module, "PUBLISHING_SCRIPTS")
    script_handlers = _callables(module, "SCRIPT_HANDLERS")
    script_outputs = _callables(module, "SCRIPT_OUTPUTS")
    read_only = {os.path.realpath(os.path.expanduser(p))
                 for p in _names(module, "READ_ONLY_SCRIPTS")}
    HANDLERS.update(handlers)
    READ_PROGRAMS.update(read_programs)
    PUBLISHING_SCRIPTS.update(publishing)
    SCRIPT_HANDLERS.update(script_handlers)
    SCRIPT_OUTPUTS.update(script_outputs)
    READ_ONLY_SCRIPTS.update(read_only)
