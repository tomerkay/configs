# GitLab from the host

`glab` is the tool for everything a task needs on gitlab.com: reading an
MR, its review threads, its pipelines or a job log, and uploading a file.
It stays inside the sandbox and its token stays inside glab - the one
failure that makes both look impossible has a one-variable fix.

**Before deciding glab cannot make a request, read `glab api --help`.**
Between `--form` for `multipart/form-data`, and `--input` with
`--header` for a raw body of any type, it shapes any request the REST API
takes, so "glab has no flag for this" is never a reason to reach for the
token. "Uploading a file" below is the case that taught it.

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
  `glab api --paginate "projects/<project>/merge_requests/<iid>/discussions?per_page=100"`.
  **The reviews of an MR are every discussion on it, read together**: the
  inline findings, the reviewer's summary note, the replies under each and
  every human comment. A `#note_<id>` on the link I give you is where
  the browser scrolls, never a filter on what to read: a finding read
  alone cannot say whether it was answered, resolved or restated, and a
  summary read alone lists findings whose own thread holds the replies.
  `--paginate` follows every page and prints one JSON array per page, so
  an MR with more discussions than one page holds is still read whole.
  A note with `system: true` is GitLab's own activity line, not a review;
  `resolvable` and `resolved` say which threads still stand, and
  `position.new_path` with `position.new_line` says where. The AI
  reviewer's findings arrive as collapsed `<details>` blocks in `body`:
  one thread per inline finding, and a "Review complete" summary in a
  thread of its own with no position, whose details list the findings
  together. The case that taught it: a link anchored at one inline
  finding, with the summary sitting in a separate thread the anchor never
  pointed at.
- The MR's pipelines: `projects/<project>/merge_requests/<iid>/pipelines`.
  The one the MR has to pass runs on `refs/merge-requests/<iid>/merge`,
  the merged result, so its sha is not the branch tip's.
- A pipeline's jobs: `projects/<project>/pipelines/<id>/jobs`; a job's
  log: `projects/<project>/jobs/<id>/trace`, read from the tail with the
  ANSI escapes stripped.

Every one of these is a read. Posting, editing or deleting a note or a
draft note, resolving or reopening a thread, or anything else that writes
to the MR is a message sent on my behalf: run it only when my message
allows that command in plain words, and otherwise print it, the note's
full text included, for me to run myself. A review I asked for on an MR
link writes nothing to it either - the `tkay-review` skill's standard says
so under "A CR asked for on a link".

## Uploading a file

An image in an MR description or a note is an upload to the project:
`POST projects/<project>/uploads` with a `multipart/form-data` body
holding one part named `file`. The JSON answer carries `markdown`,
`![name](/uploads/<hash>/name.png)`, and that is what goes into the text.

`--form` sends it. `-F` is the trap: in curl it means a form part, in
glab it is `--field`, which reads the file into a JSON field, and GitLab
refuses it:

```
❌ glab api --method POST "projects/<project>/uploads" -F "file=@shot.png"
   → HTTP 400
✅ glab api --method POST "projects/<project>/uploads" --form "file=@shot.png" | jq -r '.markdown'
```

A glab whose `glab api --help` does not list `--form` predates it: build
the multipart body in a scratch file, with `\r\n` line breaks, and send it
with `--input` and `--header "Content-Type: multipart/form-data;
boundary=<boundary>"`.

It declares `allowed_domains` in auto mode like every call above.

An upload is a write on my behalf, like a note: run it only when my
message allows it in plain words.

**A screenshot I ask to upload to an MR goes into its description.** The
upload alone shows nowhere on the MR: the image appears only once its
markdown is in the description or a note. So the ask covers both steps -
the upload, then one `PUT projects/<project>/merge_requests/<iid>` with a
JSON body whose `description` is the current text, read from the MR
right before, with the markdown appended under a `## Screenshots`
heading and a caption per view. A note gets it only when I name a note.
The case that taught it: twelve screenshots uploaded, their links handed
back in chat, and the MR page still showing none of them.

**An upload outlives the text that links it.** Replacing an image in a
description stores the new file beside the old one: the old one leaves
the MR but stays stored in the project, reachable at its URL. So when
images change, upload only the ones that changed and keep the other links
as they are, and say when asking that the old files stay stored.

Deleting one is `DELETE projects/<project>/uploads/<secret>/<filename>`,
with both parts read off its `/uploads/<secret>/<filename>` link, and it
needs the Maintainer role or above
([GitLab docs](https://docs.gitlab.com/api/project_markdown_uploads/));
Developer gets HTTP 403. Before offering one, read my access level:
`glab api user | jq .id`, then
`glab api "projects/<project>/members/all/<id>" | jq .access_level`.
`40` or above can delete; below it, say a maintainer of the project has
to, instead of handing me a command that fails. A delete is a write on my
behalf like the upload.
