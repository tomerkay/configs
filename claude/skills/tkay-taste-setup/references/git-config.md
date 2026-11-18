# Git Configuration

Commits are signed, as the `tkay-code` commit standard says. My configuration:

- `git config --global gpg.format openpgp`
- `git config user.email "tkay@crusoeenergy.com"`
- `git config user.signingkey D07B37AA6558492679499A20DB915178326D62E2`
- `git config commit.gpgsign true`

**What my sandbox blocks for git**, which `tkay-tool-use`'s
`git-in-sandbox.md` says to run outside it: anything that reaches the remote
over SSH, which its proxy refuses; any checkout, reset, rebase or
cherry-pick whose files include a repo's `.claude/` skills, hooks or
settings, which it will not write; and a directory named `secrets`, which it
hides.
