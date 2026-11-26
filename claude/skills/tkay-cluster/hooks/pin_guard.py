#!/usr/bin/env python3
"""PreToolUse hook on Bash: denies a cluster command that does not name its target, so no
command reaches whichever context the kubeconfig last pointed at.

kubectl, k, oc and stern carry --context, and -n, --namespace or -A unless what they name is
cluster-scoped; helm carries --kube-context and a namespace; helmfile carries
--kube-context whenever it reaches the cluster. A command that bash -c, xargs, find -exec
or uv run runs is held to the same. A subcommand that never reaches a cluster, and a
request for help, need neither.

It only denies, never asks, and never changes a call's input. A crash exits non-zero, and
the hook's `|| exit 2` blocks the call.

`pin_guard.py --selftest` runs the decision table's cases.
"""

import json
import sys

from command_parser import (
    HELM_LOCAL, HELMFILE_GLOBAL_VALUE_FLAGS, HELMFILE_RELEASE_WRITES, KUBECTL_GLOBAL_VALUE_FLAGS,
    KUBECTL_LOCAL, has_flag, help_only, helm_words, invocations, positionals, split_globals,
    uv_run_invocations, with_assigned_path,
)

KUBECTL_CONTEXT = "pin the context: every cluster command carries --context <ctx>"
KUBECTL_NAMESPACE = ("pin the namespace: every cluster command carries -n <ns>, "
                     "or -A when a cluster-wide view is the point")
HELM_CONTEXT = "pin the context: every helm command carries --kube-context <ctx>"
HELM_NAMESPACE = "pin the namespace: every helm command carries -n <ns>"
HELMFILE_CONTEXT = ("pin the context: every helmfile command that reaches a cluster "
                    "carries --kube-context <ctx>")

KUBECTL_PROGRAMS = {"kubectl", "k", "oc"}
# Cluster-scoped commands where kubectl ignores -n; `get --raw` carries an API path instead.
NAMESPACE_FREE = {("get", "node"), ("get", "nodes"), ("describe", "node"), ("describe", "nodes"),
                  ("top", "node"), ("top", "nodes"), ("get", "crd"), ("get", "crds"),
                  ("get", "customresourcedefinitions"), ("get", "ns"), ("get", "namespace"),
                  ("get", "namespaces"), ("label", "node"), ("label", "nodes"),
                  ("annotate", "node"), ("annotate", "nodes"), ("taint", "node"),
                  ("taint", "nodes"), ("get", "clusterpolicy"), ("get", "clusterpolicies"),
                  ("get", "cpol"), ("describe", "clusterpolicy"),
                  ("describe", "clusterpolicies"), ("describe", "cpol")}
# Verbs whose only target is a node, so the second word is the node's name.
NODE_VERBS = {"cordon", "uncordon", "drain"}
# Subcommands that reach the cluster; the rest render or fetch locally. A helmfile spreads
# its releases over namespaces, so -n is not required.
HELMFILE_CLUSTER = HELMFILE_RELEASE_WRITES | {"diff", "status", "test"}


def has_namespace(seen):
    return bool(seen.get("-n") or seen.get("--namespace") or seen.get("-A"))


def kubectl_denial(prog, args):
    rest, seen = split_globals(args, KUBECTL_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    verb = pos[0] if pos else ""
    sub = pos[1] if len(pos) > 1 else ""
    # stern reaches a cluster whatever its arguments; kubectl may not.
    if prog in KUBECTL_PROGRAMS and (not pos or verb in KUBECTL_LOCAL
                                     or (verb == "version" and "--client" in rest)):
        return None
    if not seen.get("--context"):
        return KUBECTL_CONTEXT
    namespace_free = prog in KUBECTL_PROGRAMS and (
        (verb, sub) in NAMESPACE_FREE or verb in NODE_VERBS
        or (verb == "get" and has_flag(rest, "--raw")))
    if not has_namespace(seen) and not namespace_free:
        return KUBECTL_NAMESPACE
    return None


def helm_denial(args):
    _, seen, pos = helm_words(args)
    if not pos or pos[0] in HELM_LOCAL:
        return None
    if not seen.get("--kube-context"):
        return HELM_CONTEXT
    if not has_namespace(seen):
        return HELM_NAMESPACE
    return None


def helmfile_denial(args):
    rest, seen = split_globals(args, HELMFILE_GLOBAL_VALUE_FLAGS)
    pos = positionals(rest)
    sub = pos[0] if pos else ""
    # A subcommand the shell builds at run time could be any of the cluster ones.
    if (sub in HELMFILE_CLUSTER or "$" in sub) and not seen.get("--kube-context"):
        return HELMFILE_CONTEXT
    return None


def invocation_denial(prog, args):
    """Why one program invocation is denied, or None when it names its target or needs none."""
    if help_only(prog, args):
        return None
    if prog in KUBECTL_PROGRAMS or prog == "stern":
        return kubectl_denial(prog, args)
    if prog == "helm":
        return helm_denial(args)
    if prog == "helmfile":
        return helmfile_denial(args)
    return None


def denial(command):
    """Why a Bash command is denied - its first invocation that misses a pin, nested ones
    included - or None."""
    for outer in invocations(with_assigned_path(command)):
        for prog, args in uv_run_invocations(*outer):
            reason = invocation_denial(prog, args)
            if reason:
                return reason
    return None


def hook_output(payload):
    """The hook's output for one call, or None when it has nothing to deny."""
    tool_input = payload.get("tool_input")
    if (payload.get("tool_name") != "Bash" or not isinstance(tool_input, dict)
            or not isinstance(tool_input.get("command"), str)):
        return None
    reason = denial(tool_input["command"])
    if reason is None:
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def main():
    result = hook_output(json.load(sys.stdin))
    if result is not None:
        json.dump(result, sys.stdout)


def selftest():
    cases = [
        # (command, the reason it is denied for, or None when it passes)
        ("kubectl get pods --context X -n Y", None),
        ("kubectl get pods --context=X --namespace=Y", None),
        ("kubectl get pods -nY --context X", None),
        ("kubectl --context X -n Y get pods", None),
        ("kubectl get pods \\\n  --context X -n Y", None),
        ("kubectl get pods -A --context X", None),
        ("kubectl delete pod p -n Y", KUBECTL_CONTEXT),
        ("kubectl get pods --context X", KUBECTL_NAMESPACE),
        ("kubectl get policies --context X", KUBECTL_NAMESPACE),
        ("kubectl label pod p a=b --context X", KUBECTL_NAMESPACE),
        ("kubectl certificate approve x --context X", KUBECTL_NAMESPACE),
        # An empty kubeconfig is no pin: inside a pod client-go falls back to its service account.
        ("kubectl create secret generic t --kubeconfig=/dev/null --dry-run=client -o yaml",
         KUBECTL_CONTEXT),
        # A verb built at run time still runs against some cluster.
        ("kubectl $(echo delete) pod p --context X -n Y", None),
        ("kubectl $(echo delete) pod p", KUBECTL_CONTEXT),
        ("echo $(ls); kubectl delete pod p --context X -n Y", None),
        # Cluster-scoped: the context alone.
        ("kubectl get nodes --context X -L atero/user", None),
        ("kubectl get nodes -L atero/user", KUBECTL_CONTEXT),
        ("kubectl get --raw /api/v1/nodes/n/proxy/stats/summary --context X", None),
        ("kubectl get crd --context X", None),
        ("kubectl get namespaces --context X", None),
        ("kubectl get clusterpolicies --context X", None),
        ("kubectl describe cpol cell-pin --context X", None),
        ("kubectl label node n atero/user=x --context X", None),
        ("kubectl label node n atero/user=x", KUBECTL_CONTEXT),
        ("kubectl taint nodes n k=v:NoSchedule --context X", None),
        ("kubectl cordon n --context X", None),
        ("kubectl drain n --context X --ignore-daemonsets", None),
        # Subcommands that never reach a cluster, and help.
        ("kubectl config get-contexts", None),
        ("kubectl config use-context x", None),
        ("kubectl kustomize ./overlay", None),
        ("kubectl krew install ctx", None),
        ("kubectl completion zsh", None),
        ("kubectl version --client", None),
        ("kubectl version", KUBECTL_CONTEXT),
        ("kubectl ctx", KUBECTL_CONTEXT),
        ("kubectl get pods --help", None),
        ("kubectl --help", None),
        # A --help after `--` belongs to the command in the pod, so kubectl still runs.
        ("kubectl exec p -- sh -c 'rm -rf /data' --help", KUBECTL_CONTEXT),
        ("kubectl exec p --context X -n Y -- curl localhost:8000/health", None),
        ("stern x --context X -n Y", None),
        ("stern x", KUBECTL_CONTEXT),
        ("stern x --context X", KUBECTL_NAMESPACE),
        # stern's first word is a pod query, never a kubectl verb.
        ("stern drain --context X", KUBECTL_NAMESPACE),
        ("stern --help", None),
        ("oc get pods", KUBECTL_CONTEXT),
        # A nested command is held to the same rule.
        ("bash -c 'kubectl get pods'", KUBECTL_CONTEXT),
        ("kubectl get pods -o name --context X -n Y | xargs kubectl delete", KUBECTL_CONTEXT),
        ("find . -name x -exec kubectl delete pod p \\;", KUBECTL_CONTEXT),
        ("uv --color never run kubectl delete pod p -n Y", KUBECTL_CONTEXT),
        ("kubectl get pods --context X -n Y && kubectl get pods -n Y", KUBECTL_CONTEXT),
        ("helm list --kube-context X -n Y", None),
        ("helm --kube-context X -n Y uninstall r", None),
        ("helm upgrade r ./c --kube-context X -n Y", None),
        ("helm $(echo uninstall) r --kube-context X -n Y", None),
        ("helm list --kube-context X -A", None),
        ("helm uninstall r", HELM_CONTEXT),
        ("helm list -n Y", HELM_CONTEXT),
        ("helm install r ./c -n Y", HELM_CONTEXT),
        ("helm list --kube-context X", HELM_NAMESPACE),
        ("helm template r ./chart -f values.yaml", None),
        ("helm dep build ./chart", None),
        ("helm repo list", None),
        ("helm version", None),
        ("helm upgrade --help", None),
        ("helmfile --kube-context X apply", None),
        ("helmfile --kube-context X diff", None),
        ("helmfile apply", HELMFILE_CONTEXT),
        ("helmfile status", HELMFILE_CONTEXT),
        ("helmfile $X", HELMFILE_CONTEXT),
        ("helmfile template", None),
        # The path a first statement assigns is read in place of its variable.
        ("D=/x; helmfile $D", None),
        ("ls -la", None),
    ]
    failures = 0
    for command, expected in cases:
        got = denial(command)
        ok = got == expected
        failures += not ok
        shown = command.replace("\n", "\\n")
        print(f"{'ok  ' if ok else 'FAIL'} {shown} -> {got}" + ("" if ok else f" (want {expected})"))
    payload_cases = [
        ({"tool_name": "Bash", "tool_input": {"command": "kubectl get pods"}}, KUBECTL_CONTEXT),
        ({"tool_name": "Bash", "tool_input": {"command": "kubectl get pods --context X -n Y",
                                              "description": "lists pods"}}, None),
        ({"tool_name": "Read", "tool_input": {"file_path": "/x"}}, None),
        ({"tool_name": "Bash"}, None),
        ({"tool_name": "Bash", "tool_input": {"command": None}}, None),
    ]
    for payload, expected in payload_cases:
        out = (hook_output(payload) or {}).get("hookSpecificOutput", {})
        got = out.get("permissionDecisionReason")
        ok = got == expected and (expected is None or out.get("permissionDecision") == "deny") \
            and "updatedInput" not in out
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} payload {payload} -> {got}"
              + ("" if ok else f" (want {expected})"))
    total = len(cases) + len(payload_cases)
    print(f"\n{total - failures}/{total} passed")
    return failures == 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    main()
