# Git that the sandbox blocks runs outside it from the first call

**When a git operation reaches something the sandbox blocks - the remote over
SSH, a path it will not write, a directory it hides - run it with the sandbox
off from the first call.** Inside, it dies halfway and leaves the working
tree half-updated: a checkout, reset, rebase or cherry-pick that touches a
blocked path stops partway through, and a fetch over a refused connection
fails after the work around it ran.

**To learn what a blocked path holds, ask git** - `git ls-tree`, `git show` -
which reads objects, not the directory, and works inside the sandbox.
