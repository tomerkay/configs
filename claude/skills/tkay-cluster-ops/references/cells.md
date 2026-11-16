# Every workload lands in my cell

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
or the cell has no nodes, **stop and shout**: name the cell it belongs to and
ask before installing. Deploying into someone else's cell takes their GPUs,
and nobody finds out until they look.

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
