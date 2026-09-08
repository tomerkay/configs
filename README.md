# configs

Personal machine configuration, kept here so a new Mac or Linux box can be brought
back to a known state.

## Layout

- `home/` — dotfiles, laid out exactly as they sit under `$HOME`
- `claude/` — Claude Code user configuration, laid out as it sits under `~/.claude/`
- `bin/` — the sync script

Restore by copying a file back to the matching path.

## Sync

`bin/sync-configs.sh` copies this host's files in, strips the credentials, commits
and pushes. It holds the list of files it syncs; nothing else does. Pass
`--no-push` to leave the commit local.

Cron runs it at 12:00 and 18:00:

```
0 12,18 * * * $HOME/repos/configs/bin/sync-configs.sh >> $HOME/Library/Logs/sync-configs.log 2>&1
```

`claude/skills/` holds hand-written skills only. A skill installed from a public
repo is skipped, whether it sits under `~/.claude/skills` as a symlink into
`~/.agents/skills` or as a real directory named in `~/.agents/.skill-lock.json`.
The directory is rebuilt on every run, so a skill deleted at home disappears here
too.

## Secrets

`~/.zshrc` keeps every credential between the `# >>> TOKENS >>>` and
`# <<< TOKENS <<<` markers. The sync deletes that block before committing, so the
committed `home/.zshrc` carries no token lines at all — fill them back in by hand
after a restore.

Two things stop a leak: the sync aborts if either marker has gone missing from
`~/.zshrc`, and it aborts if anything credential-shaped survives anywhere in the
tree.

These files hold nothing but credentials and are deliberately absent:

- `~/.zshenv`
- `~/.npmrc`
- `~/.netrc`
- `~/.github_token`
- `~/.config/glab-cli/config.yml`
