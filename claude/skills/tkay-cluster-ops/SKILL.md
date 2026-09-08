---
name: tkay-cluster-ops
description: Tomer's procedures for helm upgrades against a live release and for tearing his deployments off a node. Use when running helm install/upgrade on an existing release, when a server-side apply hits a field-manager conflict, or when asked to take down / remove / drain everything he owns in a namespace before a cluster is destroyed or a node is drained.
---

# Cluster operations

Context and namespace pinning, node pinning, and who may run which command are
in my global CLAUDE.md and always apply. This skill is the *how* for the two
operations that have real procedure behind them.

## Upgrading a Live Release: Get the Chart the Release Actually Used

**The deployed chart is usually NOT my local working tree.** CI stamps the chart
version from `git describe`, so the local `Chart.yaml` keeps a placeholder
(`0.1.0`) forever and never matches a released version. Compare `helm list`
against the local `Chart.yaml` before anything else. Upgrading from the local
directory smuggles in every unreleased change — different values defaults,
different ConfigMap-mounted source — under what I asked to be a one-value tweak.

Ways to get the real chart:

- **OCI ref** — the normal one for atero-charts:
  `helm upgrade <release> oci://registry.gitlab.com/crusoeenergy/atero/atero-charts/<chart> --version <version>`
- **Extract it from the release secret** (`sh.helm.release.v1.<release>.v<n>`:
  base64 → gzip → JSON carrying the chart files) when the registry is
  unreachable.

Before every upgrade:

- `helm get values <release>` first, then **ASK me whether `--reuse-values` is
  wanted — do not decide it yourself.** It replays my previous user values on
  top of the *new* chart's defaults: a no-op when the release has none, and a
  silent carry-forward of stale values when it does.
- Render with the identical flags (`helm template`, or `helm upgrade --dry-run`
  when `--reuse-values` is in play) and diff it against
  `helm get manifest <release>`, so you can tell me every field that changes —
  not just the one I asked for.

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

**Never run `--force-conflicts` on your own initiative — show me the command and
let me decide.** It transfers ownership of those fields to `helm`, and then
data-path's own redeploy applies as `worker` without force and hits the
mirror-image conflict, so forcing trades my problem for a landmine in the deploy
path. Always state that consequence when you offer it, and offer the
alternatives: make the change through data-path so `worker` stays the owner, or
patch the object directly (fast, but helm's recorded release goes out of sync
and the next upgrade silently drops the change).

---

## Removing Myself From a Node

When I say a cluster is being drained or destroyed, or ask you to take my
deployments down, the target is **`k9s -n <ns>` showing nothing** - not "the
helm releases are gone". Nothing running, nothing pending, nothing holding a
GPU.

### Never hardcode the node - discover it every time

I move between nodes constantly, so a node name from an earlier session is
worthless. Start by finding what is mine right now:

kubectl get nodes --context <ctx> -L atero/user,crusoe-ai.managed-ai.inference.node-purpose

**My namespace and my node-label value are NOT the same string** and never
assume one from the other - I have run a namespace named for one and nodes
labelled with the other in the same cluster. Read both off the cluster: the
namespace from what I told you, the label value from the node list above.

A selector pointing at a label no node carries is the trap that follows: the
workload looks deployed while scheduling nowhere.

### Enumerate before proposing anything

Helm knows about only part of it:

1. `helm list --kube-context <ctx> -n <ns>` - the releases.
2. `kubectl get deployments,statefulsets,daemonsets,jobs,pods,lws --context <ctx> -n <ns>`
   - the truth. Anything here that is not in the helm list was applied by hand,
   and helm will never remove it.
3. Cross-reference ownership with
   `-o custom-columns='NAME:.metadata.name,MANAGED_BY:.metadata.labels.app\.kubernetes\.io/managed-by,RELEASE:.metadata.annotations.meta\.helm\.sh/release-name,OWNER:.metadata.ownerReferences[*].kind'`

**`kubectl get all` is not "all" and will lie to you** - it silently omits
LeaderWorkerSets and every other CRD, plus PDBs and PVCs. Always name the kinds
explicitly, `lws` included.

**`DESIRED 0` on a daemonset does not mean it is gone.** It means no node
currently matches its selector - the object is still there and still needs
deleting. A node being drained or relabelled out from under it produces exactly
this.

Then give me three lists: what one `helm uninstall` takes, what needs
`kubectl delete` because nothing owns it, and what survives both.

### What survives `helm uninstall` and still needs deleting

- StatefulSet `volumeClaimTemplate` PVCs - helm never created them, so it never
  removes them.
- Objects a controller created rather than the chart, such as a
  LeaderWorkerSet's per-replica StatefulSets. If the LWS itself is helm-owned
  the cascade handles them; if it is not, they are a separate delete.
- Hand-applied daemonsets, services, PVCs, secrets and configmaps.

### Two commands, batched - not one per object

`helm uninstall` accepts every release name in a single invocation, and so does
`kubectl delete <kind>`. Collapse the teardown into exactly two commands - one
helm, one kubectl - in that order. Each separate invocation is another approval
I have to sit through, and a teardown is the worst possible time to make me
click twenty times.

### The things that actually block a drain

**PodDisruptionBudgets.** A PDB reporting `ALLOWED DISRUPTIONS 0` blocks
`kubectl drain` indefinitely. Find them early with
`kubectl get pdb --context <ctx> -n <ns>` and say which release owns each.

Daemonset pods do not block a drain - `kubectl drain --ignore-daemonsets` skips
them, and that flag is required regardless.

### Verify with one command and quote the output

kubectl get deployments,statefulsets,daemonsets,jobs,pods,lws --context <ctx> -n <ns>

It must come back `No resources found`. Pair it with an empty
`helm list --kube-context <ctx> -n <ns>`, and show me both - do not tell me it
is done without them.

### Two more things

**Name every data-bearing volume separately and wait for my answer**, rather
than folding it into the teardown list. Deleting a PVC is the one step here
nobody can undo.

**A refused command does not mean access is gone.** A denied mutation can black
out reads to the same cluster host for a moment afterwards. Re-test with one
cheap read before telling me you have lost the cluster - it clears on its own,
and reporting a dead connection that is actually fine sends me chasing nothing.
