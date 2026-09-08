# The silent TCP fallback

The most expensive failure mode in PD deployments. It renders clean, installs
clean, passes health checks, serves correct completions, and then destroys a
benchmark 55 minutes later with an error that blames the wrong pod.

## The chain

1. **Pod requests `nvidia.com/gpu` but not `nvidia.com/hostdev`.**
   The SR-IOV device plugin grants no RDMA device.

2. **Device nodes are visible but unopenable.**
   The chart hostPath-mounts `/dev/infiniband`, so `ls -l` shows
   `crw-rw-rw- root root 231, 193 uverbs1` — world read/write, and the container
   runs as uid 0. Permissions are not the problem. The container is
   `privileged: false`, so containerd's default device cgroup allowlist excludes
   major 231 and the kernel denies `open()`.

   The distinguishing detail: **`EPERM`, not `EACCES`.**

   ```
   python3 -c "import os; os.open('/dev/infiniband/uverbs1', os.O_RDWR)"
   # PermissionError: [Errno 1] Operation not permitted   <- device cgroup
   # [Errno 13] Permission denied would be file perms
   ```

3. **mooncake discards every NIC and falls back, at INFO level.**

   ```
   W topology.cpp:64]  Device /dev/infiniband/uverbs1 is not accessible for read/write
   W topology.cpp:169] Skipping unavailable device: mlx5_1
   ... one pair per NIC ...
   I transfer_engine_impl.cpp:252] Topology discovery complete. Found 0 HCAs.
   I tcp_transport.cpp:553]        TcpTransport: listen on port 16245
   ```

   No error. No warning. The pod goes Ready.

   Note SGLang *accepts* `disaggregation_ib_device` and shows it in `server_args`
   — mooncake then throws those devices away. **Seeing the flag in `server_args`
   proves nothing.** Only the HCA count does.

4. **Low load looks perfect.** TCP moves KV fine for single requests. Warmup
   passes, `/v1/chat/completions` returns correct text, PD genuinely splits
   prefill and decode. Nothing is wrong except the transport.

5. **Load exhausts ephemeral ports.** mooncake's TCP transport opens a connection
   per KV chunk. Sockets pile into `TIME_WAIT` faster than they drain out of
   `ip_local_port_range` (typically `32768 60999`), and `connect()` starts
   returning `EADDRNOTAVAIL`:

   ```
   E tcp_transport.cpp:720] TcpTransport::getConnection failed to create connection
     to <decode-ip>:16708. Error: connect: Cannot assign requested address
   ```

6. **SGLang reports it as a dead peer, on both sides.**

   ```
   decode:  Failed to get kvcache from prefill instance, it might be dead
   prefill: Decode instance could be dead, remote mooncake session <ip>:<port> is not alive
   ```

   Both pods accuse each other; each sees only its own broken half of the session.
   **Neither pod restarted** — `restartCount` stays 0 throughout. That is the tell
   that "dead" is a lie.

## Diagnosing it in under a minute

```
# 1. Did RDMA ever initialize? This is the whole question.
kubectl logs -n <ns> <pod> | grep -E "Found . HCAs|Skipping unavailable"

# 2. Which transport is actually in use?
kubectl logs -n <ns> <pod> | grep -o -E "[A-Za-z]+Transport::" | sort | uniq -c

# 3. Did anything actually die?
kubectl get pod -n <ns> <pod> -o jsonpath='{.status.containerStatuses[0].restartCount}'

# 4. Prove the device cgroup is the blocker
kubectl exec -n <ns> <pod> -- python3 -c \
  "import os; os.open('/dev/infiniband/uverbs1', os.O_RDWR); print('OK')"
```

`Found 0 HCAs` + `restartCount: 0` + `EADDRNOTAVAIL` is the complete signature.

## After the fix

Requesting `nvidia.com/hostdev: 1` yields:

```
I transfer_engine_impl.cpp:252] Topology discovery complete. Found 1 HCAs.
```

Each pod is granted **one arbitrary VF**, so prefill and decode typically get
*different* devices (e.g. prefill `mlx5_2`, decode `mlx5_1`). The other NICs still
log `Skipping unavailable device` — that is expected and harmless once the count
is ≥ 1. Because the grant is arbitrary, leaving all IB NICs listed in
`disaggregationIBDevice` is the robust choice; mooncake's auto-discovery uses
whichever it actually received.

**Unverified:** whether same-node prefill/decode transfers exercise the RDMA path
or take a local shortcut. Co-locating both pods on one node (the common dev setup
with a single `nodeSelector`-matched node) means the fabric is never crossed, so a
green run there does not prove cross-node RDMA works.
