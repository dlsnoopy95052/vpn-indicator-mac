#!/bin/bash
# install-launchagent.sh
# Installs vpn_indicator.py as a per-user LaunchAgent so it starts at login, then starts it now.
# To uninstall: run uninstall-launchagent.sh, or:
#   launchctl unload ~/Library/LaunchAgents/com.dlsnoopy.vpnindicator.plist
#   rm ~/Library/LaunchAgents/com.dlsnoopy.vpnindicator.plist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(command -v python3)"
LABEL="com.dlsnoopy.vpnindicator"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ -z "$PYTHON_BIN" ]; then
    echo "python3 not found. Install it (e.g. 'brew install python') and re-run this script." >&2
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$SCRIPT_DIR/vpn_indicator.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/vpn-indicator.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vpn-indicator.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Installed startup agent: $PLIST"
echo "VPN Indicator is now running in the menu bar and will start automatically at every login."
echo "Logs: /tmp/vpn-indicator.out.log /tmp/vpn-indicator.err.log"
