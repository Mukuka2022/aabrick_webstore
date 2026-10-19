"""Lay a tile on a room's floor, the way the page does, but off the page.

The homepage's picture was a screenshot of a screenshot: the canvas is
drawn at 1100 across, the pane scaled it, the frame was a JPEG, and the
crop was then stretched back up to 1100. Four resamplings, hence the mush.

This does the same arithmetic as tile-visualiser.js, on the photograph at
its own 1448 pixels, in one pass with no resampling at all. The constants
and the order of operations are copied from that file deliberately: if the
two ever disagree, the page is right and this is wrong.
"""

import io
import json
import math
import sys

from PIL import Image

S = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/blue/scenes.json")
APP = ("/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"
       "/public/images/")
TEX = "/home/frappe/frappe-bench/sites/www.aabrick.com/public/files/tex/"

GROUT_MM = 1
GROUT_DARK = 0.82
GROUT_FAINT = 0.5
SOFT_PX = 8
HIGHLIGHT = 0.75
SIDE = 512                      # the texture is squared off to this


def inside(poly, x, y):
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / float(yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def render(slug, code, out_path, size_mm=600):
    scene = {q["id"]: q for q in json.load(io.open(S, encoding="utf-8"))}[slug]
    base = Image.open(APP + "scene-%s.jpg" % slug).convert("RGB")
    w, h = base.size
    src = base.load()
    poly = scene["floor"]
    yh = scene["horizon"]
    cx = scene["cx"]
    focal = scene["focal"]
    camH = scene["height"]

    tex = Image.open(TEX + "%s.jpg" % code).convert("RGB")
    tex = tex.resize((SIDE, SIDE), Image.LANCZOS)
    td = tex.load()
    n = SIDE * SIDE
    ar = ag = ab = 0
    for ty in range(0, SIDE, 4):
        for tx in range(0, SIDE, 4):
            r, g, b = td[tx, ty]
            ar += r
            ag += g
            ab += b
    k = (SIDE // 4) ** 2
    avg = (ar / float(k), ag / float(k), ab / float(k))

    Sm = size_mm / 1000.0
    gm = GROUT_MM / 1000.0

    # the floor, and its own average brightness
    mask = bytearray(w * h)
    lum = [0.0] * (w * h)
    tot = cnt = 0
    for y in range(h):
        dy = y - yh
        if dy <= 2:
            continue
        row = y * w
        for x in range(w):
            if not inside(poly, x, y):
                continue
            mask[row + x] = 1
            r, g, b = src[x, y]
            L = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            lum[row + x] = L
            tot += L
            cnt += 1
    ref = tot / cnt if cnt else 0.6
    print("  %s: %d floor pixels, their mean brightness %.3f"
          % (slug, cnt, ref))

    out = base.copy()
    dst = out.load()
    for y in range(h):
        dy = y - yh
        if dy <= 2:
            continue
        row = y * w
        V = focal * camH / dy
        PX = dy * dy / (focal * camH)
        for x in range(w):
            if not mask[row + x]:
                continue
            U = (x - cx) * camH / dy
            fu = U / Sm
            fv = V / Sm
            fu -= math.floor(fu)
            fv -= math.floor(fv)
            ui = int(fu * SIDE)
            vi = int(fv * SIDE)
            r, g, b = td[ui if ui < SIDE else SIDE - 1,
                         vi if vi < SIDE else SIDE - 1]
            r, g, b = float(r), float(g), float(b)

            px = Sm * PX
            if px < SOFT_PX:
                m = px / SOFT_PX
                r = r * m + avg[0] * (1 - m)
                g = g * m + avg[1] * (1 - m)
                b = b * m + avg[2] * (1 - m)
            else:
                gpx = gm * PX
                band = gpx if gpx > 1 else 1
                g2 = band / PX
                if fu < g2 / Sm or fv < g2 / Sm:
                    kk = gpx / band
                    if kk < GROUT_FAINT:
                        kk = GROUT_FAINT
                    d2 = 1 - (1 - GROUT_DARK) * kk
                    r *= d2
                    g *= d2
                    b *= d2

            f = lum[row + x] / ref
            f = 0.25 if f < 0.25 else (1.7 if f > 1.7 else f)
            if f > 1:
                hi = (f - 1) * HIGHLIGHT
                if hi > 1:
                    hi = 1
                r = r + (255 - r) * hi
                g = g + (255 - g) * hi
                b = b + (255 - b) * hi
            else:
                r *= f
                g *= f
                b *= f
            dst[x, y] = (int(r if r < 255 else 255),
                         int(g if g < 255 else 255),
                         int(b if b < 255 else 255))

    out.save(out_path, "JPEG", quality=92, optimize=True, progressive=True)
    print("  wrote %s" % out_path)
    return out


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3])
