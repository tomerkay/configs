# Reading GitLab from the host

`glab` is the tool for everything on gitlab.com a task needs read: an MR,
its review threads, its pipelines, a job log. It stays inside the sandbox
and its token stays inside glab - the one failure that makes both look
impossible has a one-variable fix.

## The TLS failure and its fix

Inside the sandbox on a Mac every glab call fails with
`tls: failed to verify certificate: x509: OSStatus -26276`, while `curl`
reaches the same host. The sandbox proxy only tunnels the connection:
`curl -v` shows gitlab.com's own certificate chain, nothing intercepted,
so the certificate is fine and the verifier is what broke. glab is Go, and
Go on macOS hands verification to the Security framework, which the
sandbox cuts off from the trust store. Go on Linux reads the PEM bundle
itself and does not hit this.

The fix is glab's own `ca_cert` setting, set on the command:

```
GLAB_CA_CERT=/etc/ssl/cert.pem glab api ...
```

Given a root pool, Go verifies in pure Go against that bundle and never
asks the Security framework. Should Linux ever fail the same way, the
bundle is the distribution's own (`/etc/ssl/certs/ca-certificates.crt` on
Debian and Ubuntu). `glab config --help` lists `ca_cert` and its
environment variable; a glab that does not list it predates the setting.

Two things that look like fixes and are not:

- `dangerouslyDisableSandbox` on the call. The failure is not the sandbox
  network filter, the auto-mode classifier may refuse the bypass on a
  GitLab read, and the variable makes the sandboxed call work.
- Reading the token out (`glab auth status --show-token`, glab's config
  file) to hand it to `curl`. That materialises a credential, the
  classifier refuses it, and nothing needs it once glab itself works.

The workaround expires when a plain `glab api version` succeeds in the
sandbox without the variable: drop the variable and this section then.

## The reads

In auto mode each call declares `allowed_domains: ["gitlab.com"]`. The
project path is URL-encoded, `crusoeenergy%2Fatero%2F<repo>`.

- The MR and its description: `glab mr view <iid>`.
- Review threads, with the file and line each anchors to:
  `glab api "projects/<project>/merge_requests/<iid>/discussions?per_page=100"`.
  A note with `system: true` is GitLab's own activity line, not a review;
  `resolvable` and `resolved` say which threads still stand, and
  `position.new_path` with `position.new_line` says where. The AI
  reviewer's findings arrive as collapsed `<details>` blocks in `body`.
- The MR's pipelines: `projects/<project>/merge_requests/<iid>/pipelines`.
  The one the MR has to pass runs on `refs/merge-requests/<iid>/merge`,
  the merged result, so its sha is not the branch tip's.
- A pipeline's jobs: `projects/<project>/pipelines/<id>/jobs`; a job's
  log: `projects/<project>/jobs/<id>/trace`, read from the tail with the
  ANSI escapes stripped.

Every one of these is a read. Posting a note, resolving a thread or
anything else that writes to the MR is a message sent on my behalf and
asks first, like any other outward-facing action.
