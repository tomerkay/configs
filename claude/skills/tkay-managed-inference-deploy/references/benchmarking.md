# Benchmarking with wrenchmark

## The chart is in a different repo

`charts/wrenchmark` lives in the **wrenchmark** repo, not `atero-charts`. Running
the usual command from an `atero-charts` checkout fails with a missing-chart
error. Either run it from the wrenchmark repo root or pass an absolute chart path:

```
helm install wrenchmark <wrenchmark-repo>/charts/wrenchmark \
  -f <values>.yml --set runBy=<user> --kube-context <ctx> -n <ns>
```

## Before benchmarking, verify the deployment

Run the verification gate in `SKILL.md` first. A benchmark against a
silently-degraded deployment produces numbers that look plausible and mean
nothing — and the failure it eventually triggers gets blamed on the benchmark.

Specifically confirm `Found . HCAs` is nonzero and `max_total_num_tokens` is
large enough for `maxConcurrency × inputLen`. A KV pool that fits only a handful
of concurrent requests silently serializes the run.

## Point it at the right endpoint

`baseUrl` must not be a gateway **pod IP**: pod IPs change on every restart.
Check what it points at before each run:

```
kubectl get pods --context <ctx> -n <ns> -o wide | grep gateway
```

A stale IP produces connection errors that look like model failures.

## Capture logs as they stream — the pod may not survive

Benchmark job pods can be replaced or reaped mid-run, and once deleted their logs
are **gone** — `kubectl logs` on a deleted pod returns `NotFound`, leaving no
record of whether requests actually failed. Stream to a file from the start
rather than tailing after the fact:

```
kubectl logs job/wrenchmark-benchmark -c benchmark -f --context <ctx> -n <ns> | tee /tmp/claude/wrench.log
```

The benchmark pod runs two containers (`benchmark`, `prometheus`) — always pass
`-c benchmark`.

If a job pod is replaced mid-run (`SuccessfulCreate` for a second pod in
`kubectl get events`), treat the first run as suspect: that restart is the one
signal that it failed, and without captured logs it cannot be settled after the
fact.

## Verifying a run from the engine side

Engine logs outlive the benchmark pod, so they are the durable record:

```
kubectl logs <model-pod> --context <ctx> -n <ns> | grep -c "transfer failed"        # want 0
kubectl logs <model-pod> --context <ctx> -n <ns> | grep -c TcpTransport             # want 0
kubectl logs <model-pod> --context <ctx> -n <ns> | grep -cE "Prefill batch|Decode batch"
kubectl logs <model-pod> --context <ctx> -n <ns> | grep -v " 200 OK" | grep "HTTP/1.1"   # non-200s
```

When checking non-200 responses, **check the source IP**. Traffic from the
gateway is your benchmark; traffic from anywhere else is a validator, monitor or
probe. A direct-to-pod request in a PD setup is correctly rejected with
`400 Invalid request: Disaggregated request received without bootstrap room id`
and is not a benchmark failure.

## Reading the per-request line

```
✓ Request 18: ... e2e=0.686s, ttft=0.047s, tpot=6.458ms, avg_itl=7.807ms,
  real_num_input_tokens=1000, real_num_cached_tokens=30 (3.0%),
  real_num_output_tokens=100, e2e_tps=145.697, decode_tps=154.858
```

`real_num_*` are what the server actually saw, versus the `target` values
requested — a gap between them means truncation, template overhead or a cache hit
you did not intend, and invalidates comparisons against another run.
