---
name: tkay-cluster-ops
description: My rules for operations that change a cluster - a helm upgrade of a live release, a field-manager conflict, a node label, and taking my deployments out of a cell or off a node - what I decide myself, what you ask me first, and how you report. Use when running helm install/upgrade on an existing release, when a server-side apply hits a field-manager conflict, when asked to take down / remove / drain everything I own in a namespace before a cluster is destroyed or a node is drained, and whenever a node label would have to be added, changed or removed to make something schedule.
---

# Cluster operations

This skill holds my rules for the operations that change a cluster: what is
mine to decide, and how you work through them with me. Two rules hold
throughout.

**Every command that reaches a cluster names its target.** Read
`references/pinning.md` before the first command that reaches a cluster: the
flags per tool, the command shapes that run without a prompt, and what to do
when I did not name the cluster or the namespace.

**Every workload I deploy lands in my cell.** Read `references/cells.md`
before any install or upgrade: how a cell is named and how mine is found,
the checks before an install, and what to do when the namespace is not
mine.

## Upgrading a live release

**A release the backoffice installed is never upgraded from here.** When its
objects' field managers include `worker`, offer me the change as a backoffice
change, never as `helm upgrade`, `helm install`, `kubectl apply` or
`kubectl patch`: any of those breaks the backoffice's next deploy of it. If I
ask for one anyway, say this before anything else.

**The chart the release runs is the default, not my local tree.** When a
render of the local tree differs from it beyond the change I asked for, say so
and ask which chart to use.

**Ask me whether `--reuse-values` or `--reset-then-reuse-values` is wanted - do
not decide it yourself.**

**Tell me every field the upgrade changes**, not only the one I asked for.

**`--force-conflicts` runs only when my message says, in plain words, that you
may run it this time - otherwise show me the command and let me decide.** The
permission covers that one command in that one message. When you offer it, say
what it does to the backoffice's next deploy, and offer the alternative: the
change through the backoffice.

## Nodes and their labels

**Moving a node into or out of my cell is mine to make**, in the backoffice.

**`kubectl label node` runs only when my message says, in plain words, that you
may run that label change this time.** Not on your own initiative to claim a
node by giving it a cell's `dedicated` value, to free one by removing it, to
"correct" a label that looks wrong, as the last step of a teardown, because I
have said the node is mine, or because the label is the single thing standing
between a Pending pod and a running one. The permission covers that one
command in that one message. Without my words, print the exact command and
suggest it as `! <command>` so it runs in my session. A wrong namespace costs
me one redeploy; a wrong node label moves other people's workloads.

When a label is missing, stale or pointing at someone else, **say so plainly
and tell me where it is fixed** - that is the whole deliverable. Do not fix it
and mention it afterwards.

## Removing myself from a cell

When I say a cluster is being drained or destroyed, or ask you to take my
deployments down - or the previous owner's, in a cell I took over - the target
is **nothing of mine running in the namespace** - not "the helm releases are
gone". Nothing running, nothing pending, nothing holding a GPU.

**A teardown removes what runs. It never removes what stores, and never the
namespace.** PVCs, secrets, configmaps and the namespace itself stay unless I
ask for them by name, in that message - they are what the next round rebuilds
from, and re-copying pull secrets into a fresh namespace is a tax I pay for
nothing. Report them, hand me the command if you think one is warranted, and
stop there. Naming them in the final message is the deliverable; folding them
into a namespace delete because it sweeps them all at once is not.

### Never hardcode the node - discover it every time

I move between nodes constantly, so a node name from an earlier session is
worthless. Start by finding what is mine right now:

kubectl get nodes --context <ctx> -L dedicated,cell-display-name,crusoe-ai.managed-ai.inference.node-purpose

My nodes are the ones whose `dedicated` value is my cell's namespace - the
namespace I told you. If I did not name one, ask; never pick a cell because its
display name looks like mine.

### Four lists before anything runs

Before proposing a teardown, give me four lists: what one `helm uninstall`
takes, what the backoffice installed and so comes down through the
backoffice, what is still running that neither owns and so needs
`kubectl delete`, and what is left standing on purpose: the cell's own
components, storage, config, the namespace.

### Batch it - not one command per object

One `helm uninstall` with every release name, and a second, batched
`kubectl delete` only when something hand-applied is still running - never for
storage, config or the namespace. Each separate invocation is another command I
have to approve or run, and a teardown is the worst possible time to make me
run twenty. A model the backoffice deployed is in neither command: it comes
down through the backoffice.

**Each runs only when my message says, in plain words, that you may run that
command this time** - "uninstall them", "delete those". The permission covers
what it names, in the message it is in, not the next uninstall or delete.
Anything short of that - a question, a teardown plan I approved - means print
it and suggest it as `! <command>`.

### Verify with one command and quote the output

kubectl get deployments,statefulsets,daemonsets,cronjobs,jobs,pods,lws --context <ctx> -n <ns>

It must list nothing but the cell's own components - `No resources found`
outside a cell. Pair it with a `helm list --kube-context <ctx> -n <ns>` that
shows none of mine, and show me both - do not tell me it is done without them.

### One more thing

**A refused command does not mean access is gone** - `references/reads.md`
says what to do instead of reporting the cluster lost.
