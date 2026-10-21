---
name: tkay-cluster-ops
description: Procedures for helm upgrades against a live release, for tearing the user's deployments out of a cell or off a node, and the rule that node labels are written only on the user's explicit words. Use when running helm install/upgrade on an existing release, when a server-side apply hits a field-manager conflict, when asked to take down / remove / drain everything the user owns in a namespace before a cluster is destroyed or a node is drained, and whenever a node label would have to be added, changed or removed to make something schedule.
---

# Cluster operations

This skill is the *how* for the operations that have real procedure behind
them. Two rules hold throughout.

**Every command that reaches a cluster names its target**: `kubectl <verb> ...
--context <ctx>` plus `-n <ns>` for anything namespaced, `helm <verb> ...
--kube-context <ctx> -n <ns>`. Never
rely on the current context and never switch it with `kubectl config
use-context` - I switch contexts constantly, so the current one is whatever I
last pointed at elsewhere. If I did not name the cluster and namespace: for a
read, take them from an authoritative source - the deploy config that owns the
cluster, the cell record - and say which; with no such source, ask. For
anything that changes the cluster, ask.

**Every workload I deploy lands in my cell.** The dev clusters hand GPU nodes
out as cells: the backoffice moves a node into a cell, and a policy pins every
GPU pod in a cell's namespace to that cell's nodes with
`nodeSelector: dedicated=<namespace>`, and every other pod to the shared CPU
nodes. The deprecated `atero/user` node label is rejected on write and carried
by no node, so a selector on it schedules nothing while looking deployed.
Before any install or upgrade, check that the namespace is a cell of mine and
that the cell has nodes (`kubectl get nodes --context <ctx> -L
dedicated,cell-display-name`). If you do not know which cell is mine, ask -
never infer it from another workload. If the namespace is someone else's cell,
or the cell has no nodes, stop and ask before installing.

**Placement in a cell is the policy's alone.** Admission rejects any pod in a
cell namespace that sets `spec.nodeName`, a node affinity on `dedicated` or one
that matches by field, a toleration for `dedicated`, or - on a pod that requests
no GPU - a `dedicated` node selector. So the rendered manifest carries none of
those: check it for them before an install, and when a chart sets one, drop it
from the values rather than working around the rejection. The one exception is
a per-node agent - a DaemonSet whose pods carry
`crusoe-ai.managed-ai.inference.node-agent: "true"` - which is skipped by those
checks and must instead select its own cell itself, with
`nodeSelector: dedicated=<namespace>`.

## Upgrading a Live Release: Get the Chart the Release Actually Used

**A release data-path installed is never upgraded from here.** Read its field
managers first (the command under "Field-Manager Conflicts"): `worker` among
them means data-path installed it, and the change goes through data-path's
backoffice - offered to me as that change, never run as `helm upgrade`,
`helm install`, `kubectl apply` or `kubectl patch`. Any of those that
succeeds takes the fields it sets from `worker`, and data-path's own next
upgrade then conflicts on every one of them until the backoffice forces them
back, which only its verifiers can. If I ask for one
anyway, say this before anything else. Everything below is for releases that
are mine to upgrade.

**The deployed chart is usually NOT my local working tree.** CI stamps the chart
version from `git describe`, so the local `Chart.yaml` keeps a placeholder
(`0.1.0`) forever and never matches a released version. Compare `helm list`
against the local `Chart.yaml` before anything else. Upgrading from the local
directory smuggles in every unreleased change — different values defaults,
different ConfigMap-mounted source — under what I asked to be a one-value tweak.
So the deployed chart is the default; when a render of the local tree differs
from it beyond the change I asked for, say so and ask which chart to use.

Ways to get the real chart:

- **OCI ref** — the normal one for atero-charts:
  `helm upgrade <release> oci://registry.gitlab.com/crusoeenergy/atero/atero-charts/<chart> --version <version> --kube-context <ctx> -n <ns>`
- **Extract it from the release secret** (`sh.helm.release.v1.<release>.v<n>`:
  base64 → gzip → JSON carrying the chart files) when the registry is
  unreachable.

Before every upgrade:

- `helm get values <release> --kube-context <ctx> -n <ns>` first, then **ASK
  me whether `--reuse-values` is wanted — do not decide it yourself.** It replays my previous user values on
  top of the *new* chart's defaults: a no-op when the release has none, and a
  silent carry-forward of stale values when it does.
- Render with the identical flags (`helm template`, or `helm upgrade --dry-run`
  when `--reuse-values` is in play) and diff it against
  `helm get manifest <release> --kube-context <ctx> -n <ns>`, so you can tell
  me every field that changes — not just the one I asked for.

### Field-Manager Conflicts — `--force-conflicts` Is MY Call

Helm 4 applies server-side as field manager `helm`. A release that data-path
installed is owned by manager **`worker`**, so a helm-CLI upgrade fails on
precisely the fields I asked you to change:

```
Apply failed with 1 conflict: conflict with "worker": .data.config.json
```

That is ownership, not drift — nothing is broken and **a failed upgrade applies
nothing** (it just records a `failed` revision).

Diagnose before reacting:
`kubectl get <obj> --context <ctx> -n <ns> -o jsonpath='{range .metadata.managedFields[*]}manager={.manager} op={.operation} time={.time}{"\n"}{end}'`.
A `worker` timestamp seconds after the install means it was the *installer*, not
a live controller; also check whether a reconciler is even running before
claiming something will revert my change.

**`--force-conflicts` runs only when my message says, in plain words, that you
may run it this time — otherwise show me the command and let me decide.** The
permission covers that one command in that one message. It transfers ownership
of those fields to `helm`, and then data-path's own redeploy applies as
`worker` without force and hits the mirror-image conflict, so forcing trades my
problem for a landmine in the deploy path. Always state that consequence when you offer it, and offer the
alternative: make the change through data-path so `worker` stays the owner.
Patching the object by hand is no alternative - it takes the patched fields
from `worker` the same way, and helm's recorded release goes out of sync on
top.

---

## Getting a Node Into My Cell - Through the Backoffice

A cell and the nodes in it are backoffice state; none of it is done with
`kubectl`.

1. **Create the cell** (New Cell). Turning on "Also use for namespace" names
   the namespace `cell-<name>` instead of a generated id. Neither the namespace
   nor the display name can change after creation, so keep hardware and model
   names out of both - the cell outlives what it runs.
2. **Move a node into it** from the backoffice. The node comes out of whichever
   cell holds it now, so that is a conversation with that cell's owner first,
   and the move is mine to make.
3. **Deploy into the cell's namespace** with no node selector - the policy
   above does the pinning.

Releasing a node is the reverse move, out of my cell in the backoffice.

---

## Never Label a Node on Your Own - Only on My Words

**`kubectl label node` runs only when my message says, in plain words, that you
may run that label change this time.** Not on your own initiative to claim a
node by giving it a cell's `dedicated` value, to free one by removing it, to
"correct" a label that looks wrong, as the last step of a teardown, because I
have said the node is mine, or because the label is the single thing standing
between a Pending pod and a running one. The permission covers that one
command in that one message. Moving a node between cells is a backoffice
action; any other label change without my words, print the exact command and
suggest it as `! <command>` so it runs in my session.

The cell labels are how the fleet is carved up between people, so writing one
does two things at once: it moves a machine between cells, and it retargets
every pinned pod in the cluster at once - somebody else's pods go Pending, with
nothing in any log saying why. A wrong namespace costs me one redeploy; a wrong
node label breaks workloads that were never mine to touch.

Reading labels is free and expected: `kubectl get nodes --context <ctx> -L
dedicated,cell-display-name` as often as you need. When a label is missing,
stale or pointing at someone else, **say so plainly and tell me where it is
fixed** - that is the whole deliverable. Do not fix it and mention it
afterwards.

---

## Removing Myself From a Cell

When I say a cluster is being drained or destroyed, or ask you to take my
deployments down - or the previous owner's, in a cell I took over - the target
is **nothing of mine running in the namespace** - not "the helm releases are
gone". Nothing running, nothing pending, nothing holding a GPU.

**A cell's namespace is not all mine.** The platform installs the cell's own
components into it - an ArgoCD-managed collector, and whatever the backoffice
installs per cell, such as a router or a monitor. Those are the cell, not my
work, and they stay.

**A teardown removes what RUNS. It never removes what STORES, and never the
namespace.** PVCs, secrets, configmaps and the namespace itself stay unless I
ask for them by name, in that message - they are what the next round rebuilds
from, and re-copying pull secrets into a fresh namespace is a tax I pay for
nothing. Report them, hand me the command if you think one is warranted, and
stop there. Deleting a PVC is the one step here that nobody can undo.

### Never hardcode the node - discover it every time

I move between nodes constantly, so a node name from an earlier session is
worthless. Start by finding what is mine right now:

kubectl get nodes --context <ctx> -L dedicated,cell-display-name,crusoe-ai.managed-ai.inference.node-purpose

My nodes are the ones whose `dedicated` value is my cell's namespace - the
namespace I told you. If I did not name one, ask; never pick a cell because its
display name looks like mine.

A cell with no node left in it is the trap that follows: the workload looks
deployed while scheduling nowhere.

### Enumerate before proposing anything

Helm knows about only part of it:

1. `helm list --kube-context <ctx> -n <ns>` - the releases.
2. `kubectl get deployments,statefulsets,daemonsets,jobs,pods,lws --context <ctx> -n <ns>`
   - the truth. Anything here that is not in the helm list was applied by hand,
   and helm will never remove it.
3. Cross-reference ownership with
   `-o custom-columns='NAME:.metadata.name,MANAGED_BY:.metadata.labels.app\.kubernetes\.io/managed-by,RELEASE:.metadata.annotations.meta\.helm\.sh/release-name,OWNER:.metadata.ownerReferences[*].kind'`
4. Name who wrote each top-level object, from its field managers:
   `-o jsonpath='{range .items[*]}{.kind}/{.metadata.name}: {.metadata.managedFields[*].manager}{"\n"}{end}'`.
   `argocd-controller` is the platform's and stays; `worker` is the
   backoffice's, so it comes down through the backoffice; `helm` alone is a
   CLI install, and `helm uninstall` takes it.

**`kubectl get all` is not "all" and will lie to you** - it silently omits
LeaderWorkerSets and every other CRD, plus PDBs and PVCs. Always name the kinds
explicitly, `lws` included.

**`DESIRED 0` on a daemonset does not mean it is gone.** It means no node
currently matches its selector - the object is still there and still needs
deleting. A node being drained or relabelled out from under it produces exactly
this.

Then give me four lists: what one `helm uninstall` takes, what the backoffice
installed and so comes down through the backoffice, what is still RUNNING that
neither owns and so needs `kubectl delete`, and what is left standing on
purpose: the cell's own components, storage, config, the namespace.

### What survives `helm uninstall` - and which half of it you may delete

Still running, so it IS part of the teardown:

- Objects a controller created rather than the chart, such as a
  LeaderWorkerSet's per-replica StatefulSets. If the LWS itself is helm-owned
  the cascade handles them; if it is not, they are a separate delete.
- Hand-applied daemonsets, deployments, jobs and bare pods - these are what is
  holding the GPU the teardown exists to free.

Persists on purpose, so you REPORT it and leave it alone:

- The cell's own platform components, written by `argocd-controller` or by
  the backoffice for the cell rather than for a model.
- StatefulSet `volumeClaimTemplate` PVCs - helm never created them, so it never
  removes them, and they are data.
- Hand-applied services, secrets and configmaps - including any pull secret
  copied into the namespace to make the deploy work in the first place.
- The namespace itself, which is never part of a teardown at all.

Naming those in the final message is the deliverable. Deleting them is not, and
neither is folding them into a namespace delete because it happens to sweep
them all at once.

### Batch it - not one command per object

`helm uninstall` accepts every release name in a single invocation, and so does
`kubectl delete <kind>`. Most teardowns are therefore ONE command, the helm one.
A second, batched `kubectl delete` shows up only when something hand-applied is
still running - never for storage, config or the namespace.

**Each runs only when my message says, in plain words, that you may run that
command this time** - "uninstall them", "delete those". The permission covers
what it names, in the message it is in, not the next uninstall or delete.
Anything short of that - a question, a teardown plan I approved - means print
it and suggest it as `! <command>`.

Each separate invocation is another command I have to approve or run, and a
teardown is the worst possible time to make me run twenty. A model the
backoffice deployed is in neither command: it comes down through the
backoffice, for the same ownership reason as an upgrade.

### The things that actually block a drain

**PodDisruptionBudgets.** A PDB reporting `ALLOWED DISRUPTIONS 0` blocks
`kubectl drain` indefinitely. Find them early with
`kubectl get pdb --context <ctx> -n <ns>` and say which release owns each.

Daemonset pods do not block a drain - `kubectl drain --ignore-daemonsets` skips
them, and that flag is required regardless.

### Verify with one command and quote the output

kubectl get deployments,statefulsets,daemonsets,jobs,pods,lws --context <ctx> -n <ns>

It must list nothing but the cell's own components - `No resources found`
outside a cell. Pair it with a `helm list --kube-context <ctx> -n <ns>` that
shows none of mine, and show me both - do not tell me it is done without them.

### One more thing

**A refused command does not mean access is gone.** A denied mutation can black
out reads to the same cluster host for a moment afterwards. Re-test with one
cheap read before telling me you have lost the cluster - it clears on its own,
and reporting a dead connection that is actually fine sends me chasing nothing.
