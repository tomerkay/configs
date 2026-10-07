#!/usr/bin/env bash
#
# Copy this host's configuration files into the repo, strip the private
# blocks, have Claude review the diff, commit and push. launchd runs it twice
# a day. See README.md.

set -euo pipefail

# launchd starts with a near-empty PATH and would find neither git, ssh nor
# claude.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# claude finds its keychain entry by username, and launchd does not set these.
export USER="${USER:-$(id -un)}"
export LOGNAME="${LOGNAME:-$USER}"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$REPO/sync-configs.log"

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

# Files that must carry a private block: with the markers gone the strip below
# is a silent no-op and the block reaches the remote.
PRIVATE_FILES=(
    .zprofile
    .zshrc
)

CLAUDE_FILES=(
    CLAUDE.md
    settings.json
    settings.local.json
)

PRIVATE_OPEN='# >>> PRIVATE >>>'
PRIVATE_CLOSE='# <<< PRIVATE <<<'

SECRET_PATTERN='gh[oprsu]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_.-]{20,}|hf_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AUTH for claude|INFLECTION_APIKEY=.|://[^/@[:space:]]+:[^/@[:space:]]+@'

REVIEW_MODEL='haiku'
REVIEW_SYSTEM_PROMPT='Unattended pre-commit review of a diff for a public dotfiles repo. An added line is UNSAFE if it holds a credential (key, token, password, private key, webhook URL), a non-public hostname or IP, a cluster, context, node or namespace name, or a personal e-mail address. The owner handle, work e-mail, employer name, GPG fingerprint, home-directory paths, test fixtures and placeholders such as <ctx>, $NS or C0OTHER are fine; flag only values that are evidently real. Reply with one line per finding (file, the added line, why), then a final line that is exactly CLEAN or UNSAFE. Nothing after the verdict.'

push=true
if [ "${1:-}" = "--no-push" ]; then
    push=false
fi

# The script appends to the log itself so a manual run is recorded like a
# scheduled one; launchd captures only stderr, for failures nothing here logged.
# One block per run: a separator, the start time, the lines, a total.
log() { printf '%s\n' "$*" | tee -a "$LOG_FILE"; }
die() { log "ERROR: $*"; exit 1; }
review_calls=0
review_tokens=0
trap 'log "total: $review_calls claude call(s), $review_tokens tokens"' EXIT
log ""
log "$(printf '=%.0s' $(seq 60))"
log "$(date '+%Y-%m-%d %H:%M:%S')"

install_file() {
    local src="$1" dst="$REPO/$2"
    [ -f "$src" ] || die "missing source file: $src"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
}

# A file without markers copies through unchanged; one with an opening marker
# and no closing one would strip to the end of the file, so the count has to
# balance.
install_home_file() {
    local src="$HOME/$1" dst="$REPO/home/$1" opens closes
    [ -f "$src" ] || die "missing source file: $src"
    opens="$(grep -cxF "$PRIVATE_OPEN" "$src" || true)"
    closes="$(grep -cxF "$PRIVATE_CLOSE" "$src" || true)"
    [ "$opens" = "$closes" ] || die "unbalanced private markers in $src"
    mkdir -p "$(dirname "$dst")"
    sed "/^$PRIVATE_OPEN\$/,/^$PRIVATE_CLOSE\$/d" "$src" >"$dst"
}

# Only the added lines of the staged diff are reviewed: everything older is
# already on the remote, and a removed line cannot leak, so sending either
# spends tokens and invites a verdict about content that is not being
# published. The call carries no tools, no settings, no CLAUDE.md and no
# thinking, so those lines are nearly the whole input.
review_staged() {
    local added response usage result verdict
    added="$(git diff --cached -U0 --no-color | grep -E '^(diff --git |\+[^+])' || true)"
    if [ -z "$added" ]; then
        log "review skipped: no added lines"
        return
    fi
    response="$(printf '%s\n' "$added" | (cd /tmp && claude -p 'Review these added lines.' \
        --model "$REVIEW_MODEL" \
        --output-format json \
        --tools "" \
        --disallowedTools 'mcp__*' \
        --setting-sources "" \
        --settings '{"env":{"MAX_THINKING_TOKENS":"0"}}' \
        --system-prompt "$REVIEW_SYSTEM_PROMPT" \
        --no-session-persistence))" \
        || die "review call failed: ${response:0:300}"
    usage="$(printf '%s' "$response" | jq -r --arg model "$REVIEW_MODEL" \
        '"model=\($model) in=\(.usage.input_tokens) out=\(.usage.output_tokens) cache_read=\(.usage.cache_read_input_tokens) cache_write=\(.usage.cache_creation_input_tokens)"')"
    log "CLAUDE review: $usage"
    review_calls=1
    review_tokens="$(printf '%s' "$response" | jq -r \
        '.usage | .input_tokens + .output_tokens + .cache_read_input_tokens + .cache_creation_input_tokens')"
    # The verdict is the last line because the model reasons in its reply
    # before it concludes, and an opening word can contradict the conclusion.
    result="$(printf '%s' "$response" | jq -r '.result')"
    verdict="$(printf '%s\n' "$result" | tail -n 1)"
    case "$verdict" in
        CLEAN) log "review verdict: CLEAN" ;;
        UNSAFE)
            log "review verdict: UNSAFE, nothing committed:"
            printf '%s\n' "$result" | tee -a "$LOG_FILE"
            exit 1 ;;
        *) die "review gave no verdict: ${result:0:300}" ;;
    esac
}

for f in "${PRIVATE_FILES[@]}"; do
    grep -qxF "$PRIVATE_OPEN" "$HOME/$f" || die "no '$PRIVATE_OPEN' marker in ~/$f"
    grep -qxF "$PRIVATE_CLOSE" "$HOME/$f" || die "no '$PRIVATE_CLOSE' marker in ~/$f"
done

for f in "${HOME_FILES[@]}"; do
    install_home_file "$f"
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

rm -rf "$REPO/claude/hooks"
cp -R "$HOME/.claude/hooks" "$REPO/claude/hooks"

# This file is excluded because SECRET_PATTERN would match its own source.
found="$(grep -rInE "$SECRET_PATTERN" "$REPO" \
    --exclude-dir=.git --exclude="$(basename "$0")" | cut -d: -f1,2 || true)"
if [ -n "$found" ]; then
    log "credential-shaped content found, nothing committed:"
    printf '%s\n' "$found" | tee -a "$LOG_FILE"
    exit 1
fi

cd "$REPO"

if [ -z "$(git status --porcelain)" ]; then
    log "no changes"
else
    git add -A
    review_staged
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
