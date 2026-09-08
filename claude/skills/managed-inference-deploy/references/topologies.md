# Chart and topology selection

> **Confidence note.** The PD single-node material in this skill was verified by
> deploying and benchmarking it. The il-model and multi-node material below is
> derived from reading the charts, not from a run. Treat concrete claims as
> "what the templates say", and re-verify against the chart before relying on a
> detail in production.

## Which chart

| | `il-model` | `pd-model` |
|---|---|---|
| Pattern | interleaved — one engine does prefill + decode | disaggregated — separate prefill and decode workloads |
| Controller | `Deployment` | `LeaderWorkerSet`, or `StatefulSet` under `worker.useSts` |
| Backend key | **`model.llmBackend`** (nested) | **`llmBackend`** (top level) |
| Multi-node | **not supported** — see below | auto-detected, switches to LWS |
| Type blocks | none | `prefill:` / `decode:`, merged over `common:` |
| KV transfer | n/a | `common.sglang.kvTransfer`, `vllm.kvTransfer`, `common.disaggregationIBDevice` |
| Also has | `pdb`, `kvCacheOffload`, `fuser`, top-level `nodeSelector`/`affinity`/`tolerations` | `worker`, `stubEngine`, `terminationGracePeriodSeconds`, `sglang` |

The backend key moving between charts is an easy silent mistake: a top-level
`llmBackend:` in an il-model values file is simply ignored, and the chart quietly
uses the `model.llmBackend` default (`vllm`).

`mode.disaggregated` exists in il-model values and defaults to `false`.

## il-model is single-node only

`il-model/templates/render.yaml` renders `common.deployment` and nothing else.
There is no LWS branch, no `common.multiNode.*` call, and `il-model.validate.all`
resolves to `common.validate.all` (which is only `common.validate.required`) plus
a rolloutStrategy check.

Consequences:

- `gpusPerNode` exists in il-model values but gates nothing there.
- **Nothing rejects `tensorParallelism > gpusPerNode`.** Two distinct failures,
  depending on what `resources.nvidia.com/gpu` says (VERIFIED on H100, sglang
  v0.5.14):
  - GPU request also `> gpusPerNode` → pod sits `Pending` with a scheduling
    message that never mentions tensor parallelism.
  - GPU request fits a node (e.g. `tp: 16` with `nvidia.com/gpu: 8`, which is
    what a "multi-node" il-model values file looks like) → the pod **schedules
    and CrashLoops**. The engine is told `--tp-size 16` with `nnodes=1`,
    `node_rank=0`, `dist_init_addr=None` and dies on GPUs that do not exist:
    `NVML error querying memory affinity for GPU 8..15: Invalid Argument`.
    Nothing in the render or the events mentions tensor parallelism.
- `multiNode.glooSocketIfName` is *not* dead in il-model, but it is reached only
  through `common.gb200Env` (the GB200 NCCL socket interface), not through any
  multi-node path. il-model has no `multiNode.ncclPort` key at all.

**If a model needs more GPUs than one node has, it needs `pd-model`** (or more
replicas at a TP that fits a node).

## Multi-node in pd-model

### It is automatic, not a flag

A type is multi-node when its world size exceeds one node:

```
worldSize = tensorParallelism × dataParallelism × pipelineParallelism
multiNode = worldSize > gpusPerNode
LWS group size (nodes per replica) = worldSize / gpusPerNode
```

Both figures use the same `tp×dp×pp` product deliberately — they must agree, or a
`pp>1` group is classified multi-node while being sized as if `pp` were 1, which
under-provisions GPUs.

Prefill and decode are evaluated **independently**: one side can be multi-node
while the other is not.

### Requirements and constraints

- **LWS controller must be installed** (`leaderworkerset.x-k8s.io/v1`). Without
  it the manifests apply into nothing useful.
- **`worker.useSts: true` is incompatible.** It is a single-node debug fallback
  and fails the render explicitly:
  `worker.useSts=true does not support multi-node: <type> is multi-node (tp*dp > gpusPerNode)`.
- **SGLang has no cross-node data parallelism.** `dp>1` is allowed only while
  `tp×dp×pp` fits one node; otherwise the chart fails and tells you to scale with
  TP (`dp=1`) plus more replicas. vLLM has no such restriction.
- The consuming chart must ship `scripts/node_bootstrap.sh` — Helm's `.Files` is
  scoped to the consuming chart, so the script cannot live in `common`.
- **Known unvalidated combination:** `sglang.enableDpAttention` together with a
  multi-node type is flagged TODO in `pd-model/templates/_validation.tpl` — the
  command would emit both `--nnodes`/`--node-rank` and
  `--enable-dp-attention --dp-size=tp`. Not guarded, not blessed. Do not rely on it.

### Leader vs worker pods

Only rank 0 (the leader) serves the inference API. Worker ranks are **headless**
and do not carry the `<backend>.ai/role` label that router/ISM discovery selects
on.

**"Headless" does NOT mean "no HTTP" — it depends on the backend.** VERIFIED
in-cluster (H100, TP=16 over 2 nodes), leader serving as the control:

| | leader (rank 0) | worker (rank>0) |
|---|---|---|
| **sglang** v0.5.14 | `/health` 200, `/v1/models` 200 | `/health` **200**, `/v1/models` **404** |
| **vLLM** v0.27.1 (`--headless`) | `/health` 200, `/v1/models` 200 | **no listener** — connection refused on both |

So an sglang worker answers a liveness probe while serving nothing, and a vLLM
worker refuses it. Two opposite symptoms for the same pod class. Anything that
special-cases worker ranks must branch on the `worker-index` label, never on the
HTTP response.

Note sglang's `/health` is a bare 200 (`http_server.py` short-circuits it unless
`SGLANG_ENABLE_HEALTH_ENDPOINT_GENERATION` is set); `/health_generate` is the one
that actually generates a token. A worker's 200 therefore proves the app is up,
not that the rank can compute.

This is why the models-validator health-checks multi-node pods but skips endpoint
validation on them — the leader serves inference for the whole group. Worker
identity comes from the `leaderworkerset.sigs.k8s.io/worker-index` label
(absent → single node, `"0"` → leader, anything else → worker).

**Verification implication:** do not expect every pod in a multi-node group to
answer `/health` or appear healthy the way a single-node pod does. Check the
leader for serving, and the workers only for being Running and joined.

### Environment wiring

LWS injects `LWS_LEADER_ADDRESS` and `LWS_WORKER_INDEX`. The chart adds
`POD_NAME`, `POD_IP`, `GPUS_PER_NODE`, `NNODES`, `NCCL_PORT`
(`multiNode.ncclPort`, default 29500), and — when `multiNode.glooSocketIfName`
is set — both `GLOO_SOCKET_IFNAME` and `NCCL_SOCKET_IFNAME`. `node_bootstrap.sh`
consumes these to resolve the leader and join the NCCL collective.

A multi-node group that hangs at startup is a rendezvous problem, but not
necessarily the socket kind. Two verified causes, in order of how much time they
cost to find:

**1. vLLM multi-node TP deadlocks on non-MNNVL hardware.** The chart emits no
`--disable-custom-all-reduce`, so vLLM tries to build a Multi-Node NVLink
symmetric-memory buffer for the TP group. MNNVL is GB200/NVL72 hardware; on H100
the rendezvous never returns and all ranks block before weight loading.

Signature: logs stop right after `NCCL INFO Connected all trees` and
`Custom collectives are disabled because this multi-node group does not support
MNNVL multicast` (that warning is emitted and it still deadlocks - do not read it
as handled). GPUs sit at ~1.4 GiB (CUDA context only) and 0% util, weights never
load, `restartCount` stays 0, and there is no error. Confirmed stack:

    rendezvous (torch/distributed/_symmetric_memory/__init__.py)
    _init_mnnvl_buffer (vllm/distributed/device_communicators/custom_all_reduce.py)
    init_model_parallel_group (vllm/distributed/parallel_state.py)

Fix: add `--disable-custom-all-reduce` to `extraArgs`. VERIFIED: the same
deployment came up and served immediately after.

**2. fastsafetensors cannot load weights across nodes.** It probes GPUDirect
Storage using the GLOBAL rank as a LOCAL cuda device index, so every rank past
the first node asks about a device that does not exist and raises instead of
falling back: `is_gds_supported: cudaDeviceGetAttribute failed, deviceId=13,
err=101` -> `Exception: is_gds_supported(13) failed` -> sigquit -> the group dies.

Fix: `loadFormat: auto` (or drop `--load-format fastsafetensors`). Note
fastsafetensors is the chart DEFAULT, so multi-node needs this set explicitly.

Only after ruling out both is it worth checking the socket interface against
`hostNetwork`, `NNODES` and `NCCL_PORT`.

### Multi-node and RDMA

The `nvidia.com/hostdev` requirement in `rdma.md` is about the **PD KV transport**
(mooncake). Multi-node TP is a separate fabric user — it goes over NCCL, which
reads `NCCL_IB_HCA` / `NCCL_SOCKET_IFNAME` rather than mooncake's topology
discovery.

**Unverified:** whether NCCL in these pods hits the same device-cgroup wall that
silently disabled mooncake's RDMA. It plausibly does, since the blocker was the
container's inability to open any `uverbs` node at all — but I have not run a
multi-node deployment to confirm, and NCCL's fallback behavior and log lines
differ from mooncake's. If you deploy multi-node, check the NCCL init output for
the transport it actually selected before trusting throughput numbers.
