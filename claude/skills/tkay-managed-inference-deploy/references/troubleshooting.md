# Troubleshooting

## Read the error under the error

SGLang wraps low-level transport failures in its own request-scoped message. The
wrapper names a *component* ("instance could be dead"); the line above it names
the *actual* fault. Always grep the raw log around the first failure rather than
reading the summarized exception.

```
kubectl logs <pod> --context <ctx> -n <ns> > /tmp/claude/pod.log
grep -n "transfer failed" /tmp/claude/pod.log | head -1     # find the FIRST one
sed -n '<N-30>,<N+5>p' /tmp/claude/pod.log                  # read what preceded it
```

The first failure is almost always more informative than the thousand that
follow — later ones degrade into a generic "session is not alive".

## Symptom → cause

| Symptom | Likely cause | Confirm with |
|---|---|---|
| `Decode transfer failed ... it might be dead` / `Decode instance could be dead` | Not a dead pod. Transport-level failure — usually TCP fallback + port exhaustion. See `rdma.md`. | `restartCount` is 0 on both pods; `grep "Found . HCAs"` |
| `connect: Cannot assign requested address` | Ephemeral port exhaustion (`EADDRNOTAVAIL`), because mooncake is on TCP instead of RDMA | `grep TcpTransport`; `cat /proc/sys/net/ipv4/ip_local_port_range` |
| `Found 0 HCAs` | Missing `nvidia.com/hostdev` request → device cgroup denies uverbs | `os.open` test in `rdma.md` |
| `Invalid request: Disaggregated request received without bootstrap room id` → 400 | A client hit the PD pod **directly** instead of via the gateway. Correct behavior. Check the source IP — if it isn't the gateway, it's a validator/monitor/probe, not your traffic. | `kubectl get pods -A -o wide \| grep <source-ip>` |
| Pod Ready, `/v1/models` fine, single requests fine, load collapses | Classic silent-fallback signature. Nothing in the readiness path tests the KV transport. | the verification gate in SKILL.md |
| Only ~N concurrent requests fit, `token usage` high with few running | `--max-total-tokens` set too low in `extraArgs` — it caps the entire KV pool | `grep max_total_num_tokens` in the pod log |
| Render fails: `AteroModelSpec CRD not found` | Local `helm template` without cluster capabilities | `kubectl get crd \| grep atero`; re-render with `--api-versions "atero.ai/v1/AteroModelSpec"` |
| `GDS file-handle setup failed ... cuFileHandleRegister returned an error` | GPUDirect Storage unavailable; falls back to CPU bounce buffer. Benign. | weight-load elapsed time in the log |
| Pod Pending forever with an RDMA resource request | Combined `hostdev` across co-located pods exceeds node allocatable, **or** an unrelated `nodeSelector` pin | `kubectl describe pod` events; `kubectl describe node <n> \| grep hostdev` |
| Pod Pending, large `tensorParallelism`, no error mentioning TP | il-model is single-node only. It asked one pod for more GPUs than a node has. | chart is il-model; compare `tp` to `gpusPerNode` |
| Multi-node worker pod has no role label; `/v1/models` fails | Correct — only rank 0 serves the API. But `/health` is backend-dependent: sglang worker answers **200**, vLLM `--headless` worker **refuses the connection**. Never infer worker-ness from the HTTP response. | `leaderworkerset.sigs.k8s.io/worker-index` label on the pod |
| **vLLM** multi-node hangs before weight load, no error, GPUs ~1.4 GiB / 0% | MNNVL symmetric-memory rendezvous in vLLM's custom all-reduce. MNNVL is GB200 hardware; on H100 it never returns (seen on vLLM v0.27.1). The `does not support MNNVL multicast` warning is logged and it still deadlocks. | logs stop after `Connected all trees`; `py-spy dump` shows `_init_mnnvl_buffer`. Fix: `--disable-custom-all-reduce` |
| Multi-node dies with `is_gds_supported(N) failed`, N > local GPU count | fastsafetensors probes GDS with the GLOBAL rank as a LOCAL device index, so ranks past node 0 reference a nonexistent device | the rendered args carry `--load-format fastsafetensors`. Fix: `loadFormat: auto` |
| Multi-node group hangs and neither of the above applies | NCCL/gloo socket rendezvous. Check the interface against `hostNetwork`. | `multiNode.glooSocketIfName`, `NNODES`, `NCCL_PORT` in pod env |
| il-model pod CrashLoops with `NVML error querying memory affinity for GPU 8..15` | il-model is single-node only: `--tp-size` exceeds the GPUs in the container. `Pending` is the other form of this; which one you get depends on the GPU request. | chart is il-model; compare `tp` to `resources.nvidia.com/gpu` |
| Gateway `/v1/inference_servers` returns `{"models":[]}` though pods are discovered | The gw builds its **server** list from pod discovery but its **model catalog** from `AteroModelSpec` CRs. No CR → nothing to route to, even with `became_ready ... capacity_fetch_result="ok"` in the gw log. | `kubectl get ateromodelspec -n <ns>` |

## Reading a PD log

Useful greps once a deployment is live:

```
grep -E "Found . HCAs"                    # RDMA up?  (must be >= 1)
grep -c TcpTransport                       # TCP fallback?  (must be 0)
grep -E "max_total_num_tokens|KV Cache"    # pool sizing
grep -E "Prefill batch|Decode batch"       # is work actually split?
grep -c "transfer failed"                  # KV transfer health
grep "Disaggregation warmup"               # startup PD handshake result
```

`Disaggregation warmup request completed with status 200` on both pods at startup
means the PD handshake works — but it is a **single sequential request**, so it
passes happily over TCP. It does not validate the transport under load.

## Pods co-located on one node

A dev `nodeSelector` that matches exactly one node puts prefill and decode
together. Consequences worth remembering:

- The KV transfer never crosses the fabric, so cross-node RDMA stays untested.
- Their resource requests compete on that single node — `nvidia.com/gpu` and
  `nvidia.com/hostdev` both.
- `privileged: true` would let each pod see all GPUs and collide on GPU 0. This
  is exactly the case the chart's `privileged: false` default protects.

Check how many nodes actually match before assuming a spread:

```
kubectl get nodes --context <ctx> -l <your-selector> -o wide
```

## Getting evidence out of a multi-node group

Multi-node failures actively destroy their own evidence. Three things to set
BEFORE debugging, or you will chase ghosts (all three cost real time today):

- **`restartPolicy: Default` on the LWS while debugging.** The default
  `RecreateGroupOnPodRestart` replaces every pod in the group when any one
  restarts, so `restartCount` resets to 0 and `kubectl logs --previous` returns
  "not found". The crash looks like an external actor deleting your pods. With
  `Default` the container restarts in place and `--previous` holds the stack.
  Put gang-restart back for production — it is correct there.
- **`PYTHONUNBUFFERED=1`.** Engine stdout is block-buffered into a pipe; on
  SIGKILL the buffer is lost, so a crashing engine logs *nothing* past the last
  flush. Symptom: logs end mid-startup with no error at all.
- **`SYS_PTRACE` capability + `pip install py-spy`, then `py-spy dump --pid <pid>`.**
  The only way to see where a silent hang actually is. Without `SYS_PTRACE`
  py-spy fails with `Failed to copy Py_Version symbol: Permission denied`.
  Worker pids: `pgrep -f 'VLLM::Worker'`.

And one trap to avoid: **a not-yet-started server and a never-started server look
identical** (connection refused either way). Never conclude "this pod has no HTTP
server" while the group is still initialising — probe the leader in the same
instant as a control, and only trust the comparison once the leader answers.
