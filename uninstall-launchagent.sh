#!/bin/bash
# uninstall-launchagent.sh
# Removes the VPN Indicator LaunchAgent installed by install-launchagent.sh.

set -euo pipefail

LABEL="com.dlsnoopy.vpnindicator"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/Applications/vpn-indicator-mac.app"

echo "Removed $PLIST. Quit the menu bar icon manually if it's still running (click it > Quit)."
