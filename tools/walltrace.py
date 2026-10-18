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

SRC = "/mnt/c/Users/HC COMPUTER STORE/Local Sites/visualiser-rooms"
OUT = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls")

# file, id, roughly what colour the walls were painted, in degrees of hue.
# Pink is about 10 and green about 85; the exact figure is measured, this
# only says which colour in the room is the paint.
ROOMS = [
    # file, id, roughly what colour the walls were painted, in degrees of
    # hue. These rooms are all coral, which measures out between 6 and 12.
    # The living room and the veranda are not here: their walls were never
    # painted, so there is nothing to trace and they are floor only.
    ("Coral and Navy Modern Bathroom.png",            "ensuite",  10.0),
    ("Sunlit Coral and Navy Bathroom Spa.png",        "bathroom", 10.0),
    ("Natural Light Modern Pink and Blue Kitchen.png", "kitchen", 10.0),
]

STEP = 1           # columns. One, not three: the mask is built in blocks
#                    this wide, so anything bigger quantises every boundary
#                    and the top of a tiled wall comes out as a staircase
#                    with steps that size. Three was visible.
MIN_RUN = 14       # a span shorter than this is a reflection, not a wall
CLOSE = 8          # a break this short is a speck, not a hole in the wall
EDGE = 2           # pixels of blend taken at each end of a span
ISLAND = 400       # a patch of mask smaller than this is not a wall
PINHOLE = 12       # a hole no wider and no taller than this is not a window
SMOOTH = 9         # columns averaged when straightening the wall's own edges
WANDER = 10        # ...and the most a column may be moved while doing it


def spans(path, hint):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    w, h = im.size
    px = im.filter(ImageFilter.GaussianBlur(0.6)).load()
    found = keycolour.paint(px, w, h, hint)
    if found is None:
        return None, (w, h), None
    ref, ref_sat, win, ref_val = found
    is_wall = keycolour.tester(ref, ref_sat, win, ref_val)

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
        runs = merge(grow(runs, h, px, xs,
                          ref_val * keycolour.VLO), 0)
        if runs:
            cols.append([xs] + [c for r in runs for c in r])
    cols = tidy(cols, h)
    cols = straighten(cols, h)
    return cols, (w, h), (ref, ref_sat, win)


def blobs(grid, nc, h, want):
    """Every 4-connected patch of `want`, as (cells, width, height, edge)."""
    from collections import deque
    seen = bytearray(nc * h)
    out = []
    for start in range(nc * h):
        if seen[start] or grid[start] != want:
            continue
        q = deque([start])
        seen[start] = 1
        cells = [start]
        x0 = x1 = start % nc
        y0 = y1 = start // nc
        edge = False
        while q:
            p = q.popleft()
            cx, cy = p % nc, p // nc
            if cx == 0 or cx == nc - 1 or cy == 0 or cy == h - 1:
                edge = True
            if cx < x0:
                x0 = cx
            if cx > x1:
                x1 = cx
            if cy < y0:
                y0 = cy
            if cy > y1:
                y1 = cy
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ax, ay = cx + dx, cy + dy
                if 0 <= ax < nc and 0 <= ay < h:
                    a = ay * nc + ax
                    if not seen[a] and grid[a] == want:
                        seen[a] = 1
                        q.append(a)
                        cells.append(a)
        out.append((cells, x1 - x0 + 1, y1 - y0 + 1, edge))
    return out


def tidy(cols, h):
    """Take the specks out of the mask and fill the pinholes in it.

    Everything above this point works a column at a time, which cannot see
    a speck sitting on a toilet lid or a pinhole in the middle of a wall.
    Looked at as a mask, both are obvious, and both are what shows in the
    picture as a small patch that changes colour whenever the tile changes.

    The two thresholds are not taste, they are the gap in the measurements.
    A real wall is between fifty thousand and two hundred thousand cells;
    everything else in these rooms is under four hundred, with nothing in
    between. A window, a mirror or a sunlit reveal is between forty-five and
    two hundred and thirty rows tall; the noise is twelve by twelve or less.
    A hole has to be small in both directions to be filled, which is what
    keeps the towel and the reveals as holes: they are narrow, but they are
    long.
    """
    xs = [c[0] for c in cols]
    nc = len(xs)
    if not nc:
        return cols
    grid = bytearray(nc * h)
    for i, col in enumerate(cols):
        for k in range(1, len(col), 2):
            for y in range(col[k], min(col[k + 1] + 1, h)):
                grid[y * nc + i] = 1

    for cells, bw, bh, _ in blobs(grid, nc, h, 1):
        if len(cells) < ISLAND:
            for c in cells:
                grid[c] = 0
    for cells, bw, bh, edge in blobs(grid, nc, h, 0):
        if not edge and bw <= PINHOLE and bh <= PINHOLE:
            for c in cells:
                grid[c] = 1

    out = []
    for i, x in enumerate(xs):
        runs = []
        y0 = None
        for y in range(h):
            if grid[y * nc + i]:
                if y0 is None:
                    y0 = y
            elif y0 is not None:
                runs.append([y0, y - 1])
                y0 = None
        if y0 is not None:
            runs.append([y0, h - 1])
        if runs:
            out.append([x] + [v for r in runs for v in r])
    return out


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


def grow(runs, h, px, x, dark):
    """Stretch each run over the blend at its ends, where there is one.

    Where the wall meets a cabinet there is no edge, there is a ramp: three
    or four pixels that are part wall and part cabinet. They are not the
    paint, so the test rightly refuses them, and the tiling then stops short
    and leaves them showing as a fringe along the junction.

    Where the wall meets a black window frame there is no ramp at all. The
    wall ends at one row and the frame starts at the next, measured in all
    three rooms: zero pixels in between. Growing into that puts two pixels
    of tile along the top and bottom of every window, on a crisp black edge
    where it shows, and covers nothing that needed covering.

    So the growth stops at the first pixel that is plainly not wall, which
    is the same brightness floor the test itself uses: a frame, a tap, a
    black fitting. A blend pixel against a cabinet is dark but not that
    dark, and is still taken.

    Being mean here is cheap either way. Whatever the tile does not cover,
    the repaint pass neutralises, and a neutralised pixel is invisible.
    """
    out = []
    for a, b in runs:
        na, nb = a, b
        for i in range(1, EDGE + 1):
            y = a - i
            if y < 0 or max(px[x, y]) / 255.0 < dark:
                break
            na = y
        for i in range(1, EDGE + 1):
            y = b + i
            if y >= h or max(px[x, y]) / 255.0 < dark:
                break
            nb = y
        out.append([na, nb])
    return out


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
    for name, slug, hint in ROOMS:
        p = os.path.join(SRC, name)
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




def straighten(cols, h):
    """Take the wander out of the top and bottom edges of the wall.

    Where a wall meets a ceiling there is no line, there is a gradient: the
    ceiling catches the wall's colour and fades into it over several pixels.
    The test has to cross that gradient somewhere, and it crosses a pixel or
    two higher or lower in each column depending on nothing but noise. The
    mask is correct to within a pixel everywhere and still reads as a chewed
    edge, because the eye follows the edge rather than the pixels.

    Measured on these rooms, that wander is at most three pixels in
    ninety-five columns out of a hundred. A genuine step, where the wall
    meets a window or a cabinet, is twenty-five or more. There is a wide gap
    between the two, so a column is moved to the median of its neighbours
    only when that asks for less than WANDER pixels, and a real step is left
    exactly where it is.

    Only the outermost edges are straightened. The sides of a window are
    already crisp in the photograph, being a black frame against paint, and
    they are nobody's idea of a gradient.
    """
    if not cols:
        return cols
    first = [c[1] for c in cols]
    last = [c[-1] for c in cols]
    half = SMOOTH // 2
    out = []
    for i, col in enumerate(cols):
        a, b = max(0, i - half), min(len(cols), i + half + 1)
        ftop = sorted(first[a:b])[(b - a) // 2]
        flast = sorted(last[a:b])[(b - a) // 2]
        new = list(col)
        if abs(ftop - new[1]) <= WANDER:
            new[1] = max(0, min(ftop, new[2]))
        if abs(flast - new[-1]) <= WANDER:
            new[-1] = min(h - 1, max(flast, new[-2]))
        out.append(new)
    return out


main()
