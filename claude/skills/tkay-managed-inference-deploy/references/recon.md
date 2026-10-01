# Cluster recon and verification recipes

Concrete commands, all verified against a live H100 cluster. Ordered by when you
need them.

## Verify RDMA BEFORE the log rotates

**The `Found N HCAs` line exists only in the startup log, and it ages out.**

Under sustained traffic kubelet rotates the container log and drops the startup
portion. Observed on a busy PD pod ~27h in: 50k+ lines retained, and *zero*
matches for `server_args=`, `Load weight begin`, `fired up and ready` or
`Topology discovery`. The log began hours after the pod did.

Consequence: **you cannot retroactively prove RDMA was initialized.** Run the
HCA check within minutes of deploying, or use the age-independent checks below.

### Age-independent checks (work at any pod age)

```
# 1. Was the RDMA resource even requested?  (the root cause, not a symptom)
kubectl get pod -n <ns> <pod> -o jsonpath='{.spec.containers[0].resources}'
#    -> must contain nvidia.com/hostdev

# 2. Can the container actually open a uverbs device?
kubectl exec -n <ns> <pod> -- python3 -c \
  "import os; os.open('/dev/infiniband/uverbs1', os.O_RDWR); print('OPEN OK')"
#    EPERM  -> device cgroup blocked (missing hostdev)
#    EACCES -> file permissions (different problem)
#    OK     -> RDMA devices are reachable
```

Check 2 is the definitive live test. `ls -l /dev/infiniband` is **not** — the
nodes show `crw-rw-rw-` even when every open fails.

## Before installing

```
# GPU and RDMA headroom on the target node(s)
kubectl describe node <node> | grep -E "nvidia.com/(gpu|hostdev)"
kubectl describe node <node> | grep -A15 "Allocated resources"

# How many nodes does your selector actually match?
# One match => prefill and decode co-locate; the fabric is never crossed.
kubectl get nodes -l <your-selector> -o wide

# Which NICs are InfiniBand vs the Ethernet frontend?
kubectl exec -n <ns> <any-pod-on-that-node> -- sh -c \
  'for d in /sys/class/infiniband/*; do printf "%s %s %s\n" \
   "$(basename $d)" "$(cat $d/ports/1/link_layer)" "$(cat $d/ports/1/state)"; done'
```

Sample output from `h100-80gb-sxm-ib.8x` — `mlx5_0` is the Ethernet frontend and
must be **excluded** from `disaggregationIBDevice`:

```
mlx5_0 Ethernet   4: ACTIVE
mlx5_1 InfiniBand 4: ACTIVE
...
mlx5_8 InfiniBand 4: ACTIVE
```

## Confirming GPU isolation holds

This is how to check the claim behind the chart's `privileged: false` default —
that the NVIDIA device plugin gives each pod only its allocation:

```
kubectl exec -n <ns> <pod> -- sh -c 'echo $NVIDIA_VISIBLE_DEVICES; nvidia-smi -L'
```

Healthy result: `NVIDIA_VISIBLE_DEVICES` is a **single GPU UUID** and `nvidia-smi -L`
lists exactly one GPU, matching it. If a pod with 1 GPU allocated sees all 8,
isolation is broken and co-located pods will collide on GPU 0.

## Gateway checks

| Endpoint | Use |
|---|---|
| `GET /v1/models` | confirm a model registered |
| `POST /v1/chat/completions` | end-to-end test |

Do not take an endpoint name from another component's source: whether the
running gateway build serves it is only settled by probing it.

```
kubectl exec -n <ns> deploy/atero-gateway -- \
  curl -s --max-time 10 http://localhost:8080/v1/models
```

Readiness is `/v1/models`, not the `AteroModelSpec` CR the chart creates: the CR
is a readiness signal only if `kubectl get ateromodelspec -n <ns> -o yaml` shows
a `.status` that something maintains.

## Reading engine logs

```
grep -E "Found . HCAs"                     # RDMA up? (startup only — see above)
grep -c TcpTransport                        # TCP fallback? must be 0
grep -E "max_total_num_tokens|KV Cache"     # pool sizing (startup only)
grep -E "Prefill batch|Decode batch"        # is work actually split?
grep -c "transfer failed"                   # KV transfer health (any age)
```

`transfer failed` and `TcpTransport` counts stay meaningful after rotation because
they recur with traffic. The startup-only lines do not.

When chasing a failure, dump the whole log and find the **first** occurrence — the
first error names the real fault, later ones degrade into generic
"session is not alive":

```
kubectl logs -n <ns> <pod> > /tmp/pod.log
grep -n "transfer failed" /tmp/pod.log | head -1
sed -n '<N-30>,<N+5>p' /tmp/pod.log
```

## kubectl invocation gotcha

Flags must follow the subcommand. `kubectl --context X exec ...` fails with
`flags cannot be placed before plugin name` when krew plugins are installed, and
collapsing `-n ns --context ctx` into a shell variable used before the subcommand
gets parsed as part of the namespace:

```
kubectl exec -n <ns> --context <ctx> <pod> -- <cmd>     # correct
kubectl --context <ctx> exec -n <ns> <pod> -- <cmd>     # fails with krew
```

Prefer `--context <ctx>` on individual commands over `kubectl config use-context`
— it verifies against the right cluster without mutating the user's kubeconfig.
**Always confirm the context before concluding something is missing**: a
`namespaces "<ns>" not found` usually means the wrong cluster, not a deleted
namespace.
