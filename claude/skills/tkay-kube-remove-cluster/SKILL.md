---
name: tkay-kube-remove-cluster
description: Remove one or more clusters (cluster + context + user entries) from ~/.kube/config using kubectl config commands. Use when the user asks to remove/delete a cluster, context, or entry from their kubeconfig.
---

# Remove cluster from kubeconfig

Remove all traces of a cluster from `~/.kube/config`: its `context` entry, its `cluster` entry, and its `user` entry.

**NEVER Read or Edit ~/.kube/config directly.** The file is full of multi-KB base64 cert blobs — reading it wastes context, and exact-match edits break the moment kubectl rewrites the file (any `kubectl config use-context` reorders it). Always use `kubectl config` subcommands; they handle the YAML atomically in one shot.

All commands below that modify the file must run with sandbox disabled (`~/.kube/config` is outside the sandbox write allowlist — the user has approved this workflow). The global allowlist has rules for `kubectl config delete-context:*` / `delete-cluster:*` / `delete-user:*` and the exact backup command — use the exact command forms written below (including the literal `~/.kube/config` paths) so they match without prompting.

## Steps

Input: one or more context/cluster names (e.g. `***REMOVED***`). If the user gave a partial name, resolve it against `kubectl config get-contexts -o name` first.

1. **Backup** (cheap insurance — client keys are not recoverable):
   ```
   cp ~/.kube/config ~/.kube/config.bak
   ```

2. **Resolve the referenced cluster and user** for each context name `$NAME`:
   ```
   kubectl config view -o jsonpath="{.contexts[?(@.name=='$NAME')].context.cluster}"
   kubectl config view -o jsonpath="{.contexts[?(@.name=='$NAME')].context.user}"
   ```
   Crusoe CMK convention: context and cluster share the name, user is `crusoe-client-admin-<name>` — but always resolve, never assume.

3. **Delete the context first**, then the cluster and user — but only delete the cluster/user if no OTHER remaining context still references them:
   ```
   kubectl config delete-context "$NAME"
   kubectl config view -o jsonpath='{range .contexts[*]}{.context.cluster}{"\n"}{end}' | grep -qx "$CLUSTER" || kubectl config delete-cluster "$CLUSTER"
   kubectl config view -o jsonpath='{range .contexts[*]}{.context.user}{"\n"}{end}' | grep -qx "$USER_ENTRY" || kubectl config delete-user "$USER_ENTRY"
   ```

4. **Fix current-context if it was the deleted one**: `kubectl config current-context` — if it errors or still names the deleted context, tell the user and ask which context to switch to (do not pick one for them).

5. **Verify**:
   ```
   grep -c "$NAME" ~/.kube/config   # expect 0
   kubectl config get-contexts -o name | head -3   # confirms the file still parses
   ```

6. Report what was deleted (context/cluster/user names), that a backup exists at `~/.kube/config.bak`, and the current-context state.
