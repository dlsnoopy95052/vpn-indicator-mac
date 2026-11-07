#!/bin/bash
# install-launchagent.sh
# Installs vpn_indicator.py as a per-user LaunchAgent so it starts at login, then starts it now.
# To uninstall: run uninstall-launchagent.sh, or:
#   launchctl unload ~/Library/LaunchAgents/com.dlsnoopy.vpnindicator.plist
#   rm ~/Library/LaunchAgents/com.dlsnoopy.vpnindicator.plist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_PYTHON="$(command -v python3 || true)"
PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
LABEL="com.dlsnoopy.vpnindicator"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
APP_NAME="vpn-indicator-mac"
APP_DIR="$HOME/Applications/$APP_NAME.app"

if [ ! -x "$PYTHON_BIN" ]; then
    if [ -z "$SYSTEM_PYTHON" ]; then
        echo "python3 not found. Install it (e.g. 'brew install python') and re-run this script." >&2
        exit 1
    fi
    # A venv with a current pip avoids building pyobjc from source (fails with the old system pip).
    "$SYSTEM_PYTHON" -m venv "$SCRIPT_DIR/.venv"
    "$PYTHON_BIN" -m pip install -q --upgrade pip
    "$PYTHON_BIN" -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
fi

mkdir -p "$HOME/Library/LaunchAgents"

# Build a tiny launcher app so System Settings > Login Items shows "$APP_NAME" instead of "python3".
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
cp "$SCRIPT_DIR/icon.icns" "$APP_DIR/Contents/Resources/icon.icns"
cat > "$APP_DIR/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$LABEL</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF
LAUNCHER_C="$(mktemp -t launcher).c"
cat > "$LAUNCHER_C" <<EOF
#include <unistd.h>
int main(void) {
    char *args[] = {"$PYTHON_BIN", "$SCRIPT_DIR/vpn_indicator.py", 0};
    execv("$PYTHON_BIN", args);
    return 1;
}
EOF
clang -o "$APP_DIR/Contents/MacOS/$APP_NAME" "$LAUNCHER_C"
rm -f "$LAUNCHER_C"
codesign --force --sign - "$APP_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_DIR/Contents/MacOS/$APP_NAME</string>
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
