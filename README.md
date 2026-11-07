# VPN Indicator (macOS)

A small menu bar icon for macOS that shows at a glance whether a VPN is connected. This is the
macOS port of the [Windows VPN Indicator](../vpn-indicator) — same idea, same green/amber/red V
icon, implemented with Python + [rumps](https://github.com/jaredks/rumps) instead of PowerShell.

| Icon | Meaning |
|---|---|
| 🟢 Green V | VPN is up **and** internet traffic goes through it |
| 🟠 Amber V | A VPN interface is up, but internet traffic is **not** going through it (split tunnel) |
| 🔴 Red V | No VPN connected |

Click the icon for the current status line, **Open Network Settings**, **Refresh now**, **Notify
on change** (a notification when status changes), and **Quit**.

## Files

| File | Purpose |
|---|---|
| `vpn_indicator.py` | The menu bar app |
| `requirements.txt` | Python dependencies (`rumps`, `pillow`) |
| `install-launchagent.sh` | Makes the app start at login and starts it now |
| `uninstall-launchagent.sh` | Removes the login item |
| `README.md` | This file |

## Requirements

- macOS with Python 3 (`python3 --version`). If missing: `brew install python` (or use Xcode
  Command Line Tools' python3).
- `pip3 install -r requirements.txt`

> **Apple's built-in python3** (`/usr/bin/python3`, 3.9) ships with pip 21.2, which is too old to
> find the prebuilt `pyobjc-core` wheel that `rumps` needs and fails trying to compile it. Upgrade
> pip first: `python3 -m pip install --user --upgrade pip`.

## Install

```bash
cd /path/to/vpn-indicator-mac
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt
chmod +x install-launchagent.sh uninstall-launchagent.sh
./install-launchagent.sh
```

This installs a per-user LaunchAgent (`~/Library/LaunchAgents/com.dlsnoopy.vpnindicator.plist`)
and starts the app immediately. It will start automatically at every login from now on.

The first time it runs, macOS may ask for permission to show notifications — allow it if you want
the "Notify on change" feature to work.

### Run once without installing

```bash
python3 vpn_indicator.py
```

## Uninstall

```bash
./uninstall-launchagent.sh
```

Then click the menu bar icon → **Quit** if it's still running. Optionally delete the
`vpn-indicator-mac` folder.

Nothing else is installed: no background services beyond the one LaunchAgent, no data written
outside the log files in `/tmp` and generated icon PNGs in a temp folder.

## What it can detect

**Tunnel interfaces** — matched by interface name via `ifconfig`:

| Interface prefix | Typical VPN |
|---|---|
| `utun*` | WireGuard, Tailscale, Surfshark, NordVPN, ProtonVPN, Mullvad, macOS built-in IKEv2, most modern VPN apps |
| `tun*`, `tap*` | Older OpenVPN clients (tuntaposx) |
| `ppp*` | L2TP/PPTP profiles under *System Settings → VPN* |
| `ipsec*` | Cisco IPSec profiles |

An interface only counts if it's up **and** has an IPv4 address assigned — this avoids false
positives from unrelated `utun` interfaces macOS creates for other features (e.g. Handoff).

**Where traffic actually goes.** It asks macOS which interface a probe route to `1.1.1.1` would
use (`route -n get`), so it can tell a full tunnel (green) from a split tunnel or idle adapter
(amber).

## What it can't do

- **Browser-only VPNs** (extensions, Opera's built-in VPN) protect only the browser and create no
  interface, so they aren't detected.
- **Unlisted VPN apps** that use an interface name outside the patterns above aren't detected
  until you add the prefix (see *Customize*).
- **Tailscale** is currently counted as a VPN (it uses `utun`); remove it from the pattern if you
  don't want that.
- It **does not check for leaks** (DNS or IPv6 leaks, or your public IP). Green means traffic is
  routed into the tunnel interface, not that the VPN provider is working correctly.
- It **cannot connect, disconnect or change** any VPN or network setting. It only reads status.
- It checks every **3 seconds**, so a change can take up to 3 seconds to show.

## Customize

Edit the settings block at the top of `vpn_indicator.py`:

```python
POLL_SECONDS = 3
VPN_IFACE_RE = re.compile(r'^(utun|tun|tap|ppp|ipsec)\d+$')
```

To see your active interfaces while a VPN is connected: `ifconfig | less`. Then adjust the regex,
quit the app, and run `./install-launchagent.sh` again (or `python3 vpn_indicator.py`).

## Privacy and security

- **No secrets:** no passwords, API keys or tokens are stored in the scripts.
- **No network traffic:** nothing is sent anywhere. `1.1.1.1` is only used as a sample address for
  a local route lookup; no packets are sent to it.
- **No logs or data:** nothing is written to disk except the LaunchAgent plist, its stdout/stderr
  logs in `/tmp`, and small generated icon PNGs in a temp folder.
- **Easy to audit:** `vpn_indicator.py` is plain Python, short enough to read end to end.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: rumps` | `pip3 install -r requirements.txt` |
| Icon not visible | Check the menu bar overflow (`>>`) on narrow screens |
| Doesn't start after reboot | Re-run `./install-launchagent.sh`; check `/tmp/vpn-indicator.err.log` |
| Stays red while the VPN is on | Run `ifconfig` while connected, find the interface name, add its prefix to `VPN_IFACE_RE` |
| Amber while the VPN is on | The VPN is split tunnel, or the app keeps its interface up while disconnected |
| Notifications don't show | Allow notifications for the app in *System Settings → Notifications* (may be listed as "Python") |
