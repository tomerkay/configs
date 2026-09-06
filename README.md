# configs

Personal machine configuration, kept here so a new Mac or Linux box can be brought
back to a known state.

## Layout

- `home/` — dotfiles, laid out exactly as they sit under `$HOME`
- `claude/` — Claude Code user configuration, laid out as it sits under `~/.claude/`

Restore by copying a file back to the matching path.

## Secrets

`home/.zshrc` is committed with its credential values blanked. Fill in locally:
`HF_TOKEN`, `GITHUB_TOKEN`, `GITLAB_TOKEN`, `INFLECTION_APIKEY`.

These files hold nothing but credentials and are deliberately absent:

- `~/.zshenv`
- `~/.npmrc`
- `~/.netrc`
- `~/.github_token`
- `~/.config/glab-cli/config.yml`
