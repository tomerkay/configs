# configs

Personal machine configuration, kept here so a new Mac or Linux box can be brought
back to a known state.

## Layout

- `home/` — dotfiles, laid out exactly as they sit under `$HOME`
- `claude/` — Claude Code user configuration, laid out as it sits under `~/.claude/`
- `bin/` — the sync script and its launchd installer

Restore by copying a file back to the matching path.

## Sync

`bin/sync-configs.sh` copies this host's files in, strips the private blocks,
has Claude review the staged diff, commits and pushes. It holds the list of home
files it syncs. The Claude files are whatever the `~/.claude` git repo tracks,
so that repo's `.gitignore` allowlist decides them. Pass `--no-push` to leave
the commit local.

Every run, scheduled or manual, appends to `sync-configs.log` in this directory,
which is gitignored. `bin/install-launchd.sh` registers the script with launchd
for the schedule it names. It runs as a LaunchAgent and not from cron because
cron runs outside the login session and cannot reach the keychain that holds the
`claude` CLI's login, so the review call fails there.

`claude/` is rebuilt on every run from the files the `~/.claude` repo tracks,
except its `.gitignore`, which would ignore everything under `claude/` here. A
file changed at home is copied as it is, committed there or not. A new file is
copied once it is tracked there. A tracked file deleted at home stops the sync
until the deletion is committed there.

## Secrets

Every credential, private hostname and cluster name in a home file sits between
the `PRIVATE_OPEN` and `PRIVATE_CLOSE` markers the script defines. The sync
deletes those blocks before committing, so the committed copies carry none of
it — fill the blocks back in by hand after a restore. The files listed in
`PRIVATE_FILES` must carry a block; the others are copied as they are.

Three things stop a leak: the sync aborts if a required block is missing or a
marker is unbalanced, it aborts if anything matching `SECRET_PATTERN` survives
anywhere in the tree, and it has Claude read every added line of the staged
diff and refuses to commit on a finding. The review's token usage and verdict
are logged with the run; a refusal leaves the tree dirty for the next run to
retry once the source file is fixed.

These files hold nothing but credentials and are deliberately absent:

- `~/.zshenv`
- `~/.npmrc`
- `~/.netrc`
- `~/.github_token`
- `~/.config/glab-cli/config.yml`
