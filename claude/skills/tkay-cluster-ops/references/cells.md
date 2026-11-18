# Every workload lands in my cell

**Every workload I deploy lands in my cell.** The dev clusters hand GPU nodes
out as cells, one namespace per cell, named by its backoffice cell record -
the record that owns it. Before any install or upgrade, check that the
namespace is a cell of mine and that the cell has nodes (`kubectl get nodes
--context <ctx> -L dedicated,cell-display-name`). If you do not know which
cell is mine, read it from the backoffice cell records or ask - never from a
copy written down, since cells move, and never from another workload. If the
namespace is someone else's cell, or the cell has no nodes, **stop and
shout**: name the cell it belongs to and ask before installing. Deploying
into someone else's cell takes their GPUs, and nobody finds out until they
look.

**When I say "unified clusters" I mean this cell layout**: one namespace per
customer slice, next to the older layout where one tenant filled a single
shared namespace. Per cell is per namespace.
