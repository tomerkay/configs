# Always pin the context and the namespace - every cluster command, no exceptions

**Every single command that reaches a Kubernetes cluster spells out the context,
and the namespace for anything namespaced, explicitly, in the command itself.**
A cluster-scoped read - nodes, CRDs - carries the context alone. Read-only or mutating, one-off or inside a loop, typed by you or emitted
by a script you wrote, whatever else is allowed. No command is too small, too harmless or too read-only for this rule.

**Why it is absolute:** I switch contexts constantly. The current context is
whatever I last pointed at, in another terminal, for another cluster - so an
unpinned command is a command aimed at a cluster nobody chose. Reading `dev` when I
asked about `prod` sends me chasing a phantom; writing to `prod` when I meant `dev`
is an outage. Same missing flag, both times.

## The flags, per tool

- `kubectl get pods --context <ctx> -n <ns>`
- `helm list --kube-context <ctx> -n <ns>` - helm spells it **`--kube-context`**,
  not `--context`

**Verb first, pin flags after it.** The permission allowlist matches on the
command prefix, so `Bash(kubectl get *)` recognises `kubectl get pods
--context X -n Y` as a read and lets it through, while `kubectl --context X
get pods` matches nothing and prompts. Both tools accept their global flags in
any position, so this costs nothing and is the only ordering that lets a
read-only verb be allowlisted without also allowlisting `delete`.

**One flat command per invocation - no `for`, no `if`, no `$VAR`, no `$(...)`.**
The harness splits a compound command on `;`, `&&`, `|` and newlines and checks
every piece against the allowlist. `for p in a b`, `do`, `done` and
`POD=$(...)` are pieces no rule can ever match, so a loop over pods prompts
every single time however read-only its body is. Three pods to describe means
three `kubectl describe pod <literal-name> --context X -n Y` calls, issued in
parallel. `echo` banners and `| grep` / `| sed -n` / `| tail` are fine - those
pieces are auto-allowed.

**No `>` or `>>` either.** A redirect into a file turns an auto-allowed read
(`jq`, `grep`, `kubectl get`) into a write and prompts, and a `$TMPDIR` path the
harness cannot resolve prompts on its own. Pipe into the next command instead.

**No inline interpreter either.** `| python3 -c "..."` is arbitrary code to the
harness and prompts every time, whatever it computes. Slice output with
`-o jsonpath=`, `-o custom-columns=` or `| jq` - all three pass without a
prompt and cover everything an investigation needs.
- **Any other tool that speaks to a cluster** - `stern`, `k9s`, `kubectl` plugins,
  `argocd`, `flux`, `helmfile`, a wrapper alias like `k` - takes that tool's
  equivalent flags. If you do not know them, look them up or ask me. "That tool has
  no way to pin it" is only acceptable after you actually checked.
- `-A` / `--all-namespaces` is a deliberate choice, never an escape from `-n`. Use
  it only when I asked for a cluster-wide view, and pin `--context` regardless.

## The loopholes that are not loopholes

- **`kubectl config current-context` is not permission to omit the flag.** Neither
  is my having named the cluster three messages ago, nor an earlier command in this
  session having worked. Every invocation carries its own flags.
- **Do not "set" the target instead of flagging it** - no `kubectl config
  use-context`, no `kubens`, no exporting `KUBECONFIG`. That is relying on ambient
  state with extra steps, and it mutates my environment on top. A switch I ask
  for in words is a change to my environment, and the next command still
  carries its flags.
- **Nesting exempts nothing.** A cluster command inside a pipeline, a `for` loop,
  `xargs`, `bash -c`, a heredoc, a Makefile target or a script you write gets the
  flags on every invocation.
- **`get` / `logs` / `describe` / `--dry-run` are not exempt.** Wrong-cluster reads
  are how wrong conclusions get made, and I act on your conclusions.

## If I did not name the cluster and the namespace

For a read, derive them from an authoritative source and name the source in
the reply: the deploy config that owns the cluster, the record that owns the
namespace, or what I named earlier in the session. Derived means
looked up, never chosen as the most plausible of several: with no such source,
or with two environments the question does not pick between, ask and wait. A
context missing from my kubeconfig is asked for before it is added. For a
mutation, ask every time whatever the source - no go-ahead is a licence to
guess which cluster.

## If you catch yourself without the flags

About to run an unpinned cluster command: **stop and add them**, derived or
asked for per the section above. Already ran one: say so in one sentence,
tell me which context it actually hit, and treat every conclusion drawn from
it as unverified until you re-run it pinned.
