# Every workload lands in my cell

**Every workload I deploy lands in my cell.** The dev clusters hand GPU nodes
out as cells, one namespace per cell. Before any install or upgrade, check that
the namespace is a cell of mine and that the cell has nodes (`kubectl get nodes
--context <ctx> -L dedicated,cell-display-name`). If you do not know which cell
is mine, ask - never infer it from another workload. If the namespace is
someone else's cell, or the cell has no nodes, **stop and shout**: name the
cell it belongs to and ask before installing. Deploying into someone else's
cell takes their GPUs, and nobody finds out until they look.
