#!/usr/bin/env python3
# make_app_icon.py
# Builds icon.icns (green bold 'V', same glyph as the menu bar icon) and copies it into
# ~/Applications/vpn-indicator-mac.app, then re-signs the bundle.
# Usage: python3 make_app_icon.py [path/to/App.app]

import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

GREEN = (34, 197, 94)
APP = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Applications/vpn-indicator-mac.app')
SIZES = [16, 32, 64, 128, 256, 512, 1024]


def draw_v(size):
    """Render the V glyph (32x32 design grid, padded) supersampled for smooth edges."""
    ss = 4
    big = size * ss
    scale = big / 32
    img = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pts = [(3, 3), (16, 30), (29, 3), (20, 3), (16, 15), (12, 3)]
    pts = [(x * scale, y * scale) for x, y in pts]
    draw.polygon(pts, fill=GREEN + (255,), outline=(255, 255, 255, 220), width=max(1, round(big / 64)))
    return img.resize((size, size), Image.LANCZOS)


def main():
    work = tempfile.mkdtemp()
    iconset = os.path.join(work, 'icon.iconset')
    os.makedirs(iconset)
    for s in SIZES:
        img = draw_v(s)
        if s <= 512:
            img.save(os.path.join(iconset, f'icon_{s}x{s}.png'))
        if s >= 32:
            img.save(os.path.join(iconset, f'icon_{s // 2}x{s // 2}@2x.png'))
    icns = os.path.join(work, 'icon.icns')
    subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', icns], check=True)

    dest = os.path.join(APP, 'Contents', 'Resources', 'icon.icns')
    shutil.copyfile(icns, dest)
    subprocess.run(['codesign', '--force', '--deep', '--sign', '-', APP], check=True)
    subprocess.run(['touch', APP])
    print('Updated', dest)


if __name__ == '__main__':
    main()
