# About Me and My Work

My name is Tomer. I am a software engineer for Atero, who were purchased by Crusoe. Atero is now the Israel site of Crusoe, and we are in charge of the cloud service, focused on offering the best LLM inference out there in the world. I am not training, so most likely any question I have regards inference and not training.

**My handle is `tkay`**, and every place that names me uses it:

- **Branch names** - when a repo's convention puts a person in the name, that
  person is `tkay`, never `tomerk`, `tomerkay`, `tomer` or any other spelling,
  even where older branches of mine use one.
- **Branch ownership** - a branch I created is mine alone, and I force-push my
  branches.
- **Dev cluster capacity** - my GPUs come through my cells in the backoffice.

What I work on and with:

- LLM inference, utilizing vllm and sglang. When I use `PD` I mean the disaggregation setup.
- When I say `unified clusters` I mean the cell structure: a cluster carved into
  `cell-<id>` namespaces, one per customer slice, next to the older layout where
  one tenant filled a single shared namespace. Per cell is per namespace.
- Grafana (including grafana alerts) for my dashboards and the promql for the queries.
- kubernetes and helm for my deployments. **Every command that touches a cluster
  pins the context and the namespace explicitly - see "Always pin the context and
  the namespace".**
- Python language (utilizing asyncio) and sometimes Rust. I am using uv for Python virtual environment.
- Mac, but also works on remote machines that are Linux. When I ask you how to run any commands or anything in general answer to both setups, but never answer about Windows!
- zsh, tmux, vim
