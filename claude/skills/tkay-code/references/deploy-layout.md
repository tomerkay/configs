# Dev and production deployment material in a repo

Where the files that install a service live says who they are for. Two
directories, two audiences, and nothing crosses between them.

## `deploy/` is production's

Everything production needs to be installed, and only that:

- **The installer** - the script, the helmfile or the GitOps manifests. A
  production installer never lives under `dev/`, however it started out. A
  reader who finds it there assumes it is a dev tool, and a reader of `dev/`
  assumes nothing in it can touch production. Both assumptions are what the
  directory names are for.
- **The topology** - which cluster, which namespace, which released version,
  which components. This is the one place a cluster name may appear in a repo
  ("Nothing personal in a repo" in my global CLAUDE.md).
- **Production values** for the charts this repo owns. Values for a chart
  another repo owns live in that repo's `examples/`, never here ("Values for a
  chart live with the chart").

## `dev/` targets a dev cluster and nothing else

Dev values with placeholders no node or cluster carries, mocks, tooling that
only makes sense against a dev cluster. Nothing production reads lives here,
and nothing here reads from `deploy/`. A dev install is the same chart as
production with the dev values and `--set` for whatever names the engineer:
image tag, node pin, cluster name. It does not run the production installer
against a dev topology. The installer has one audience, and a script that
serves both grows a mode switch that nobody tests on the production side.

## A hand-written installer is a stopgap, and says so

The idiom is a GitOps controller, ArgoCD here, reconciling one Application per
release from a chart version and a values file. A script that runs `helm
upgrade --install` from a topology file is the interim until those
Applications exist. Its header says that, and its inputs are shaped the way
the controller will take them: one values file per release, the version in
the topology, nothing the script computes that a controller could not. Then
the migration is a move, not a rewrite.

Do not grow the stopgap. Retries, waiting on a LoadBalancer, per-environment
branches, health polling: each is a feature the controller already has, and
each is a reason the migration never happens.

## Naming

The path reads as what it is: `deploy/deploy.py install deploy/prod.yaml` is
production at a glance, `dev/deploy.py` is not. The verbs (`install`,
`status`, `uninstall`) are the script's subcommands, so the script itself is
not named after one of them.
