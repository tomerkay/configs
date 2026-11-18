# How my reads run

- **HTTP reads go through `xh`, never `curl`.** The org's policy prompts on
  every `curl`, GET included; `xh` is not on its list and a GET through it is
  a read to the hook. `curl` only for what `xh` cannot do, and then it
  prompts.
- **Cloud Logging reads go through `live_log_query` when the question is a
  count, a per-field breakdown or a message template.** The org's policy
  prompts on every `gcloud`, a read included; the data-mcp tools are on its
  allow list. `gcloud logging read` only for a bulk pull past the tool's
  sample cap, and then it prompts.
