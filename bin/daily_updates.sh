#!/bin/sh
ZSH="$HOME/.oh-my-zsh"
export ZSH

# cron's PATH omits /opt/homebrew/bin, so every brew call exited 127.
PATH="/opt/homebrew/bin:$PATH"
export PATH

CLAUDE="$HOME/.local/bin/claude"
ATERO_MARKETPLACE=atero-skills
ATERO_BUNDLE="atero-skills@$ATERO_MARKETPLACE"
STATUS_FILE=/tmp/update_crontab.txt
BREW_FORMULAE="crusoe k9s gh glab uv kubectx pomerium/tap/pomerium-cli"
GO_PIN_REPO="$HOME/repos/data-path"

# A formula can keep older kegs until cleanup runs, so take the last (newest) column.
brew_version() {
	brew list --versions "$1" 2>/dev/null | awk '{print $NF}'
}

bundle_version() {
	jq -r --arg p "$ATERO_BUNDLE" '.plugins[$p][0].version // empty' \
		"$HOME/.claude/plugins/installed_plugins.json" 2>/dev/null
}

report() {
	if [ "$2" = "$3" ]; then
		result="not updated ($2)"
	else
		result="updated $2 -> $3"
	fi
	if [ "$4" -eq 0 ]; then
		echo "$1: $result"
	else
		echo "$1: FAILED (exit $4) - $result"
	fi
}

omz_before=$(git -C "$ZSH" rev-parse --short HEAD 2>/dev/null)
claude_before=$("$CLAUDE" --version 2>/dev/null)

# brew's own auto-update only fires once every 24h, which a daily cron can miss,
# leaving the upgrades to resolve against a stale tap index.
brew update
brew_update_status=$?

# `omz update` is a zsh function, absent outside an interactive shell; upgrade.sh is
# the unattended entry point (-i would make it prompt).
zsh -f "$ZSH/tools/upgrade.sh" -v default
omz_status=$?

# check_for_upgrade.sh prompts again 13 days after this stamp, so cron has to write it.
echo "LAST_EPOCH=$(( $(date +%s) / 86400 ))" > "$ZSH/cache/.zsh-update"

"$CLAUDE" update
claude_status=$?

bundle_before=$(bundle_version)
# An installed plugin is a frozen copy pinned to its plugin.json version, so the
# marketplace pull alone changes nothing until `plugin update` re-copies it.
"$CLAUDE" plugin marketplace update "$ATERO_MARKETPLACE" && "$CLAUDE" plugin update "$ATERO_BUNDLE"
bundle_status=$?

go_before=$(ls "$HOME/.gvm/gos" | tr '\n' ' ')
# The pin is read from origin/main, so whatever branch the checkout is on does not
# change it. BatchMode makes a fetch that would prompt for a passphrase fail instead
# of hanging the cron.
go_pin=$(GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=15' \
	git -C "$GO_PIN_REPO" fetch -q origin main >&2 &&
	git -C "$GO_PIN_REPO" show origin/main:.go-version)
go_status=$?
if [ "$go_status" -eq 0 ]; then
	# gvm is a set of bash functions; -B installs the prebuilt binary, which needs no
	# go1.4 bootstrap. Go writes the module cache read-only, which gvm uninstall's
	# rm -rf cannot remove.
	bash -c '
		. "$HOME/.gvm/scripts/gvm" || exit 1
		[ -d "$GVM_ROOT/gos/$1" ] || gvm install "$1" -B || exit 1
		gvm use "$1" --default >/dev/null || exit 1
		for v in $(ls "$GVM_ROOT/gos"); do
			[ "$v" = "$1" ] && continue
			chmod -R u+w "$GVM_ROOT/pkgsets/$v" 2>/dev/null
			gvm uninstall "$v" || exit 1
		done
	' _ "$go_pin" >&2
	go_status=$?
fi
go_after=$(ls "$HOME/.gvm/gos" | tr '\n' ' ')

brew_report=$(
	for f in $BREW_FORMULAE; do
		before=$(brew_version "$f")
		# brew's own output belongs in the cron log, not in the captured report.
		brew upgrade -y "$f" >&2
		status=$?
		after=$(brew_version "$f")
		report "$f" "$before" "$after" "$status"
	done
)

omz_after=$(git -C "$ZSH" rev-parse --short HEAD 2>/dev/null)
claude_after=$("$CLAUDE" --version 2>/dev/null)
bundle_after=$(bundle_version)

# Newest run first, so the head of the file is the current state.
{
	echo "last run: $(date '+%Y-%m-%d %H:%M:%S %Z')"
	report "oh-my-zsh" "$omz_before" "$omz_after" "$omz_status"
	report "claude" "$claude_before" "$claude_after" "$claude_status"
	report "$ATERO_BUNDLE" "$bundle_before" "$bundle_after" "$bundle_status"
	report "go (data-path pin)" "$go_before" "$go_after" "$go_status"
	if [ "$brew_update_status" -eq 0 ]; then
		echo "brew update: ok"
	else
		echo "brew update: FAILED (exit $brew_update_status)"
	fi
	echo "$brew_report"
	echo "============================================================"
	cat "$STATUS_FILE" 2>/dev/null
} > "$STATUS_FILE.new"
mv "$STATUS_FILE.new" "$STATUS_FILE"
