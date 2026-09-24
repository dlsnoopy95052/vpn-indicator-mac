#!/usr/bin/env python3
# vpn_indicator.py
# macOS menu bar icon showing VPN status:
#   green = VPN up and internet traffic goes through it
#   amber = a VPN interface is up, but internet traffic is NOT going through it (split tunnel)
#   red   = no VPN connected
# Requires Python 3 + `pip3 install -r requirements.txt`. Use install-launchagent.sh to run it at login.

import os
import re
import subprocess
import tempfile

import rumps
from PIL import Image, ImageDraw

# ---------------- settings ----------------
POLL_SECONDS = 3
# Interface name patterns that count as a VPN tunnel:
#   utun/tun/tap -> WireGuard, Tailscale, Surfshark, NordVPN, ProtonVPN, Mullvad, OpenVPN, macOS IKEv2
#   ppp/ipsec    -> L2TP/PPTP/Cisco IPSec profiles under System Settings > VPN
VPN_IFACE_RE = re.compile(r'^(utun|tun|tap|ppp|ipsec)\d+$')
# Address used to check which interface internet traffic leaves through (nothing is sent to it)
PROBE_ADDRESS = '1.1.1.1'
# ------------------------------------------

COLORS = {
    'Full':  (34, 197, 94),
    'Split': (245, 158, 11),
    'Down':  (239, 68, 68),
}

ICON_DIR = os.path.join(tempfile.gettempdir(), 'vpn-indicator-mac-icons')
os.makedirs(ICON_DIR, exist_ok=True)


def make_v_icon(rgb):
    """Draw the same bold 'V' glyph used by the Windows tray icon, scaled up for Retina."""
    size = 44
    scale = size / 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pts = [(3, 3), (16, 30), (29, 3), (20, 3), (16, 15), (12, 3)]
    pts = [(x * scale, y * scale) for x, y in pts]
    draw.polygon(pts, fill=rgb + (255,), outline=(255, 255, 255, 220))
    path = os.path.join(ICON_DIR, 'v_{}_{}_{}.png'.format(*rgb))
    img.save(path)
    return path


ICONS = {state: make_v_icon(rgb) for state, rgb in COLORS.items()}


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return ''


def get_vpn_interfaces():
    """Return the set of up tunnel interfaces that have an IPv4 address assigned."""
    out = sh(['ifconfig'])
    ifaces = set()
    for block in re.split(r'\n(?=\S)', out):
        m = re.match(r'^(\S+?):\s*flags=\d+<([^>]*)>', block)
        if not m:
            continue
        name, flags = m.group(1), m.group(2)
        if not VPN_IFACE_RE.match(name):
            continue
        if 'UP' not in flags.split(','):
            continue
        if re.search(r'\n\s*inet\s+\d+\.\d+\.\d+\.\d+', block):
            ifaces.add(name)
    return ifaces


def get_default_route_iface():
    out = sh(['route', '-n', 'get', PROBE_ADDRESS])
    m = re.search(r'interface:\s*(\S+)', out)
    return m.group(1) if m else None


def get_vpn_state():
    vpn_ifaces = get_vpn_interfaces()
    if not vpn_ifaces:
        return 'Down', 'VPN: DOWN'

    route_iface = get_default_route_iface()
    names = ', '.join(sorted(vpn_ifaces))
    if route_iface and route_iface in vpn_ifaces:
        return 'Full', 'VPN: UP - ' + names
    return 'Split', 'VPN: UP (not default route) - ' + names


class VpnIndicatorApp(rumps.App):
    def __init__(self):
        super().__init__('VPN', icon=ICONS['Down'], title='', quit_button=None)
        self.template = False  # keep the icon in color instead of menu-bar monochrome

        self.status_item = rumps.MenuItem('Checking...')
        self.notify_item = rumps.MenuItem('Notify on change', callback=self.toggle_notify)
        self.notify_item.state = True

        self.menu = [
            self.status_item,
            None,
            rumps.MenuItem('Open Network Settings', callback=self.open_settings),
            rumps.MenuItem('Refresh now', callback=lambda _: self.update()),
            self.notify_item,
            None,
            rumps.MenuItem('Quit', callback=rumps.quit_application),
        ]

        self.last_state = None
        self.update()

    def toggle_notify(self, sender):
        sender.state = not sender.state

    def open_settings(self, _):
        subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.network'])

    @rumps.timer(POLL_SECONDS)
    def tick(self, _):
        self.update()

    def update(self):
        state, label = get_vpn_state()
        self.icon = ICONS[state]
        self.status_item.title = label

        if self.last_state and self.last_state != state and self.notify_item.state:
            rumps.notification('VPN status changed', '', label)
        self.last_state = state


if __name__ == '__main__':
    VpnIndicatorApp().run()
