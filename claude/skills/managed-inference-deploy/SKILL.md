---
name: managed-inference-deploy
description: Deploying inference models to Crusoe k8s with the il-model (interleaved) and pd-model (disaggregated prefill/decode) Helm charts, single-node and multi-node — writing values.yaml, rendering locally, installing, and the post-install verification that catches silent misconfiguration. Use when a helm install/upgrade of a model chart fails to render, when choosing between il-model and pd-model or sizing tensor parallelism across nodes, when a deployment serves single requests but collapses under load, when KV-transfer errors appear ("transfer failed", "instance could be dead"), when RDMA/InfiniBand is not being used, or when running a wrenchmark benchmark against a deployment.
---

# Deploying managed-inference models

Covers `charts/model/il-model` and `charts/model/pd-model` in `atero-charts`.
The charts' own `values.yaml` comments are the reference for what each knob does
— this skill covers what those comments do NOT tell you: the failures that render
clean, install clean, and serve correct answers for an hour before falling over.

> **Confidence:** the single-node PD material here was verified by deploying and
> benchmarking it. The il-model and multi-node material in `references/topologies.md`
> is derived from reading the charts, not from a run — it is marked as such there.

## The one rule

**A model that passes a smoke test is not a model that works.**

Every serious failure in this skill was invisible to `kubectl get pods`, invisible
to `/v1/models`, and invisible to a single chat completion. They surface only under
concurrent load, and the error they surface with points at the wrong component.

Run the verification gate below on **every** fresh deploy. It takes ten seconds.

## Pick the chart before writing values

| Need | Chart |
|---|---|
| One engine does prefill + decode | `il-model` |
| Separate prefill/decode workloads, KV transfer between them | `pd-model` |
| Model needs more GPUs than one node has | **`pd-model` only** |

**`il-model` is single-node only.** It renders a plain `Deployment`, has no
LeaderWorkerSet path, and validates nothing about `tp` vs `gpusPerNode`. An
oversized TP either produces an unschedulable pod or — if the GPU request happens
to fit a node — a pod that **schedules and CrashLoops** on GPUs that do not exist.
Neither failure mentions tensor parallelism. A values file named
`..._multinode.yaml` for il-model cannot work, whatever its comments claim.
`pd-model` auto-detects multi-node (`tp×dp×pp > gpusPerNode`) and switches to LWS.

Backend selection differs between the charts and is silently ignored if you use
the wrong one: **`model.llmBackend`** in il-model, **`llmBackend`** (top level) in
pd-model.

See `references/topologies.md` for the full comparison and multi-node rules.

## Deploy loop

### 1. Render locally first

```
helm template <release> charts/model/<chart> -f <values>.yaml -n <ns> \
  --api-versions "atero.ai/v1/AteroModelSpec" \
  --api-versions "leaderworkerset.x-k8s.io/v1"      # multi-node only
```

`--api-versions` is **required** for local rendering. Without cluster access
`.Capabilities.APIVersions.Has` returns false and the chart fails with a
CRD-missing error that says nothing about your values. Two capability gates exist,
and each produces its own false alarm:

- `AteroModelSpec CRD not found` → needs `atero.ai/v1/AteroModelSpec`
- `LWS CRD (leaderworkerset.x-k8s.io/v1) is not installed` → needs
  `leaderworkerset.x-k8s.io/v1`; only fires for multi-node, since single-node
  under `worker.useSts` never reaches the LWS path

Before believing either from a **real** install, check the cluster:
`kubectl get crd | grep -Ei 'atero|leaderworker'`.

Chart validation is `fail()`-based and runs at render time, so a bad values file
never reaches the API server. Render errors are precise — read them literally.

### 2. Install / upgrade

Cluster-mutating commands are the user's to run. Print them as `! <command>`
and let them execute, unless they have explicitly authorized you for the
namespace and cluster in the current session.

### 3. Verification gate — non-negotiable

**All deployments** — did the KV pool actually get the memory you paid for?

```
kubectl logs -n <ns> <pod> | grep -E "max_total_num_tokens|KV Cache is allocated"
```

**PD only** — is RDMA alive? `0` HCAs means mooncake silently fell back to TCP
and the deployment will collapse under load. **Run this within minutes of
deploying**: the line lives only in the startup log and is lost once kubelet
rotates it under traffic (see `references/recon.md` for age-independent checks):

```
for p in prefill decode; do
  kubectl logs -n <ns> <release>-pd-model-$p-0 | grep -E "Found . HCAs"
  kubectl logs -n <ns> <release>-pd-model-$p-0 | grep -c TcpTransport   # must be 0
done
```

**PD only** — is work actually being split? A single pod doing both halves means
PD is not functioning as PD:

```
kubectl logs -n <ns> <release>-pd-model-prefill-0 | grep "Prefill batch" | tail -2
kubectl logs -n <ns> <release>-pd-model-decode-0  | grep "Decode batch"  | tail -2
```

**Multi-node** — only rank 0 serves. Workers are headless: no HTTP server, no
probes, no role label. Do not read a worker's lack of `/health` as a fault. Check
the leader for serving, workers for Running + joined, and the NCCL init output for
which transport it selected.

Pod names differ by chart — il-model pods come from a `Deployment` (hashed suffix),
pd-model from LWS/StatefulSet (`-prefill-0` / `-decode-0`). Resolve with
`kubectl get pods -n <ns> -l app.kubernetes.io/instance=<release>`.

Then a real request through the gateway. If the gateway returns no route, check
`/v1/inference_servers` on the management port: `{"models":[]}` means pod
discovery worked but there is no `AteroModelSpec` CR, so the model catalog is
empty. Discovery gives the gw *servers*; the CR gives it *models*.

## PD deployments: the RDMA trap

**`nvidia.com/hostdev` is required, and nothing tells you when it's missing.**

Requesting `nvidia.com/gpu` alone gives the container GPUs but no RDMA device. The
`hostPath` mount of `/dev/infiniband` makes the uverbs nodes *visible* with
`crw-rw-rw-` permissions, but the kernel device cgroup still denies `open()` —
`EPERM`, not `EACCES`, so file permissions look fine while every open fails.

mooncake then logs `Skipping unavailable device` per NIC, `Found 0 HCAs`, and
starts a **TCP** listener at INFO level. No error, no warning, no crash.

Add to both `prefill.resources` and `decode.resources`:

```yaml
requests:
  nvidia.com/gpu: 1
  nvidia.com/hostdev: 1
limits:
  nvidia.com/gpu: 1
  nvidia.com/hostdev: 1
```

Sizing: match the node's GPU:NIC ratio (H100 SXM 8x is 8:8, so 1 NIC per GPU).
Both PD pods usually land on the same node, so their combined `hostdev` request
must fit that node's allocatable — check with
`kubectl describe node <node> | grep hostdev`.

`nvidia.com/hostdev` is the SR-IOV device plugin resource
(`network-operator-sriovdp-config`, selector `isRdma: true`), which is what
actually grants the device-cgroup entry.

**Do not "fix" this with `privileged: true`.** It works, but the chart sets
`privileged: false` deliberately: privileged bypasses the device cgroup so the
container sees every GPU on the node, breaking the NVIDIA device plugin's per-pod
isolation. Co-located prefill and decode then collide on GPU 0.

See `references/rdma.md` for the full failure chain and how to diagnose it.

## Config gotchas that survive rendering

| Symptom | Cause |
|---|---|
| KV pool tiny, GPU mostly idle | `--max-total-tokens` in `extraArgs` sizes the **whole KV cache pool**, not a batch. It overrides `gpuMemoryUtilization`. Omit it unless you mean it; use `--max-running-requests` / `--max-prefill-tokens` for batch limits. |
| Backend setting ignored | Wrong key for the chart: `model.llmBackend` (il-model) vs `llmBackend` (pd-model). |
| Render fails: `sglang.kvTransfer moved` | Key lives at `common.sglang.kvTransfer`, with optional `prefill.`/`decode.` overrides. Top-level `sglang:` still exists for other knobs. |
| PD configured but no `--disaggregation-*` flags | `common.disaggregationIBDevice` unset. Backend-agnostic (SGLang flag / vLLM NIC env). List only InfiniBand HCAs — exclude the Ethernet frontend NIC (usually `mlx5_0`; confirm via `link_layer` under `/sys/class/infiniband/*/ports/1/`). |
| **vLLM** multi-node hangs before weight load, no error at all | MNNVL symmetric-memory rendezvous in vLLM's custom all-reduce. MNNVL is GB200-class hardware, so on H100 it never returns. Add `--disable-custom-all-reduce` to `extraArgs`. VERIFIED on H100 + vLLM v0.27.1; the chart does not emit this flag, so **every vLLM multi-node deployment from pd-model hangs on non-MNNVL hardware.** |
| Multi-node dies with `is_gds_supported(N) failed` | fastsafetensors (the chart **default**) probes GPUDirect Storage with the GLOBAL rank as a LOCAL cuda device index, so ranks past node 0 reference a device that does not exist. Set `loadFormat: auto` for any multi-node type. |
| Render fails: `worker.useSts=true does not support multi-node` | `useSts` is a single-node debug fallback. Unset it to get LWS. |
| Pod Pending, no useful reason, large TP | il-model with `tp > gpusPerNode` — it has no multi-node path and no validation for this. Use pd-model. |
| `GDS file-handle setup failed ... cuFileHandleRegister` | Benign. GPUDirect Storage unavailable, weight loading falls back to a CPU bounce buffer. Costs seconds on a small model; matters more on large ones. |

## References

- `references/recon.md` — verified commands: pre-install capacity, RDMA checks
  that survive log rotation, gateway endpoints, GPU-isolation proof
- `references/topologies.md` — il-model vs pd-model, and all multi-node rules
- `references/rdma.md` — the silent-TCP-fallback failure chain, start to finish
- `references/troubleshooting.md` — symptom → root cause, including the
  misleading "instance could be dead" family
- `references/benchmarking.md` — running wrenchmark, and capturing its logs
  before the pod is reaped
