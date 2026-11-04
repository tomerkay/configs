#!/bin/sh
ZSH="$HOME/.oh-my-zsh"
export ZSH

# cron's PATH omits /opt/homebrew/bin, so every brew call exited 127.
PATH="/opt/homebrew/bin:$PATH"
export PATH

CLAUDE="$HOME/.local/bin/claude"
ATERO_MARKETPLACE=atero-skills
ATERO_BUNDLE="atero-skills@$ATERO_MARKETPLACE"
PLUGINS_FILE="$HOME/.claude/plugins/installed_plugins.json"
LOG_FILE="$(cd "$(dirname "$0")/.." && pwd)/daily-updates.log"
BREW_FORMULAE="crusoe k9s gh glab uv kubectx pomerium/tap/pomerium-cli"
GO_PIN_REPO="$HOME/repos/data-path"
LINT_REPO="https://github.com/golangci/golangci-lint"
LINT_BIN="$HOME/.local/bin/golangci-lint"

STEP_ERR=$(mktemp)
trap 'rm -f "$STEP_ERR"' EXIT

# Keeps the step's stderr in a file as well as passing it on, so step_reason can
# read it even when the step ran inside a command substitution.
run_step() {
	"$@" 2>"$STEP_ERR"
	step_status=$?
	cat "$STEP_ERR" >&2
	return "$step_status"
}

# git, brew, gvm, curl and claude print the cause on the first line that names an
# error and follow it with generic advice, so that line beats the last one.
step_reason() {
	grep -m1 -iE 'error|fatal|fail|ssh:|curl:' "$STEP_ERR" ||
		grep -v '^[[:space:]]*$' "$STEP_ERR" | tail -n 1
}

# A formula can keep older kegs until cleanup runs, so take the last (newest) column.
brew_version() {
	brew list --versions "$1" 2>/dev/null | awk '{print $NF}'
}

# $1 is the project path of a project-scope install, or empty for the user one.
bundle_version() {
	jq -r --arg p "$ATERO_BUNDLE" --arg dir "$1" \
		'.plugins[$p][] | select((.projectPath // "") == $dir) | .version' \
		"$PLUGINS_FILE" 2>/dev/null
}

bundle_project_dirs() {
	jq -r --arg p "$ATERO_BUNDLE" '.plugins[$p][] | select(.scope == "project") | .projectPath' \
		"$PLUGINS_FILE" 2>/dev/null
}

# $5 is the cause, printed only when $4 is a failing exit code.
report() {
	if [ "$2" = "$3" ]; then
		result="not updated ($2)"
	else
		result="updated $2 -> $3"
	fi
	if [ "$4" -eq 0 ]; then
		echo "$1: $result"
	else
		echo "$1: FAILED: ${5:-no error output} (exit $4) - $result"
	fi
}

report_status() {
	if [ "$2" -eq 0 ]; then
		echo "$1: ok"
	else
		echo "$1: FAILED: ${3:-no error output} (exit $2)"
	fi
}

# A linked worktree's .git is a file naming the main checkout, whose own .git is a
# directory. `plugin update --scope project` run in a worktree updates the main
# checkout's record and leaves the worktree's own where it is, and `plugin install`
# refuses a record that exists, so nothing moves a worktree's record.
worktree_record() {
	[ -f "$1/.git" ]
}

# $1 is the record's project path. A session started there recreates a missing
# record at the current version.
drop_bundle_record() {
	tmp=$(mktemp "$PLUGINS_FILE.XXXXXX") || return 1
	if jq --arg p "$ATERO_BUNDLE" --arg dir "$1" \
		'.plugins[$p] |= map(select((.projectPath // "") != $dir))' "$PLUGINS_FILE" > "$tmp" &&
		mv "$tmp" "$PLUGINS_FILE"; then
		return 0
	fi
	rm -f "$tmp"
	return 1
}

# The user install is the copy every directory gets; a project record is listed only
# when it ends up on another version, or has to be dropped.
bundle_report() {
	user_before=$(bundle_version "")
	# The update's own output belongs in the cron log, not in the captured report.
	run_step "$CLAUDE" plugin update "$ATERO_BUNDLE" >&2
	user_status=$?
	user_after=$(bundle_version "")
	report "$ATERO_BUNDLE" "$user_before" "$user_after" "$user_status" "$(step_reason)"
	for dir in $(bundle_project_dirs); do
		label="$ATERO_BUNDLE (${dir##*/})"
		before=$(bundle_version "$dir")
		drop_why=
		if [ ! -d "$dir" ]; then
			drop_why="its directory is gone"
		elif worktree_record "$dir"; then
			[ "$before" = "$user_after" ] && continue
			drop_why="a stale worktree record, recreated by the next session there"
		fi
		if [ -n "$drop_why" ]; then
			if drop_bundle_record "$dir"; then
				echo "$label: dropped $before, $drop_why"
			else
				echo "$label: FAILED: could not drop $before, $drop_why"
			fi
			continue
		fi
		echo "project-scope update in $dir:" >&2
		(cd "$dir" 2>"$STEP_ERR" && run_step "$CLAUDE" plugin update --scope project "$ATERO_BUNDLE") >&2
		status=$?
		after=$(bundle_version "$dir")
		if [ "$status" -ne 0 ]; then
			report "$label" "$before" "$after" "$status" "$(step_reason)"
		elif [ "$after" != "$user_after" ]; then
			echo "$label: FAILED: on $after while the user install is on $user_after"
		fi
	done
}

# A subshell body, so its cd leaves the script's directory alone.
install_lint() (
	cd "$lint_dir" &&
		curl -sSfLO "$LINT_REPO/releases/download/v$lint_latest/$lint_asset.tar.gz" &&
		curl -sSfLO "$LINT_REPO/releases/download/v$lint_latest/golangci-lint-$lint_latest-checksums.txt" &&
		grep " $lint_asset.tar.gz\$" "golangci-lint-$lint_latest-checksums.txt" | shasum -a 256 -c &&
		tar -xzf "$lint_asset.tar.gz" &&
		mkdir -p "$(dirname "$LINT_BIN")" &&
		mv "$lint_asset/golangci-lint" "$LINT_BIN"
)

# The data-path remote is reachable from here only over the tailnet; without it the
# fetch waits out ssh's connect timeout and fails.
tailscale_state=$(tailscale status --json 2>/dev/null | jq -r .BackendState 2>/dev/null)
if [ "$tailscale_state" != Running ]; then
	echo "tailscale is ${tailscale_state:-not answering}: start it, data-path cannot be fetched" >&2
fi

omz_before=$(git -C "$ZSH" rev-parse --short HEAD 2>/dev/null)
claude_before=$("$CLAUDE" --version 2>/dev/null)

# brew's own auto-update only fires once every 24h, which a daily cron can miss,
# leaving the upgrades to resolve against a stale tap index.
run_step brew update
brew_update_status=$?
brew_update_reason=$(step_reason)

# `omz update` is a zsh function, absent outside an interactive shell; upgrade.sh is
# the unattended entry point (-i would make it prompt).
run_step zsh -f "$ZSH/tools/upgrade.sh" -v default
omz_status=$?
omz_reason=$(step_reason)

# check_for_upgrade.sh prompts again 13 days after this stamp, so cron has to write it.
echo "LAST_EPOCH=$(( $(date +%s) / 86400 ))" > "$ZSH/cache/.zsh-update"

run_step "$CLAUDE" update
claude_status=$?
claude_reason=$(step_reason)

# An installed plugin is a frozen copy pinned to its plugin.json version, so the
# marketplace pull alone changes nothing until `plugin update` re-copies it. Each
# scope is its own copy, and the default update touches only the user one.
run_step "$CLAUDE" plugin marketplace update "$ATERO_MARKETPLACE"
marketplace_status=$?
marketplace_reason=$(step_reason)
if [ "$marketplace_status" -eq 0 ]; then
	bundle_report=$(bundle_report)
fi

go_before=$(ls "$HOME/.gvm/gos" | tr '\n' ' ')
if [ "$tailscale_state" = Running ]; then
	# The pin is read from origin/main, so whatever branch the checkout is on does not
	# change it. BatchMode makes a fetch that would prompt for a passphrase fail instead
	# of hanging the cron.
	go_stage="fetching data-path origin/main"
	run_step env GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=15' \
		git -C "$GO_PIN_REPO" fetch -q origin main
	go_status=$?
	if [ "$go_status" -eq 0 ]; then
		go_stage="reading .go-version from data-path origin/main"
		go_pin=$(run_step git -C "$GO_PIN_REPO" show origin/main:.go-version)
		go_status=$?
	fi
	if [ "$go_status" -eq 0 ]; then
		go_stage="switching gvm and ~/.local/bin to $go_pin"
		# gvm is a set of bash functions; -B installs the prebuilt binary, which needs no
		# go1.4 bootstrap. Go writes the module cache read-only, which gvm uninstall's
		# rm -rf cannot remove.
		run_step bash -c '
			. "$HOME/.gvm/scripts/gvm" || exit 1
			[ -d "$GVM_ROOT/gos/$1" ] || gvm install "$1" -B || exit 1
			gvm use "$1" --default >/dev/null || exit 1
			# A process started before a pin change keeps a PATH to the version the loop
			# below uninstalls; these links resolve go to the pin from any PATH that
			# carries ~/.local/bin.
			for bin in go gofmt; do
				ln -sfn "$GVM_ROOT/gos/$1/bin/$bin" "$HOME/.local/bin/$bin" || exit 1
			done
			for v in $(ls "$GVM_ROOT/gos"); do
				[ "$v" = "$1" ] && continue
				chmod -R u+w "$GVM_ROOT/pkgsets/$v" 2>/dev/null
				gvm uninstall "$v" || exit 1
			done
		' _ "$go_pin" >&2
		go_status=$?
		# A tmux server hands every new pane the GOROOT it started with, which the
		# uninstall above can delete; with it unset, gvm in .zshrc sets the pin's.
		tmux set-environment -gu GOROOT 2>/dev/null
	fi
	go_reason="$go_stage: $(step_reason)"
fi
go_after=$(ls "$HOME/.gvm/gos" | tr '\n' ' ')

# Homebrew's formula depends on its own go, a second toolchain beside the gvm pin.
# The release binary has no such dependency and runs whichever go is on PATH.
lint_before=$("$LINT_BIN" version --short 2>/dev/null)
lint_after=$lint_before
lint_stage="looking up the latest release"
lint_latest=$(run_step curl -sSfL -o /dev/null -w '%{url_effective}' "$LINT_REPO/releases/latest")
lint_status=$?
lint_latest=${lint_latest##*/v}
if [ "$lint_status" -eq 0 ] && [ "$lint_latest" != "$lint_before" ]; then
	lint_stage="installing v$lint_latest"
	lint_asset="golangci-lint-$lint_latest-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/')"
	lint_dir=$(mktemp -d)
	run_step install_lint >&2
	lint_status=$?
	rm -rf "$lint_dir"
	lint_after=$("$LINT_BIN" version --short 2>/dev/null)
fi
lint_reason="$lint_stage: $(step_reason)"

brew_report=$(
	for f in $BREW_FORMULAE; do
		before=$(brew_version "$f")
		# brew's own output belongs in the cron log, not in the captured report.
		run_step brew upgrade -y "$f" >&2
		status=$?
		reason=$(step_reason)
		after=$(brew_version "$f")
		report "$f" "$before" "$after" "$status" "$reason"
	done
)

omz_after=$(git -C "$ZSH" rev-parse --short HEAD 2>/dev/null)
claude_after=$("$CLAUDE" --version 2>/dev/null)

body=$(
	if [ "$tailscale_state" = Running ]; then
		echo "tailscale: ok"
	else
		echo "tailscale: FAILED: ${tailscale_state:-not answering}"
	fi
	report "oh-my-zsh" "$omz_before" "$omz_after" "$omz_status" "$omz_reason"
	report "claude" "$claude_before" "$claude_after" "$claude_status" "$claude_reason"
	report_status "$ATERO_MARKETPLACE marketplace" "$marketplace_status" "$marketplace_reason"
	[ -n "$bundle_report" ] && echo "$bundle_report"
	if [ "$tailscale_state" = Running ]; then
		report "go (data-path pin)" "$go_before" "$go_after" "$go_status" "$go_reason"
	else
		echo "go (data-path pin): skipped, tailscale is down - not updated ($go_before)"
	fi
	report "golangci-lint" "$lint_before" "$lint_after" "$lint_status" "$lint_reason"
	report_status "brew update" "$brew_update_status" "$brew_update_reason"
	echo "$brew_report"
)

names_matching() {
	echo "$body" | grep -- "$1" | sed 's/: .*//' | paste -sd, - | sed 's/,/, /g'
}

failed=$(names_matching ': FAILED')
updated=$(names_matching ': updated ')
dropped=$(names_matching ': dropped ')
if [ -n "$failed" ]; then
	summary="FAILED: $failed"
else
	summary="all ok"
fi
if [ -n "$updated" ]; then
	summary="$summary; updated: $updated"
else
	summary="$summary; nothing updated"
fi
[ -n "$dropped" ] && summary="$summary; dropped: $dropped"

# Reasons are free text that can hold the summary's own separators, so each failure
# gets a line of its own.
failures=$(echo "$body" | grep ': FAILED: ' |
	sed -E 's/ - (not )?updated .*$//; s/: FAILED: /: /; s/^/failed: /')

{
	echo "last run: $(date '+%Y-%m-%d %H:%M:%S %Z')"
	echo "summary: $summary"
	[ -n "$failures" ] && echo "$failures"
	echo "$body"
	echo "============================================================"
} >> "$LOG_FILE"
