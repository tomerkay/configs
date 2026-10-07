#!/usr/bin/env bash
#
# Register sync-configs.sh with launchd so it runs at 12:00 and 18:00 while
# this user is logged in. Re-running replaces the agent. See README.md.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LABEL='local.sync-configs'
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

# Paths in a plist cannot expand $HOME, so it is generated per machine rather
# than tracked.
mkdir -p "$(dirname "$PLIST")"
cat >"$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array><string>$REPO/bin/sync-configs.sh</string></array>
    <key>StartCalendarInterval</key>
    <array>
      <dict><key>Hour</key><integer>12</integer><key>Minute</key><integer>0</integer></dict>
      <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
    </array>
    <key>StandardErrorPath</key><string>$REPO/sync-configs.log</string>
</dict>
</plist>
PLIST
plutil -lint "$PLIST" >/dev/null

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl print "$DOMAIN/$LABEL" | grep -E 'state|path' | head -3
