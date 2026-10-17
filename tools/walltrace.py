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
CLOSE = 8          # a break this short is a speck, not a hole in the wall
EDGE = 2           # pixels of blend always taken at each end of a span
REACH = 6          # ...and up to this many while the edge is still in shadow
DARKER = 1.6       # how much brighter than the span's own edge still counts


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

    order = []
    raw = {}
    for x in range(0, w, STEP):
        xs = min(x, w - 1)
        order.append(xs)
        runs = []
        y0 = None
        for y in range(0, h):
            if is_wall(*px[xs, y]):
                if y0 is None:
                    y0 = y
            else:
                if y0 is not None:
                    runs.append([y0, y - 1])
                y0 = None
        if y0 is not None:
            runs.append([y0, h - 1])
        raw[xs] = merge(runs, CLOSE)

    cols = []
    for i, xs in enumerate(order):
        left = raw[order[i - 1]] if i > 0 else None
        right = raw[order[i + 1]] if i + 1 < len(order) else None
        runs = [r for r in raw[xs]
                if r[1] - r[0] + 1 >= MIN_RUN or joined(r, left, right)]
        runs = merge(grow(runs, h, px, xs), 0)
        if runs:
            cols.append([xs] + [c for r in runs for c in r])
    return cols, (w, h), (ref, ref_sat, win)


def joined(run, left, right):
    """Is this short run part of the wall on either side of it.

    The minimum length is there to throw away a speck: a reflection, a
    highlight, a few pixels of noise that happen to be the right colour. But
    it throws away honest wall too, wherever a run is cut short — under the
    lip of a cabinet, beside the hood — and what is left is a dash of old
    paint standing on a tiled wall. Every dash in all three rooms was
    thirteen pixels or less against a threshold of fourteen.

    So the length alone no longer decides. A short run is kept when the
    columns to either side are wall at the same height, because that is a
    continuous surface seen through a narrow gap. A speck has no such
    neighbours, which is exactly what makes it a speck.
    """
    a, b = run
    sides = [s for s in (left, right) if s is not None]
    if not sides:
        return False
    for s in sides:
        if not any(r[0] <= b and r[1] >= a for r in s):
            return False
    return True


def merge(runs, gap):
    """Join runs separated by no more than gap pixels.

    A flat wall photographs with specks in it: a pixel of sensor noise, the
    highlight on a socket, the line of a shadow. Each one cuts the column in
    two and leaves a dot of old paint showing through the tiling. Nothing
    that short is a real hole in a wall, and a window or a mirror is hundreds
    of pixels, so it survives this untouched.
    """
    out = []
    for a, b in runs:
        if out and a - out[-1][1] - 1 <= gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def grow(runs, h, px, x):
    """Stretch each run over the blend at its ends.

    Where the wall meets a cabinet there is no edge, there is a ramp: a few
    pixels that are part wall and part cabinet. They are not the paint, so
    the test rightly refuses them, and the tiling then stops short and
    leaves them showing. They are dark, and a dark green pixel still reads
    green, so what you see is a ragged green fringe along every junction in
    the room.

    How wide the ramp is varies: one pixel against a bright worktop, five or
    six up in the shadow where the wall meets the ceiling. A fixed width is
    either mean somewhere or greedy somewhere else, so the run takes EDGE
    pixels always and then keeps going, as far as REACH, while the pixels
    stay dark. The span's own edge sets what dark means, because a wall in
    shadow is dark everywhere along that edge; the first pixel appreciably
    brighter than it is the cabinet, or the worktop, or the ceiling, and the
    growth stops there.
    """
    out = []
    for a, b in runs:
        va = value(px[x, a])
        vb = value(px[x, b])
        na, nb = max(0, a - EDGE), min(h - 1, b + EDGE)
        # from where the growth started, or the limit moves with it and the
        # run walks the whole column looking for something bright
        top, bot, far = na, nb, REACH - EDGE
        y = top - 1
        while y >= 0 and top - y <= far and value(px[x, y]) <= va * DARKER:
            na = y
            y -= 1
        y = bot + 1
        while y < h and y - bot <= far and value(px[x, y]) <= vb * DARKER:
            nb = y
            y += 1
        out.append([na, nb])
    return out


def value(rgb):
    return max(rgb) / 255.0


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
