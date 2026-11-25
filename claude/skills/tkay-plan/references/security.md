# Security: what would an auditor write about this?

**Read every component as an outside auditor, a security researcher or an
analyst writing about the company would - when writing it and when reviewing
it.** Anything they could write down that makes us look careless is a
finding, whether or not anyone has exploited it. The company is judged on what
that report says, not on whether the hole was ever used.

Ask these of every change and every design, and of the component it lands
in; in a plan, write each answer into the fix - "not exposed, because
<reason>" included:

- **Does anything cross a network in plaintext?** HTTP where HTTPS exists, an
  insecure gRPC channel, TLS verification switched off (`verify=False`,
  `InsecureSkipVerify`, `curl -k`). Inside the cluster counts too: "it is an
  internal network" is the first line such a report quotes.
- **Can a secret leak?** A token, key or password in source, a values file, an
  image layer, a URL or query string, a log line, an error message, a metric
  label or a startup dump of the environment. A secret comes from a secret
  store at run time and is never printed.
- **Does customer data go where the customer did not send it?** Prompts,
  completions, request bodies or user identifiers in logs, traces, metrics,
  crash dumps or a third-party service. Log a request's ID and shape, never
  its content.
- **Can one tenant reach another?** A shared cache, queue, volume or namespace
  through which one customer's data or traffic reaches another's, or a lookup
  keyed on something the caller controls.
- **Is every endpoint authenticated, and reachable only by who needs it?** An
  admin, debug, metrics or profiling endpoint exposed past its users, a
  default credential, a firewall rule open to `0.0.0.0/0`, a LoadBalancer
  where a ClusterIP would do.
- **Does it run with more than it needs?** Root in the container,
  `privileged`, `hostNetwork`, a wildcard RBAC rule, a cloud role broader than
  its one job.
- **Can input reach a shell, a query or a path?** A shell command, SQL, file
  path or template built from anything the caller sends.
- **Is what it pulls in trusted?** An unpinned image or dependency, a
  `curl | sh`, a package from an unknown source, a dependency with a known
  CVE, home-grown crypto, MD5 or SHA-1 used for security.

**Closing one of these exposures is not over-engineering, and not extra
scope.** The scenario that justifies it is the report that names it. A
control for an exposure nobody can reach is still over-engineering.

**An exposure found on the way is always reported**, never left unmentioned
because the change at hand did not cause it.
