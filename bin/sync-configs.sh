#!/usr/bin/env bash
#
# Copy this host's configuration files into the repo, strip the credentials,
# commit and push. Cron runs it twice a day. See README.md.

set -euo pipefail

# cron starts with a near-empty PATH and would find neither git nor ssh.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="$(cd "$(dirname "$0")/.." && pwd)"

HOME_FILES=(
    .bashrc
    .config/git/ignore
    .config/pip/pip.conf
    .gitconfig
    .gitignore
    .oh-my-zsh/themes/my_theme.zsh-theme
    .screenrc
    .tmux.conf
    .vimrc
    .zprofile
    .zshrc
    .zshrc.crusoe
)

CLAUDE_FILES=(
    CLAUDE.md
    settings.json
)

TOKENS_OPEN='# >>> TOKENS >>>'
TOKENS_CLOSE='# <<< TOKENS <<<'

SECRET_PATTERN='gh[oprsu]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_.-]{20,}|hf_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AUTH for claude|INFLECTION_APIKEY=.|://[^/@[:space:]]+:[^/@[:space:]]+@'

push=true
if [ "${1:-}" = "--no-push" ]; then
    push=false
fi

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

install_file() {
    local src="$1" dst="$REPO/$2"
    [ -f "$src" ] || die "missing source file: $src"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
}

for f in "${HOME_FILES[@]}"; do
    install_file "$HOME/$f" "home/$f"
done

for f in "${CLAUDE_FILES[@]}"; do
    install_file "$HOME/.claude/$f" "claude/$f"
done

# The tkay- prefix is what marks a hand-written skill; everything else under
# ~/.claude/skills is installed from a public repo or synced from claude.ai.
# Rebuilt from scratch so a skill deleted at home disappears here too.
rm -rf "$REPO/claude/skills"
mkdir -p "$REPO/claude/skills"
cp -R "$HOME"/.claude/skills/tkay-* "$REPO/claude/skills/"

# A renamed or hand-deleted marker turns the strip below into a silent no-op and
# publishes every token in the file, so refuse to continue without both.
grep -qxF "$TOKENS_OPEN" "$HOME/.zshrc" || die "no '$TOKENS_OPEN' marker in ~/.zshrc"
grep -qxF "$TOKENS_CLOSE" "$HOME/.zshrc" || die "no '$TOKENS_CLOSE' marker in ~/.zshrc"

sed "/^$TOKENS_OPEN\$/,/^$TOKENS_CLOSE\$/d" "$HOME/.zshrc" >"$REPO/home/.zshrc"

# This file is excluded because SECRET_PATTERN would match its own source.
found="$(grep -rInE "$SECRET_PATTERN" "$REPO" \
    --exclude-dir=.git --exclude="$(basename "$0")" | cut -d: -f1,2 || true)"
if [ -n "$found" ]; then
    log "credential-shaped content found, nothing committed:"
    printf '%s\n' "$found" >&2
    exit 1
fi

cd "$REPO"

if [ -z "$(git status --porcelain)" ]; then
    log "no changes"
else
    git add -A
    git commit -q -m "chore: sync configs from $(hostname -s)"
    log "committed $(git rev-parse --short HEAD)"
fi

# Checked separately from the commit above: a commit left behind by --no-push,
# or by a run that died before pushing, would otherwise sit local forever
# because the next run finds nothing to copy and stops.
if [ -z "$(git log --oneline '@{u}..HEAD')" ]; then
    log "nothing to push"
    exit 0
fi

if [ "$push" = true ]; then
    git push -q
    log "pushed to $(git remote get-url origin)"
else
    log "--no-push given, commit left local"
fi
