#!/usr/bin/env python3
# make-icon.py: regenerates icon.icns (green 'V' (same shape as the menu bar icon) on a dark rounded square). Needs Pillow + macOS iconutil.
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw

SIZE = 1024


def draw():
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((100, 100, SIZE - 100, SIZE - 100), radius=185, fill=(34, 40, 52, 255))
    # Same polygon as the menu bar V (32x32 grid), scaled into the square.
    pts = [(3, 3), (16, 30), (29, 3), (20, 3), (16, 15), (12, 3)]
    k = 20  # 32 * 20 = 640px glyph box
    ox, oy = (SIZE - 32 * k) // 2, (SIZE - 32 * k) // 2
    pts = [(ox + x * k, oy + y * k) for x, y in pts]
    d.polygon(pts, fill=(52, 199, 89, 255))
    return img


with tempfile.TemporaryDirectory() as tmp:
    iconset = os.path.join(tmp, 'icon.iconset')
    os.mkdir(iconset)
    base = draw()
    for s in (16, 32, 128, 256, 512):
        base.resize((s, s), Image.LANCZOS).save(f'{iconset}/icon_{s}x{s}.png')
        base.resize((s * 2, s * 2), Image.LANCZOS).save(f'{iconset}/icon_{s}x{s}@2x.png')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.icns')
    subprocess.run(['iconutil', '-c', 'icns', iconset, '-o', out], check=True)
