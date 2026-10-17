"""Trace the pink walls, the same way the blue floors were traced.

A wall is given as spans rather than as an outline. A floor is one shape and
an outline describes it; a wall has a window punched through it, a mirror on
it and a shower screen across it, and an outline cannot say "not here". So
each column carries a list of top and bottom pairs, and everything between a
pair is wall.

The geometry needs nothing new. The floor outline is the wall's own skirting,
so the depth of the wall in any column is the depth of the floor directly
below it, which the floor trace already knows. Height up the wall and
distance along it follow from that, and the drawing code cannot tell the
difference between those and the two numbers it uses for a floor.
"""

import io
import json
import os

from PIL import Image, ImageDraw, ImageFilter

SRC = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/images")
OUT = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls")

# Only the rooms whose walls were painted. The others have no key to trace.
ROOMS = [(14, "ensuite"), (15, "kitchen"), (16, "bathroom")]

STEP = 3           # columns
HUE = 10.0         # degrees either side of the wall's own hue
SAT = 0.72         # of the wall's own saturation, at least
MIN_RUN = 14       # a span shorter than this is a reflection, not a wall


def hsv(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx / 255.0
    d = mx - mn
    if mx == 0 or d == 0:
        return 0.0, 0.0, v
    s = d / float(mx)
    if mx == r:
        h = 60.0 * (((g - b) / float(d)) % 6)
    elif mx == g:
        h = 60.0 * (((b - r) / float(d)) + 2)
    else:
        h = 60.0 * (((r - g) / float(d)) + 4)
    return h, s, v


def wall_paint(px, w, h):
    """The wall's own hue and saturation, from a band across the top.

    Saturation is the half that does the work. Everything in these rooms is
    warm, because the paint throws pink light over all of it, so hue alone
    cannot tell paint from a basin: in the ensuite the wall measures 9
    degrees and the toilet 12. What the paint has and the porcelain has not
    is strength of colour, 0.6 against 0.25; and the one strongly coloured
    thing that is not wall, the oak vanity, sits 17 degrees away in hue.
    Neither test holds alone and together they are clean.
    """
    from collections import Counter
    c = Counter()
    for y in range(int(h * 0.08), int(h * 0.32), 2):
        for x in range(0, w, 2):
            hh, ss, vv = hsv(*px[x, y])
            if ss > 0.40 and vv > 0.12:
                c[round(hh)] += 1
    if sum(c.values()) < 500:
        return None
    # the mode, averaged over its neighbours so a single degree cannot win
    ref = max(c, key=lambda k: sum(c.get(k + d, 0) for d in range(-4, 5)))

    sats = []
    for y in range(int(h * 0.08), int(h * 0.32), 2):
        for x in range(0, w, 2):
            hh, ss, vv = hsv(*px[x, y])
            d = abs(hh - ref)
            if d > 180:
                d = 360 - d
            if d < HUE and ss > 0.40 and vv > 0.12:
                sats.append(ss)
    sats.sort()
    return float(ref), sats[len(sats) // 2]


def spans(path):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    w, h = im.size
    px = im.filter(ImageFilter.GaussianBlur(0.6)).load()
    found = wall_paint(px, w, h)
    if found is None:
        return None, (w, h), None
    ref, ref_sat = found
    floor_sat = ref_sat * SAT

    def is_wall(r, g, b):
        hh, ss, vv = hsv(r, g, b)
        if ss < floor_sat or vv < 0.10:
            return False
        d = abs(hh - ref)
        if d > 180:
            d = 360 - d
        return d < HUE

    cols = []
    for x in range(0, w, STEP):
        xs = min(x, w - 1)
        runs = []
        y0 = None
        for y in range(0, h):
            if is_wall(*px[xs, y]):
                if y0 is None:
                    y0 = y
            else:
                if y0 is not None and y - y0 >= MIN_RUN:
                    runs.append([y0, y - 1])
                y0 = None
        if y0 is not None and h - y0 >= MIN_RUN:
            runs.append([y0, h - 1])
        if runs:
            cols.append([xs] + [c for r in runs for c in r])
    return cols, (w, h), (ref, ref_sat)


def overlay(path, cols, dst, label):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for col in cols:
        x = col[0]
        for i in range(1, len(col), 2):
            d.rectangle([x, col[i], x + STEP - 1, col[i + 1]],
                        fill=(0, 220, 120, 95))
    d.text((16, 16), label, fill=(255, 255, 0, 255))
    im.save(dst, "JPEG", quality=86)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    out = {}
    for n, slug in ROOMS:
        p = "%s/%d.webp" % (SRC, n)
        cols, (w, h), found = spans(p)
        if cols is None:
            print("  %-10s no wall paint found" % slug)
            continue
        ref, ref_sat = found
        nums = sum(len(c) for c in cols)
        out[slug] = {"step": STEP, "size": [w, h], "cols": cols}
        overlay(p, cols, os.path.join(OUT, "%s.jpg" % slug),
                "%s  hue %.0f deg  sat %.2f  %d columns  %d numbers"
                % (slug, ref, ref_sat, len(cols), nums))
        print("  %-10s hue %3.0f deg  sat %.2f  %4d columns  %5d numbers"
              % (slug, ref, ref_sat, len(cols), nums))
    with io.open(os.path.join(OUT, "walls.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("walls traced")


main()
