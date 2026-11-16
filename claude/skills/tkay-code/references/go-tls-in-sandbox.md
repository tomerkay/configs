# A Go CLI fails TLS inside the sandbox on a Mac

A Go command-line tool that fails inside the sandbox on a Mac with
`tls: failed to verify certificate: x509: OSStatus -26276` is neither a
network block nor a bad certificate. The request reaches its host - `curl -v`
to the same host shows the host's own certificate chain, nothing intercepted -
but Go on macOS hands verification to the Security framework, which the
sandbox cuts off from the trust store. Go on Linux reads the PEM bundle itself
and does not hit this.

**The fix is a CA bundle the tool reads itself, when it has a setting for
one**: given a root pool, Go verifies in pure Go against that bundle and never
asks the Security framework. `/etc/ssl/cert.pem` is the bundle on macOS, and
`/etc/ssl/certs/ca-certificates.crt` on Debian and Ubuntu. `SSL_CERT_FILE`
does not help - Go ignores it on macOS. **A tool with no such setting runs with
the sandbox off.**

**Never read a credential out to hand it to another client** that does work
in the sandbox: that materialises a secret, and nothing needs it once the tool
itself works.

The workaround expires when the tool's plainest read succeeds inside the
sandbox without it.
