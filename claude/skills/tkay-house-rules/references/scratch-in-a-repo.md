# A file a tool must find in a repo reaches it from scratch

**A file of your own that a tool must find somewhere else reaches it from
your scratch directory first.** A repo holds the change I asked for and no
throwaway file of yours.

- **A throwaway test a Go package must compile** goes in through
  `go test -overlay`, mapping its path in the package to the copy in scratch.
- **A throwaway Python test** runs where it is, with the repo's source and
  test directories on `PYTHONPATH`, the repo's fixtures loaded by
  `pytest -p conftest`, and `PYTHONDONTWRITEBYTECODE=1`.
- **A commit message** goes through `git commit -F` with its scratch path.

Only when no such route exists does the file go where the tool reads it,
and inside a repo only when the work cannot be done any other way. Such a
file is never staged or committed.
