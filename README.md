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
has Claude review the staged diff, commits and pushes. It holds the list of files
it syncs; nothing else does. Pass `--no-push` to leave the commit local.

Every run, scheduled or manual, appends to `sync-configs.log` in this directory,
which is gitignored. `bin/install-launchd.sh` registers the script with launchd
for the schedule it names. It runs as a LaunchAgent and not from cron because
cron runs outside the login session and cannot reach the keychain that holds the
`claude` CLI's login, so the review call fails there.

`claude/skills/` holds the `tkay-*` skills from `~/.claude/skills` and nothing
else: the prefix marks a skill as hand-written, so anything installed from a
public repo or synced from the claude.ai account stays out. The directory is
rebuilt on every run, so a skill deleted or renamed at home disappears here too.
`claude/hooks/` is rebuilt the same way from all of `~/.claude/hooks`.

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
