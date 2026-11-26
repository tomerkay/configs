#!/usr/bin/env python3
"""The rating's cases: what command_parser rates a Bash command, with no extension, with
one, and with one that fails to load, what rate.py hands back to Claude Code, and that
only rate.py loads the extension the config names.

    python3 test_rate.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import command_parser  # noqa: E402
import rate  # noqa: E402
from command_parser import DANGER, READ, RUNS_CODE, UNCLASSIFIED, WRITE  # noqa: E402

# A path in the harness scratch root, which some cases write to; the rating never reads it.
s = scratch = "/private/tmp/claude/"

# (command, expected rating) with no extension loaded
GENERIC_CASES = [
    # (command, expected rating): heredoc bodies are data, never programs
    (f"git commit -q -F - <<'EOF'\nfix: drop; rm -rf {s}x\nEOF", WRITE),
    ("cat <<EOF\nrm -rf /\nEOF", READ),
    ("cat <<EOF\nhello\nEOF\nrm -rf /", DANGER),
    # caffeinate's options are not the program it runs.
    ("caffeinate -i go vet ./x", READ),
    ("caffeinate -dims -t 600 rm -rf /etc", DANGER),
    ("caffeinate -i -w 123", READ),
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
    # A substitution closed right before an operator still ends there.
    ("echo $(ls); rm -rf /etc", DANGER),
    ("echo $(ls)&&rm -rf /etc", DANGER),
    ("echo $(ls)|rm -rf /etc", DANGER),
    ("echo `ls`; rm -rf /etc", DANGER),
    ("for f in $(ls); do rm -rf /etc; done", DANGER),
    ("echo $(ls); ls", READ),
    # Leaving the shell or a function changes nothing, so a chain is rated by its work.
    ("exit 1", READ),
    ("return 0", READ),
    ("cp a /x/b || exit 1", WRITE),
    ("glab mr update 3 --description-file d.md", DANGER),
    ('echo "a\nb"', READ),
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
    ("glab api projects/p/uploads --form file=@f.png", DANGER),
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
    ("gh api -X PATCH repos/o/r/pulls/1 -f body=x", WRITE),
    # go env changes Go's user config only with -w or -u.
    ("go env GOPATH", READ),
    ("go env -w GOFLAGS=-mod=mod", WRITE),
    ("go env -u GOFLAGS", WRITE),
    # defaults export writes a file unless it sends the plist to stdout.
    ("defaults export com.apple.dock -", READ),
    ("defaults export com.apple.dock a.plist", WRITE),
    # go build keeps a binary only for one main package or at -o.
    ("go build ./...", READ),
    ("go build -tags scaling_test ./...", READ),
    ("go build ./cmd/a ./cmd/b", READ),
    ("go build --tags x ./cmd/a", WRITE),
    ("go build ./cmd/a ./cmd/a", WRITE),
    ("go build ./cmd/a", WRITE),
    ("go build", WRITE),
    ("go build -o /x/out ./...", WRITE),
    ("go build -toolexec /x/t ./...", WRITE),
    # Go writes nothing at -o /dev/null, for one package or several.
    ("go build -o /dev/null ./cmd/a", READ),
    ("go build -o=/dev/null ./...", READ),
    ("go -C /x build --o /dev/null ./cmd/a", READ),
    ("go build -o /dev/null -o /x/out ./cmd/a", WRITE),
    ("go build -o /dev/null -toolexec /x/t ./cmd/a", WRITE),
    # -mod=mod, as a flag or in GOFLAGS, lets a build command rewrite go.mod and go.sum.
    ("go vet ./...", READ),
    ("go vet -mod=mod ./...", WRITE),
    ("go build -mod mod ./...", WRITE),
    ("GOFLAGS=-mod=mod go vet ./...", WRITE),
    ("GOFLAGS='-tags=x -mod=mod' go list ./...", WRITE),
    ("GOFLAGS=-mod=readonly go vet ./...", READ),
    # A test run or a script runs code the hook cannot read: above a known write, below
    # an unknown program.
    ("go test ./pkg/foo", RUNS_CODE),
    ("cargo test name", RUNS_CODE),
    ("cargo bench", RUNS_CODE),
    ("pytest tests/test_x.py", RUNS_CODE),
    ("pytest --version", READ),
    ("python3 -m pytest -q", RUNS_CODE),
    ("python3 -m unittest", RUNS_CODE),
    ("uv run pytest -q", RUNS_CODE),
    ("uv run --group dev pytest", RUNS_CODE),
    ("uv --color never run pytest", RUNS_CODE),
    ("uv --cache-dir c tree", READ),
    ("uv run sed -i s/a/b/ f --version", WRITE),
    ("uv sync -V", WRITE),
    ("uv --version", READ),
    ("uv -q -V", READ),
    ("env -i ls", READ),
    ("diff3 -m a base b", READ),
    ("python3.12 x.py", RUNS_CODE),
    ("python3.12 -m json.tool f", READ),
    ("PYTHONUSERBASE=ub python3 -m json.tool f.json", RUNS_CODE),
    ("export PYTHONPATH=", READ),
    ("env -u HOME sed -i s/a/b/ f", WRITE),
    ("env -iu HOME sed -i s/a/b/ f", WRITE),
    ("env -P /x ls", RUNS_CODE),
    ("env -iP/x ls", RUNS_CODE),
    ("env -S '-P /x ls'", RUNS_CODE),
    ("env -S '-i sed -i s/a/b/ f'", WRITE),
    ("env --split-string='sed -i s/a/b/ f'", WRITE),
    ("python3 /x/run.py", RUNS_CODE),
    ("python3 -c 'print(1)'", RUNS_CODE),
    ("perl -e 'print 1'", RUNS_CODE),
    ("ruby -e 'puts 1'", RUNS_CODE),
    ("perl -pi -e s/a/b/ f", WRITE),
    ("cp a b && go test ./x", RUNS_CODE),
    ("make test", RUNS_CODE),
    ("npm test", RUNS_CODE),
    ("pnpm run test", RUNS_CODE),
    ("yarn t", RUNS_CODE),
    ("npm run lint", RUNS_CODE),
    ("yarn run typecheck", RUNS_CODE),
    ("make -n build", READ),
    ("go test ./x && frobnicate", UNCLASSIFIED),
    ("cd /x/src && GOFLAGS=-mod=mod go vet ./... 2>&1 | tail -5; "
     "go test -count=1 -race ./... 2>&1 | tail -20", RUNS_CODE),
    # terraform test creates real infrastructure for its run blocks; plan only reads.
    ("terraform test", DANGER),
    ("tofu test -filter=tests/a.tftest.hcl", DANGER),
    ("terraform plan", READ),
    ("kill 12345", DANGER),
    ("pkill -f temporal", DANGER),
    ("killall temporal", DANGER),
    # fuser only lists the processes holding a file, unless -k makes it signal them.
    ("fuser -cu /x", READ),
    ("fuser -v -n tcp 8080", READ),
    ("fuser -k 8080/tcp", DANGER),
    ("fuser -ki -TERM /x", DANGER),
    ("fuser --kill /x", DANGER),
    # A program the classifier has never met is UNCLASSIFIED: above a known write, below a
    # known danger, and never READ.
    ("frobnicate --all", UNCLASSIFIED),
    ("cp a b && frobnicate", UNCLASSIFIED),
    ("frobnicate && git push", DANGER),
    ("ls && frobnicate", UNCLASSIFIED),
    ("FOO=1 frobnicate", UNCLASSIFIED),
    # A line the lexer cannot parse is UNCLASSIFIED too.
    ("echo 'unterminated", UNCLASSIFIED),
]

# A tool of one person's own: rated only once an extension names it.
PERSONAL_TOOLS = [
    ("acmectl clusters list", UNCLASSIFIED),
    ("acme-view x", UNCLASSIFIED),
    ("python3 /x/report.py fetch --out /x/r.json", RUNS_CODE),
    ("python3 /x/publish_image.py --tag t", RUNS_CODE),
    ("/x/publish_image.py --tag t", UNCLASSIFIED),
    ("python3 -u /x/rating-cli.py 'git status'", RUNS_CODE),
]

EXTENSION = """
from command_parser import DANGER, READ, WRITE, positionals

GENERIC_VERB_CLIS = {"acmectl"}
READ_PROGRAMS = {"acme-view"}
HANDLERS = {"acme": lambda args: READ if positionals(args)[:1] == ["show"] else DANGER}
PUBLISHING_SCRIPTS = {"publish_image.py"}
SCRIPT_HANDLERS = {"report.py": lambda args: WRITE if "--out" in args else READ}
SCRIPT_OUTPUTS = {"report.py": lambda args: args[args.index("--out") + 1] if "--out" in args else None}
READ_ONLY_SCRIPTS = {"/x/rating-cli.py"}
"""

# (command, expected rating) with EXTENSION loaded
EXTENSION_CASES = [
    ("acmectl clusters list", READ),
    ("acmectl clusters delete c", DANGER),
    ("acme-view x", READ),
    ("acme show x", READ),
    ("acme drop x", DANGER),
    ("python3 /x/report.py fetch --out /x/r.json", WRITE),
    (f"python3 /x/report.py fetch --out {scratch}r.json", WRITE),
    ("python3 /x/report.py fetch", READ),
    ("python3 /x/publish_image.py --tag t", DANGER),
    ("uv run /x/publish_image.py --tag t", DANGER),
    ("/x/publish_image.py --tag t", DANGER),
    ("python3.12 publish_image.py", DANGER),
    ("python3 -u publish_image.py", DANGER),
    ("python3 -W ignore publish_image.py --push", DANGER),
    # A read-only script stays a read only while nothing else can run code through Python.
    ("python3 -u /x/rating-cli.py 'git status'", READ),
    ("python3 -u -i /x/rating-cli.py 'git status'", RUNS_CODE),
    ("PYTHONINSPECT=1 python3 /x/rating-cli.py 'git status'", RUNS_CODE),
    ("env PYTHONINSPECT=x python3 /x/rating-cli.py 'git status'", RUNS_CODE),
    ("PYTHONINSPECT= python3 /x/rating-cli.py 'git status'", READ),
    ("PYTHONPATH=pyp python3 /x/rating-cli.py 'git status'", RUNS_CODE),
    ("PYTHONPATH=pyp uv run python3 /x/rating-cli.py 'git status'", RUNS_CODE),
    ("export PYTHONPATH=pyp; python3 /x/rating-cli.py 'git status'", RUNS_CODE),
    # The generic tables still rate what they rated.
    ("git push", DANGER),
    ("ls", READ),
]

# Extensions that fail to load, each leaving every rating UNCLASSIFIED.
BROKEN_EXTENSIONS = {
    "a syntax error": "HANDLERS = {",
    "a program the generic tables rate": "HANDLERS = {'git': lambda args: 'x'}",
    "a read program the generic tables rate": "READ_PROGRAMS = {'rm'}",
    "a program in two tables": "READ_PROGRAMS = {'acme'}\nGENERIC_VERB_CLIS = {'acme'}",
    "a set given as a string": "PUBLISHING_SCRIPTS = 'publish_image.py'",
    "a handler that is no function": "SCRIPT_HANDLERS = {'report.py': 'READ'}",
}

failures = 0


def check(label, got, expected):
    global failures
    ok = got == expected
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {label} -> {got}" + ("" if ok else f" (want {expected})"))


def rate_cases(label, cases):
    for command, expected in cases:
        check(f"{label} {command!r}", command_parser.classify_command(command), expected)


def write(directory, name, text):
    path = os.path.join(directory, name)
    with open(path, "w") as f:
        f.write(text)
    return path


def configure_with(directory, extension_text=None, config_text=None):
    """Configure the parser from a config in directory naming an extension with this text."""
    if config_text is None:
        extension = write(directory, "ext.py", extension_text)
        config_text = json.dumps({command_parser.CONFIG_KEY: extension})
    command_parser.configure(write(directory, "config.json", config_text))


def hook(payload):
    output = rate.rated(payload)
    return output and output["hookSpecificOutput"]["updatedInput"]["description"]


with tempfile.TemporaryDirectory() as tmp:
    command_parser.configure(os.path.join(tmp, "no-config.json"))
    check("no config: no error", command_parser.extension_error, None)
    rate_cases("generic", GENERIC_CASES)
    rate_cases("generic", PERSONAL_TOOLS)
    configure_with(tmp, config_text="{}")
    check("config without the key: no error", command_parser.extension_error, None)
    rate_cases("config without the key", PERSONAL_TOOLS[:1])

    configure_with(tmp, EXTENSION)
    check("extension: no error", command_parser.extension_error, None)
    rate_cases("extension", EXTENSION_CASES)
    check("extension: script output", command_parser.SCRIPT_OUTPUTS["report.py"](
        ["fetch", "--out", "/x/r.json"]), "/x/r.json")

    for label, text in BROKEN_EXTENSIONS.items():
        configure_with(tmp, text)
        check(f"broken, {label}: error kept", command_parser.extension_error is not None, True)
        rate_cases(f"broken, {label}", [("ls", UNCLASSIFIED), ("git status", UNCLASSIFIED)])
        check(f"broken, {label}: nothing merged", command_parser.SCRIPT_HANDLERS, {})
    for label, config in (("config that is no JSON", "{"),
                          ("key that is no path", json.dumps({command_parser.CONFIG_KEY: 1})),
                          ("missing extension file",
                           json.dumps({command_parser.CONFIG_KEY: os.path.join(tmp, "nope.py")}))):
        configure_with(tmp, config_text=config)
        rate_cases(f"broken, {label}", [("ls", UNCLASSIFIED)])

    # A later configure starts from the generic tables again.
    command_parser.configure(os.path.join(tmp, "no-config.json"))
    rate_cases("generic again", [("ls", READ)] + PERSONAL_TOOLS)

    # What the hook hands back: the description opens with the rating, once.
    bash = {"tool_name": "Bash", "session_id": "s"}
    check("hook rates the description", hook({**bash, "permission_mode": "default", "tool_input":
          {"command": "ls", "description": "lists files"}}), f"{READ} · lists files")
    check("hook replaces an old rating", hook({**bash, "tool_input":
          {"command": "rm -rf /x", "description": f"{READ} · deletes x"}}), f"{DANGER} · deletes x")
    check("hook rates an empty description", hook({**bash, "tool_input": {"command": "ls"}}), READ)
    # Auto mode refuses a call whose input changed after its review.
    check("hook leaves auto mode alone", rate.rated({**bash, "permission_mode": "auto",
          "tool_input": {"command": "ls", "description": "d"}}), None)
    check("hook leaves other tools alone", rate.rated({"tool_name": "Read",
          "tool_input": {"file_path": "/x"}}), None)

    def raises(command):
        raise RuntimeError("parser bug")

    saved, rate.classify_command = rate.classify_command, raises
    try:
        check("a parser error rates unclassified", hook({**bash, "tool_input":
              {"command": "ls", "description": "d"}}), f"{UNCLASSIFIED} · d")
    finally:
        rate.classify_command = saved

    # Only the rating hook reads the config: importing the parser runs nothing it names,
    # so a process that loads an extension of its own never runs the configured one.
    home = os.path.join(tmp, "home")
    os.makedirs(os.path.join(home, ".config"))
    ran = os.path.join(tmp, "ran")
    extension = write(tmp, "home-ext.py", f"open({ran!r}, 'w').close()\nREAD_PROGRAMS = {{'acme-view'}}\n")
    write(os.path.join(home, ".config"), "tkay-tools.json",
          json.dumps({command_parser.CONFIG_KEY: extension}))
    child = dict(os.environ, HOME=home, PYTHONDONTWRITEBYTECODE="1")
    here = os.path.dirname(os.path.abspath(__file__))
    imported = subprocess.run(
        [sys.executable, "-c", "import command_parser as p; print(sorted(p.READ_PROGRAMS & {'acme-view'}))"],
        cwd=here, env=child, capture_output=True, text=True)
    check("import loads no extension", (imported.stdout.strip(), os.path.exists(ran)), ("[]", False))
    hooked = subprocess.run(
        [sys.executable, os.path.join(here, "rate.py")], env=child, capture_output=True, text=True,
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "acme-view x", "description": "d"}}))
    check("the hook rates with the configured extension",
          json.loads(hooked.stdout or "{}").get("hookSpecificOutput", {}).get("updatedInput", {}).get("description"),
          f"{READ} · d")

print(f"\n{'all passed' if not failures else f'{failures} failed'}")
sys.exit(1 if failures else 0)
