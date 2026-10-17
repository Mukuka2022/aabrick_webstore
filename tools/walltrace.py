"""Trace the painted walls, the same way the blue floors were traced.

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

What separates paint from furniture lives in keycolour.py, including why the
hue is hinted rather than discovered.
"""

import io
import json
import os

from PIL import Image, ImageDraw, ImageFilter

import keycolour

SRC = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/images")
OUT = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls")

# file, id, roughly what colour the walls were painted, in degrees of hue.
# Pink is about 10 and green about 85; the exact figure is measured, this
# only says which colour in the room is the paint.
ROOMS = [
    (19, "ensuite",  10.0),
    (23, "kitchen",  85.0),
    (18, "bathroom", 10.0),
]

STEP = 3           # columns
MIN_RUN = 14       # a span shorter than this is a reflection, not a wall


def spans(path, hint):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    w, h = im.size
    px = im.filter(ImageFilter.GaussianBlur(0.6)).load()
    found = keycolour.paint(px, w, h, hint)
    if found is None:
        return None, (w, h), None
    ref, ref_sat, win = found
    is_wall = keycolour.tester(ref, ref_sat, win)

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
    return cols, (w, h), (ref, ref_sat, win)


def overlay(path, cols, dst, label):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for col in cols:
        x = col[0]
        for i in range(1, len(col), 2):
            d.rectangle([x, col[i], x + STEP - 1, col[i + 1]],
                        fill=(255, 0, 200, 110))
    d.text((16, 16), label, fill=(255, 255, 0, 255))
    im.save(dst, "JPEG", quality=86)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    out = {}
    for n, slug, hint in ROOMS:
        p = "%s/%d.webp" % (SRC, n)
        cols, (w, h), found = spans(p, hint)
        if cols is None:
            print("  %-10s no paint near %.0f degrees" % (slug, hint))
            continue
        ref, ref_sat, win = found
        nums = sum(len(c) for c in cols)
        out[slug] = {"step": STEP, "size": [w, h], "cols": cols}
        overlay(p, cols, os.path.join(OUT, "%s.jpg" % slug),
                "%s  hint %.0f -> hue %.0f deg  sat %.2f  window %.0f  %d columns"
                % (slug, hint, ref, ref_sat, win, len(cols)))
        print("  %-10s hint %3.0f -> hue %3.0f deg  sat %.2f  %4d columns"
              " window %2.0f %5d numbers" % (slug, hint, ref, ref_sat, len(cols), win, nums))
    with io.open(os.path.join(OUT, "walls.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("walls traced")


main()
